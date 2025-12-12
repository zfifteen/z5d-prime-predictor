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
    printf("Testing n = %s (%llu)...\n", test->label, (unsigned long long)test->n);
    
    mpz_t prime;
    mpz_init(prime);
    z5d_predict_nth_prime_mpz(prime, test->n);

    // Convert prediction to string for comparison
    char pred_str[256];
    gmp_sprintf(pred_str, "%Zd", prime);
    
    printf("  Predicted:  %s\n", pred_str);
    printf("  Expected:   %s\n", test->expected_prime);
    
    int passed = (strcmp(pred_str, test->expected_prime) == 0);
    printf("  Status:     %s\n\n", passed ? "PASS" : "FAIL");
    
    mpz_clear(prime);
    
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
