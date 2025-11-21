#!/usr/bin/env python3
"""
Verify primality of 'prime_found' values in z5d-mersenne benchmark CSV outputs.

Usage:
  python verify_primes.py path/to/z5d_mersenne_*.csv
  python verify_primes.py --glob 'z5d_mersenne_2025-11-21*.csv'

Exit codes:
  0 = all primes verified / no primes to verify
  1 = at least one value failed primality test or verification incomplete

Notes:
  - Uses sympy.isprime for deterministic BPSW testing (sufficient for very large integers; widely accepted).
  - For rows with primes_found != 1 or locked != true, prime_found is skipped.
  - Rows lacking a prime_found value are reported.
  - Timestamp: 2025-11-21T07:30:06.196Z
"""
from __future__ import annotations
import csv
import argparse
import sys
import pathlib
from typing import List, Tuple

try:
    from sympy import isprime  # BPSW primality test
except ImportError:  # pragma: no cover
    print("ERROR: sympy not installed. Install with: pip install sympy", file=sys.stderr)
    sys.exit(2)

HEADER_EXPECTED = [
    "tool","scenario","precision_bits","mr_rounds","params","k","primes_found","locked",
    "window_max","final_window","step","R","wall_ms","candidates","prime_found"
]

class PrimeCheckResult:
    def __init__(self, k: str, prime: str, ok: bool, message: str):
        self.k = k
        self.prime = prime
        self.ok = ok
        self.message = message

    def to_row(self) -> List[str]:
        return [self.k, self.prime, "OK" if self.ok else "FAIL", self.message]


def load_csv(path: pathlib.Path) -> Tuple[List[str], List[List[str]]]:
    with path.open("r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        raise ValueError(f"Empty CSV: {path}")
    header = rows[0]
    data = rows[1:]
    return header, data


def verify_header(header: List[str]) -> None:
    if header != HEADER_EXPECTED:
        print(f"WARNING: Header mismatch; proceeding anyway. Found: {header}", file=sys.stderr)


def check_prime(k: str, prime_str: str) -> PrimeCheckResult:
    if not prime_str:
        return PrimeCheckResult(k, prime_str, False, "missing prime_found")
    try:
        n = int(prime_str)
    except ValueError:
        return PrimeCheckResult(k, prime_str, False, "non-integer prime_found")
    ok = isprime(n)
    return PrimeCheckResult(k, prime_str, ok, "verified BPSW" if ok else "composite (BPSW)")


def process_file(path: pathlib.Path) -> List[PrimeCheckResult]:
    header, data = load_csv(path)
    verify_header(header)
    # Map column indices
    col_index = {name: i for i, name in enumerate(header)}
    required_cols = ["k","primes_found","locked","prime_found"]
    for c in required_cols:
        if c not in col_index:
            raise ValueError(f"Missing required column '{c}' in {path}")
    results: List[PrimeCheckResult] = []
    for row in data:
        if not row or len(row) < len(header):
            continue
        k = row[col_index["k"]]
        primes_found = row[col_index["primes_found"]]
        locked = row[col_index["locked"]].lower()
        prime_found = row[col_index["prime_found"]] if col_index["prime_found"] < len(row) else ""
        # Only verify when exactly one prime was reported and locked true
        if primes_found == "1" and locked == "true":
            results.append(check_prime(k, prime_found))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify primality in z5d-mersenne benchmark CSV files")
    parser.add_argument("paths", nargs="*", help="CSV file paths")
    parser.add_argument("--glob", dest="glob", help="Glob pattern (evaluated relative to benchmarks/z5d-mersenne)")
    parser.add_argument("--fail-on-missing", action="store_true", help="Fail if any prime_found is missing for a locked row")
    args = parser.parse_args()

    files: List[pathlib.Path] = []
    if args.glob:
        base = pathlib.Path(__file__).parent
        files.extend(sorted(base.glob(args.glob)))
    files.extend(pathlib.Path(p) for p in args.paths)
    files = [f for f in files if f.is_file()]

    if not files:
        print("No CSV files provided.", file=sys.stderr)
        return 2

    overall_ok = True
    report_rows: List[List[str]] = []

    for f in files:
        print(f"Processing {f}", file=sys.stderr)
        try:
            results = process_file(f)
        except Exception as e:  # pragma: no cover
            print(f"ERROR processing {f}: {e}", file=sys.stderr)
            overall_ok = False
            continue
        for r in results:
            report_rows.append(r.to_row())
            if not r.ok:
                overall_ok = False
    # Output summary table (CSV to stdout)
    print("k,prime_found,status,message")
    for r in report_rows:
        print(",".join(r))

    if args.fail_on_missing:
        # Re-scan for missing primes
        for f in files:
            header, data = load_csv(f)
            col_index = {name: i for i, name in enumerate(header)}
            for row in data:
                if not row or len(row) < len(header):
                    continue
                if row[col_index["primes_found"]] == "1" and row[col_index["locked"]].lower() == "true":
                    if not row[col_index["prime_found"]]:
                        overall_ok = False
                        print(f"MISSING prime_found for k={row[col_index['k']]} (locked row)", file=sys.stderr)
    return 0 if overall_ok else 1

if __name__ == "__main__":
    sys.exit(main())
