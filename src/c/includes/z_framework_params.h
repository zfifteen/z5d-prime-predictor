/**
 * Z Framework Parameter Standardization (C Header)
 * ===============================================
 *
 * This header provides standardized parameter values for C implementations,
 * ensuring consistency with the Python framework parameters defined in
 * src/core/params.py.
 *
 * These parameters address the k parameter standardization issue by providing:
 * - Distinct variable names for different contexts (geodesic vs Z_5D vs nth prime)
 * - Empirically validated optimal values with bootstrap confidence intervals
 * - Frame-normalized consistency (Δₙ via κ(n) = d(n) · ln(n+1)/e²)
 *
 * @file z_framework_params.h
 * @author Z Framework Team
 * @version 2.0 (Parameter Standardization)
 */

#ifndef Z_FRAMEWORK_PARAMS_H
#define Z_FRAMEWORK_PARAMS_H

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================================
 * PRECISION SETTINGS (from src/core/params.py)
 * ======================================================================================== */

/* Precision for all calculations */
#define ZF_MP_DPS                    50

/* Dynamic precision settings for adaptive scaling */
#define ZF_MP_DPS_HIGH              50      /* For Δₙ < 10^-16 or high-precision requirements */
#define ZF_MP_DPS_MEDIUM            30      /* For standard calculations with k error threshold */
#define ZF_MP_DPS_LOW               15      /* For quick approximations or large scale computations */

/* Scale thresholds for dynamic precision */
#define ZF_PRECISION_SCALE_THRESHOLD_HIGH    1e-16  /* Switch to high precision below this delta */
#define ZF_PRECISION_SCALE_THRESHOLD_MEDIUM  1e-10  /* Switch to medium precision below this */
#define ZF_K_SCALE_THRESHOLD_HIGH            1e10   /* Use high precision above this k value */
#define ZF_K_SCALE_THRESHOLD_ULTRA           1e12   /* Ultra-scale threshold for warnings */

/* Bootstrap resampling defaults for statistical validation */
#define ZF_BOOTSTRAP_RESAMPLES_DEFAULT       1000
#define ZF_BOOTSTRAP_CI_ALPHA               0.05   /* For 95% confidence intervals */

/* ========================================================================================
 * GEODESIC MAPPING PARAMETERS (kappa_geo) - from src/core/params.py
 * ======================================================================================== */

/* Geodesic exponent (fractional) for prime-density mapping */
/* Optimal for conditional prime density improvement under canonical benchmark methodology */
/* CI [14.6%, 15.4%] at higher N; bootstrap-validated */
/* Context: θ'(n, k) = φ * {n/φ}^k geodesic transformation */
#define ZF_KAPPA_GEO_DEFAULT        0.3
#define ZF_MIN_KAPPA_GEO            0.05   /* Avoid near-zero fractals that cause numerical instability */
#define ZF_MAX_KAPPA_GEO            10.0

/* Geodesic optimization bounds and resolution */
#define ZF_KAPPA_GEO_GRID_STEP      0.01   /* Grid search resolution */
#define ZF_KAPPA_GEO_GRID_RANGE_MIN 0.05   /* Extended range for optimization */
#define ZF_KAPPA_GEO_GRID_RANGE_MAX 0.5

/* ========================================================================================
 * Z_5D CALIBRATION PARAMETERS (kappa_star) - from src/core/params.py
 * ======================================================================================== */

/* Z_5D calibration factor for e-term scaling */
/* Reverted to optimal value for ultra-low Z_5D errors (<0.01% at k=10^5) */
/* Context: Enhanced prediction with curvature correction */
#define ZF_KAPPA_STAR_DEFAULT       0.04449  /* *** KEY PARAMETER from params.py *** */
#define ZF_MIN_KAPPA_STAR           0.001
#define ZF_MAX_KAPPA_STAR           1.0

/* Z_5D additional calibration parameters */
#define ZF_Z5D_C_CALIBRATED         -0.00247  /* From least-squares optimization */
#define ZF_Z5D_VARIANCE_TARGET      0.118     /* Target variance for geodesic scaling */

/* ========================================================================================
 * NTH PRIME INDEX PARAMETERS (k_nth) - from src/core/params.py
 * ======================================================================================== */

/* Prime index bounds for nth prime calculations */
/* Context: Predicting the k_nth prime where k_nth is large integer */
#define ZF_MIN_K_NTH                2         /* Minimum meaningful prime index */
#define ZF_MAX_K_NTH_VALIDATED      1e12      /* Empirically validated up to this scale */
#define ZF_MAX_K_NTH_COMPUTATIONAL  1e16      /* Computational framework supports with extrapolation */

