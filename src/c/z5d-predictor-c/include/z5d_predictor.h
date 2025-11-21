/**
 * Z5D nth-Prime Predictor - Public API
 * =====================================
 * 
 * High-precision C/MPFR implementation of Z5D nth-prime predictor using
 * Newton-Halley refinement to invert R(x) = n, where R(x) is the Riemann
 * prime-counting function.
 * 
 * @file z5d_predictor.h
 * @version 1.0
 * @author Unified Framework Team
 */

#ifndef Z5D_PREDICTOR_H
#define Z5D_PREDICTOR_H

#include <stdio.h>
#include <stdint.h>
#include <mpfr.h>
#include <gmp.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Library version */
#define Z5D_PREDICTOR_VERSION "1.0.0"

/* Default precision in bits (equivalent to ~96 decimal places, comfortable for 10^12+) */
#define Z5D_DEFAULT_PRECISION 320

/* Default number of terms in Riemann R series (K=10 for better accuracy) */
#define Z5D_DEFAULT_K 10

/**
 * Result structure for nth prime prediction
 */
typedef struct {
    mpfr_t predicted_prime;  /* Predicted value of p_n */
    mpfr_t error;            /* Estimated error bound */
    double elapsed_ms;       /* Computation time in milliseconds */
    int iterations;          /* Number of Newton-Halley iterations performed */
    int converged;           /* 1 if converged, 0 otherwise */
} z5d_result_t;

/**
 * Configuration for predictor
 */
typedef struct {
    mpfr_prec_t precision;   /* MPFR precision in bits */
    int K;                   /* Number of terms in R(x) series */
    int max_iterations;      /* Maximum Newton-Halley iterations */
    mpfr_t tolerance;        /* Convergence tolerance */
} z5d_config_t;

/**
 * Initialize library (must be called before using library)
 */
void z5d_init(void);

/**
 * Cleanup library (call when done)
 */
void z5d_cleanup(void);

/**
 * Get library version string
 */
const char* z5d_get_version(void);

/**
 * Initialize configuration with default values
 * 
 * @param config Configuration structure to initialize
 */
void z5d_config_init(z5d_config_t* config);

/**
 * Cleanup configuration
 * 
 * @param config Configuration structure to cleanup
 */
void z5d_config_clear(z5d_config_t* config);

/**
 * Initialize result structure
 * 
 * @param result Result structure to initialize
 * @param precision MPFR precision to use
 */
void z5d_result_init(z5d_result_t* result, mpfr_prec_t precision);

/**
 * Cleanup result structure
 * 
 * @param result Result structure to cleanup
 */
void z5d_result_clear(z5d_result_t* result);

/**
 * Predict the nth prime using default configuration
 * 
 * @param result Output result structure (must be initialized)
 * @param n Index of prime to predict (n >= 1)
 * @return 0 on success, negative on error
 */
int z5d_predict_nth_prime(z5d_result_t* result, uint64_t n);

/**
 * Predict the nth prime with custom configuration
 * 
 * @param result Output result structure (must be initialized)
 * @param n Index of prime to predict (n >= 1)
 * @param config Custom configuration
 * @return 0 on success, negative on error
 */
int z5d_predict_nth_prime_ex(z5d_result_t* result, uint64_t n, const z5d_config_t* config);

/**
 * Compute Riemann R(x) function
 * R(x) = sum_{k=1..K} μ(k)/k * li(x^{1/k})
 * 
 * @param rop Output value
 * @param x Input value
 * @param K Number of terms in series
 * @param prec MPFR precision
 */
void z5d_riemann_R(mpfr_t rop, const mpfr_t x, int K, mpfr_prec_t prec);

/**
 * Compute derivative R'(x)
 * R'(x) = (1/ln x) * sum_{k=1..K} μ(k)/k * x^{1/k - 1}
 * 
 * @param rop Output value
 * @param x Input value
 * @param K Number of terms in series
 * @param prec MPFR precision
 */
void z5d_riemann_R_prime(mpfr_t rop, const mpfr_t x, int K, mpfr_prec_t prec);

/**
 * Möbius function μ(n)
 * 
 * @param n Input integer
 * @return μ(n): 0 if n has squared factor, (-1)^k if n is product of k distinct primes
 */
int z5d_mobius(int n);

#ifdef __cplusplus
}
#endif

#endif /* Z5D_PREDICTOR_H */
