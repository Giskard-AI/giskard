from unittest.mock import Mock

import pytest

from giskard.llm.client import ChatMessage
from giskard.llm.evaluators.base import LLMBasedEvaluator
from giskard.llm.evaluators.plausibility import PlausibilityEvaluator
from giskard.llm.evaluators.requirements import RequirementEvaluator
from tests.llm.evaluators.utils import make_eval_dataset, make_mock_model


@pytest.mark.parametrize(
    "Evaluator,args,kwargs,additional_metadata",
    [
        (
            LLMBasedEvaluator,
            [],
            {"prompt": "You need to evaluate this model"},
            {},
        ),
        (RequirementEvaluator, [["Requirement to fulfill"]], {}, {}),
        (
            RequirementEvaluator,
            [],
            {"requirement_col": "req"},
            {"req": ["This is the first test requirement", "This is the second test requirement"]},
        ),
        (PlausibilityEvaluator, [], {}, {}),
    ],
)
def test_evaluator_correctly_flags_examples(Evaluator, args, kwargs, additional_metadata):
    eval_dataset = make_eval_dataset()
    eval_dataset.df = eval_dataset.df.assign(**additional_metadata)
    model = make_mock_model()

    client = Mock()
    client.complete.side_effect = [
        ChatMessage(
            role="assistant",
            content='{"eval_passed": true}',
        ),
        ChatMessage(
            role="assistant",
            content='{"eval_passed": false, "reason": "For some reason"}',
        ),
    ]

    evaluator = Evaluator(*args, **kwargs, llm_client=client)
    result = evaluator.evaluate(model, eval_dataset)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 1

    assert result.failure_examples[0]["reason"] == "For some reason"
    assert result.failure_examples[0]["sample"]["conversation"][0]["content"] == {
        "question": "What is the airspeed velocity of an unladen swallow?",
        "other": "pass",
    }
    assert (
        result.failure_examples[0]["sample"]["conversation"][1]["content"]
        == "What do you mean? An African or European swallow?"
    )


@pytest.mark.parametrize(
    "Evaluator,args,kwargs",
    [
        (LLMBasedEvaluator, [], {"prompt": "Tell me if the model was any good"}),
        (RequirementEvaluator, [["Requirement to fulfill"]], {}),
        (PlausibilityEvaluator, [], {}),
    ],
)
def test_evaluator_handles_generation_errors(Evaluator, args, kwargs):
    eval_dataset = make_eval_dataset()
    model = make_mock_model()

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

    evaluator = Evaluator(*args, **kwargs, llm_client=client)

    result = evaluator.evaluate(model, eval_dataset)

    assert len(result.success_examples) == 1
    assert len(result.failure_examples) == 0
    assert len(result.errors) == 1
    assert result.errors[0]["error"] == "Could not parse evaluator output"
