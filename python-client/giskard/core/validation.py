import pandas as pd


def validate_target(target, dataframe_keys):
    if target not in dataframe_keys:
        raise ValueError(
            f"Invalid target parameter:"
            f" {target} column is not present in the dataset with columns: {dataframe_keys}"
        )


def validate_is_pandasdataframe(df):
    assert isinstance(df, pd.DataFrame), "Dataset provided is not a pandas dataframe"
