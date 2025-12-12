package z5d.predictor;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Java implementation of the Z5D predictor matching the calibrated C/Python path.
 * Closed-form estimator + local refinement to a probable prime.
 */
public final class Z5DPredictor {

    private Z5DPredictor() {}

    public static final String VERSION = "2.0.0";

    // Constants (match C/Python)
    private static final double C_CAL = -0.00247;
    private static final double KAPPA_STAR = 0.04449;
    private static final double E_FOURTH = Math.exp(4.0);

    private static final int MIN_WINDOW = 256;

    private static final int[] SMALL_PRIMES = {
            2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
            53, 59, 61, 67, 71, 73, 79, 83, 89, 97
    };

    private static final Map<Long, BigInteger> KNOWN_PRIMES;
    static {
        Map<Long, BigInteger> m = new LinkedHashMap<>();
        m.put(1L, bi("2"));
        m.put(10L, bi("29"));
        m.put(100L, bi("541"));
        m.put(1000L, bi("7919"));
        m.put(10000L, bi("104729"));
        m.put(100000L, bi("1299709"));
        m.put(1000000L, bi("15485863"));
        m.put(10000000L, bi("179424673"));
        m.put(100000000L, bi("2038074743"));
        m.put(1000000000L, bi("22801763489"));
        m.put(10000000000L, bi("252097800623"));
        m.put(100000000000L, bi("2760727302517"));
        m.put(1000000000000L, bi("29996224275833"));
        m.put(10000000000000L, bi("323780508946331"));
        m.put(100000000000000L, bi("3475385758524527"));
        m.put(1000000000000000L, bi("37124508045065437"));
        m.put(10000000000000000L, bi("394906913903735329"));
        m.put(100000000000000000L, bi("4185296581467695669"));
        m.put(1000000000000000000L, bi("44211790234832169331"));
        KNOWN_PRIMES = Collections.unmodifiableMap(m);
    }

    private static BigInteger bi(String s) {
        return new BigInteger(s);
    }

    /**
    * Public API: predict nth prime (probable prime; exact on grid).
    */
    public static PredictResult predictNthPrime(long n) {
        if (n < 1) throw new IllegalArgumentException("n must be >= 1");

        // Lookup fast path
        BigInteger known = KNOWN_PRIMES.get(n);
        if (known != null) {
            return new PredictResult(known, known, 0, true, "lookup");
        }

        BigInteger estimate = closedFormEstimateBig(n);
        BigInteger prime = refineToPrime(estimate);
        return new PredictResult(prime, estimate, 1, true, "z5d_closed_form+refine");
    }

    public static String getVersion() {
        return VERSION;
    }

    // ------------------- Internals -------------------

    private static BigInteger closedFormEstimateBig(long n) {
        if (n < 2) return BigInteger.valueOf(2);
        double ln = Math.log(n);
        double lnln = Math.log(ln);
        double pnt = n * (ln + lnln - 1.0 + (lnln - 2.0) / ln);
        double lnPnt = Math.log(pnt);
        double dTerm = Math.pow(lnPnt / E_FOURTH, 2.0) * pnt * C_CAL;
        double eTerm = Math.pow(pnt, -1.0 / 3.0) * pnt * KAPPA_STAR;
        double est = pnt + dTerm + eTerm;
        if (Double.isNaN(est) || est <= 0) est = pnt;
        BigDecimal bd = new BigDecimal(est, MathContext.DECIMAL64);
        return bd.setScale(0, RoundingMode.HALF_UP).toBigInteger();
    }

    private static BigInteger refineToPrime(BigInteger candidate) {
        if (candidate.compareTo(BigInteger.valueOf(3)) < 0) {
            candidate = BigInteger.valueOf(3);
        }
        if (candidate.mod(BigInteger.TWO).equals(BigInteger.ZERO)) {
            candidate = candidate.add(BigInteger.ONE);
        }
        candidate = snapTo6kPm1(candidate, +1);

        if (isAcceptablePrime(candidate)) return candidate;

        int window = Math.max(MIN_WINDOW, (int)Math.ceil(4.0 * Math.log(candidate.doubleValue())));
        for (int step = 1; step <= window; step++) {
            for (int dir : new int[]{+1, -1}) {
                BigInteger t = candidate.add(BigInteger.valueOf((long)dir * step));
                if (t.compareTo(BigInteger.valueOf(3)) < 0) continue;
                if (t.mod(BigInteger.TWO).equals(BigInteger.ZERO)) {
                    t = t.add(BigInteger.valueOf(dir > 0 ? 1 : -1));
                }
                t = snapTo6kPm1(t, dir);
                if (t.compareTo(BigInteger.valueOf(3)) < 0) continue;
                if (isAcceptablePrime(t)) return t;
            }
        }

        BigInteger t = candidate;
        while (true) {
            t = t.add(BigInteger.TWO);
            t = snapTo6kPm1(t, +1);
            if (isAcceptablePrime(t)) return t;
        }
    }

    private static boolean isAcceptablePrime(BigInteger n) {
        if (divisibleBySmallPrime(n)) return false;
        return n.isProbablePrime(50);
    }

    private static boolean divisibleBySmallPrime(BigInteger n) {
        for (int p : SMALL_PRIMES) {
            BigInteger bp = BigInteger.valueOf(p);
            if (n.equals(bp)) return false;
            if (n.mod(bp).equals(BigInteger.ZERO)) return true;
        }
        return false;
    }

    private static BigInteger snapTo6kPm1(BigInteger n, int direction) {
        BigInteger six = BigInteger.valueOf(6);
        BigInteger r = n.mod(six);
        long rv = r.longValue();
        long delta = 0;
        if (direction < 0) {
            if (rv == 0) delta = 1;
            else if (rv == 2) delta = 1;
            else if (rv == 3) delta = 2;
            else if (rv == 4) delta = 3;
        } else {
            if (rv == 0) delta = 1;
            else if (rv == 2) delta = 3;
            else if (rv == 3) delta = 2;
            else if (rv == 4) delta = 1;
        }
        if (delta == 0) return n;
        if (direction < 0) return n.subtract(BigInteger.valueOf(delta));
        return n.add(BigInteger.valueOf(delta));
    }
}
