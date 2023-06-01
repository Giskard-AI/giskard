import numpy as np
import pandas as pd
from dataclasses import dataclass

from giskard import Dataset
from giskard.models import cache as models_cache
from giskard.models.base import BaseModel
from giskard.scanner.decorators import detector
from giskard.scanner.issues import Issue
from giskard.scanner.logger import logger


@detector(name="stochasticity", tags=["stochasticity", "classification", "regression"])
class StochasticityDetector:
    def run(self, model: BaseModel, dataset: Dataset):
        logger.info("StochasticityDetector: Running")
        sample_size = min(100, len(dataset))
        reduced_dataset = dataset.slice(lambda df: df.sample(sample_size), row_level=False)

        with models_cache.no_cache():
            prediction_1 = model.predict(reduced_dataset).raw
            prediction_2 = model.predict(reduced_dataset).raw

        changed_samples = ~(np.isclose(prediction_1, prediction_2).all(axis=-1))

        if not changed_samples.any():
            return []

        fail_samples = pd.DataFrame(
            columns=["First prediction", "Second prediction"],
            index=reduced_dataset.df.loc[changed_samples].index,
        )
        fail_samples["First prediction"] = list(prediction_1[changed_samples])
        fail_samples["Second prediction"] = list(prediction_2[changed_samples])

        return [StochasticityIssue(model, dataset, level="medium", info=StochasticityInfo(samples=fail_samples))]


@dataclass
class StochasticityInfo:
    samples: pd.DataFrame


class StochasticityIssue(Issue):
    group = "Stochasticity"

    @property
    def domain(self) -> str:
        return ""

    @property
    def metric(self) -> str:
        return "Stochasticity"

    @property
    def deviation(self) -> str:
        return "Your model provides different results at each execution."

    @property
    def description(self) -> str:
        return f"We found {len(self.info.samples)} examples for which your model provides a different output at each execution."

    def examples(self, n=3) -> pd.DataFrame:
        return self.info.samples.head(n)

    @property
    def importance(self) -> float:
        return 1

    def generate_tests(self, with_names=False) -> list:
        return []
