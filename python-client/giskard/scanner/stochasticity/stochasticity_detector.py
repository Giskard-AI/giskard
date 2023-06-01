from giskard import Dataset
from giskard.models.base import BaseModel
from giskard.scanner.decorators import detector
from giskard.scanner.issues import Issue
from giskard.scanner.logger import logger
import numpy as np
import pandas as pd


@detector(name="stochasticity", tags=["stochasticity", "classification", "regression"])
class StochasticityDetector:
    def run(self, model: BaseModel, dataset: Dataset):
        logger.info("StochasticityDetector: Running")
        reduced_dataset = dataset.slice(lambda df: df.sample(100), row_level=False)

        prediction_1 = model.predict(reduced_dataset).raw
        prediction_2 = model.predict(reduced_dataset).raw

        if np.isclose(prediction_1, prediction_2).all():
            return []

        return [StochasticityIssue(model, dataset, level="medium")]


class StochasticityIssue(Issue):
    group = "Stochasticity"

    @property
    def domain(self) -> str:
        return ""

    @property
    def metric(self) -> str:
        return "Prediction"

    @property
    def deviation(self) -> str:
        return "Your model provides different results at each execution."

    @property
    def description(self) -> str:
        return ""

    def examples(self, n=3) -> pd.DataFrame:
        return pd.DataFrame()

    @property
    def importance(self) -> float:
        return 1

    def generate_tests(self) -> list:
        return []
