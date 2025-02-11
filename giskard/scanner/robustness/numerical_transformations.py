import numpy as np
import pandas as pd

from .base_perturbation_function import PerturbationFunction


class NumericalTransformation(PerturbationFunction):
    def __init__(self, column: str, needs_dataset: bool = False) -> None:
        super().__init__(column, needs_dataset=needs_dataset)

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna()
        data.loc[feature_data.index, self.column] = self.make_perturbation(feature_data)
        return data


class MultiplyByFactor(NumericalTransformation):
    name = "Multiply by factor"

    def __init__(self, column: str, factor: float) -> None:
        super().__init__(column)
        self.factor = factor

    def make_perturbation(self, values: pd.Series) -> pd.Series:
        # Round if the column is an integer type
        if np.issubdtype(values.dtype, np.integer):
            return np.round(values * self.factor).astype(values.dtype)
        return values * self.factor


class AddGaussianNoise(NumericalTransformation):
    name = "Add Gaussian noise"

    def __init__(self, column: str, mean: float = 0, std: float = 0.01, rng_seed: int = 1729) -> None:
        super().__init__(column)
        self.mean = mean
        self.std = std
        self.rng = np.random.default_rng(seed=rng_seed)

    def make_perturbation(self, values: pd.Series) -> pd.Series:
        noise = self.rng.normal(self.mean, self.std, values.shape)
        if np.issubdtype(values.dtype, np.integer):
            return np.round(values + noise).astype(values.dtype)
        return values + noise
