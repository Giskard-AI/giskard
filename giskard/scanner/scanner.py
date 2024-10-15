from typing import Optional, Sequence

import datetime
import logging
import uuid
import warnings
from collections import Counter
from time import perf_counter

import pandas as pd

from ..client.python_utils import warning
from ..core.model_validation import validate_model
from ..datasets.base import Dataset
from ..llm.client import get_default_client
from ..llm.errors import LLMGenerationError
from ..llm.utils import generate_test_dataset
from ..models.base import BaseModel
from ..utils import fullname
from ..utils.analytics_collector import (
    analytics,
    analytics_method,
    get_dataset_properties,
    get_model_properties,
)
from ..utils.logging_utils import TemporaryRootLogLevel
from .issues import DataLeakage, Issue, Stochasticity
from .logger import logger
from .registry import DetectorRegistry
from .report import ScanReport

COST_ESTIMATE_TEMPLATE = """Estimated calls to your model: ~{num_model_calls}
Estimated LLM calls for evaluation: {num_llm_calls}
"""

COST_SUMMARY_TEMPLATE = """LLM-assisted detectors have used the following resources:
OpenAI LLM calls for evaluation: {num_llm_calls} ({num_llm_prompt_tokens} prompt tokens and {num_llm_sampled_tokens} sampled tokens)
"""

# Hardcoded for now…
PROMPT_TOKEN_COST = 0.03e-3
SAMPLED_TOKEN_COST = 0.06e-3


