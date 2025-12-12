package z5d.predictor;

import java.math.BigInteger;

/**
 * Result record for Z5D predictions.
 */
public record PredictResult(
        BigInteger prime,
        BigInteger estimate,
        int iterations,
        boolean converged,
        String method) {
}