/* ========================================================================================
 * ENHANCEMENT CALCULATION STANDARDS - from src/core/params.py
 * ======================================================================================== */

/* Statistical rigor requirements for enhancement calculations */
#define ZF_ENHANCEMENT_MIN_SAMPLES          10    /* Minimum samples for reliable analysis */
#define ZF_ENHANCEMENT_DEFAULT_BINS         50    /* Default histogram bins */
#define ZF_ENHANCEMENT_EXPECTED_RANGE_MIN   0     /* Expected realistic enhancement percentage range */
#define ZF_ENHANCEMENT_EXPECTED_RANGE_MAX   5

/* Bootstrap validation settings */
#define ZF_ENHANCEMENT_BOOTSTRAP_SAMPLES    1000
#define ZF_ENHANCEMENT_CI_PERCENTILE_LOW    2.5   /* For 95% CI */
#define ZF_ENHANCEMENT_CI_PERCENTILE_HIGH   97.5

/* ========================================================================================
 * SHA MATCHING VALIDATION THRESHOLDS - from src/core/params.py
 * ======================================================================================== */

/* SHA matching score threshold for metrics locking */
#define ZF_SHA_MATCHING_SCORE_THRESHOLD     0.85

/* Pearson correlation threshold for zeta-SHA consistency */
#define ZF_PEARSON_CORRELATION_THRESHOLD    0.93

/* Pass rate threshold for validation tests */
#define ZF_PASS_RATE_THRESHOLD              0.8

/* ========================================================================================
 * MATHEMATICAL CONSTANTS
 * ======================================================================================== */

#define ZF_E_SQUARED                7.38905609893065   /* e^2 */
#define ZF_E_FOURTH                 54.59815003314424  /* e^4 */
#define ZF_GOLDEN_PHI               1.61803398874989   /* Golden ratio φ */
#define ZF_PI                       3.14159265358979   /* π */

/* ========================================================================================
 * PARAMETER VALIDATION HELPERS
 * ======================================================================================== */

/**
 * Validate kappa_geo parameter bounds
 * Returns 1 if valid, 0 if invalid
 */
static inline int zf_validate_kappa_geo(double kappa_geo) {
    return (kappa_geo >= ZF_MIN_KAPPA_GEO && kappa_geo <= ZF_MAX_KAPPA_GEO);
}

/**
 * Validate kappa_star parameter bounds
 * Returns 1 if valid, 0 if invalid
 */
static inline int zf_validate_kappa_star(double kappa_star) {
    return (kappa_star >= ZF_MIN_KAPPA_STAR && kappa_star <= ZF_MAX_KAPPA_STAR);
}

/**
 * Validate k_nth parameter bounds
 * Returns 1 if valid, 0 if invalid
 */
static inline int zf_validate_k_nth(double k_nth) {
    return (k_nth >= ZF_MIN_K_NTH && k_nth <= ZF_MAX_K_NTH_COMPUTATIONAL);
}

/**
 * Get standardized Z5D calibration parameters
 * Returns standardized parameter values from params.py
 */
typedef struct {
    double c;
    double kappa_star;
    double kappa_geo;
} zf_standard_params_t;

static inline zf_standard_params_t zf_get_standard_params(void) {
    zf_standard_params_t params = {
        .c = ZF_Z5D_C_CALIBRATED,
        .kappa_star = ZF_KAPPA_STAR_DEFAULT,
        .kappa_geo = ZF_KAPPA_GEO_DEFAULT
    };
    return params;
}

/* ========================================================================================
 * PARAMETER INFORMATION
 * ======================================================================================== */

/**
 * Print parameter standardization information
 */
static inline void zf_print_parameter_info(void) {
    printf("Z Framework Parameter Standardization\n");
    printf("=====================================\n");
    printf("Parameter standardization addresses k parameter overloading.\n");
    printf("  - kappa_geo: Geodesic exponent (fractional, %.3f)\n", ZF_KAPPA_GEO_DEFAULT);
    printf("  - kappa_star: Z_5D calibration factor (%.5f)\n", ZF_KAPPA_STAR_DEFAULT);
    printf("  - k_nth: Prime index (large integers, %d to %.0e)\n", ZF_MIN_K_NTH, ZF_MAX_K_NTH_COMPUTATIONAL);
    printf("\nThese values are synchronized with src/core/params.py\n");
    printf("Bootstrap validation: %d resamples, %.0f%% CI\n", 
           ZF_BOOTSTRAP_RESAMPLES_DEFAULT, (1.0 - ZF_BOOTSTRAP_CI_ALPHA) * 100.0);
}

#ifdef __cplusplus
}
#endif

#endif /* Z_FRAMEWORK_PARAMS_H */