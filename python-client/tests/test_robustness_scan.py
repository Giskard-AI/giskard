from giskard.scanner.perturbation import ModelRobustnessDetector


def test_perturbation_classification(german_credit_model, german_credit_data):
    analyzer = ModelRobustnessDetector(german_credit_model, german_credit_data)
    res = analyzer.run()
    assert res

def test_text(enron_model, enron_data):
    analyzer = ModelRobustnessDetector(enron_model, enron_data)
    res = analyzer.run()
    assert res