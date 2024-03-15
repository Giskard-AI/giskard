from unittest.mock import Mock

import pandas as pd
import pytest

from giskard.datasets.base import Dataset
from giskard.llm.client import ChatMessage
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
    model.feature_names = feature_names if feature_names else ["question"]
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
            content='{"eval_passed": true, "reason": ""}',
        ),
        ChatMessage(
            role="assistant",
            content='{"eval_passed": false, "reason": "The model output does not agree with the ground truth: Rome is the capital of Italy"}',
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

    conv = result.failure_examples[0]["sample"]["conversation"]
    assert conv[0]["content"] == "What is the capital of Italy?"
    assert conv[1]["content"] == "The capital of Italy is Paris"

    assert result.failure_examples[0]["sample"]["meta"]["reference_answer"] == "Rome is the capital of Italy"
    assert (
        result.failure_examples[0]["sample"]["meta"]["reference_context"]
        == "Italy covers an area of 301,340 km2 is the third-most populous member state of the European Union. Its capital and largest city is Rome."
    )


def test_correctness_evaluator_handles_generation_errors():
    dataset = _make_eval_dataset()
    model = _make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='{"eval_passed": true}',
        ),
        ChatMessage(
            role="assistant",
            content='BREAK JSON{"eval_passed": false, "reason": "The model output does not agree with the ground truth: Rome is the capital of Italy"}',
        ),
    ]

    evaluator = CorrectnessEvaluator(llm_client=client)

    result = evaluator.evaluate(model, dataset)
    result.failure_examples
    assert len(result.success_examples) == 1
    assert len(result.errors) == 1

    assert result.errors[0]["error"] == "Could not parse evaluator output"


def test_raises_error_if_missing_column_in_dataset():
    dataset = _make_eval_dataset()
    dataset.df = dataset.df.drop("reference_answer", axis=1)

    model = _make_mock_model()

    evaluator = CorrectnessEvaluator(llm_client=Mock())
    with pytest.raises(ValueError, match="Could not find reference answer"):
        evaluator.evaluate(model, dataset)
