import pandas as pd


def df_std(dataset, feature, negative=False):
    sign = -1 if negative else 1
    if dataset.column_types[feature] == "numerical":
        return sign * (dataset.df[feature].std())


def generate_std_transfo(std):
    def func(x: pd.Series) -> pd.Series:
        return x + std

    return func
