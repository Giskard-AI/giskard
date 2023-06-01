from giskard.scanner.performance.metrics import PerformanceMetric
from giskard.models.base import BaseModel
from giskard.datasets.base import Dataset
from giskard.scanner.prediction.loss_generators.borderline import BorderlineDatasetGenerator
from giskard.scanner.prediction.loss_generators.overconfidence import OverconfidenceDatasetGenerator


class OverconfidenceMAE(PerformanceMetric):
    name = "probamae"
    greater_is_better = False

    def __call__(self, model: BaseModel, dataset: Dataset) -> float:
        if not model.is_classification:
            raise ValueError(f"Metric '{self.name}' is only defined for classification models.")

        ocd = OverconfidenceDatasetGenerator(model, dataset)

        return self._calculate_metric(ocd)

    def _calculate_metric(self, ocd) -> float:
        return ocd.get_proba_rmse()


class BorderlineMAE(PerformanceMetric):
    name = "borderline"
    greater_is_better = True

    def __call__(self, model: BaseModel, dataset: Dataset) -> float:
        if not model.is_classification:
            raise ValueError(f"Metric '{self.name}' is only defined for classification models.")

        bld = BorderlineDatasetGenerator(model, dataset)

        return self._calculate_metric(bld)

    def _calculate_metric(self, bld) -> float:
        return bld.get_proba_rmse()
