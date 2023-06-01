from giskard.scanner.perturbation import RobustnessScan


def test_perturbation_classification(german_credit_model, german_credit_data):
    analyzer = RobustnessScan(german_credit_model, german_credit_data)
    res = analyzer.run()
    assert res

def test_text(enron_model, enron_data):
    analyzer = RobustnessScan(enron_model, enron_data)
    res = analyzer.run()
    assert res