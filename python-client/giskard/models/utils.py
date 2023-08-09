import itertools
import random
from collections.abc import Iterator
from functools import lru_cache
from typing import List

import numpy as np
import pandas as pd

from giskard import Dataset
from giskard.models.base import BaseModel


def map_to_tuples(data: Iterator):
    item = next(data)
    data = itertools.chain([item], data)

    if isinstance(item, tuple):  # nothing to do
        return data

    return map(lambda x: (x,), data)


def np_types_to_native(some_list: List):
    if some_list is not None:
        return [np_type_to_native(i) for i in some_list]
    return some_list


def np_type_to_native(i):
    return i.item() if isinstance(i, np.generic) else i


def fix_seed(seed=1337):
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


@lru_cache(None)
def warn_once(logger, msg: str):
    logger.warning(msg)


def prepare_df(df: pd.DataFrame, model: BaseModel, dataset: Dataset) -> pd.DataFrame:
    """Prepare dataframe for an inference step."""
    df = model.prepare_dataframe(df, column_dtypes=dataset.column_dtypes, target=dataset.target)

    if dataset.target in df.columns:
        prepared_dataset = Dataset(df, column_types=dataset.column_types, target=dataset.target)
    else:
        prepared_dataset = Dataset(df, column_types=dataset.column_types)

    # Make sure column order is the same as in the dataset.df.
    columns_original_order = (
        model.meta.feature_names
        if model.meta.feature_names
        else [c for c in dataset.df.columns if c in prepared_dataset.df.columns]
    )

    prepared_df = prepared_dataset.df[columns_original_order]
    return prepared_df
