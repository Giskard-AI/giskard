import json
from typing import Optional

from ...datasets.base import Dataset
from ...llm.utils import llm_fn_call
from ...models import cache as model_cache
from ...models.base import BaseModel
from ..errors import LLMGenerationError
from .base import EVALUATE_MODEL_FUNCTIONS, EvaluationResult, LLMBasedEvaluator

COHERENCY_EVAL_PROMPT = """You are a QA specialist evaluating an AI model for coherency. Please evaluate if the model provided coherent, consistent answers based on the following input and output pairs.

MODEL: {model_name} - {model_description}.

INPUT 1:
###
{input_1}
###

OUTPUT 1:
###
{output_1}
###

---

INPUT 2:
###
{input_2}
###

OUTPUT 2:
###
{output_2}
###

Decide whether these pairs of input and output are coherent and consistent. Think step by step. Here are some tips:
- note that coherency of the the inputs is not relevant for this test, only the model output consistency and its relationship with the input
- the type of the model can affect your evaluation, for example:
    * if the model is answering questions, it should not contradict itself: thus the outputs must then be coherent
    * if the model is generating content based on the input, for example a summary, then the model outputs may not be consistent but you should check that they are consistent with respect to the input

If the input pairs are coherent and consistent, the model passes the evaluation test.
Call the `evaluate_model` function with the result of your evaluation.
If the model does not pass the test, also provide a brief reason as an argument to the `evaluate_model`.
"""


class CoherencyEvaluator(LLMBasedEvaluator):
    def __init__(self, eval_prompt=None):
        self.eval_prompt = eval_prompt or COHERENCY_EVAL_PROMPT

    def evaluate(self, model: BaseModel, dataset_1: Dataset, dataset_2: Optional[Dataset] = None) -> EvaluationResult:
        if dataset_2 is not None and len(dataset_1) != len(dataset_2):
            raise ValueError("Datasets must have the same index.")

        outputs_1 = model.predict(dataset_1).prediction

        if dataset_2 is not None:
            outputs_2 = model.predict(dataset_2).prediction
        else:
            with model_cache.no_cache():
                outputs_2 = model.predict(dataset_2).prediction

        inputs_1 = dataset_1.df.to_dict("records")
        inputs_2 = dataset_2.df.loc[dataset_1.df.index].to_dict("records")

        errors = []
        success_examples = []
        failure_examples = []
        for input_1, input_2, output_1, output_2 in zip(inputs_1, inputs_2, outputs_1, outputs_2):
            sample = {
                "input_1": input_1,
                "output_1": output_1,
                "input_2": input_2,
                "output_2": output_2,
            }

            try:
                passed, reason = self._eval_pair(model, input_1, input_2, output_1, output_2)
            except LLMGenerationError as err:
                errors.append({"message": str(err), "sample": sample})

            sample["reason"] = reason
            if passed:
                success_examples.append(sample)
            else:
                failure_examples.append(sample)

        return EvaluationResult(success_examples=success_examples, failure_examples=failure_examples, errors=errors)

    def _eval_pair(self, model: BaseModel, input_1, input_2, output_1, output_2):
        prompt = self.eval_prompt.format(
            model_name=model.meta.name,
            model_description=model.meta.description,
            input_1=input_1,
            input_2=input_2,
            output_1=output_1,
            output_2=output_2,
        )

        out = llm_fn_call([{"role": "system", "content": prompt}], functions=EVALUATE_MODEL_FUNCTIONS, temperature=0.1)

        try:
            args = json.loads(out.function_call.arguments)
            return (
                args["passed_test"],
                args.get("reason"),
            )
        except (AttributeError, KeyError, json.JSONDecodeError) as err:
            raise LLMGenerationError("LLM evaluation function did not return the expected arguments.") from err
