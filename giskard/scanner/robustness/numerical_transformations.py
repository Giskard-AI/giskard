import numpy as np
import pandas as pd
from ...core.core import DatasetProcessFunctionMeta
from ...datasets import Dataset
from ...registry.registry import get_object_uuid
from ...registry.transformation_function import TransformationFunction

class NumericalTransformation(TransformationFunction):
    name: str

    def __init__(self, column, needs_dataset=False):
        super().__init__(None, row_level=False, cell_level=False, needs_dataset=needs_dataset)
        self.column = column
        self.meta = DatasetProcessFunctionMeta(type="TRANSFORMATION")
        self.meta.uuid = get_object_uuid(self)
        self.meta.code = self.name
        self.meta.name = self.name
        self.meta.display_name = self.name
        self.meta.tags = ["pickle", "scan"]
        self.meta.doc = self.meta.default_doc("Automatically generated transformation function")

    def __str__(self):
        return self.name

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna()
        data.loc[feature_data.index, self.column] = self.make_perturbation(feature_data)
        return data

    def make_perturbation(self, values: pd.Series) -> pd.Series:
        raise NotImplementedError()

class MultiplyByFactor(NumericalTransformation):
    name = "Multiply by factor"

    def __init__(self, column: str, factor: float):
        super().__init__(column)
        self.factor = factor

    def make_perturbation(self, values: pd.Series) -> pd.Series:
        if np.issubdtype(values.dtype, np.integer):
            return np.round(values * self.factor).astype(values.dtype)
        return values * self.factor

class AddGaussianNoise(NumericalTransformation):
    name = "Add Gaussian noise"

    def __init__(self, column: str, mean: float = 0, std: float = 0.01):
        super().__init__(column)
        self.mean = mean
        self.std = std

    def make_perturbation(self, values: pd.Series) -> pd.Series:
        if np.issubdtype(values.dtype, np.integer):
            return np.round(values + np.random.normal(self.mean, self.std, values.shape)).astype(values.dtype)
        return values + np.random.normal(self.mean, self.std, values.shape)
