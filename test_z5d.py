import subprocess
import time
import os

os.chdir("/Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/z5d-predictor-c")

for exp in [6, 7, 8, 9]:
    n = 10**exp
    print(f"=== Z5D n=10^{exp} ({n}) ===")
    for trial in range(1, 6):
        start = time.time()
        result = subprocess.run(
            ["./bin/z5d_cli", str(n)], capture_output=True, text=True
        )
        end = time.time()
        runtime = end - start
        lines = result.stdout.strip().split("\n")
        pred_line = [line for line in lines if "Predicted prime:" in line][-1]
        pred = pred_line.split(": ")[1]
        print(f"Trial {trial}: {runtime:.6f} s, Predicted: {pred}")
