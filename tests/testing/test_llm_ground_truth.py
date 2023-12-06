import pandas as pd
import pytest
from langchain.chains import LLMChain
from langchain.llms.fake import FakeListLLM

from giskard import Model, Dataset
from giskard.testing.tests.llm import test_llm_ground_truth_similarity, test_llm_ground_truth


def test_ground_truth_exact():
    llm = FakeListLLM(responses=["GREETING", "GREETING", "NOT_GREETING"])
    chain = LLMChain.from_string(llm=llm, template="Is it a greeting: {text}")
    model = Model(
        chain,
        "text_generation",
        feature_names=["text"],
        name="Greeting classification",
        description="Classify text between GREETING and NOT_GREETING",
    )

    dataset = Dataset(
        pd.DataFrame(
            {
                "text": ["Bonjour, comment ca va?", "Hi, how are you?", "Je traduis en anglais"],
                "target": ["GREETING", "GREETING", "NOT_GREETING"],
            }
        ),
        target="target",
    )

    result = test_llm_ground_truth(model, dataset).execute()

    assert result.passed

    llm = FakeListLLM(responses=["NOT_GREETING" * 3])
    chain = LLMChain.from_string(llm=llm, template="Is it a greeting: {text}")
    model = Model(
        chain,
        "text_generation",
        feature_names=["text"],
        name="Greeting classification",
        description="Classify text between GREETING and NOT_GREETING",
    )

    result = test_llm_ground_truth(model, dataset).execute()

    assert not result.passed


def test_ground_truth_exact_no_target():
    llm = FakeListLLM(responses=["GREETING", "GREETING", "NOT_GREETING"])
    chain = LLMChain.from_string(llm=llm, template="Is it a greeting: {text}")
    model = Model(
        chain,
        "text_generation",
        feature_names=["text"],
        name="Greeting classification",
        description="Classify text between GREETING and NOT_GREETING",
    )

    dataset = Dataset(
        pd.DataFrame(
            {
                "text": ["Bonjour, comment ca va?", "Hi, how are you?", "Je traduis en anglais"],
            }
        )
    )

    with pytest.raises(ValueError):
        test_llm_ground_truth(model, dataset).execute()


@pytest.mark.memory_expensive
def test_ground_truth_similarity():
    llm = FakeListLLM(responses=["Hello, how are you?", "Salut, ca va?", "I translate in English"])
    chain = LLMChain.from_string(llm=llm, template="Translate in {lang}: {text}")
    model = Model(
        chain,
        "text_generation",
        feature_names=["lang", "text"],
        name="Translator",
        description="Translate to any language",
    )

    dataset = Dataset(
        pd.DataFrame(
            {
                "lang": ["en", "fr", "en"],
                "text": ["Bonjour, comment ca va?", "Hi, how are you?", "Je traduis en anglais"],
                "target": ["Hi, how are you?", "Bonjour, comment ca va?", "I translate in English"],
            }
        ),
        target="target",
    )

    result = test_llm_ground_truth_similarity(model, dataset).execute()

    assert result.passed

    llm = FakeListLLM(responses=["Sorry, I don't know the translation" * 3])
    chain = LLMChain.from_string(llm=llm, template="Translate in {lang}: {text}")
    model = Model(
        chain,
        "text_generation",
        feature_names=["lang", "text"],
        name="Translator",
        description="Translate to any language",
    )

    result = test_llm_ground_truth_similarity(model, dataset).execute()

    assert not result.passed


def test_ground_truth_similarity_no_target():
    llm = FakeListLLM(responses=["Hello, how are you?", "Salut, ca va?", "I translate in English"])
    chain = LLMChain.from_string(llm=llm, template="Translate in {lang}: {text}")
    model = Model(
        chain,
        "text_generation",
        feature_names=["lang", "text"],
        name="Translator",
        description="Translate to any language",
    )

    dataset = Dataset(
        pd.DataFrame(
            {
                "lang": ["en", "fr", "en"],
                "text": ["Bonjour, comment ca va?", "Hi, how are you?", "Je traduis en anglais"],
            }
        )
    )

    with pytest.raises(ValueError):
        test_llm_ground_truth_similarity(model, dataset).execute()