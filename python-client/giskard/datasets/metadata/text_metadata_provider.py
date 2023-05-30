import pandas as pd
import numpy as np

from .registry import MetadataProvider
import langdetect
from langdetect import DetectorFactory

DetectorFactory.seed = 0


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
                "avg_whitespace": values.map(_avg_whitespace),
                "avg_digits": values.map(_avg_digits),
                "language": values.map(_detect_lang),
            },
            index=values.index,
        )

    def supported_types(self):
        return ["text"]


def _detect_charset(text: str):
    import chardet

    charset = chardet.detect(text.encode("utf-8", errors="ignore"))["encoding"]
    return charset or "undefined"


def _avg_word_length(text: str):
    # @TODO: improve this
    words = text.split()
    if len(words) == 0:
        return 0.0
    return np.mean([len(w) for w in words])


def _avg_whitespace(text: str):
    chars = list(text)
    if len(chars) == 0:
        return 0.0
    return np.mean([c.isspace() for c in chars])


def _avg_digits(text: str):
    chars = list(text)
    if len(chars) == 0:
        return 0.0
    return np.mean([c.isdigit() for c in chars])


def _detect_lang(text: str):
    if len(text.split()) <= 5:
        return pd.NA
    try:
        detected = langdetect.detect_langs(text)
        language = detected[0].lang
    except langdetect.lang_detect_exception.LangDetectException:
        language = "unknown"
    return language
