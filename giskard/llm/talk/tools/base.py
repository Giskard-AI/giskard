from __future__ import annotations

from typing import TYPE_CHECKING

from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from giskard.models.base import BaseModel
    from giskard.scanner.report import ScanReport

from giskard.datasets.base import Dataset


class BaseTool(ABC):
    default_name: str = ...
    default_description: str = ...

    def __init__(
        self,
        model: BaseModel = None,
        dataset: Dataset = None,
        scan_result: ScanReport = None,
        name: str = None,
        description: str = None,
    ):
        self._model = model
        self._dataset = dataset
        self._scan_result = scan_result
        self._name = name if name is not None else self.default_name
        self._description = description if description is not None else self.default_description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    @abstractmethod
    def specification(self) -> str:
        ...

    @abstractmethod
    def __call__(self, *args, **kwargs) -> str:
        ...


def get_feature_json_type(dataset: Dataset) -> dict[any, str]:
    number_columns = {column: "number" for column in dataset.df.select_dtypes(include=(int, float)).columns}
    string_columns = {column: "string" for column in dataset.df.select_dtypes(exclude=(int, float)).columns}
    return number_columns | string_columns
