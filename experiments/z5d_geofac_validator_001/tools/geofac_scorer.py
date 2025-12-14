#!/usr/bin/env python3
"""
Geofac Resonance Scorer
========================

Generates and scores candidate factor pairs using geometric/phase resonance.

This module provides resonance-based scoring that Z5D will validate.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

import gmpy2 as gp
import numpy as np

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))
import z_shared


@dataclass
class ResonanceResult:
    """Result of resonance scoring for a candidate pair."""
    p: int
    q: int
    resonance_rank: int
    resonance_score: float
    product: int
    error: float
    is_factor: bool


class GeofacScorer:
    """
    Geofac (Geometric Factor) resonance-based candidate scorer.
    
    Generates candidate pairs near √N using φ-based geometric sampling
    and scores them based on phase resonance.
    """
    
    def __init__(self, seed: int = z_shared.SEED_DEFAULT, verbose: bool = False):
        """
        Initialize scorer with fixed seed.
        
        Args:
            seed: Random seed for determinism
            verbose: Enable verbose logging
        """
        z_shared.set_seed(seed)
        self.seed = seed
        self.verbose = verbose
        self.rng = z_shared.create_rng(seed)
        
        if self.verbose:
            z_shared.log_seed_info()
    
    def generate_candidates(
        self,
        N: int,
        num_candidates: int = 1000,
        window_factor: float = 0.1
    ) -> List[Tuple[int, int]]:
        """
        Generate candidate factor pairs near √N using geometric sampling.
        
        Args:
            N: Target semiprime
            num_candidates: Number of candidates to generate
            window_factor: Sampling window as fraction of √N
            
        Returns:
            List of (p, q) candidate pairs
        """
        if self.verbose:
            print(f"[GEOFAC] Generating {num_candidates} candidates for N={N}", file=sys.stderr)
        
        sqrt_N = int(gp.sqrt(gp.mpz(N)))
        window = int(sqrt_N * window_factor)
        
        candidates = []
        
        # Generate candidates using φ-biased sampling
        for i in range(num_candidates):
            # Use golden ratio to bias sampling
            u = self.rng.random()
            v = self.rng.random()
            
            # Apply φ-transform to create harmonic spacing
            phi_u = float(z_shared.phi_transform(u))
            phi_v = float(z_shared.phi_transform(v))
            
            # Map to window around √N
            offset_p = int((phi_u % 1.0 - 0.5) * 2 * window)
            offset_q = int((phi_v % 1.0 - 0.5) * 2 * window)
            
            p_candidate = sqrt_N + offset_p
            q_candidate = sqrt_N + offset_q
            
            # Ensure positive and odd (except 2)
            if p_candidate < 2:
                p_candidate = 2
            elif p_candidate % 2 == 0:
                p_candidate += 1
            
            if q_candidate < 2:
                q_candidate = 2
            elif q_candidate % 2 == 0:
                q_candidate += 1
            
            candidates.append((p_candidate, q_candidate))
        
        # Add actual √N for reference
        candidates.append((sqrt_N, sqrt_N))
        
        return candidates
    
    def _compute_resonance_score(self, N: int, p: int, q: int, dps: int) -> float:
        """
        Compute resonance score for a candidate pair.
        
        The score is based on:
        1. Phase alignment (Dirichlet-style)
        2. Φ-harmonic resonance
        3. Geometric balance around √N
        
        Higher scores indicate stronger resonance.
        
        Args:
            N: Target semiprime
            p: First factor candidate
            q: Second factor candidate
            dps: Decimal precision
            
        Returns:
            Resonance score (higher = better)
        """
        z_shared.assert_dps(N, dps)
        
        ctx = z_shared.set_gmpy2_precision(N)
        old_ctx = gp.get_context()
        gp.set_context(ctx)
        try:
            N_mpfr = gp.mpfr(N)
            p_mpfr = gp.mpfr(p)
            q_mpfr = gp.mpfr(q)
            sqrt_N = gp.sqrt(N_mpfr)
            
            # 1. Phase resonance across multiple harmonics
            phase_score = gp.mpfr(0)
            for harmonic in [1, 2, 3, 5]:  # Include Fibonacci harmonics
                phase_p = z_shared.dirichlet_phase(N, p, harmonic)
                phase_q = z_shared.dirichlet_phase(N, q, harmonic)
                
                # Resonance when phases are in sync (mod 2π)
                phase_sum = phase_p + phase_q
                phase_alignment = gp.cos(phase_sum)
                phase_score += phase_alignment
            
            # 2. Geometric balance (penalize asymmetry)
            ratio_p = p_mpfr / sqrt_N
            ratio_q = q_mpfr / sqrt_N
            balance = gp.exp(-abs(gp.log(ratio_p / ratio_q)))
            
            # 3. Φ-resonance (golden ratio harmonics)
            phi = z_shared.PHI
            phi_mod_p = gp.fmod(p_mpfr / sqrt_N, phi)
            phi_mod_q = gp.fmod(q_mpfr / sqrt_N, phi)
            phi_alignment = gp.exp(-abs(phi_mod_p - phi_mod_q))
            
            # Combine scores
            score = float(
                10.0 * phase_score
                + 5.0 * balance
                + 3.0 * phi_alignment
            )
            
            return score
        finally:
            gp.set_context(old_ctx)
    
    def score_candidates(
        self,
        N: int,
        pairs: List[Tuple[int, int]],
        dps: Optional[int] = None
    ) -> List[ResonanceResult]:
        """
        Score and rank candidate pairs by resonance.
        
        Args:
            N: Target semiprime
            pairs: List of (p, q) candidate pairs
            dps: Decimal precision (auto-computed if None)
            
        Returns:
            List of ResonanceResult, sorted by rank (best first)
        """
        if dps is None:
            dps = z_shared.get_required_precision(N)
        
        z_shared.assert_dps(N, dps)
        
        if self.verbose:
            z_shared.log_precision_info(N, dps)
            print(f"[GEOFAC] Scoring {len(pairs)} candidates for N={N}", file=sys.stderr)
        
        # Score all pairs
        results = []
        for p, q in pairs:
            score = self._compute_resonance_score(N, p, q, dps)
            product = p * q
            error = abs(product - N)
            is_factor = (product == N)
            
            results.append(ResonanceResult(
                p=p,
                q=q,
                resonance_rank=-1,  # Will be set after sorting
                resonance_score=score,
                product=product,
                error=error,
                is_factor=is_factor
            ))
        
        # Sort by score (descending) and assign ranks
        results.sort(key=lambda r: r.resonance_score, reverse=True)
        for rank, result in enumerate(results, start=1):
            result.resonance_rank = rank
        
        if self.verbose:
            top_5 = results[:5]
            print(f"[GEOFAC] Top 5 by resonance:", file=sys.stderr)
            for r in top_5:
                print(f"  Rank {r.resonance_rank}: p={r.p}, q={r.q}, "
                      f"score={r.resonance_score:.3f}, error={r.error}", file=sys.stderr)
        
        return results


def generate_and_score(
    N: int,
    num_candidates: int = 1000,
    seed: int = z_shared.SEED_DEFAULT,
    dps: Optional[int] = None,
    verbose: bool = False
) -> List[ResonanceResult]:
    """
    Generate and score candidates in one call.
    
    Args:
        N: Target semiprime
        num_candidates: Number of candidates to generate
        seed: Random seed
        dps: Decimal precision (auto-computed if None)
        verbose: Enable verbose logging
        
    Returns:
        List of ResonanceResult, sorted by rank
    """
    scorer = GeofacScorer(seed=seed, verbose=verbose)
    pairs = scorer.generate_candidates(N, num_candidates)
    return scorer.score_candidates(N, pairs, dps)


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI interface for testing the scorer."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Geofac Scorer: Generate and score candidate factor pairs"
    )
    parser.add_argument("N", type=int, help="Target semiprime")
    parser.add_argument(
        "--candidates",
        type=int,
        default=1000,
        help="Number of candidates to generate (default: 1000)"
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
    parser.add_argument(
        "--window",
        type=float,
        default=0.1,
        help="Sampling window factor (default: 0.1)"
    )
    
    args = parser.parse_args()
    
    # Generate and score
    scorer = GeofacScorer(seed=args.seed, verbose=args.verbose)
    pairs = scorer.generate_candidates(
        args.N,
        num_candidates=args.candidates,
        window_factor=args.window
    )
    results = scorer.score_candidates(args.N, pairs, args.dps)
    
    # Output top K
    print(f"\nTop {args.top_k} candidates by resonance for N={args.N}:")
    print(f"{'Rank':<6} {'p':<20} {'q':<20} {'Score':<12} {'Error':<15} {'Factor?'}")
    print("-" * 90)
    
    for result in results[:args.top_k]:
        is_factor_str = "✓ YES" if result.is_factor else "✗ No"
        print(
            f"{result.resonance_rank:<6} {result.p:<20} {result.q:<20} "
            f"{result.resonance_score:<12.3f} {result.error:<15} {is_factor_str}"
        )
    
    # Report if true factors were found
    true_factors = [r for r in results if r.is_factor]
    if true_factors:
        print(f"\n✓ Found {len(true_factors)} true factor(s)")
        for tf in true_factors:
            print(f"  Rank {tf.resonance_rank}: {tf.p} × {tf.q} = {tf.product}")
    else:
        print("\n✗ No true factors in candidate set")


if __name__ == "__main__":
    main()
