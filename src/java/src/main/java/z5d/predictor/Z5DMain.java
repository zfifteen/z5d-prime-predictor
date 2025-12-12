package z5d.predictor;

import java.math.BigInteger;

/**
 * Minimal CLI entry point: java -cp build/classes/java/main z5d.predictor.Z5DMain <n>
 */
public final class Z5DMain {
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java -cp <classes> z5d.predictor.Z5DMain <n>");
            System.exit(1);
        }
        try {
            BigInteger n = new BigInteger(args[0]);
            PredictResult res = Z5DPredictor.predictNthPrimeBig(n);
            BigInteger prime = res.prime();
            System.out.println(prime);
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }
}
