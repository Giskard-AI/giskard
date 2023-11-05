"""
This module contains detectors that measure the robustness of a model to spot potential robustness problems. For
classification models, this means detecting a change in the predicted class as a result of a small change in the input
data. For regression models, this means detecting a significant variation in the predicted value as a result of a small
change in the input features.

These detectors are generally based on some form of metamorphic invariance testing, e.g. by applying a transformation
to the input data that is not supposed to affect the output significantly, and compare the output of the model before
and after the transformation.
"""
from .base_detector import BaseTextPerturbationDetector
from .ethical_bias_detector import EthicalBiasDetector
from .text_perturbation_detector import TextPerturbationDetector

__all__ = ["EthicalBiasDetector", "TextPerturbationDetector", "BaseTextPerturbationDetector"]
