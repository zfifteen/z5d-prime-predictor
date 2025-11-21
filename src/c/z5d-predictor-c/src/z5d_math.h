/**
 * Z5D Mathematical Functions - Internal Header
 * ============================================
 * 
 * Internal mathematical functions for Z5D predictor.
 * 
 * @file z5d_math.h
 * @version 1.0
 */

#ifndef Z5D_MATH_H
#define Z5D_MATH_H

#include <mpfr.h>

/**
 * Compute logarithmic integral li(x) using MPFR
 * 
 * @param rop Output value
 * @param x Input value
 * @param prec MPFR precision
 */
void z5d_li(mpfr_t rop, const mpfr_t x, mpfr_prec_t prec);

/**
 * Compute Dusart initializer for nth prime
 * x0 = n * (ln n + ln ln n - 1 + (ln ln n - 2)/ln n)
 * 
 * @param rop Output value
 * @param n Index of prime
 * @param prec MPFR precision
 */
void z5d_dusart_initializer(mpfr_t rop, const mpfr_t n, mpfr_prec_t prec);

/**
 * Perform one Newton-Halley iteration step
 * Solves R(x) = n for x
 * 
 * @param rop Output value (new x)
 * @param x Current x value
 * @param n Target n value
 * @param K Number of terms in R(x)
 * @param prec MPFR precision
 * @return 0 on success, negative on error
 */
int z5d_newton_halley_step(mpfr_t rop, const mpfr_t x, const mpfr_t n, int K, mpfr_prec_t prec);

#endif /* Z5D_MATH_H */
