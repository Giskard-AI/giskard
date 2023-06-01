from ...models.base import BaseModel
from ...datasets.base import Dataset
from ..logger import logger
import pandas as pd


class DataLeakageDetector:
    def run(self, model: BaseModel, dataset: Dataset):
        logger.debug(
            f"DataLeakageDetector: Running"
        )
        self.dataset = dataset
        small_dataset = dataset.slice(lambda df: df.sample(100), row_level=False)
        issues = self._find_issues(model, small_dataset)

        return issues

    def _find_issues(self, model, dataset):
        existing_leak = False
        results = model.predict(dataset)
        prediction = pd.DataFrame(results.prediction)
        for i in range(len(dataset.df)):
            row = dataset.slice(lambda df: df.iloc[i:i+1], row_level=False)
            pre_computed_output = prediction.iloc[i:i+1]
            online_computed_output = pd.Series(model.predict(row).prediction)
            if pre_computed_output.values != online_computed_output.values:
                existing_leak = True
        if existing_leak:
            return DataLeakageIssue()


class DataLeakageIssue:
    """DataLeakage Issue"""

    group = ""
    info = "DataLeakage issue"  # TODO: Sentence TBD

