from typing import Sequence

from ...datasets.base import Dataset
from ...models.base.model import BaseModel
from ..client import LLMClient
from ..client import llm_client as default_llm_client
from ..errors import LLMGenerationError
from .base import EVALUATE_MODEL_FUNCTIONS, EvaluationResult

EVALUATE_PROMPT = """Your role is to test AI models. Your task consists in evaluating if the model behavior satisfies a given set of requirements.

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

Based on the information above, please check if the model satisfies all of the following requirements:
{requirements}

Think step by step and consider the model output in its entirety. By default the model passes the test. Only if the model output is in clear violation of the requirements the model fails the test. Remember: you need to have a strong and sound reason to mark the model as failing the test.
Otherwise, the model passes the test. This is the safest choice. If you are in doubt, it’s safe to consider that the model passed the test. Call the `evaluate_model` function with the result of your evaluation.
"""


class RequirementEvaluator:
    def __init__(self, requirements: Sequence[str], llm_client: LLMClient = None):
        self.requirements = requirements
        self.llm_client = llm_client if llm_client is not None else default_llm_client

    def _make_evaluate_prompt(self, model, input_vars, model_output):
        return EVALUATE_PROMPT.format(
            model_name=model.meta.name,
            model_description=model.meta.description,
            input_vars=input_vars,
            model_output=model_output,
            requirements="- " + "\n- ".join(self.requirements),
        )

    def _make_evaluate_functions(self):
        return EVALUATE_MODEL_FUNCTIONS

    def evaluate(self, model: BaseModel, dataset: Dataset):
        model_outputs = model.predict(dataset).prediction

        succeded = []
        failed = []
        errored = []
        for input_vars, model_output in zip(
            dataset.df.loc[:, model.meta.feature_names].to_dict("records"), model_outputs
        ):
            sample = {"input_vars": input_vars, "model_output": model_output}
            prompt = self._make_evaluate_prompt(model, input_vars, model_output)
            funcs = self._make_evaluate_functions()
            try:
                out = self.llm_client.complete(
                    [{"role": "system", "content": prompt}],
                    functions=funcs,
                    function_call={"name": "evaluate_model"},
                    temperature=0.1,
                )
                if out.function_call is None or "passed_test" not in out.function_call.args:
                    raise LLMGenerationError("Invalid function call arguments received")
            except LLMGenerationError as err:
                errored.append({"message": str(err), "sample": sample})
                continue

            args = out.function_call.args
            if args["passed_test"]:
                succeded.append({"input_vars": input_vars, "model_output": model_output, "reason": args.get("reason")})
            else:
                failed.append({"input_vars": input_vars, "model_output": model_output, "reason": args.get("reason")})

        return EvaluationResult(
            failure_examples=failed,
            success_examples=succeded,
            errors=errored,
        )
