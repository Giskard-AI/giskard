from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field
from typing import List, Optional

from ..config import llm_config
from ..prompts.prompts import VALIDATE_TEST_CASE
from ...models.base.model import BaseModel
from ...scanner.llm.utils import LLMImportError

try:
    from langchain import PromptTemplate, LLMChain
    from langchain.output_parsers import PydanticOutputParser
    from langchain.output_parsers import RetryWithErrorOutputParser
except ImportError as err:
    raise LLMImportError() from err


class TestResult(PydanticBaseModel):
    result: bool = Field(description="true if the test passed, false if the test failed")
    reason: str = Field(description="A small explanation on why the test has passed or failed")
    tip: Optional[str] = Field(description="A small tip on how to improve the model if the test failed")


parser = PydanticOutputParser(pydantic_object=TestResult)

prompt = PromptTemplate(
    template=VALIDATE_TEST_CASE,
    input_variables=["prompt", "test_case", "response", "model_name", "model_description"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = LLMChain(llm=llm_config.build_llm(temperature=0.2), prompt=prompt)

retry_parser = RetryWithErrorOutputParser.from_llm(parser=parser, llm=llm_config.build_llm(temperature=0.2))


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

    return [retry_parser.parse_with_prompt(chain.run(**input), prompt.format_prompt(**input)) for input in inputs]


def validate_test_case(model: BaseModel, test_case: str, df, predictions: List[str]) -> List[bool]:
    return [res.result for res in validate_test_case_with_reason(model, test_case, df, predictions)]
