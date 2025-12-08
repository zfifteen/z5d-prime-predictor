#!/usr/bin/env python3
"""
Contour Map Visualization for θ′(n,k) Error Landscape

Generates filled contour maps of the error surface near Stadlmann's θ≈0.525,
exposing ridges/valleys that may align with φ-related (golden ratio) harmonics.

This script:
    - Scans a grid θ ∈ [0.525±0.06], k ∈ [0.05, 1.0]
    - Samples log₁₀(n) ∈ {14, 15, 16, 17, 18} (validation gate scales)
    - Plots filled contours of the error surface
    - Uses a placeholder error model; swap in real vectorized_z5d_prime benchmark

Usage:
    python generate_contour_map.py --output ../artifacts/plots/contour_log14.png --log10n 14
    python generate_contour_map.py --output ../artifacts/contour_data/surface_log14.json --log10n 14 --save-data
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np

# Optional matplotlib import - we'll check availability
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for server environments
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# Mathematical constants from z_framework_params.h
# Golden ratio φ = (1 + √5) / 2 with high precision
PHI = (1 + np.sqrt(5)) / 2
STADLMANN_THETA = 0.525  # Stadlmann's θ approximation

# Ground truth primes for specific powers of 10
KNOWN_PRIMES = {
    10**1: 29,
    10**2: 541,
    10**3: 7919,
    10**4: 104729,
    10**5: 1299709,
    10**6: 15485863,
    10**7: 179424673,
    10**8: 2038074743,
    10**9: 22801763489,
    10**10: 252097800623,
    10**11: 2760727302517,
    10**12: 29996224275833,
    10**13: 323780508946331,
    10**14: 3475385758524527,
    10**15: 37124508045065437,
    10**16: 394906913903735329,
    10**17: 4185296581467695669,
    10**18: 44211790234832169331,
}


def theta_prime_error_mock(theta: np.ndarray, k: np.ndarray, log10n: float) -> np.ndarray:
    """
    Mock θ′(n,k) error model for visualization.
    
    This is a placeholder that generates plausible error surfaces.
    Replace with real vectorized_z5d_prime benchmark for true maps.
    
    The mock model incorporates:
    - Distance from Stadlmann's optimal θ≈0.525
    - φ-related harmonic structure (to test for bias detection)
    - Scale-dependent (log₁₀n) variations
    - k-dependent modulation
    
    Args:
        theta: 2D array of θ values (grid)
        k: 2D array of k values (grid)
        log10n: log₁₀(n) scale parameter (14-18)
    
    Returns:
        2D array of error values (smaller = better prediction)
    """
    # Base error: quadratic distance from optimal θ
    optimal_theta = STADLMANN_THETA
    base_error = (theta - optimal_theta) ** 2
    
    # Scale-dependent shift in optimal θ (simulates scale coupling)
    scale_shift = 0.002 * (log10n - 16)  # Shift relative to center scale
    adjusted_theta = theta - scale_shift
    scale_error = (adjusted_theta - optimal_theta) ** 2
    
    # φ-related harmonic structure
    # Creates periodic bands that may align with golden ratio harmonics
    phi_harmonic = 0.1 * np.sin(2 * np.pi * (theta - optimal_theta) / (1 / PHI))
    
    # k-dependent modulation
    # Creates valleys/ridges in the k dimension
    k_modulation = 0.05 * np.cos(np.pi * k / 0.5) * np.exp(-((theta - optimal_theta) ** 2) / 0.01)
    
    # Scale-dependent amplitude of harmonics
    harmonic_amplitude = 1 + 0.1 * (log10n - 14) / 4  # Grows slightly with scale
    
    # Combined error surface
    error = (
        0.5 * base_error +
        0.3 * scale_error +
        phi_harmonic * harmonic_amplitude +
        k_modulation
    )
    
    # Add small noise for realism
    rng = np.random.default_rng(42 + int(log10n))
    noise = 0.005 * rng.standard_normal(theta.shape)
    
    # Ensure positive error values
    error = np.abs(error + noise)
    
    return error


def vectorized_z5d_prime(n: float, theta: np.ndarray) -> np.ndarray:
    """
    Vectorized numpy implementation of the z5d prime predictor.
    'n' is a scalar (e.g., 10**log10n), 'theta' is a numpy array.
    
    P_n ≈ n (ln n + ln ln n - 1 + (ln ln n - 2) / ln n - (ln ln n)^2 / (2 (ln n)^2) + ... )
    For simplicity, using PNT 2nd order approximation plus theta adjustment.
    """
    log_n = np.log(n)
    log_log_n = np.log(log_n)
    
    # PNT 2nd order (simplified for primary terms)
    # This is a common approximation, not the full Riemann R function.
    # The form used in repro_z5d_origin.py is a simplified PNT with a theta adjustment.
    # We will use the formula from repro_z5d_origin.py.
    
    base_prediction = n * (log_n + log_log_n - 1)
    
    # Apply theta adjustment as observed in z5d approaches
    # This simplified model uses theta directly as a coefficient to an adjustment term.
    adjustment = theta * (n / log_n) # This is a conceptual integration of theta
    
    return base_prediction + adjustment


def theta_prime_error_real(theta: np.ndarray, k: np.ndarray, log10n: float) -> np.ndarray:
    """
    Real error model based on vectorized_z5d_prime using known ground truth primes.
    
    Args:
        theta: 2D array of θ values (grid)
        k: 2D array of k values (grid) - NOTE: This parameter is ignored by z5d.
        log10n: log₁₀(n) scale parameter
    
    Returns:
        2D array of absolute error values (predicted - actual)
    """
    n_val = 10**log10n
    
    actual_prime = KNOWN_PRIMES.get(int(n_val))
    if actual_prime is None:
        # Fallback to float key if int not found (for intermediate log10n values perhaps)
        actual_prime = KNOWN_PRIMES.get(n_val)

    if actual_prime is None:
        raise ValueError(f"Ground truth prime for n={n_val} (log₁₀n={log10n}) is not available in KNOWN_PRIMES.")

    # Reshape theta_grid to match expected input for vectorized_z5d_prime
    # We expect theta to be a 2D array, and vectorized_z5d_prime expects an array for theta
    # where n is a scalar. So we pass n and the theta_grid directly.
    predicted_primes = vectorized_z5d_prime(n_val, theta)
    
    # Return the absolute error. We want to minimize this.
    error = np.abs(predicted_primes - actual_prime)
    
    return error


def generate_theta_k_grid(
    theta_center: float = STADLMANN_THETA,
    theta_delta: float = 0.06,
    k_min: float = 0.05,
    k_max: float = 1.0,
    theta_resolution: int = 100,
    k_resolution: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate 2D grid of (θ, k) values for contour plotting.
    
    Args:
        theta_center: Center θ value (default: Stadlmann's 0.525)
        theta_delta: Range ±delta around center
        k_min: Minimum k value
        k_max: Maximum k value
        theta_resolution: Number of θ points
        k_resolution: Number of k points
    
    Returns:
        Tuple of (theta_grid, k_grid) as 2D arrays
    """
    theta_values = np.linspace(
        theta_center - theta_delta,
        theta_center + theta_delta,
        theta_resolution
    )
    k_values = np.linspace(k_min, k_max, k_resolution)
    
    return np.meshgrid(theta_values, k_values)


