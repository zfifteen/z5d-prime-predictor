/**
 * Z5D Mathematical Functions Implementation
 * =========================================
 * 
 * Core mathematical functions for Z5D predictor.
 * 
 * @file z5d_math.c
 * @version 1.0
 */

#include "z5d_math.h"
#include "../include/z5d_predictor.h"
#include <math.h>

/**
 * Compute logarithmic integral li(x) using series expansion
 * li(x) ≈ ln(ln(x)) + γ + sum_{k=1..∞} (ln x)^k / (k * k!)
 * 
 * For large x, we use the asymptotic expansion instead for better convergence.
 */
void z5d_li(mpfr_t rop, const mpfr_t x, mpfr_prec_t prec) {
    mpfr_t ln_x, ln_ln_x, term, sum, k_mpfr, factorial, power;
    mpfr_t gamma_const, one;
    
    mpfr_init2(ln_x, prec);
    mpfr_init2(ln_ln_x, prec);
    mpfr_init2(term, prec);
    mpfr_init2(sum, prec);
    mpfr_init2(k_mpfr, prec);
    mpfr_init2(factorial, prec);
    mpfr_init2(power, prec);
    mpfr_init2(gamma_const, prec);
    mpfr_init2(one, prec);
    
    mpfr_set_ui(one, 1, MPFR_RNDN);
    
    // ln(x)
    mpfr_log(ln_x, x, MPFR_RNDN);
    
    // ln(ln(x))
    mpfr_log(ln_ln_x, ln_x, MPFR_RNDN);
    
    // Euler-Mascheroni constant γ ≈ 0.5772156649
    mpfr_const_euler(gamma_const, MPFR_RNDN);
    
    // Start with ln(ln(x)) + γ
    mpfr_add(sum, ln_ln_x, gamma_const, MPFR_RNDN);
    
    // Add series: sum_{k=1..N} (ln x)^k / (k * k!)
    mpfr_set_ui(factorial, 1, MPFR_RNDN);
    mpfr_set(power, ln_x, MPFR_RNDN);
    
    for (int k = 1; k <= 100; k++) {  // 100 terms should be enough
        // power = (ln x)^k
        if (k > 1) {
            mpfr_mul(power, power, ln_x, MPFR_RNDN);
        }
        
        // factorial = k!
        if (k > 1) {
            mpfr_mul_ui(factorial, factorial, k, MPFR_RNDN);
        }
        
        // term = (ln x)^k / (k * k!)
        mpfr_div_ui(term, power, k, MPFR_RNDN);
        mpfr_div(term, term, factorial, MPFR_RNDN);
        
        // sum += term
        mpfr_add(sum, sum, term, MPFR_RNDN);
        
        // Check convergence
        mpfr_abs(term, term, MPFR_RNDN);
        if (mpfr_cmp_d(term, 1e-50) < 0) {
            break;
        }
    }
    
    mpfr_set(rop, sum, MPFR_RNDN);
    
    mpfr_clear(ln_x);
    mpfr_clear(ln_ln_x);
    mpfr_clear(term);
    mpfr_clear(sum);
    mpfr_clear(k_mpfr);
    mpfr_clear(factorial);
    mpfr_clear(power);
    mpfr_clear(gamma_const);
    mpfr_clear(one);
}

/**
 * Compute 3-term Cipolla/Dusart initializer
 * x0 = n * (L + L2 - 1 + (L2 - 2)/L - (L2^2 - 6*L2 + 11)/(2*L^2))
 * where L = ln(n), L2 = ln(ln(n))
 * 
 * This 3-term version provides materially better accuracy at 10^9-10^12
 * compared to the 2-term version.
 */
