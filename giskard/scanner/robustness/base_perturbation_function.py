from typing import Any

import pandas as pd

from ...core.core import DatasetProcessFunctionMeta
from ...registry.registry import get_object_uuid
from ...registry.transformation_function import TransformationFunction


class PerturbationFunction(TransformationFunction):
    name: str

    def __init__(self, column: str, needs_dataset: bool = False) -> None:
        super().__init__(None, row_level=False, cell_level=False, needs_dataset=needs_dataset)
        self.column = column
        self.meta = DatasetProcessFunctionMeta(type="TRANSFORMATION")
        self.meta.uuid = get_object_uuid(self)
        self.meta.code = self.name
        self.meta.name = self.name
        self.meta.display_name = self.name
        self.meta.tags = ["pickle", "scan"]
        self.meta.doc = self.meta.default_doc("Automatically generated transformation function")

    def __str__(self) -> str:
        return self.name

    def make_perturbation(self, data_or_series: Any) -> Any:
        raise NotImplementedError()

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError()
