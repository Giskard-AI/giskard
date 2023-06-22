import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def get_df():
    df = pd.DataFrame({"x": np.arange(100), "y": np.arange(100)})
    return df


def get_model_and_df():
    df = get_df()

    reg = LinearRegression()
    reg.fit(df["x"].to_numpy().reshape(100, 1), df["y"].to_numpy().reshape(100, 1))
    return reg, df


def get_pipeline():
    reg, _ = get_model_and_df()

    def preprocessor(df):
        return df["x"].to_numpy().reshape(len(df["x"]), 1)

    return preprocessor, reg
