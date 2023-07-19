from ...core.errors import GiskardInstallationError
from ...datasets.base import Dataset
from dataclasses import dataclass
import pandas as pd
from ..issues import Issue
import re


class LLMImportError(GiskardInstallationError):
    flavor = "llm"
    functionality = "LLM"


def load_default_dataset():
    try:
        import datasets
    except ImportError as err:
        raise LLMImportError() from err

    df = datasets.load_dataset("truthful_qa", "generation", split="validation").to_pandas()

    return Dataset(
        df.loc[:, ("type", "question", "best_answer")],
        column_types={
            "type": "category",
            "question": "text",
            "best_answer": "text",
        },
    )


def detect_gender(sentence: str) -> str:
    is_male = bool(re.search(r"\b(he|him|his)\b", sentence.lower()))
    is_female = bool(re.search(r"\b(she|her)\b", sentence.lower()))
    if is_male and (not is_female):
        return "male"
    elif (not is_male) and is_female:
        return "female"
    elif is_male and is_female:
        return "both"
    else:
        return "neutral"


@dataclass
class StereotypeExamplesInfo:
    examples: pd.DataFrame
    metric: str
    deviation: float


class StereotypeIssue(Issue):
    group = "Stereotype"

    @property
    def domain(self) -> str:
        return "Prompt level"

    @property
    def metric(self) -> str:
        return self.info.metric

    @property
    def deviation(self) -> str:
        return str(round(self.info.deviation * 100, 2)) + "%"

    @property
    def description(self) -> str:
        return "We found that the model is likely to generate sentences with stereotypes"

    def examples(self, n=3) -> pd.DataFrame:
        return self.info.examples

    @property
    def importance(self) -> float:
        return 1
