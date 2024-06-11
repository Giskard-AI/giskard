from typing import Sequence

import pandas as pd

from ...datasets import Dataset
from ...models.base import BaseModel
from ...registry.slicing_function import SlicingFunction
from ...testing.tests.calibration import (
    _calculate_overconfidence_score,
    _default_overconfidence_threshold,
)
from ..common.examples import ExampleExtractor
from ..common.loss_based_detector import LossBasedDetector
from ..decorators import detector
from ..issues import Issue, IssueLevel, Overconfidence
from ..logger import logger


@detector(name="overconfidence", tags=["overconfidence", "classification"])
class OverconfidenceDetector(LossBasedDetector):
    def __init__(self, threshold=0.10, p_threshold=None, method="tree", **kwargs):
        self.threshold = threshold
        self.p_threshold = p_threshold
        self.method = method
        super().__init__(**kwargs)

    @property
    def _numerical_slicer_method(self):
        return self.method

    def run(self, model: BaseModel, dataset: Dataset, features: Sequence[str]):
        if not model.is_classification:
            raise ValueError("Overconfidence bias detector only works for classification models.")

        return super().run(model, dataset, features)

    def _calculate_loss(self, model: BaseModel, dataset: Dataset) -> pd.DataFrame:
        loss = _calculate_overconfidence_score(model, dataset).to_frame(self.LOSS_COLUMN_NAME)
        return loss[loss[self.LOSS_COLUMN_NAME] > 0]

    def _find_issues(
        self,
        slices: Sequence[SlicingFunction],
        model: BaseModel,
        dataset: Dataset,
        meta: pd.DataFrame,
    ) -> Sequence[Issue]:
        # Add the loss column to the dataset
        dataset_with_meta = Dataset(
            dataset.df.join(meta, how="left"),
            target=dataset.target,
            column_types=dataset.column_types,
        )
        # For performance
        dataset_with_meta.load_metadata_from_instance(dataset.column_meta)

        p_threshold = self.p_threshold or _default_overconfidence_threshold(model)
        logger.info(f"{self.__class__.__name__}: Using overconfidence threshold = {p_threshold}")

        reference_rate = (dataset_with_meta.df[self.LOSS_COLUMN_NAME].dropna() > p_threshold).mean()

        issues = []
        for slice_fn in slices:
            sliced_dataset = dataset_with_meta.slice(slice_fn)

            slice_rate = (sliced_dataset.df[self.LOSS_COLUMN_NAME].dropna() > p_threshold).mean()
            fail_idx = (
                sliced_dataset.df[(sliced_dataset.df[self.LOSS_COLUMN_NAME] > p_threshold)]
                .sort_values(self.LOSS_COLUMN_NAME, ascending=False)
                .index
            )
            relative_delta = (slice_rate - reference_rate) / reference_rate

            # Skip non representative slices
            # @TODO: do this with a statistical test instead of filtering by count only (GSK-1279)
            if len(fail_idx) < 20:
                continue

            if relative_delta > self.threshold:
                level = IssueLevel.MAJOR if relative_delta > 2 * self.threshold else IssueLevel.MEDIUM
                description = (
                    "For records in the dataset where {slicing_fn}, we found a significantly higher number of "
                    "overconfident wrong predictions ({num_overconfident_samples} samples, corresponding to "
                    "{metric_value_perc:.2f}% of the wrong predictions in the data slice)."
                )
                issue = Issue(
                    model,
                    dataset,
                    group=Overconfidence,
                    level=level,
                    description=description,
                    slicing_fn=slice_fn,
                    meta={
                        "metric": "Overconfidence rate",
                        "metric_value": slice_rate,
                        "metric_value_perc": slice_rate * 100,
                        "metric_reference_value": reference_rate,
                        "num_overconfident_samples": len(fail_idx),
                        "deviation": f"{relative_delta*100:+.2f}% than global",
                        "slice_size": len(sliced_dataset),
                        "threshold": self.threshold,
                        "p_threshold": p_threshold,
                        "fail_idx": fail_idx,
                    },
                    tests=_generate_overconfidence_tests,
                    importance=relative_delta,
                    taxonomy=["avid-effect:performance:P0204"],
                    detector_name=self.__class__.__name__,
                )

                # Add examples
                extractor = ExampleExtractor(issue, _filter_examples)
                examples = extractor.get_examples_dataframe(20, with_prediction=2)
                issue.add_examples(examples)

                issues.append(issue)

        return issues


def _filter_examples(issue, dataset):
    fail_idx = issue.meta["fail_idx"]

    return dataset.slice(lambda df: df.loc[fail_idx], row_level=False)


def _generate_overconfidence_tests(issue):
    from ...testing.tests.calibration import test_overconfidence_rate

    abs_threshold = issue.meta["metric_reference_value"] * (1 + issue.meta["threshold"])

    tests = {
        f"Overconfidence on data slice “{issue.slicing_fn}”": test_overconfidence_rate(
            slicing_function=issue.slicing_fn,
            threshold=abs_threshold,
            p_threshold=issue.meta["p_threshold"],
        )
    }

    return tests
