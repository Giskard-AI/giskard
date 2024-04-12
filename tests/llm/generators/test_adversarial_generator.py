import json
from unittest.mock import Mock

from giskard.llm.client import ChatMessage
from giskard.llm.generators.adversarial import AdversarialDataGenerator


def test_generator_formats_prompt_with_issue_desc_and_requirement():
    llm_client = Mock()
    llm_client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content=json.dumps(
                {
                    "inputs": [
                        {"question": "What is the meaning of life?", "other_feature": "test"},
                        {
                            "question": "What is the airspeed velocity of an unladen swallow?",
                            "other_feature": "pass",
                        },
                    ]
                }
            ),
        )
    ]

    model = Mock()
    model.feature_names = ["question", "other_feature"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"

    generator = AdversarialDataGenerator(
        "This is a issue description",
        "This is a requirement",
        llm_client=llm_client,
    )

    generator.generate_dataset(model, num_samples=2)

    llm_client.complete.assert_called_once()

    called_prompt = llm_client.complete.call_args[1]["messages"][-1].content

    assert model.description in called_prompt
    assert "This is a issue description" in called_prompt
    assert "This is a requirement" in called_prompt
