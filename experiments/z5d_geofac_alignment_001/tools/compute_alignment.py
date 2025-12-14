#!/usr/bin/env python3
"""
Compute overlap and alignment statistics between Z5D and Geofac peaks.

Calculates:
- Jaccard index on bins
- Top-K hit rate
- Spearman rank correlation
- Bootstrap confidence intervals

Usage:
    python compute_alignment.py \
        --z5d ../artifacts/z5d/peaks_phi_qmc_001.jsonl \
        --geofac ../artifacts/geofac/peaks_phi_qmc_001.jsonl \
        --output ../artifacts/alignment/phi_qmc_001/overlap_report.json \
        --bootstrap-samples 1000
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

import numpy as np
from scipy import stats


def read_jsonl(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Read JSONL file with metadata.
    
    Returns:
        Tuple of (metadata, results_list)
    """
    with path.open('r') as f:
        lines = f.readlines()
    
    # First line is metadata
    metadata = json.loads(lines[0])['_metadata']
    
    # Rest are results
    results = [json.loads(line) for line in lines[1:]]
    
    return metadata, results


def extract_bins(results: List[Dict[str, Any]]) -> Set[int]:
    """Extract set of bin IDs from results."""
    bins = set()
    for r in results:
        if 'bin_id' in r and r['bin_id'] is not None:
            bins.add(r['bin_id'])
    return bins


def compute_jaccard(bins_a: Set[int], bins_b: Set[int]) -> float:
    """
    Compute Jaccard index: |A ∩ B| / |A ∪ B|
    """
    if not bins_a and not bins_b:
        return 1.0
    if not bins_a or not bins_b:
        return 0.0
    
    intersection = bins_a & bins_b
    union = bins_a | bins_b
    
    return len(intersection) / len(union)


def compute_topk_hitrate(bins_z5d: Set[int], bins_geofac: Set[int]) -> float:
    """
    Compute fraction of z5d top-K bins present in geofac top-K.
    """
    if not bins_z5d:
        return 0.0
    
    hits = bins_z5d & bins_geofac
    return len(hits) / len(bins_z5d)


