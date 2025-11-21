/**
 * Z5D nth-Prime Predictor - Core Implementation
 * =============================================
 * 
 * High-precision implementation using MPFR for solving R(x) = n
 * to predict the nth prime.
 * 
 * @file z5d_predictor.c
 * @version 1.0
 */

#include "../include/z5d_predictor.h"
#include "z5d_math.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>

/* Static flag for initialization */
static int z5d_initialized = 0;

/* Precomputed Möbius function values for k=1..15 for better performance */
static const int MOBIUS_TABLE[16] = {
    0, 1, -1, -1, 0, -1, 1, -1, 0, 0, 1, -1, 0, -1, 1, 1
};

void z5d_init(void) {
    if (!z5d_initialized) {
        mpfr_set_default_prec(Z5D_DEFAULT_PRECISION);
        z5d_initialized = 1;
    }
}

void z5d_cleanup(void) {
    if (z5d_initialized) {
        mpfr_free_cache();
        z5d_initialized = 0;
    }
}

const char* z5d_get_version(void) {
    return Z5D_PREDICTOR_VERSION;
}

void z5d_config_init(z5d_config_t* config) {
    config->precision = Z5D_DEFAULT_PRECISION;
    config->K = Z5D_DEFAULT_K;
    config->max_iterations = 10;
    mpfr_init2(config->tolerance, Z5D_DEFAULT_PRECISION);
    mpfr_set_d(config->tolerance, 1e-50, MPFR_RNDN);
}

void z5d_config_clear(z5d_config_t* config) {
    mpfr_clear(config->tolerance);
}

void z5d_result_init(z5d_result_t* result, mpfr_prec_t precision) {
    mpfr_init2(result->predicted_prime, precision);
    mpfr_init2(result->error, precision);
    result->elapsed_ms = 0.0;
    result->iterations = 0;
    result->converged = 0;
}

void z5d_result_clear(z5d_result_t* result) {
    mpfr_clear(result->predicted_prime);
    mpfr_clear(result->error);
}

/**
 * Möbius function using precomputed table for k ≤ 15
 * Falls back to trial division for k > 15 (rarely needed with K ≤ 15)
 */
int z5d_mobius(int n) {
    // Use precomputed table for n ≤ 15
    if (n >= 1 && n <= 15) {
        return MOBIUS_TABLE[n];
    }
    
    // Fallback for n > 15
    if (n == 1) return 1;
    
    int prime_factors = 0;
    int temp_n = n;
    
    for (int i = 2; i * i <= temp_n; i++) {
        if (temp_n % i == 0) {
            prime_factors++;
            temp_n /= i;
            if (temp_n % i == 0) {
                return 0;
            }
        }
    }
    
    if (temp_n > 1) {
        prime_factors++;
    }
    
    return (prime_factors % 2) ? -1 : 1;
}

/**
 * Compute Riemann R(x) function
 */
void z5d_riemann_R(mpfr_t rop, const mpfr_t x, int K, mpfr_prec_t prec) {
    mpfr_t sum, term, x_power, li_val, k_mpfr, mu_k;
    
    mpfr_init2(sum, prec);
    mpfr_init2(term, prec);
    mpfr_init2(x_power, prec);
    mpfr_init2(li_val, prec);
    mpfr_init2(k_mpfr, prec);
    mpfr_init2(mu_k, prec);
    
    mpfr_set_ui(sum, 0, MPFR_RNDN);
    
    for (int k = 1; k <= K; k++) {
        int mu = z5d_mobius(k);
        if (mu == 0) continue;
        
        // x^(1/k)
        mpfr_set_ui(k_mpfr, k, MPFR_RNDN);
        mpfr_ui_div(k_mpfr, 1, k_mpfr, MPFR_RNDN);  // 1/k
        mpfr_pow(x_power, x, k_mpfr, MPFR_RNDN);
        
        // li(x^(1/k))
        z5d_li(li_val, x_power, prec);
        
        // term = μ(k)/k * li(x^(1/k))
        mpfr_set_si(mu_k, mu, MPFR_RNDN);
        mpfr_div_ui(term, mu_k, k, MPFR_RNDN);
        mpfr_mul(term, term, li_val, MPFR_RNDN);
        
        // sum += term
        mpfr_add(sum, sum, term, MPFR_RNDN);
    }
    
    mpfr_set(rop, sum, MPFR_RNDN);
    
    mpfr_clear(sum);
    mpfr_clear(term);
    mpfr_clear(x_power);
    mpfr_clear(li_val);
    mpfr_clear(k_mpfr);
    mpfr_clear(mu_k);
}

