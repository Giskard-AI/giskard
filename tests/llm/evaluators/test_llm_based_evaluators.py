from unittest.mock import Mock

import pandas as pd
import pytest

from giskard.core.test_result import TestResultStatus
from giskard.llm.client import LLMFunctionCall, LLMMessage, LLMToolCall
from giskard.llm.evaluators.base import LLMBasedEvaluator
from giskard.llm.evaluators.plausibility import PlausibilityEvaluator
from giskard.llm.evaluators.requirements import PerRowRequirementEvaluator, RequirementEvaluator
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
        (
            PerRowRequirementEvaluator,
            [pd.DataFrame({"req": ["This is the first test requirement", "This is the second test requirement"]})],
            {},
        ),
        (PlausibilityEvaluator, [], {}),
    ],
)
def test_evaluator_correctly_flags_examples(Evaluator, args, kwargs):
    eval_dataset = make_eval_dataset()
    model = make_mock_model()

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
                        arguments={"passed_test": True},
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
                        name="evaluate_model", arguments={"passed_test": False, "reason": "For some reason"}
                    ),
                )
            ],
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
    assert args[1]["tools"][0]["function"]["name"] == "evaluate_model"

    assert result.details.inputs == eval_dataset.df.loc[:, model.feature_names].to_dict("list")
    assert result.details.outputs == model.predict(eval_dataset).prediction
    assert result.details.results == [TestResultStatus.PASSED, TestResultStatus.FAILED]
    assert result.details.metadata == {"reason": [None, "For some reason"]}


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
                        arguments={"passed_test": True},
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

    evaluator = Evaluator(*args, **kwargs, llm_client=client)

    result = evaluator.evaluate(model, eval_dataset)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 0
    assert len(result.errors) == 1
    assert result.errors[0]["message"] == "Invalid function call arguments received"

    assert result.details.inputs == eval_dataset.df.loc[:, model.feature_names].to_dict("list")
    assert result.details.outputs == model.predict(eval_dataset).prediction
    assert result.details.results == [TestResultStatus.PASSED, TestResultStatus.ERROR]
    assert result.details.metadata == {"reason": [None, "Invalid function call arguments received"]}
