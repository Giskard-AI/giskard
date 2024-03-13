from typing import Any, Dict, Optional, Sequence

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ...core.test_result import TestResultDetails, TestResultStatus
from ...datasets.base import Dataset
from ...models.base.model import BaseModel
from ..client import LLMClient, get_default_client
from ..errors import LLMGenerationError

EVALUATE_MODEL_FUNCTIONS = [
    {
        "type": "function",
        "function": {
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
                "required": ["passed_test"],
            },
        },
    },
]


@dataclass
class EvaluationResult:
    failure_examples: Sequence[dict]
    success_examples: Sequence[dict]
    errors: Sequence[dict]
    details: Optional[TestResultDetails] = None

    @property
    def passed(self):
        return len(self.failure_examples) == 0 and len(self.success_examples) > 0

    @property
    def failed(self):
        return not self.passed

    @property
    def has_errors(self):
        return len(self.errors) > 0

    @property
    def passed_ratio(self):
        return len(self.success_examples) / (len(self.success_examples) + len(self.failure_examples))

    @classmethod
    def empty(cls):
        return EvaluationResult(list(), list(), list(), TestResultDetails.empty())

    def append(self, status: TestResultStatus, inputs, output, metadata, example: dict):
        self.details = self.details or TestResultDetails.empty()
        self.details.append(status, inputs, output, metadata)

        if status == TestResultStatus.PASSED:
            self.success_examples.append(example)
        elif status == TestResultStatus.FAILED:
            self.failure_examples.append(example)
        elif status == TestResultStatus.ERROR:
            self.errors.append(example)


class BaseEvaluator(ABC):
    """Base class for evaluators that define a way of detecting a LLM failure"""

    @abstractmethod
    def evaluate(self, model: BaseModel, dataset: Dataset):
        ...


class LLMBasedEvaluator(BaseEvaluator):
    _default_eval_prompt: str

    def __init__(self, eval_prompt=None, llm_temperature=0.1, llm_client: LLMClient = None, rng_seed: int = 1729):
        self.eval_prompt = eval_prompt or self._default_eval_prompt
        self.llm_temperature = llm_temperature
        self.llm_client = llm_client if llm_client is not None else get_default_client()
        self.rng_seed = rng_seed

    def _make_evaluate_prompt(self, model: BaseModel, input_vars, model_output, row_idx):
        return self.eval_prompt.format(
            model_name=model.name,
            model_description=model.description,
            input_vars=input_vars,
            model_output=model_output,
        )

    def _make_evaluate_functions(self, model: BaseModel, input_vars, model_output):
        return EVALUATE_MODEL_FUNCTIONS

    def _get_metadata(self, row_idx, *args, **kwargs) -> Dict[str, Any]:
        return dict()

    def evaluate(self, model: BaseModel, dataset: Dataset):
        model_outputs = model.predict(dataset).prediction

        evaluation_result = EvaluationResult.empty()
        for row_index, input_vars, model_output in zip(
            dataset.df.index,
            dataset.df.loc[:, model.feature_names].to_dict("records"),
            model_outputs,
        ):
            sample = {"input_vars": input_vars, "model_output": model_output}
            prompt = self._make_evaluate_prompt(model, input_vars, model_output, row_index)
            funcs = self._make_evaluate_functions(model, input_vars, model_output)
            metadata = self._get_metadata(row_index)
            try:
                out = self.llm_client.complete(
                    [{"role": "system", "content": prompt}],
                    tools=funcs,
                    tool_choice={"type": "function", "function": {"name": "evaluate_model"}},
                    temperature=self.llm_temperature,
                    caller_id=self.__class__.__name__,
                    seed=self.rng_seed,
                )
                if len(out.tool_calls) != 1 or "passed_test" not in out.tool_calls[0].function.arguments:
                    raise LLMGenerationError("Invalid function call arguments received")
            except LLMGenerationError as err:
                metadata["Reason"] = str(err)
                evaluation_result.append(
                    TestResultStatus.ERROR, input_vars, model_output, metadata, {"message": str(err), "sample": sample}
                )
                continue

            args = out.tool_calls[0].function.arguments
            metadata["Reason"] = args.get("reason")
            evaluation_result.append(
                TestResultStatus.PASSED if args["passed_test"] else TestResultStatus.FAILED,
                input_vars,
                model_output,
                metadata,
                {"input_vars": input_vars, "model_output": model_output, "reason": args.get("reason")},
            )

        return evaluation_result
