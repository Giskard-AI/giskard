
from giskard.scanner.prediction.loss_generators.overconfidence import OverconfidenceDatasetGenerator
from giskard.scanner.prediction.prediction_bias_detectors import PredictionBiasDetector

class OverconfidenceBiasDetector(PredictionBiasDetector):
    def _get_meta(self, model, dataset):
        # oc = OverconfidenceDatasetGenerator(model, dataset)
        bd = OverconfidenceDatasetGenerator(model, dataset)
        meta = bd.get_dataset()
        return meta