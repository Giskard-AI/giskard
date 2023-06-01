from giskard.scanner.decorators import detector
from giskard.scanner.prediction import PredictionBiasDetector
from giskard.scanner.prediction.computing.borderline import ComputeBorderline


@detector(name="Borderline bias", tags=["borderline_bias", "classification"])
class BorderlineBiasDetector(PredictionBiasDetector):
    def _get_meta(self, model, dataset):
        return ComputeBorderline(model, dataset).get_dataset()
