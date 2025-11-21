Conclusion: Found prime 1000000000000000003 starting from 1000000000000000000 in 0.132 ms (program-reported); is_mersenne=0.

Details:
- Command: /Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/prime-generator/bin/prime_generator --start 1000000000000000000 --count 1 --csv
- Start value: 1000000000000000000
- Expected (reference): 1000000000000000003
- Prime found: 1000000000000000003
- Program-reported time (ms): 0.132
- Mersenne flag: 0
- Platform: Apple Silicon, MPFR/GMP via Homebrew, defaults for precision and MR rounds.

Notes:
- This is a smoke test only; count=1, default filters/jumps enabled.
- Consider re-running if the prime differs from expected or if wall time exceeds target (< ~250 ms).