def compute_error_surface(
    theta_grid: np.ndarray,
    k_grid: np.ndarray,
    log10n: float,
    error_func=None
) -> np.ndarray:
    """
    Compute error surface for given grid and scale.
    
    Args:
        theta_grid: 2D array of θ values
        k_grid: 2D array of k values
        log10n: log₁₀(n) scale parameter
        error_func: Custom error function (uses mock if None)
    
    Returns:
        2D array of error values
    """
    if error_func is None:
        error_func = theta_prime_error_real
    
    return error_func(theta_grid, k_grid, log10n)


def plot_contour_map(
    theta_grid: np.ndarray,
    k_grid: np.ndarray,
    error_surface: np.ndarray,
    log10n: float,
    output_path: Path,
    title: str = None,
    show_phi_lines: bool = True
) -> None:
    """
    Generate and save filled contour plot of error surface.
    
    Args:
        theta_grid: 2D array of θ values
        k_grid: 2D array of k values
        error_surface: 2D array of error values
        log10n: log₁₀(n) scale for labeling
        output_path: Path to save the plot
        title: Custom title (auto-generated if None)
        show_phi_lines: Whether to show φ-related reference lines
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create filled contour plot
    levels = 20  # Number of contour levels
    contour = ax.contourf(
        theta_grid, k_grid, error_surface,
        levels=levels,
        cmap='viridis'
    )
    
    # Add contour lines for clarity
    ax.contour(
        theta_grid, k_grid, error_surface,
        levels=levels,
        colors='white',
        linewidths=0.3,
        alpha=0.5
    )
    
    # Colorbar
    fig.colorbar(contour, ax=ax, label='θ′(n,k) Error')
    
    # Reference lines for φ-related harmonics
    if show_phi_lines:
        # Stadlmann's optimal θ
        ax.axvline(x=STADLMANN_THETA, color='red', linestyle='--', 
                   linewidth=1.5, alpha=0.8, label=f'θ = {STADLMANN_THETA}')
        
        # φ-related offsets
        phi_offsets = [1/PHI**2, 1/PHI, 1.0]  # ≈0.382, ≈0.618, 1.0
        for offset in phi_offsets:
            scaled_offset = offset * 0.1  # Scale to θ range
            ax.axvline(x=STADLMANN_THETA + scaled_offset, color='gold', 
                       linestyle=':', linewidth=1, alpha=0.6)
            ax.axvline(x=STADLMANN_THETA - scaled_offset, color='gold', 
                       linestyle=':', linewidth=1, alpha=0.6)
        
        ax.legend(loc='upper right')
    
    # Labels and title
    ax.set_xlabel('θ (theta parameter)', fontsize=12)
    ax.set_ylabel('k (geodesic exponent)', fontsize=12)
    
    if title is None:
        title = f"θ′(n,k) Error Landscape at log₁₀(n) = {log10n}"
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add annotation about φ-lines
    if show_phi_lines:
        ax.text(0.02, 0.02, 'Gold lines: φ-related harmonics',
                transform=ax.transAxes, fontsize=8, color='gold',
                verticalalignment='bottom')
    
    # Tight layout and save
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Saved contour plot to {output_path}")


def save_surface_data(
    theta_grid: np.ndarray,
    k_grid: np.ndarray,
    error_surface: np.ndarray,
    log10n: float,
    output_path: Path,
    metadata: Dict[str, Any] = None
) -> None:
    """
    Save error surface data to JSON for later analysis.
    
    Args:
        theta_grid: 2D array of θ values
        k_grid: 2D array of k values
        error_surface: 2D array of error values
        log10n: log₁₀(n) scale
        output_path: Path to save JSON data
        metadata: Additional metadata to include
    """
    data = {
        '_metadata': {
            'log10n': log10n,
            'theta_min': float(theta_grid.min()),
            'theta_max': float(theta_grid.max()),
            'k_min': float(k_grid.min()),
            'k_max': float(k_grid.max()),
            'theta_resolution': theta_grid.shape[1],
            'k_resolution': theta_grid.shape[0],
            'stadlmann_theta': STADLMANN_THETA,
            'phi': PHI,
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'error_model': metadata.get('error_model', 'mock') if metadata else 'mock'
        },
        'theta': theta_grid.tolist(),
        'k': k_grid.tolist(),
        'error': error_surface.tolist(),
        'statistics': {
            'error_min': float(error_surface.min()),
            'error_max': float(error_surface.max()),
            'error_mean': float(error_surface.mean()),
            'error_std': float(error_surface.std()),
            'optimal_theta': float(theta_grid.flat[error_surface.argmin()]),
            'optimal_k': float(k_grid.flat[error_surface.argmin()])
        }
    }
    
    if metadata:
        data['_metadata'].update(metadata)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved surface data to {output_path}")


def generate_multi_scale_summary(
    log10n_values: list = None,
    theta_center: float = STADLMANN_THETA,
    theta_delta: float = 0.06,
    output_dir: Path = None
) -> Dict[str, Any]:
    """
    Generate summary statistics across multiple scales.
    
    Args:
        log10n_values: List of log₁₀(n) values to analyze
        theta_center: Center θ value
        theta_delta: Range ±delta around center
        output_dir: Directory for output files
    
    Returns:
        Dictionary with summary statistics
    """
    if log10n_values is None:
        log10n_values = [14, 15, 16, 17, 18]
    
    summary = {
        'scales': [],
        'optimal_theta_drift': [],
        'optimal_k': [],
        'min_error': [],
        'phi_alignment_score': []
    }
    
    for log10n in log10n_values:
        theta_grid, k_grid = generate_theta_k_grid(
            theta_center=theta_center,
            theta_delta=theta_delta
        )
        error_surface = compute_error_surface(theta_grid, k_grid, log10n)
        
        # Find optimal point
        min_idx = error_surface.argmin()
        optimal_theta = theta_grid.flat[min_idx]
        optimal_k = k_grid.flat[min_idx]
        
        # Measure φ-alignment score (how well error minima align with φ-harmonics)
        theta_from_optimal = np.abs(theta_grid - optimal_theta)
        phi_distances = []
        for n in range(1, 5):
            phi_distance = np.abs(theta_from_optimal - 1/(PHI**n) * 0.1)
            phi_distances.append(phi_distance.min())
        phi_alignment = 1.0 / (1.0 + np.mean(phi_distances) * 100)
        
        summary['scales'].append(int(log10n))
        summary['optimal_theta_drift'].append(float(optimal_theta - STADLMANN_THETA))
        summary['optimal_k'].append(float(optimal_k))
        summary['min_error'].append(float(error_surface.min()))
        summary['phi_alignment_score'].append(float(phi_alignment))
    
    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Generate contour maps of θ′(n,k) error landscape'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (PNG/PDF for plots, JSON for data)'
    )
    parser.add_argument(
        '--log10n',
        type=float,
        default=16,
        help='log₁₀(n) scale parameter (default: 16)'
    )
    parser.add_argument(
        '--theta-center',
        type=float,
        default=STADLMANN_THETA,
        help=f'Center θ value (default: {STADLMANN_THETA})'
    )
    parser.add_argument(
        '--theta-delta',
        type=float,
        default=0.06,
        help='θ range ±delta (default: 0.06)'
    )
    parser.add_argument(
        '--k-min',
        type=float,
        default=0.05,
        help='Minimum k value (default: 0.05)'
    )
    parser.add_argument(
        '--k-max',
        type=float,
        default=1.0,
        help='Maximum k value (default: 1.0)'
    )
    parser.add_argument(
        '--resolution',
        type=int,
        default=100,
        help='Grid resolution for both axes (default: 100)'
    )
    parser.add_argument(
        '--save-data',
        action='store_true',
        help='Save surface data as JSON instead of plotting'
    )
    parser.add_argument(
        '--all-scales',
        action='store_true',
        help='Generate for all scales (14-18) and create summary'
    )
    parser.add_argument(
        '--no-phi-lines',
        action='store_true',
        help='Disable φ-related reference lines on plots'
    )
    
    args = parser.parse_args()
    
    # Validate matplotlib availability for plotting
    if not args.save_data and not MATPLOTLIB_AVAILABLE:
        print("ERROR: matplotlib is required for plotting.", file=sys.stderr)
        print("Install with: pip install matplotlib", file=sys.stderr)
        return 1
    
    # Default output path
    if args.output is None:
        base_dir = Path(__file__).parent.parent / 'artifacts'
        if args.save_data:
            args.output = base_dir / 'contour_data' / f'surface_log{int(args.log10n)}.json'
        else:
            args.output = base_dir / 'plots' / f'contour_log{int(args.log10n)}.png'
    
    if args.all_scales:
        # Generate for all validation gate scales
        log10n_values = [14, 15, 16, 17, 18]
        base_dir = args.output.parent
        
        for log10n in log10n_values:
            print(f"\nProcessing log₁₀(n) = {log10n}...")
            
            theta_grid, k_grid = generate_theta_k_grid(
                theta_center=args.theta_center,
                theta_delta=args.theta_delta,
                k_min=args.k_min,
                k_max=args.k_max,
                theta_resolution=args.resolution,
                k_resolution=args.resolution
            )
            
            error_surface = compute_error_surface(theta_grid, k_grid, log10n)
            
            if args.save_data:
                output_path = base_dir / f'surface_log{int(log10n)}.json'
                save_surface_data(theta_grid, k_grid, error_surface, log10n, output_path)
            else:
                output_path = base_dir / f'contour_log{int(log10n)}.png'
                plot_contour_map(
                    theta_grid, k_grid, error_surface, log10n, output_path,
                    show_phi_lines=not args.no_phi_lines
                )
        
        # Generate summary
        summary = generate_multi_scale_summary(log10n_values, args.theta_center, args.theta_delta)
        summary_path = base_dir / 'multi_scale_summary.json'
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open('w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nSaved multi-scale summary to {summary_path}")
        
    else:
        # Single scale
        print(f"Generating error surface for log₁₀(n) = {args.log10n}...")
        
        theta_grid, k_grid = generate_theta_k_grid(
            theta_center=args.theta_center,
            theta_delta=args.theta_delta,
            k_min=args.k_min,
            k_max=args.k_max,
            theta_resolution=args.resolution,
            k_resolution=args.resolution
        )
        
        error_surface = compute_error_surface(theta_grid, k_grid, args.log10n)
        
        print(f"Error surface statistics:")
        print(f"  Min: {error_surface.min():.6f}")
        print(f"  Max: {error_surface.max():.6f}")
        print(f"  Mean: {error_surface.mean():.6f}")
        print(f"  Std: {error_surface.std():.6f}")
        
        if args.save_data:
            save_surface_data(
                theta_grid, k_grid, error_surface, args.log10n, args.output
            )
        else:
            plot_contour_map(
                theta_grid, k_grid, error_surface, args.log10n, args.output,
                show_phi_lines=not args.no_phi_lines
            )
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
