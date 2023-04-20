from giskard.push.perturbation import perturbation
from giskard.push.contribution import contribution

def test_perturbation(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        testl.append(perturbation(german_credit_model, german_credit_data, i))
    assert testl != []


def test_contribution(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        testl.append(contribution(german_credit_model, german_credit_data, i))
    assert testl != []
