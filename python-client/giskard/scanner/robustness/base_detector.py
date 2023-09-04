from abc import abstractmethod
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..issues import Issue, IssueLevel, Robustness
from ..llm.utils import LLMImportError
from ..logger import logger
from ..registry import Detector
from .text_transformations import TextTransformation


class BaseTextPerturbationDetector(Detector):
    _issue_group = Robustness

    def __init__(
        self,
        transformations: Optional[Sequence[TextTransformation]] = None,
        threshold: Optional[float] = None,
        output_sensitivity=None,
        num_samples: Optional[int] = None,
    ):
        self.transformations = transformations
        self.threshold = threshold
        self.num_samples = num_samples
        self.output_sensitivity = output_sensitivity

    def run(self, model: BaseModel, dataset: Dataset) -> Sequence[Issue]:
        transformations = self.transformations or self._get_default_transformations(model, dataset)
        features = [
            col
            for col, col_type in dataset.column_types.items()
            if col_type == "text" and pd.api.types.is_string_dtype(dataset.df[col].dtype)
        ]

        # Only analyze the model features
        if model.meta.feature_names:
            features = [f for f in features if f in model.meta.feature_names]

        logger.info(
            f"{self.__class__.__name__}: Running with transformations={[t.name for t in transformations]} "
            f"threshold={self.threshold} output_sensitivity={self.output_sensitivity} num_samples={self.num_samples}"
        )

        issues = []
        for transformation in transformations:
            issues.extend(self._detect_issues(model, dataset, transformation, features))

        return [i for i in issues if i is not None]

    @abstractmethod
    def _get_default_transformations(self, model: BaseModel, dataset: Dataset) -> Sequence[TextTransformation]:
        ...

    def _detect_issues(
        self,
        model: BaseModel,
        dataset: Dataset,
        transformation: TextTransformation,
        features: Sequence[str],
    ) -> Sequence[Issue]:
        num_samples = self.num_samples or _get_default_num_samples(model)
        output_sensitivity = self.output_sensitivity or _get_default_output_sensitivity(model)
        threshold = self.threshold or _get_default_threshold(model)

        issues = []
        # @TODO: integrate this with Giskard metamorphic tests already present
        for feature in features:
            transformation_fn = transformation(column=feature)
            transformed = dataset.transform(transformation_fn)

            # Select only the records which were changed
            changed_idx = dataset.df.index[transformed.df[feature] != dataset.df[feature]]

            if changed_idx.empty:
                continue

            # Select a random subset of the changed records
            if len(changed_idx) > num_samples:
                rng = np.random.default_rng(747)
                changed_idx = changed_idx[rng.choice(len(changed_idx), num_samples, replace=False)]

            original_data = Dataset(
                dataset.df.loc[changed_idx],
                target=dataset.target,
                column_types=dataset.column_types,
                validation=False,
            )
            perturbed_data = Dataset(
                transformed.df.loc[changed_idx],
                target=dataset.target,
                column_types=dataset.column_types,
                validation=False,
            )

            # Calculate predictions
            original_pred = model.predict(original_data)
            perturbed_pred = model.predict(perturbed_data)

            if model.is_classification:
                passed = original_pred.raw_prediction == perturbed_pred.raw_prediction
            elif model.is_regression:
                rel_delta = _relative_delta(perturbed_pred.raw_prediction, original_pred.raw_prediction)
                passed = np.abs(rel_delta) < output_sensitivity
            elif model.is_text_generation:
                try:
                    import evaluate
                except ImportError as err:
                    raise LLMImportError() from err

                scorer = evaluate.load("bertscore")
                score = scorer.compute(
                    predictions=perturbed_pred.prediction,
                    references=original_pred.prediction,
                    model_type="distilbert-base-multilingual-cased",
                    idf=True,
                )
                passed = np.array(score["f1"]) > 1 - output_sensitivity
            else:
                raise NotImplementedError("Only classification, regression, or text generation models are supported.")

            pass_rate = passed.mean()
            fail_rate = 1 - pass_rate
            logger.info(
                f"{self.__class__.__name__}: Testing `{feature}` for perturbation `{transformation.name}`\tFail rate: {fail_rate:.3f}"
            )

            if fail_rate >= threshold:
                # Severity
                issue_level = IssueLevel.MAJOR if fail_rate >= 2 * threshold else IssueLevel.MEDIUM

                # Prepare examples dataframe
                examples = original_data.df.loc[~passed, (feature,)].copy()
                examples[f"{transformation_fn.name}({feature})"] = perturbed_data.df.loc[~passed, feature]
                examples["Original prediction"] = original_pred.prediction[~passed]
                examples["Prediction after perturbation"] = perturbed_pred.prediction[~passed]

                # Description
                desc = "When we perturb the content of feature “{feature}” with the transformation “{transformation_fn}” (see examples below), your model changes its prediction in about {fail_rate_percent}% of the cases. We expected the predictions not to be affected by this transformation."

                issue = Issue(
                    model,
                    dataset,
                    group=self._issue_group,
                    level=issue_level,
                    transformation_fn=transformation_fn,
                    description=desc,
                    meta={
                        "feature": feature,
                        "domain": f"Feature `{feature}`",
                        "deviation": f"{round(fail_rate * 100, 2)}% of tested samples changed prediction after perturbation",
                        "fail_rate": fail_rate,
                        "fail_rate_percent": round(fail_rate * 100, 2),
                        "metric": "Fail rate",
                        "metric_value": fail_rate,
                        "threshold": threshold,
                        "output_sentitivity": output_sensitivity,
                        "perturbed_data_slice": perturbed_data,
                        "perturbed_data_slice_predictions": perturbed_pred,
                    },
                    importance=fail_rate,
                    examples=examples,
                    tests=_generate_robustness_tests,
                )

                issues.append(issue)

        return issues


def _generate_robustness_tests(issue: Issue):
    from ...testing.tests.metamorphic import test_metamorphic_invariance

    # Only generates a single metamorphic test
    return {
        f"Invariance to “{issue.transformation_fn}”": test_metamorphic_invariance(
            model=issue.model,
            dataset=issue.dataset,
            transformation_function=issue.transformation_fn,
            slicing_function=None,
            threshold=1 - issue.meta["threshold"],
            output_sensitivity=issue.meta["output_sentitivity"],
        )
    }


def _relative_delta(actual, reference):
    return (actual - reference) / reference


def _get_default_num_samples(model) -> int:
    if model.is_text_generation:
        return 10

    return 1_000


def _get_default_output_sensitivity(model) -> float:
    if model.is_text_generation:
        return 0.15

    return 0.05


def _get_default_threshold(model) -> float:
    if model.is_text_generation:
        return 0.10

    return 0.05
