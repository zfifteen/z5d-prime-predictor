import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from z5d_predictor import predict_nth_prime, get_version, Z5D_PREDICTOR_VERSION


KNOWN = [
    (1, 2),
    (10, 29),
    (100, 541),
    (1000, 7919),
    (10000, 104729),
    (100000, 1299709),
    (1000000, 15485863),
    (10000000, 179424673),
    (100000000, 2038074743),
    (1000000000, 22801763489),
]


class TestPredictor(unittest.TestCase):
    def test_version(self):
        self.assertEqual(get_version(), Z5D_PREDICTOR_VERSION)
        self.assertEqual(Z5D_PREDICTOR_VERSION, "2.0.0")

    def test_known_grid_exact(self):
        for n, p in KNOWN:
            with self.subTest(n=n):
                res = predict_nth_prime(n)
                self.assertEqual(res.prime, p)
                self.assertTrue(res.converged)

    def test_refinement_moves_to_prime(self):
        # Choose an n where estimate is near but not equal to p_n (medium scale)
        n = 1234567
        res = predict_nth_prime(n)
        self.assertTrue(res.prime % 2 == 1)
        # simple Fermat check base 2 to ensure compositeness unlikely
        self.assertEqual(pow(2, res.prime - 1, res.prime), 1)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            predict_nth_prime(0)
        with self.assertRaises(ValueError):
            predict_nth_prime(-5)


if __name__ == "__main__":
    unittest.main()
