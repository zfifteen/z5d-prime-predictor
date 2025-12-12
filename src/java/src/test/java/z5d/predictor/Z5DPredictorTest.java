package z5d.predictor;

import org.junit.jupiter.api.Test;

import java.math.BigInteger;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class Z5DPredictorTest {

    private static final List<long[]> KNOWN = List.of(
            new long[]{1L, 2L},
            new long[]{10L, 29L},
            new long[]{100L, 541L},
            new long[]{1000L, 7919L},
            new long[]{10000L, 104729L},
            new long[]{100000L, 1299709L},
            new long[]{1000000L, 15485863L},
            new long[]{10000000L, 179424673L},
            new long[]{100000000L, 2038074743L},
            new long[]{1000000000L, 22801763489L}
    );

    @Test
    void versionMatches() {
        assertEquals("2.0.0", Z5DPredictor.getVersion());
    }

    @Test
    void knownGridExact() {
        for (long[] pair : KNOWN) {
            long n = pair[0];
            long p = pair[1];
            PredictResult res = Z5DPredictor.predictNthPrime(n);
            assertEquals(BigInteger.valueOf(p), res.prime());
            assertTrue(res.converged());
        }
    }

    @Test
    void offGridRefinementProducesProbablePrime() {
        long n = 1_234_567L;
        PredictResult res = Z5DPredictor.predictNthPrime(n);
        BigInteger p = res.prime();
        // quick Fermat base 2 check for plausibility
        assertEquals(BigInteger.ONE, BigInteger.valueOf(2).modPow(p.subtract(BigInteger.ONE), p));
    }

    @Test
    void invalidInputThrows() {
        assertThrows(IllegalArgumentException.class, () -> Z5DPredictor.predictNthPrime(0));
        assertThrows(IllegalArgumentException.class, () -> Z5DPredictor.predictNthPrime(-5));
    }
}
