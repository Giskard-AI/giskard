import inspect
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ....datasets.base import Dataset
from ....llm.client import get_default_client
from ....llm.errors import LLMGenerationError
from ....llm.evaluators import RequirementEvaluator
from ....ml_worker.testing.registry.decorators import test
from ....ml_worker.testing.test_result import TestMessage, TestMessageLevel, TestResult
from ....models.base import BaseModel
from .. import debug_description_prefix, debug_prefix


class EvalTestResult(PydanticBaseModel):
    score: int = Field(
        description="A number ranging from 1 to 5: 1 indicates that the answer does not meet the criteria at all, 3 indicates that the answer can be improved, 5 indicates that the answer completely meets the criteria"
    )
    reason: str = Field(description="A text that clearly explains the given score")
    tip: Optional[str] = Field(
        description="A text that offers a clear and descriptive suggestion on how to enhance the model", default=None
    )


EVALUATE_PROMPT = """You are auditing an AI model. Your task is to evaluate the model based on given requirements.

You are auding the following model:

Model name: {model_name}
Model description: {model_description}

Here is the input that was provided to the model and its output:

PROVIDED INPUT:
###
{input_vars}
###

MODEL OUTPUT:
###
{model_output}
###

Based on the information above, please check that the model behaviour satisfies all of the following requirements:
- {requirements}

Your decision must be only based on the listed requirements.

If the model satisfies the requirements, it passes the evaluation test. On the contrary, if the model output does not satisfy the requirements, the model fails the test.
Call the `evaluate_model` function with the result of your evaluation.
If the model does not pass the test, also provide a brief reason as an argument to the `evaluate_model`.
If you are not sure, just answer 'I don’t know'.
"""

EVALUATE_FUNCTIONS = [
    {
        "name": "evaluate_model",
        "description": "Evaluates if the model passes the test",
        "parameters": {
            "type": "object",
            "properties": {
                "passed_test": {
                    "type": "boolean",
                    "description": "true if the model successfully passes the test",
                },
                "reason": {
                    "type": "string",
                    "description": "optional short description of why the model does not pass the test, in 1 or 2 short sentences",
                },
            },
        },
        "required": ["passed_test"],
    }
]


def validate_test_case_with_reason(
    model: BaseModel, test_case: str, df, predictions: List[str]
) -> List[EvalTestResult]:
    llm_client = get_default_client()
    inputs = [
        {
            "input_vars": df.iloc[i].to_dict(),
            "requirements": test_case,
            "model_output": predictions[i],
            "model_name": model.meta.name,
            "model_description": model.meta.description,
        }
        for i in range(len(predictions))
    ]
    results = []
    for data in inputs:
        prompt = EVALUATE_PROMPT.format(
            model_name=model.meta.name,
            model_description=model.meta.description,
            input_vars=data["input_vars"],
            model_output=data["model_output"],
            requirements=data["requirements"],
        )
        try:
            out = llm_client.complete(
                messages=[{"role": "system", "content": prompt}], functions=EVALUATE_FUNCTIONS, temperature=0.1
            )

            if out.function_call is None or "passed_test" not in out.function_call.args:
                raise LLMGenerationError("Could not parse the function call")
        except LLMGenerationError:
            results.append(EvalTestResult(score=5, reason=""))

        if out.function_call.args["passed_test"]:
            results.append(EvalTestResult(score=5, reason="The answer is correct"))
        else:
            results.append(EvalTestResult(score=0, reason=out.function_call.args.get("reason")))

    return results


