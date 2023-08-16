import wandb
import pytest
import re

import numpy as np

from giskard import scan, Dataset
from giskard.models.model_explanation import explain_with_shap, explain_full, explain_one

wandb.setup(wandb.Settings(mode="disabled", program=__name__, program_relpath=__name__, disable_code=True))


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("hotel_text_data", "hotel_text_model"),
        ("german_credit_data", "german_credit_model"),
        ("breast_cancer_data", "breast_cancer_model"),
        ("drug_classification_data", "drug_classification_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes"),
    ],
)
def test_fast(dataset_name, model_name, request):
    # Expect the 'NotImplementedError' when dataset contains textual features.
    exception_fixtures = ("hotel_text_data",)

    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    _compare_explain_functions(model, dataset)

    if dataset_name in exception_fixtures:
        with pytest.raises(NotImplementedError) as e:
            _to_wandb(model, dataset)
        assert e.match(r"We do not support the SHAP logging of text*")


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
def test_slow(dataset_name, model_name, request):
    exception_fixtures = ("enrol_data_full", "medical_transcript_data", "amazon_review_data")

    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    _compare_explain_functions(model, dataset)

    if dataset_name in exception_fixtures:
        with pytest.raises(NotImplementedError) as e:
            _to_wandb(model, dataset)
        assert e.match(r"We do not support the SHAP logging of text*")


def _to_wandb(model, dataset):
    # verify that the logging of a dataset works
    dataset.to_wandb()

    # verify that the logging of scan results works
    scan_results = scan(model, dataset)
    scan_results.to_wandb()

    # verify that the logging of test suite results works
    test_suite_results = scan_results.generate_test_suite().run()
    test_suite_results.to_wandb()

    # Verify that the logging of the SHAP explanation charts works.
    explanation_results = explain_with_shap(model, dataset)
    explanation_results.to_wandb()

    assert re.match("^[0-9a-z]{8}$", str(wandb.run.id))


def _compare_explain_functions(model, dataset):
    # Form one-sample dataset, as the 'explain' function process such input.
    one_sample_dataset = Dataset(
        dataset.df.head(1), target=dataset.target, column_types=dataset.column_types, validation=False
    )

    # Define 'explain_full' input.
    explain_full_input = {"model": model, "dataset": one_sample_dataset}

    # Define 'explain_one' input.
    explain_one_input = explain_full_input.copy()
    explain_one_input["input_data"] = one_sample_dataset.df.iloc[0].to_dict()

    # Check if outputs are equal.
    assert (np.isclose(explain_one(**explain_one_input), explain_full(**explain_full_input))).all()
