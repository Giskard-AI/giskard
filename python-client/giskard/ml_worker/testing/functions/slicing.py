from typing import List

import numpy as np
import pandas as pd

from giskard.ml_worker.testing.registry.slicing_function import slicing_function


@slicing_function(name="Short comment", tags=["text"], cell_level=True)
def short_comment_slicing_fn(text: str, max_words: int = 5) -> bool:
    """
    Filter the rows where the specified 'column_name' contains a short comment, defined as one with at most 'max_words'.
    """
    return not pd.isnull(text) and len(text.split()) <= max_words


@slicing_function(name="Keyword lookup", tags=["text"], cell_level=True)
def keyword_lookup_slicing_fn(text: str, keywords: List[str]) -> bool:
    """
    Filter the rows where the specified 'column_name' contains at least one of the specified 'keywords'.
    """
    return not pd.isnull(text) and any(word in text.lower() for word in keywords)


@slicing_function(name="Positive sentiment", row_level=False, tags=["sentiment", "text"])
def positive_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    """
    Filter the rows where the specified 'column_name' has a positive sentiment, as determined by a pre-trained sentiment analysis model.
    """
    return _sentiment_analysis(x, column_name, threshold, None, "POSITIVE")


@slicing_function(name="Offensive sentiment", row_level=False, tags=["sentiment", "text"])
def offensive_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    """
    Filter the rows where the specified 'column_name' has a offensive sentiment, as determined by a pre-trained sentiment analysis model.
    """
    return _sentiment_analysis(x, column_name, threshold, "cardiffnlp/twitter-roberta-base-offensive", "offensive")


@slicing_function(name="Irony sentiment", row_level=False, tags=["sentiment", "text"])
def irony_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    """
    Filter the rows where the specified 'column_name' has a ironic sentiment, as determined by a pre-trained sentiment analysis model.
    """
    return _sentiment_analysis(x, column_name, threshold, "cardiffnlp/twitter-roberta-base-irony", "irony")


@slicing_function(name="Hate sentiment", row_level=False, tags=["sentiment", "text"])
def hate_sentiment_analysis(x: pd.DataFrame, column_name: str, threshold: float = 0.9) -> pd.DataFrame:
    """
    Filter the rows where the specified 'column_name' has a hateful sentiment, as determined by a pre-trained sentiment analysis model.
    """
    return _sentiment_analysis(x, column_name, threshold, "cardiffnlp/twitter-roberta-base-hate", "hate")


@slicing_function(name="Emotion sentiment", row_level=False, tags=["sentiment", "text"])
def emotion_sentiment_analysis(x: pd.DataFrame, column_name: str, emotion: str, threshold: float = 0.9) -> pd.DataFrame:
    """
    Filter the rows where the specified 'column_name' has an emotion matching 'emotion', as determined by a pre-trained sentiment analysis model.
    Possible emotion are: 'optimism', 'anger', 'sadness', 'joy'
    """
    return _sentiment_analysis(x, column_name, threshold, "cardiffnlp/twitter-roberta-base-emotion", emotion)


def _sentiment_analysis(x, column_name, threshold, model, emotion):
    from transformers import pipeline

    sentiment_pipeline = pipeline("sentiment-analysis", model=model)
    # Limit text to 512 characters
    sentences = list(map(lambda txt: txt[:512], list(x[column_name])))
    return x.iloc[list(map(lambda s: s["label"] == emotion and s["score"] >= threshold, sentiment_pipeline(sentences)))]


# ====== debug feature slicing_functions ======
@slicing_function(name="Incorrect Rows", row_level=False, tags=["performance", "hidden"])
def incorrect_rows(x: pd.DataFrame, target: str, predictions: np.ndarray) -> pd.DataFrame:
    return x[x[target] != predictions]


@slicing_function(name="Outlier Filter", tags=["number"], cell_level=True)
def outlier_filter(value: float, lower_bound: float, upper_bound: float) -> bool:
    """
    Filter rows where the specified column values fall outside the specified range.
    """
    return not pd.isnull(value) and (value < lower_bound or value > upper_bound)
