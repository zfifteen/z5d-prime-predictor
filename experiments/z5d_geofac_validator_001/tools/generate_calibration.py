#!/usr/bin/env python3
"""
Generate Calibration and Reliability Curves
============================================

Analyzes the agreement between Geofac resonance scores and Z5D validation
to produce calibration curves and reliability metrics.

Output: Calibration data and plots (if matplotlib available)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))
import z_shared


def load_crosscheck_results(csv_path: Path) -> List[Dict]:
    """Load results from standard CSV format."""
    import csv
    
    results = []
    with csv_path.open("r") as f:
        # Skip comment lines
        lines = []
        for line in f:
            if not line.startswith("#"):
                lines.append(line)
        
        # Parse CSV from non-comment lines
        reader = csv.DictReader(lines)
        for row in reader:
            if not row or not row.get("run_id"):
                continue
            
            results.append({
                "p": int(row["p"]),
                "q": int(row["q"]),
                "resonance_rank": int(row["resonance_rank"]) if row["resonance_rank"] else None,
                "resonance_score": float(row["resonance_score"]) if row["resonance_score"] else None,
                "z5d_rank": int(row["z5d_rank"]) if row["z5d_rank"] else None,
                "z5d_score": float(row["z5d_score"]) if row["z5d_score"] else None,
                "error": float(row["error"]),
                "is_factor": row["is_factor"].lower() == "true",
                "agree": row["agree"].lower() == "true",
            })
    
    return results


def compute_calibration_curve(
    results: List[Dict],
    num_bins: int = 10
) -> Dict[str, Any]:
    """
    Compute calibration curve: binned resonance score vs. actual success rate.
    
    "Success" is defined as Z5D agreeing (ranking in top-K).
    
    Args:
        results: List of result dictionaries
        num_bins: Number of bins for calibration curve
        
    Returns:
        Dictionary with calibration data
    """
    # Filter to pairs with both scores
    scored = [
        r for r in results
        if r["resonance_score"] is not None and r["z5d_score"] is not None
    ]
    
    if not scored:
        return {"error": "No scored pairs"}
    
    # Extract scores and agreement
    resonance_scores = np.array([r["resonance_score"] for r in scored])
    agreements = np.array([r["agree"] for r in scored], dtype=float)
    
    # Bin by resonance score
    score_min = resonance_scores.min()
    score_max = resonance_scores.max()
    bin_edges = np.linspace(score_min, score_max, num_bins + 1)
    bin_indices = np.digitize(resonance_scores, bin_edges) - 1
    bin_indices = np.clip(bin_indices, 0, num_bins - 1)
    
    # Compute success rate per bin
    calibration_data = []
    for i in range(num_bins):
        mask = bin_indices == i
        if not mask.any():
            continue
        
        bin_center = (bin_edges[i] + bin_edges[i + 1]) / 2
        bin_count = mask.sum()
        bin_success_rate = agreements[mask].mean()
        
        calibration_data.append({
            "bin_idx": i,
            "bin_center": float(bin_center),
            "bin_min": float(bin_edges[i]),
            "bin_max": float(bin_edges[i + 1]),
            "count": int(bin_count),
            "success_rate": float(bin_success_rate),
        })
    
    return {
        "num_bins": num_bins,
        "total_pairs": len(scored),
        "bins": calibration_data,
    }


def compute_roc_data(results: List[Dict]) -> Dict[str, Any]:
    """
    Compute ROC-style data: resonance score thresholds vs. Z5D agreement rate.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Dictionary with ROC data
    """
    scored = [
        r for r in results
        if r["resonance_score"] is not None and r["z5d_score"] is not None
    ]
    
    if not scored:
        return {"error": "No scored pairs"}
    
    # Sort by resonance score (descending)
    sorted_results = sorted(scored, key=lambda r: r["resonance_score"], reverse=True)
    
    # Compute cumulative agreement rate at different thresholds
    roc_data = []
    for i, threshold_idx in enumerate(range(0, len(sorted_results), max(1, len(sorted_results) // 20))):
        top_k_results = sorted_results[:threshold_idx + 1]
        if not top_k_results:
            continue
        
        agreement_rate = sum(1 for r in top_k_results if r["agree"]) / len(top_k_results)
        threshold_score = sorted_results[threshold_idx]["resonance_score"]
        
        roc_data.append({
            "threshold_idx": threshold_idx,
            "threshold_score": float(threshold_score),
            "top_k": len(top_k_results),
            "agreement_rate": float(agreement_rate),
        })
    
    # Compute AUC (simple trapezoid rule)
    if len(roc_data) > 1:
        x = [d["top_k"] / len(sorted_results) for d in roc_data]
        y = [d["agreement_rate"] for d in roc_data]
        auc = np.trapz(y, x)
    else:
        auc = None
    
    return {
        "total_pairs": len(sorted_results),
        "roc_points": roc_data,
        "auc": float(auc) if auc is not None else None,
    }


def plot_calibration_curve(calibration_data: Dict, output_path: Path):
    """Plot calibration curve (requires matplotlib)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Warning: matplotlib not available, skipping plot", file=sys.stderr)
        return
    
    bins = calibration_data["bins"]
    if not bins:
        print("Warning: No calibration data to plot", file=sys.stderr)
        return
    
    x = [b["bin_center"] for b in bins]
    y = [b["success_rate"] for b in bins]
    counts = [b["count"] for b in bins]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot calibration curve
    ax.scatter(x, y, s=[c * 5 for c in counts], alpha=0.6, label="Observed")
    ax.plot(x, y, "b-", alpha=0.3)
    
    # Plot perfect calibration (diagonal)
    min_score = min(x)
    max_score = max(x)
    ax.plot([min_score, max_score], [0, 1], "r--", label="Perfect calibration")
    
    ax.set_xlabel("Resonance Score (binned)")
    ax.set_ylabel("Z5D Agreement Rate")
    ax.set_title("Calibration Curve: Geofac Resonance vs. Z5D Validation")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved calibration plot to: {output_path}")


