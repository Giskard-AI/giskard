import numpy as np
import pandas as pd

from giskard.ml_worker.testing.tests.performance import test_accuracy


def test_dataset_index_is_preserved(german_credit_data, german_credit_model):
    dataset = german_credit_data
    model = german_credit_model

    # Permute the index to make it non banal, otherwise reset_index will produce,
    # by change, the same sequence.
    dataset.df.set_index(dataset.df.index.values[np.random.permutation(len(dataset.df))], inplace=True)
    original_idx = dataset.df.index.copy()

    _ = test_accuracy(
        dataset=dataset,
        model=model,
        threshold=0.8
    ).execute()

    assert (dataset.df.index == original_idx).all()

    # Try with an index that is not a sequence of integers
    dataset.df.set_index(pd.to_datetime(dataset.df.index), inplace=True)
    original_idx = dataset.df.index.copy()

    _ = test_accuracy(
        dataset=dataset,
        model=model,
        threshold=0.8
    ).execute()

    assert (dataset.df.index == original_idx).all()
