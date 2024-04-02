import numpy as np
import pandas as pd

from giskard.registry.slicing_function import slicing_function


# Performance tests: Classification
@slicing_function(name="Incorrect rows", row_level=False)
def incorrect_rows_slicing_fn(df: pd.DataFrame, target: str, prediction: np.ndarray) -> pd.DataFrame:
    """
    Filter the rows where the ground truth (target) does not match the model predictions.
    """
    return df[df[target] != prediction]


# Performance tests: Regression
@slicing_function(name="nlargest abs err rows", row_level=False)
def nlargest_abs_err_rows_slicing_fn(
    df: pd.DataFrame, target: str, prediction: np.ndarray, debug_percent_rows: float = 0.3
) -> pd.DataFrame:
    """
    Filter the largest debug_percent_rows of rows based on the absolute error between
    the ground truth (target) and the model predictions.
    """
    df["metric"] = abs(df[target] - prediction)
    top_n = round(debug_percent_rows * len(df))
    return df.nlargest(top_n, "metric").drop("metric", axis=1)


# Miscellaneous: Monotonicity
@slicing_function(name="Rows failing monotonicity", row_level=False)
def row_failing_slicing_fn(df: pd.DataFrame, index_failure: pd.Index) -> pd.DataFrame:
    """
    Filter the dataset by index
    """
    return df.loc[index_failure]
