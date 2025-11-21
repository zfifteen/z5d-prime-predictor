#!/bin/bash
# Z5D nth-Prime Predictor - Demonstration Script
# ==============================================
#
# Demonstrates the Z5D nth-prime predictor capabilities.
#
# @file demo.sh
# @version 1.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLI_BIN="$PROJECT_DIR/bin/z5d_cli"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Z5D nth-Prime Predictor - Demonstration          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if CLI exists
if [ ! -f "$CLI_BIN" ]; then
    echo -e "${RED}Error: CLI executable not found at $CLI_BIN${NC}"
    echo -e "${YELLOW}Please run 'make cli' first${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} CLI executable found"
echo ""

# Function to run prediction
run_prediction() {
    local n=$1
    local label=$2
    local opts=$3
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Predicting the ${label} prime (n=$n)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    $CLI_BIN $opts $n
    echo ""
}

# Demonstrate basic predictions
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  PHASE 1: Small Scale Predictions (10^1 - 10^6)  ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""

run_prediction 10 "10th" "-v"
run_prediction 100 "100th" "-v"
run_prediction 1000 "1,000th" "-v"
run_prediction 10000 "10,000th" "-v"
run_prediction 100000 "100,000th" "-v"
run_prediction 1000000 "1,000,000th" "-v"

# Medium scale
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  PHASE 2: Medium Scale Predictions (10^7 - 10^9) ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""

run_prediction 10000000 "10,000,000th" "-v"
run_prediction 100000000 "100,000,000th" "-v"
run_prediction 1000000000 "1,000,000,000th" "-v"

# Custom configuration
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  PHASE 3: Custom Configuration Demo               ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Testing with different K values (series terms)${NC}"
echo ""

run_prediction 1000000 "1,000,000th with K=3" "-k 3 -v"
run_prediction 1000000 "1,000,000th with K=5" "-k 5 -v"
run_prediction 1000000 "1,000,000th with K=10" "-k 10 -v"

echo -e "${YELLOW}Testing with different precision values${NC}"
echo ""

run_prediction 100000000 "100,000,000th with 150 bits" "-p 150 -v"
run_prediction 100000000 "100,000,000th with 200 bits" "-p 200 -v"
run_prediction 100000000 "100,000,000th with 300 bits" "-p 300 -v"

# Summary
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Demonstration Complete                            ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Key Features Demonstrated:${NC}"
echo -e "  ${GREEN}✓${NC} High-precision MPFR arithmetic"
echo -e "  ${GREEN}✓${NC} Newton-Halley iteration for solving R(x) = n"
echo -e "  ${GREEN}✓${NC} Riemann prime-counting function R(x)"
echo -e "  ${GREEN}✓${NC} Configurable precision and series terms"
echo -e "  ${GREEN}✓${NC} Fast convergence (typically 1-3 iterations)"
echo -e "  ${GREEN}✓${NC} Sub-millisecond to millisecond timing"
echo ""
echo -e "${YELLOW}Try it yourself:${NC}"
echo -e "  ${BLUE}$CLI_BIN -h${NC}           # Show help"
echo -e "  ${BLUE}$CLI_BIN 1000000${NC}      # Predict 1,000,000th prime"
echo -e "  ${BLUE}$CLI_BIN -k 10 -p 300 1000000000${NC}  # Custom config"
echo ""
