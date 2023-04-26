import pandas as pd
import numpy as np


# Performance tests
def incorrect_rows_mask(df: pd.DataFrame, targets: pd.Series, prediction: np.ndarray):
    return df.index[targets != prediction].tolist()


# Performance tests: RMSE, MAE, R2
def top_nper_abs_err_rows_mask(df: pd.DataFrame, targets: pd.Series, raw_prediction: np.ndarray,
                               debug_percent_rows: float = 0.3):
    df['metric'] = abs(targets - raw_prediction)
    top_n = round(debug_percent_rows * len(df))
    return df.nlargest(top_n, 'metric').index.tolist()
