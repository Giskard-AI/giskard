import langdetect
import pandas as pd


def detect_lang(text: str):
    if len(text.split()) <= 5:
        return pd.NA
    try:
        detected = langdetect.detect_langs(text)
        language = detected[0].lang
    except langdetect.lang_detect_exception.LangDetectException:
        language = "unknown"
    return language
