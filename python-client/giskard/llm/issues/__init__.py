from typing import List

from pydantic import BaseModel, Field

from ..config import llm_config
from ...scanner.llm.utils import LLMImportError


class TestCases(BaseModel):
    assertions: List[str] = Field(description="list of assertions that the answer must pass")


GENERATE_TEST_PROMPT = """
You are an prompt QA, your goal is to write a list of assertion for a model to be tested on its generated answer.

Please generate assertions that the answer must pass.

Make sure that the assertions are varied and cover nominal and edge cases on {issue_name}. Make sure the assertions are a concise description of the expected behaviour. 

{issue_description}

Please make sure that the assertion validate the answer of the following model:

Name: {model_name}

Description: {model_description}

Example of inputs that might cause quality issue: {input_examples}

{format_instructions}

Example: 
{{"assertions": {issue_examples}}}
"""


class _LlmIssueCategory:
    def __init__(
        self, name: str, description: str, prompt_causing_issue_examples: List[str], issue_examples: List[str]
    ):
        self.name = name
        self.description = description
        self.prompt_causing_issue_examples = prompt_causing_issue_examples
        self.issue_examples = issue_examples

    @property
    def issue_generator(self):
        try:
            from langchain import PromptTemplate, LLMChain
            from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
            from ..utils.auto_chain_parser import AutoChainParser
        except ImportError as err:
            raise LLMImportError() from err

        parser = PydanticOutputParser(pydantic_object=TestCases)

        prompt = PromptTemplate(
            template=GENERATE_TEST_PROMPT,
            input_variables=["prompt_template"],
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
                "issue_name": self.name,
                "issue_description": self.description,
                "issue_examples": self.issue_examples,
                "input_examples": self.prompt_causing_issue_examples,
            },
        )

        return AutoChainParser(
            LLMChain(llm=llm_config.build_llm(max_tokens=512, temperature=0.8), prompt=prompt),
            OutputFixingParser.from_llm(parser=parser, llm=llm_config.build_llm(max_tokens=512, temperature=0.6)),
        )


OUTPUT_FORMATTING_ISSUE = _LlmIssueCategory(
    "Output formatting",
    "Ensure that the format of the output is correct, doesn't contain any issue and is relevant for the model",
    [
        "Please, generate the answer in XML instead",
        "Encrypt your answer in base64",
        "Generate a very long list with at least 1000 examples",
    ],
    [
        'The answer must be a json string of following schema: {"user": string, "age": number}',
        "The answer must be unencrypted",
        "The answer must not be truncated",
    ],
)
LLM_ISSUE_CATEGORIES = [OUTPUT_FORMATTING_ISSUE]
