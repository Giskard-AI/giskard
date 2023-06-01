import pandas as pd

from giskard.ml_worker.testing.registry.slicing_function import slicing_function


@slicing_function(name='Short comment')
def short_comment_slicing_fn(x: pd.Series, column_name: str, max_characters: int = 5) -> bool:
    return len(x[column_name].split()) <= max_characters


@slicing_function(name="Keyword lookup")
def keyword_lookup_slicing_fn(x: pd.Series, column_name: str, keyword: str) -> bool:
    return any(word in x[column_name].lower() for word in [keyword])


@slicing_function(name="Positive sentiment", row_level=False, tags=["sentiment"])
def positive_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    from transformers import pipeline
    sentiment_pipeline = pipeline("sentiment-analysis")

    # Limit text to 512 characters
    sentences = list(map(lambda txt: txt[:512], list(x[column_name])))

    return x.iloc[list(
        map(lambda s: s['label'] == 'POSITIVE' and s['score'] >= threshold, sentiment_pipeline(sentences)))]


@slicing_function(name="Offensive sentiment", row_level=False, tags=["sentiment"])
def offensive_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    from transformers import pipeline
    sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-offensive")

    # Limit text to 512 characters
    sentences = list(map(lambda txt: txt[:512], list(x[column_name])))

    return x.iloc[list(
        map(lambda s: s['label'] == 'offensive' and s['score'] >= threshold, sentiment_pipeline(sentences)))]


@slicing_function(name="Irony sentiment", row_level=False, tags=["sentiment"])
def irony_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    from transformers import pipeline
    sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-irony")

    # Limit text to 512 characters
    sentences = list(map(lambda txt: txt[:512], list(x[column_name])))

    return x.iloc[list(
        map(lambda s: s['label'] == 'irony' and s['score'] >= threshold, sentiment_pipeline(sentences)))]
