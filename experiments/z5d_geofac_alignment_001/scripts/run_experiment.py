#!/usr/bin/env python3
"""
Master script to run the complete Z5D-Geofac alignment validation experiment.

This script orchestrates the entire experiment pipeline:
1. Generate QMC seeds
2. Run Z5D predictor
3. Run Geofac resonance analysis
4. Compute alignment statistics
5. Generate executive summary report

Usage:
    python run_experiment.py --samples 10000 --test
    python run_experiment.py --samples 200000 --full
"""
import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List


class ExperimentRunner:
    def __init__(self, base_dir: Path, test_mode: bool = False):
        self.base_dir = base_dir
        self.scripts_dir = base_dir / 'scripts'
        self.artifacts_dir = base_dir / 'artifacts'
        self.test_mode = test_mode
        
        self.seed_set_id = 'phi_qmc_001_test' if test_mode else 'phi_qmc_001'
        self.seed_file = self.artifacts_dir / 'seedsets' / f'{self.seed_set_id}.csv'
        self.z5d_file = self.artifacts_dir / 'z5d' / f'peaks_{self.seed_set_id}.jsonl'
        self.geofac_file = self.artifacts_dir / 'geofac' / f'peaks_{self.seed_set_id}.jsonl'
        self.report_file = self.artifacts_dir / 'alignment' / self.seed_set_id / 'overlap_report.json'
    
    def run_command(self, cmd: List[str], description: str) -> bool:
        """Run a command and report success/failure."""
        print(f"\n{'='*60}")
        print(f"Step: {description}")
        print(f"Command: {' '.join(str(c) for c in cmd)}")
        print(f"{'='*60}\n")
        
        try:
            result = subprocess.run(cmd, check=True, text=True)
            print(f"\n✓ {description} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n✗ {description} failed with exit code {e.returncode}", file=sys.stderr)
            return False
    
    def step_generate_seeds(self, num_samples: int) -> bool:
        """Step 1: Generate QMC seeds."""
        cmd = [
            'python3',
            str(self.scripts_dir / 'generate_qmc_seeds.py'),
            '--type', 'sobol',
            '--samples', str(num_samples),
            '--dimensions', '5',
            '--seed', '42',
            '--output', str(self.seed_file),
            '--set-id', self.seed_set_id
        ]
        return self.run_command(cmd, 'Generate QMC seeds')
    
    def step_run_z5d(self, max_samples: int = None) -> bool:
        """Step 2: Run Z5D predictor."""
        cmd = [
            'python3',
            str(self.scripts_dir / 'run_z5d_peaks.py'),
            '--seeds', str(self.seed_file),
            '--output', str(self.z5d_file),
            '--scale-min', '14',
            '--scale-max', '18',
            '--top-k', '2000'
        ]
        if max_samples:
            cmd.extend(['--max-samples', str(max_samples)])
        
        return self.run_command(cmd, 'Run Z5D predictor')
    
    def step_run_geofac(self, max_samples: int = None) -> bool:
        """Step 3: Run Geofac resonance analysis."""
        cmd = [
            'python3',
            str(self.scripts_dir / 'run_geofac_peaks.py'),
            '--seeds', str(self.seed_file),
            '--output', str(self.geofac_file),
            '--scale-min', '14',
            '--scale-max', '18',
            '--top-k', '2000'
        ]
        if max_samples:
            cmd.extend(['--max-samples', str(max_samples)])
        
        return self.run_command(cmd, 'Run Geofac resonance analysis')
    
    def step_compute_alignment(self, bootstrap_samples: int = 1000) -> bool:
        """Step 4: Compute alignment statistics."""
        cmd = [
            'python3',
            str(self.scripts_dir / 'compute_alignment.py'),
            '--z5d', str(self.z5d_file),
            '--geofac', str(self.geofac_file),
            '--output', str(self.report_file),
            '--bootstrap-samples', str(bootstrap_samples)
        ]
        return self.run_command(cmd, 'Compute alignment statistics')
    
    def step_generate_summary(self) -> bool:
        """Step 5: Generate executive summary."""
        cmd = [
            'python3',
            str(self.scripts_dir / 'generate_summary.py'),
            '--report', str(self.report_file),
            '--output', str(self.base_dir / 'docs' / f'EXPERIMENT_SUMMARY_{self.seed_set_id}.md')
        ]
        return self.run_command(cmd, 'Generate executive summary')
    
    def run_full_experiment(self, num_samples: int, max_process_samples: int = None):
        """Run the complete experiment pipeline."""
        print(f"\n{'#'*60}")
        print(f"# Z5D-Geofac Alignment Validation Experiment")
        print(f"# Mode: {'TEST' if self.test_mode else 'FULL'}")
        print(f"# Samples: {num_samples}")
        print(f"# Started: {datetime.now(timezone.utc).isoformat()}")
        print(f"{'#'*60}\n")
        
        steps = [
            (self.step_generate_seeds, [num_samples]),
            (self.step_run_z5d, [max_process_samples]),
            (self.step_run_geofac, [max_process_samples]),
            (self.step_compute_alignment, [100 if self.test_mode else 1000]),
            (self.step_generate_summary, [])
        ]
        
        for i, (step_func, args) in enumerate(steps, 1):
            print(f"\n\n{'='*60}")
            print(f"PIPELINE STEP {i}/{len(steps)}")
            print(f"{'='*60}")
            
            success = step_func(*args)
            if not success:
                print(f"\n\n✗ Experiment failed at step {i}", file=sys.stderr)
                return 1
        
        print(f"\n\n{'#'*60}")
        print(f"# EXPERIMENT COMPLETED SUCCESSFULLY")
        print(f"# Finished: {datetime.now(timezone.utc).isoformat()}")
        print(f"#")
        print(f"# Results:")
        print(f"#   - Seeds: {self.seed_file}")
        print(f"#   - Z5D peaks: {self.z5d_file}")
        print(f"#   - Geofac peaks: {self.geofac_file}")
        print(f"#   - Report: {self.report_file}")
        print(f"#   - Summary: {self.base_dir / 'docs' / f'EXPERIMENT_SUMMARY_{self.seed_set_id}.md'}")
        print(f"{'#'*60}\n")
        
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Run Z5D-Geofac alignment validation experiment'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=10000,
        help='Number of QMC samples to generate (default: 10000)'
    )
    parser.add_argument(
        '--max-process',
        type=int,
        help='Maximum samples to process in Z5D/Geofac (for faster testing)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (fewer bootstrap samples, test suffix)'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full experiment (200k samples, 1000 bootstrap)'
    )
    
    args = parser.parse_args()
    
    # Determine parameters
    if args.full:
        num_samples = 200000
        test_mode = False
    else:
        num_samples = args.samples
        test_mode = args.test
    
    # Find experiment base directory
    script_path = Path(__file__).resolve()
    base_dir = script_path.parent.parent
    
    # Run experiment
    runner = ExperimentRunner(base_dir, test_mode)
    return runner.run_full_experiment(num_samples, args.max_process)


if __name__ == '__main__':
    sys.exit(main())
