from ...datasets.base import Dataset


class LLMImportError(ImportError):
    _DEFAULT_MSG = "It seems that you are using Giskard LLM functionality but you are missing some required package. Please install Giskard with LLM support with `pip install giskard[llm]`."

    def __init__(self, msg=None) -> None:
        self.msg = msg or self._DEFAULT_MSG


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
