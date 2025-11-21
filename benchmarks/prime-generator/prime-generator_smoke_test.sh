#!/usr/bin/env bash
set -euo pipefail

# Smoke test runner for prime_generator at ~1e18 scale (Apple Silicon)
# Produces matching CSV + Markdown (conclusion-first) in this folder.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BIN="$ROOT/src/c/prime-generator/bin/prime_generator"
OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="prime-generator_smoke-1e18"
CSV="$OUT_DIR/${BASE}.csv"
MD="$OUT_DIR/${BASE}.md"

# Pick a large composite near 1e18; expected next prime is start+3 for this value.
START="${START:-1000000000000000000}"
EXPECTED="${EXPECTED:-1000000000000000003}"

# Build if missing
if [[ ! -x "$BIN" ]]; then
  echo "Building prime_generator..."
  "$ROOT/src/c/build_all.sh" >/dev/null
fi

cmd=( "$BIN" --start "$START" --count 1 --csv )

echo "Running: ${cmd[*]}"
output="$("${cmd[@]}")"

# Parse CSV output (header + one row)
line=$(printf "%s\n" "$output" | tail -n 1)
IFS=',' read -r idx prime is_mersenne ms_report <<<"$line"

# Use program-reported ms as canonical runtime (external shell timing overhead dominates this tiny run)
elapsed_ms="$ms_report"

# Write our normalized CSV
{
  echo "start,prime_found,elapsed_ms,ms_reported,is_mersenne"
  echo "$START,$prime,$elapsed_ms,$ms_report,$is_mersenne"
} > "$CSV"

# Write Markdown explainer (conclusion-first)
cat > "$MD" <<EOF
Conclusion: Found prime $prime starting from $START in ${elapsed_ms} ms (program-reported); is_mersenne=${is_mersenne}.

Details:
- Command: ${cmd[*]}
- Start value: $START
- Expected (reference): $EXPECTED
- Prime found: $prime
- Program-reported time (ms): $ms_report
- Mersenne flag: $is_mersenne
- Platform: Apple Silicon, MPFR/GMP via Homebrew, defaults for precision and MR rounds.

Notes:
- This is a smoke test only; count=1, default filters/jumps enabled.
- Consider re-running if the prime differs from expected or if wall time exceeds target (< ~250 ms).
EOF

echo "Wrote $CSV and $MD"
