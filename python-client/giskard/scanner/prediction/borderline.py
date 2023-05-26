from giskard.scanner.prediction import PredictionBiasDetector
from giskard.scanner.prediction.computing.borderline import ComputeBorderline

class BorderlineBiasDetector(PredictionBiasDetector):
    def _get_meta(self, model, dataset):
        return ComputeBorderline(model, dataset).get_dataset()
