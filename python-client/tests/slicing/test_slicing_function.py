import pandas as pd
from giskard import slicing_function


def test_slicing_function(german_credit_data):
    # Define a slicing function
    @slicing_function(row_level=False)
    def head_slice(df: pd.DataFrame) -> pd.DataFrame:
        return df.head(10)

    # Slice the dataset
    data_slice = german_credit_data.slice(head_slice)

    assert data_slice.df == german_credit_data.df.head(10)