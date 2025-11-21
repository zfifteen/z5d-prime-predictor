#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building z5d-predictor-c..."
(cd "$here/z5d-predictor-c" && make clean && make)

echo "Building z5d-mersenne..."
(cd "$here/z5d-mersenne" && make clean && make)

echo "Building prime-generator..."
(cd "$here/prime-generator" && make clean && make)

echo "✅ All builds completed."
