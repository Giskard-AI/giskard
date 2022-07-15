import numpy as np
import pytest

from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.core.model import GiskardModel
from ml_worker.core.model_explanation import explain


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
        ("diabetes_dataset_with_target", "linear_regression_diabetes", False)
    ]
)
def test_explain(ds_name: str, model_name: str, include_feature_names: bool, request):
    ds: GiskardDataset = request.getfixturevalue(ds_name)
    model: GiskardModel = request.getfixturevalue(model_name)

    # Try without feature names, it should also work
    if not include_feature_names:
        model.feature_names = None

    explanations = explain(model, ds, ds.df.iloc[0].to_dict())

    assert explanations and explanations.get('explanations')

    if model.model_type == "classification":
        for l in model.classification_labels:
            label_explanation = explanations.get('explanations').get(l)
            assert label_explanation
            for l, e in label_explanation.items():
                assert np.issubdtype(type(e), np.floating), f"'{l}' explanation value isn't float"
    elif model.model_type == "regression":
        assert 'default' in explanations.get('explanations')
        exp = explanations.get('explanations').get('default')
        for l, e in exp.items():
            assert np.issubdtype(type(e), np.floating), f"'{l}' explanation value isn't float"
