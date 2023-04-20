from giskard.push.perturbation import perturbation


def test_perturbation(german_credit_model, german_credit_test_data):
    perturbation(german_credit_model, german_credit_test_data, 0)
