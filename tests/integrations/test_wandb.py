import sys

import pytest
import wandb

from giskard import scan
from giskard.models.model_explanation import explain_with_shap

NOT_SUPP_TEXT_WARNING_MSG = r"We do not support the wandb logging of ShapResult for text features yet.*"


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("hotel_text_data", "hotel_text_model"),
        ("drug_classification_data", "drug_classification_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes"),
    ],
)
@pytest.mark.memory_expensive
def test_fast(dataset_name, model_name, request):
    # Expect the 'NotImplementedError' when dataset contains textual features.
    exception_fixtures = ("hotel_text_data",)

    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)

    if dataset_name in exception_fixtures:
        with pytest.warns(
            UserWarning,
            match=NOT_SUPP_TEXT_WARNING_MSG,
        ):
            _to_wandb(model, dataset)
    else:
        _to_wandb(model, dataset)


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        pytest.param(
            "breast_cancer_data",
            "breast_cancer_model",
            marks=pytest.mark.skipif(sys.platform == "darwin", reason="xboost issue on macos"),
        ),
        ("german_credit_data", "german_credit_model"),
        ("enron_data_full", "enron_model"),
        ("medical_transcript_data", "medical_transcript_model"),
        # ("fraud_detection_data", "fraud_detection_model"),
        ("amazon_review_data", "amazon_review_model"),
    ],
)
@pytest.mark.slow
def test_slow(dataset_name, model_name, request):
    exception_fixtures = ("enron_data_full", "medical_transcript_data", "amazon_review_data")

    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)

    if dataset_name in exception_fixtures:
        with pytest.warns(
            UserWarning,
            match=NOT_SUPP_TEXT_WARNING_MSG,
        ):
            _to_wandb(model, dataset)
    else:
        _to_wandb(model, dataset)


def _to_wandb(model, dataset):
    run = wandb.init(project="tests")

    # verify that the logging of a dataset works
    dataset.to_wandb(run)

    # verify that the logging of scan results works
    scan_results = scan(model, dataset)
    scan_results.to_wandb(run)

    # verify that the logging of test suite results works
    test_suite_results = scan_results.generate_test_suite().run()
    test_suite_results.to_wandb(run)

    # Verify that the logging of the SHAP explanation charts works.
    explanation_results = explain_with_shap(model, dataset)
    explanation_results.to_wandb(run)

    run.finish()


@pytest.mark.parametrize(
    "dataset_name",
    ["german_credit_data"],
)
def test_error(dataset_name, request):
    dataset = request.getfixturevalue(dataset_name)

    with pytest.raises(ValueError, match=r"There are currently no active wandb runs available"):
        dataset.to_wandb()
