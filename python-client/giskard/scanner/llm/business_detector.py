from dataclasses import dataclass
from typing import List, Sequence

import pandas as pd
from pydantic import BaseModel, Field

from .utils import LLMImportError
from ..decorators import detector
from ..issues import Issue
from ..llm.prompts import GENERATE_TEST_PROMPT
from ..llm.utils import infer_dataset
from ...datasets.base import Dataset
from ...models.langchain import LangchainModel
from ...testing.tests.llm import test_test_case


@dataclass
class LLMExamplesInfo:
    examples: pd.DataFrame
    test_case: str
    metric: float


class LLMBusinessIssue(Issue):
    group = "Use cases"

    @property
    def domain(self) -> str:
        return f"Test: '{self.info.test_case.capitalize()}'"

    @property
    def metric(self) -> str:
        return f"{self.info.metric * 100:.2f}% of the generated answer failed to respect the test"

    @property
    def deviation(self) -> str:
        return ""

    @property
    def description(self) -> str:
        return f"For the test '{self.info.test_case}', we found that {self.info.metric * 100:.2f} of the generated answers does not respect it."

    def examples(self, n=3) -> pd.DataFrame:
        return self.info.examples.style.set_tooltips(self.info.examples)

    @property
    def importance(self) -> float:
        return 1

    def generate_tests(self, with_names=False) -> list:
        tests = [test_test_case(test_case=self.info.test_case, threshold=1 - self.info.metric + 0.1)]

        if with_names:
            names = [f"Test: '{self.info.test_case}'"]
            return list(zip(tests, names))

        return tests


def _generate_test_cases(model):
    try:
        from langchain import PromptTemplate, LLMChain, OpenAI
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

    chain = LLMChain(llm=OpenAI(model_name="gpt-3.5-turbo", max_tokens=512, temperature=0.8), prompt=prompt)

    output = chain.run(prompt_template=f"{model.meta.name} - {model.meta.description}")

    fix_parser = OutputFixingParser.from_llm(
        parser=parser, llm=OpenAI(model_name="gpt-3.5-turbo", max_tokens=512, temperature=0.6)
    )

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
            info = LLMExamplesInfo(df_with_pred[failed], test_case=test_case, metric=metric)
            issues.append(LLMBusinessIssue(model, dataset, level="major" if metric < threshold else "minor", info=info))

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
