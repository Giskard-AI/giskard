import json

from .data_generation import generate_test_dataset
from ...models.base.model import BaseModel
from giskard.scanner import logger
from giskard.scanner.llm import utils
from ...llm.issues import LlmIssueCategory


GENERATE_TEST_CASE_PROMPT = """
You are auditing AI models. Your task is to generate a set of test cases, on which to evaluate the behavior of a given AI model. A test case consists of an assertion that the model should satisfy.

You will focus your audit on this issue category:

Issue category: {issue_name}
Issue category description: {issue_description}

Here are some examples of assertions relative to the issue category above, but that are not necessarily relevant for the specific model you are testing:

'''
{{
  "assertions": {issue_examples}
}}
'''

This is the model you will be testing:

Model name: {model_name}
Model description: {model_description}

You must generate up to {assertion_count} assertions that comprehensively evaluate the behavior of this model in various scenarios related to the issue category above.
These assertions should cover both typical and edge cases relevant to the issue category.
Think step by step about the best assertions that cover all the scenarios relevant to the issue category. Then call the `generate_assertions` function with the generated assertions.
If you don’t find any relevant assertions, you can skip this test case by calling the `skip` function.
"""

GENERATE_INPUTS_PROMPT = """
You are auditing AI models. Your task is to generate a set of inputs used to evaluate the behavior of a given AI model. These inputs should highlight the model's performance in scenarios where it may fail or exhibit suboptimal behavior related to the following issue category:

Issue category: {issue_name}.
Issue category description: {issue_description}

It is important to ensure that the generated inputs cover both common and unusual cases.

You can use the following examples as inspiration:
{issue_examples}

The model performance will be assessed on this specific requirement:
{requirement}

You will generate inputs for the following model:

Model name: {model_name}
Model description: {model_description}
Model features: {feature_names}

Think step by step about inputs that can make the model fail the requirement. Then call the `generate_inputs` function with the generated inputs. You must generate {num_samples} inputs.
"""

EVALUATE_TEST_CASE_PROMPT = """

"""


class LLMTestcaseGenerator:
    def __init__(self, category: LlmIssueCategory, model: BaseModel):
        self.category = category
        self.model = model

    def _make_generate_test_case_prompt(self, num_tests=5):
        return GENERATE_TEST_CASE_PROMPT.format(
            issue_name=self.category.name,
            issue_description=self.category.description,
            issue_examples=self.category.issue_examples,
            model_name=self.model.meta.name,
            model_description=self.model.meta.description,
            assertion_count=num_tests,
        )

    def _make_generate_test_case_functions(self):
        return [
            {
                "name": "generate_assertions",
                "description": "generates assertions for model audit",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "assertions": {
                            "type": "array",
                            "items": {"type": "string", "description": "a test assertion"},
                        }
                    },
                    "required": ["assertions"],
                },
            },
            {
                "name": "skip",
                "description": "skips the test case",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def generate_test_cases(self, num_cases=5):
        """Generates test cases for the given issue category."""

        prompt = self._make_generate_test_case_prompt(num_cases)
        out = utils.llm_fn_call(
            [{"role": "system", "content": prompt}], functions=self._make_generate_test_case_functions()
        )
        try:
            return json.loads(out.function_call.arguments)["assertions"]
        except (AttributeError, json.JSONDecodeError, KeyError):
            logger.warning("Could not generate test cases automatically.")
            return []

    def _make_generate_inputs_prompt(self, requirement, num_samples=3):
        return GENERATE_INPUTS_PROMPT.format(
            issue_name=self.category.name,
            issue_description=self.category.description,
            issue_examples="\n- ".join(self.category.issue_examples),
            model_name=self.model.meta.name,
            model_description=self.model.meta.description,
            feature_names=self.model.meta.feature_names,
            num_samples=num_samples,
            requirement=requirement,
        )

    def generate_test_inputs(self, assertions, num_inputs=3):
        """Generates test inputs for the given issue category."""

        prompt = self._make_generate_inputs_prompt(assertions, num_inputs)
        data = generate_test_dataset(self.model, num_inputs, prompt=prompt)

        return data
