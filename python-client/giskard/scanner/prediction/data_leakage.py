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
        leak_list = []
        rate = 0
        for i in range(len(dataset.df)):
            row = dataset.slice(lambda df: df.iloc[i:i + 1], row_level=False)
            pre_computed_output = prediction.iloc[i:i + 1]
            online_computed_output = pd.Series(model.predict(row).prediction)
            if pre_computed_output.values != online_computed_output.values:
                leak_list.append([pre_computed_output, online_computed_output])
                rate += 1

            return DataLeakageIssue(dataset=dataset,
                                    model=model,
                                    level="minor",
                                    leak_list=leak_list,
                                    error_rate=rate / len(dataset.df))


class DataLeakageIssue(Issue):
    """DataLeakage Issue"""

    group = "Prediction bias"
    info = "DataLeakage issue"

    def __init__(
            self,
            model: BaseModel,
            dataset: Dataset,
            level: str,
            leak_list,
            error_rate
    ):
        super().__init__(model, dataset, level)
        self.leak_list = leak_list
        self.error_rate = error_rate

    def __repr__(self):
        return f"<DataLeakageIssue {self.error_rate}%>"

    @property
    def description(self):
        return f"{self.error_rate}% of the dataset"
