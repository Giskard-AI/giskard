from unittest.mock import Mock

from giskard.llm.client import ChatMessage
from giskard.llm.evaluators import RequirementEvaluator
from tests.llm.evaluators.utils import make_eval_dataset, make_mock_model


def test_evaluator_prompt_contains_requirements():
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
            content='{"eval_passed": false, "reason": "For some reason"}',
        ),
    ]

    evaluator = RequirementEvaluator(["This is my test requirement"], llm_client=client)
    evaluator.evaluate(model, eval_dataset)

    args = client.complete.call_args_list[0]
    assert "This is my test requirement" in args[0][0][-1].content


def test_evaluator_prompt_contains_row_requirements():
    reqs = ["This is the first test requirement", "This is the second test requirement"]
    eval_dataset = make_eval_dataset()
    eval_dataset.df["req"] = reqs
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

    evaluator = RequirementEvaluator(requirement_col="req", llm_client=client)
    evaluator.evaluate(model, eval_dataset)

    args = client.complete.call_args_list[0]
    assert reqs[0] in args[0][0][-1].content

    args = client.complete.call_args_list[1]
    assert reqs[1] in args[0][0][-1].content
