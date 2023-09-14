import os
import sys

import pytest
from giskard.llm.talk.talk import ModelSpec
from langchain.agents import AgentExecutor
from langchain.llms import FakeListLLM

from giskard import llm_config


def test_predict(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    expected = german_credit_model.predict(
        german_credit_test_data.slice(lambda df: df.head(10), row_level=False)
    ).prediction

    for i in range(10):
        assert model_spec.predict(german_credit_test_data.df.iloc[i].to_json()) == expected[i]


def test_predict_missing_features(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    assert (
        model_spec.predict(german_credit_test_data.df.drop("credit_history", axis=1).iloc[0].to_json())
        == "ValueError(\"Required features `{'credit_history'}` are not provided.\")"
    )


def test_explain_missing_features(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model, dataset=german_credit_test_data)

    assert (
        model_spec.explain(german_credit_test_data.df.drop("job", axis=1).iloc[0].to_json())
        == "ValueError(\"Required features `{'job'}` are not provided.\")"
    )


def test_explain_missing_dataset(german_credit_test_data, german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    assert (
        model_spec.explain(german_credit_test_data.df.drop("job", axis=1).iloc[0].to_json())
        == "Explanation is not available since no dataset has been provided"
    )


def test_scan_result_info_missing_scan(german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    assert model_spec.scan_result_info() == "The model should be scanned with Giskard first"


def test_model_quality_missing_scan(german_credit_model):
    model_spec = ModelSpec(model=german_credit_model)

    assert model_spec.model_quality() == "The model should be scanned with Giskard first"


def test_model_create_llm_agent(german_credit_test_data, german_credit_model):
    llm = FakeListLLM(responses=[""] * 100)
    llm_config.set_default_llm(llm)

    agent = german_credit_model._llm_agent(german_credit_test_data, True)

    assert isinstance(agent, AgentExecutor)
    assert agent.agent.allowed_tools == [
        "SKLearnModel_info",
        "model_description",
        "model_prediction",
        "model_explain_prediction",
    ]


@pytest.mark.skipif(
    sys.version_info.major < 9, reason="The Langchain agent use the new ast module implemented in Python 3.9"
)
def test_model_ask_description(german_credit_model):
    llm = FakeListLLM(
        responses=[
            """
            Action: model_description
            Action Input: None
            """,
            """
            Final Answer: The goal of this model is to predict if a potential debtor might default
            """,
        ]
        * 100
    )
    llm_config.set_default_llm(llm)

    assert (
        german_credit_model.talk("What is the goal of this model?")
        == "The goal of this model is to predict if a potential debtor might default"
    )


@pytest.mark.skipif(
    sys.version_info.major >= 9, reason="The Langchain agent use the new ast module implemented in Python 3.8"
)
def test_model_ask_description_invalid_version(german_credit_model):
    with pytest.raises(
        Exception,
        match=f"This tool relies on Python 3.9 or higher (as it uses new functionality in the `ast` module, you have Python version: {sys.version})",
    ):
        llm = FakeListLLM(
            responses=[
                """
                                    Action: model_description
                                    Action Input: None
                                    """,
                """
                                    Final Answer: The goal of this model is to predict if a potential debtor might default
                                    """,
            ]
            * 100
        )
        llm_config.set_default_llm(llm)

        german_credit_model.talk("What is the goal of this model?")


def test_model_talk_no_llm_nor_api_key(german_credit_model):
    llm_config.set_default_llm(None)

    previous_env = os.getenv("OPENAI_API_KEY")
    if previous_env is not None:
        del os.environ["OPENAI_API_KEY"]

    with pytest.raises(OSError):
        german_credit_model.talk("What is the goal of this model?")

    if previous_env is not None:
        os.environ["OPENAI_API_KEY"] = previous_env
