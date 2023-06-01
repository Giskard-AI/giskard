
from scanner.prediction.loss_generators.overconfidence import OverconfidenceDatasetGenerator
from . import PredictionBiasDetector

class OverconfidenceBiasDetector(PredictionBiasDetector):
    def _get_meta(self, model, dataset):
        # oc = OverconfidenceDatasetGenerator(model, dataset)
        bd = OverconfidenceDatasetGenerator(model, dataset)
        meta = bd.get_dataset()
        return meta