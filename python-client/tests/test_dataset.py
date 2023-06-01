from giskard.datasets import dataset
from giskard.datasets.base import Dataset
import pandas as pd
import pytest

valid_df = pd.DataFrame({"categorical_column": ['turtle', 'crocodile', 'turtle'],
                         "text_column": ['named Giskard', 'a nile crocodile', 'etc'],
                         "numeric_column": [15.5, 25.9, 2.4]})
valid_df_column_types = {'categorical_column': 'category', 'text_column': 'text', 'numeric_column': 'numeric'}

nonvalid_df = pd.DataFrame({"categorical_column": [['turtle'], ['crocodile'], ['turtle']],
                            "text_column": [{1: 'named Giskard'}, {2: 'a nile crocodile'}, {3: 'etc'}],
                            "numeric_column": [(15.5, 1), (25.9, 2), (2.4, 3)]})


def test_factory():
    my_dataset = dataset(valid_df)
    assert isinstance(my_dataset, Dataset)


def test_valid_df_column_types():
    # Option 0: none of column_types, cat_columns, infer_column_types = True are provided
    with pytest.warns(
            UserWarning,
            match="You did not provide any of \[column_types, cat_columns, infer_column_types = True\] " # noqa
                  "for your Dataset\. In this case, we assume that there\\'s no categorical columns in your Dataset\."): # noqa
        my_dataset = dataset(valid_df)
    assert my_dataset.column_types == {'categorical_column': 'text', 'text_column': 'text', 'numeric_column': 'numeric'}

    # Option 1: column_types is provided
    my_dataset = dataset(valid_df, column_types=valid_df_column_types)
    assert my_dataset.column_types == valid_df_column_types

    # Option 2: cat_columns is provided
    cat_columns = ['categorical_column']
    my_dataset = dataset(valid_df, cat_columns=cat_columns)
    assert my_dataset.column_types == valid_df_column_types

    # Option 3: infer_column_types is provided
    my_dataset = dataset(valid_df, infer_column_types=True)
    assert my_dataset.column_types == valid_df_column_types


def test_nonvalid_df_column_types():
    # Option 0: none of column_types, cat_columns, infer_column_types = True are provided
    with pytest.raises(
            TypeError,
            match="The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. " # noqa
                  "We currently support only hashable column types such as int, bool, str, tuple and not list or dict\."): # noqa
        dataset(nonvalid_df)

    # Option 1: column_types is provided
    with pytest.raises(
            TypeError,
            match="The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. " # noqa
                  "We currently support only hashable column types such as int, bool, str, tuple and not list or dict\."): # noqa
        dataset(nonvalid_df, column_types=valid_df_column_types)

    # Option 2: cat_columns is provided
    cat_columns = ['categorical_column']
    with pytest.raises(
            TypeError,
            match="The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. " # noqa
                  "We currently support only hashable column types such as int, bool, str, tuple and not list or dict\."): # noqa
        dataset(nonvalid_df, cat_columns=cat_columns)

    # Option 3: infer_column_types is provided
    with pytest.raises(
            TypeError,
            match="The following columns in your df: \['categorical_column', 'text_column'\] are not hashable\. " # noqa
                  "We currently support only hashable column types such as int, bool, str, tuple and not list or dict\."): # noqa
        dataset(nonvalid_df, infer_column_types=True)
