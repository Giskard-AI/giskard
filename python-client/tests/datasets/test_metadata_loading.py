import pandas as pd
from unittest.mock import patch
from giskard.datasets.base import Dataset


def _make_dataset():
    return Dataset(
        pd.DataFrame({"col1": ["hello!", "world"], "col2": ["CAT1", "CAT2"], "col3": [1, 2]}),
        target="col3",
        column_types={"col1": "text"},
    )


ds = _make_dataset()


def test_metadata_are_passed_to_dataset_copy():
    dataset = _make_dataset()
    with patch('giskard.datasets.metadata.indexing.MetadataIndexer') as indexer:
        dataset.copy()
        indexer.load_meta.called_once_with(dataset.column_meta)


def test_metadata_are_passed_to_dataset_slice():
    dataset = _make_dataset()
    with patch('giskard.datasets.metadata.indexing.MetadataIndexer') as indexer:
        dataset.slice(lambda df: df.head(10), row_level=False)
        indexer.load_meta.called_once_with(dataset.column_meta)


def test_metadata_are_regenerated_after_dataset_transform():
    dataset = _make_dataset()
    with patch('giskard.datasets.metadata.indexing.MetadataIndexer') as indexer:
        dataset.transform(lambda df: df, row_level=False)
        indexer.load_meta.not_called()


def test_metadata_returned_on_dataset_copy():
    dataset = _make_dataset()
    dscopy = dataset.copy()
    assert dscopy.column_meta["col1", "text"]["text_length"].tolist() == [6, 5]


def test_metadata_returned_on_dataset_slice():
    dataset = _make_dataset()
    ds = dataset.slice(lambda df: df.tail(1), row_level=False)
    assert ds.column_meta["col1", "text"]["text_length"].tolist() == [5]


def test_metadata_returned_on_dataset_transform():
    dataset = _make_dataset()

    def append_123(df):
        df["col1"] = df["col1"] + "123"
        return df

    ds = dataset.transform(append_123, row_level=False)
    assert ds.column_meta["col1", "text"]["text_length"].tolist() == [9, 8]
