import pandas as pd

from giskard.ml_worker.testing.registry.slicing_function import slicing_function


@slicing_function(name='Short comment')
def short_comment_slicing_fn(x: pd.Series, column_name: str, max_characters: int = 5) -> bool:
    return len(x[column_name].split()) <= max_characters


@slicing_function(name="Keyword lookup")
def keyword_lookup_slicing_fn(x: pd.Series, column_name: str, keyword: str) -> bool:
    return any(word in x[column_name].lower() for word in [keyword])
