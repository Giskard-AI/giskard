import pytest
from giskard.core.suite import Suite
from giskard.scanner import Scanner
from giskard.scanner.result import ScanResult


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


def test_classification_model_no_dataset(german_credit_model):
    scanner = Scanner()
    with pytest.raises(ValueError):
        scanner.analyze(german_credit_model)


def test_generative_model_no_dataset():
    from langchain import LLMChain, PromptTemplate
    from langchain.chat_models import ChatOpenAI
    from giskard import Model
    from unittest.mock import patch

    llm = ChatOpenAI(model="gpt-3.5-turbo")
    prompt = PromptTemplate(template="{input}", input_variables=["input"])
    chain = LLMChain(prompt=prompt, llm=llm)

    model = Model(chain, model_type='generative')
    scanner = Scanner()


    with patch('Scanner().analyze(Model()).load_default_dataset()'):
        scanner.analyze(model)


def test_generative_model_dataset():
    from langchain import LLMChain, PromptTemplate
    from langchain.chat_models import ChatOpenAI
    from giskard import Model, Dataset
    import pandas as pd

    llm = ChatOpenAI(model="gpt-3.5-turbo")
    prompt = PromptTemplate(template="{input}", input_variables=["input"])
    chain = LLMChain(prompt=prompt, llm=llm)

    model = Model(chain, model_type='generative')
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
    assert scanner.analyze(model, dataset)
