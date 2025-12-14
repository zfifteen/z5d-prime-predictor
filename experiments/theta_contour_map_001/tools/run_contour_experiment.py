#!/usr/bin/env python3
"""
Master script to run the theta contour map visualization experiment.

This script orchestrates the complete experiment pipeline:
1. Generate contour maps for all validation gate scales (log₁₀n = 14-18)
2. Save surface data as JSON
3. Generate plots (if matplotlib available)
4. Create multi-scale summary analysis

Usage:
    python run_contour_experiment.py --test          # Quick test with lower resolution
    python run_contour_experiment.py --full          # Full experiment with high resolution
    python run_contour_experiment.py --data-only     # Only save JSON data, skip plots
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List


class ContourExperimentRunner:
    """Orchestrates the theta contour map experiment."""
    
    def __init__(self, base_dir: Path, test_mode: bool = False):
        self.base_dir = base_dir
        self.scripts_dir = base_dir / 'tools'
        self.artifacts_dir = base_dir / 'artifacts'
        self.test_mode = test_mode
        
        # Output directories
        self.data_dir = self.artifacts_dir / 'contour_data'
        self.plots_dir = self.artifacts_dir / 'plots'
        
        # Scales to process (validation gate scales)
        self.log10n_values = [14, 15, 16, 17, 18]
        
        # Resolution settings
        self.resolution = 50 if test_mode else 100
    
    def run_command(self, cmd: List[str], description: str) -> bool:
        """Run a command and report success/failure."""
        print(f"\n{'='*60}")
        print(f"Step: {description}")
        print(f"Command: {' '.join(str(c) for c in cmd)}")
        print(f"{'='*60}\n")
        
        try:
            subprocess.run(cmd, check=True, text=True)
            print(f"\n✓ {description} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n✗ {description} failed with exit code {e.returncode}", file=sys.stderr)
            return False
    
    def step_generate_data(self) -> bool:
        """Step 1: Generate contour surface data for all scales."""
        cmd = [
            sys.executable,
            str(self.scripts_dir / 'generate_contour_map.py'),
            '--all-scales',
            '--save-data',
            '--output', str(self.data_dir / 'surface.json'),  # Base path
            '--resolution', str(self.resolution)
        ]
        return self.run_command(cmd, 'Generate contour surface data')
    
    def step_generate_plots(self) -> bool:
        """Step 2: Generate contour plots for all scales."""
        cmd = [
            sys.executable,
            str(self.scripts_dir / 'generate_contour_map.py'),
            '--all-scales',
            '--output', str(self.plots_dir / 'contour.png'),  # Base path
            '--resolution', str(self.resolution)
        ]
        return self.run_command(cmd, 'Generate contour plots')
    
    def step_generate_summary_report(self) -> bool:
        """Step 3: Generate markdown summary report."""
        try:
            import json
            
            summary_path = self.data_dir / 'multi_scale_summary.json'
            if not summary_path.exists():
                print(f"Warning: Summary file not found at {summary_path}", file=sys.stderr)
                return True  # Not a fatal error
            
            with summary_path.open('r') as f:
                summary = json.load(f)
            
            # Generate markdown report
            report_path = self.base_dir / 'docs' / 'EXPERIMENT_SUMMARY.md'
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with report_path.open('w') as f:
                f.write("# Theta Contour Map Experiment Summary\n\n")
                f.write(f"**Generated**: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"**Mode**: {'Test' if self.test_mode else 'Full'}\n")
                f.write(f"**Resolution**: {self.resolution}×{self.resolution}\n\n")
                
                f.write("## Results\n\n")
                f.write("### Optimal θ Drift Across Scales\n\n")
                f.write("| log₁₀(n) | θ Drift from 0.525 | Optimal k | Min Error | φ-Alignment |\n")
                f.write("|----------|-------------------|-----------|-----------|-------------|\n")
                
                for i, scale in enumerate(summary['scales']):
                    drift = summary['optimal_theta_drift'][i]
                    k = summary['optimal_k'][i]
                    err = summary['min_error'][i]
                    phi = summary['phi_alignment_score'][i]
                    f.write(f"| {scale} | {drift:+.6f} | {k:.4f} | {err:.6f} | {phi:.4f} |\n")
                
                f.write("\n### Interpretation\n\n")
                
                # Analyze drift pattern
                drifts = summary['optimal_theta_drift']
                drift_trend = "increasing" if drifts[-1] > drifts[0] else "decreasing"
                drift_range = max(drifts) - min(drifts)
                
                f.write(f"- **θ Drift**: {drift_trend} trend across scales ")
                f.write(f"(range: {drift_range:.6f})\n")
                
                if drift_range > 0.001:
                    f.write("  - Suggests scale-coupled bias correction may be beneficial\n")
                else:
                    f.write("  - Drift is minimal; θ = 0.525 appears stable across scales\n")
                
                # Analyze φ-alignment
                avg_phi = sum(summary['phi_alignment_score']) / len(summary['phi_alignment_score'])
                f.write(f"- **φ-Alignment**: Average score = {avg_phi:.4f}\n")
                if avg_phi > 0.5:
                    f.write("  - High alignment suggests φ-related harmonics in error structure\n")
                else:
                    f.write("  - Moderate alignment; further investigation recommended\n")
                
                f.write("\n## Artifacts\n\n")
                f.write("### Data Files\n")
                for scale in self.log10n_values:
                    f.write(f"- `artifacts/contour_data/surface_log{scale}.json`\n")
                f.write("- `artifacts/contour_data/multi_scale_summary.json`\n")
                
                f.write("\n### Plot Files\n")
                for scale in self.log10n_values:
                    f.write(f"- `artifacts/plots/contour_log{scale}.png`\n")
                
                f.write("\n## Methodology\n\n")
                f.write("This experiment scans the θ-k parameter space:\n\n")
                f.write("- **θ range**: 0.525 ± 0.06 (centered on Stadlmann's optimal)\n")
                f.write("- **k range**: [0.05, 1.0]\n")
                f.write("- **Scales**: log₁₀(n) ∈ {14, 15, 16, 17, 18}\n")
                f.write("- **Error model**: Mock θ′(n,k) error function\n\n")
                f.write("### Hook Your Real Error Function\n\n")
                f.write("To use actual Z5D predictions:\n\n")
                f.write("```python\n")
                f.write("# In generate_contour_map.py, replace theta_prime_error_mock with:\n")
                f.write("def theta_prime_error_real(theta, k, log10n):\n")
                f.write("    # Your vectorized_z5d_prime benchmark implementation\n")
                f.write("    pass\n")
                f.write("```\n")
                
                f.write("\n---\n")
                f.write("\n*Report generated by run_contour_experiment.py*\n")
            
            print(f"Saved summary report to {report_path}")
            return True
            
        except Exception as e:
            print(f"Error generating summary report: {e}", file=sys.stderr)
            return False
    
    def run_experiment(self, data_only: bool = False):
        """Run the complete experiment pipeline."""
        print(f"\n{'#'*60}")
        print(f"# Theta Contour Map Visualization Experiment")
        print(f"# Mode: {'TEST' if self.test_mode else 'FULL'}")
        print(f"# Resolution: {self.resolution}×{self.resolution}")
        print(f"# Started: {datetime.now(timezone.utc).isoformat()}")
        print(f"{'#'*60}\n")
        
        steps = [
            (self.step_generate_data, 'Generate surface data'),
        ]
        
        if not data_only:
            steps.append((self.step_generate_plots, 'Generate plots'))
        
        steps.append((self.step_generate_summary_report, 'Generate summary report'))
        
        for i, (step_func, step_name) in enumerate(steps, 1):
            print(f"\n\n{'='*60}")
            print(f"PIPELINE STEP {i}/{len(steps)}: {step_name}")
            print(f"{'='*60}")
            
            success = step_func()
            if not success:
                print(f"\n\n✗ Experiment failed at step {i}", file=sys.stderr)
                return 1
        
        print(f"\n\n{'#'*60}")
        print(f"# EXPERIMENT COMPLETED SUCCESSFULLY")
        print(f"# Finished: {datetime.now(timezone.utc).isoformat()}")
        print(f"#")
        print(f"# Results:")
        print(f"#   - Data: {self.data_dir}/")
        if not data_only:
            print(f"#   - Plots: {self.plots_dir}/")
        print(f"#   - Summary: {self.base_dir / 'docs' / 'EXPERIMENT_SUMMARY.md'}")
        print(f"{'#'*60}\n")
        
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Run theta contour map visualization experiment'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (lower resolution, faster)'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full experiment (high resolution)'
    )
    parser.add_argument(
        '--data-only',
        action='store_true',
        help='Only generate JSON data, skip plotting'
    )
    
    args = parser.parse_args()
    
    # Find experiment base directory
    script_path = Path(__file__).resolve()
    base_dir = script_path.parent.parent
    
    # Determine mode
    test_mode = args.test and not args.full
    
    # Run experiment
    runner = ContourExperimentRunner(base_dir, test_mode)
    return runner.run_experiment(data_only=args.data_only)


if __name__ == '__main__':
    sys.exit(main())
