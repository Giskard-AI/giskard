from giskard.ml_worker.testing.functions.transformation import mad_transformation

from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.slicing_function import slicing_function
from giskard.push import Push
from giskard.push.contribution import create_contribution_push
from giskard.push.perturbation import create_perturbation_push
from giskard.push.prediction import create_underconfidence_push, create_overconfidence_push
from giskard.slicing.slice import QueryBasedSliceFunction
import pandas as pd


# Classification
def test_instance_if_not_none(german_credit_model, german_credit_data):
    for i in range(50):
        push_list = [
            create_contribution_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_perturbation_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_overconfidence_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_underconfidence_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
        ]
        for push in push_list:
            if push is not None:
                assert isinstance(push, Push)


def test_slicing_function(german_credit_model, german_credit_data):
    for i in range(50):
        push = create_contribution_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]])
        if push is not None:
            assert isinstance(push.slicing_function, QueryBasedSliceFunction)


def test_test_function(german_credit_model, german_credit_data):
    for i in range(50):
        push_list = [
            create_contribution_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_perturbation_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_overconfidence_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_underconfidence_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
        ]
        for push in push_list:
            if push is not None:
                for test in push.tests:
                    assert isinstance(test(), GiskardTest)


# Regression
def test_instance_if_not_none_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    for i in range(50):
        push_list = [
            create_contribution_push(
                linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
            ),
            create_perturbation_push(
                linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
            ),
            create_overconfidence_push(
                linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
            ),
            create_underconfidence_push(
                linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
            ),
        ]
        for push in push_list:
            if push is not None:
                assert isinstance(push, Push)


def test_slicing_function_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    for i in range(50):
        push = create_contribution_push(
            linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
        )
        if push is not None:
            assert isinstance(push.slicing_function, QueryBasedSliceFunction)


def test_test_function_reg(linear_regression_diabetes, diabetes_dataset_with_target):
    for i in range(50):
        push_list = [
            create_contribution_push(
                linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
            ),
            create_perturbation_push(
                linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
            ),
            create_overconfidence_push(
                linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
            ),
            create_underconfidence_push(
                linear_regression_diabetes, diabetes_dataset_with_target, diabetes_dataset_with_target.df.iloc[[i]]
            ),
        ]
        for push in push_list:
            if push is not None:
                for test in push.tests:
                    assert isinstance(test(), GiskardTest)


# Multiclass Classification
def test_instance_if_not_none_multi(enron_model, enron_data):
    for i in range(50):
        push_list = [
            create_contribution_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
            create_perturbation_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
            create_overconfidence_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
            create_underconfidence_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
        ]
        for push in push_list:
            if push is not None:
                assert isinstance(push, Push)


def test_slicing_function_multi(enron_model, enron_data):
    for i in range(50):
        push = create_contribution_push(enron_model, enron_data, enron_data.df.iloc[[i]])
        if push is not None:
            assert isinstance(push.slicing_function, QueryBasedSliceFunction)


def test_test_function_multi(enron_model, enron_data):
    for i in range(50):
        push_list = [
            create_contribution_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
            create_perturbation_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
            create_overconfidence_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
            create_underconfidence_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
        ]
        for push in push_list:
            if push is not None:
                for test in push.tests:
                    assert isinstance(test(), GiskardTest)


def test_mad_transformation_mad_precomputed(enron_data):
    data = enron_data.copy().df
    res = mad_transformation(data, "salary", value_added=1000)
    assert res


def test_mad_transformation_mad_empty(enron_data):
    data = enron_data.copy().df
    res = mad_transformation(data, "salary")
    assert res


def test_mad_transformation_slicing(enron_data):
    @slicing_function(row_level=False)
    def head_slice(df: pd.DataFrame) -> pd.DataFrame:
        return df.head(10)

    data = enron_data.copy()
    res = mad_transformation(column_name="Nb_of_forwarded_msg")
    data_s = data.slice(head_slice)
    output = data_s.transform(res)
    assert output
