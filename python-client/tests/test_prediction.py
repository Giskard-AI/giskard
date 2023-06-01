from giskard.scanner.prediction.data_leakage import DataLeakageDetector
from giskard.scanner.prediction.overconfidence import OverconfidenceBiasDetector
from giskard.scanner.prediction.borderline import BorderlineBiasDetector
from giskard.scanner.prediction.metrics import OverconfidenceMAE, BorderlineMAE
from giskard.scanner.prediction.stochasticity import StochasticityDetector


def test_overconfidence_issue(german_credit_model, german_credit_data):
    overconfidence_issues = OverconfidenceBiasDetector(metrics=[OverconfidenceMAE()]).run(german_credit_model, german_credit_data)
    assert overconfidence_issues

def test_borderline_issue(german_credit_model, german_credit_data):
    borderline_issues = BorderlineBiasDetector(metrics=[BorderlineMAE()]).run(german_credit_model, german_credit_data)
    assert borderline_issues

def test_dataleakage_issue(german_credit_model, german_credit_data):
    dataleakage_issues = DataLeakageDetector().run(german_credit_model, german_credit_data)
    assert dataleakage_issues is None

def test_stochasticity_issue(german_credit_model, german_credit_data):
    stochasticity_issues = StochasticityDetector().run(german_credit_model, german_credit_data)
    assert stochasticity_issues is None
