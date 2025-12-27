#!/usr/bin/env python3
"""
Main Experiment Runner: Z5D as Geofac Validator
================================================

Orchestrates the complete experiment:
1. Generate test semiprimes
2. Run Geofac scorer
3. Run Z5D validator
4. Compute metrics
5. Generate calibration curves
6. Produce findings report

Usage:
    python run_experiment.py --test          # Quick test
    python run_experiment.py --full          # Full experiment
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))
import z_shared


def generate_test_semiprimes(scale_min: int = 14, scale_max: int = 18, count: int = 5) -> List[Tuple[int, int, int]]:
    """
    Generate test semiprimes in the specified scale range.
    
    Returns:
        List of (N, p, q) tuples where N = p * q
    """
    import gmpy2 as gp
    
    semiprimes = []
    
    for scale in range(scale_min, scale_max + 1):
        for i in range(count // (scale_max - scale_min + 1) + 1):
            # Generate a semiprime near 10^scale
            target = 10 ** scale
            
            # Find primes near sqrt(target)
            sqrt_target = int(gp.sqrt(gp.mpz(target)))
            
            # Offset to create variety
            offset = i * 1000
            p = int(gp.next_prime(sqrt_target + offset))
            q = int(gp.next_prime(p + offset // 2))
            
            N = p * q
            
            # Check if in range
            if 10**scale_min <= N <= 10**(scale_max + 1):
                semiprimes.append((N, p, q))
                
                if len(semiprimes) >= count:
                    return semiprimes
    
    return semiprimes


def run_experiment(
    semiprimes: List[Tuple[int, int, int]],
    num_candidates: int,
    top_k: int,
    seed: int,
    output_dir: Path,
    run_id: str,
    verbose: bool = False
):
    """Run the full experiment."""
    print(f"\n{'='*80}")
    print(f"Experiment: Z5D as Geofac Validator")
    print(f"{'='*80}")
    print(f"Run ID: {run_id}")
    print(f"Semiprimes: {len(semiprimes)}")
    print(f"Candidates per N: {num_candidates}")
    print(f"Top-K: {top_k}")
    print(f"Seed: {seed}")
    print(f"{'='*80}\n")
    
    # Initialize
    z_shared.initialize(seed=seed)
    
    # Extract just the N values for crosscheck
    n_values = [N for N, p, q in semiprimes]
    
    # Run crosscheck
    print("Running crosscheck...")
    crosscheck_cmd = [
        sys.executable,
        str(Path(__file__).parent / "crosscheck.py"),
        *map(str, n_values),
        "--candidates", str(num_candidates),
        "--top-k", str(top_k),
        "--seed", str(seed),
        "--output-dir", str(output_dir / "outputs"),
        "--run-id", run_id,
    ]
    
    if verbose:
        crosscheck_cmd.append("--verbose")
    
    result = subprocess.run(crosscheck_cmd, capture_output=False)
    if result.returncode != 0:
        print(f"✗ Crosscheck failed with code {result.returncode}")
        sys.exit(1)
    
    print("\n✓ Crosscheck completed")
    
    # Generate calibration curves
    print("\nGenerating calibration curves...")
    results_csv = output_dir / "outputs" / f"{run_id}.csv"
    
    if not results_csv.exists():
        print(f"✗ Results CSV not found: {results_csv}")
        sys.exit(1)
    
    calibration_cmd = [
        sys.executable,
        str(Path(__file__).parent / "generate_calibration.py"),
        str(results_csv),
        "--output-dir", str(output_dir / "analysis"),
        "--bins", "10",
        "--plot",
    ]
    
    result = subprocess.run(calibration_cmd, capture_output=False)
    if result.returncode != 0:
        print(f"✗ Calibration generation failed with code {result.returncode}")
        # Don't exit, this is not critical
    else:
        print("✓ Calibration curves generated")
    
    # Load metrics
    metrics_path = output_dir / "outputs" / f"{run_id}_metrics.json"
    with metrics_path.open("r") as f:
        metrics = json.load(f)
    
    return metrics


def generate_findings_report(
    metrics: dict,
    semiprimes: List[Tuple[int, int, int]],
    run_id: str,
    output_path: Path
):
    """Generate FINDINGS.md report."""
    
    # Compute aggregate metrics
    all_metrics = list(metrics["metrics_by_n"].values())
    
    avg_jaccard = sum(m["jaccard_index"] for m in all_metrics) / len(all_metrics)
    avg_agreement = sum(m["agreement_rate"] for m in all_metrics) / len(all_metrics)
    
    # Check if any true factors were found
    total_true_factors = sum(m["true_factors_found"] for m in all_metrics)
    
    # Determine conclusion
    if avg_jaccard >= 0.20 and all(m["jaccard_index"] >= 0.10 for m in all_metrics):
        conclusion = "✓ VALIDATED: Z5D is an effective validator for Geofac candidates"
        status = "PASS"
    else:
        conclusion = "✗ INCONCLUSIVE: Validation criteria not met"
        status = "FAIL"
    
    # Generate report
    report = f"""# FINDINGS: Z5D as Geofac Validator

**Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Run ID**: {run_id}  
**Status**: {status}

## Conclusion

{conclusion}

### Summary Statistics

- **Semiprimes tested**: {len(semiprimes)}
- **Average Jaccard index**: {avg_jaccard:.3f}
- **Average agreement rate**: {avg_agreement:.3f}
- **True factors found**: {total_true_factors}

### Key Findings

1. **Cross-System Agreement**: Z5D and Geofac show {'strong' if avg_agreement > 0.7 else 'moderate' if avg_agreement > 0.4 else 'weak'} agreement (rate={avg_agreement:.3f})

2. **Ranking Overlap**: Jaccard index of {avg_jaccard:.3f} indicates {'significant' if avg_jaccard > 0.3 else 'moderate' if avg_jaccard > 0.15 else 'limited'} overlap in top-K rankings

3. **Validation Utility**: Z5D {'successfully' if avg_jaccard >= 0.20 else 'partially'} validates Geofac resonance scores

## Technical Evidence

### Experimental Configuration

```json
{{
  "run_id": "{run_id}",
  "seed": {metrics["seed"]},
  "top_k": {metrics["top_k"]},
  "scale_range": "10^14 to 10^18",
  "semiprimes_count": {len(semiprimes)},
  "methodology": "Cross-validation with deterministic seed"
}}
```

### Results by Semiprime

"""
    
    for n_str, m in metrics["metrics_by_n"].items():
        report += f"""
#### N = {n_str}

- **Total pairs evaluated**: {m['total_pairs']}
- **Jaccard index**: {m['jaccard_index']:.3f}
- **Agreement rate**: {m['agreement_rate']:.3f}
- **Spearman correlation**: {m['spearman_correlation']:.3f} (p={m['spearman_p_value']:.2e})
- **True factors found**: {m['true_factors_found']}
"""
        
        if m['true_factors_found'] > 0:
            report += "\n**True factors:**\n"
            for tf in m['true_factors']:
                report += f"- {tf['p']} × {tf['q']}: Geofac rank {tf['resonance_rank']}, Z5D rank {tf['z5d_rank']}\n"
    
    report += f"""

### Calibration Analysis

Calibration curves show the relationship between Geofac resonance scores and Z5D validation success rate.

**Interpretation**: 
- Well-calibrated system: observed agreement rate ≈ predicted score
- Over-confident: observed < predicted
- Under-confident: observed > predicted

See: `artifacts/analysis/{run_id}_calibration.json` for detailed data.

### ROC Analysis

ROC-style analysis shows how agreement rate changes with resonance score threshold.

- **AUC interpretation**: Higher AUC indicates better discriminative ability
- AUC = 0.5: random performance
- AUC = 1.0: perfect discrimination

See: `artifacts/analysis/{run_id}_roc.json` for detailed data.

## Methodology

### 1. Candidate Generation (Geofac)

- Generate {metrics['top_k']}+ candidate pairs near √N
- Use φ-biased geometric sampling with Dirichlet phase resonance
- Score based on phase alignment and geometric balance

### 2. Validation (Z5D)

- Apply Z5D ranking to same candidates
- Score based on geometric proximity, φ-harmonics, and product error
- Rank candidates by combined score

### 3. Agreement Analysis

- Compare top-K sets from both systems
- Compute Jaccard index, hit rates, rank correlation
- Generate calibration and ROC curves

### 4. Reproducibility

All operations use:
- **Fixed seed**: {metrics['seed']}
- **Deterministic precision**: Auto-scaled by magnitude
- **Standard schema**: CSV/JSONL with metadata
- **Checksums**: SHA-256 for all artifacts

## Artifacts

