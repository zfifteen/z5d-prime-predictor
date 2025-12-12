#!/bin/bash
# compare_z5dp_implementations.sh
# 
# Purpose: Validate Z5D-P C99/Python/Java implementations against Ground Truth.
# Usage: ./compare_z5dp_implementations.sh
#
# This script serves as the "Compliance Certificate" for the C, Python, and Java implementations.
# It builds C and Java, executes all three against known primes (10^1 to 10^18),
# and enforces strict mathematical correctness.

# 1. Setup & Configuration
# ------------------------
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
C_SRC_DIR="$REPO_ROOT/src/c/z5d-predictor-c"
BIN_DIR="$C_SRC_DIR/bin"
EXECUTABLE="$BIN_DIR/z5d_bench"
DATA_FILE="$REPO_ROOT/data/KNOWN_PRIMES.md"
TEMP_LOG="/tmp/z5d_c_validation.log"

echo "=== Z5D-P Compliance Verification (C99 + Python + Java parity) ==="
echo "Repo Root: $REPO_ROOT"
echo "Source:    $C_SRC_DIR"
echo "Data:      $DATA_FILE"

# 2. Compilation (using Makefile)
# -------------------------------
echo -e "\n[1/4] Building C99 Implementation..."

cd "$C_SRC_DIR"
make clean > /dev/null
make > /dev/null

if [ $? -ne 0 ]; then
    echo "❌ Make failed."
    exit 1
fi

EXECUTABLE="$C_SRC_DIR/bin/z5d_cli"

if [ ! -f "$EXECUTABLE" ]; then
    echo "❌ Executable not found at $EXECUTABLE"
    exit 1
fi

echo "✅ Build SUCCESS."


# 3. Ground Truth Parsing
# -----------------------
echo -e "\n[2/4] Parsing Ground Truth Data..."

if [ ! -f "$DATA_FILE" ]; then
    echo "❌ Ground truth file not found: $DATA_FILE"
    exit 1
fi

# Extract lines like "| 1000 | 10^3 | 7919 | ..."
# Format: n, p_n
declare -a INDICES
declare -a EXPECTED_PRIMES

# Skip header and read lines
while IFS='|' read -r empty n scientific p_n source; do
    # Trim whitespace
    n=$(echo "$n" | xargs)
    p_n=$(echo "$p_n" | xargs)
    
    # Check if n is a number (skip header lines)
    if [[ "$n" =~ ^[0-9]+$ ]]; then
        INDICES+=("$n")
        EXPECTED_PRIMES+=("$p_n")
    fi
done < "$DATA_FILE"

COUNT=${#INDICES[@]}
echo "✅ Loaded $COUNT test cases from KNOWN_PRIMES.md"


# 4. Validation Loop (C vs Python vs Ground Truth)
# ------------------------------------------------
echo -e "\n[3/4] Building Java Implementation..."
JAVA_DIR="$REPO_ROOT/src/java"
JAVA_MAIN_CLASS="z5d.predictor.Z5DMain"
JAVA_CP="$JAVA_DIR/build/classes/java/main"
cd "$JAVA_DIR"
gradle -q testClasses
if [ $? -ne 0 ]; then
    echo "❌ Gradle build failed."
    exit 1
fi
echo "✅ Java build SUCCESS."

echo -e "\n[4/4] Running Validation Suite..."
echo "      (Tolerance: Exact match required)"

PASS_COUNT=0
FAIL_COUNT=0

# Create CSV header for log
echo "n,expected,c,python,java,status,time_ms_c,time_ms_py,time_ms_java" > "$TEMP_LOG"

for (( i=0; i<COUNT; i++ )); do
    n="${INDICES[$i]}"
    expected="${EXPECTED_PRIMES[$i]}"
    
    # --- C binary ---
    t0_c=$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)
    output_c=$("$EXECUTABLE" "$n" 2>&1)
    t1_c=$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)
    time_c_ms=$(python3 - <<PY
start=$t0_c
end=$t1_c
print((end-start)*1000)
PY
)
    actual_c=$(echo "$output_c" | grep "Predicted prime:" | awk '{print $3}')
    
    # --- Python predictor (inline, no wrapper) ---
    t0_py=$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)
    actual_py=$(python3 - <<PY
import sys, os
sys.path.append(os.path.join("$REPO_ROOT","src","python"))
from z5d_predictor import predict_nth_prime
print(predict_nth_prime($n).prime)
PY
)
    t1_py=$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)
    time_py_ms=$(python3 - <<PY
start=$t0_py
end=$t1_py
print((end-start)*1000)
PY
)

    # --- Java predictor ---
    t0_java=$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)
    actual_java=$(java -cp "$JAVA_CP" "$JAVA_MAIN_CLASS" "$n")
    t1_java=$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)
    time_java_ms=$(python3 - <<PY
start=$t0_java
end=$t1_java
print((end-start)*1000)
PY
)

    status="PASS"
    message=""

    if [ "$actual_c" != "$expected" ] && [ "$actual_py" != "$expected" ] && [ "$actual_java" != "$expected" ]; then
        status="FAIL"
        message="C != expected; PY != expected; JAVA != expected"
    elif [ "$actual_c" != "$expected" ] && [ "$actual_py" == "$expected" ] && [ "$actual_java" == "$expected" ]; then
        status="FAIL"
        message="C FAIL (PY & JAVA OK)"
    elif [ "$actual_c" == "$expected" ] && [ "$actual_py" != "$expected" ] && [ "$actual_java" == "$expected" ]; then
        status="FAIL"
        message="PY FAIL (C & JAVA OK)"
    elif [ "$actual_c" == "$expected" ] && [ "$actual_py" == "$expected" ] && [ "$actual_java" != "$expected" ]; then
        status="FAIL"
        message="JAVA FAIL (C & PY OK)"
    elif [ "$actual_c" != "$actual_py" ] || [ "$actual_c" != "$actual_java" ] || [ "$actual_py" != "$actual_java" ]; then
        status="FAIL"
        message="Implementations disagree (check individual outputs)"
    fi

    if [ "$status" == "PASS" ]; then
        echo "  [PASS] n=$n -> p_n=$expected (C=$actual_c, PY=$actual_py, JAVA=$actual_java)"
        ((PASS_COUNT++))
    else
        echo "  [FAIL] n=$n"
        echo "         Expected: $expected"
        echo "         C:        $actual_c"
        echo "         Python:   $actual_py"
        echo "         Java:     $actual_java"
        echo "         Note:     $message"
        ((FAIL_COUNT++))
    fi

    echo "$n,$expected,$actual_c,$actual_py,$actual_java,$status,$time_c_ms,$time_py_ms,$time_java_ms" >> "$TEMP_LOG"
done

# 5. Final Report
# ----------------
echo -e "\n=== Summary ==="
echo "Total Tests: $COUNT"
echo "Passed:      $PASS_COUNT"
echo "Failed:      $FAIL_COUNT"

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ Z5D-P C99, Python, and Java implementations are COMPLIANT."
    exit 0
else
    echo "❌ Verification FAILED."
    exit 1
fi
