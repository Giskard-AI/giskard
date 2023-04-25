from giskard.push.perturbation import perturbation
from giskard.push.contribution import contribution
from tests.fixtures.regression import linear_regression_diabetes, linear_regression_diabetes_raw


def test_perturbation(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        res = perturbation(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert len(testl)>0



def test_contribution(german_credit_model, german_credit_data):
    testl = []
    for i in range(100):
        res = contribution(german_credit_model, german_credit_data, i)
        if res is not None:
            testl.append(res)
    assert  len(testl)>0


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
