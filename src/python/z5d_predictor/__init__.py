"""
Z5D nth-Prime Predictor (Python)
--------------------------------
Parity with the revised C predictor: closed-form estimator + discrete
refinement returning a probable prime (exact on the benchmark grid).
"""

from .predictor import PredictResult, Z5D_PREDICTOR_VERSION, get_version, predict_nth_prime

__version__ = Z5D_PREDICTOR_VERSION

__all__ = [
    "PredictResult",
    "predict_nth_prime",
    "get_version",
    "Z5D_PREDICTOR_VERSION",
]
