import pytest

from giskard import Dataset
from giskard.scanner import Scanner
from giskard.core.suite import Suite
from giskard.scanner.result import ScanResult
from giskard import GiskardClient


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("german_credit_data", "german_credit_model"),
        ("enron_data_full", "enron_model"),
        ("medical_transcript_data", "medical_transcript_model"),
        ("breast_cancer_data", "breast_cancer_model"),
        ("fraud_detection_data", "fraud_detection_model"),
        ("drug_classification_data", "drug_classification_model"),
        ("amazon_review_data", "amazon_review_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes"),
        ("hotel_text_data", "hotel_text_model"),
    ],
)
def test_scanner_returns_non_empty_scan_result(dataset_name, model_name, request):
    _EXCEPTION_MODELS = ["linear_regression_diabetes"]

    scanner = Scanner()

    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)

    result = scanner.analyze(model, dataset)

    assert isinstance(result, ScanResult)
    assert result.to_html()

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


@pytest.mark.skip(reason="For active testing of the UI")
@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("german_credit_data", "german_credit_model"),
        ("enron_data_full", "enron_model"),
        ("medical_transcript_data", "medical_transcript_model"),
        ("breast_cancer_data", "breast_cancer_model"),
        ("fraud_detection_data", "fraud_detection_model"),
        ("drug_classification_data", "drug_classification_model"),
        ("amazon_review_data", "amazon_review_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes"),
        ("hotel_text_data", "hotel_text_model"),
    ],
)
def test_scanner_on_the_UI(dataset_name, model_name, request):
    _EXCEPTION_MODELS = ["linear_regression_diabetes"]

    scanner = Scanner()

    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)

    result = scanner.analyze(model, dataset)

    # Do not do below tests for the diabetes regression model.
    if model_name not in _EXCEPTION_MODELS:
        test_suite = result.generate_test_suite()

        client = GiskardClient(
            url="http://localhost:19000",  # URL of your Giskard instance
            token="API_TOKEN"
        )

        try:
            client.create_project("testing_UI", "testing_UI", "testing_UI")
        except ValueError:
            pass

        test_suite.upload(client, "testing_UI")


def test_warning_duplicate_index(german_credit_model, german_credit_data):
    df = german_credit_data.df.copy()
    new_row = df.loc[1]
    df = df.append(new_row)

    dataset = Dataset(
        df=df,
        target=german_credit_data.target,
        cat_columns=german_credit_data.cat_columns
    )

    scanner = Scanner()

    with pytest.warns(match="You dataframe has duplicate indexes, which is currently not supported. "
                            "We have to reset the dataframe index to avoid issues."):
        scanner.analyze(german_credit_model, dataset)


def test_generate_test_suite_some_tests(titanic_model, titanic_dataset):
    scanner = Scanner()

    suite = scanner.analyze(titanic_model, titanic_dataset).generate_test_suite()
    created_tests = len(suite.tests)
    assert created_tests, "Titanic scan doesn't produce tests"
