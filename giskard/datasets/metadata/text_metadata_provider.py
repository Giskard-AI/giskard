import langdetect
import pandas as pd
from langdetect import DetectorFactory

from .registry import MetadataProvider

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
                "charset": pd.Categorical(values.map(_detect_charset)),
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


def _detect_lang(text: str):
    if len(text.split()) <= 5:
        return pd.NA
    try:
        detected = langdetect.detect_langs(text)
        language = detected[0].lang
    except langdetect.lang_detect_exception.LangDetectException:
        language = "unknown"
    return language
