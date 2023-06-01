from giskard import Dataset
from giskard.models.base import BaseModel
from giskard.scanner.decorators import detector
from giskard.scanner.issues import Issue
from giskard.scanner.logger import logger
import pandas as pd


@detector(name="Stochasticity bias", tags=["prediction_bias", "classification", "regression"])
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


class StochasticityIssue(Issue):
    """Stochasticity Issue"""

    group = "Prediction bias"
    info = "Stochasticity issue"

    def __repr__(self):
        return f"<StochasticityIssue>"

    @property
    def description(self):
        return f"Running the model twice on the same dataset returns different results"
