import numpy as np
import pytest

from giskard.datasets.base import Dataset
from giskard.models.base import BaseModel
from giskard.models.model_explanation import explain, explain_text


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
        model.feature_names = None

    explanations = explain(model, ds, ds.df.iloc[0].to_dict())

    assert explanations and explanations.get("explanations")

    if model.is_classification:
        for label in model.meta.classification_labels:
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
    german_credit_model.feature_names = None
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
