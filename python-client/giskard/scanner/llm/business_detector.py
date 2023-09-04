from typing import List, Sequence

import pandas as pd
from pydantic import BaseModel, Field

from .utils import LLMImportError
from ..decorators import detector
from ..issues import Issue, IssueLevel, IssueGroup
from ..llm.prompts import GENERATE_TEST_PROMPT
from ..llm.utils import infer_dataset
from ...datasets.base import Dataset
from ...llm.config import llm_config
from ...models.langchain import LangchainModel


def _generate_test_cases(model):
    try:
        from langchain import PromptTemplate, LLMChain
        from langchain.output_parsers import PydanticOutputParser
        from langchain.output_parsers import OutputFixingParser
    except ImportError as err:
        raise LLMImportError() from err

    class TestCases(BaseModel):
        assertions: List[str] = Field(description="list of assertions that the answer must pass")

    parser = PydanticOutputParser(pydantic_object=TestCases)

    prompt = PromptTemplate(
        template=GENERATE_TEST_PROMPT,
        input_variables=["prompt_template"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = LLMChain(llm=llm_config.default_llm(max_tokens=512, temperature=0.8), prompt=prompt)

    output = chain.run(prompt_template=f"{model.meta.name} - {model.meta.description}")

    fix_parser = OutputFixingParser.from_llm(parser=parser, llm=llm_config.default_llm(max_tokens=512, temperature=0.6))

    return fix_parser.parse(output).assertions


def validate_prediction(model, test_cases: List[str], dataset: Dataset, predictions: List[str], threshold: float):
    from ...llm.utils.validate_test_case import validate_test_case

    issues = list()

    df_with_pred = dataset.df.rename(columns={column: f"prompt_input ({column})" for column in dataset.df.columns})
    df_with_pred["prediction_result"] = predictions

    for test_case in test_cases:
        print(f"Validating test: {test_case}")
        failed = [not passed for passed in validate_test_case(model, test_case, predictions)]
        failed_count = len([result for result in failed if result])
        metric = failed_count / len(predictions)
        print(f"Results: {metric} ({failed_count})")

        if failed_count > 0:
            print("Test failed")

            issues.append(
                Issue(
                    model,
                    dataset,
                    level=IssueLevel.MAJOR if metric < threshold else IssueLevel.MINOR,
                    # TODO: Use the LlmIssueCategory name and description
                    group=IssueGroup(name="Use case", description="TODO"),
                    description=f"For the test '{test_case}', we found that {metric * 100:.2f} of the generated answers does not respect it.",
                    # Todo: add more meta
                    meta={
                        "metric": "Use case",
                    },
                    examples=df_with_pred[failed],
                )
            )

    return issues


@detector("llm_business", tags=["business", "llm", "generative", "text_generation"])
class LLMBusinessDetector:
    def __init__(self, threshold: float = 0.6, num_samples=10, num_tests=4):
        self.threshold = threshold
        self.num_samples = num_samples
        self.num_tests = num_tests

    def run(self, model: LangchainModel, dataset: Dataset) -> Sequence[Issue]:
        test_cases = _generate_test_cases(model)[: self.num_tests]
        print(f"Generated tests: {test_cases}")

        potentially_failing_dataset = dataset = infer_dataset(
            f"""
        Name: {model.meta.name}
        
        Description: {model.meta.description}
        """,
            model.meta.feature_names,
            True,
        )

        print(f"Generated potentially failing prompts: {test_cases}")

        df = pd.concat([potentially_failing_dataset.df, dataset.df]).reset_index(drop=True)
        df = df.head(min(len(df.index), self.num_samples))
        dataset = Dataset(df)

        predictions = model.predict(dataset).prediction

        return validate_prediction(model, test_cases, dataset, predictions, self.threshold)
