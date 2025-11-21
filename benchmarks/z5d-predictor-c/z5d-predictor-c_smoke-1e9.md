Conclusion: Predicted p_1000000000 ≈ 2.2801797563375461764651401773517071350342957620515848814993870805296885285906459113318134637543347e10 vs true 22801763489 (abs error 34074, rel error 1.494375e-6) in 31 ms.

Details:
- Command: /Users/velocityworks/IdeaProjects/z5d-prime-predictor/src/c/z5d-predictor-c/bin/z5d_cli 1000000000
- k input: 1000000000
- True p_k: 22801763489
- Predicted p_k: 2.2801797563375461764651401773517071350342957620515848814993870805296885285906459113318134637543347e10
- Absolute error: 34074
- Relative error: 1.494375e-6
- Time (ms): 31 (wall)
- Platform: Apple Silicon, MPFR/GMP via Homebrew; default precision in z5d-predictor-c.

Notes:
- Smoke test only; single k point at 1e9.
- Adjust P_TRUE/K_VAL if using a different reference point.
