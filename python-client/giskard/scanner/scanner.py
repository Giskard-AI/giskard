import datetime
import warnings
from collections import Counter
from time import perf_counter
from typing import Optional, Sequence

from .issues import Issue
from .logger import logger
from .registry import DetectorRegistry
from .result import ScanResult
from ..core.model_validation import validate_model
from ..datasets.base import Dataset
from ..models.base import BaseModel, WrapperModel
from ..utils import fullname
from ..utils.analytics_collector import analytics
from giskard.client.python_utils import warning

MAX_ISSUES_PER_DETECTOR = 15


class Scanner:
    def __init__(self, params: Optional[dict] = None, only=None):
        if isinstance(only, str):
            only = [only]

        self.params = params or dict()
        self.only = only

    def analyze(self, model: BaseModel, dataset: Dataset, verbose=True) -> ScanResult:
        """Runs the analysis of a model and dataset, detecting issues."""
        validate_model(model=model, validate_ds=dataset)

        if not dataset.df.index.is_unique:
            warning(
                "You dataframe has duplicate indexes, which is currently not supported. "
                "We have to reset the dataframe index to avoid issues."
            )
            dataset = Dataset(
                df=dataset.df.reset_index(drop=True),
                name=dataset.name,
                target=dataset.target,
                column_types=dataset.column_types,
            )

        maybe_print("Running scan…", verbose=verbose)
        time_start = perf_counter()

        # Collect the detectors
        detectors = self.get_detectors(tags=[model.meta.model_type.value])

        if not detectors:
            raise RuntimeError("No issue detectors available. Scan will not be performed.")

        logger.info(f"Running detectors: {[d.__class__.__name__ for d in detectors]}")

        # @TODO: this should be selective to specific warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            issues = []
            for detector in detectors:
                maybe_print(f"Running detector {detector.__class__.__name__}…", end="", verbose=verbose)
                detector_start = perf_counter()
                detected_issues = detector.run(model, dataset)
                detected_issues = sorted(detected_issues, key=lambda i: -i.importance)[:MAX_ISSUES_PER_DETECTOR]
                detector_elapsed = perf_counter() - detector_start
                maybe_print(
                    f" {len(detected_issues)} issues detected. (Took {datetime.timedelta(seconds=detector_elapsed)})",
                    verbose=verbose,
                )
                issues.extend(detected_issues)

        elapsed = perf_counter() - time_start
        maybe_print(
            f"Scan completed: {len(issues) or 'no'} issue{'s' if len(issues) != 1 else ''} found. (Took {datetime.timedelta(seconds=elapsed)})",
            verbose=verbose,
        )

        issues = self._postprocess(issues)
        self._collect_analytics(model, dataset, issues, elapsed)

        return ScanResult(issues)

    def _postprocess(self, issues: Sequence[Issue]) -> Sequence[Issue]:
        # If we detected a StochasticityIssue, we will have a possibly false
        # positive DataLeakageIssue. We remove it here.
        from .stochasticity.stochasticity_detector import StochasticityIssue
        from .data_leakage.data_leakage_detector import DataLeakageIssue

        if any(isinstance(issue, StochasticityIssue) for issue in issues):
            issues = [issue for issue in issues if not isinstance(issue, DataLeakageIssue)]

        return issues

    def _collect_analytics(self, model, dataset, issues, elapsed):
        inner_model_class = fullname(model.model) if isinstance(model, WrapperModel) else None
        issues_cnt = Counter([fullname(i) for i in issues]) if issues else {}

        analytics.track(
            "scan",
            {
                "model_class": fullname(model),
                "inner_model_class": inner_model_class,
                "model_id": str(model.id),
                "model_type": model.meta.model_type.value,
                "dataset_id": str(dataset.id),
                "elapsed": elapsed,
                **issues_cnt
            },
        )

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


def maybe_print(*args, **kwargs):
    if kwargs.pop("verbose", True):
        print(*args, **kwargs)
