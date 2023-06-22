from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.push import Push
from giskard.push.contribution import create_contribution_push
from giskard.push.perturbation import create_perturbation_push
from giskard.push.prediction import create_borderline_push, create_overconfidence_push
from giskard.slicing.slice import QueryBasedSliceFunction


# Classification
def test_instance_if_not_none(german_credit_model, german_credit_data):
    for i in range(50):
        push_list = [
            create_contribution_push(german_credit_model, german_credit_data, i),
            create_perturbation_push(german_credit_model, german_credit_data, i),
            create_overconfidence_push(german_credit_model, german_credit_data, i),
            create_borderline_push(german_credit_model, german_credit_data, i),
        ]
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
        push_list = [
            create_contribution_push(german_credit_model, german_credit_data, i),
            create_perturbation_push(german_credit_model, german_credit_data, i),
            create_overconfidence_push(german_credit_model, german_credit_data, i),
            create_borderline_push(german_credit_model, german_credit_data, i),
        ]
        for push in push_list:
            if push is not None:
                for test in push.tests:
                    assert isinstance(test(), GiskardTest)


# Regression
def test_instance_if_not_none_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    for i in range(50):
        push_list = [
            create_contribution_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
            create_perturbation_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
            create_overconfidence_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
            create_borderline_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
        ]
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
        push_list = [
            create_contribution_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
            create_perturbation_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
            create_overconfidence_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
            create_borderline_push(linear_regression_diabetes, diabetes_dataset_with_target, i),
        ]
        for push in push_list:
            if push is not None:
                for test in push.tests:
                    assert isinstance(test(), GiskardTest)


# Multiclass Classification
def test_instance_if_not_none_multi(enron_model, enron_data):
    for i in range(50):
        push_list = [
            create_contribution_push(enron_model, enron_data, i),
            create_perturbation_push(enron_model, enron_data, i),
            create_overconfidence_push(enron_model, enron_data, i),
            create_borderline_push(enron_model, enron_data, i),
        ]
        for push in push_list:
            if push is not None:
                assert isinstance(push, Push)


def test_slicing_function_multi(enron_model, enron_data):
    for i in range(50):
        push = create_contribution_push(enron_model, enron_data, i)
        if push is not None:
            assert isinstance(push.slicing_function, QueryBasedSliceFunction)


def test_test_function_multi(enron_model, enron_data):
    for i in range(50):
        push_list = [
            create_contribution_push(enron_model, enron_data, i),
            create_perturbation_push(enron_model, enron_data, i),
            create_overconfidence_push(enron_model, enron_data, i),
            create_borderline_push(enron_model, enron_data, i),
        ]
        for push in push_list:
            if push is not None:
                for test in push.tests:
                    assert isinstance(test(), GiskardTest)