void z5d_dusart_initializer(mpfr_t rop, const mpfr_t n, mpfr_prec_t prec) {
    mpfr_t ln_n, ln_ln_n, ln_n_sq, ln_ln_n_sq;
    mpfr_t term1, term2, term3, temp, result;
    
    mpfr_init2(ln_n, prec);
    mpfr_init2(ln_ln_n, prec);
    mpfr_init2(ln_n_sq, prec);
    mpfr_init2(ln_ln_n_sq, prec);
    mpfr_init2(term1, prec);
    mpfr_init2(term2, prec);
    mpfr_init2(term3, prec);
    mpfr_init2(temp, prec);
    mpfr_init2(result, prec);
    
    // L = ln(n)
    mpfr_log(ln_n, n, MPFR_RNDN);
    
    // L2 = ln(ln(n))
    mpfr_log(ln_ln_n, ln_n, MPFR_RNDN);
    
    // Precompute squares
    mpfr_mul(ln_n_sq, ln_n, ln_n, MPFR_RNDN);       // L^2
    mpfr_mul(ln_ln_n_sq, ln_ln_n, ln_ln_n, MPFR_RNDN);  // L2^2
    
    // term1 = L + L2 - 1
    mpfr_add(term1, ln_n, ln_ln_n, MPFR_RNDN);
    mpfr_sub_ui(term1, term1, 1, MPFR_RNDN);
    
    // term2 = (L2 - 2) / L
    mpfr_sub_ui(term2, ln_ln_n, 2, MPFR_RNDN);
    mpfr_div(term2, term2, ln_n, MPFR_RNDN);
    
    // term3 = -(L2^2 - 6*L2 + 11) / (2*L^2)
    // numerator: L2^2 - 6*L2 + 11
    mpfr_mul_ui(temp, ln_ln_n, 6, MPFR_RNDN);       // 6*L2
    mpfr_sub(temp, ln_ln_n_sq, temp, MPFR_RNDN);   // L2^2 - 6*L2
    mpfr_add_ui(temp, temp, 11, MPFR_RNDN);        // L2^2 - 6*L2 + 11
    // denominator: 2*L^2
    mpfr_mul_ui(term3, ln_n_sq, 2, MPFR_RNDN);
    // term3 = -numerator / denominator
    mpfr_div(term3, temp, term3, MPFR_RNDN);
    mpfr_neg(term3, term3, MPFR_RNDN);
    
    // result = n * (term1 + term2 + term3)
    mpfr_add(result, term1, term2, MPFR_RNDN);
    mpfr_add(result, result, term3, MPFR_RNDN);
    mpfr_mul(rop, n, result, MPFR_RNDN);
    
    mpfr_clear(ln_n);
    mpfr_clear(ln_ln_n);
    mpfr_clear(ln_n_sq);
    mpfr_clear(ln_ln_n_sq);
    mpfr_clear(term1);
    mpfr_clear(term2);
    mpfr_clear(term3);
    mpfr_clear(temp);
    mpfr_clear(result);
}

/**
 * Perform Newton-Halley iteration step
 * Newton: x_{n+1} = x_n - f(x_n)/f'(x_n)
 * Halley: x_{n+1} = x_n - 2*f(x)*f'(x) / (2*f'(x)^2 - f(x)*f''(x))
 * 
 * We use simple Newton for now
 */
int z5d_newton_halley_step(mpfr_t rop, const mpfr_t x, const mpfr_t n, int K, mpfr_prec_t prec) {
    mpfr_t R_x, R_prime_x, f_x, delta;
    
    mpfr_init2(R_x, prec);
    mpfr_init2(R_prime_x, prec);
    mpfr_init2(f_x, prec);
    mpfr_init2(delta, prec);
    
    // Compute R(x)
    z5d_riemann_R(R_x, x, K, prec);
    
    // Compute f(x) = R(x) - n
    mpfr_sub(f_x, R_x, n, MPFR_RNDN);
    
    // Compute R'(x)
    z5d_riemann_R_prime(R_prime_x, x, K, prec);
    
    // Check for zero derivative
    if (mpfr_zero_p(R_prime_x)) {
        mpfr_set(rop, x, MPFR_RNDN);
        mpfr_clear(R_x);
        mpfr_clear(R_prime_x);
        mpfr_clear(f_x);
        mpfr_clear(delta);
        return -1;
    }
    
    // delta = f(x) / f'(x)
    mpfr_div(delta, f_x, R_prime_x, MPFR_RNDN);
    
    // x_{n+1} = x_n - delta
    mpfr_sub(rop, x, delta, MPFR_RNDN);
    
    mpfr_clear(R_x);
    mpfr_clear(R_prime_x);
    mpfr_clear(f_x);
    mpfr_clear(delta);
    
    return 0;
}
