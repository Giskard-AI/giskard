from unittest.mock import MagicMock, patch

import pandas as pd

from giskard import Dataset
from giskard.core.core import ModelMeta, SupportedModelTypes
from giskard.core.test_result import TestResultStatus
from giskard.llm.evaluators.base import EvaluationResult, EvaluationResultExample
from giskard.models.base.model import BaseModel
from giskard.testing.tests import llm as llm_tests


def _mock_evaluation_result_error():
    return EvaluationResult(
        results=[
            EvaluationResultExample(status=TestResultStatus.ERROR, sample=dict(), reason="Something went wrong!"),
            EvaluationResultExample(
                status=TestResultStatus.PASSED,
                sample={
                    "conversation": [
                        {
                            "role": "user",
                            "content": {"feature": "value"},
                        },
                        {
                            "role": "agent",
                            "content": "demo",
                        },
                    ]
                },
                reason="This is a test",
            ),
        ]
    )


def _mock_evaluation_result(status: TestResultStatus, examples=2):
    return EvaluationResult(
        results=[
            EvaluationResultExample(
                status=status,
                sample={
                    "conversation": [
                        {
                            "role": "user",
                            "content": {"feature": "value"},
                        },
                        {
                            "role": "agent",
                            "content": "demo",
                        },
                    ]
                },
                reason="This is a test",
            ),
            EvaluationResultExample(
                status=status,
                sample={
                    "conversation": [
                        {
                            "role": "user",
                            "content": {"feature": "value2"},
                        },
                        {
                            "role": "agent",
                            "content": "demo2",
                        },
                    ]
                },
                reason="This is another test",
            ),
        ][:examples]
    )


@patch("giskard.testing.tests.llm.output_requirements.RequirementEvaluator")
def test_llm_output_requirement(RequirementEvaluator):
    model = MagicMock(BaseModel)
    dataset = Dataset(pd.DataFrame({"feature": ["value"]}))

    # Successful test
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result(TestResultStatus.PASSED)

    my_test = llm_tests.test_llm_output_against_requirement(
        model=model,
        dataset=dataset,
        requirement="The model should not generate content that incites harm or violence",
    )
    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.output_df is None

    RequirementEvaluator.assert_called_once_with(
        ["The model should not generate content that incites harm or violence"], llm_seed=1729
    )
    RequirementEvaluator.return_value.evaluate.assert_called_once_with(model, dataset)

    # Failed test
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result(TestResultStatus.FAILED)

    res = my_test.execute()
    assert not res.passed
    assert res.metric == 2
    assert res.metric_name == "Failing examples"

    # Errored tests
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result_error()
    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.messages[0].text == "Something went wrong!"
    assert res.is_error


@patch("giskard.testing.tests.llm.output_requirements.RequirementEvaluator")
def test_llm_single_output_requirement(RequirementEvaluator):
    model = MagicMock(BaseModel)
    model.meta = ModelMeta(
        name=None,
        description=None,
        model_type=SupportedModelTypes.TEXT_GENERATION,
        feature_names=["question"],
        classification_labels=[],
        classification_threshold=[],
        loader_class="",
        loader_module="",
    )
    input_var = "My demo question??"

    # Successful test
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result(TestResultStatus.PASSED, 1)
    my_test = llm_tests.test_llm_single_output_against_requirement(
        model=model,
        input_var=input_var,
        requirement="The model should not generate content that incites harm or violence",
        debug=True,
    )
    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.output_df is None

    RequirementEvaluator.assert_called_once_with(
        ["The model should not generate content that incites harm or violence"], llm_seed=1729
    )
    RequirementEvaluator.return_value.evaluate.assert_called_once()
    assert RequirementEvaluator.return_value.evaluate.call_args[0][0] == model
    arg2 = RequirementEvaluator.return_value.evaluate.call_args[0][1]
    assert isinstance(arg2, Dataset)
    assert len(arg2) == 1
    assert arg2.df.iloc[0].question == "My demo question??"

    # Failed test
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result(TestResultStatus.FAILED, 1)

    res = my_test.execute()
    assert not res.passed
    assert res.metric == 1
    assert res.metric_name == "Failing examples"

    # Errored tests
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result_error()

    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.messages[0].text == "Something went wrong!"
    assert res.is_error


@patch("giskard.testing.tests.llm.output_requirements.RequirementEvaluator")
def test_llm_output_requirement_per_row(RequirementEvaluator):
    model = MagicMock(BaseModel)
    dataset = Dataset(
        pd.DataFrame(
            {
                "feature": ["value"],
                "requirement": ["The model should not generate content that incites harm or violence"],
            }
        )
    )

    # Successful test
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result(TestResultStatus.PASSED)

    my_test = llm_tests.test_llm_output_against_requirement_per_row(
        model=model, dataset=dataset, requirement_column="requirement", rng_seed=1
    )
    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.output_df is None

    RequirementEvaluator.assert_called_once()

    assert RequirementEvaluator.call_args.kwargs["requirement_col"] == "requirement"
    assert RequirementEvaluator.call_args.kwargs["llm_seed"] == 1

    # Failed test
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result(TestResultStatus.FAILED)

    res = my_test.execute()
    assert not res.passed
    assert res.metric == 2
    assert res.metric_name == "Failing examples"

    # Errored tests
    RequirementEvaluator.return_value.evaluate.return_value = _mock_evaluation_result_error()

    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.messages[0].text == "Something went wrong!"
    assert res.is_error
