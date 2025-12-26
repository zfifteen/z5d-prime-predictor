#!/bin/bash
#
# crosscheck.sh - Simple wrapper for Z5D-Geofac cross-validation
#
# Usage:
#   ./crosscheck.sh N [N2 N3 ...]
#   ./crosscheck.sh --test
#   ./crosscheck.sh --full
#
# Examples:
#   ./crosscheck.sh 1000000000000000
#   ./crosscheck.sh 1000000000000000 10000000000000000
#   ./crosscheck.sh --test

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/tools"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found" >&2
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import gmpy2, numpy, scipy" 2>/dev/null || {
    echo "Error: Missing dependencies. Install with:"
    echo "  pip3 install gmpy2 numpy scipy"
    exit 1
}

# Parse arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 N [N2 N3 ...] | --test | --full"
    exit 1
fi

# Run appropriate mode
case "$1" in
    --test)
        echo "Running test experiment..."
        cd "$TOOLS_DIR"
        python3 run_experiment.py --test
        ;;
    --full)
        echo "Running full experiment..."
        cd "$TOOLS_DIR"
        python3 run_experiment.py --full
        ;;
    *)
        # Custom N values
        echo "Running crosscheck for specified semiprimes..."
        cd "$TOOLS_DIR"
        python3 crosscheck.py "$@" --verbose
        ;;
esac

echo ""
echo "✓ Done. Results in: $SCRIPT_DIR/artifacts/"
