from ...core.errors import GiskardInstallationError
from ...datasets.base import Dataset
from dataclasses import dataclass
import pandas as pd
from ..issues import Issue


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
        return self.info.deviation

    @property
    def description(self) -> str:
        return "We found that the model is likely to generate sentences with stereotypes"

    def examples(self, n=3) -> pd.DataFrame:
        return self.info.examples

    @property
    def importance(self) -> float:
        return 1
