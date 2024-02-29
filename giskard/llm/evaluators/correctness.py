from ...core.test_result import TestResultStatus, create_test_result_details
from ...datasets import Dataset
from ...models.base.model import BaseModel
from ..client.base import LLMMessage
from ..errors import LLMGenerationError
from .base import EVALUATE_MODEL_FUNCTIONS, EvaluationResult, LLMBasedEvaluator

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
    """Assess the correctness of a model answers given questions and associated reference answers."""

    _default_eval_prompt = CORRECTNESS_EVALUATION_PROMPT

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

    def evaluate(
        self,
        model: BaseModel,
        dataset: Dataset,
        question_col: str = "question",
        reference_answer_col: str = "reference_answer",
    ):
        if not (question_col in dataset.df and reference_answer_col in dataset.df):
            raise ValueError(
                f"Missing required columns in the evaluation dataset. Make sure the dataset has columns {question_col} and {reference_answer_col}."
            )

        if question_col not in model.feature_names:
            raise ValueError(
                f"Model has no feature '{question_col}'. Make sure your Model wrapper accepts '{question_col}'."
            )

        model_outputs = model.predict(dataset).prediction

        succeeded = []
        failed = []
        errored = []
        status = []
        reasons = []
        for evaluation_question, model_output in zip(dataset.df.to_dict("records"), model_outputs):
            try:
                passed, reason = self._evaluate_single(
                    model,
                    evaluation_question[question_col],
                    evaluation_question[reference_answer_col],
                    model_output,
                )
                reasons.append(reason)
                sample = {
                    **evaluation_question,
                    "reason": reason,
                    "model_output": model_output,
                    "model_evaluation": passed,
                }
                if passed:
                    succeeded.append(sample)
                    status.append(TestResultStatus.PASSED)
                else:
                    failed.append(sample)
                    status.append(TestResultStatus.FAILED)
            except LLMGenerationError as err:
                errored.append({"message": str(err), "sample": {**evaluation_question, "model_output": model_output}})
                reasons.append(str(err))
                status.append(TestResultStatus.ERROR)

        return EvaluationResult(
            failure_examples=failed,
            success_examples=succeeded,
            errors=errored,
            details=create_test_result_details(dataset, model, model_outputs, status, {"reason": reasons}),
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
            [LLMMessage(role="system", content=prompt)],
            tools=self._make_evaluate_functions(),
            tool_choice={"type": "function", "function": {"name": "evaluate_model"}},
            temperature=self.llm_temperature,
            caller_id=self.__class__.__name__,
            seed=self.rng_seed,
        )

        try:
            passed_test = out.tool_calls[0].function.arguments["passed_test"]
            reason = out.tool_calls[0].function.arguments.get("reason")
        except (AttributeError, KeyError, IndexError):
            raise LLMGenerationError("Invalid function call arguments received")

        return passed_test, reason