def compute_spearman_correlation(z5d_results: List[Dict[str, Any]], 
                                 geofac_results: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation between scores/amplitudes in matching bins.
    
    Returns:
        Tuple of (rho, p_value)
    """
    # Build maps from bin_id to score/amplitude
    z5d_scores = {}
    for r in z5d_results:
        if 'bin_id' in r and 'score' in r and r['bin_id'] is not None:
            z5d_scores[r['bin_id']] = r['score']
    
    geofac_scores = {}
    for r in geofac_results:
        if 'bin_id' in r and 'amplitude' in r and r['bin_id'] is not None:
            geofac_scores[r['bin_id']] = r['amplitude']
    
    # Find common bins
    common_bins = set(z5d_scores.keys()) & set(geofac_scores.keys())
    
    if len(common_bins) < 3:
        return 0.0, 1.0  # Not enough data for correlation
    
    # Build paired arrays
    z5d_vals = [z5d_scores[b] for b in common_bins]
    geofac_vals = [geofac_scores[b] for b in common_bins]
    
    # Compute Spearman correlation
    rho, pval = stats.spearmanr(z5d_vals, geofac_vals)
    
    return float(rho), float(pval)


def bootstrap_jaccard(z5d_results: List[Dict[str, Any]], 
                     geofac_results: List[Dict[str, Any]],
                     n_bootstrap: int = 1000,
                     confidence_level: float = 0.95) -> Tuple[float, List[float]]:
    """
    Compute bootstrap confidence interval for Jaccard index.
    
    Resamples rows (by row_id) to estimate variability.
    
    Returns:
        Tuple of (mean_jaccard, [lower_ci, upper_ci])
    """
    # Get all row_ids
    z5d_row_ids = set(r['row_id'] for r in z5d_results if 'row_id' in r)
    geofac_row_ids = set(r['row_id'] for r in geofac_results if 'row_id' in r)
    common_row_ids = list(z5d_row_ids & geofac_row_ids)
    
    if len(common_row_ids) < 10:
        # Not enough data for bootstrap
        bins_z5d = extract_bins(z5d_results)
        bins_geofac = extract_bins(geofac_results)
        j = compute_jaccard(bins_z5d, bins_geofac)
        return j, [j, j]
    
    # Build index for fast lookup
    z5d_by_row = {r['row_id']: r for r in z5d_results if 'row_id' in r and 'bin_id' in r}
    geofac_by_row = {r['row_id']: r for r in geofac_results if 'row_id' in r and 'bin_id' in r}
    
    jaccards = []
    rng = np.random.RandomState(42)
    
    for _ in range(n_bootstrap):
        # Resample row_ids with replacement
        sample_ids = rng.choice(common_row_ids, size=len(common_row_ids), replace=True)
        
        # Get bins for this sample
        z5d_bins = set()
        geofac_bins = set()
        
        for rid in sample_ids:
            if rid in z5d_by_row and z5d_by_row[rid].get('bin_id') is not None:
                z5d_bins.add(z5d_by_row[rid]['bin_id'])
            if rid in geofac_by_row and geofac_by_row[rid].get('bin_id') is not None:
                geofac_bins.add(geofac_by_row[rid]['bin_id'])
        
        # Compute Jaccard for this sample
        j = compute_jaccard(z5d_bins, geofac_bins)
        jaccards.append(j)
    
    # Compute confidence interval
    alpha = 1 - confidence_level
    lower = np.percentile(jaccards, 100 * alpha / 2)
    upper = np.percentile(jaccards, 100 * (1 - alpha / 2))
    mean_j = np.mean(jaccards)
    
    return mean_j, [float(lower), float(upper)]


def get_git_sha(repo_path: Path) -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return 'unknown'


def main():
    parser = argparse.ArgumentParser(
        description='Compute alignment statistics between Z5D and Geofac peaks'
    )
    parser.add_argument(
        '--z5d',
        type=Path,
        required=True,
        help='Z5D peaks JSONL file'
    )
    parser.add_argument(
        '--geofac',
        type=Path,
        required=True,
        help='Geofac peaks JSONL file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output JSON file for overlap report'
    )
    parser.add_argument(
        '--bootstrap-samples',
        type=int,
        default=1000,
        help='Number of bootstrap samples for CI (default: 1000)'
    )
    parser.add_argument(
        '--confidence-level',
        type=float,
        default=0.95,
        help='Confidence level for CI (default: 0.95)'
    )
    
    args = parser.parse_args()
    
    # Read input files
    print(f"Reading Z5D peaks from {args.z5d}...", file=sys.stderr)
    z5d_meta, z5d_results = read_jsonl(args.z5d)
    print(f"Loaded {len(z5d_results)} Z5D results", file=sys.stderr)
    
    print(f"Reading Geofac peaks from {args.geofac}...", file=sys.stderr)
    geofac_meta, geofac_results = read_jsonl(args.geofac)
    print(f"Loaded {len(geofac_results)} Geofac results", file=sys.stderr)
    
    # Extract bins
    print("Extracting bins...", file=sys.stderr)
    z5d_bins = extract_bins(z5d_results)
    geofac_bins = extract_bins(geofac_results)
    
    print(f"Z5D: {len(z5d_bins)} unique bins", file=sys.stderr)
    print(f"Geofac: {len(geofac_bins)} unique bins", file=sys.stderr)
    
    # Compute Jaccard index
    print("Computing Jaccard index...", file=sys.stderr)
    jaccard = compute_jaccard(z5d_bins, geofac_bins)
    print(f"Jaccard index: {jaccard:.4f}", file=sys.stderr)
    
    # Compute top-K hit rate
    print("Computing top-K hit rate...", file=sys.stderr)
    topk_hitrate = compute_topk_hitrate(z5d_bins, geofac_bins)
    print(f"Top-K hit rate: {topk_hitrate:.4f}", file=sys.stderr)
    
    # Compute Spearman correlation
    print("Computing Spearman correlation...", file=sys.stderr)
    spearman_rho, spearman_pval = compute_spearman_correlation(z5d_results, geofac_results)
    print(f"Spearman rho: {spearman_rho:.4f} (p={spearman_pval:.4e})", file=sys.stderr)
    
    # Bootstrap CI
    print(f"Computing bootstrap CI ({args.bootstrap_samples} samples)...", file=sys.stderr)
    mean_jaccard, jaccard_ci = bootstrap_jaccard(
        z5d_results, geofac_results, 
        args.bootstrap_samples, 
        args.confidence_level
    )
    print(f"Bootstrap mean Jaccard: {mean_jaccard:.4f}", file=sys.stderr)
    print(f"Bootstrap {int(args.confidence_level*100)}% CI: [{jaccard_ci[0]:.4f}, {jaccard_ci[1]:.4f}]", file=sys.stderr)
    
    # Get git SHAs
    repo_path = Path(__file__).parent.parent.parent.parent
    git_sha = get_git_sha(repo_path)
    
    # Prepare report
    report = {
        'seed_set_id': z5d_meta.get('seed_set_id', 'unknown'),
        'qmc_type': z5d_meta.get('qmc_type', 'unknown'),
        'K': z5d_meta.get('top_k', len(z5d_results)),
        'jaccard_bins': float(jaccard),
        'jaccard_ci_95': jaccard_ci,
        'jaccard_bootstrap_mean': float(mean_jaccard),
        'topk_hit_rate': float(topk_hitrate),
        'spearman_rho': float(spearman_rho),
        'spearman_pval': float(spearman_pval),
        'scale_gate': f"10^{z5d_meta.get('scale_min', 14)}–10^{z5d_meta.get('scale_max', 18)}",
        'dataset': 'RSA-synthetic',  # Since we're generating test semiprimes
        'precision': {
            'scale': 256,  # From z5d implementation
            'rounding': 'HALF_EVEN'
        },
        'num_bins': z5d_meta.get('num_bins', 1000),
        'z5d_unique_bins': len(z5d_bins),
        'geofac_unique_bins': len(geofac_bins),
        'intersection_bins': len(z5d_bins & geofac_bins),
        'union_bins': len(z5d_bins | geofac_bins),
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'git': {
            'sha': git_sha
        },
        'bootstrap_samples': args.bootstrap_samples,
        'confidence_level': args.confidence_level
    }
    
    # Gate decision
    passes_gate = jaccard >= 0.20 and jaccard_ci[0] > 0.10
    report['gate_decision'] = {
        'passes_z5d_gate': passes_gate,
        'criteria': 'Jaccard >= 0.20 and CI_lower > 0.10',
        'jaccard_threshold': 0.20,
        'ci_lower_threshold': 0.10
    }
    
    # Write report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nWrote overlap report to {args.output}", file=sys.stderr)
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"GATE DECISION: {'PASS' if passes_gate else 'FAIL'}", file=sys.stderr)
    print(f"  Jaccard: {jaccard:.4f} (threshold: 0.20)", file=sys.stderr)
    print(f"  CI lower: {jaccard_ci[0]:.4f} (threshold: 0.10)", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
