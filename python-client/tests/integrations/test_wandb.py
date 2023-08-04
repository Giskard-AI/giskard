import wandb
import pytest
import re

from giskard import scan

wandb.setup(wandb.Settings(mode="disabled", program=__name__, program_relpath=__name__, disable_code=True))


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("german_credit_data", "german_credit_model"),
        ("breast_cancer_data", "breast_cancer_model"),
        ("drug_classification_data", "drug_classification_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes"),
        ("hotel_text_data", "hotel_text_model"),
    ],
)
def test_fast(dataset_name, model_name, request):
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
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
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    _to_wandb(model, dataset)


def _to_wandb(model, dataset):
    # verify that the logging of a dataset works
    dataset.to_wandb()

    # verify that the logging of scan results works
    scan_results = scan(model, dataset)
    scan_results.to_wandb()

    # verify that the logging of test suite results works
    test_suite_results = scan_results.generate_test_suite().run()
    test_suite_results.to_wandb()

    assert re.match("^[0-9a-z]{8}$", str(wandb.run.id))
