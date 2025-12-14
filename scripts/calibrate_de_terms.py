#!/usr/bin/env python3
"""
Calibrate the Z5D d/e-term coefficients (c, kappa_star) against ground truth.

Default dataset: data/KNOWN_PRIMES.md (n, p_n for 10^0..10^18).
Outputs:
  - CSV of per-n errors  -> scripts/output/calibration_errors.csv
  - CSV of comparison runs (optional) -> scripts/output/calibration_comparison.csv
Printed:
  - Best (c, kappa_star) by max-relative-error (ppm) plus RMS ppm.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

# Add repository src/python to path for local imports
REPO_ROOT = Path(__file__).resolve().parent.parent
PY_SRC = REPO_ROOT / "src" / "python"
if str(PY_SRC) not in sys.path:
    sys.path.insert(0, str(PY_SRC))

from z5d_predictor import closed_form_estimate  # type: ignore

DEFAULT_OUTPUT_DIR = REPO_ROOT / "scripts" / "output"
DEFAULT_DATA_MD = REPO_ROOT / "data" / "KNOWN_PRIMES.md"


@dataclass
class EvalResult:
    c: float
    kappa_star: float
    max_rel_ppm: float
    rms_ppm: float


def parse_int(s: str) -> int:
    return int(s.replace(",", "").replace("_", "").strip())


def load_known_primes_md(path: Path) -> List[Tuple[int, int]]:
    rows: List[Tuple[int, int]] = []
    with path.open() as f:
        for line in f:
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) < 3:
                continue
            # Expect: Index | Scientific | Prime | Source
            try:
                n = parse_int(parts[0])
                p_n = parse_int(parts[2])
            except ValueError:
                continue
            rows.append((n, p_n))
    if not rows:
        raise ValueError(f"No rows parsed from {path}")
    return rows


def load_csv_pairs(path: Path) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    with path.open() as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not {"n", "p_n"}.issubset(reader.fieldnames):
            raise ValueError("CSV must have headers: n,p_n")
        for row in reader:
            out.append((parse_int(row["n"]), parse_int(row["p_n"])))
    if not out:
        raise ValueError(f"No rows parsed from {path}")
    return out


def eval_coeffs(
    data: Sequence[Tuple[int, int]],
    c: float,
    kappa_star: float,
) -> Tuple[EvalResult, List[Tuple[int, int, int, float, float]]]:
    """
    Returns EvalResult and per-row details: (n, p_n, est, abs_err, rel_ppm)
    """
    per_rows: List[Tuple[int, int, int, float, float]] = []
    max_rel = -math.inf
    sum_sq = 0.0
    last_est = -math.inf

    for n, p_n in data:
        est = int(closed_form_estimate(n, c=c, kappa_star=kappa_star))
        abs_err = est - p_n
        rel_ppm = abs(abs_err) / p_n * 1e6

        # Monotonicity check (estimates should not decrease with n)
        if est < last_est:
            return EvalResult(c, kappa_star, math.inf, math.inf), []
        last_est = est

        per_rows.append((n, p_n, est, abs_err, rel_ppm))
        max_rel = max(max_rel, rel_ppm)
        sum_sq += rel_ppm * rel_ppm

    rms = math.sqrt(sum_sq / len(data))
    return EvalResult(c, kappa_star, max_rel, rms), per_rows


def linspace(start: float, stop: float, num: int) -> Iterable[float]:
    if num == 1:
        yield start
        return
    step = (stop - start) / (num - 1)
    for i in range(num):
        yield start + i * step


def grid_search(
    data: Sequence[Tuple[int, int]],
    c_bounds: Tuple[float, float],
    k_bounds: Tuple[float, float],
    c_steps: int,
    k_steps: int,
) -> EvalResult:
    best = EvalResult(0.0, 0.0, math.inf, math.inf)
    for c in linspace(*c_bounds, c_steps):
        for kappa in linspace(*k_bounds, k_steps):
            res, _ = eval_coeffs(data, c, kappa)
            if not math.isfinite(res.max_rel_ppm):
                continue
            if res.max_rel_ppm < best.max_rel_ppm:
                best = res
    return best


def refine_search(
    data: Sequence[Tuple[int, int]],
    best: EvalResult,
    c_span: float,
    k_span: float,
    steps: int,
) -> EvalResult:
    c_min = best.c - c_span
    c_max = best.c + c_span
    k_min = best.kappa_star - k_span
    k_max = best.kappa_star + k_span
    return grid_search(data, (c_min, c_max), (k_min, k_max), steps, steps)


def write_errors_csv(path: Path, per_rows: List[Tuple[int, int, int, float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["n", "p_n", "estimate", "abs_error", "rel_error_ppm"])
        for row in per_rows:
            writer.writerow(row)


def write_comparison_csv(path: Path, rows: List[EvalResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["c", "kappa_star", "max_rel_ppm", "rms_ppm"])
        for r in rows:
            writer.writerow([r.c, r.kappa_star, r.max_rel_ppm, r.rms_ppm])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA_MD, help="Dataset file (md table or CSV with n,p_n).")
    ap.add_argument("--extra-csv", type=Path, help="Optional additional CSV with n,p_n to append.")
    ap.add_argument(
        "--min-n",
        type=int,
        default=10_000,
        help="Minimum n supported. If the dataset contains smaller n and --filter-below-min is not set, the run exits.",
    )
    ap.add_argument(
        "--filter-below-min",
        action="store_true",
        help="Drop rows with n < --min-n instead of exiting.",
    )
    ap.add_argument("--c-bounds", type=float, nargs=2, default=[-0.01, 0.01], metavar=("C_MIN", "C_MAX"))
    ap.add_argument("--k-bounds", type=float, nargs=2, default=[0.0, 0.2], metavar=("K_MIN", "K_MAX"))
    ap.add_argument("--c-steps", type=int, default=25, help="Grid steps for c.")
    ap.add_argument("--k-steps", type=int, default=25, help="Grid steps for kappa_star.")
    ap.add_argument("--refine", action="store_true", help="Run a refinement pass around the best coarse result.")
    ap.add_argument("--refine-factor", type=float, default=0.2, help="Span as a fraction of coarse step size.")
    ap.add_argument("--refine-steps", type=int, default=15, help="Grid steps in refinement pass.")
    ap.add_argument("--compare", action="store_true", help="Also evaluate current constants and perturbations.")
    ap.add_argument("--delta-c", type=float, default=0.0001, help="Perturbation for c when --compare is set.")
    ap.add_argument("--delta-k", type=float, default=0.001, help="Perturbation for kappa_star when --compare is set.")
    ap.add_argument(
        "--errors-csv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "calibration_errors.csv",
        help="Where to write per-n errors.",
    )
    ap.add_argument(
        "--comparison-csv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "calibration_comparison.csv",
        help="Where to write comparison table when --compare is set.",
    )
    args = ap.parse_args()

    # Load data
    if args.data.suffix.lower() == ".csv":
        data = load_csv_pairs(args.data)
    else:
        data = load_known_primes_md(args.data)
    if args.extra_csv:
        data.extend(load_csv_pairs(args.extra_csv))
    data.sort(key=lambda t: t[0])

    if data and data[0][0] < args.min_n:
        if args.filter_below_min:
            data = [(n, p) for n, p in data if n >= args.min_n]
            if not data:
                raise SystemExit(f"All rows filtered out by min-n={args.min_n}. Provide larger-n data.")
        else:
            raise SystemExit(
                f"Dataset contains n<{args.min_n} (min={data[0][0]}). "
                "Small n not supported by default; rerun with --filter-below-min to drop them "
                "or lower --min-n if you intentionally want to include small n."
            )

    # Coarse search
    best = grid_search(data, tuple(args.c_bounds), tuple(args.k_bounds), args.c_steps, args.k_steps)

    # Optional refinement
    if args.refine:
        c_step = (args.c_bounds[1] - args.c_bounds[0]) / max(args.c_steps - 1, 1)
        k_step = (args.k_bounds[1] - args.k_bounds[0]) / max(args.k_steps - 1, 1)
        best = refine_search(data, best, c_step * args.refine_factor, k_step * args.refine_factor, args.refine_steps)

    # Evaluate best for detailed CSV
    best_res, per_rows = eval_coeffs(data, best.c, best.kappa_star)
    write_errors_csv(args.errors_csv, per_rows)

    print("Best coefficients:")
    print(f"  c          = {best_res.c:.8f}")
    print(f"  kappa_star = {best_res.kappa_star:.8f}")
    print(f"  max_rel_ppm= {best_res.max_rel_ppm:.6f}")
    print(f"  rms_ppm    = {best_res.rms_ppm:.6f}")
    print(f"Per-n errors written to: {args.errors_csv}")

    if args.compare:
        comparisons: List[EvalResult] = []
        current = EvalResult(-0.00016667, 0.06500, math.inf, math.inf)
        for c in [current.c, current.c + args.delta_c, current.c - args.delta_c]:
            for k in [current.kappa_star, current.kappa_star + args.delta_k, current.kappa_star - args.delta_k]:
                res, _ = eval_coeffs(data, c, k)
                comparisons.append(res)
        # Ensure best (possibly new) is included
        comparisons.append(best_res)
        write_comparison_csv(args.comparison_csv, comparisons)
        print(f"Comparison table written to: {args.comparison_csv}")


if __name__ == "__main__":
    main()
