from giskard.push.perturbation import perturbation
from giskard.push.contribution import contribution


def test_perturbation(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        res = perturbation(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert testl != []


def test_contribution(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        res = contribution(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert testl != []
