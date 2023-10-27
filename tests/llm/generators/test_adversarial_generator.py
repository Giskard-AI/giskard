from unittest.mock import Mock

from giskard.llm.client import LLMFunctionCall, LLMOutput
from giskard.llm.generators.adversarial import AdversarialExamplesGenerator


def test_generator_formats_prompt_with_issue_desc_and_requirement():
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
    model.meta.feature_names = ["question", "other_feature"]
    model.meta.name = "Mock model for test"
    model.meta.description = "This is a model for testing purposes"

    generator = AdversarialExamplesGenerator(
        "This is an issue description",
        "This is a requirement",
        llm_client=llm_client,
        prompt="My custom prompt {model_name} {model_description} {feature_names}, with {num_samples} samples {issue_description} {requirement}",
    )

    generator.generate_dataset(model, num_samples=2)

    llm_client.complete.assert_called_once()

    called_prompt = llm_client.complete.call_args[1]["messages"][0]["content"]

    assert (
        called_prompt
        == "My custom prompt Mock model for test This is a model for testing purposes question, other_feature, with 2 samples This is an issue description This is a requirement"
    )
