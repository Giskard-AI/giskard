from typing import Optional

from pydantic import BaseModel as PydenticBaseModel
from pydantic import Field

from ...datasets.base import Dataset
from ...ml_worker.testing.registry.decorators import test
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ...ml_worker.testing.test_result import TestResult
from ...models.base import BaseModel
from ...scanner.llm.prompts import VALIDATE_TEST_CASE
from ...scanner.llm.utils import LLMImportError


@test(name="Test case", tags=["llm"])
def test_test_case(
    model: BaseModel,
    dataset: Dataset,
    test_case: str,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: float = 1.0,
):
    try:
        from langchain import PromptTemplate, LLMChain, OpenAI
        from langchain.output_parsers import PydanticOutputParser
        from langchain.output_parsers import RetryWithErrorOutputParser
    except ImportError as err:
        raise LLMImportError() from err

    class TestResultModel(PydenticBaseModel):
        result: bool = Field(description="true if the test passed, false if the test failed")

    parser = PydanticOutputParser(pydantic_object=TestResultModel)

    prompt = PromptTemplate(
        template=VALIDATE_TEST_CASE,
        input_variables=["prompt", "test_case", "response"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = LLMChain(llm=OpenAI(temperature=0.2), prompt=prompt)

    retry_parser = RetryWithErrorOutputParser.from_llm(parser=parser, llm=OpenAI(temperature=0.2))

    if slicing_function is not None:
        dataset = dataset.slice(slicing_function)

    predictions = model.predict(dataset).prediction

    inputs = [
        {
            "prompt": model.prompt.format_prompt(**dataset.df.iloc[i].to_dict()),
            "test_case": test_case,
            "response": predictions[i],
        }
        for i in range(len(predictions))
    ]

    passed = [
        retry_parser.parse_with_prompt(chain.run(**input), prompt.format_prompt(**input)).result for input in inputs
    ]
    metric = len([result for result in passed if result]) / len(predictions)

    return TestResult(
        actual_slices_size=[len(dataset)],
        metric=metric,
        passed=bool(metric > threshold),
    )
