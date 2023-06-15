from dataclasses import dataclass
import pandas as pd
from sklearn.metrics import adjusted_mutual_info_score

from ..issues import Issue

from ...slicing.slice_finder import SliceFinder
from ..logger import logger
from ...datasets.base import Dataset
from ...models.base import BaseModel
from ..registry import Detector
from ..decorators import detector


@detector(name="spurious_correlation", tags=["spurious_correlation", "classification"])
class SpuriousCorrelationDetector(Detector):
    def __init__(self, threshold=0.8) -> None:
        self.threshold = threshold

    def run(self, model: BaseModel, dataset: Dataset):
        logger.info(f"{self.__class__.__name__}: Running")

        # Dataset prediction
        ds_predictions = pd.Series(model.predict(dataset).prediction, dataset.df.index)

        # Keep only interesting features
        features = model.meta.feature_names or dataset.columns.drop(dataset.target, errors="ignore")

        # Prepare dataset for slicing
        df = dataset.df.copy()
        df[dataset.target] = pd.Categorical(df[dataset.target])
        wdata = Dataset(df, column_types=dataset.column_types)

        # Find slices
        sliced_cols = SliceFinder("tree").run(wdata, features, target=dataset.target)

        issues = []
        for col, slices in sliced_cols.items():
            dx = pd.DataFrame(
                {"feature": "unsliced", "target": dataset.df[dataset.target], "prediction": ds_predictions},
                index=dataset.df.index,
            )
            for s in slices:
                dx.loc[dataset.slice(s).df.index, "feature"] = str(s)

            dx["feature"] = dx["feature"].astype("category")
            dx.dropna(inplace=True)

            mutual_info = adjusted_mutual_info_score(dx.feature, dx.prediction)
            logger.info(f"{self.__class__.__name__}: Feature `{col}`\t I = {mutual_info:.3f}")

            if mutual_info > self.threshold:
                info = SpuriousCorrelationInfo(col, mutual_info)
                issues.append(SpuriousCorrelationIssue(model, dataset, "info", info))

        return issues


@dataclass
class SpuriousCorrelationInfo:
    feature: str
    mutual_info: float


class SpuriousCorrelationIssue(Issue):
    group = "Spurious correlation"

    @property
    def domain(self) -> str:
        return f"Feature `{self.info.feature}`"

    @property
    def metric(self) -> str:
        return "Mutual information"

    @property
    def deviation(self) -> str:
        return f"{self.info.mutual_info:.3f}"

    @property
    def description(self) -> str:
        return ""

    def examples(self, n=3) -> pd.DataFrame:
        return pd.DataFrame()

    @property
    def importance(self) -> float:
        return self.info.mutual_info
