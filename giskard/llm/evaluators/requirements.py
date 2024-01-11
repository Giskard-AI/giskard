from typing import Sequence

from abc import abstractmethod

import pandas as pd

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


class BaseRequirementEvaluator(LLMBasedEvaluator):
    """Base class for requirement evaluation."""

    _default_eval_prompt = EVALUATE_PROMPT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def requirements(self, row_idx) -> str:
        """Define the evaluation requirements for a given input."""
        ...

    def _make_evaluate_prompt(self, model: BaseModel, input_vars, model_output, row_idx):
        return self.eval_prompt.format(
            model_name=model.name,
            model_description=model.description,
            input_vars=input_vars,
            model_output=model_output,
            requirements=self.requirements(row_idx),
        )


class RequirementEvaluator(BaseRequirementEvaluator):
    """Evaluator for global requirements over the entire dataset."""

    def __init__(self, requirements: Sequence[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requirements_list = requirements

    def requirements(self, row_idx):
        return "\n".join([f"- {r}" for r in self.requirements_list])


class PerRowRequirementEvaluator(BaseRequirementEvaluator):
    """Evaluator for requirements evaluated individually for each row in a dataset."""

    def __init__(self, requirements_df: pd.DataFrame, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requirements_df = requirements_df

    def requirements(self, row_idx):
        return "\n".join([f"- {r}" for r in self.requirements_df.iloc[row_idx]])
