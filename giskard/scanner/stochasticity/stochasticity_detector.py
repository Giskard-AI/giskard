import numpy as np
import pandas as pd

from giskard.datasets import Dataset
from giskard.models import cache as models_cache
from giskard.models.base import BaseModel
from giskard.scanner.decorators import detector
from giskard.scanner.issues import Issue, IssueLevel, Stochasticity
from giskard.scanner.logger import logger

from ..registry import Detector


@detector(name="stochasticity", tags=["stochasticity", "classification", "regression"])
class StochasticityDetector(Detector):
    """Detects stochasticity in the model predictions.

    This detector ensures that the model predictions are deterministic, i.e. that the same input always produces the
    same output.
    """

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

        desc = "We found {num_stochastic_samples} examples for which your model provides a different output at each execution."
        return [
            Issue(
                model,
                dataset,
                level=IssueLevel.MEDIUM,
                group=Stochasticity,
                description=desc,
                meta={
                    "domain": "Whole dataset",
                    "deviation": "Model gives different results at each execution",
                    "num_stochastic_samples": len(fail_samples),
                },
                examples=fail_samples,
                taxonomy=["avid-effect:performance:P0201"],
            )
        ]
