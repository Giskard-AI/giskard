from unittest.mock import MagicMock, patch

import pandas as pd

from giskard import Dataset
from giskard.core.core import ModelMeta, SupportedModelTypes
from giskard.llm.evaluators.base import EvaluationResult
from giskard.models.base.model import BaseModel
from giskard.testing.tests import llm as llm_tests

_demo_samples = [
    {"input_vars": {"feature": "value"}, "model_output": "demo", "reason": "This is a test"},
    {"input_vars": {"feature": "value2"}, "model_output": "demo2", "reason": "This is another test"},
]


@patch("giskard.testing.tests.llm.output_requirements.RequirementEvaluator")
def test_llm_output_requirement(RequirementEvaluator):
    model = MagicMock(BaseModel)
    dataset = Dataset(pd.DataFrame({"feature": ["value"]}))

    # Successful test
    RequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        output_ds=dataset.slice(lambda df: df.iloc[[]], row_level=False),
        failure_examples=[],
        success_examples=_demo_samples,
        errors=[],
    )

    my_test = llm_tests.test_llm_output_against_requirement(
        model=model,
        dataset=dataset,
        requirement="The model should not generate content that incites harm or violence",
    )
    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.output_df is None
    assert len(res.output_ds) == 1
    assert len(res.output_ds[0].df) == 0

    RequirementEvaluator.assert_called_once_with(
        ["The model should not generate content that incites harm or violence"]
    )
    RequirementEvaluator.return_value.evaluate.assert_called_once_with(model, dataset)

    # Failed test
    RequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        output_ds=dataset.slice(lambda df: df, row_level=False),
        failure_examples=_demo_samples,
        success_examples=[],
        errors=[],
    )
    res = my_test.execute()
    assert not res.passed
    assert res.metric == 2
    assert res.metric_name == "Failing examples"
    assert len(res.output_ds) == 1
    assert len(res.output_ds[0].df) == len(dataset.df)

    # Errored tests
    RequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        output_ds=dataset.slice(lambda df: df.iloc[[]], row_level=False),
        failure_examples=[],
        success_examples=_demo_samples,
        errors=[{"message": "Something went wrong!", "sample": dict()}],
    )
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
    demo_sample = _demo_samples[:1]

    # Successful test
    RequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        failure_examples=[], success_examples=demo_sample, errors=[], output_ds=Dataset(pd.DataFrame({"feature": []}))
    )

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
        ["The model should not generate content that incites harm or violence"]
    )
    RequirementEvaluator.return_value.evaluate.assert_called_once()
    assert RequirementEvaluator.return_value.evaluate.call_args[0][0] == model
    arg2 = RequirementEvaluator.return_value.evaluate.call_args[0][1]
    assert isinstance(arg2, Dataset)
    assert len(arg2) == 1
    assert arg2.df.iloc[0].question == "My demo question??"

    # Failed test
    RequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        output_ds=Dataset(pd.DataFrame({"feature": ["value"]})),
        failure_examples=demo_sample,
        success_examples=[],
        errors=[],
    )
    res = my_test.execute()
    assert not res.passed
    assert res.metric == 1
    assert res.metric_name == "Failing examples"
    assert isinstance(res.output_df, Dataset)

    # Errored tests
    RequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        output_ds=Dataset(pd.DataFrame({"feature": []})),
        failure_examples=[],
        success_examples=demo_sample,
        errors=[{"message": "Something went wrong!", "sample": dict()}],
    )
    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.messages[0].text == "Something went wrong!"
    assert res.is_error


@patch("giskard.testing.tests.llm.output_requirements.PerRowRequirementEvaluator")
def test_llm_output_requirement_per_row(PerRowRequirementEvaluator):
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
    PerRowRequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        output_ds=dataset.slice(lambda df: df.iloc[[]], row_level=False),
        failure_examples=[],
        success_examples=_demo_samples,
        errors=[],
    )

    my_test = llm_tests.test_llm_output_against_requirement_per_row(
        model=model,
        dataset=dataset,
        requirement_column="requirement",
    )
    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.output_df is None

    PerRowRequirementEvaluator.assert_called_once_with("requirement")
    PerRowRequirementEvaluator.return_value.evaluate.assert_called_once_with(model, dataset)

    # Failed test
    PerRowRequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        output_ds=dataset.slice(lambda df: df.iloc[dataset.df.index], row_level=False),
        failure_examples=_demo_samples,
        success_examples=[],
        errors=[],
    )
    res = my_test.execute()
    assert not res.passed
    assert res.metric == 2
    assert res.metric_name == "Failing examples"
    assert len(res.output_ds) == 1
    assert isinstance(res.output_ds[0], Dataset)

    # Errored tests
    PerRowRequirementEvaluator.return_value.evaluate.return_value = EvaluationResult(
        output_ds=dataset.slice(lambda df: df.iloc[[]], row_level=False),
        failure_examples=[],
        success_examples=_demo_samples,
        errors=[{"message": "Something went wrong!", "sample": dict()}],
    )
    res = my_test.execute()
    assert res.passed
    assert res.metric == 0
    assert res.messages[0].text == "Something went wrong!"
    assert res.is_error
