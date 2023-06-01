from giskard import Dataset
from giskard.models.base import BaseModel
from giskard.scanner.decorators import detector
from giskard.scanner.issues import Issue
from giskard.scanner.logger import logger
import pandas as pd


@detector(name="DataLeakage bias", tags=["dataleakage_bias", "classification", "regression"])
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
        results = model.predict(dataset)
        prediction = pd.DataFrame(results.prediction)

        for i in range(len(dataset.df)):
            row = dataset.slice(lambda df: df.iloc[i:i + 1], row_level=False)
            pre_computed_output = prediction.iloc[i:i + 1]
            online_computed_output = pd.Series(model.predict(row).prediction)
            if pre_computed_output.values != online_computed_output.values:
                return DataLeakageIssue()


class DataLeakageIssue(Issue):
    """DataLeakage Issue"""

    group = "Prediction bias"
    info = "DataLeakage issue"

    def __repr__(self):
        return f"<DataLeakageIssue"

    @property
    def description(self):
        return f"Your model contains a data leak"
