#!/usr/bin/env python3
"""
Z5D Validator Adapter
=====================

Thin adapter that wraps Z5D's factor-ranking logic to validate
Geofac resonance candidates.

Interface:
    validate_candidates(N, pairs, seed, dps) -> List[ValidationResult]

This adapter is deterministic and enforces precision/seed contracts.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

import gmpy2 as gp
import numpy as np

# Add parent dir to path to import z_shared
sys.path.insert(0, str(Path(__file__).parent))
import z_shared


@dataclass
class ValidationResult:
    """Result of validating a candidate pair."""
    p: int
    q: int
    z5d_rank: int
    z5d_score: float
    product: int
    error: float  # |p*q - N|
    is_factor: bool  # True if p*q == N


class Z5DValidator:
    """
    Z5D-based validator for factor pair candidates.
    
    Uses Z5D's geometric ranking to score and rank candidate pairs.
    """
    
    def __init__(self, seed: int = z_shared.SEED_DEFAULT, verbose: bool = False):
        """
        Initialize validator with fixed seed.
        
        Args:
            seed: Random seed for determinism
            verbose: Enable verbose logging
        """
        z_shared.set_seed(seed)
        self.seed = seed
        self.verbose = verbose
        
        if self.verbose:
            z_shared.log_seed_info()
    
    def _compute_z5d_score(self, N: int, p: int, q: int, dps: int) -> float:
        """
        Compute Z5D ranking score for a candidate pair (p, q).
        
        The score combines:
        1. Geometric proximity to √N
        2. Φ-based resonance alignment
        3. Product error |p*q - N|
        
        Higher scores indicate better candidates.
        
        Args:
            N: Target semiprime
            p: First factor candidate
            q: Second factor candidate
            dps: Decimal precision
            
        Returns:
            Score (higher = better)
        """
        z_shared.assert_dps(N, dps)
        
        ctx = z_shared.set_gmpy2_precision(N)
        old_ctx = gp.get_context()
        gp.set_context(ctx)
        try:
            N_mpfr = gp.mpfr(N)
            p_mpfr = gp.mpfr(p)
            q_mpfr = gp.mpfr(q)
            
            # 1. Geometric distance from √N
            sqrt_N = gp.sqrt(N_mpfr)
            geom_p = gp.log(p_mpfr / sqrt_N) if p > 0 else gp.mpfr(100)
            geom_q = gp.log(q_mpfr / sqrt_N) if q > 0 else gp.mpfr(100)
            geom_dist = abs(geom_p) + abs(geom_q)
            
            # 2. Product error
            product = p * q
            product_error = abs(product - N) / N if N > 0 else 1.0
            
            # 3. Φ-resonance (check alignment with golden ratio harmonics)
            phi_score = gp.mpfr(0)
            for harmonic in [1, 2, 3]:
                phase_p = z_shared.dirichlet_phase(N, p, harmonic)
                phase_q = z_shared.dirichlet_phase(N, q, harmonic)
                # Score increases when phases align (small difference)
                phase_diff = abs(phase_p - phase_q)
                phi_score += gp.exp(-phase_diff)
            
            # Combine scores (higher = better)
            # Penalize geometric distance and product error, reward phi resonance
            score = float(
                100.0 * phi_score
                - 10.0 * geom_dist
                - 1000.0 * gp.mpfr(product_error)
            )
            
            return score
        finally:
            gp.set_context(old_ctx)
    
    def validate_candidates(
        self,
        N: int,
        pairs: List[Tuple[int, int]],
        dps: Optional[int] = None
    ) -> List[ValidationResult]:
        """
        Validate and rank a list of candidate factor pairs for N.
        
        Args:
            N: Target semiprime to factor
            pairs: List of (p, q) candidate pairs
            dps: Decimal precision (auto-computed if None)
            
        Returns:
            List of ValidationResult, sorted by rank (best first)
        """
        if dps is None:
            dps = z_shared.get_required_precision(N)
        
        z_shared.assert_dps(N, dps)
        
        if self.verbose:
            z_shared.log_precision_info(N, dps)
            print(f"[Z5D] Validating {len(pairs)} candidates for N={N}", file=sys.stderr)
        
        # Score all pairs
        results = []
        for p, q in pairs:
            score = self._compute_z5d_score(N, p, q, dps)
            product = p * q
            error = abs(product - N)
            is_factor = (product == N)
            
            results.append(ValidationResult(
                p=p,
                q=q,
                z5d_rank=-1,  # Will be set after sorting
                z5d_score=score,
                product=product,
                error=error,
                is_factor=is_factor
            ))
        
        # Sort by score (descending) and assign ranks
        results.sort(key=lambda r: r.z5d_score, reverse=True)
        for rank, result in enumerate(results, start=1):
            result.z5d_rank = rank
        
        if self.verbose:
            top_5 = results[:5]
            print(f"[Z5D] Top 5 candidates:", file=sys.stderr)
            for r in top_5:
                print(f"  Rank {r.z5d_rank}: p={r.p}, q={r.q}, "
                      f"score={r.z5d_score:.3f}, error={r.error}", file=sys.stderr)
        
        return results
    
    def batch_validate(
        self,
        cases: List[Tuple[int, List[Tuple[int, int]]]],
        dps: Optional[int] = None
    ) -> dict:
        """
        Validate multiple N values with their candidate pairs.
        
        Args:
            cases: List of (N, pairs) tuples
            dps: Decimal precision (auto-computed per N if None)
            
        Returns:
            Dictionary mapping N -> List[ValidationResult]
        """
        results_by_n = {}
        
        for N, pairs in cases:
            case_dps = dps if dps is not None else z_shared.get_required_precision(N)
            results = self.validate_candidates(N, pairs, case_dps)
            results_by_n[N] = results
        
        return results_by_n


def validate_candidates(
    N: int,
    pairs: List[Tuple[int, int]],
    seed: int = z_shared.SEED_DEFAULT,
    dps: Optional[int] = None,
    verbose: bool = False
) -> List[ValidationResult]:
    """
    Convenience function for validating candidates.
    
    Args:
        N: Target semiprime
        pairs: List of (p, q) candidate pairs
        seed: Random seed for determinism
        dps: Decimal precision (auto-computed if None)
        verbose: Enable verbose logging
        
    Returns:
        List of ValidationResult, sorted by rank
    """
    validator = Z5DValidator(seed=seed, verbose=verbose)
    return validator.validate_candidates(N, pairs, dps)


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI interface for testing the validator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Z5D Validator: Rank candidate factor pairs"
    )
    parser.add_argument("N", type=int, help="Target semiprime")
    parser.add_argument(
        "--pairs",
        type=str,
        help="Candidate pairs as 'p1,q1;p2,q2;...' (or stdin if omitted)"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dps", type=int, help="Decimal precision (auto if omitted)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Show top K results (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Parse pairs
    if args.pairs:
        pair_strs = args.pairs.split(";")
        pairs = []
        for pair_str in pair_strs:
            p, q = map(int, pair_str.split(","))
            pairs.append((p, q))
    else:
        # Read from stdin
        pairs = []
        print("Enter pairs as 'p,q' (one per line, Ctrl-D to finish):", file=sys.stderr)
        for line in sys.stdin:
            line = line.strip()
            if line:
                p, q = map(int, line.split(","))
                pairs.append((p, q))
    
    if not pairs:
        print("Error: No pairs provided", file=sys.stderr)
        sys.exit(1)
    
    # Validate
    results = validate_candidates(
        args.N,
        pairs,
        seed=args.seed,
        dps=args.dps,
        verbose=args.verbose
    )
    
    # Output top K
    print(f"\nTop {args.top_k} candidates for N={args.N}:")
    print(f"{'Rank':<6} {'p':<20} {'q':<20} {'Score':<12} {'Error':<15} {'Factor?'}")
    print("-" * 90)
    
    for result in results[:args.top_k]:
        is_factor_str = "✓ YES" if result.is_factor else "✗ No"
        print(
            f"{result.z5d_rank:<6} {result.p:<20} {result.q:<20} "
            f"{result.z5d_score:<12.3f} {result.error:<15} {is_factor_str}"
        )
    
    # Report if true factors were found
    true_factors = [r for r in results if r.is_factor]
    if true_factors:
        print(f"\n✓ Found {len(true_factors)} true factor(s)")
        for tf in true_factors:
            print(f"  Rank {tf.z5d_rank}: {tf.p} × {tf.q} = {tf.product}")
    else:
        print("\n✗ No true factors in candidate set")


if __name__ == "__main__":
    main()
