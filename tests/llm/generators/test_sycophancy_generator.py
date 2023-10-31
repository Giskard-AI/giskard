from unittest.mock import Mock

from giskard.datasets.base import Dataset
from giskard.llm.client import LLMFunctionCall, LLMOutput
from giskard.llm.generators.sycophancy import SycophancyDataGenerator


def test_generator_returns_dataset():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        LLMOutput(
            None,
            LLMFunctionCall(
                "generate_inputs",
                {
                    "inputs": [
                        {
                            "input_version_1": {"question": "What is the meaning of life?", "other_feature": "test 1"},
                            "input_version_2": {"question": "What is life?", "other_feature": "test 2"},
                        },
                        {
                            "input_version_1": {
                                "question": "What is the airspeed velocity of an European swallow?",
                                "other_feature": "test 1",
                            },
                            "input_version_2": {
                                "question": "What is the airspeed velocity of an African swallow?",
                                "other_feature": "test 2",
                            },
                        },
                    ]
                },
            ),
        )
    ] * 2

    model = Mock()
    model.meta.feature_names = ["question", "other_feature"]
    model.meta.name = "Mock model for test"
    model.meta.description = "This is a model for testing purposes"

    generator = SycophancyDataGenerator(
        llm_client=llm_client,
        llm_temperature=1.416,
        llm_model="gpt-99",
        prompt="My custom prompt {model_name} {model_description} {feature_names}, with {num_samples} samples",
    )

    dataset1, dataset2 = generator.generate_dataset(model, num_samples=2)
    for dataset in [dataset1, dataset2]:
        assert isinstance(dataset, Dataset)
        assert len(dataset) == 2

    assert dataset1.df.iloc[0]["question"] == "What is the meaning of life?"
    assert dataset1.df.iloc[1]["other_feature"] == "test 1"
    assert dataset2.df.iloc[1]["question"] == "What is the airspeed velocity of an African swallow?"
    assert dataset2.df.iloc[1]["other_feature"] == "test 2"

    llm_client.complete.assert_called_once()
    call_args = llm_client.complete.call_args

    called_prompt = call_args.kwargs["messages"][0]["content"]
    called_temperature = call_args.kwargs["temperature"]
    called_model = call_args.kwargs["model"]
    called_functions = call_args.kwargs["functions"]

    assert (
        called_prompt
        == "My custom prompt Mock model for test This is a model for testing purposes question, other_feature, with 2 samples"
    )
    assert called_temperature == 1.416
    assert called_model == "gpt-99"
    assert len(called_functions) == 1
    assert called_functions[0]["name"] == "generate_inputs"
