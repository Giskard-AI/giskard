import json
from typing import List, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ..config import llm_config
from ...models.base.model import BaseModel
from ...scanner.llm.utils import LLMImportError
from giskard.scanner.llm import utils

try:
    from langchain.prompts import ChatPromptTemplate
    from langchain.chains.openai_functions import create_structured_output_chain
except ImportError as err:
    raise LLMImportError() from err


class TestResult(PydanticBaseModel):
    score: int = Field(
        description="A number ranging from 1 to 5: 1 indicates that the answer does not meet the criteria at all, 3 indicates that the answer can be improved, 5 indicates that the answer completely meets the criteria"
    )
    reason: str = Field(description="A text that clearly explains the given score")
    tip: Optional[str] = Field(
        description="A text that offers a clear and descriptive suggestion on how to enhance the model"
    )


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a prompt QA responsible for evaluating the LLM answer based on test assertions of the {model_name} model.

**Scope**: Please focus on testing '{test_case}'.

**Description**: The objective is to verify that the model answer related to the user prompt passes the test correctly.

**Model Information**:
``` 
{model_description}
```

**Format Instructions**: 
Please provide a JSON object as a response, including the following keys:
- Score: A number ranging from 1 to 5:
  - 1 indicates that the answer does not meet the criteria at all
  - 3 indicates that the answer can be improved
  - 5 indicates that the answer completely meets the criteria
- Reason: A text that clearly explains the given score
- Tip: A text that offers a clear and descriptive suggestion on how to enhance the model

Example: 
{{"score": 1, "reason": "The answer is missing the required key 'tips' in the JSON response", "tip": "To ensure that the schema is respected, provide an example of the expected JSON response"}}
""",
        ),
        (
            "user",
            """
```json
{prompt}
```

You are auditing an AI model. Your task is to evaluate the model in the context of the following issue category

Issue category: {issue_category_name}
Issue category description: {issue_category_description}

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

Based on the information above, please check that the output satisfies all of the following requirements:
{requirements}

If the model satisfies the requirements, it passes the evaluation test. On the contrary, if the model output does not satisfy the requirements, the model fails the test.
Call the `evaluate_model` function with the result of your evaluation.
If the model does not pass the test, also provide a brief reason as an argument to the `evaluate_model`.
If you are not sure, just answer 'I don’t know'.
""",
        ),
        ("ai", "{response}"),
    ]
)

chain = create_structured_output_chain(
    TestResult, llm_config.build_scan_llm(gpt4_preferred=True, max_tokens=512, temperature=0.2), prompt
)


EVALUATE_PROMPT = """You are auditing an AI model. Your task is to evaluate the model based on given requirements.

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

Based on the information above, please check that the model behaviour satisfies all of the following requirements:
- {requirements}

Your decision must be only based on the listed requirements.

If the model satisfies the requirements, it passes the evaluation test. On the contrary, if the model output does not satisfy the requirements, the model fails the test.
Call the `evaluate_model` function with the result of your evaluation.
If the model does not pass the test, also provide a brief reason as an argument to the `evaluate_model`.
If you are not sure, just answer 'I don’t know'.
"""

EVALUATE_FUNCTIONS = [
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
    }
]


def validate_test_case_with_reason(model: BaseModel, test_case: str, df, predictions: List[str]) -> List[TestResult]:
    inputs = [
        {
            "input_vars": df.iloc[i].to_dict(),
            "requirements": test_case,
            "model_output": predictions[i],
            "model_name": model.meta.name,
            "model_description": model.meta.description,
        }
        for i in range(len(predictions))
    ]
    results = []
    for data in inputs:
        prompt = EVALUATE_PROMPT.format(
            model_name=model.meta.name,
            model_description=model.meta.description,
            input_vars=data["input_vars"],
            model_output=data["model_output"],
            requirements=data["requirements"],
        )
        out = utils.llm_fn_call([{"role": "system", "content": prompt}], functions=EVALUATE_FUNCTIONS, temperature=0.1)

        try:
            args = json.loads(out.function_call.arguments)

            if args["passed_test"]:
                results.append(TestResult(score=5, reason="The answer is correct"))
            else:
                print("EVAL", args)
                results.append(TestResult(score=0, reason=args.get("reason")))

        except (AttributeError, json.JSONDecodeError, KeyError):
            results.append(TestResult(score=5, reason=""))

    return results


def validate_test_case(model: BaseModel, test_case: str, df, predictions: List[str]) -> List[bool]:
    return [res.score >= 3 for res in validate_test_case_with_reason(model, test_case, df, predictions)]
