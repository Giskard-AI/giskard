import tempfile

import pandas as pd
import pytest

from giskard.datasets import Dataset


@pytest.mark.parametrize(
    "dataset",
    [
        Dataset(
            pd.DataFrame(
                {
                    "question": [
                        "What is the capital of France?",
                        "What is the capital of Germany?",
                    ]
                }
            ),
            column_types={"question": "text"},
            target=None,
        ),
        Dataset(
            pd.DataFrame(
                {
                    "country": ["France", "Germany", "France", "Germany", "France"],
                    "capital": ["Paris", "Berlin", "Paris", "Berlin", "Paris"],
                }
            ),
            column_types={"country": "category", "capital": "category"},
            cat_columns=["country", "capital"],
            target=None,
        ),
        Dataset(
            pd.DataFrame(
                {
                    "x": [1, 2, 3, 4, 5],
                    "y": [2, 4, 6, 8, 10],
                }
            ),
            column_types={"x": "numeric", "y": "numeric"},
            target="y",
        ),
    ],
    ids=["text", "category", "numeric"],
)
def test_save_and_load_dataset(dataset: Dataset):
    with tempfile.TemporaryDirectory() as tmp_test_folder:
        dataset.save(tmp_test_folder)

        loaded_dataset = Dataset.load(tmp_test_folder)

        assert loaded_dataset.id != dataset.id
        assert loaded_dataset.original_id == dataset.id
        assert pd.DataFrame.equals(loaded_dataset.df, dataset.df)
        assert loaded_dataset.meta == dataset.meta
