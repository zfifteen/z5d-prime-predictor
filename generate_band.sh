#!/bin/bash

# generate_band.sh <exp>
# Generates comparison data for band 10^exp (exp=12-18)

if [ $# -ne 1 ]; then
    echo "Usage: $0 <exp> (integer 12-18)"
    exit 1
fi

EXP=$1
if ! [[ "$EXP" =~ ^[0-9]+$ ]] || [ $EXP -lt 12 ] || [ $EXP -gt 18 ]; then
    echo "Invalid exp: must be integer 12-18"
    exit 1
fi

N=$(echo "10^$EXP" | bc)
DIR="/Users/velocityworks/IdeaProjects/z5d-prime-predictor"
BENCH_DIR="$DIR/benchmarks"

mkdir -p "$BENCH_DIR"
cd "$DIR/src/c/z5d-predictor-c"

echo "Generating for 10^$EXP (n=$N)"

# Z5D run (1 trial)
Z5D_START=$(date +%s.%3N)
Z5D_OUTPUT=$(./bin/z5d_cli $N 2>&1)
Z5D_END=$(date +%s.%3N)
Z5D_TIME=$(echo "$Z5D_END - $Z5D_START" | bc -l)
Z5D_PRED=$(echo "$Z5D_OUTPUT" | grep "Predicted prime:" | awk '{print $3}')

# Primesieve run with timeout
PS_START=$(date +%s.%3N)
if timeout 600 primesieve $N -n --time > /tmp/ps_out 2>&1; then
    PS_END=$(date +%s.%3N)
    PS_TIME=$(echo "$PS_END - $PS_START" | bc -l)
    PS_PRIME=$(grep "Nth prime:" /tmp/ps_out | awk '{print $3}')
else
    PS_TIME="inf"
    PS_PRIME="timeout"
fi
rm -f /tmp/ps_out

# Compute speedup
if [ "$PS_TIME" != "inf" ]; then
    SPEEDUP=$(echo "scale=4; $PS_TIME / $Z5D_TIME" | bc -l)
else
    SPEEDUP="N/A"
fi

# JSON with full format
cat > "$BENCH_DIR/band_10_$EXP.json" << EOF
{
  "band": "10^$EXP",
  "n": $N,
  "z5d": {
    "mean_time_s": $Z5D_TIME,
    "std_time_s": 0,
    "trials": [$Z5D_TIME],
    "predictions": ["$Z5D_PRED"]
  },
  "primesieve": {
    "mean_time_s": $PS_TIME,
    "std_time_s": 0,
    "trials": [$PS_TIME],
    "primes": ["$PS_PRIME"]
  },
  "z5d_speedup_factor": $SPEEDUP
}
EOF

echo "Done: $BENCH_DIR/band_10_$EXP.json"