from unittest.mock import Mock

from giskard.llm.client import LLMFunctionCall, LLMOutput
from giskard.llm.evaluators import RequirementEvaluator
from tests.llm.evaluators.utils import make_eval_dataset, make_mock_model


def test_evaluator_prompt_contains_requirements():
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

    evaluator = RequirementEvaluator(["This is my test requirement"], llm_client=client)
    evaluator.evaluate(model, eval_dataset)

    args = client.complete.call_args_list[0]
    assert "This is my test requirement" in args[0][0][0]["content"]
