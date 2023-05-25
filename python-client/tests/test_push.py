from giskard.push.perturbation import create_perturbation_push
from giskard.push.contribution import create_contribution_push
from giskard.slicing.slice import QueryBasedSliceFunction
from giskard.push.prediction import create_overconfidence_push, create_borderline_push
from giskard.push import Push

def test_instance_if_not_None(german_credit_model, german_credit_data):
    for i in range(50):
        push_list = [create_contribution_push(german_credit_model, german_credit_data, i),
                     create_perturbation_push(german_credit_model, german_credit_data, i),
                     create_overconfidence_push(german_credit_model, german_credit_data, i),
                     create_borderline_push(german_credit_model, german_credit_data, i)]
        for push in push_list:
            if push is not None:
                assert isinstance(push, Push)


def test_contribution(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        res = create_contribution_push(german_credit_model, german_credit_data, i)
        if res is not None:
            isinstance(res.slicing_function, QueryBasedSliceFunction)
            testl.append(res)
    assert len(testl) > 0


def test_contribution_reg(linear_regression_diabetes, diabetes_dataset_with_target):  # @TODO: SKlearn model no target
    testl = []

    for i in range(400):
        res = create_contribution_push(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            isinstance(res.slicing_function, QueryBasedSliceFunction)
            testl.append(res)
    assert len(testl) > 0


def test_perturbation_text(enron_model, enron_data):
    testl = []
    for i in range(40):
        res = create_perturbation_push(enron_model, enron_data, i)
        if res is not None:
            testl.append(res)
    assert testl != []


def test_perturbation(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        res = create_perturbation_push(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_perturbation_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    testl = []
    for i in range(400):
        res = create_perturbation_push(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_overconfidence(german_credit_model, german_credit_data):
    testl = []
    for i in range(200):
        res = create_overconfidence_push(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_overconfidence_enron(enron_model, enron_data):
    testl = []
    for i in range(50):
        res = create_overconfidence_push(enron_model, enron_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_borderline(german_credit_model, german_credit_data):
    testl = []
    for i in range(200):
        res = create_borderline_push(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_borderline_enron(enron_model, enron_data):
    testl = []
    for i in range(40):
        res = create_borderline_push(enron_model, enron_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0
