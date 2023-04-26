import pandas as pd

from giskard.ml_worker.testing.registry.slicing_function import slicing_function


@slicing_function(name='Short comment')
def short_comment_slicing_fn(x: pd.Series, column_name: str, max_characters: int = 5) -> bool:
    return len(x[column_name].split()) <= max_characters


@slicing_function(name="Keyword lookup")
def keyword_lookup_slicing_fn(x: pd.Series, column_name: str, keywords: list[str]) -> bool:
    return any(word in x[column_name].lower() for word in keywords)


@slicing_function(name="Positive sentiment", row_level=False, tags=["sentiment"])
def positive_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    return _sentiment_analysis(x, column_name, threshold, None, "POSITIVE")


@slicing_function(name="Offensive sentiment", row_level=False, tags=["sentiment"])
def offensive_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    return _sentiment_analysis(x, column_name, threshold, "cardiffnlp/twitter-roberta-base-offensive", "offensive")


@slicing_function(name="Irony sentiment", row_level=False, tags=["sentiment"])
def irony_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    return _sentiment_analysis(x, column_name, threshold, "cardiffnlp/twitter-roberta-base-irony", "irony")


@slicing_function(name="Hate sentiment", row_level=False, tags=["sentiment"])
def hate_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    return _sentiment_analysis(x, column_name, threshold, "cardiffnlp/twitter-roberta-base-hate", "hate")


@slicing_function(name="Emotion sentiment", row_level=False, tags=["sentiment"])
def emotion_sentiment_analysis(x: pd.DataFrame, column_name: str, emotion: str, threshold: float = 0.9) -> pd.DataFrame:
    return _sentiment_analysis(x, column_name, threshold, "cardiffnlp/twitter-roberta-base-emotion", emotion)


def _sentiment_analysis(x, column_name, threshold, model, emotion):
    from transformers import pipeline
    sentiment_pipeline = pipeline("sentiment-analysis", model=model)
    # Limit text to 512 characters
    sentences = list(map(lambda txt: txt[:512], list(x[column_name])))
    return x.iloc[list(
        map(lambda s: s['label'] == emotion and s['score'] >= threshold, sentiment_pipeline(sentences)))]
