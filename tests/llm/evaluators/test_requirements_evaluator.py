from unittest.mock import Mock

import pandas as pd

from giskard.datasets.base import Dataset
from giskard.llm.client import LLMFunctionCall, LLMOutput
from giskard.llm.evaluators.requirements import RequirementEvaluator
from giskard.models.base.model_prediction import ModelPredictionResults


def _make_eval_dataset():
    return Dataset(pd.DataFrame({"question": ["How are you?", "Who are you?"], "other": ["ok", "ok"]}))


def _make_mock_model():
    model = Mock()
    model.predict.return_value = ModelPredictionResults(prediction=["good", "bad"])
    model.meta.feature_names = ["question", "other"]
    model.meta.name = "Mock model for test"
    model.meta.description = "This is a model for testing purposes"
    return model


def test_requirements_evaluator_correctly_flags_examples():
    eval_dataset = _make_eval_dataset()
    model = _make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        LLMOutput(
            function_call=LLMFunctionCall(
                function="evaluate_model",
                args={"passed_test": True},
            )
        ),
        LLMOutput(
            function_call=LLMFunctionCall(
                function="evaluate_model",
                args={"passed_test": False, "reason": "The model must always answer 'good'"},
            )
        ),
    ]

    evaluator = RequirementEvaluator(
        ["The model must always answer 'good'", "The model must be kind"], llm_client=client
    )

    result = evaluator.evaluate(model, eval_dataset)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 1

    assert result.failure_examples[0]["reason"] == "The model must always answer 'good'"
    assert result.failure_examples[0]["input_vars"] == {"question": "Who are you?", "other": "ok"}
    assert result.failure_examples[0]["model_output"] == "bad"

    # Check LLM client calls arguments
    args = client.complete.call_args_list[0]
    assert "This is a model for testing purposes" in args[0][0][0]["content"]
    assert args[1]["functions"][0]["name"] == "evaluate_model"


def test_requirements_evaluator_handles_generation_errors():
    eval_dataset = _make_eval_dataset()
    model = _make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        LLMOutput(
            function_call=LLMFunctionCall(
                function="invalid_function",
                args={"passed_test": True},
            )
        ),
        LLMOutput(
            function_call=LLMFunctionCall(
                function="evaluate_model",
                args={"model_did_pass_the_test": False},
            )
        ),
    ]

    evaluator = RequirementEvaluator(
        ["The model must always answer 'good'", "The model must be kind"], llm_client=client
    )

    result = evaluator.evaluate(model, eval_dataset)

    assert len(result.success_examples) == 0
    assert len(result.failure_examples) == 0
    assert len(result.errors) == 2
