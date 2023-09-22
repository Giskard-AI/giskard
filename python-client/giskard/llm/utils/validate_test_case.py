from typing import List, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ..config import llm_config
from ...models.base.model import BaseModel
from ...scanner.llm.utils import LLMImportError

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
""",
        ),
        (
            "user",
            """
```json
{prompt}
```
""",
        ),
        ("ai", "{response}"),
    ]
)

chain = create_structured_output_chain(
    TestResult, llm_config.build_scan_llm(gpt4_preferred=True, max_tokens=512, temperature=0.2), prompt
)


def validate_test_case_with_reason(model: BaseModel, test_case: str, df, predictions: List[str]) -> List[TestResult]:
    inputs = [
        {
            "prompt": df.iloc[i].to_dict(),
            "test_case": test_case,
            "response": predictions[i],
            "model_name": model.meta.name,
            "model_description": model.meta.description,
        }
        for i in range(len(predictions))
    ]

    return [chain.run(**input) for input in inputs]


def validate_test_case(model: BaseModel, test_case: str, df, predictions: List[str]) -> List[bool]:
    return [res.score >= 3 for res in validate_test_case_with_reason(model, test_case, df, predictions)]
