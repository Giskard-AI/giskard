from dataclasses import dataclass
from typing import Sequence

from ...datasets.base import Dataset
from ...models.base.model import BaseModel
from ..client import LLMClient, get_default_client
from ..errors import LLMGenerationError

EVALUATE_MODEL_FUNCTIONS = [
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
    },
]


@dataclass
class EvaluationResult:
    failure_examples: Sequence[dict]
    success_examples: Sequence[dict]
    errors: Sequence[dict]

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


class LLMBasedEvaluator:
    _default_eval_prompt: str

    def __init__(self, eval_prompt=None, llm_model="gpt-4", llm_temperature=0.1, llm_client: LLMClient = None):
        self.eval_prompt = eval_prompt or self._default_eval_prompt
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.llm_client = llm_client if llm_client is not None else get_default_client()

    def _make_evaluate_prompt(self, model: BaseModel, input_vars, model_output):
        return self.eval_prompt.format(
            model_name=model.meta.name,
            model_description=model.meta.description,
            input_vars=input_vars,
            model_output=model_output,
        )

    def _make_evaluate_functions(self, model: BaseModel, input_vars, model_output):
        return EVALUATE_MODEL_FUNCTIONS

    def evaluate(self, model: BaseModel, dataset: Dataset):
        model_outputs = model.predict(dataset).prediction

        succeeded = []
        failed = []
        errored = []
        for input_vars, model_output in zip(
            dataset.df.loc[:, model.meta.feature_names].to_dict("records"), model_outputs
        ):
            sample = {"input_vars": input_vars, "model_output": model_output}
            prompt = self._make_evaluate_prompt(model, input_vars, model_output)
            funcs = self._make_evaluate_functions(model, input_vars, model_output)
            try:
                out = self.llm_client.complete(
                    [{"role": "system", "content": prompt}],
                    functions=funcs,
                    function_call={"name": "evaluate_model"},
                    temperature=self.llm_temperature,
                    model=self.llm_model,
                    caller_id=self.__class__.__name__,
                )
                if out.function_call is None or "passed_test" not in out.function_call.args:
                    raise LLMGenerationError("Invalid function call arguments received")
            except LLMGenerationError as err:
                errored.append({"message": str(err), "sample": sample})
                continue

            args = out.function_call.args
            if args["passed_test"]:
                succeeded.append({"input_vars": input_vars, "model_output": model_output, "reason": args.get("reason")})
            else:
                failed.append({"input_vars": input_vars, "model_output": model_output, "reason": args.get("reason")})

        return EvaluationResult(
            failure_examples=failed,
            success_examples=succeeded,
            errors=errored,
        )
