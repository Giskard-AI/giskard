from unittest.mock import Mock

import pandas as pd
import pytest

from giskard.datasets.base import Dataset
from giskard.llm.client import ChatMessage, LLMFunctionCall
from giskard.llm.client.base import LLMToolCall
from giskard.llm.evaluators.correctness import CorrectnessEvaluator
from giskard.models.base.model_prediction import ModelPredictionResults


def _make_eval_dataset():
    ds = Dataset(
        pd.DataFrame(
            {
                "question": ["What is the capital of France?", "What is the capital of Italy?"],
                "reference_answer": ["Paris is the capital of France", "Rome is the capital of Italy"],
                "reference_context": [
                    "France is a unitary semi-presidential republic with its capital in Paris, the country's largest city and main cultural and commercial centre.",
                    "Italy covers an area of 301,340 km2 is the third-most populous member state of the European Union. Its capital and largest city is Rome.",
                ],
                "question_type": [0, 1],
                "answerable": [True, True],
            }
        )
    )
    return ds


def _make_mock_model(feature_names=None):
    model = Mock()
    model.predict.return_value = ModelPredictionResults(
        prediction=["The capital of France is Paris", "The capital of Italy is Paris"]
    )
    model.feature_names = feature_names if feature_names else ["question", "reference_answer", "reference_context"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"
    return model


def test_correctness_evaluator_correctly_flags_examples():
    dataset = _make_eval_dataset()
    model = _make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            tool_calls=[
                LLMToolCall(
                    id="1",
                    type="function",
                    function=LLMFunctionCall(
                        name="evaluate_model",
                        arguments={"passed_test": True, "reason": ""},
                    ),
                )
            ],
        ),
        ChatMessage(
            role="assistant",
            tool_calls=[
                LLMToolCall(
                    id="2",
                    type="function",
                    function=LLMFunctionCall(
                        name="evaluate_model",
                        arguments={
                            "passed_test": False,
                            "reason": "The model output does not agree with the ground truth: Rome is the capital of Italy",
                        },
                    ),
                )
            ],
        ),
    ]

    evaluator = CorrectnessEvaluator(llm_client=client)

    result = evaluator.evaluate(model, dataset)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 1

    assert (
        result.failure_examples[0]["reason"]
        == "The model output does not agree with the ground truth: Rome is the capital of Italy"
    )
    assert result.failure_examples[0]["question"] == "What is the capital of Italy?"
    assert result.failure_examples[0]["reference_answer"] == "Rome is the capital of Italy"
    assert (
        result.failure_examples[0]["reference_context"]
        == "Italy covers an area of 301,340 km2 is the third-most populous member state of the European Union. Its capital and largest city is Rome."
    )
    assert result.failure_examples[0]["model_output"] == "The capital of Italy is Paris"
    assert not result.failure_examples[0]["model_evaluation"]

    # Check LLM client calls arguments
    args = client.complete.call_args_list[0]
    assert "Your role is to test AI models" in args[0][0][0].content
    assert args[1]["tools"][0]["function"]["name"] == "evaluate_model"


def test_correctness_evaluator_handles_generation_errors():
    dataset = _make_eval_dataset()
    model = _make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            tool_calls=[
                LLMToolCall(
                    id="1",
                    type="function",
                    function=LLMFunctionCall(name="evaluate_model", arguments={"passed_test": True, "reason": ""}),
                )
            ],
        ),
        ChatMessage(
            role="assistant",
            tool_calls=[
                LLMToolCall(
                    id="2",
                    type="function",
                    function=LLMFunctionCall(
                        name="evaluate_model",
                        arguments={
                            "pass": False,
                            "reason": "The model output does not agree with the ground truth: Rome is the capital of Italy",
                        },
                    ),
                )
            ],
        ),
    ]

    evaluator = CorrectnessEvaluator(llm_client=client)

    result = evaluator.evaluate(model, dataset)

    assert len(result.success_examples) == 1
    assert len(result.errors) == 1

    assert result.errors[0]["message"] == "Invalid function call arguments received"


def test_raises_error_if_missing_column_in_dataset():
    dataset = _make_eval_dataset()
    dataset.df = dataset.df.drop("question", axis=1)

    model = _make_mock_model()

    evaluator = CorrectnessEvaluator(llm_client=Mock())
    with pytest.raises(ValueError, match="Missing required columns in the evaluation dataset."):
        evaluator.evaluate(model, dataset)


def test_raises_error_if_missing_feature_in_model():
    dataset = _make_eval_dataset()

    model = _make_mock_model(feature_names=["reference_answer"])

    evaluator = CorrectnessEvaluator(llm_client=Mock())
    with pytest.raises(ValueError, match="Model has no feature 'question'"):
        evaluator.evaluate(model, dataset)
