#!/usr/bin/env bash
set -euo pipefail

# Smoke test runner for z5d_mersenne (nearby-prime scanner) at ~1e18 scale on Apple Silicon.
# Produces CSV + Markdown (conclusion-first) in this folder.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BIN="$ROOT/src/c/z5d-mersenne/bin/z5d_mersenne"
OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="z5d-mersenne_smoke-1e18"
CSV="$OUT_DIR/${BASE}.csv"
MD="$OUT_DIR/${BASE}.md"

# Configure k near 1e18 (fits current CLI expectations)
K_VAL="${K_VAL:-1000000000000000007}"
MAX_MS="${MAX_MS:-20000}"          # generous wall cap in ms for smoke
REQUIRE_LOCKED="${REQUIRE_LOCKED:-true}"

# Build if missing
if [[ ! -x "$BIN" ]]; then
  echo "Building z5d_mersenne..."
  "$ROOT/src/c/build_all.sh" >/dev/null
fi

cmd=( "$BIN" "$K_VAL" --json )

echo "Running: ${cmd[*]}"
output="$("${cmd[@]}")"

# Parse JSON with python stdlib (no jq dependency)
parse_py='import json, sys
data = json.loads(sys.stdin.read())
print(
    data.get("prime_found",""),
    data.get("window",""),
    data.get("step",""),
    data.get("mr_calls",""),
    data.get("elapsed_ms",""),
    data.get("locked",""),
    data.get("wheel_residue","")
)'
read -r prime window step mr_calls elapsed_ms locked wheel <<<"$(python3 -c "$parse_py" <<<"$output")"

# Assertions
fail=0
if [[ -z "$prime" ]]; then
  echo "FAIL: no prime returned" >&2
  fail=1
fi
if [[ "$REQUIRE_LOCKED" == "true" && "$locked" != "True" && "$locked" != "true" ]]; then
  echo "FAIL: locked flag is $locked" >&2
  fail=1
fi
ms_int=$(python3 - <<PY
try:
    import math
    v=float("$elapsed_ms")
    print(int(math.ceil(v)))
except Exception:
    print(9999999)
PY
)
if (( ms_int > MAX_MS )); then
  echo "FAIL: elapsed_ms $elapsed_ms exceeds MAX_MS $MAX_MS" >&2
  fail=1
fi
if [[ -z "$mr_calls" || "$mr_calls" == "None" ]]; then
  echo "FAIL: missing mr_calls" >&2
  fail=1
fi

# Write CSV
{
  echo "k,prime_found,window,step,mr_calls,elapsed_ms,locked,wheel_residue"
  echo "$K_VAL,$prime,$window,$step,$mr_calls,$elapsed_ms,$locked,$wheel"
} > "$CSV"

# Write Markdown explainer (conclusion-first)
cat > "$MD" <<EOF
Conclusion: Found prime $prime from k=$K_VAL using window=$window, step=$step in ${elapsed_ms} ms (MR calls: $mr_calls); locked=$locked.

Details:
- Command: ${cmd[*]}
- k input: $K_VAL
- Prime found: $prime
- Window / step: $window / $step
- MR calls: $mr_calls
- Time (ms): $elapsed_ms
- Wheel residue set: $wheel
- Locked: $locked
- Platform: Apple Silicon, MPFR/GMP via Homebrew; defaults for precision/window/MR in z5d_mersenne.

Notes:
- Smoke test only; defaults used. Re-run with different k or higher precision if needed.
EOF

echo "Wrote $CSV and $MD"
exit $fail
