import pandas as pd
import numpy as np
import pytest
from giskard.datasets.base import Dataset

valid_df = pd.DataFrame(
    {
        "categorical_column": ["turtle", "crocodile", "turtle"],
        "text_column": ["named Giskard", "a nile crocodile", "etc"],
        "numeric_column": [15.5, 25.9, 2.4],
    }
)
valid_df_column_types = {
    "categorical_column": "category",
    "text_column": "text",
    "numeric_column": "numeric",
}

nonvalid_df = pd.DataFrame(
    {
        "categorical_column": [["turtle"], ["crocodile"], ["turtle"]],
        "text_column": [{1: "named Giskard"}, {2: "a nile crocodile"}, {3: "etc"}],
        "numeric_column": [(15.5, 1), (25.9, 2), (2.4, 3)],
    }
)


def test_factory():
    my_dataset = Dataset(valid_df)
    assert isinstance(my_dataset, Dataset)


def test_valid_df_column_types():
    # Option 0: none of column_types, cat_columns, infer_column_types = True are provided
    with pytest.warns(
        UserWarning,
        match=r"You did not provide the optional argument 'target'\. 'target' is the column name "
        r"in df corresponding to the actual target variable \(ground truth\)\.",
    ):
        my_dataset = Dataset(valid_df)
    assert my_dataset.column_types == {
        "categorical_column": "category",
        "text_column": "text",
        "numeric_column": "numeric",
    }

    # Option 1: column_types is provided
    my_dataset = Dataset(valid_df, column_types=valid_df_column_types)
    assert my_dataset.column_types == valid_df_column_types

    # Option 2: cat_columns is provided
    cat_columns = ["categorical_column"]
    my_dataset = Dataset(valid_df, cat_columns=cat_columns)
    assert my_dataset.column_types == valid_df_column_types

    # Option 3: infer_column_types is provided
    my_dataset = Dataset(valid_df)
    assert my_dataset.column_types == valid_df_column_types


def test_nonvalid_df_column_types():
    # Option 0: none of column_types, cat_columns, infer_column_types = True are provided
    with pytest.raises(
        TypeError,
        match=r"The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. "
        r"We currently support only hashable column types such as int, bool, str, tuple and not list or dict\.",
    ):
        Dataset(nonvalid_df)

    # Option 1: column_types is provided
    with pytest.raises(
        TypeError,
        match=r"The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. "
        r"We currently support only hashable column types such as int, bool, str, tuple and not list or dict\.",
    ):
        Dataset(nonvalid_df, column_types=valid_df_column_types)

    # Option 2: cat_columns is provided
    cat_columns = ["categorical_column"]
    with pytest.raises(
        TypeError,
        match=r"The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. "
        r"We currently support only hashable column types such as int, bool, str, tuple and not list or dict\.",
    ):
        Dataset(nonvalid_df, cat_columns=cat_columns)

    # Option 3: infer_column_types is provided
    with pytest.raises(
        TypeError,
        match=r"The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. "
        r"We currently support only hashable column types such as int, bool, str, tuple and not list or dict\.",
    ):
        Dataset(nonvalid_df)


def test_dataset_raises_exception_if_mixed_column_types():
    df = pd.DataFrame(
        {"feature": [1, 2, "string", None, np.nan], "target": [0, 0, 1, 1, 0]}
    )

    with pytest.raises(TypeError):
        Dataset(df, target="target")


def test_inference_priority():
    column_types = {"categorical_column": "text"}
    expected_df_column_types = {
        "categorical_column": "text",
        "text_column": "text",
        "numeric_column": "numeric",
    }

    # Case 1: only one column in column_types is provided
    my_dataset = Dataset(valid_df, column_types=column_types)
    assert my_dataset.column_types == expected_df_column_types

    # Case 2: one column in column_types is provided, one in cat_columns
    my_dataset = Dataset(
        valid_df, column_types=column_types, cat_columns=["categorical_column"]
    )
    assert my_dataset.column_types == valid_df_column_types

    # Case 3: an unknown column in column_types is provided
    column_types = {"unknown_column": "text"}
    my_dataset = Dataset(
        valid_df, column_types=column_types, cat_columns=["categorical_column"]
    )
    assert my_dataset.column_types == valid_df_column_types


def test_numeric_column_names():
    df = pd.DataFrame(np.ones((10, 3)), columns=[1, 2, 3])

    assert Dataset(df, target=2)
    assert Dataset(df, column_types={1: "numeric"})
