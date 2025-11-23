#!/usr/bin/env python3
"""
Z5D Predictor Peak Extractor

Runs z5d-predictor-c for a range of k values derived from QMC seeds
and extracts peak candidates for alignment analysis.

Usage:
    python run_z5d_peaks.py --seeds ../artifacts/seedsets/phi_qmc_001.csv \
                            --output ../artifacts/z5d/peaks_phi_qmc_001.jsonl \
                            --scale-min 14 --scale-max 18 --top-k 2000
"""
import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import numpy as np


def read_seed_csv(seed_path: Path) -> tuple[List[int], np.ndarray, Dict[str, Any]]:
    """
    Read QMC seed CSV file.
    
    Returns:
        Tuple of (row_ids, samples, metadata)
    """
    with seed_path.open('r') as f:
        reader = csv.reader(f)
        
        # Parse metadata from comments
        metadata = {}
        for row in reader:
            if not row or not row[0].startswith('#'):
                break
            if ':' in row[0]:
                key, value = row[0][1:].split(':', 1)
                metadata[key.strip()] = value.strip()
        
        # Read header
        header = next(reader)
        
        # Read data
        row_ids = []
        samples = []
        for row in reader:
            if row:
                row_ids.append(int(row[0]))
                samples.append([float(x) for x in row[1:]])
    
    return row_ids, np.array(samples), metadata


def map_qmc_to_k(qmc_values: np.ndarray, scale_min: int, scale_max: int) -> np.ndarray:
    """
    Map QMC samples [0,1]^d to k indices in range [10^scale_min, 10^scale_max].
    
    Uses the first dimension of QMC samples.
    
    Args:
        qmc_values: QMC samples array of shape (n, d)
        scale_min: Minimum scale exponent (e.g., 14 for 10^14)
        scale_max: Maximum scale exponent (e.g., 18 for 10^18)
        
    Returns:
        Array of k indices
    """
    # Use first dimension for k mapping
    u = qmc_values[:, 0]
    
    # Map [0, 1] to [10^scale_min, 10^scale_max] logarithmically
    log_min = scale_min
    log_max = scale_max
    log_k = log_min + u * (log_max - log_min)
    k_values = np.power(10.0, log_k).astype(np.int64)
    
    return k_values


def run_z5d_predictor_mock(k: int) -> Dict[str, Any]:
    """
    Mock Z5D predictor using Riemann R approximation.
    Used when z5d_cli is not available (non-Apple Silicon platforms).
    
    Args:
        k: Index for nth prime prediction
        
    Returns:
        Dictionary with prediction results
    """
    import sympy
    
    # Use Riemann R function approximation for nth prime
    # This is a simplified version of what z5d does
    log_k = np.log(float(k))
    
    # Riemann R approximation
    if k < 10:
        predicted_prime = sympy.nextprime(int(k))
    else:
        # R(x) ≈ x * (log(x) + log(log(x)) - 1)
        # We need to find x such that R(x) ≈ k
        # Use iterative approximation
        x = k * (log_k + np.log(log_k))
        
        # Improve estimate
        for _ in range(3):
            if x <= 1:
                x = 2
                break
            log_x = np.log(x)
            log_log_x = np.log(log_x) if log_x > 1 else 0
            R_x = x / log_x  # Simplified
            if R_x > 0:
                x = x * k / R_x
        
        predicted_prime = int(x)
    
    score = np.log10(float(k))
    
    return {
        'k': k,
        'predicted_prime': predicted_prime,
        'score': score,
        'window': 1,
        'bin_id': None,
        'method': 'mock'  # Mark as mock for transparency
    }


