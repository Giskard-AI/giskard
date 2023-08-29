import re
import warnings
from unittest import mock

import numpy as np
import pandas as pd
import pytest
from langchain import LLMChain, PromptTemplate
from langchain.llms.fake import FakeListLLM

from giskard import Dataset, GiskardClient, Model
from giskard.core.suite import Suite
from giskard.scanner import Scanner
from giskard.scanner.report import ScanReport


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
def test_scanner_returns_non_empty_scan_result_fast(dataset_name, model_name, request):
    _test_scanner_returns_non_empty_scan_result(dataset_name, model_name, request)


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
def test_scanner_returns_non_empty_scan_result_slow(dataset_name, model_name, request):
    _test_scanner_returns_non_empty_scan_result(dataset_name, model_name, request)


def _test_scanner_returns_non_empty_scan_result(dataset_name, model_name, request):
    _EXCEPTION_MODELS = ["linear_regression_diabetes"]

    scanner = Scanner()

    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)

    result = scanner.analyze(model, dataset, raise_exceptions=True)

    assert isinstance(result, ScanReport)
    assert result.to_html()

    # Do not do below tests for the diabetes regression model.
    if model_name not in _EXCEPTION_MODELS:
        assert result.has_issues()

        test_suite = result.generate_test_suite()
        assert isinstance(test_suite, Suite)


def test_scanner_should_work_with_empty_model_feature_names(german_credit_data, german_credit_model):
    scanner = Scanner()
    german_credit_model.meta.feature_names = None
    result = scanner.analyze(german_credit_model, german_credit_data, raise_exceptions=True)

    assert isinstance(result, ScanReport)
    assert result.has_issues()


def test_scanner_raises_exception_if_no_detectors_available(german_credit_data, german_credit_model):
    scanner = Scanner(only="non-existent-detector")

    with pytest.raises(RuntimeError):
        scanner.analyze(german_credit_model, german_credit_data)


def test_scanner_works_if_dataset_has_no_target(titanic_model, titanic_dataset):
    scanner = Scanner()
    no_target_dataset = Dataset(titanic_dataset.df, target=None)
    result = scanner.analyze(titanic_model, no_target_dataset, raise_exceptions=True)

    assert isinstance(result, ScanReport)
    assert result.has_issues()
    assert result.to_html()


def test_scan_raises_exception_if_no_dataset_provided(german_credit_model):
    scanner = Scanner()
    with pytest.raises(ValueError) as info:
        scanner.analyze(german_credit_model)
    assert "Dataset must be provided " in str(info.value)


def test_default_dataset_is_used_with_generative_model():
    model = mock.MagicMock(Model)
    model.is_text_generation = True
    scanner = Scanner()

    with mock.patch("giskard.scanner.llm.utils.load_default_dataset") as load_default_dataset:
        try:
            scanner.analyze(model)
        except:  # noqa
            pass
        load_default_dataset.assert_called_once()


@pytest.mark.slow
def test_generative_model_dataset():
    llm = FakeListLLM(responses=["Are you dumb or what?", "I don't know and I don’t want to know."] * 100)
    prompt = PromptTemplate(template="{instruct}: {question}", input_variables=["instruct", "question"])
    chain = LLMChain(llm=llm, prompt=prompt)
    model = Model(chain, model_type="text_generation")
    dataset = Dataset(
        pd.DataFrame(
            {
                "instruct": ["Paraphrase this", "Answer this question"],
                "question": ["Who is the mayor of Rome?", "How many bridges are there in Paris?"],
            }
        ),
        column_types={"instruct": "text", "question": "text"},
    )

    scanner = Scanner()
    result = scanner.analyze(model, dataset)
    assert result.has_issues()


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

        client = GiskardClient(url="http://localhost:19000", token="API_TOKEN")  # URL of your Giskard instance

        try:
            client.create_project("testing_UI", "testing_UI", "testing_UI")
        except ValueError:
            pass

        test_suite.upload(client, "testing_UI")


@pytest.mark.slow
def test_warning_duplicate_index(german_credit_model, german_credit_data):
    df = german_credit_data.df.copy()
    new_row = df.loc[1]
    df = df.append(new_row)

    dataset = Dataset(df=df, target=german_credit_data.target, cat_columns=german_credit_data.cat_columns)

    scanner = Scanner()

    with pytest.warns(
        match="You dataframe has duplicate indexes, which is currently not supported. "
        "We have to reset the dataframe index to avoid issues."
    ):
        scanner.analyze(german_credit_model, dataset)


@pytest.mark.slow
def test_generate_test_suite_some_tests(titanic_model, titanic_dataset):
    scanner = Scanner()

    suite = scanner.analyze(titanic_model, titanic_dataset).generate_test_suite()
    created_tests = len(suite.tests)
    assert created_tests, "Titanic scan doesn't produce tests"


def test_scanner_raises_error_if_non_giskard_model_is_passed(titanic_model, titanic_dataset):
    scanner = Scanner()
    msg = re.escape("The model object you provided is not valid. Please wrap it with the `giskard.Model` class.")
    with pytest.raises(ValueError, match=msg):
        scanner.analyze(titanic_model.model, titanic_dataset)


def test_scanner_raises_error_if_non_giskard_dataset_is_passed(titanic_model, titanic_dataset):
    scanner = Scanner()
    msg = re.escape("The dataset object you provided is not valid")
    with pytest.raises(ValueError, match=msg):
        scanner.analyze(titanic_model, titanic_dataset.df)


def test_scanner_warns_if_too_many_features():
    scanner = Scanner()

    # Model with no feature names
    model = Model(lambda x: np.ones(len(x)), model_type="classification", classification_labels=[0, 1])
    dataset = Dataset(pd.DataFrame(np.ones((10, 120)), columns=map(str, np.arange(120))), target="0")

    with pytest.warns(
        UserWarning, match=re.escape("It looks like your dataset has a very large number of features (120)")
    ):
        scanner.analyze(model, dataset)

    # Model specifying few feature names should not raise a warning
    model = Model(
        lambda x: np.ones(len(x)),
        model_type="classification",
        classification_labels=[0, 1],
        feature_names=["1", "2", "3"],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        scanner.analyze(model, dataset)
