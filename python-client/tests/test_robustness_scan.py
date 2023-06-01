from giskard.scanner.robustness.robustness_detector import RobustnessDetector


def test_perturbation_classification(german_credit_model, german_credit_data):
    analyzer = RobustnessDetector(german_credit_model, german_credit_data)
    res = analyzer.run()
    assert res


def test_text(enron_model, enron_data):
    analyzer = RobustnessDetector()
    res = analyzer.run(enron_model, enron_data)
    assert res
