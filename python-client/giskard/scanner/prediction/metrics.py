from giskard.scanner.performance.metrics import PerformanceMetric
from giskard.models.base import BaseModel
from giskard.datasets.base import Dataset
from giskard.scanner.prediction.computing.borderline import ComputeBorderline
from giskard.scanner.prediction.computing.overconfidence import ComputeOverconfidence
import pandas as pd


class OverconfidenceMAE(PerformanceMetric):
    name = "probamae"
    greater_is_better = False

    def __call__(self, model: BaseModel, dataset: Dataset) -> float:
        if not model.is_classification:
            raise ValueError(f"Metric '{self.name}' is only defined for classification models.")
        return self._calculate_metric(model, dataset)

    def _calculate_metric(self, model, dataset) -> float:
        return ComputeOverconfidence(model, dataset).get_metric()


class BorderlineMAE(PerformanceMetric):
    name = "borderline"
    greater_is_better = True

    def __call__(self, model: BaseModel, dataset: Dataset) -> float:
        if not model.is_classification:
            raise ValueError(f"Metric '{self.name}' is only defined for classification models.")



        return self._calculate_metric(model,dataset)

    def _calculate_metric(self, model,dataset) -> float:
        return ComputeBorderline(model,dataset).get_metric()
