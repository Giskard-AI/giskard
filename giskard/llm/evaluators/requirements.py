from typing import Sequence

from ...models.base.model import BaseModel
from .base import LLMBasedEvaluator

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


class RequirementEvaluator(LLMBasedEvaluator):
    _default_eval_prompt = EVALUATE_PROMPT

    def __init__(self, requirements: Sequence[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requirements = requirements

    def _make_evaluate_prompt(self, model: BaseModel, input_vars, model_output):
        return self.eval_prompt.format(
            model_name=model.meta.name,
            model_description=model.meta.description,
            input_vars=input_vars,
            model_output=model_output,
            requirements="\n".join([f"- {r}" for r in self.requirements]),
        )
