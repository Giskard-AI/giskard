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
from giskard.ml_worker.testing.registry.decorators_utils import (
    validate_arg_type,
    drop_arg,
    make_all_optional_or_suite_input,
    set_return_type,
)
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry

TransformationFunctionType = Callable[..., pd.Series]

default_tags = ['transformation']


class TransformationFunction(Savable[TransformationFunctionType, DatasetProcessFunctionMeta]):
    func: TransformationFunctionType = None
    row_level: bool = True
    params = {}
    is_initialized = False

    @classmethod
    def _get_name(cls) -> str:
        return 'transformations'

    def __init__(self, func: TransformationFunctionType, row_level=True):
        self.func = func
        self.row_level = row_level
        test_uuid = get_object_uuid(func)
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            meta = tests_registry.register(DatasetProcessFunctionMeta(func, tags=default_tags, type='TRANSFORMATION'))
        super().__init__(func, meta)

    def __call__(self, *args, **kwargs) -> 'TransformationFunction':
        self.is_initialized = True
        self.params = kwargs

        for idx, arg in enumerate(args):
            self.params[next(iter([arg.name for arg in self.meta.args.values() if arg.argOrder == idx]))] = arg

        return self

    def execute(self, data: Union[pd.Series, pd.DataFrame]):
        if self.row_level:
            return data.apply(lambda row: self.func(row, **self.params), axis=1)
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
            func_obj = func()
        else:
            func_obj = cls(func)
            tests_registry.add_func(meta)
            func_obj.meta = meta

        return func_obj

    @classmethod
    def _read_meta_from_loca_dir(cls, uuid: str, project_key: Optional[str]) -> DatasetProcessFunctionMeta:
        meta = tests_registry.get_test(uuid)
        assert meta is not None, f"Cannot find transformation function {uuid}"
        return meta

    @classmethod
    def _get_meta_class(cls):
        return DatasetProcessFunctionMeta


def transformation_function(
    _fn: Union[TransformationFunctionType, Type[TransformationFunction]] = None,
    row_level=True,
    name=None,
    tags: Optional[List[str]] = None,
):
    def inner(func: Union[TransformationFunctionType, Type[TransformationFunction]]) -> TransformationFunction:
        from giskard.ml_worker.testing.registry.registry import tests_registry

        tests_registry.register(
            DatasetProcessFunctionMeta(
                func, name=name, tags=default_tags if not tags else (default_tags + tags), type='TRANSFORMATION'
            )
        )
        if inspect.isclass(func) and issubclass(func, TransformationFunction):
            return func
        return _wrap_transformation_function(func, row_level)()

    if callable(_fn):
        return functools.wraps(_fn)(inner(_fn))
    else:
        return inner


def _wrap_transformation_function(original: Callable, row_level: bool):
    transformation_fn = functools.wraps(original)(TransformationFunction(original, row_level))

    validate_arg_type(transformation_fn, 0, pd.Series if row_level else pd.DataFrame)
    drop_arg(transformation_fn, 0)

    make_all_optional_or_suite_input(transformation_fn)
    set_return_type(transformation_fn, TransformationFunction)

    return configured_validate_arguments(transformation_fn)
