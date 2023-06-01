from giskard.scanner.prediction.data_leakage import DataLeakageDetector
from giskard.scanner.prediction.stochasticity import StochasticityDetector
def test_dataleakage(german_credit_model,german_credit_data):
    detector = DataLeakageDetector()
    issues = detector.run(german_credit_model,german_credit_data)
    assert issues

def test_stochasticity(german_credit_model, german_credit_data):
    detector = StochasticityDetector()
    issues = detector.run(german_credit_model, german_credit_data)
    assert issues
