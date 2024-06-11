from typing import Optional, Sequence

import pandas as pd

from ...datasets.base import Dataset
from ...models.base import BaseModel
from ...slicing.slice_finder import SliceFinder
from ...testing.tests.statistic import _cramer_v, _mutual_information, _theil_u
from ..common.examples import ExampleExtractor
from ..decorators import detector
from ..issues import Issue, IssueLevel, SpuriousCorrelation
from ..logger import logger
from ..registry import Detector


@detector(name="spurious_correlation", tags=["spurious_correlation", "classification"])
class SpuriousCorrelationDetector(Detector):
    def __init__(
        self, method: Optional[str] = "theil", threshold: Optional[float] = 0.5, min_slice_size: Optional[float] = None
    ):
        self.threshold = threshold
        self.method = method
        self.min_slice_size = min_slice_size

    def run(self, model: BaseModel, dataset: Dataset, features: Sequence[str]):
        logger.info(f"{self.__class__.__name__}: Running")

        # Dataset prediction
        ds_predictions = pd.Series(model.predict(dataset).prediction, dataset.df.index)

        # Warm up text metadata
        for f in features:
            if dataset.column_types[f] == "text":
                dataset.column_meta[f, "text"]

        # Prepare dataset for slicing
        df = dataset.df.copy()
        if dataset.target is not None:
            df.drop(columns=dataset.target, inplace=True)
        df["__gsk__target"] = pd.Categorical(ds_predictions)
        wdata = Dataset(df, target="__gsk__target", column_types=dataset.column_types)
        wdata.load_metadata_from_instance(dataset.column_meta)

        # Find slices
        sliced_cols = SliceFinder("tree").run(wdata, features, target=wdata.target, min_slice_size=self.min_slice_size)

        measure_fn, measure_name = self._get_measure_fn()
        issues = []
        for col, slices in sliced_cols.items():
            if not slices:
                continue

            for slice_fn in slices:
                data_slice = dataset.slice(slice_fn)

                # Skip small slices
                if len(data_slice) < 20 or len(data_slice) < 0.05 * len(dataset):
                    continue

                dx = pd.DataFrame(
                    {
                        "feature": dataset.df.index.isin(data_slice.df.index).astype(int),
                        "prediction": ds_predictions,
                    },
                    index=dataset.df.index,
                )
                dx.dropna(inplace=True)

                metric_value = measure_fn(dx.feature, dx.prediction)
                logger.info(f"{self.__class__.__name__}: {slice_fn}\tAssociation = {metric_value:.3f}")

                if metric_value > self.threshold:
                    predictions = dx[dx.feature > 0].prediction.value_counts(normalize=True)
                    plabel, p = predictions.index[0], predictions.iloc[0]

                    description = "Data slice {slicing_fn} seems to be highly associated to prediction {target} = `{plabel}` ({p_perc:.2f}% of predictions in the data slice)."

                    issue = Issue(
                        model,
                        dataset,
                        group=SpuriousCorrelation,
                        level=IssueLevel.MINOR,
                        slicing_fn=slice_fn,
                        meta={
                            "metric": f"Nominal association ({measure_name})",
                            "metric_value": metric_value,
                            "method": self.method,
                            "deviation": f"Prediction {dataset.target} = `{plabel}` for {p * 100:.2f}% of samples in the slice",
                            "target": dataset.target,
                            "plabel": plabel,
                            "p": p,
                            "p_perc": p * 100,
                            "threshold": self.threshold,
                        },
                        description=description,
                        importance=metric_value,
                        tests=_generate_spurious_corr_tests,
                        taxonomy=["avid-effect:performance:P0103"],
                        detector_name=self.__class__.__name__,
                    )

                    extractor = ExampleExtractor(issue)
                    examples = extractor.get_examples_dataframe(20, with_prediction=1)
                    issue.add_examples(examples)

                    issues.append(issue)

        return issues

    def _get_measure_fn(self):
        if self.method == "theil":
            return _theil_u, "Theil's U"
        if self.method == "mutual_information" or self.method == "mi":
            return _mutual_information, "Mutual information"
        if self.method == "cramer":
            return _cramer_v, "Cramer's V"
        raise ValueError(f"Unknown method `{self.method}`")


_metric_test_mapping = {
    "cramer": "test_cramer_v",
    "mutual_information": "test_mutual_information",
    "mi": "test_mutual_information",
    "theil": "test_theil_u",
}


def _metric_to_test_object(metric_name):
    from ...testing.tests import statistic

    try:
        test_name = _metric_test_mapping[metric_name]
        return getattr(statistic, test_name)
    except (KeyError, AttributeError):
        return None


def _generate_spurious_corr_tests(issue):
    test_fn = _metric_to_test_object(issue.meta["method"])

    if test_fn is None:
        return []

    return {
        f"{issue.meta['metric']} on data slice “{issue.slicing_fn}”": test_fn(
            slicing_function=issue.slicing_fn,
            threshold=issue.meta["threshold"],
        )
    }
