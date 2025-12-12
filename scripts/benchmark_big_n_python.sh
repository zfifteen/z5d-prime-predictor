#!/bin/bash
# benchmark_big_n_python.sh
# Sweep large n values up to 10^1233 using the Python predictor.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_SRC_DIR="$REPO_ROOT/src/python"
OUTPUT_DIR="$REPO_ROOT/scripts/output"
OUT_CSV="$OUTPUT_DIR/z5d_big_n_timings_python.csv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$OUTPUT_DIR"

# Verify gmpy2 is available in the chosen interpreter (no fallbacks)
if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1; then
import gmpy2
PY
  echo "❌ gmpy2 not found in $PYTHON_BIN. Install with:"
  echo "   $PYTHON_BIN -m pip install gmpy2"
  exit 1
fi

if [ -n "${EXPS_OVERRIDE:-}" ]; then
  IFS=',' read -r -a EXPS <<< "$EXPS_OVERRIDE"
else
  EXPS=(20)
  for e in $(seq 50 50 1200); do EXPS+=("$e"); done
  EXPS+=("1230" "1233")
fi

echo "=== Z5D big-n benchmark (Python) ==="
print_hardware_overview() {
  echo "Hardware Overview:"
  if command -v sysctl >/dev/null 2>&1; then
    model=$(sysctl -n hw.model 2>/dev/null || true)
    chip=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || true)
    pcores=$(sysctl -n hw.physicalcpu 2>/dev/null || true)
    lcores=$(sysctl -n hw.logicalcpu 2>/dev/null || true)
    mem_bytes=$(sysctl -n hw.memsize 2>/dev/null || true)
    os_ver=$(sw_vers -productVersion 2>/dev/null || true)

    if [ -n "${mem_bytes:-}" ]; then
      mem_gb=$(( (mem_bytes + 1024*1024*512) / 1024 / 1024 / 1024 ))
      mem_str="${mem_gb} GB"
    else
      mem_str="unknown"
    fi

    [ -n "${model:-}" ] && echo "  Model: $model"
    [ -n "${chip:-}" ] && echo "  Chip: $chip"
    [ -n "${pcores:-}" ] && echo "  Physical Cores: $pcores"
    [ -n "${lcores:-}" ] && echo "  Logical Cores: $lcores"
    echo "  Memory: ${mem_str}"
    [ -n "${os_ver:-}" ] && echo "  macOS: $os_ver"
  else
    echo "  (hardware details unavailable: sysctl not found)"
  fi
  echo
}

print_hardware_overview

# Warm-up sweep (not logged)
echo "Warm-up sweep (not logged)..."
for EXP in "${EXPS[@]}"; do
  n_str=$("$PYTHON_BIN" - <<PY
exp = int("${EXP}")
print(10**exp)
PY
)
  "$PYTHON_BIN" - <<PY
import sys, os
sys.path.append("$PY_SRC_DIR")
from z5d_predictor import predict_nth_prime
predict_nth_prime(int("${n_str}"))
PY
done
echo "Warm-up done. Running measured sweep..."

echo "n,elapsed_ms,prime_digits" > "$OUT_CSV"

for EXP in "${EXPS[@]}"; do
  n_str=$("$PYTHON_BIN" - <<PY
exp = int("${EXP}")
print(10**exp)
PY
)

  start_ns=$(date +%s%N)
  prime=$("$PYTHON_BIN" - <<PY
import sys, os, time
sys.path.append("$PY_SRC_DIR")
from z5d_predictor import predict_nth_prime
print(predict_nth_prime(int("${n_str}" )).prime)
PY
)
  end_ns=$(date +%s%N)
  elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))
  digits=${#prime}

  echo "10^$EXP: ${elapsed_ms} ms, digits=$digits"
  echo "$n_str,$elapsed_ms,$digits" >> "$OUT_CSV"
done

echo "Results written to $OUT_CSV"
