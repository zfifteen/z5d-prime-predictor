import subprocess
import time
import json
import statistics
import os

os.chdir("/Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/z5d-predictor-c")


def run_z5d(n, trials=1):
    times = []
    preds = []
    for _ in range(trials):
        start = time.time()
        result = subprocess.run(
            ["./bin/z5d_cli", str(n)], capture_output=True, text=True
        )
        end = time.time()
        times.append(end - start)
        lines = result.stdout.strip().split("\n")
        pred_line = [line for line in lines if "Predicted prime:" in line][-1]
        pred = pred_line.split(": ")[1]
        preds.append(pred)
    return times, preds


def run_primesieve(n, trials=1, timeout=300):
    times = []
    primes = []
    for _ in range(trials):
        try:
            start = time.time()
            result = subprocess.run(
                ["primesieve", str(n), "-n", "--time"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            end = time.time()
            times.append(end - start)
            lines = result.stdout.strip().split("\n")
            prime_line = [line for line in lines if "Nth prime:" in line][0]
            prime = prime_line.split(": ")[1]
            primes.append(prime)
        except subprocess.TimeoutExpired:
            times.append(float("inf"))
            primes.append("timeout")
    return times, primes


for exp in range(4, 12):  # 10^4 to 10^11
    n = 10**exp
    print(f"Testing band 10^{exp} (n={n})")

    # Z5D
    z5d_times, z5d_preds = run_z5d(n)
    z5d_mean = statistics.mean(z5d_times) if z5d_times else float("inf")
    z5d_std = statistics.stdev(z5d_times) if len(z5d_times) > 1 else 0

    # Primesieve
    ps_times, ps_primes = run_primesieve(n)
    ps_mean = (
        statistics.mean([t for t in ps_times if t != float("inf")])
        if any(t != float("inf") for t in ps_times)
        else float("inf")
    )
    ps_std = (
        statistics.stdev([t for t in ps_times if t != float("inf")])
        if len([t for t in ps_times if t != float("inf")]) > 1
        else 0
    )

    # Check if all timeout
    if all(t == float("inf") for t in ps_times):
        print(f"Primesieve timeout for 10^{exp}, skipping further")
        break

    # JSON
    data = {
        "band": f"10^{exp}",
        "n": n,
        "z5d": {
            "mean_time_s": z5d_mean,
            "std_time_s": z5d_std,
            "trials": z5d_times,
            "predictions": z5d_preds,
        },
        "primesieve": {
            "mean_time_s": ps_mean,
            "std_time_s": ps_std,
            "trials": ps_times,
            "primes": ps_primes,
        },
        "z5d_speedup_factor": ps_mean / z5d_mean
        if ps_mean != float("inf") and z5d_mean != float("inf")
        else "N/A",
    }

    filename = f"/Users/velocityworks/IdeaProjects/z5d-prime-predictor/benchmarks/band_10_{exp}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"JSON written to {filename}")
    print(f"Z5D mean: {z5d_mean:.6f}s, Primesieve mean: {ps_mean:.6f}s")
