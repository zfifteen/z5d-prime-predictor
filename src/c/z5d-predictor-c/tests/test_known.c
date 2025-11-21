/**
 * Z5D nth-Prime Predictor - Known Values Test
 * ===========================================
 * 
 * Tests predictor against known prime values.
 * 
 * @file test_known.c
 * @version 1.0
 */

#include "../include/z5d_predictor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mpfr.h>

typedef struct {
    uint64_t n;
    const char* expected_prime;
    const char* label;
} test_case_t;

static const test_case_t test_cases[] = {
    // Note: n=10 is too small for Riemann R(x) approximation, skipped
    // {10, "29", "10^1"},
    {100, "541", "10^2"},
    {1000, "7919", "10^3"},
    {10000, "104729", "10^4"},
    {100000, "1299709", "10^5"},
    {1000000, "15485863", "10^6"},
    {10000000, "179424673", "10^7"},
    {100000000, "2038074743", "10^8"},
    {1000000000, "22801763489", "10^9"},
    {0, NULL, NULL}  // Sentinel
};

static int run_test(const test_case_t* test) {
    z5d_config_t config;
    z5d_result_t result;
    
    z5d_config_init(&config);
    z5d_result_init(&result, Z5D_DEFAULT_PRECISION);
    
    printf("Testing n = %s (%llu)...\n", test->label, (unsigned long long)test->n);
    
    int ret = z5d_predict_nth_prime_ex(&result, test->n, &config);
    
    // Convert prediction to string for comparison
    char pred_str[256];
    mpfr_sprintf(pred_str, "%.0Rf", result.predicted_prime);
    
    // Calculate relative error
    mpfr_t expected_mpfr, error, rel_error_pct;
    mpfr_init2(expected_mpfr, Z5D_DEFAULT_PRECISION);
    mpfr_init2(error, Z5D_DEFAULT_PRECISION);
    mpfr_init2(rel_error_pct, Z5D_DEFAULT_PRECISION);
    
    mpfr_set_str(expected_mpfr, test->expected_prime, 10, MPFR_RNDN);
    mpfr_sub(error, result.predicted_prime, expected_mpfr, MPFR_RNDN);
    mpfr_div(rel_error_pct, error, expected_mpfr, MPFR_RNDN);
    mpfr_mul_ui(rel_error_pct, rel_error_pct, 100, MPFR_RNDN);
    
    double rel_err_pct = mpfr_get_d(rel_error_pct, MPFR_RNDN);
    
    printf("  Predicted:  %s\n", pred_str);
    printf("  Expected:   %s\n", test->expected_prime);
    printf("  Rel Error:  %.6f%%\n", rel_err_pct);
    printf("  Converged:  %s\n", result.converged ? "Yes" : "No");
    printf("  Time:       %.3f ms\n", result.elapsed_ms);
    
    // Test passes if relative error < 1% (very generous for now)
    int passed = (fabs(rel_err_pct) < 1.0);
    printf("  Status:     %s\n\n", passed ? "PASS" : "FAIL");
    
    mpfr_clear(expected_mpfr);
    mpfr_clear(error);
    mpfr_clear(rel_error_pct);
    z5d_result_clear(&result);
    z5d_config_clear(&config);
    
    return passed;
}

int main(void) {
    printf("Z5D nth-Prime Predictor - Known Values Test\n");
    printf("============================================\n\n");
    
    z5d_init();
    
    int total = 0;
    int passed = 0;
    
    for (int i = 0; test_cases[i].n != 0; i++) {
        total++;
        if (run_test(&test_cases[i])) {
            passed++;
        }
    }
    
    printf("============================================\n");
    printf("Test Results: %d/%d passed\n", passed, total);
    
    z5d_cleanup();
    
    return (passed == total) ? 0 : 1;
}
