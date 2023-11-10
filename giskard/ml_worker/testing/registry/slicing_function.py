from typing import Callable, Dict, List, Optional, Set, Type, Union

import functools
import inspect
from pathlib import Path

import pandas as pd

from giskard.core.core import DatasetProcessFunctionMeta, DatasetProcessFunctionType
from giskard.core.validation import configured_validate_arguments
from giskard.ml_worker.core.savable import Artifact, RegistryArtifact
from giskard.ml_worker.testing.registry.decorators_utils import (
    drop_arg,
    make_all_optional_or_suite_input,
    set_return_type,
    validate_arg_type,
)
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry

SlicingFunctionType = Callable[..., bool]

default_tags = ["filter"]


class SlicingFunction(RegistryArtifact[DatasetProcessFunctionMeta]):
    """
    A slicing function used to subset data.

    Attributes:
        func (SlicingFunctionType): The function used to slice the data.
        row_level (bool): Whether the slicing function should operate on rows or columns.
        cell_level (bool): Whether the slicing function should operate at the cell level.
        params (Dict): Additional parameters for the slicing function.
        is_initialized (bool): Indicates if the slicing function has been initialized.
    """

    func: SlicingFunctionType
    row_level: bool
    cell_level: bool
    params: Dict
    is_initialized: bool

    @classmethod
    def _get_name(cls) -> str:
        """
        Returns the name of the class.

        :return: The name of the class.
        :rtype: str
        """
        return "slices"

    def __init__(self, func: Optional[SlicingFunctionType], row_level=True, cell_level=False):
        """
        Initializes a new instance of the SlicingFunction class.

        :param func: The function used to slice the data.
        :type func: SlicingFunctionType
        :param row_level: Whether the slicing function should operate on rows or the whole dataframe. Defaults to True.
        :type row_level: bool
        """
        self.is_initialized = False
        self.params = {}
        self.func = func
        self.row_level = row_level
        self.cell_level = cell_level

        test_uuid = get_object_uuid(func)
        meta = tests_registry.get_test(test_uuid)
        if meta is None and func is not None:
            meta = DatasetProcessFunctionMeta(func, tags=default_tags, type="SLICE", cell_level=self.cell_level)
            tests_registry.register(meta)
        super().__init__(meta)

    def __call__(self, *args, **kwargs) -> "SlicingFunction":
        self.is_initialized = True
        self.params = kwargs

        for idx, arg in enumerate(args):
            self.params[next(iter([arg.name for arg in self.meta.args.values() if arg.argOrder == idx]))] = arg

        return self

    @property
    def dependencies(self) -> Set[Artifact]:
        if self.func is None:
            return set()

        from inspect import Parameter, signature

        parameters: List[Parameter] = list(signature(self.func).parameters.values())

        return set([param.default for param in parameters if isinstance(param.default, Artifact)])

    def execute(self, data: Union[pd.Series, pd.DataFrame]):
        """
        Slices the data using the slicing function.

        Args:
            data (Union[pd.Series, pd.DataFrame]): The data to slice.

        Returns:
            Union[pd.Series, pd.DataFrame]: The sliced data.
        """
        func = configured_validate_arguments(self.func)
        if self.cell_level:
            actual_params = {k: v for k, v in self.params.items() if k != "column_name"}
            return data.loc[data.apply(lambda row: func(row[self.params["column_name"]], **actual_params), axis=1)]
        if self.row_level:
            return data.loc[data.apply(lambda row: func(row, **self.params), axis=1)]
        else:
            return func(data, **self.params)

    @classmethod
    def load(cls, local_dir: Path, uuid: str, meta: DatasetProcessFunctionMeta):
        if meta.process_type == DatasetProcessFunctionType.CODE:
            return super().load(local_dir, uuid, meta)
        else:
            return cls._load_no_code(meta)

    @classmethod
    def _get_meta_class(cls):
        return DatasetProcessFunctionMeta

    @classmethod
    def _load_no_code(cls, meta: DatasetProcessFunctionMeta):
        from ....slicing.slice import Query, QueryBasedSliceFunction

        return QueryBasedSliceFunction(Query.from_clauses(meta.clauses))


def slicing_function(_fn=None, row_level=True, name=None, tags: Optional[List[str]] = None, cell_level=False):
    """
    Decorator that registers a function as a slicing function and returns a SlicingFunction instance.
    It can be used for slicing datasets in a specific way during testing.

    :param _fn: function to decorate. No need to provide this argument, the decorator will automatically take as input the function to decorate.
    :param name: Optional name to use for the function when registering it.
    :param tags: Optional list of tags to use when registering the function.
    :param row_level: Whether to apply the slicing function row-wise (default) or on the full dataframe. If `row_level`
                      is True, the slicing function will receive a row (either a Series or DataFrame),
                      and if False, it will receive the entire dataframe.
    :param cell_level: Whether to apply the slicing function on the cell level. If True, the slicing function
                       will be applied to individual cells instead of rows or the entire dataframe.
    :return: The wrapped function or a new instance of SlicingFunction.
    """

    def inner(func: Union[SlicingFunctionType, Type[SlicingFunction]]) -> SlicingFunction:
        from giskard.ml_worker.testing.registry.registry import tests_registry

        tests_registry.register(
            DatasetProcessFunctionMeta(
                func,
                name=name,
                tags=default_tags if not tags else (default_tags + tags),
                type="SLICE",
                cell_level=cell_level,
            )
        )
        if inspect.isclass(func) and issubclass(func, SlicingFunction):
            return func

        return _wrap_slicing_function(func, row_level, cell_level)

    if callable(_fn):
        return functools.wraps(_fn)(inner(_fn))
    else:
        return inner


def _wrap_slicing_function(original: Callable, row_level: bool, cell_level: bool):
    slicing_fn = functools.wraps(original)(SlicingFunction(original, row_level, cell_level))

    if not cell_level:
        validate_arg_type(slicing_fn, 0, pd.Series if row_level else pd.DataFrame)

    drop_arg(slicing_fn, 0)

    make_all_optional_or_suite_input(slicing_fn)
    set_return_type(slicing_fn, SlicingFunction)

    return slicing_fn()
