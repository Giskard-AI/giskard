from giskard.scanner.prediction.computing.borderline import ComputeBorderline
from giskard.scanner.prediction.prediction_bias_detectors import PredictionBiasDetector

class BorderlineBiasDetector(PredictionBiasDetector):
    def _get_meta(self, model, dataset):
        return ComputeBorderline(model, dataset).get_dataset()
