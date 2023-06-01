import pytest

from giskard.scanner import Scanner
from giskard.core.suite import Suite
from giskard.scanner.result import ScanResult


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("german_credit_data", "german_credit_model"),
        ("enron_data", "enron_model"),
        ("medical_transcript_data", "medical_transcript_model"),
        ("breast_cancer_data", "breast_cancer_model"),
        ("fraud_detection_data", "fraud_detection_model"),
        ("drug_classification_data", "drug_classification_model"),
        ("amazon_review_data", "amazon_review_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes")
    ],
)
def test_scanner_returns_non_empty_scan_result(dataset_name, model_name, request):
    _EXCEPTION_MODELS = ["linear_regression_diabetes"]

    scanner = Scanner()

    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)

    result = scanner.analyze(model, dataset)

    assert isinstance(result, ScanResult)

    # Do not do below tests for the diabetes regression model.
    if model_name not in _EXCEPTION_MODELS:
        assert result.has_issues()

        test_suite = result.generate_test_suite()
        assert isinstance(test_suite, Suite)


def test_scanner_should_work_with_empty_model_feature_names(german_credit_data, german_credit_model):
    scanner = Scanner()
    german_credit_model.meta.feature_names = None
    result = scanner.analyze(german_credit_model, german_credit_data)

    assert isinstance(result, ScanResult)
    assert result.has_issues()


def test_scanner_raises_exception_if_no_detectors_available(german_credit_data, german_credit_model):
    scanner = Scanner(only="non-existent-detector")

    with pytest.raises(RuntimeError):
        scanner.analyze(german_credit_model, german_credit_data)