@test(
    name="Validate LLM evaluation dataset using GPT-4",
    tags=["llm", "GPT-4"],
    debug_description=debug_description_prefix + "that are <b>failing the evaluation criteria</b>.",
)
def test_llm_response_validation(
    model: BaseModel, dataset: Dataset, evaluation_criteria: str, threshold: float = 0.5, debug: bool = False
):
    """Tests that the rate of generated response is over a threshold for a given test case.

    The generated response will be validated using GPT-4
    using the OPENAI_API_TOKEN stored inside the environment variable.

    Arguments:
        model(BaseModel): The generative model to test.
        dataset(Dataset): The dataset to test the model on.
        evaluation_criteria(str): The test case used to evaluate the response generated by the model
            must be explicit and clear in order to be interpreted properly
            Good assertions
              - The model response must be a JSON valid that respect the following schema
              - The model response must be an apologies with an explanation of the model scope if the question is out of scope (not related to the Pandas Python library)
            Bad assertion
              - A valid json answer
              - Answer to pandas documentation
        threshold(float, optional): The threshold for good response rate, i.e. the min ratio of responses that pass the assertion. Default is 0.50 (50%).
        debug(bool):
            If True and the test fails,
            a dataset will be provided containing the rows that have failed the evaluation criteria
    """
    predictions = model.predict(dataset).prediction

    results = validate_test_case_with_reason(model, evaluation_criteria, dataset.df, predictions)
    passed_tests = [res.score >= 3 for res in results]
    metric = len([result for result in passed_tests if result]) / len(predictions)
    passed = bool(metric >= threshold)

    # --- debug ---
    output_ds = None
    if not passed and debug:
        output_ds = dataset.copy()
        output_ds.df = dataset.df.loc[[not test_passed for test_passed in passed_tests]]
        test_name = inspect.stack()[0][3]
        output_ds.name = debug_prefix + test_name
    # ---

    return TestResult(
        actual_slices_size=[len(dataset)],
        metric=metric,
        passed=passed,
        messages=[
            TestMessage(
                type=TestMessageLevel.INFO,
                text=f"""
Prompt intput: {dataset.df.iloc[i].to_dict()}
                
LLM response: {predictions[i]}
                
Score: {results[i].score}/5
                
Reason: {results[i].reason}
                """,
            )
            for i in range(min(len(predictions), 3))
        ],
        output_df=output_ds,
    )


@test(name="Validate LLM single prompt input using GPT-4", tags=["llm", "GPT-4"])
def test_llm_individual_response_validation(
    model: BaseModel, prompt_input: str, evaluation_criteria: str, debug: bool = False
):
    """Tests that the rate of generated response is over a threshold for a given test case.

    The generated response will be validated using GPT-4
    using the OPENAI_API_TOKEN stored inside the environment variable.

    Arguments:
        model(BaseModel): The generative model to test.
        prompt_input(str): The prompt input to test the model on.
        evaluation_criteria(str): The test case used to evaluate the response generated by the model
            must be explicit and clear in order to be interpreted properly
            Good assertions
              - The model response must be a JSON valid that respect the following schema
              - The model response must be an apologies with an explanation of the model scope if the question is out of scope (not related to the Pandas Python library)
            Bad assertion
              - A valid json answer
              - Answer to pandas documentation
        debug(bool):
            If True and the test fails,
            a dataset will be provided containing the rows that have failed the evaluation criteria
    """
    if len(model.meta.feature_names) != 1:
        raise ValueError(
            "LLM individual response validation only work for models having single input, please use LLM response validation using"
        )

    dataset = Dataset(
        pd.DataFrame({model.meta.feature_names[0]: [prompt_input]}),
        name=f'Single entry dataset for "{evaluation_criteria}"',
        column_types={model.meta.feature_names[0]: "text"},
    )

    return test_llm_response_validation(model, dataset, evaluation_criteria, 1.0, debug).execute()


@test(
    name="llm_output_requirement",
    tags=["llm"],
    debug_description=debug_description_prefix + "that are <b>failing the evaluation criteria</b>.",
)
def test_llm_output_requirement(model: BaseModel, dataset: Dataset, requirement: str, debug: bool = False):
    evaluator = RequirementEvaluator([requirement])
    eval_result = evaluator.evaluate(model, dataset)

    output_ds = None

    if eval_result.failed:
        df = pd.DataFrame([ex["input_vars"] for ex in eval_result.failure_examples])
        output_ds = Dataset(
            df,
            name="Test dataset for requirement (automatically generated)",
            column_types=dataset.column_types,
            validation=False,
        )

    return TestResult(
        passed=eval_result.passed, output_df=output_ds, metric=len(eval_result.success_examples) / len(dataset)
    )
