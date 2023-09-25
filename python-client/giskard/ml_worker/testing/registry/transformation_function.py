import functools
import inspect
from typing import Optional, List, Union, Type, Callable

import pandas as pd

from giskard.core.core import DatasetProcessFunctionMeta
from giskard.core.validation import configured_validate_arguments
from giskard.ml_worker.core.savable import RegistryArtifact
from giskard.ml_worker.testing.registry.decorators_utils import (
    validate_arg_type,
    drop_arg,
    make_all_optional_or_suite_input,
    set_return_type,
)
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry

TransformationFunctionType = Callable[..., Union[pd.Series, pd.DataFrame]]

default_tags = ["transformation"]


class TransformationFunction(RegistryArtifact[DatasetProcessFunctionMeta]):
    func: TransformationFunctionType = None
    row_level: bool = True
    cell_level: bool = False
    params = {}
    is_initialized = False

    @classmethod
    def _get_name(cls) -> str:
        return "transformations"

    def __init__(self, func: Optional[TransformationFunctionType], row_level=True, cell_level=False):
        self.func = configured_validate_arguments(func)
        self.row_level = row_level
        self.cell_level = cell_level

        test_uuid = get_object_uuid(func)
        meta = tests_registry.get_test(test_uuid)
        if meta is None and func is not None:
            meta = tests_registry.register(
                DatasetProcessFunctionMeta(func, tags=default_tags, type="TRANSFORMATION", cell_level=self.cell_level)
            )
        super().__init__(meta)

    def __call__(self, *args, **kwargs) -> "TransformationFunction":
        self.is_initialized = True
        self.params = kwargs

        for idx, arg in enumerate(args):
            self.params[next(iter([arg.name for arg in self.meta.args.values() if arg.argOrder == idx]))] = arg

        return self

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the data using the transformation function.

        Args:
            data (Union[pd.Series, pd.DataFrame]): The data to transform.

        Returns:
            Union[pd.Series, pd.DataFrame]: The transformed data.
        """
        if self.cell_level:
            actual_params = {k: v for k, v in self.params.items() if k != "column_name"}

            def apply(row: pd.Series) -> pd.Series:
                row[self.params["column_name"]] = self.func(row[self.params["column_name"]], **actual_params)
                return row

            return data.apply(apply, axis=1)
        elif self.row_level:
            return data.apply(lambda row: self.func(row, **self.params), axis=1)
        else:
            return self.func(data, **self.params)

    @classmethod
    def _get_meta_class(cls):
        return DatasetProcessFunctionMeta


def transformation_function(
    _fn: Union[TransformationFunctionType, Type[TransformationFunction]] = None,
    row_level=True,
    cell_level=False,
    name=None,
    tags: Optional[List[str]] = None,
):
    """
    Decorator that registers a function as a transformation function and returns a TransformationFunction instance.
    It can be used for transforming datasets in a specific way during testing.

    :param _fn: function to decorate. No need to provide this argument, the decorator will automatically take as input the function to decorate.
    :param name: Optional name to use for the function when registering it.
    :param tags: Optional list of tags to use when registering the function.
    :param row_level: Whether to apply the transformation function row-wise (default) or on the full dataframe. If `row_level`
                      is True, the slicing function will receive a row (either a Series or DataFrame),
                      and if False, it will receive the entire dataframe.
    :param cell_level: Whether to apply the transformation function on the cell level. If True, the slicing function
                       will be applied to individual cells instead of rows or the entire dataframe.
    :return: The wrapped function or a new instance of TransformationFunction.
    """

    def inner(func: Union[TransformationFunctionType, Type[TransformationFunction]]) -> TransformationFunction:
        from giskard.ml_worker.testing.registry.registry import tests_registry

        tests_registry.register(
            DatasetProcessFunctionMeta(
                func,
                name=name,
                tags=default_tags if not tags else (default_tags + tags),
                type="TRANSFORMATION",
                cell_level=cell_level,
            )
        )

        if inspect.isclass(func) and issubclass(func, TransformationFunction):
            return func
        return _wrap_transformation_function(func, row_level, cell_level)()

    if callable(_fn):
        return functools.wraps(_fn)(inner(_fn))
    else:
        return inner


def _wrap_transformation_function(original: Callable, row_level: bool, cell_level: bool):
    transformation_fn = functools.wraps(original)(TransformationFunction(original, row_level, cell_level))

    if not cell_level:
        validate_arg_type(transformation_fn, 0, pd.Series if row_level else pd.DataFrame)

    drop_arg(transformation_fn, 0)

    make_all_optional_or_suite_input(transformation_fn)
    set_return_type(transformation_fn, TransformationFunction)
    return transformation_fn()
