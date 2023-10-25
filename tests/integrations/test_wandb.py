import wandb
import pytest
import re

from giskard import scan
from giskard.models.model_explanation import explain_with_shap

wandb.setup(wandb.Settings(mode="disabled", program=__name__, program_relpath=__name__, disable_code=True))

NOT_SUPP_TEXT_WARNING_MSG = r"We do not support the wandb logging of ShapResult for text features yet.*"


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
        ("enron_data_full", "enron_model"),
        ("medical_transcript_data", "medical_transcript_model"),
        ("fraud_detection_data", "fraud_detection_model"),
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

    assert re.match("^[0-9a-z]{8}$", str(run.id))
    run.finish()
