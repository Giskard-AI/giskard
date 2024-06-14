from typing import List, Optional

import numpy as np
import pandas as pd

from ..core.core import DatasetProcessFunctionMeta
from ..registry.registry import get_object_uuid
from ..registry.transformation_function import TransformationFunction


class CategorialTransformation(TransformationFunction):
    name: str

    def __init__(self, cat_column, needs_dataset=False):
        super().__init__(None, row_level=False, cell_level=False, needs_dataset=needs_dataset)
        self.cat_column = cat_column
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
        feature_data = data[self.cat_column]
        data.loc[feature_data.index, self.column] = feature_data.apply(self.make_perturbation)
        return data

    def make_perturbation(self) -> Optional[List[str]]:
        raise NotImplementedError()


class CategorialShuffle(CategorialTransformation):
    name = "Shuffle categorial values"

    def __init__(self, cat_column, rng_seed=1729):
        super.__init__(cat_column)
        self.rng = np.random.default_rng(seed=rng_seed)

    def execute(self, data: pd.DataFrame):
        feature_data = data[self.cat_column]
        cat_values = list(set(feature_data))
        for i in range(len(cat_values)):
            shuffle_cat_value = self.rng.choice(cat_values)
            cat_values[i] = shuffle_cat_value

        return data
