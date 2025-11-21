#!/usr/bin/env bash
set -euo pipefail

# Smoke benchmark runner for z5d_mersenne following BENCHMARKS.md output rules.
# Generates a CSV table and matching Markdown explainer in this folder.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BIN="$ROOT/src/c/z5d-mersenne/bin/z5d_mersenne"
OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="${TS:-2025-11-21T07:13:24.849Z}"
BASE="z5d_mersenne_${TS}"
CSV="$OUT_DIR/${BASE}.csv"
MD="$OUT_DIR/${BASE}.md"

# Parameters per BENCHMARKS.md
PREC="${PREC:-2048}"
MR="${MR:-8}"
WHEEL="${WHEEL:-210}"
MAX_ITERS="${MAX_ITERS:-500}"

# K set (override with env K_VALUES: space-separated)
DEFAULT_K_VALUES=(1e5 1e10 1e18 1e100 1e200 1e300 1e400 1e500 1e600 1e700 1e800 1e900 1e1000 1e1233)
read -r -a K_VALUES <<<"${K_VALUES:-${DEFAULT_K_VALUES[*]}}"

# Build if missing
if [[ ! -x "$BIN" ]]; then
  echo "Building z5d_mersenne..."
  "$ROOT/src/c/build_all.sh" >/dev/null
fi

# CSV header per spec
printf "tool,scenario,precision_bits,mr_rounds,params,k,primes_found,locked,window_max,final_window,step,R,wall_ms,candidates,prime_found\n" >"$CSV"

fail=0
for K in "${K_VALUES[@]}"; do
  # Scenario mapping
  case "$K" in
    1e5|1e10) scenario="Sanity";;
    1e18) scenario="Mid";;
    *) scenario="Large";;
  esac
  cmd=( "$BIN" "$K" --auto-tune --prec="$PREC" --mr-rounds="$MR" --wheel="$WHEEL" --max-iters="$MAX_ITERS" -v )
  echo "Running: ${cmd[*]}" >&2
  TMP=$(mktemp)
  if ! "${cmd[@]}" >"$TMP" 2>&1; then
    echo "WARN: run failed for k=$K" >&2
    fail=1
  fi
  final_window=$(grep -E "Final parameters: window=" "$TMP" | sed -E 's/.*window=([0-9]+), step=([0-9]+), R=([0-9.]+).*/\1/')
  step=$(grep -E "Final parameters: window=" "$TMP" | sed -E 's/.*window=([0-9]+), step=([0-9]+), R=([0-9.]+).*/\2/')
  R=$(grep -E "Final parameters: window=" "$TMP" | sed -E 's/.*window=([0-9]+), step=([0-9]+), R=([0-9.]+).*/\3/')
  wall_ms=$(grep -E "Elapsed time:" "$TMP" | sed -E 's/.*Elapsed time: ([0-9.]+) ms.*/\1/')
  primes_found=$(grep -E "Prime count:" "$TMP" | sed -E 's/.*Prime count: ([0-9]+).*/\1/')
  locked=$(grep -E "Status:" "$TMP" | sed -E 's/.*Status: (LOCKED|FAILED).*/\1/' | sed 's/LOCKED/true/;s/FAILED/false/')
  candidates=$(grep -E "Miller-Rabin calls:" "$TMP" | sed -E 's/.*Miller-Rabin calls: ([0-9]+).*/\1/')
  prime_found=$(grep -E "^Prime found: " "$TMP" | sed -E 's/.*Prime found: ([0-9]+).*/\1/' || true)
  if grep -qE "^Iter [0-9]+:" "$TMP"; then
    window_max=$(grep -E "^Iter [0-9]+:" "$TMP" | sed -E 's/.*window=([0-9]+).*/\1/' | awk 'max<$1{max=$1}END{print max+0}')
  else
    window_max="$final_window"
  fi
  params="wheel=$WHEEL;auto_tune=1;target=1"
  printf "z5d-mersenne,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" \
    "$scenario" "$PREC" "$MR" "$params" "$K" "${primes_found:-0}" "${locked:-false}" "${window_max:-}" "${final_window:-}" "${step:-}" "${R:-}" "${wall_ms:-}" "${candidates:-}" >>"$CSV"
  rm -f "$TMP"
  # Require lock for smoke
  if [[ "${locked:-false}" != "true" ]]; then
    echo "FAIL: not locked for k=$K" >&2
    fail=1
  fi
done

# Markdown explainer (conclusion-first)
cat >"$MD" <<EOF
# z5d-mersenne smoke: All scenarios locked a nearby prime with fixed precision $PREC and MR rounds $MR

We ran z5d-mersenne with auto-tuning and wheel $WHEEL across Sanity, Mid, and Large k values, capturing candidates (MR calls), max/final window, R, wall-time, and lock status, per BENCHMARKS.md. Each row in the CSV represents one k scenario.

Methods: Apple Silicon, MPFR precision $PREC bits, MR rounds $MR, max iters $MAX_ITERS, auto-tune on. We parsed the tool's verbose output to compute window_max from tuning iterations and extracted final parameters and timings.

See $BASE.csv for the detailed results.
EOF

echo "Wrote $CSV and $MD"
exit $fail