class Scanner:
    def __init__(self, params: Optional[dict] = None, only=None):
        """Scanner for model issues & vulnerabilities.

        Parameters
        ----------
        params : dict
            Advanced configuration of the detectors, in the form of arguments for each detector, keyed by detector id.
            For example, ``params={"performance_bias": {"metrics": ["accuracy"], "threshold": 0.10}}`` will set the
            ``metrics`` and ``threshold`` parameters of the ``performance_bias`` detector (check the detector classes
            for information about detector identifier and  accepted parameters).
        only : Sequence[str]
            A tag list to limit the scan to a subset of detectors. For example,
            ``giskard.scan(model, dataset, only=["performance"])`` will only run detectors for performance issues.
        """
        if isinstance(only, str):
            only = [only]

        self.params = params or dict()
        self.only = only
        self.uuid = uuid.uuid4()

    def analyze(
        self,
        model: BaseModel,
        dataset: Optional[Dataset] = None,
        features: Optional[Sequence[str]] = None,
        verbose=True,
        raise_exceptions=False,
        max_issues_per_detector=15,
    ) -> ScanReport:
        """Runs the analysis of a model and dataset, detecting issues.

        Parameters
        ----------
        model : BaseModel
            A Giskard model object.
        dataset : Dataset
            A Giskard dataset object.
        features : Sequence[str], optional
            A list of features to analyze. If not provided, all model features will be analyzed.
        verbose : bool
            Whether to print detailed info messages. Enabled by default.
        raise_exceptions : bool
            Whether to raise an exception if detection errors are encountered. By default, errors are logged and
            handled gracefully, without interrupting the scan.
        max_issues_per_detector : int
            Maximal number of issues per detector in the report

        Returns
        -------
        ScanReport
            A report object containing the detected issues and other information.
        """
        with TemporaryRootLogLevel(logging.INFO if verbose else logging.NOTSET):
            # Check that the model and dataset were appropriately wrapped with Giskard
            model, dataset, model_validation_time = self._validate_model_and_dataset(model, dataset)

            # Check that provided features are valid
            features = self._validate_features(features, model, dataset)

            # Initialize LLM logger if needed
            if model.is_text_generation:
                llm_logger = _maybe_get_llm_logger()
                llm_logger is not None and llm_logger.reset()

            # Good, we can start
            maybe_print("🔎 Running scan…", verbose=verbose)
            time_start = perf_counter()

            # Collect the detectors
            detectors = self.get_detectors(tags=[model.meta.model_type.value])
            detectors_names = [detector.__class__.__name__ for detector in detectors]

            # Print cost estimate
            if verbose:
                self._print_cost_estimate(model, dataset, detectors)

            # @TODO: this should be selective to specific warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                issues, errors = self._run_detectors(
                    detectors,
                    model,
                    dataset,
                    features,
                    verbose=verbose,
                    raise_exceptions=raise_exceptions,
                    max_issues_per_detector=max_issues_per_detector,
                )

            issues = self._postprocess(issues)

            # Scan completed
            elapsed = perf_counter() - time_start

            if verbose:
                self._print_execution_summary(model, issues, errors, elapsed)

            self._collect_analytics(model, dataset, issues, elapsed, model_validation_time, detectors)

        return ScanReport(issues, model=model, dataset=dataset, detectors_names=detectors_names)

    def _run_detectors(
        self, detectors, model, dataset, features, verbose=True, raise_exceptions=False, max_issues_per_detector=None
    ):
        if not detectors:
            raise RuntimeError("No issue detectors available. Scan will not be performed.")

        logger.info(f"Running detectors: {[d.__class__.__name__ for d in detectors]}")

        issues = []
        errors = []
        for detector in detectors:
            maybe_print(f"Running detector {detector.__class__.__name__}…", verbose=verbose)
            detector_start = perf_counter()
            try:
                detected_issues = detector.run(model, dataset, features=features)
            except Exception as err:
                logger.exception(f"Detector {detector.__class__.__name__} failed with error: {err}")
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
            detected_issues = sorted(detected_issues, key=lambda i: -i.importance)[:max_issues_per_detector]
            detector_elapsed = perf_counter() - detector_start
            maybe_print(
                f"{detector.__class__.__name__}: {len(detected_issues)} issue{'s' if len(detected_issues) > 1 else ''} detected. (Took {datetime.timedelta(seconds=detector_elapsed)})",
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

    def _validate_model_and_dataset(self, model, dataset):
        if not isinstance(model, BaseModel):
            raise ValueError(
                "The model object you provided is not valid. Please wrap it with the `giskard.Model` class. "
                "See the instructions here: https://docs.giskard.ai/en/stable/guides/wrap_model/index.html"
            )

        if dataset is not None and not isinstance(dataset, Dataset):
            raise ValueError(
                "The dataset object you provided is not valid. Please wrap your dataframe with `giskard.Dataset`. "
                "You can follow the docs here: https://docs.giskard.ai/en/stable/guides/wrap_dataset/index.html"
            )

        model, dataset = self._prepare_model_dataset(model, dataset)

        if not model.is_text_generation:
            time_start = perf_counter()
            validate_model(model=model, validate_ds=dataset)
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

        return model, dataset, model_validation_time

    def _validate_features(
        self, features: Optional[Sequence[str]], model: BaseModel, dataset: Optional[Dataset] = None
    ):
        _default_features = model.meta.feature_names or dataset.columns.drop(dataset.target, errors="ignore")

        if features is None:
            features = _default_features
        else:
            if not set(features).issubset(_default_features):
                raise ValueError(
                    "The `features` argument contains invalid feature names: "
                    f"{', '.join(set(features) - set(_default_features))}. "
                    f"Valid features for this model are: {', '.join(_default_features)}."
                )

        if len(features) < 1:
            raise ValueError(
                "No features to scan. Please provide a non-empty list of features to scan,"
                "and ensure that you correctly set the `features_names` argument when wrapping your model."
            )

        if len(features) > 100:
            warning(
                f"It looks like your dataset has a very large number of features ({len(features)}), "
                "are you sure this is correct? The giskard.Dataset should be created from raw data *before* "
                "pre-processing (categorical encoding, vectorization, etc.). "
                "You can also limit the number of features to scan by setting the `features` argument. "
                "Check https://docs.giskard.ai/en/stable/guides/wrap_dataset/index.html for more details."
            )

        return list(features)

    def _prepare_model_dataset(self, model: BaseModel, dataset: Optional[Dataset]):
        if model.is_text_generation and dataset is None:
            logger.debug("Automatically generating test dataset.")
            try:
                return model, generate_test_dataset(model)
            except LLMGenerationError:
                warning(
                    "Failed to generate test dataset. Trying to run the scan with an empty dataset. For improved results, please provide a test dataset."
                )
                return model, Dataset(pd.DataFrame([], columns=model.meta.feature_names))

        if dataset is None:
            raise ValueError(f"Dataset must be provided for {model.meta.model_type.value} models.")

        return model, dataset

    @analytics_method
    def _collect_analytics(self, model, dataset, issues, elapsed, model_validation_time, detectors):
        issues_counter = Counter([fullname(i) for i in issues]) if issues else {}

        properties = dict(
            elapsed=elapsed,
            model_validation_time=model_validation_time,
            total_issues=len(issues),
            detectors=[d.__class__.__name__ for d in detectors],
            **issues_counter,
        )
        properties.update(get_model_properties(model))
        properties.update(get_dataset_properties(dataset))

        cost_estimate = self._get_cost_estimate(model, dataset, detectors)
        properties.update(cost_estimate)

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

    def _get_cost_estimate(self, model, dataset, detectors):
        cost_estimates = [d.get_cost_estimate(model, dataset) for d in detectors if hasattr(d, "get_cost_estimate")]

        # Counts
        num_model_calls = sum(c.get("model_predict_calls", 0) for c in cost_estimates)
        num_llm_calls = sum(c.get("llm_calls", 0) for c in cost_estimates)
        num_llm_prompt_tokens = sum(c.get("llm_prompt_tokens", 0) for c in cost_estimates)
        num_llm_sampled_tokens = sum(c.get("llm_sampled_tokens", 0) for c in cost_estimates)

        estimated_usd = PROMPT_TOKEN_COST * num_llm_prompt_tokens + SAMPLED_TOKEN_COST * num_llm_sampled_tokens

        return {
            "num_model_calls": num_model_calls,
            "num_llm_calls": num_llm_calls,
            "num_llm_prompt_tokens": num_llm_prompt_tokens,
            "num_llm_sampled_tokens": num_llm_sampled_tokens,
            "estimated_usd": estimated_usd,
        }

    def _get_cost_measure(self):
        llm_logger = _maybe_get_llm_logger()
        if llm_logger is None:
            return None

        num_calls = llm_logger.get_num_calls()
        num_prompt_tokens = llm_logger.get_num_prompt_tokens()
        num_sampled_tokens = llm_logger.get_num_sampled_tokens()

        return {
            "num_llm_calls": num_calls,
            "num_llm_prompt_tokens": num_prompt_tokens,
            "num_llm_sampled_tokens": num_sampled_tokens,
            "estimated_usd": PROMPT_TOKEN_COST * num_prompt_tokens + SAMPLED_TOKEN_COST * num_sampled_tokens,
        }

    def _print_cost_estimate(self, model, dataset, detectors):
        if model.is_text_generation:
            estimates = self._get_cost_estimate(model, dataset, detectors)
            print(COST_ESTIMATE_TEMPLATE.format(num_detectors=len(detectors), **estimates))

    def _print_execution_summary(self, model, issues, errors, elapsed):
        print(
            f"Scan completed: {len(issues) or 'no'} issue{'s' if len(issues) != 1 else ''} found. (Took {datetime.timedelta(seconds=elapsed)})"
        )
        if model.is_text_generation:
            measured = self._get_cost_measure()
            if measured is not None:
                print(COST_SUMMARY_TEMPLATE.format(**measured))
        if errors:
            warning(
                f"{len(errors)} errors were encountered while running detectors. Please check the log to understand what went wrong. "
                "You can run the scan again with `raise_exceptions=True` to disable graceful handling."
            )


def maybe_print(*args, **kwargs):
    if kwargs.pop("verbose", True):
        print(*args, **kwargs)


def _maybe_get_llm_logger():
    """Get the LLM client logger if available."""
    try:
        return get_default_client().logger
    except Exception:
        return None
