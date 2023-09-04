import numpy as np
from giskard.ml_worker.testing.functions.transformation import mad_transformation

from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.slicing_function import slicing_function
from giskard.push import Push
from giskard.push.contribution import create_contribution_push
from giskard.push.perturbation import create_perturbation_push
from giskard.push.prediction import create_borderline_push, create_overconfidence_push
from giskard.push.utils import (
    SupportedPerturbationType,
    TransformationInfo,
    coltype_to_supported_perturbation_type,
    slice_bounds,
)
from giskard.slicing.slice import QueryBasedSliceFunction
import pandas as pd


# Classification
def test_instance_if_not_none(german_credit_model, german_credit_data):
    for i in range(50):
        push_list = [
            create_contribution_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_perturbation_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_overconfidence_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
            create_borderline_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
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
            create_borderline_push(german_credit_model, german_credit_data, german_credit_data.df.iloc[[i]]),
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
            create_borderline_push(
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
            create_borderline_push(
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
            create_borderline_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
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
            create_borderline_push(enron_model, enron_data, enron_data.df.iloc[[i]]),
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


def test_supported_perturbation_type_enum():
    assert SupportedPerturbationType.NUMERIC.value == "numeric"
    assert SupportedPerturbationType.TEXT.value == "text"


def test_transformation_info():
    ti = TransformationInfo([1, 2], [np.log, np.sqrt], [{"base": 2}, {}])
    assert ti.value_perturbed == [1, 2]
    assert ti.transformation_functions == [np.log, np.sqrt]
    assert ti.transformation_functions_params == [{"base": 2}, {}]


def test_slice_bounds_valid_numeric(german_credit_data):
    numeric_col = german_credit_data.df["credit_amount"]
    # Get quartile bounds
    q1, q2, q3 = np.percentile(numeric_col, [25, 50, 75])

    # Test quartile values
    bounds = slice_bounds("credit_amount", q2, german_credit_data)
    assert bounds == [q2, q3]

    # Test min/max
    bounds = slice_bounds("credit_amount", numeric_col.min(), german_credit_data)
    assert bounds == [numeric_col.min(), q1]

    bounds = slice_bounds("credit_amount", numeric_col.max(), german_credit_data)
    assert bounds == [q3, numeric_col.max()]

    # Test valid values
    bounds = slice_bounds("credit_amount", 1500, german_credit_data)
    assert bounds == [1365.5, 2319.5]

    bounds = slice_bounds("credit_amount", 2500, german_credit_data)
    assert bounds == [2319.5, 3972.25]


def test_slice_bounds_non_numeric(german_credit_data):
    bounds = slice_bounds("account_check_status", "c", german_credit_data)
    assert bounds is None


def test_coltype_to_supported_perturbation_type():
    perturbation_type = coltype_to_supported_perturbation_type("numeric")
    assert perturbation_type == SupportedPerturbationType.NUMERIC

    perturbation_type = coltype_to_supported_perturbation_type("text")
    assert perturbation_type == SupportedPerturbationType.TEXT
