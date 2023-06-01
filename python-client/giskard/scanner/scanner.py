import warnings
from typing import Optional, Sequence

from ..models.base import BaseModel
from ..datasets.base import Dataset
from ..core.model_validation import validate_model
from .registry import DetectorRegistry
from .result import ScanResult


MAX_ISSUES_PER_DETECTOR = 15


class Scanner:
    def __init__(self, params: Optional[dict] = None, only=None):
        if isinstance(only, str):
            only = [only]

        self.params = params or dict()
        self.only = only

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
        classes = DetectorRegistry.get_detector_classes(tags=tags)

        # Filter detector classes
        if self.only:
            only_classes = DetectorRegistry.get_detector_classes(tags=self.only)
            keys_to_keep = set(only_classes.keys()).intersection(classes.keys())
            classes = {k: classes[k] for k in keys_to_keep}

        # Configure instances
        for name, detector_cls in classes.items():
            kwargs = self.params.get(name) or dict()
            detectors.append(detector_cls(**kwargs))

        return detectors
