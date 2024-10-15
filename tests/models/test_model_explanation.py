import sys

import numpy as np
import pytest

from giskard.datasets.base import Dataset
from giskard.models.base import BaseModel
from giskard.models.model_explanation import (
    _calculate_dataset_shap_values,
    _calculate_sample_shap_values,
    explain,
    explain_text,
)


@pytest.mark.parametrize(
    "ds_name, model_name, include_feature_names",
    [
        ("german_credit_test_data", "german_credit_model", True),
        ("german_credit_data", "german_credit_model", True),
        ("diabetes_dataset", "linear_regression_diabetes", True),
        ("diabetes_dataset_with_target", "linear_regression_diabetes", True),
        ("german_credit_test_data", "german_credit_model", False),
        ("german_credit_data", "german_credit_model", False),
        ("diabetes_dataset", "linear_regression_diabetes", False),
        ("diabetes_dataset_with_target", "linear_regression_diabetes", False),
        ("enron_data", "enron_model", False),
    ],
)
def test_explain(ds_name: str, model_name: str, include_feature_names: bool, request):
    ds: Dataset = request.getfixturevalue(ds_name)
    model: BaseModel = request.getfixturevalue(model_name)

    # Try without feature names, it should also work
    if not include_feature_names:
        model.meta.feature_names = None

    explanations = explain(model, ds, ds.df.iloc[0].to_dict())

    assert explanations and explanations.get("explanations")

    if model.is_classification:
        for label in model.classification_labels:
            label_explanation = explanations.get("explanations").get(label)
            assert label_explanation
            for i, e in label_explanation.items():
                assert np.issubdtype(type(e), np.floating), f"'{i}' explanation value isn't float"
    elif model.is_regression:
        assert "default" in explanations.get("explanations")
        exp = explanations.get("explanations").get("default")
        for i, e in exp.items():
            assert np.issubdtype(type(e), np.floating), f"'{i}' explanation value isn't float"


def test_explain_shuffle_columns(german_credit_test_data, german_credit_model):
    german_credit_model.meta.feature_names = None
    ds = german_credit_test_data
    # change column order
    res = explain(german_credit_model, ds, ds.df.iloc[0][ds.df.columns[::-1]].to_dict())
    assert res


def test_explain_text(enron_test_data, enron_model):
    df = enron_test_data.df.dropna()
    sample = df.head(1)
    result = explain_text(
        model=enron_model, input_df=sample, text_column="Content", text_document=sample["Content"].iloc[0]
    )
    assert result


def test_explain_text_regression(hotel_text_data, hotel_text_model):
    df = hotel_text_data.df.dropna()
    sample = df.head(1)
    result = explain_text(
        model=hotel_text_model, input_df=sample, text_column="Full_Review", text_document=sample["Full_Review"].iloc[0]
    )
    assert result


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("hotel_text_data", "hotel_text_model"),
        ("german_credit_data", "german_credit_model"),
        pytest.param(
            "breast_cancer_data",
            "breast_cancer_model",
            marks=pytest.mark.skipif(sys.platform == "darwin", reason="xboost issue on macos"),
        ),
        ("drug_classification_data", "drug_classification_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes"),
    ],
)
def test_equal_explain_functions_fast(dataset_name, model_name, request):
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    _compare_explain_functions(model, dataset)


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("enron_data_full", "enron_model"),
        ("medical_transcript_data", "medical_transcript_model"),
        ("fraud_detection_data", "fraud_detection_model"),
        ("amazon_review_data", "amazon_review_model"),
    ],
)
@pytest.mark.slow
def test_equal_explain_functions_slow(dataset_name, model_name, request):
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    _compare_explain_functions(model, dataset)


def _compare_explain_functions(model, dataset):
    # Form one-sample dataset, as the 'explain' function process such input.
    one_sample_dataset = Dataset(
        dataset.df.head(1), target=dataset.target, column_types=dataset.column_types, validation=False
    )

    # Define 'explain_full' input.
    dataset_shap_input = {"model": model, "dataset": one_sample_dataset}

    # Define 'explain_one' input.
    sample_shap_input = dataset_shap_input.copy()
    sample_shap_input["input_data"] = one_sample_dataset.df.iloc[0].to_dict()

    # Check if outputs are equal.
    assert (
        np.isclose(
            _calculate_sample_shap_values(**sample_shap_input), _calculate_dataset_shap_values(**dataset_shap_input)
        )
    ).all()
