import pandas as pd
from langdetect import DetectorFactory

from ...utils.language_detection import detect_lang
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
                "language": values.map(detect_lang),
            },
            index=values.index,
        )

    def supported_types(self):
        return ["text"]


def _detect_charset(text: str):
    import chardet

    charset = chardet.detect(text.encode("utf-8", errors="ignore"))["encoding"]
    return charset or "undefined"
