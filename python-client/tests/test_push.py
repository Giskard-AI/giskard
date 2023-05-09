from giskard.push.perturbation import perturbation
from giskard.push.contribution import contribution
from giskard.push.prediction import overconfidence, borderline, stochasticity


def test_perturbation(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        res = perturbation(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
            print(res.slicing_function)
    assert len(testl) > 0


def test_contribution(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        res = contribution(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_overconfidence(german_credit_model, german_credit_data):
    testl = []
    for i in range(200):
        res = overconfidence(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_borderline(german_credit_model, german_credit_data):
    testl = []
    for i in range(200):
        res = borderline(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_stochasticity_german(german_credit_model, german_credit_data):
    testl = []
    for i in range(200):
        res = stochasticity(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_stochasticity_diabete(linear_regression_diabetes, diabetes_dataset_with_target):
    testl = []
    for i in range(200):
        res = stochasticity(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0


def test_perturbation_text(enron_model, enron_data):
    testl = []
    for i in range(40):
        res = perturbation(enron_model, enron_data, i)
        if res is not None:
            testl.append(res)
    assert testl != []


def test_contribution_reg(linear_regression_diabetes, diabetes_dataset_with_target):  # @TODO: SKlearn model no target
    testl = []
    # print(diabetes_dataset.df.count())

    for i in range(400):
        # print(linear_regression_diabetes.__dict__)
        res = contribution(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            testl.append(res)
            print(res.slicing_function)
    assert len(testl) > 0


def test_perturbation_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    testl = []
    for i in range(400):
        res = perturbation(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            testl.append(res)
            print(res.slicing_function)
    assert len(testl) > 0


# def test_perturbation_text(enron_model, enron_data):
#     testl = []
#     for i in range(40):
#         res = perturbation(enron_model, enron_data, i)
#         if res is not None:
#             testl.append(res)
#     assert testl != []


def test_contribution_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    testl = []
    # print(diabetes_dataset.df.count())

    for i in range(400):
        # print(linear_regression_diabetes.__dict__)
        res = contribution(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            testl.append(res)
    assert len(testl)>0

def test_perturbation_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    testl = []
    for i in range(400):
        res = perturbation(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            testl.append(res)
    assert len(testl)>0


def test_overconfidence_reg(linear_regression_diabetes, diabetes_dataset_with_target):  # @TODO: SKlearn model no target
    testl = []
    for i in range(200):
        res = overconfidence(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0
