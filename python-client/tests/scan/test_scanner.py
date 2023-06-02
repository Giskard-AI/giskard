import pytest
import pandas as pd
from unittest import mock
from giskard import Model, Dataset
from giskard.scanner import Scanner
from giskard.core.suite import Suite
from giskard.scanner.result import ScanResult
from langchain import LLMChain, PromptTemplate
from langchain.llms.fake import FakeListLLM


def test_scanner_returns_non_empty_scan_result(german_credit_data, german_credit_model):
    scanner = Scanner()
    result = scanner.analyze(german_credit_model, german_credit_data)

    assert isinstance(result, ScanResult)
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


def test_scan_raises_exception_if_no_dataset_provided(german_credit_model):
    scanner = Scanner()
    with pytest.raises(ValueError) as info:
        scanner.analyze(german_credit_model)
    assert "Dataset must be provided " in str(info.value)


def test_default_dataset_is_used_with_generative_model():
    model = mock.MagicMock()
    model.is_generative = True
    scanner = Scanner()

    with mock.patch('giskard.scanner.llm.utils.load_default_dataset') as load_default_dataset:
        try:
            scanner.analyze(model)
        except:  # noqa
            pass
        load_default_dataset.assert_called_once()


def test_generative_model_dataset():
    llm = FakeListLLM(responses=["Are you dumb or what?", "I don't know and I don’t want to know."] * 100)
    prompt = PromptTemplate(template="{instruct}: {question}", input_variables=["instruct", "question"])
    chain = LLMChain(llm=llm, prompt=prompt)
    model = Model(chain, model_type="generative")
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
