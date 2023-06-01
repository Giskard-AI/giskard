import inspect
import pickle
import sys
from pathlib import Path
from typing import Optional, List, Union, Type, Callable

import pandas as pd

from giskard.core.core import CallableMeta
from giskard.ml_worker.core.savable import Savable
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry

SlicingFunctionType = Union[Callable[[pd.Series], bool], Callable[[pd.DataFrame], bool]]

default_tags = ['filter']


class SlicingFunction(Savable[SlicingFunctionType, CallableMeta]):
    """
    A slicing function used to subset data.

    :param func: The function used to slice the data.
    :type func: SlicingFunctionType
    :param row_level: Whether the slicing function should operate on rows or columns. Defaults to True.
    :type row_level: bool
    """
    func: SlicingFunctionType = None
    row_level: bool = True

    @classmethod
    def _get_name(cls) -> str:
        """
        Returns the name of the class.

        :return: The name of the class.
        :rtype: str
        """
        return 'slices'

    def __init__(self, func: SlicingFunctionType, row_level=True):
        """
        Initializes a new instance of the SlicingFunction class.

        :param func: The function used to slice the data.
        :type func: SlicingFunctionType
        :param row_level: Whether the slicing function should operate on rows or the whole dataframe. Defaults to True.
        :type row_level: bool
        """
        self.func = func
        self.row_level = row_level
        test_uuid = get_object_uuid(func)
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            meta = tests_registry.register(CallableMeta(func, tags=default_tags, type='SLICE'))
        super().__init__(func, meta)

    def __call__(self, data: Union[pd.Series, pd.DataFrame]):
        """
        Slices the data using the slicing function.

        :param data: The data to slice.
        :type data: Union[pd.Series, pd.DataFrame]
        :return: The sliced data.
        :rtype: Union[pd.Series, pd.DataFrame]
        """
        if self.row_level:
            return data.loc[data.apply(self.func, axis=1)]
        else:
            return self.func(data)

    def _should_save_locally(self) -> bool:
        return self.data.__module__.startswith('__main__')

    def _should_upload(self) -> bool:
        return self.meta.version is None

    @classmethod
    def _read_from_local_dir(cls, local_dir: Path, meta: CallableMeta):
        if not meta.module.startswith('__main__'):
            func = getattr(sys.modules[meta.module], meta.name)
        else:
            if not local_dir.exists():
                return None
            with open(Path(local_dir) / 'data.pkl', 'rb') as f:
                func = pickle.load(f)

        _slicing_function = cls(func)

        tests_registry.add_func(meta)
        _slicing_function.meta = meta

        return _slicing_function

    @classmethod
    def _read_meta_from_loca_dir(cls, uuid: str, project_key: Optional[str]) -> CallableMeta:
        meta = tests_registry.get_test(uuid)
        assert meta is not None, f"Cannot find slicing function {uuid}"
        return meta

    @classmethod
    def _get_meta_class(cls):
        return CallableMeta


def slicing_function(_fn=None, row_level=True, name=None, tags: Optional[List[str]] = None):
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
            CallableMeta(func, name=name, tags=default_tags if not tags else (default_tags + tags), type='SLICE'))
        if inspect.isclass(func) and issubclass(func, SlicingFunction):
            return func
        return SlicingFunction(func, row_level)

    if callable(_fn):
        return inner(_fn)
    else:
        return inner
