import sys

import numpy as np
import pandas as pd
import pytest

import giskard.push
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
    slice_bounds_quartile,
)
from giskard.slicing.slice import QueryBasedSliceFunction

DATASETS = [
    pytest.param(("german_credit_model", "german_credit_data", 50), id="German Credit"),
    pytest.param(("enron_model", "enron_data", 50), id="Enron"),
    pytest.param(("linear_regression_diabetes", "diabetes_dataset_with_target", 50), id="Diabetes"),
]

PUSH_TYPES = [
    pytest.param(("contribution", giskard.push.ContributionPush, create_contribution_push), id="Contribution"),
    pytest.param(("perturbation", giskard.push.PerturbationPush, create_perturbation_push), id="Perturbation"),
    pytest.param(("overconfidence", giskard.push.OverconfidencePush, create_overconfidence_push), id="Overconfidence"),
    pytest.param(("borderline", giskard.push.BorderlinePush, create_borderline_push), id="Borderline"),
]
# fmt: off
EXPECTED_COUNTS = {
    "german_credit_model" : {
        "contribution" :[0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1],
        "perturbation": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "overconfidence": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "borderline": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    },
    "linear_regression_diabetes": {
        "contribution" :[0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0],
        "perturbation" :[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "overconfidence" :[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "borderline" :[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
    "enron_model": {
        "contribution" :[0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "perturbation" :[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "overconfidence" :[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "borderline" :[0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    }
}
# fmt: on


@pytest.mark.parametrize("dataset", DATASETS)
@pytest.mark.parametrize("push_type", PUSH_TYPES)
def test_test_function(request, dataset, push_type):
    model_name, data_name, nb_line = dataset
    model = request.getfixturevalue(model_name)
    data = request.getfixturevalue(data_name)

    push_type_name, push_type_class, push_func = push_type
    if model_name == "enron_model" and push_type_name == "perturbation" and sys.platform == "win32":
        pytest.skip("This test give different results on windows")

    push_list = []
    for i in range(nb_line):
        push: Push = push_func(model, data, data.df.iloc[[i]])
        if push is not None:
            assert isinstance(push, Push)
            assert isinstance(push, push_type_class)
            push_list.append(len(push.tests))
            assert all([isinstance(test(), GiskardTest) for test in push.tests])
            if hasattr(push, "slicing_function"):
                assert isinstance(push.slicing_function, QueryBasedSliceFunction)
        else:
            push_list.append(0)
    print(push_list)
    assert push_list == EXPECTED_COUNTS[model_name][push_type_name]


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
    bounds = slice_bounds_quartile("credit_amount", q2, german_credit_data)
    assert bounds == (q2, q3)

    # Test min/max
    bounds = slice_bounds_quartile("credit_amount", numeric_col.min(), german_credit_data)
    assert bounds == (numeric_col.min(), q1)

    bounds = slice_bounds_quartile("credit_amount", numeric_col.max(), german_credit_data)
    assert bounds == (q3, numeric_col.max())

    # Test valid values
    bounds = slice_bounds_quartile("credit_amount", 1500, german_credit_data)
    assert bounds == (1365.5, 2319.5)

    bounds = slice_bounds_quartile("credit_amount", 2500, german_credit_data)
    assert bounds == (2319.5, 3972.25)


def test_slice_bounds_non_numeric(german_credit_data):
    bounds = slice_bounds_quartile("account_check_status", "c", german_credit_data)
    assert bounds is None


def test_coltype_to_supported_perturbation_type():
    perturbation_type = coltype_to_supported_perturbation_type("numeric")
    assert perturbation_type == SupportedPerturbationType.NUMERIC

    perturbation_type = coltype_to_supported_perturbation_type("text")
    assert perturbation_type == SupportedPerturbationType.TEXT


def test_text_explain_in_push(medical_transcript_model, medical_transcript_data):
    problematic_df_entry = medical_transcript_data.df.iloc[[3]]
    output = create_contribution_push(medical_transcript_model, medical_transcript_data, problematic_df_entry)
    assert output is not None
    assert output.value is not None
