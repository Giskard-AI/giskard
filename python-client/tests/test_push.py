from giskard.push import perturbation

def test_perturbation(german_credit_model,german_credit_test_data,0):
    perturbation(german_credit_model,german_credit_test_data,0)