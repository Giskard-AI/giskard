import functools
import inspect
import pickle
import sys
from pathlib import Path
from typing import Optional, List, Union, Type, Callable

import pandas as pd

from giskard.core.core import DatasetProcessFunctionMeta
from giskard.core.validation import configured_validate_arguments
from giskard.ml_worker.core.savable import Savable
from giskard.ml_worker.testing.registry.decorators_utils import validate_arg_type, drop_arg, \
    make_all_optional_or_suite_input, set_return_type
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry

SlicingFunctionType = Callable[..., bool]

default_tags = ['filter']


class SlicingFunction(Savable[SlicingFunctionType, DatasetProcessFunctionMeta]):
    """
    A slicing function used to subset data.

    :param func: The function used to slice the data.
    :type func: SlicingFunctionType
    :param row_level: Whether the slicing function should operate on rows or columns. Defaults to True.
    :type row_level: bool
    """
    func: SlicingFunctionType = None
    row_level: bool = True
    cell_level: bool = False
    params = {}
    is_initialized = False

    @classmethod
    def _get_name(cls) -> str:
        """
        Returns the name of the class.

        :return: The name of the class.
        :rtype: str
        """
        return 'slices'

    def __init__(self, func: SlicingFunctionType, row_level=True, cell_level=False):
        """
        Initializes a new instance of the SlicingFunction class.

        :param func: The function used to slice the data.
        :type func: SlicingFunctionType
        :param row_level: Whether the slicing function should operate on rows or the whole dataframe. Defaults to True.
        :type row_level: bool
        """
        self.func = func
        self.row_level = row_level
        self.cell_level = cell_level

        test_uuid = get_object_uuid(func)
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            meta = tests_registry.register(
                DatasetProcessFunctionMeta(func, tags=default_tags, type='SLICE', cell_level=self.cell_level))
        super().__init__(func, meta)

    def __call__(self, *args, **kwargs) -> 'SlicingFunction':
        self.is_initialized = True
        self.params = kwargs

        for idx, arg in enumerate(args):
            self.params[next(iter([arg.name for arg in self.meta.args.values() if arg.argOrder == idx]))] = arg

        return self

    def execute(self, data: Union[pd.Series, pd.DataFrame]):
        """
        Slices the data using the slicing function.

        :param data: The data to slice.
        :type data: Union[pd.Series, pd.DataFrame]
        :return: The sliced data.
        :rtype: Union[pd.Series, pd.DataFrame]
        """
        if self.cell_level:
            actual_params = {k: v for k, v in self.params.items() if k != 'column_name'}
            return data.loc[data.apply(lambda row: self.func(row[self.params['column_name']], **actual_params), axis=1)]
        if self.row_level:
            return data.loc[data.apply(lambda row: self.func(row, **self.params), axis=1)]
        else:
            return self.func(data, **self.params)

    def _should_save_locally(self) -> bool:
        return self.data.__module__.startswith('__main__')

    def _should_upload(self) -> bool:
        return self.meta.version is None

    @classmethod
    def _read_from_local_dir(cls, local_dir: Path, meta: DatasetProcessFunctionMeta):
        if not meta.module.startswith('__main__'):
            func = getattr(sys.modules[meta.module], meta.name)
        else:
            if not local_dir.exists():
                return None
            with open(Path(local_dir) / 'data.pkl', 'rb') as f:
                func = pickle.load(f)

        if inspect.isclass(func) or hasattr(func, 'meta'):
            _slicing_function = func()
        else:
            _slicing_function = cls(func)
            tests_registry.add_func(meta)
            _slicing_function.meta = meta

        return _slicing_function

    @classmethod
    def _read_meta_from_loca_dir(cls, uuid: str, project_key: Optional[str]) -> DatasetProcessFunctionMeta:
        meta = tests_registry.get_test(uuid)
        assert meta is not None, f"Cannot find slicing function {uuid}"
        return meta

    @classmethod
    def _get_meta_class(cls):
        return DatasetProcessFunctionMeta


def slicing_function(_fn=None, row_level=True, name=None, tags: Optional[List[str]] = None, cell_level=False):
    """
    Decorator that registers a slicing function with the testing registry and returns a SlicingFunction instance.

    :param _fn: Optional function to decorate.
    :param row_level: Whether to apply the slicing function row-wise (default) or on the full dataframe.
    :param name: Optional name to use for the function when registering it with the testing registry.
    :param tags: Optional list of tags to use when registering the function.
    :return: The wrapped function or a new instance of SlicingFunction.
    """

    def inner(func: Union[SlicingFunctionType, Type[SlicingFunction]]) -> SlicingFunction:

        from giskard.ml_worker.testing.registry.registry import tests_registry

        tests_registry.register(
            DatasetProcessFunctionMeta(func, name=name, tags=default_tags if not tags else (default_tags + tags),
                                       type='SLICE', cell_level=cell_level))
        if inspect.isclass(func) and issubclass(func, SlicingFunction):
            return func

        return _wrap_slicing_function(func, row_level, cell_level)()

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

    return configured_validate_arguments(slicing_fn)
