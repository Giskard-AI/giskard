from unittest.mock import Mock

import pandas as pd
import pytest

from giskard.datasets.base import Dataset
from giskard.llm.client import ChatMessage
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
        ChatMessage(
            role="assistant",
            content='{"eval_passed": false, "reason": "Model output is not coherent"}',
        ),
        ChatMessage(
            role="assistant",
            content='{"eval_passed": true}',
        ),
    ]

    evaluator = CoherencyEvaluator(llm_client=client)

    result = evaluator.evaluate(model, dataset1, dataset2)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 1

    assert result.failure_examples[0]["reason"] == "Model output is not coherent"
    result.failure_examples[0]
    assert result.failure_examples[0]["sample"]["conversation_1"][0]["content"] == {
        "question": "What is the capital of France?",
        "other": "test 1",
    }
    assert result.failure_examples[0]["sample"]["conversation_2"][0]["content"] == {
        "question": "Why is Madrid the capital of France?",
        "other": "test 1",
    }
    assert result.failure_examples[0]["sample"]["conversation_1"][1]["content"] == "Paris"


def test_requirements_evaluator_handles_generation_errors():
    dataset1, dataset2 = _make_eval_datasets()
    model = _make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='{"eval_passed": true}',
        ),
        ChatMessage(
            role="assistant",
            content='{"model_did_pass_the_test": false}',
        ),
    ]

    evaluator = CoherencyEvaluator(llm_client=client)

    result = evaluator.evaluate(model, dataset1, dataset2)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 0
    assert len(result.errors) == 1
    assert result.errors[0]["error"] == "Could not parse evaluator output"


def test_raises_error_if_datasets_have_different_length():
    dataset1, dataset2 = _make_eval_datasets()
    dataset2.df.drop(dataset2.df.index[0], inplace=True)
    model = _make_mock_model()

    evaluator = CoherencyEvaluator(llm_client=Mock())
    with pytest.raises(ValueError, match="Datasets must have the same index"):
        evaluator.evaluate(model, dataset1, dataset2)
