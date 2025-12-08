
import mpmath as mp
import time
from sympy import prime

def z5d_predictor(n):
    with mp.workdps(50):
        n_mp = mp.mpf(n)
        log_n = mp.log(n_mp)
        log_log_n = mp.log(log_n)
        # PNT 2nd order
        x = n_mp * log_n + n_mp * log_log_n - n_mp
        return int(mp.floor(x))

def z5d_predictor_with_dist_level(n, dist_level):
    base = z5d_predictor(n)
    with mp.workdps(50):
        n_mp = mp.mpf(n)
        log_n = mp.log(n_mp)
        adjustment = dist_level * n_mp / log_n
        return int(mp.floor(base + adjustment))

indices = [10**12, 10**15, 10**18]
thetas = [0.525, 0.71]

# Ground truth from common knowledge or previous steps
# p(10^12) = 29996224275833
# p(10^15) = 37124508045065437
# p(10^18) = 44211790234832169331
actuals = {
    10**12: 29996224275833,
    10**15: 37124508045065437,
    10**18: 44211790234832169331
}

print(f"| n | Theta | Predicted | Actual | Error (ppm) | Time (ms) |")
print(f"|---|---|---|---|---|---|")

for n in indices:
    actual = actuals[n]
    for theta in thetas:
        start = time.time()
        pred = z5d_predictor_with_dist_level(n, theta)
        elapsed = (time.time() - start) * 1000
        error_ppm = abs(pred - actual) / actual * 1e6
        print(f"| 10^{int(mp.log10(n))} | {theta} | {pred} | {actual} | {error_ppm:.2f} | {elapsed:.2f} |")
