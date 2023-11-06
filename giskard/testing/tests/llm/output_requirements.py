import json

import pandas as pd

from ....datasets.base import Dataset
from ....llm.evaluators import RequirementEvaluator
from ....ml_worker.testing.registry.decorators import test
from ....ml_worker.testing.test_result import TestMessage, TestMessageLevel, TestResult
from ....models.base import BaseModel
from ....utils.display import truncate
from .. import debug_description_prefix


def _test_output_against_requirement(model: BaseModel, dataset: Dataset, requirement: str, debug: bool = False):
    evaluator = RequirementEvaluator([requirement])
    eval_result = evaluator.evaluate(model, dataset)

    output_ds = None

    if eval_result.failed and debug:
        df = pd.DataFrame([ex["input_vars"] for ex in eval_result.failure_examples])
        output_ds = Dataset(
            df,
            name=truncate(f'Failing examples for requirement "{requirement}"'),
            column_types=dataset.column_types,
            validation=False,
        )

    messages = []
    if eval_result.has_errors:
        messages = [TestMessage(TestMessageLevel.ERROR, err["message"]) for err in eval_result.errors]

    return TestResult(
        passed=eval_result.passed,
        output_df=output_ds,
        metric=len(eval_result.failure_examples),
        metric_name="Failing examples",
        is_error=eval_result.has_errors,
        messages=messages,
    )


@test(
    name="Evaluation of model output using an LLM (LLM-as-a-judge)",
    tags=["llm", "llm-as-a-judge"],
    debug_description=debug_description_prefix + "that are <b>failing the evaluation criteria</b>.",
)
def test_llm_output_against_requirement(model: BaseModel, dataset: Dataset, requirement: str, debug: bool = False):
    """Evaluates the model output against a given requirement with another LLM (LLM-as-a-judge).

    The model outputs over a given dataset will be validated against the specified requirement using GPT-4 (note that
    this requires you to set the `OPENAI_API_TOKEN` environment variable for the test to run correctly).

    Parameters
    ----------
    model : BaseModel
        The generative model to test.
    dataset : Dataset
        A dataset of examples which will be provided as inputs to the model.
    requirement : str
        The requirement to evaluate the model output against. This should be a clear and explicit requirement that can
        be interpreted by the LLM, for example: “The model should decline to answer”, “The model should not generate
        content that incites harm or violence”, or “The model should apologize and explain that it cannot answer
        questions unrelated to its scope”.
    debug : bool, optional
        If True and the test fails, a dataset containing the rows that have failed the evaluation criteria will be
        included in the test result.

    Returns
    -------
    TestResult
        A TestResult object containing the test result.
    """
    return _test_output_against_requirement(model, dataset, requirement, debug)


@test(
    name="Evaluation of model output for a single example using an LLM (LLM-as-a-judge)",
    tags=["llm", "llm-as-a-judge"],
    debug_description=debug_description_prefix + "that are <b>failing the evaluation criteria</b>.",
)
def test_llm_single_output_against_requirement(
    model: BaseModel, input_var: str, requirement: str, input_as_json: bool = False, debug: bool = False
):
    """Evaluates the model output against a given requirement with another LLM (LLM-as-a-judge).

    The model outputs over a given dataset will be validated against the specified requirement using GPT-4 (note that
    this requires you to set the `OPENAI_API_TOKEN` environment variable for the test to run correctly).

    Parameters
    ----------
    model : BaseModel
        The generative model to test.
    input_var : str
        The input to provide to the model. If your model has a single input variable, this will be used as its value.
        For example, if your model has a single input variable called `question`, you can set `input_var` to the
        question you want to ask the model, `question = "What is the capital of France?"`.
        If need to pass multiple input variables to the model, set `input_as_json` to `True` and specify `input_var` as
        a JSON encoded object. For example:
        ```
        input_var = '{"question": "What is the capital of France?", "language": "English"}'
        ```
    requirement : str
        The requirement to evaluate the model output against. This should be a clear and explicit requirement that can
        be interpreted by the LLM, for example: “The model should decline to answer”, “The model should not generate
        content that incites harm or violence”.
    input_as_json : bool, optional
        If True, `input_var` will be parsed as a JSON encoded object. Default is False.
    debug : bool, optional
        If True and the test fails, a dataset containing the rows that have failed the evaluation criteria will be
        included in the test result.

    Returns
    -------
    TestResult
        A TestResult object containing the test result.
    """
    # Create the single-entry dataset
    if input_as_json:
        input_sample = json.loads(input_var)
    else:
        input_sample = {model.meta.feature_names[0]: input_var}

    dataset = Dataset(
        pd.DataFrame([input_sample]),
        name=truncate(f'Single entry dataset for "{requirement}"'),
        column_types={k: "text" for k in input_sample.keys()},
    )

    # Run normal output requirement test
    return _test_output_against_requirement(model, dataset, requirement, debug)
