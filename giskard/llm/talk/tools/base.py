from __future__ import annotations

from typing import TYPE_CHECKING

from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from giskard.models.base import BaseModel
    from giskard.scanner.report import ScanReport

from giskard.datasets.base import Dataset


class BaseTool(ABC):
    """Base class of the Tool object.

    Attributes
    ----------
    default_name : str
        The default name of the Tool. Can be re-defined with constructor.
    default_description: str
        The default description of the Tool's functioning. Can be re-defined with constructor.
    """

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
        """Constructor of the class.

        Parameters
        ----------
        model : BaseModel
            The Giskard Model.
        dataset : Dataset
            The Giskard Dataset.
        scan_result : ScanReport
            The Giskard ScanReport object.
        name : str
            The name of the Tool. If not set, the `default_name` is used.
        description : str
            The description of the Tool. If not set, the `default_description` is used.
        """
        self._model = model
        self._dataset = dataset
        self._scan_result = scan_result
        self._name = name if name is not None else self.default_name
        self._description = description if description is not None else self.default_description

    @property
    def name(self) -> str:
        """Return the name of the Tool.

        Returns
        -------
        str
            The name of the Tool.
        """
        return self._name

    @property
    def description(self) -> str:
        """Return the description of the Tool.

        Returns
        -------
        str
            The description of the Tool.
        """
        return self._description

    @property
    @abstractmethod
    def specification(self) -> str:
        """Return the Tool's specification in a JSON Schema format.

        Returns
        -------
        str
            The Tool's specification.
        """
        ...

    @abstractmethod
    def __call__(self, *args, **kwargs) -> str:
        """Execute the Tool's functionality.

        Returns
        -------
        str
            The result of the Tool's execution.
        """
        ...


def get_feature_json_type(dataset: Dataset) -> dict[str, str]:
    """Get features' JSON type.

    Determine the JSON type of features from the given `dataset`.

    Parameters
    ----------
    dataset : Dataset
        The Giskard Dataset.

    Returns
    -------
    dict[str, str]
        The dictionary with columns and related JSON types.
    """
    number_columns = {column: "number" for column in dataset.df.select_dtypes(include=(int, float)).columns}
    string_columns = {column: "string" for column in dataset.df.select_dtypes(exclude=(int, float)).columns}
    return number_columns | string_columns
