from unittest.mock import Mock

import pytest

from giskard.datasets.base import Dataset
from giskard.llm.client import LLMFunctionCall, LLMOutput
from giskard.llm.errors import LLMGenerationError
from giskard.llm.generators.adversarial import AdversarialDataGenerator
from giskard.llm.generators.base import BaseDataGenerator
from giskard.llm.generators.implausible import ImplausibleDataGenerator
from giskard.llm.generators.sycophancy import SycophancyDataGenerator


@pytest.mark.parametrize(
    "Generator,args,kwargs",
    [
        (BaseDataGenerator, [], {}),
        (ImplausibleDataGenerator, [], {}),
        (AdversarialDataGenerator, ["demo", "demo"], {}),
    ],
)
def test_generator_returns_dataset(Generator, args, kwargs):
    llm_client = Mock()
    llm_client.complete.side_effect = [
        LLMOutput(
            None,
            LLMFunctionCall(
                "generate_inputs",
                {
                    "inputs": [
                        {"question": "What is the meaning of life?", "other_feature": "test"},
                        {"question": "What is the airspeed velocity of an unladen swallow?", "other_feature": "pass"},
                    ]
                },
            ),
        )
    ]

    model = Mock()
    model.feature_names = ["question", "other_feature"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"

    generator = Generator(
        *args,
        **kwargs,
        llm_client=llm_client,
        llm_temperature=1.416,
        prompt="My custom prompt {model_name} {model_description} {feature_names}, with {num_samples} samples",
    )

    dataset = generator.generate_dataset(model, num_samples=2)

    assert isinstance(dataset, Dataset)
    assert len(dataset) == 2
    assert dataset.df.iloc[0]["question"] == "What is the meaning of life?"
    assert dataset.df.iloc[1]["other_feature"] == "pass"

    llm_client.complete.assert_called_once()

    called_prompt = llm_client.complete.call_args[1]["messages"][0]["content"]
    called_temperature = llm_client.complete.call_args[1]["temperature"]
    called_functions = llm_client.complete.call_args[1]["functions"]

    assert (
        called_prompt
        == "My custom prompt Mock model for test This is a model for testing purposes question, other_feature, with 2 samples"
    )
    assert called_temperature == 1.416
    assert len(called_functions) == 1
    assert called_functions[0]["name"] == "generate_inputs"


@pytest.mark.parametrize(
    "Generator,args,kwargs",
    [
        (BaseDataGenerator, [], {}),
        (ImplausibleDataGenerator, [], {}),
        (SycophancyDataGenerator, [], {}),
        (AdversarialDataGenerator, ["demo", "demo"], {}),
    ],
)
def test_generator_raises_generation_error_if_function_call_fails(Generator, args, kwargs):
    # Missing function call
    llm_client = Mock()
    llm_client.complete.side_effect = [LLMOutput("Sorry, I can't.", None)]

    model = Mock()
    model.feature_names = ["question", "other_feature"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"

    generator = Generator(*args, **kwargs, llm_client=llm_client)

    with pytest.raises(LLMGenerationError):
        generator.generate_dataset(model, num_samples=2)

    # Wrong function call
    llm_client = Mock()
    llm_client.complete.side_effect = [LLMOutput(None, LLMFunctionCall("wrong_function", {"have_no_inputs": True}))]

    model = Mock()
    model.feature_names = ["question", "other_feature"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"

    generator = Generator(*args, **kwargs, llm_client=llm_client)

    with pytest.raises(LLMGenerationError):
        generator.generate_dataset(model, num_samples=2)


@pytest.mark.parametrize(
    "Generator,args,kwargs",
    [
        (BaseDataGenerator, [], {}),
        (ImplausibleDataGenerator, [], {}),
    ],
)
def test_generator_casts_based_on_column_types(Generator, args, kwargs):
    llm_client = Mock()
    llm_client.complete.side_effect = [
        LLMOutput(
            None,
            LLMFunctionCall(
                "generate_inputs",
                {
                    "inputs": [
                        {"question": True, "other_feature": 1},
                        {"question": False, "other_feature": 2},
                    ]
                },
            ),
        )
    ] * 2

    model = Mock()
    model.feature_names = ["question", "other_feature"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"

    generator = Generator(
        *args,
        **kwargs,
        llm_client=llm_client,
        llm_temperature=1.416,
        prompt="My custom prompt {model_name} {model_description} {feature_names}, with {num_samples} samples",
    )
    generator = BaseDataGenerator(llm_client=llm_client)

    dataset = generator.generate_dataset(model, num_samples=2)

    assert dataset.column_types["question"] == "numeric"
    assert dataset.column_types["other_feature"] == "numeric"

    dataset = generator.generate_dataset(
        model, num_samples=2, column_types={"question": "text", "other_feature": "numeric"}
    )

    assert dataset.column_types["question"] == "text"
    assert dataset.column_types["other_feature"] == "numeric"


@pytest.mark.parametrize(
    "Generator,args,kwargs",
    [
        (BaseDataGenerator, [], {}),
        (ImplausibleDataGenerator, [], {}),
        (AdversarialDataGenerator, ["demo", "demo"], {}),
    ],
)
def test_generator_adds_languages_requirements_in_prompts(Generator, args, kwargs):
    llm_client = Mock()
    llm_client.complete.side_effect = [
        LLMOutput(
            None,
            LLMFunctionCall(
                "generate_inputs",
                {
                    "inputs": [
                        {"question": "What is the meaning of life?", "other_feature": "test"},
                        {
                            "question": "Quel est le rôle des gaz à effet de serre dans le réchauffement climatique??",
                            "other_feature": "pass",
                        },
                    ]
                },
            ),
        )
    ]

    model = Mock()
    model.feature_names = ["question", "other_feature"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"

    generator = Generator(
        *args,
        **kwargs,
        llm_client=llm_client,
        llm_temperature=1.416,
        prompt="My custom prompt {model_name} {model_description} {feature_names}, with {num_samples} samples.\n",
        languages=["en", "fr"],
    )

    dataset = generator.generate_dataset(model, num_samples=2)

    llm_client.complete.assert_called_once()

    called_prompt = llm_client.complete.call_args[1]["messages"][0]["content"]
    prompt_with_language_requirement = "My custom prompt Mock model for test This is a model for testing purposes question, other_feature, with 2 samples.\nYou must generate input using different languages among the following list: ['en', 'fr']."

    assert isinstance(dataset, Dataset)
    assert called_prompt == prompt_with_language_requirement


@pytest.mark.parametrize(
    "Generator,args,kwargs",
    [
        (BaseDataGenerator, [], {}),
        (ImplausibleDataGenerator, [], {}),
        (AdversarialDataGenerator, ["demo", "demo"], {}),
    ],
)
def test_generator_empty_languages_requirements(Generator, args, kwargs):
    llm_client = Mock()
    llm_client.complete.side_effect = [
        LLMOutput(
            None,
            LLMFunctionCall(
                "generate_inputs",
                {
                    "inputs": [
                        {"question": "What is the meaning of life?", "other_feature": "test"},
                        {
                            "question": "Quel est le rôle des gaz à effet de serre dans le réchauffement climatique??",
                            "other_feature": "pass",
                        },
                    ]
                },
            ),
        )
    ]

    model = Mock()
    model.feature_names = ["question", "other_feature"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"

    generator = Generator(
        *args,
        **kwargs,
        llm_client=llm_client,
        llm_temperature=1.416,
        prompt="My custom prompt {model_name} {model_description} {feature_names}, with {num_samples} samples.\n",
        languages=[],
    )

    dataset = generator.generate_dataset(model, num_samples=2)

    llm_client.complete.assert_called_once()

    called_prompt = llm_client.complete.call_args[1]["messages"][0]["content"]

    assert isinstance(dataset, Dataset)
    assert (
        called_prompt
        == "My custom prompt Mock model for test This is a model for testing purposes question, other_feature, with 2 samples.\n"
    )
