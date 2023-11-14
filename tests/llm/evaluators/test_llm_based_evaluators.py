from unittest.mock import Mock

import pytest

from giskard.llm.client import LLMFunctionCall, LLMOutput
from giskard.llm.evaluators.base import LLMBasedEvaluator
from giskard.llm.evaluators.plausibility import PlausibilityEvaluator
from giskard.llm.evaluators.requirements import RequirementEvaluator
from tests.llm.evaluators.utils import make_eval_dataset, make_mock_model


@pytest.mark.parametrize(
    "Evaluator,args,kwargs",
    [
        (
            LLMBasedEvaluator,
            [],
            {"eval_prompt": "Test this: {model_name} {model_description} {input_vars} {model_output}"},
        ),
        (RequirementEvaluator, [["Requirement to fulfill"]], {}),
        (PlausibilityEvaluator, [], {}),
    ],
)
def test_evaluator_correctly_flags_examples(Evaluator, args, kwargs):
    eval_dataset = make_eval_dataset()
    model = make_mock_model()

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
                args={"passed_test": False, "reason": "For some reason"},
            )
        ),
    ]

    evaluator = Evaluator(*args, **kwargs, llm_client=client)
    result = evaluator.evaluate(model, eval_dataset)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 1

    assert result.failure_examples[0]["reason"] == "For some reason"
    assert result.failure_examples[0]["input_vars"] == {
        "question": "What is the airspeed velocity of an unladen swallow?",
        "other": "pass",
    }
    assert result.failure_examples[0]["model_output"] == "What do you mean? An African or European swallow?"

    # Check LLM client calls arguments
    args = client.complete.call_args_list[0]
    assert "This is a model for testing purposes" in args[0][0][0]["content"]
    assert args[1]["functions"][0]["name"] == "evaluate_model"


@pytest.mark.parametrize(
    "Evaluator,args,kwargs",
    [
        (LLMBasedEvaluator, [], {"eval_prompt": "Tell me if the model was any good"}),
        (RequirementEvaluator, [["Requirement to fulfill"]], {}),
        (PlausibilityEvaluator, [], {}),
    ],
)
def test_evaluator_handles_generation_errors(Evaluator, args, kwargs):
    eval_dataset = make_eval_dataset()
    model = make_mock_model()

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
                args={"model_did_pass_the_test": False},
            )
        ),
    ]

    evaluator = Evaluator(*args, **kwargs, llm_client=client)

    result = evaluator.evaluate(model, eval_dataset)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 0
    assert len(result.errors) == 1
    assert result.errors[0]["message"] == "Invalid function call arguments received"