```
experiments/z5d_geofac_validator_001/
├── artifacts/
│   ├── outputs/
│   │   ├── {run_id}.csv              # Standard results
│   │   └── {run_id}_metrics.json     # Summary metrics
│   └── analysis/
│       ├── {run_id}_calibration.json # Calibration data
│       ├── {run_id}_calibration.png  # Calibration plot
│       ├── {run_id}_roc.json         # ROC data
│       └── {run_id}_roc.png          # ROC plot
└── docs/
    └── FINDINGS.md                    # This document
```

## Conclusion

{conclusion}

### Recommendation

{'**ACCEPT**: Z5D can be used as a fast validator for Geofac candidates. Agreement is sufficient to reduce false positives without adding classical factoring algorithms.' if status == 'PASS' else '**REVIEW**: Results show limited agreement. Further investigation needed to determine if systems are measuring orthogonal signals or if methodology needs adjustment.'}

### Next Steps

"""
    
    if status == "PASS":
        report += """1. **Production Integration**: Implement Z5D validator in Geofac pipeline
2. **Scaling Study**: Test on larger semiprimes (10^20+)
3. **Optimization**: Tune threshold and top-K parameters
4. **Real RSA Challenges**: Validate on actual RSA challenge numbers
"""
    else:
        report += """1. **Sensitivity Analysis**: Vary top-K and candidate count
2. **Algorithm Tuning**: Adjust scoring functions in both systems
3. **Dataset Expansion**: Test on more semiprimes and scales
4. **Root Cause Analysis**: Investigate sources of disagreement
"""
    
    report += f"""

## References

- Z5D Predictor: `/src/python/z5d_predictor/`
- Shared utilities: `tools/z_shared.py`
- Z5D adapter: `tools/z5d_adapter.py`
- Geofac scorer: `tools/geofac_scorer.py`
- Validation gates: `/docs/VALIDATION_GATES.md`

---

**Generated**: {datetime.now(timezone.utc).isoformat()}
"""
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        f.write(report)
    
    print(f"\n✓ Generated findings report: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run Z5D-Geofac validator experiment"
    )
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--test",
        action="store_true",
        help="Run quick test (5 semiprimes, 500 candidates)"
    )
    mode_group.add_argument(
        "--full",
        action="store_true",
        help="Run full experiment (20 semiprimes, 2000 candidates)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Configure based on mode
    if args.test:
        num_semiprimes = 5
        num_candidates = 500
        top_k = 10
        run_suffix = "test"
    else:  # full
        num_semiprimes = 20
        num_candidates = 2000
        top_k = 20
        run_suffix = "full"
    
    # Generate run ID
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    run_id = f"z5d_validator_{run_suffix}_{timestamp}"
    
    # Output directory
    experiment_root = Path(__file__).parent.parent
    output_dir = experiment_root / "artifacts"
    
    # Generate test semiprimes
    print("Generating test semiprimes...")
    semiprimes = generate_test_semiprimes(
        scale_min=14,
        scale_max=18,
        count=num_semiprimes
    )
    print(f"✓ Generated {len(semiprimes)} semiprimes")
    
    for N, p, q in semiprimes[:5]:  # Show first 5
        print(f"  {N} = {p} × {q} ({len(str(N))} digits)")
    if len(semiprimes) > 5:
        print(f"  ... and {len(semiprimes) - 5} more")
    
    # Run experiment
    metrics = run_experiment(
        semiprimes=semiprimes,
        num_candidates=num_candidates,
        top_k=top_k,
        seed=args.seed,
        output_dir=output_dir,
        run_id=run_id,
        verbose=args.verbose
    )
    
    # Generate findings report
    findings_path = experiment_root / "docs" / "FINDINGS.md"
    generate_findings_report(
        metrics=metrics,
        semiprimes=semiprimes,
        run_id=run_id,
        output_path=findings_path
    )
    
    print(f"\n{'='*80}")
    print("Experiment completed successfully!")
    print(f"{'='*80}")
    print(f"\nResults:")
    print(f"  - CSV: {output_dir / 'outputs' / f'{run_id}.csv'}")
    print(f"  - Metrics: {output_dir / 'outputs' / f'{run_id}_metrics.json'}")
    print(f"  - Calibration: {output_dir / 'analysis' / f'{run_id}_calibration.json'}")
    print(f"  - ROC: {output_dir / 'analysis' / f'{run_id}_roc.json'}")
    print(f"  - Findings: {findings_path}")
    print()


if __name__ == "__main__":
    main()
