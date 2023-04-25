from giskard.scanner.issues import Issue
from giskard.scanner.performance import ModelBiasDetector


def test_model_bias_detector(german_credit_model, german_credit_data):
    detector = ModelBiasDetector()
    issues = detector.run(german_credit_model, german_credit_data)

    assert len(issues) > 0
    assert all([isinstance(issue, Issue) for issue in issues])
