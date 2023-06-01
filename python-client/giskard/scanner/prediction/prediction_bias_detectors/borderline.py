from scanner.prediction.loss_generators.borderline import BorderlineDatasetGenerator
from . import PredictionBiasDetector

class BorderlineBiasDetector(PredictionBiasDetector):
    def _get_meta(self, model, dataset):
        oc = BorderlineDatasetGenerator(model, dataset)
        meta = oc.get_dataset()
        return meta
