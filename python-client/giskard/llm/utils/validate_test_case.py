from typing import List

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

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


parser = PydanticOutputParser(pydantic_object=TestResult)

prompt = PromptTemplate(
    template=VALIDATE_TEST_CASE,
    input_variables=["prompt", "test_case", "response"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = LLMChain(llm=llm_config.default_llm(temperature=0.2), prompt=prompt)

retry_parser = RetryWithErrorOutputParser.from_llm(parser=parser, llm=llm_config.default_llm(temperature=0.2))


def validate_test_case(model: BaseModel, test_case: str, predictions: List[str]) -> List[bool]:
    model_description = f"{model.meta.name} - {model.meta.description}"

    inputs = [
        {
            "prompt": model_description,
            "test_case": test_case,
            "response": predictions[i],
        }
        for i in range(len(predictions))
    ]

    return [
        retry_parser.parse_with_prompt(chain.run(**input), prompt.format_prompt(**input)).result for input in inputs
    ]
