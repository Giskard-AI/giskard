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

def test_scanner_without_dataset():
    from langchain import LLMChain, PromptTemplate
    from langchain.chat_models import ChatOpenAI
    from giskard import Model

    llm = ChatOpenAI(model="gpt-3.5-turbo")
    prompt = PromptTemplate(template="{input}", input_variables=["input"])
    chain = LLMChain(prompt=prompt, llm=llm)

    model = Model(chain, model_type='generative')
    scanner = Scanner()
    assert scanner.analyze(model)