from dataclasses import dataclass
from typing import Sequence

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

    def __init__(self, eval_prompt=None, llm_model="gpt-4", llm_temperature=0.1):
        self.eval_prompt = eval_prompt or self._default_eval_prompt
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
