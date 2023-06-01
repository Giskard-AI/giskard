import pandas as pd
import numpy as np

from .registry import MetadataProvider


class TextMetadataProvider(MetadataProvider):
    def __init__(self, name="text"):
        self.name = name

    def generate_metadata(self, values: pd.Series):
        # Ensure this is text encoded as a string
        values = values.astype(str)

        return pd.DataFrame(
            {
                "text_length": values.map(len),
                "avg_word_length": values.map(_avg_word_length),
                "charset": pd.Categorical(values.map(_detect_charset)),
            },
            index=values.index,
        )

    def supported_types(self):
        return ["text"]


def _detect_charset(text: str):
    import chardet

    charset = chardet.detect(text.encode("utf-8", errors="ignore"))["encoding"]
    return charset or "undefined"


def _avg_word_length(text: str) -> float:
    # @TODO: improve this
    words = text.split()
    if len(words) == 0:
        return 0.0
    return np.mean([len(w) for w in words])
