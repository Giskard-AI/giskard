from ...core.errors import GiskardInstallationError
from ...datasets.base import Dataset


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
