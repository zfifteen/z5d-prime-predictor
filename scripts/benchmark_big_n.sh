#!/bin/bash
# benchmark_big_n.sh
# Sweep large n values up to 10^1233 using the C predictor (big-n path).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
C_SRC_DIR="$REPO_ROOT/src/c/z5d-predictor-c"
CLI="$C_SRC_DIR/bin/z5d_cli"
OUT_CSV="/tmp/z5d_big_n_timings.csv"

EXPS=()
for e in $(seq 20 10 1230); do EXPS+=("$e"); done
EXPS+=("1233")

echo "=== Z5D big-n benchmark (C) ==="
echo "Building C predictor..."
cd "$C_SRC_DIR"
make -s

echo "n,elapsed_ms,prime_digits" > "$OUT_CSV"

for EXP in "${EXPS[@]}"; do
  n_str=$(python3 - <<PY
from decimal import Decimal, getcontext
import sys
exp=int(sys.argv[1])
getcontext().prec = exp + 10
print((Decimal(10) ** exp).to_integral_exact())
PY
"$EXP")

  start_ns=$(date +%s%N)
  output=$("$CLI" "$n_str")
  end_ns=$(date +%s%N)
  elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))

  prime=$(echo "$output" | awk '/Predicted prime:/ {print $3}')
  digits=${#prime}

  echo "10^$EXP: ${elapsed_ms} ms, digits=$digits"
  echo "$n_str,$elapsed_ms,$digits" >> "$OUT_CSV"
done

echo "Results written to $OUT_CSV"
