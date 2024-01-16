from typing import Sequence

from giskard.datasets import Dataset
from giskard.llm.errors import LLMGenerationError
from giskard.llm.evaluators.base import (
    EVALUATE_MODEL_FUNCTIONS,
    EvaluationResult,
    LLMBasedEvaluator,
)
from giskard.models.base.model import BaseModel

CORRECTNESS_EVALUATION_PROMPT = """Your role is to test AI models. Your task consists in assessing whether a model output correctly answers a question. 
You are provided with the ground truth answer to the question. Your task is then to evaluate if the model answer is close to the ground thruth answer. 

You are auditing the following model:

Model name: {model_name}
Model description: {model_description}

Here is the question that was asked to the model and its output, followed by the expected ground truth answer:

QUESTION:
###
{question}
###

MODEL OUTPUT:
###
{model_output}
###

GROUND TRUTH:
###
{ground_truth}
###

Think step by step and consider the model output in its entirety. Remember: you need to have a strong and sound reason to support your evaluation.
Call the `evaluate_model` function with the result of your evaluation.
"""


class CorrectnessEvaluator(LLMBasedEvaluator):
    _default_eval_prompt = CORRECTNESS_EVALUATION_PROMPT
    _required_features = ["question", "reference_answer"]

    def _make_evaluate_functions(self):
        return EVALUATE_MODEL_FUNCTIONS

    def _make_evaluate_prompt(self, model_name, model_description, question, model_output, ground_truth):
        return self.eval_prompt.format(
            model_name=model_name,
            model_description=model_description,
            question=question,
            model_output=model_output,
            ground_truth=ground_truth,
        )

    def evaluate(self, model: BaseModel, dataset: Dataset, feature_names: Sequence = None):
        feature_names = self._required_features if feature_names is None else feature_names

        if any([name not in dataset.df for name in feature_names]):
            raise ValueError(f"Missing at least one required feature in the evaluation dataset among: {feature_names}.")

        if any([name not in model.feature_names for name in feature_names]):
            raise ValueError(f"Missing at least one required feature in the evaluated model among: {feature_names}.")

        model_outputs = model.predict(dataset).prediction
        succeeded = []
        failed = []
        errored = []
        for evaluation_question, model_output in zip(dataset.df.to_dict("records"), model_outputs):
            try:
                passed, reason = self._evaluate_single(
                    model, evaluation_question[feature_names[0]], evaluation_question[feature_names[1]], model_output
                )
                sample = {
                    **evaluation_question,
                    "reason": reason,
                    "model_output": model_output,
                    "model_evaluation": passed,
                }
                if passed:
                    succeeded.append(sample)
                else:
                    failed.append(sample)
            except LLMGenerationError as err:
                errored.append({"message": str(err), "sample": {**evaluation_question, "model_output": model_output}})

        return EvaluationResult(
            failure_examples=failed,
            success_examples=succeeded,
            errors=errored,
        )

    def _evaluate_single(self, model: BaseModel, question, reference_answer, model_output):
        prompt = self._make_evaluate_prompt(
            model.meta.name,
            model.meta.description,
            question,
            model_output,
            reference_answer,
        )

        out = self.llm_client.complete(
            [{"role": "system", "content": prompt}],
            functions=self._make_evaluate_functions(),
            function_call={"name": "evaluate_model"},
            temperature=self.llm_temperature,
            caller_id=self.__class__.__name__,
        )
        if out.function_call is None or "passed_test" not in out.function_call.args:
            raise LLMGenerationError("Invalid function call arguments received")

        return out.function_call.args["passed_test"], out.function_call.args.get("reason")
