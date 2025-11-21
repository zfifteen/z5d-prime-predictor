#!/usr/bin/env bash
set -euo pipefail

# Smoke test runner for z5d-predictor-c (nth-prime predictor) on Apple Silicon.
# Uses a known p_k for k=1e9 to check accuracy and timing, emits CSV+MD.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BIN="$ROOT/src/c/z5d-predictor-c/bin/z5d_cli"
OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="z5d-predictor-c_smoke-1e9"
CSV="$OUT_DIR/${BASE}.csv"
MD="$OUT_DIR/${BASE}.md"

# Known ground truth: p_1e9 = 22801763489 (OEIS A006988)
K_VAL="${K_VAL:-1000000000}"
P_TRUE="${P_TRUE:-22801763489}"

# Build if missing
if [[ ! -x "$BIN" ]]; then
  echo "Building z5d-predictor-c..."
  "$ROOT/src/c/build_all.sh" >/dev/null
fi

cmd=( "$BIN" "$K_VAL" )

echo "Running: ${cmd[*]}"
start_ns=$(python3 - <<'PY'
import time; print(int(time.perf_counter()*1e9))
PY
)
output="$("${cmd[@]}")"
end_ns=$(python3 - <<'PY'
import time; print(int(time.perf_counter()*1e9))
PY
)
elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))

# z5d_cli prints multiple lines; grab the predicted prime line
p_hat=$(printf "%s\n" "$output" | grep -E "Predicted prime:" | sed 's/.*Predicted prime:[[:space:]]*//')

abs_err=$(python3 - <<PY
from decimal import Decimal
p_true=Decimal("$P_TRUE"); p_hat=Decimal("$p_hat")
print(int(abs(p_hat-p_true)))
PY
)
rel_err=$(python3 - <<PY
from decimal import Decimal, getcontext
getcontext().prec = 50
p_true=Decimal("$P_TRUE"); p_hat=Decimal("$p_hat")
err = abs(p_hat-p_true)/p_true
print("{:.6e}".format(err))
PY
)

# Write CSV
{
  echo "k,p_true,p_hat,abs_error,rel_error,elapsed_ms"
  echo "$K_VAL,$P_TRUE,$p_hat,$abs_err,$rel_err,$elapsed_ms"
} > "$CSV"

# Write Markdown explainer (conclusion-first)
cat > "$MD" <<EOF
Conclusion: Predicted p_$K_VAL ≈ $p_hat vs true $P_TRUE (abs error $abs_err, rel error $rel_err) in ${elapsed_ms} ms.

Details:
- Command: ${cmd[*]}
- k input: $K_VAL
- True p_k: $P_TRUE
- Predicted p_k: $p_hat
- Absolute error: $abs_err
- Relative error: $rel_err
- Time (ms): $elapsed_ms (wall)
- Platform: Apple Silicon, MPFR/GMP via Homebrew; default precision in z5d-predictor-c.

Notes:
- Smoke test only; single k point at 1e9.
- Adjust P_TRUE/K_VAL if using a different reference point.
EOF

echo "Wrote $CSV and $MD"
