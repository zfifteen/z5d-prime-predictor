#!/bin/bash

cd /Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/z5d-predictor-c

for exp in 6 7 8 9 10 11 12; do
  n=$((10**$exp))
  echo "=== Z5D n=10^$exp ($n) ==="
  for trial in {1..5}; do
    runtime=$({ /usr/bin/time -f "%e" ./bin/z5d_cli $n 2>/dev/null ; } 2>&1 | tail -1)
    pred=$(./bin/z5d_cli $n 2>/dev/null | grep "Predicted prime:" | awk '{print $3}')
    echo "Trial $trial: $runtime s, Predicted: $pred"
  done
done