def run_z5d_predictor(k: int, z5d_cli_path: Path, use_mock: bool = False) -> Dict[str, Any]:
    """
    Run z5d-predictor-c for a single k value and parse output.
    
    Args:
        k: Index for nth prime prediction
        z5d_cli_path: Path to z5d_cli binary
        use_mock: If True, use mock implementation instead of binary
        
    Returns:
        Dictionary with prediction results including score/amplitude
    """
    if use_mock:
        return run_z5d_predictor_mock(k)
    
    try:
        result = subprocess.run(
            [str(z5d_cli_path), str(k)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {'error': result.stderr, 'k': k}
        
        # Parse output - z5d_cli outputs the predicted prime
        output = result.stdout.strip()
        
        # The output is typically just the predicted prime number
        # We'll treat the prediction as the "amplitude" and use log(k) as a proxy score
        try:
            predicted_prime = int(output)
            score = np.log10(float(k))  # Use log scale as score proxy
            
            return {
                'k': k,
                'predicted_prime': predicted_prime,
                'score': score,
                'window': 1,  # Single point prediction
                'bin_id': None  # To be assigned during binning
            }
        except ValueError:
            return {'error': f'Failed to parse output: {output}', 'k': k}
            
    except subprocess.TimeoutExpired:
        return {'error': 'Timeout', 'k': k}
    except Exception as e:
        return {'error': str(e), 'k': k}


def extract_z5d_peaks(row_ids: List[int], k_values: np.ndarray, z5d_cli_path: Path, 
                      max_samples: int = None, use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Run z5d predictor for all k values and extract results.
    
    Args:
        row_ids: List of row IDs from seed CSV
        k_values: Array of k indices
        z5d_cli_path: Path to z5d_cli binary
        max_samples: Maximum number of samples to process (for testing)
        use_mock: Use mock predictor if True
        
    Returns:
        List of prediction results
    """
    results = []
    
    if max_samples:
        row_ids = row_ids[:max_samples]
        k_values = k_values[:max_samples]
    
    total = len(row_ids)
    for idx, (row_id, k) in enumerate(zip(row_ids, k_values)):
        if idx % 1000 == 0:
            print(f"Processing {idx}/{total} ({100*idx/total:.1f}%)...", file=sys.stderr)
        
        result = run_z5d_predictor(k, z5d_cli_path, use_mock)
        result['row_id'] = row_id
        result['n_or_param'] = k
        results.append(result)
    
    return results


def assign_bins(results: List[Dict[str, Any]], num_bins: int = 1000) -> List[Dict[str, Any]]:
    """
    Assign bin IDs to results based on predicted prime values.
    
    Uses equal-width binning in log space.
    
    Args:
        results: List of prediction results
        num_bins: Number of bins
        
    Returns:
        Updated results with bin_id assigned
    """
    # Filter valid results
    valid_results = [r for r in results if 'predicted_prime' in r]
    
    if not valid_results:
        return results
    
    # Get prime range
    primes = np.array([r['predicted_prime'] for r in valid_results])
    log_primes = np.log10(primes)
    
    # Create bins
    min_log = log_primes.min()
    max_log = log_primes.max()
    bins = np.linspace(min_log, max_log, num_bins + 1)
    
    # Assign bin IDs
    for r in valid_results:
        if 'predicted_prime' in r:
            log_p = np.log10(r['predicted_prime'])
            bin_id = np.searchsorted(bins[:-1], log_p, side='right') - 1
            bin_id = max(0, min(num_bins - 1, bin_id))
            r['bin_id'] = int(bin_id)
    
    return results


def write_jsonl(results: List[Dict[str, Any]], output_path: Path, metadata: Dict[str, Any]):
    """
    Write results to JSONL file with metadata.
    
    Args:
        results: List of prediction results
        output_path: Path to output file
        metadata: Metadata dictionary
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open('w') as f:
        # Write metadata as first line
        meta_line = {'_metadata': metadata}
        f.write(json.dumps(meta_line) + '\n')
        
        # Write results
        for result in results:
            f.write(json.dumps(result) + '\n')


def main():
    parser = argparse.ArgumentParser(
        description='Extract Z5D predictor peaks for alignment analysis'
    )
    parser.add_argument(
        '--seeds',
        type=Path,
        required=True,
        help='Input QMC seed CSV file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output JSONL file for peaks'
    )
    parser.add_argument(
        '--z5d-cli',
        type=Path,
        default=Path('src/c/z5d-predictor-c/bin/z5d_cli'),
        help='Path to z5d_cli binary'
    )
    parser.add_argument(
        '--scale-min',
        type=int,
        default=14,
        help='Minimum scale (10^N) for k range (default: 14)'
    )
    parser.add_argument(
        '--scale-max',
        type=int,
        default=18,
        help='Maximum scale (10^N) for k range (default: 18)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=2000,
        help='Number of top peaks to keep (default: 2000)'
    )
    parser.add_argument(
        '--num-bins',
        type=int,
        default=1000,
        help='Number of bins for binning (default: 1000)'
    )
    parser.add_argument(
        '--max-samples',
        type=int,
        help='Maximum samples to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Check z5d_cli exists
    z5d_cli_path = args.z5d_cli
    if not z5d_cli_path.is_absolute():
        z5d_cli_path = Path('/home/runner/work/z5d-prime-predictor/z5d-prime-predictor') / z5d_cli_path
    
    use_mock = False
    if not z5d_cli_path.exists():
        print(f"WARNING: z5d_cli not found at {z5d_cli_path}", file=sys.stderr)
        print("Using mock Z5D predictor (Riemann R approximation)", file=sys.stderr)
        print("Note: This is not the full Z5D implementation but allows testing on non-Apple Silicon", file=sys.stderr)
        use_mock = True
    
    # Read seeds
    print(f"Reading seeds from {args.seeds}...", file=sys.stderr)
    row_ids, samples, seed_metadata = read_seed_csv(args.seeds)
    print(f"Loaded {len(row_ids)} seed samples", file=sys.stderr)
    
    # Map to k values
    print(f"Mapping QMC samples to k values in range [10^{args.scale_min}, 10^{args.scale_max}]...", file=sys.stderr)
    k_values = map_qmc_to_k(samples, args.scale_min, args.scale_max)
    
    # Run predictions
    print(f"Running z5d predictor{'(mock)' if use_mock else ''}...", file=sys.stderr)
    results = extract_z5d_peaks(row_ids, k_values, z5d_cli_path, args.max_samples, use_mock)
    
    # Assign bins
    print("Assigning bins...", file=sys.stderr)
    results = assign_bins(results, args.num_bins)
    
    # Sort by score and keep top-K
    valid_results = [r for r in results if 'score' in r and 'error' not in r]
    valid_results.sort(key=lambda x: x['score'], reverse=True)
    top_results = valid_results[:args.top_k]
    
    print(f"Keeping top {len(top_results)} results out of {len(valid_results)} valid predictions", file=sys.stderr)
    
    # Prepare metadata
    metadata = {
        'seed_set_id': seed_metadata.get('seed_set_id', 'unknown'),
        'qmc_type': seed_metadata.get('qmc_type', 'unknown'),
        'scale_min': args.scale_min,
        'scale_max': args.scale_max,
        'top_k': args.top_k,
        'num_bins': args.num_bins,
        'total_samples': len(results),
        'valid_samples': len(valid_results),
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'tool': 'z5d-predictor-c' + (' (mock)' if use_mock else '')
    }
    
    # Write output
    write_jsonl(top_results, args.output, metadata)
    print(f"Wrote {len(top_results)} peaks to {args.output}", file=sys.stderr)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
