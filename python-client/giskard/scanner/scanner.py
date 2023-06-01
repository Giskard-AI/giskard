import warnings
from typing import Optional, Sequence

from ..models.base import BaseModel
from ..datasets.base import Dataset
from ..core.model_validation import validate_model
from .registry import DetectorRegistry
from .result import ScanResult


MAX_ISSUES_PER_DETECTOR = 15


class Scanner:
    def __init__(self, params: Optional[dict] = None):
        self.params = params or dict()

    def analyze(self, model: BaseModel, dataset: Dataset) -> ScanResult:
        """Runs the analysis of a model and dataset, detecting issues."""
        validate_model(model=model, validate_ds=dataset)

        # Collect the detectors
        detectors = self.get_detectors(tags=[model.meta.model_type.value])

        # @TODO: this should be selective to specific warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            issues = []
            for detector in detectors:
                issues.extend(
                    sorted(detector.run(model, dataset), key=lambda i: -i.importance)[:MAX_ISSUES_PER_DETECTOR]
                )

        return ScanResult(issues)

    def get_detectors(self, tags: Optional[Sequence[str]] = None) -> Sequence:
        """Returns the detector instances."""
        detectors = []
        classes = DetectorRegistry.get_detector_classes(tags=tags or [])
        for name, detector_cls in classes.items():
            kwargs = self.params.get(name) or dict()
            detectors.append(detector_cls(**kwargs))
        return detectors
