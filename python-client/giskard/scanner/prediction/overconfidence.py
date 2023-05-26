from giskard.scanner.decorators import detector
from giskard.scanner.prediction.computing.overconfidence import ComputeOverconfidence
from giskard.scanner.prediction import PredictionBiasDetector


@detector(name="Overconfidence bias", tags=["prediction_bias", "classification"])
class OverconfidenceBiasDetector(PredictionBiasDetector):
    def _get_meta(self, model, dataset):
        return ComputeOverconfidence(model,dataset).get_dataset()
