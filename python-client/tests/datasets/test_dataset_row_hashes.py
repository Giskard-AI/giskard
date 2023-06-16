import pandas as pd
from xxhash import xxh3_128_hexdigest

from giskard import Dataset


def test_hash_generated_once():
    df = pd.DataFrame([{"foo": "bar", "baz": 42}, {"foo": "Hello!", "baz": 3.14}])
    dataset = Dataset(df, cat_columns=[])

    expected_hashes = [
        xxh3_128_hexdigest("'bar', 42.0".encode("utf-8")),
        xxh3_128_hexdigest("'Hello!', 3.14".encode("utf-8")),
    ]

    assert expected_hashes == list(dataset.row_hashes.values)

    dataset.df = pd.DataFrame([{"foo": "not bar", "baz": 42000}, {"foo": "Hi!", "baz": 3.147}])

    # Hash not recomputed (dataset are be mutable)
    assert expected_hashes == list(dataset.row_hashes.values)


def test_hash_differentiate_str_int():
    df_int = pd.DataFrame([42, 3])
    dataset_int = Dataset(df_int, cat_columns=[])

    df_str = pd.DataFrame(["42", "3"])
    dataset_str = Dataset(df_str, cat_columns=[])

    assert list(dataset_int.row_hashes.values) != list(dataset_str.row_hashes.values)


def test_hash_differentiate_str_bool():
    df_bool = pd.DataFrame([True, False])
    dataset_bool = Dataset(df_bool, cat_columns=[])

    df_str = pd.DataFrame(["True", "False"])
    dataset_str = Dataset(df_str, cat_columns=[])

    assert list(dataset_bool.row_hashes.values) != list(dataset_str.row_hashes.values)


def test_hash_deterministic():
    df = pd.DataFrame([42, 3.14])
    dataset_one = Dataset(df, cat_columns=[])

    dataset_two = Dataset(df, cat_columns=[])

    assert list(dataset_one.row_hashes.values) == list(dataset_two.row_hashes.values)
