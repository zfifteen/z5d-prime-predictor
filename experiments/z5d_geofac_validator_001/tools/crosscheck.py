#!/usr/bin/env python3
"""
Cross-Validation Script: Geofac + Z5D
======================================

This script:
1. Generates candidates using Geofac resonance
2. Validates them using Z5D ranking
3. Analyzes agreement and produces calibration metrics

Output: Unified CSV/JSONL with standard schema
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))
import z_shared
from geofac_scorer import GeofacScorer
from z5d_adapter import Z5DValidator


def merge_results(geofac_results, z5d_results, top_k: int = 10):
    """
    Merge Geofac and Z5D results and compute agreement.
    
    Args:
        geofac_results: List of ResonanceResult from Geofac
        z5d_results: List of ValidationResult from Z5D
        top_k: Top-K threshold for agreement
        
    Returns:
        List of merged result dictionaries
    """
    # Create lookup by (p, q)
    geofac_map = {(r.p, r.q): r for r in geofac_results}
    z5d_map = {(r.p, r.q): r for r in z5d_results}
    
    # Get top-K sets
    geofac_top_k = set((r.p, r.q) for r in geofac_results[:top_k])
    z5d_top_k = set((r.p, r.q) for r in z5d_results[:top_k])
    
    # Merge
    merged = []
    all_pairs = set(geofac_map.keys()) | set(z5d_map.keys())
    
    for pair in all_pairs:
        p, q = pair
        geofac = geofac_map.get(pair)
        z5d = z5d_map.get(pair)
        
        # Agreement: both in top-K or both not in top-K
        in_geofac_top_k = pair in geofac_top_k
        in_z5d_top_k = pair in z5d_top_k
        agree = in_geofac_top_k == in_z5d_top_k
        
        merged.append({
            "p": p,
            "q": q,
            "product": geofac.product if geofac else z5d.product,
            "error": geofac.error if geofac else z5d.error,
            "is_factor": geofac.is_factor if geofac else z5d.is_factor,
            "resonance_rank": geofac.resonance_rank if geofac else None,
            "resonance_score": geofac.resonance_score if geofac else None,
            "z5d_rank": z5d.z5d_rank if z5d else None,
            "z5d_score": z5d.z5d_score if z5d else None,
            "agree": agree,
            "in_geofac_top_k": in_geofac_top_k,
            "in_z5d_top_k": in_z5d_top_k,
        })
    
    return merged


def compute_metrics(merged_results, top_k: int = 10):
    """
    Compute calibration and agreement metrics.
    
    Args:
        merged_results: List of merged result dictionaries
        top_k: Top-K threshold
        
    Returns:
        Dictionary of metrics
    """
    # Filter to pairs with both scores
    both_scored = [
        r for r in merged_results
        if r["resonance_score"] is not None and r["z5d_score"] is not None
    ]
    
    if not both_scored:
        return {"error": "No pairs scored by both systems"}
    
    # Agreement rate
    agree_count = sum(1 for r in both_scored if r["agree"])
    agreement_rate = agree_count / len(both_scored)
    
    # Top-K overlap (Jaccard)
    geofac_top_k = set(
        (r["p"], r["q"]) for r in both_scored if r["in_geofac_top_k"]
    )
    z5d_top_k = set(
        (r["p"], r["q"]) for r in both_scored if r["in_z5d_top_k"]
    )
    
    intersection = geofac_top_k & z5d_top_k
    union = geofac_top_k | z5d_top_k
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # Hit rate (asymmetric)
    hit_rate_geofac = len(intersection) / len(geofac_top_k) if geofac_top_k else 0.0
    hit_rate_z5d = len(intersection) / len(z5d_top_k) if z5d_top_k else 0.0
    
    # Rank correlation (Spearman)
    from scipy.stats import spearmanr
    
    geofac_ranks = [r["resonance_rank"] for r in both_scored]
    z5d_ranks = [r["z5d_rank"] for r in both_scored]
    
    if len(geofac_ranks) > 1:
        spearman_corr, spearman_p = spearmanr(geofac_ranks, z5d_ranks)
    else:
        spearman_corr, spearman_p = None, None
    
    # Find true factors
    true_factors = [r for r in both_scored if r["is_factor"]]
    
    metrics = {
        "total_pairs": len(both_scored),
        "top_k": top_k,
        "agreement_rate": agreement_rate,
        "jaccard_index": jaccard,
        "hit_rate_geofac_to_z5d": hit_rate_geofac,
        "hit_rate_z5d_to_geofac": hit_rate_z5d,
        "spearman_correlation": spearman_corr,
        "spearman_p_value": spearman_p,
        "true_factors_found": len(true_factors),
        "true_factors": [
            {
                "p": r["p"],
                "q": r["q"],
                "resonance_rank": r["resonance_rank"],
                "z5d_rank": r["z5d_rank"],
            }
            for r in true_factors
        ],
    }
    
    return metrics


def run_crosscheck(
    N: int,
    num_candidates: int,
    seed: int,
    dps: int,
    top_k: int,
    verbose: bool = False
):
    """
    Run full cross-validation for a single N.
    
    Returns:
        Tuple of (merged_results, metrics)
    """
    if verbose:
        print(f"\n{'='*80}", file=sys.stderr)
        print(f"Cross-validation for N={N}", file=sys.stderr)
        print(f"{'='*80}", file=sys.stderr)
    
    # 1. Geofac: Generate and score candidates
    if verbose:
        print("\n[1/3] Running Geofac scorer...", file=sys.stderr)
    
    geofac = GeofacScorer(seed=seed, verbose=verbose)
    pairs = geofac.generate_candidates(N, num_candidates)
    geofac_results = geofac.score_candidates(N, pairs, dps)
    
    # 2. Z5D: Validate same candidates
    if verbose:
        print("\n[2/3] Running Z5D validator...", file=sys.stderr)
    
    z5d = Z5DValidator(seed=seed, verbose=verbose)
    z5d_results = z5d.validate_candidates(N, pairs, dps)
    
    # 3. Merge and analyze
    if verbose:
        print("\n[3/3] Merging and computing metrics...", file=sys.stderr)
    
    merged = merge_results(geofac_results, z5d_results, top_k)
    metrics = compute_metrics(merged, top_k)
    
    return merged, metrics


def write_standard_csv(
    path: Path,
    results: List[Dict],
    N: int,
    seed: int,
    dps: int,
    run_id: str
):
    """Write results in standard CSV format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with path.open("w", newline="") as f:
        # Write metadata as comments
        f.write(f"# run_id: {run_id}\n")
        f.write(f"# N: {N}\n")
        f.write(f"# seed: {seed}\n")
        f.write(f"# dps: {dps}\n")
        f.write(f"# timestamp: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"# schema_version: {z_shared.SCHEMA_VERSION}\n")
        
        # Write data
        writer = csv.DictWriter(f, fieldnames=[
            "run_id", "N", "seed", "dps", "p", "q",
            "resonance_rank", "resonance_score",
            "z5d_rank", "z5d_score",
            "error", "is_factor", "agree",
        ])
        writer.writeheader()
        
        for r in results:
            writer.writerow({
                "run_id": run_id,
                "N": N,
                "seed": seed,
                "dps": dps,
                "p": r["p"],
                "q": r["q"],
                "resonance_rank": r["resonance_rank"],
                "resonance_score": r["resonance_score"],
                "z5d_rank": r["z5d_rank"],
                "z5d_score": r["z5d_score"],
                "error": r["error"],
                "is_factor": r["is_factor"],
                "agree": r["agree"],
            })


def main():
    parser = argparse.ArgumentParser(
        description="Cross-validate Geofac and Z5D on semiprimes"
    )
    parser.add_argument(
        "N",
        type=int,
        nargs="+",
        help="Target semiprime(s) to analyze"
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=1000,
        help="Number of candidates to generate (default: 1000)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Top-K threshold for agreement (default: 10)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--dps",
        type=int,
        help="Decimal precision (auto-computed if omitted)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("../artifacts/outputs"),
        help="Output directory (default: ../artifacts/outputs)"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=f"crosscheck_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        help="Run identifier"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Initialize
    z_shared.initialize(seed=args.seed)
    
    # Process each N
    all_results = []
    all_metrics = {}
    
    for N in args.N:
        dps = args.dps if args.dps else z_shared.get_required_precision(N)
        
        merged, metrics = run_crosscheck(
            N=N,
            num_candidates=args.candidates,
            seed=args.seed,
            dps=dps,
            top_k=args.top_k,
            verbose=args.verbose
        )
        
        all_results.extend(merged)
        all_metrics[N] = metrics
        
        # Report metrics
        print(f"\n{'='*80}")
        print(f"Results for N={N}")
        print(f"{'='*80}")
        print(f"Total pairs:          {metrics['total_pairs']}")
        print(f"Agreement rate:       {metrics['agreement_rate']:.3f}")
        print(f"Jaccard index:        {metrics['jaccard_index']:.3f}")
        print(f"Spearman correlation: {metrics['spearman_correlation']:.3f}")
        print(f"True factors found:   {metrics['true_factors_found']}")
        
        if metrics['true_factors_found'] > 0:
            print("\nTrue factors:")
            for tf in metrics['true_factors']:
                print(f"  {tf['p']} × {tf['q']}: "
                      f"Geofac rank {tf['resonance_rank']}, "
                      f"Z5D rank {tf['z5d_rank']}")
    
    # Write outputs
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # CSV
    csv_path = output_dir / f"{args.run_id}.csv"
    write_standard_csv(csv_path, all_results, args.N[0], args.seed, dps, args.run_id)
    print(f"\n✓ Wrote results to: {csv_path}")
    
    # Metrics JSON
    metrics_path = output_dir / f"{args.run_id}_metrics.json"
    with metrics_path.open("w") as f:
        json.dump({
            "run_id": args.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "seed": args.seed,
            "top_k": args.top_k,
            "metrics_by_n": {str(k): v for k, v in all_metrics.items()},
        }, f, indent=2)
    print(f"✓ Wrote metrics to: {metrics_path}")


if __name__ == "__main__":
    main()
