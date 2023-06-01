from giskard.scanner.perturbation import RobustnessScan


def test_perturbation(german_credit_model,german_credit_data):
    analyzer = RobustnessScan(german_credit_model,german_credit_data)
    assert analyzer.run()