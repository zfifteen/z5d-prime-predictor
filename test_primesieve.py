import subprocess
import time

for exp in [6, 7, 8, 9]:
    n = 10**exp
    print(f"=== Primesieve n=10^{exp} ({n}) ===")
    for trial in range(1, 6):
        start = time.time()
        result = subprocess.run(
            ["primesieve", str(n), "-n", "--time"], capture_output=True, text=True
        )
        end = time.time()
        runtime = end - start
        lines = result.stdout.strip().split("\n")
        prime_line = [line for line in lines if "Nth prime:" in line][0]
        prime = prime_line.split(": ")[1]
        time_line = [line for line in lines if "Seconds:" in line][0]
        internal_time = float(time_line.split(": ")[1])
        print(
            f"Trial {trial}: {runtime:.6f} s (internal {internal_time:.6f} s), Prime: {prime}"
        )
