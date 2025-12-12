#!/bin/bash
# compare_z5dp_implementations.sh
# 
# Purpose: Validate Z5D-P C99 Implementation against Ground Truth.
# Usage: ./compare_z5dp_implementations.sh
#
# This script serves as the "Compliance Certificate" for the C implementation.
# It compiles the C code, runs it against known primes (10^1 to 10^18), 
# and enforces strict mathematical correctness.

# 1. Setup & Configuration
# ------------------------
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
C_SRC_DIR="$REPO_ROOT/src/c/z5d-predictor-c"
BIN_DIR="$C_SRC_DIR/bin"
EXECUTABLE="$BIN_DIR/z5d_bench"
DATA_FILE="$REPO_ROOT/data/KNOWN_PRIMES.md"
TEMP_LOG="/tmp/z5d_c_validation.log"

echo "=== Z5D-P Compliance Verification (C99) ==="
echo "Repo Root: $REPO_ROOT"
echo "Source:    $C_SRC_DIR"
echo "Data:      $DATA_FILE"

# 2. Compilation (using Makefile)
# -------------------------------
echo -e "\n[1/3] Building C99 Implementation..."

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
echo -e "\n[2/3] Parsing Ground Truth Data..."

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


# 4. Validation Loop
# ------------------
echo -e "\n[3/3] Running Validation Suite..."
echo "      (Tolerance: Exact match required)"

PASS_COUNT=0
FAIL_COUNT=0

# Create CSV header for log
echo "n,expected,actual,status,time_ms" > "$TEMP_LOG"

for (( i=0; i<COUNT; i++ )); do
    n="${INDICES[$i]}"
    expected="${EXPECTED_PRIMES[$i]}"
    
    # Run C binary
    # CLI usage: ./z5d_cli <n>
    output=$("$EXECUTABLE" "$n" 2>&1)
    
    # Parse output: "Predicted prime: 12345"
    actual=$(echo "$output" | grep "Predicted prime:" | awk '{print $3}')
    
    # Validation
    if [ "$actual" == "$expected" ]; then
        echo "  [PASS] n=10^$(( ${#n} - 1 )) -> p_n=$actual"
        ((PASS_COUNT++))
    else
        echo "  [FAIL] n=$n"
        echo "         Expected: $expected"
        echo "         Got:      $actual"
        echo "         Output:   $output"
        ((FAIL_COUNT++))
    fi
done

# 5. Final Report
#లుగా---------------
echo -e "\n=== Summary ==="
echo "Total Tests: $COUNT"
echo "Passed:      $PASS_COUNT"
echo "Failed:      $FAIL_COUNT"

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ Z5D-P C99 Implementation is COMPLIANT."
    exit 0
else
    echo "❌ Z5D-P C99 Implementation FAILED verification."
    exit 1
fi
