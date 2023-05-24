from ...models.base import BaseModel
from ...datasets.base import Dataset
from ..logger import logger
import pandas as pd


class StochasticityDetector:
    def run(self, model: BaseModel, dataset: Dataset):
        logger.debug(
            f"DataLeakageDetector: Running"
        )
        small_dataset = dataset.slice(lambda df: df.sample(100), row_level=False)
        issues = self._find_issues(model, small_dataset)
        return issues

    def _find_issues(self, model, dataset):
        prediction_1 = pd.DataFrame(model.predict(dataset).prediction)
        prediction_2 = pd.DataFrame(model.predict(dataset).prediction)
        if not prediction_1.equals(prediction_2):
                return StochasticityIssue()


class StochasticityIssue:
    """Stochasticity Issue"""

    group = ""
    info = "Stochasticity issue"  # TODO: Sentence TBD