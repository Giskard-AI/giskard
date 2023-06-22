from dataclasses import dataclass
import pandas as pd
from sklearn.metrics import adjusted_mutual_info_score, mutual_info_score
from scipy import stats

from ..common.examples import ExampleExtractor
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ..issues import Issue
from ...slicing.slice_finder import SliceFinder
from ..logger import logger
from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..registry import Detector
from ..decorators import detector


@detector(name="spurious_correlation", tags=["spurious_correlation", "classification"])
class SpuriousCorrelationDetector(Detector):
    def __init__(self, method="theil", threshold=0.5) -> None:
        self.threshold = threshold
        self.method = method

    def run(self, model: BaseModel, dataset: Dataset):
        logger.info(f"{self.__class__.__name__}: Running")

        # Dataset prediction
        ds_predictions = pd.Series(model.predict(dataset).prediction, dataset.df.index)

        # Keep only interesting features
        features = model.meta.feature_names or dataset.columns.drop(dataset.target, errors="ignore")

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
        sliced_cols = SliceFinder("tree").run(wdata, features, target=wdata.target)

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
                    info = SpuriousCorrelationInfo(col, slice_fn, metric_value, measure_name, predictions)
                    issues.append(SpuriousCorrelationIssue(model, dataset, "info", info))

        return issues

    def _get_measure_fn(self):
        if self.method == "theil":
            return _theil_u, "Theil's U"
        if self.method == "mutual_information" or self.method == "mi":
            return _mutual_information, "Mutual information"
        if self.method == "cramer":
            return _cramer_v, "Cramer's V"
        raise ValueError(f"Unknown method `{self.method}`")


def _cramer_v(x, y):
    ct = pd.crosstab(x, y)
    return stats.contingency.association(ct, method="cramer")


def _mutual_information(x, y):
    return adjusted_mutual_info_score(x, y)


def _theil_u(x, y):
    return mutual_info_score(x, y) / stats.entropy(pd.Series(y).value_counts(normalize=True))


@dataclass
class SpuriousCorrelationInfo:
    feature: str
    slice_fn: SlicingFunction
    metric_value: float
    metric_name: str
    predictions: pd.DataFrame


class SpuriousCorrelationIssue(Issue):
    group = "Spurious correlation"

    @property
    def features(self):
        return [self.info.feature]

    @property
    def domain(self) -> str:
        return str(self.info.slice_fn)

    @property
    def metric(self) -> str:
        return f"Nominal association ({self.info.metric_name})"

    @property
    def deviation(self) -> str:
        plabel, p = self.info.predictions.index[0], self.info.predictions.iloc[0]

        return f"Prediction {self.dataset.target} = `{plabel}` for {p * 100:.2f}% of samples in the slice"

    @property
    def slicing_fn(self):
        return self.info.slice_fn

    @property
    def description(self) -> str:
        pred = self.model.predict(self.dataset.slice(self.info.slice_fn)).prediction
        classes = pd.Series(pred).value_counts(normalize=True)
        plabel, p = classes.index[0], classes.iloc[0]
        return f"Data slice {self.info.slice_fn} seems to be highly associated to prediction {self.dataset.target} = `{plabel}` ({p * 100:.2f}% of predictions in the data slice)."

    # @lru_cache
    def examples(self, n=3):
        extractor = ExampleExtractor(self)
        return extractor.get_examples_dataframe(n, with_prediction=1)

    @property
    def importance(self) -> float:
        return self.info.metric_value
