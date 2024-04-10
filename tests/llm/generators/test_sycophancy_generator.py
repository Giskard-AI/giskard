import json
from unittest.mock import Mock

from giskard.datasets.base import Dataset
from giskard.llm.client import ChatMessage
from giskard.llm.generators.sycophancy import SycophancyDataGenerator


def test_generator_returns_dataset():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content=json.dumps(
                {
                    "inputs": [
                        {
                            "input_1": {"question": "What is the meaning of life?", "other_feature": "test 1"},
                            "input_2": {"question": "What is life?", "other_feature": "test 2"},
                        },
                        {
                            "input_1": {
                                "question": "What is the airspeed velocity of an European swallow?",
                                "other_feature": "test 1",
                            },
                            "input_2": {
                                "question": "What is the airspeed velocity of an African swallow?",
                                "other_feature": "test 2",
                            },
                        },
                    ]
                }
            ),
        )
    ] * 2

    model = Mock()
    model.feature_names = ["question", "other_feature"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"

    generator = SycophancyDataGenerator(
        llm_client=llm_client,
        llm_temperature=1.416,
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

    called_prompt = call_args.kwargs["messages"][-1].content
    called_temperature = call_args.kwargs["temperature"]

    assert "This is a model for testing purposes" in called_prompt
    assert "### NUM EXAMPLES\n2" in called_prompt
    assert called_temperature == 1.416
