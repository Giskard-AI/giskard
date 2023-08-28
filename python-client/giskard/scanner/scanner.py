import datetime
import uuid
import warnings
from collections import Counter
from time import perf_counter
from typing import Optional, Sequence

from giskard.client.python_utils import warning
from giskard.core.model_validation import ValidationFlags

from ..core.model_validation import validate_model
from ..datasets.base import Dataset
from ..models.base import BaseModel
from ..utils import fullname
from ..utils.analytics_collector import analytics, analytics_method, get_dataset_properties, get_model_properties
from .issues import DataLeakage, Issue, Stochasticity
from .logger import logger
from .registry import DetectorRegistry
from .report import ScanReport

MAX_ISSUES_PER_DETECTOR = 15


class Scanner:
    def __init__(self, params: Optional[dict] = None, only=None):
        if isinstance(only, str):
            only = [only]

        self.params = params or dict()
        self.only = only
        self.uuid = uuid.uuid4()

    def analyze(
        self,
        model: BaseModel,
        dataset: Optional[Dataset] = None,
        verbose=True,
        raise_exceptions=False,
        validation_flags: Optional[ValidationFlags] = ValidationFlags(),
    ) -> ScanReport:
        """Runs the analysis of a model and dataset, detecting issues."""

        # Check that the model and dataset were appropriately wrapped with Giskard
        if not isinstance(model, BaseModel):
            raise ValueError(
                "The model object you provided is not valid. Please wrap it with the `giskard.Model` class. "
                "See the instructions here: https://docs.giskard.ai/en/latest/guides/wrap_model/index.html"
            )

        if dataset is not None and not isinstance(dataset, Dataset):
            raise ValueError(
                "The dataset object you provided is not valid. Please wrap your dataframe with `giskard.Dataset`. "
                "You can follow the docs here: https://docs.giskard.ai/en/latest/guides/wrap_dataset/index.html"
            )

        # Some extra checks
        if model.is_text_generation:
            logger.warning(
                "LLM support is in alpha version — 🔥 things may break ! Please report any issues to https://github.com/giskard-AI/giskard/issues."
            )

        model, dataset = self._prepare_model_dataset(model, dataset)

        if not model.is_text_generation:
            time_start = perf_counter()
            validate_model(model=model, validate_ds=dataset, validation_flags=validation_flags)
            model_validation_time = perf_counter() - time_start
        else:
            model_validation_time = None

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

        num_features = len(model.meta.feature_names) if model.meta.feature_names else len(dataset.columns)
        if num_features > 100:
            warning(
                f"It looks like your dataset has a very large number of features ({num_features}), "
                "are you sure this is correct? The giskard.Dataset should be created from raw data *before* "
                "pre-processing (categorical encoding, vectorization, etc.). "
                "Check https://docs.giskard.ai/en/latest/guides/wrap_dataset/index.html for more details."
            )

        # Good, we can start
        maybe_print("🔎 Running scan…", verbose=verbose)
        time_start = perf_counter()

        # Collect the detectors
        detectors = self.get_detectors(tags=[model.meta.model_type.value])

        # @TODO: this should be selective to specific warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            issues, errors = self._run_detectors(
                detectors, model, dataset, verbose=verbose, raise_exceptions=raise_exceptions
            )

        elapsed = perf_counter() - time_start
        maybe_print(
            f"Scan completed: {len(issues) or 'no'} issue{'s' if len(issues) != 1 else ''} found. (Took {datetime.timedelta(seconds=elapsed)})",
            verbose=verbose,
        )
        if errors:
            warning(
                f"{len(errors)} errors were encountered while running detectors. Please check the log to understand what went wrong. "
                "You can run the scan again with `raise_exceptions=True` to disable graceful handling."
            )

        issues = self._postprocess(issues)
        self._collect_analytics(model, dataset, issues, elapsed, model_validation_time)

        return ScanReport(issues)

    def _run_detectors(self, detectors, model, dataset, verbose=True, raise_exceptions=False):
        if not detectors:
            raise RuntimeError("No issue detectors available. Scan will not be performed.")

        logger.info(f"Running detectors: {[d.__class__.__name__ for d in detectors]}")

        issues = []
        errors = []
        for detector in detectors:
            maybe_print(f"Running detector {detector.__class__.__name__}…", end="", verbose=verbose)
            detector_start = perf_counter()
            try:
                detected_issues = detector.run(model, dataset)
            except Exception as err:
                logger.error(f"Detector {detector.__class__.__name__} failed with error: {err}")
                errors.append((detector, err))
                analytics.track(
                    "scan:run-detector:error",
                    {
                        "scan_uuid": self.uuid.hex,
                        "detector": fullname(detector),
                        "error": str(err),
                        "error_class": fullname(err),
                    },
                )
                if raise_exceptions:
                    raise err

                detected_issues = []
            detected_issues = sorted(detected_issues, key=lambda i: -i.importance)[:MAX_ISSUES_PER_DETECTOR]
            detector_elapsed = perf_counter() - detector_start
            maybe_print(
                f" {len(detected_issues)} issues detected. (Took {datetime.timedelta(seconds=detector_elapsed)})",
                verbose=verbose,
            )
            analytics.track(
                "scan:detector-run",
                {
                    "scan_uuid": self.uuid.hex,
                    "detector": fullname(detector),
                    "detector_elapsed": detector_elapsed,
                    "detected_issues": len(detected_issues),
                },
            )

            issues.extend(detected_issues)

        return issues, errors

    def _postprocess(self, issues: Sequence[Issue]) -> Sequence[Issue]:
        # If we detected a Stochasticity issue, we will have a possibly false
        # positive DataLeakage issue. We remove it here.
        if any(issue.group == Stochasticity for issue in issues):
            issues = [issue for issue in issues if issue.group != DataLeakage]

        return issues

    def _prepare_model_dataset(self, model: BaseModel, dataset: Optional[Dataset]):
        if model.is_text_generation and dataset is None:
            logger.warning(
                "No dataset provided. We will use TruthfulQA as a default dataset. This involves rewriting your model prompt."
            )
            from .llm.utils import load_default_dataset

            dataset = load_default_dataset()
            model = model.rewrite_prompt(
                template="{question}", input_variables=["question"], feature_names=["question"]
            )

            return model, dataset

        if dataset is None:
            raise ValueError(f"Dataset must be provided for {model.meta.model_type.value} models.")

        return model, dataset

    @analytics_method
    def _collect_analytics(self, model, dataset, issues, elapsed, model_validation_time):
        issues_counter = Counter([fullname(i) for i in issues]) if issues else {}

        properties = dict(
            elapsed=elapsed,
            model_validation_time=model_validation_time,
            total_issues=len(issues),
            **issues_counter,
        )
        properties.update(get_model_properties(model))
        properties.update(get_dataset_properties(dataset))

        analytics.track("scan", properties)

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
