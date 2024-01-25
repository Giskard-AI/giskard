from unittest.mock import Mock

import pandas as pd
import pytest

from giskard.datasets.base import Dataset
from giskard.llm.client import LLMFunctionCall, LLMMessage, LLMToolCall
from giskard.llm.evaluators.coherency import CoherencyEvaluator
from giskard.models.base.model_prediction import ModelPredictionResults


def _make_eval_datasets():
    ds1 = Dataset(
        pd.DataFrame({"question": ["What is the capital of France?", "Quo vadis?"], "other": ["test 1", "test 2"]})
    )
    ds2 = Dataset(
        pd.DataFrame(
            {
                "question": ["Why is Madrid the capital of France?", "Eo Romam, quo vadis?"],
                "other": ["test 1", "test 2"],
            }
        )
    )
    return ds1, ds2


def _make_mock_model():
    model = Mock()
    model.predict.return_value = ModelPredictionResults(prediction=["Paris", "Eo Romam"])
    model.feature_names = ["question", "other"]
    model.name = "Mock model for test"
    model.description = "This is a model for testing purposes"
    return model


def test_requirements_evaluator_correctly_flags_examples():
    dataset1, dataset2 = _make_eval_datasets()
    model = _make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        LLMMessage(
            role="assistant",
            content=None,
            function_call=None,
            tool_calls=[
                LLMToolCall(
                    id="call_abc123",
                    type="function",
                    function=LLMFunctionCall(
                        name="evaluate_model",
                        arguments={"passed_test": False, "reason": "Model output is not coherent"},
                    ),
                )
            ],
        ),
        LLMMessage(
            role="assistant",
            content=None,
            function_call=None,
            tool_calls=[
                LLMToolCall(
                    id="call_abc123",
                    type="function",
                    function=LLMFunctionCall(
                        name="evaluate_model",
                        arguments={
                            "passed_test": True,
                        },
                    ),
                )
            ],
        ),
    ]

    evaluator = CoherencyEvaluator(llm_client=client)

    result = evaluator.evaluate(model, dataset1, dataset2)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 1

    assert result.failure_examples[0]["reason"] == "Model output is not coherent"
    assert result.failure_examples[0]["input_1"] == {"question": "What is the capital of France?", "other": "test 1"}
    assert result.failure_examples[0]["input_2"] == {
        "question": "Why is Madrid the capital of France?",
        "other": "test 1",
    }
    assert result.failure_examples[0]["output_1"] == "Paris"

    # Check LLM client calls arguments
    args = client.complete.call_args_list[0]
    assert "This is a model for testing purposes" in args[0][0][0]["content"]
    assert args[1]["tools"][0]["function"]["name"] == "evaluate_model"


def test_requirements_evaluator_handles_generation_errors():
    dataset1, dataset2 = _make_eval_datasets()
    model = _make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        LLMMessage(
            role="assistant",
            content=None,
            function_call=None,
            tool_calls=[
                LLMToolCall(
                    id="call_abc123",
                    type="function",
                    function=LLMFunctionCall(
                        name="evaluate_model",
                        arguments={
                            "passed_test": True,
                        },
                    ),
                )
            ],
        ),
        LLMMessage(
            role="assistant",
            content=None,
            function_call=None,
            tool_calls=[
                LLMToolCall(
                    id="call_abc123",
                    type="function",
                    function=LLMFunctionCall(
                        name="evaluate_model",
                        arguments={"model_did_pass_the_test": False},
                    ),
                )
            ],
        ),
    ]

    evaluator = CoherencyEvaluator(llm_client=client)

    result = evaluator.evaluate(model, dataset1, dataset2)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 0
    assert len(result.errors) == 1
    assert result.errors[0]["message"] == "Invalid function call arguments received"


def test_raises_error_if_datasets_have_different_length():
    dataset1, dataset2 = _make_eval_datasets()
    dataset2.df.drop(dataset2.df.index[0], inplace=True)
    model = _make_mock_model()

    evaluator = CoherencyEvaluator(llm_client=Mock())
    with pytest.raises(ValueError, match="Datasets must have the same index"):
        evaluator.evaluate(model, dataset1, dataset2)
