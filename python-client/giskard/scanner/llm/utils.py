from typing import List, Dict

import pandas as pd
from pydantic import BaseModel, Field

from .prompts import (
    FIND_CATEGORY_PROMPT,
    FIND_CATEGORY_PROMPT_FAILED_SUFFIX,
    GENERATE_INPUT_PROMPT,
    GENERATE_INPUT_PROMPT_FAILED_SUFFIX,
)
from ...core.errors import GiskardInstallationError
from ...datasets.base import Dataset
from ...llm.config import llm_config


class LLMImportError(GiskardInstallationError):
    flavor = "llm"
    functionality = "LLM"


def _find_categories(model_description, failed=False):
    try:
        from langchain import PromptTemplate, LLMChain
        from langchain.output_parsers import PydanticOutputParser
        from langchain.output_parsers import RetryWithErrorOutputParser
    except ImportError as err:
        raise LLMImportError() from err

    class Scenarios(BaseModel):
        objectives: List[str] = Field(description="Clear and concise use objective the prompt")

    parser = PydanticOutputParser(pydantic_object=Scenarios)

    prompt = PromptTemplate(
        template=FIND_CATEGORY_PROMPT + (FIND_CATEGORY_PROMPT_FAILED_SUFFIX if failed else ""),
        input_variables=["prompt_template"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = LLMChain(llm=llm_config.build_llm(max_tokens=512, temperature=0.8), prompt=prompt)

    output = chain.run(prompt_template=model_description)

    retry_parser = RetryWithErrorOutputParser.from_llm(
        parser=parser, llm=llm_config.build_llm(max_tokens=512, temperature=0.6)
    )

    return retry_parser.parse_with_prompt(output, prompt.format_prompt(prompt_template=model_description)).objectives


def _generate_inputs(model_description, feature_names, categories, failed=False):
    try:
        from langchain import PromptTemplate, LLMChain
        from langchain.output_parsers import PydanticOutputParser
        from langchain.output_parsers import RetryWithErrorOutputParser
    except ImportError as err:
        raise LLMImportError() from err

    class PromptInputs(BaseModel):
        input: Dict[str, str] = Field(
            description="An input dictionary, the keys are the variable name inside brackets and the realistic value are the replacement text"
        )

    parser = PydanticOutputParser(pydantic_object=PromptInputs)

    prompt = PromptTemplate(
        template=GENERATE_INPUT_PROMPT + (GENERATE_INPUT_PROMPT_FAILED_SUFFIX if failed else ""),
        input_variables=["prompt_template", "category", "variables"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = LLMChain(llm=llm_config.build_llm(max_tokens=512, temperature=0.8), prompt=prompt)

    retry_parser = RetryWithErrorOutputParser.from_llm(
        parser=parser, llm=llm_config.build_llm(max_tokens=512, temperature=0.6)
    )

    results = dict()

    for category in categories:
        output = chain.run(prompt_template=model_description, category=category, variables=feature_names)

        results[category] = [
            {
                key: value
                for key, value in retry_parser.parse_with_prompt(
                    output,
                    prompt.format_prompt(prompt_template=model_description, category=category, variables=feature_names),
                ).input.items()
                if key in feature_names
            }
        ]

    return results


def infer_dataset(model_description, feature_names, failed=False):
    categories = _find_categories(model_description, failed)
    data = [
        data
        for _, examples in _generate_inputs(model_description, feature_names, categories, failed).items()
        for data in examples
    ]

    return Dataset(pd.DataFrame.from_records(data))
