from giskard.scanner.prediction.computing.overconfidence import ComputeOverconfidence
from giskard.scanner.prediction.prediction_bias_detectors import PredictionBiasDetector


class OverconfidenceBiasDetector(PredictionBiasDetector):
    def _get_meta(self, model, dataset):
        return ComputeOverconfidence(model,dataset).get_dataset()
