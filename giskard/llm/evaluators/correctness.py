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
    """Correctness evaluator class: assess the correctness of a model answers
    given questions and associated reference answers.
    """

    _default_eval_prompt = CORRECTNESS_EVALUATION_PROMPT
    _question_feature_name = "question"
    _reference_answer_feature_name = "reference_answer"

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
        question_feature_name: str = None,
        reference_answer_feature_name: str = None,
    ):
        question_feature_name = (
            question_feature_name if question_feature_name is not None else self._question_feature_name
        )
        reference_answer_feature_name = (
            reference_answer_feature_name
            if reference_answer_feature_name is not None
            else self._reference_answer_feature_name
        )
        qa_feature_names = [question_feature_name, reference_answer_feature_name]

        # question and reference_answer feature names must be present in the dataset
        if not (question_feature_name in dataset.df and reference_answer_feature_name in dataset.df):
            raise ValueError(
                f"Missing at least one required feature in the evaluation dataset among: {qa_feature_names}."
            )

        # question feature name must be inside model's features
        if question_feature_name not in model.feature_names:
            raise ValueError(f"Missing question feature: '{question_feature_name}' inside model's features.")

        model_outputs = model.predict(dataset).prediction
        succeeded = []
        failed = []
        errored = []
        status = []
        reasons = []
        for idx, (evaluation_question, model_output) in enumerate(zip(dataset.df.to_dict("records"), model_outputs)):
            try:
                passed, reason = self._evaluate_single(
                    model,
                    evaluation_question[question_feature_name],
                    evaluation_question[reference_answer_feature_name],
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
                    status.append(TestResultStatus.FAILED)
                    failed.append(sample)
            except LLMGenerationError as err:
                status.append(TestResultStatus.ERROR)
                reasons.append(str(err))
                errored.append({"message": str(err), "sample": {**evaluation_question, "model_output": model_output}})

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
        )

        try:
            passed_test = out.tool_calls[0].function.arguments["passed_test"]
            reason = out.tool_calls[0].function.arguments.get("reason")
        except (AttributeError, KeyError, IndexError, TypeError):
            raise LLMGenerationError("Invalid function call arguments received")

        return passed_test, reason
