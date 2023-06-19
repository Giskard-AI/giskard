from giskard.push.contribution import contribution
from giskard.push.prediction import overconfidence
from giskard.push import Push
from giskard.slicing.slice import QueryBasedSliceFunction
from giskard.push.prediction import create_overconfidence_push, create_borderline_push
from giskard.push import Push
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest

# Classification
def test_instance_if_not_none(german_credit_model, german_credit_data):
    for i in range(50):
        push_list = [create_contribution_push(german_credit_model, german_credit_data, i),
                     create_perturbation_push(german_credit_model, german_credit_data, i),
                     create_overconfidence_push(german_credit_model, german_credit_data, i),
                     create_borderline_push(german_credit_model, german_credit_data, i)]
        for push in push_list:
            if push is not None:
                assert isinstance(push, Push)

def test_slicing_function(german_credit_model, german_credit_data):
    for i in range(50):
        push = create_contribution_push(german_credit_model, german_credit_data, i)
        if push is not None:
            assert isinstance(push.slicing_function, QueryBasedSliceFunction)

def test_test_function(german_credit_model, german_credit_data):
    for i in range(50):
        push_list = [create_contribution_push(german_credit_model, german_credit_data, i),
                     create_perturbation_push(german_credit_model, german_credit_data, i),
                     create_overconfidence_push(german_credit_model, german_credit_data, i),
                     create_borderline_push(german_credit_model, german_credit_data, i)]
        for push in push_list:
            if push is not None:
                for test in push.tests:
                    assert isinstance(test(), GiskardTest)

# Regression
def test_instance_if_not_none_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    for i in range(50):
        push_list = [create_contribution_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
                     create_perturbation_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
                     create_overconfidence_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
                     create_borderline_push(linear_regression_diabetes, diabetes_dataset_with_target, i)]
        for push in push_list:
            if push is not None:
                assert isinstance(push, Push)

def test_slicing_function_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    for i in range(50):
        push = create_contribution_push(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if push is not None:
            assert isinstance(push.slicing_function, QueryBasedSliceFunction)

def test_test_function_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    for i in range(50):
        push_list = [create_contribution_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
                     create_perturbation_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
                     create_overconfidence_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
                     create_borderline_push(linear_regression_diabetes, diabetes_dataset_with_target, i)]
        for push in push_list:
            if push is not None:
                for test in push.tests:
                    assert isinstance(test(), GiskardTest)

# Multiclass Classification
def test_instance_if_not_none_multi(enron_model, enron_data):
    for i in range(50):
        push_list = [create_contribution_push(enron_model, enron_data, i),
                     create_perturbation_push(enron_model, enron_data, i),
                     create_overconfidence_push(enron_model, enron_data, i),
                     create_borderline_push(enron_model, enron_data, i)]
        for push in push_list:
            if push is not None:
                assert isinstance(push, Push)

def test_slicing_function_multi(enron_model, enron_data):
    for i in range(50):
        push = create_contribution_push(enron_model, enron_data, i)
        if push is not None:
            assert isinstance(push.slicing_function, QueryBasedSliceFunction)


def test_borderline_enron(enron_model, enron_data):
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
def test_perturbation_text(enron_model, enron_data):
    testl = []
    for i in range(40):
        res = perturbation(enron_model, enron_data, i)
        if res is not None:
            isinstance(res.slicing_function, QueryBasedSliceFunction)
            testl.append(res)
            # if isinstance(res, Push):
                # print(res.transformation_function)
    assert testl != []


def test_contribution_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    testl = []
    # print(diabetes_dataset.df.count())

    for i in range(400):
        # print(linear_regression_diabetes.__dict__)
        res = contribution(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            isinstance(res.slicing_function, QueryBasedSliceFunction)
            testl.append(res)
    assert len(testl)>0

def test_perturbation_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    testl = []
    for i in range(400):
        res = perturbation(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            isinstance(res.slicing_function, QueryBasedSliceFunction)
            testl.append(res)
    assert len(testl)>0


def test_overconfidence_reg(linear_regression_diabetes, diabetes_dataset_with_target):  # @TODO: SKlearn model no target
    testl = []
    for i in range(200):
        res = overconfidence(linear_regression_diabetes, diabetes_dataset_with_target, i)
        if res is not None:
            testl.append(res)
    assert len(testl) > 0