/**
 * Compute R'(x) derivative
 */
void z5d_riemann_R_prime(mpfr_t rop, const mpfr_t x, int K, mpfr_prec_t prec) {
    mpfr_t sum, term, x_power, ln_x, k_mpfr, mu_k, exponent;
    
    mpfr_init2(sum, prec);
    mpfr_init2(term, prec);
    mpfr_init2(x_power, prec);
    mpfr_init2(ln_x, prec);
    mpfr_init2(k_mpfr, prec);
    mpfr_init2(mu_k, prec);
    mpfr_init2(exponent, prec);
    
    mpfr_set_ui(sum, 0, MPFR_RNDN);
    mpfr_log(ln_x, x, MPFR_RNDN);
    
    for (int k = 1; k <= K; k++) {
        int mu = z5d_mobius(k);
        if (mu == 0) continue;
        
        // exponent = 1/k - 1
        mpfr_set_ui(k_mpfr, k, MPFR_RNDN);
        mpfr_ui_div(exponent, 1, k_mpfr, MPFR_RNDN);
        mpfr_sub_ui(exponent, exponent, 1, MPFR_RNDN);
        
        // x^(1/k - 1)
        mpfr_pow(x_power, x, exponent, MPFR_RNDN);
        
        // term = μ(k)/k * x^(1/k - 1)
        mpfr_set_si(mu_k, mu, MPFR_RNDN);
        mpfr_div_ui(term, mu_k, k, MPFR_RNDN);
        mpfr_mul(term, term, x_power, MPFR_RNDN);
        
        // sum += term
        mpfr_add(sum, sum, term, MPFR_RNDN);
    }
    
    // R'(x) = sum / ln(x)
    mpfr_div(rop, sum, ln_x, MPFR_RNDN);
    
    mpfr_clear(sum);
    mpfr_clear(term);
    mpfr_clear(x_power);
    mpfr_clear(ln_x);
    mpfr_clear(k_mpfr);
    mpfr_clear(mu_k);
    mpfr_clear(exponent);
}

/**
 * Get current time in milliseconds
 */
static double get_time_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * 1000.0 + tv.tv_usec / 1000.0;
}

int z5d_predict_nth_prime(z5d_result_t* result, uint64_t n) {
    z5d_config_t config;
    z5d_config_init(&config);
    int ret = z5d_predict_nth_prime_ex(result, n, &config);
    z5d_config_clear(&config);
    return ret;
}

int z5d_predict_nth_prime_ex(z5d_result_t* result, uint64_t n, const z5d_config_t* config) {
    if (n == 0) return -1;
    if (!z5d_initialized) z5d_init();
    
    double start_time = get_time_ms();
    
    mpfr_t n_mpfr, x_current, x_next, delta;
    
    mpfr_init2(n_mpfr, config->precision);
    mpfr_init2(x_current, config->precision);
    mpfr_init2(x_next, config->precision);
    mpfr_init2(delta, config->precision);
    
    // Convert n to MPFR
    mpfr_set_ui(n_mpfr, n, MPFR_RNDN);
    
    // Compute Dusart initializer
    z5d_dusart_initializer(x_current, n_mpfr, config->precision);
    
    // Newton iteration
    result->converged = 0;
    for (int iter = 0; iter < config->max_iterations; iter++) {
        result->iterations = iter + 1;
        
        // Perform one Newton step
        int ret = z5d_newton_halley_step(x_next, x_current, n_mpfr, config->K, config->precision);
        if (ret != 0) {
            break;  // Failed to converge
        }
        
        // Check convergence: |x_next - x_current| < tolerance
        mpfr_sub(delta, x_next, x_current, MPFR_RNDN);
        mpfr_abs(delta, delta, MPFR_RNDN);
        
        if (mpfr_cmp(delta, config->tolerance) < 0) {
            result->converged = 1;
            mpfr_set(result->predicted_prime, x_next, MPFR_RNDN);
            break;
        }
        
        // Update for next iteration
        mpfr_set(x_current, x_next, MPFR_RNDN);
    }
    
    // If not converged in loop, still return last value
    if (!result->converged) {
        mpfr_set(result->predicted_prime, x_next, MPFR_RNDN);
    }
    
    // Estimate error as last delta
    mpfr_set(result->error, delta, MPFR_RNDN);
    
    result->elapsed_ms = get_time_ms() - start_time;
    
    mpfr_clear(n_mpfr);
    mpfr_clear(x_current);
    mpfr_clear(x_next);
    mpfr_clear(delta);
    
    return result->converged ? 0 : -1;
}
