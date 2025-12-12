/**
 * Z5D nth-Prime Predictor - Medium Scale Test
 * ===========================================
 * 
 * Tests predictor at medium scales (10^10 - 10^12).
 * 
 * @file test_medium_scale.c
 * @version 1.0
 */

#include "../include/z5d_predictor.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <mpfr.h>
#include <string.h>

typedef struct {
    uint64_t n;
    const char* expected_prime;
    const char* label;
} test_case_t;

static const test_case_t test_cases[] = {
    {10000000000ULL, "252097800623", "10^10"},
    {100000000000ULL, "2760727302517", "10^11"},
    {1000000000000ULL, "29996224275833", "10^12"},
    {0, NULL, NULL}  // Sentinel
};

static int run_test(const test_case_t* test) {
    printf("Testing n = %s (%llu)...\n", test->label, (unsigned long long)test->n);
    
    mpz_t prime;
    mpz_init(prime);
    z5d_predict_nth_prime_mpz(prime, test->n);

    printf("  Predicted:  ");
    gmp_printf("%Zd\n", prime);
    printf("  Expected:   %s\n", test->expected_prime);

    char* prime_str = mpz_get_str(NULL, 10, prime);
    int passed = prime_str && strcmp(prime_str, test->expected_prime) == 0;
    free(prime_str);
    printf("  Status:     %s\n\n", passed ? "PASS" : "FAIL");
    mpz_clear(prime);
    
    return passed;
}

int main(void) {
    printf("Z5D nth-Prime Predictor - Medium Scale Test\n");
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