def plot_roc_curve(roc_data: Dict, output_path: Path):
    """Plot ROC-style curve (requires matplotlib)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Warning: matplotlib not available, skipping plot", file=sys.stderr)
        return
    
    points = roc_data["roc_points"]
    if not points:
        print("Warning: No ROC data to plot", file=sys.stderr)
        return
    
    x = [p["top_k"] / roc_data["total_pairs"] for p in points]
    y = [p["agreement_rate"] for p in points]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(x, y, "b-", linewidth=2, label=f"ROC (AUC={roc_data['auc']:.3f})")
    ax.plot([0, 1], [0, 1], "r--", alpha=0.5, label="Random")
    
    ax.set_xlabel("Fraction of Top Candidates (by Resonance Score)")
    ax.set_ylabel("Z5D Agreement Rate")
    ax.set_title("ROC-Style Curve: Resonance Threshold vs. Z5D Agreement")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved ROC plot to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate calibration and reliability curves"
    )
    parser.add_argument(
        "results_csv",
        type=Path,
        help="Path to crosscheck results CSV"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("../artifacts/analysis"),
        help="Output directory (default: ../artifacts/analysis)"
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=10,
        help="Number of bins for calibration curve (default: 10)"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate plots (requires matplotlib)"
    )
    
    args = parser.parse_args()
    
    # Load results
    print(f"Loading results from: {args.results_csv}")
    results = load_crosscheck_results(args.results_csv)
    print(f"✓ Loaded {len(results)} pairs")
    
    # Compute calibration curve
    print("\nComputing calibration curve...")
    calibration = compute_calibration_curve(results, args.bins)
    
    if "error" not in calibration:
        print(f"✓ Computed calibration with {len(calibration['bins'])} bins")
        for bin_data in calibration["bins"]:
            print(f"  Bin [{bin_data['bin_min']:.2f}, {bin_data['bin_max']:.2f}]: "
                  f"success_rate={bin_data['success_rate']:.3f} "
                  f"(n={bin_data['count']})")
    else:
        print(f"✗ Error: {calibration['error']}")
    
    # Compute ROC data
    print("\nComputing ROC data...")
    roc = compute_roc_data(results)
    
    if "error" not in roc:
        print(f"✓ Computed ROC with {len(roc['roc_points'])} points")
        print(f"  AUC: {roc['auc']:.3f}")
    else:
        print(f"✗ Error: {roc['error']}")
    
    # Save data
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    run_id = args.results_csv.stem
    
    calibration_path = output_dir / f"{run_id}_calibration.json"
    with calibration_path.open("w") as f:
        json.dump(calibration, f, indent=2)
    print(f"\n✓ Saved calibration data to: {calibration_path}")
    
    roc_path = output_dir / f"{run_id}_roc.json"
    with roc_path.open("w") as f:
        json.dump(roc, f, indent=2)
    print(f"✓ Saved ROC data to: {roc_path}")
    
    # Generate plots if requested
    if args.plot:
        print("\nGenerating plots...")
        plot_calibration_curve(
            calibration,
            output_dir / f"{run_id}_calibration.png"
        )
        plot_roc_curve(
            roc,
            output_dir / f"{run_id}_roc.png"
        )


if __name__ == "__main__":
    main()
