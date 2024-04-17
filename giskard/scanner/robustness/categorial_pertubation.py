from typing import Sequence, Optional

from adc import abstractmethod 

from ..datasets.base import Dataset 
from 
from ..issues import Robustness
from ..registry import Detector 
from .feature_transformation import CategorialTransformation


class BaseCategorialPertubationDetector(Detector):
    """Base class for metamorphic detectors based on categorial feature"""
    _issue_group = Robustness
    # @TODO : Reserch for the adapted value for the taxonomy.
    _taxonomy = None 

    def __init__(
            self, 
            transformations: Optional[Sequence[CategorialTransformation]] = None, 
            threshold: Optional[float] = None, 
            output_sensitivity: Optional[float] = None, 
            num_samples: Optional[int] = None,
    ):
        """
        Create a new instance of the detector 
        # @TODO : Reread the docstring in order to make open source ready
        Parameters 
        ----------
        transformations: Optional[Sequence[CategorialTransformation]]
            The categorial transformation used in the metamorphic test. If not provided, a default set of transformation will be used.
        threshold: Optional[float]
            The threshold for the fail rate, which is defined as the proportion of samples for which the model
            prediction has changed. If the fail rate is greater than the threshold, an issue is created.
            If not provided, a default threshold will be used.
        output_sensitivity: Optional[float]
            For regression models, the output sensitivity is the maximum relative change in the prediction that is
            considered acceptable. If the relative change is greater than the output sensitivity, an issue is created.
            This parameter is ignored for classification models. If not provided, a default output sensitivity will be
            used.
        num_samples: Optional[int]
            The maximum number of samples to use for the metamorphic testing. If not provided, a default number of
            samples will be used.
        """
        self.transformations = transformations
        self.threshold = threshold
        self.num_samples = num_samples
        self.output_sensitivity = output_sensitivity

        def run()
        ...