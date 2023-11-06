"""
This module contains detectors that measure the performance of a model to spot potential performance problems. In
particular, we aim at detecting performance problems affecting specific subpopulations of the data (data slices).

For example, consider a census model that performs well on the overall population but performs poorly on a specific
subpopulation (e.g. age < 30). This is a performance problem that we want to detect.
"""
from .performance_bias_detector import PerformanceBiasDetector

__all__ = ["PerformanceBiasDetector"]
