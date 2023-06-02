import functools
import inspect
import pickle
import sys
from pathlib import Path
from typing import Optional, List, Union, Type, Callable

import cloudpickle
import pandas as pd

from giskard.core.core import DatasetProcessFunctionMeta
from giskard.core.validation import configured_validate_arguments
from giskard.ml_worker.core.savable import Artifact
from giskard.ml_worker.testing.registry.decorators_utils import (
    validate_arg_type,
    drop_arg,
    make_all_optional_or_suite_input,
    set_return_type,
)
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry

TransformationFunctionType = Callable[..., Union[pd.Series, pd.DataFrame]]

default_tags = ['transformation']


class TransformationFunction(Artifact[DatasetProcessFunctionMeta]):
    func: TransformationFunctionType = None
    row_level: bool = True
    cell_level: bool = False
    params = {}
    is_initialized = False

    @classmethod
    def _get_name(cls) -> str:
        return 'transformations'

    def __init__(self, func: Optional[TransformationFunctionType], row_level=True, cell_level=False):
        self.func = func
        self.row_level = row_level
        self.cell_level = cell_level

        test_uuid = get_object_uuid(func)
        meta = tests_registry.get_test(test_uuid)
        if meta is None and func is not None:
            meta = tests_registry.register(DatasetProcessFunctionMeta(func, tags=default_tags, type='TRANSFORMATION',
                                                                      cell_level=self.cell_level))
        super().__init__(meta)

    def __call__(self, *args, **kwargs) -> 'TransformationFunction':
        self.is_initialized = True
        self.params = kwargs

        for idx, arg in enumerate(args):
            self.params[next(iter([arg.name for arg in self.meta.args.values() if arg.argOrder == idx]))] = arg

        return self

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:

        if self.cell_level:
            actual_params = {k: v for k, v in self.params.items() if k != 'column_name'}

            def apply(row: pd.Series) -> pd.Series:
                row[self.params['column_name']] = self.func(row[self.params['column_name']], **actual_params)
                return row

            return data.apply(apply, axis=1)
        elif self.row_level:
            return data.apply(lambda row: self.func(row, **self.params), axis=1)
        else:
            return self.func(data, **self.params)

    def _should_upload(self) -> bool:
        return self.meta.version is None

    def save(self, local_dir: Path):
        with open(Path(local_dir) / 'data.pkl', 'wb') as f:
            cloudpickle.dump(self, f, protocol=pickle.DEFAULT_PROTOCOL)

    @classmethod
    def _load_meta_locally(cls, local_dir, uuid: str) -> Optional[DatasetProcessFunctionMeta]:
        meta = tests_registry.get_test(uuid)

        if meta is not None:
            return meta

        return super()._load_meta_locally(local_dir, uuid)

    @classmethod
    def load(cls, local_dir: Path, uuid: str, meta: DatasetProcessFunctionMeta):
        _transformation_function: Optional[TransformationFunction]
        if local_dir.exists():
            with open(local_dir / 'data.pkl', 'rb') as f:
                _transformation_function = cloudpickle.load(f)
        else:
            try:
                func = getattr(sys.modules[meta.module], meta.name)

                if inspect.isclass(func) or hasattr(func, 'meta'):
                    _transformation_function = func()
                else:
                    _transformation_function = cls(func)
                    _transformation_function.meta = meta
            except Exception:
                return None

        tests_registry.register(_transformation_function.meta)

        return _transformation_function

    @classmethod
    def _get_meta_class(cls):
        return DatasetProcessFunctionMeta


def transformation_function(_fn: Union[TransformationFunctionType, Type[TransformationFunction]] = None,
                            row_level=True,
                            cell_level=False,
                            name=None,
                            tags: Optional[List[str]] = None):

    def inner(func: Union[TransformationFunctionType, Type[TransformationFunction]]) -> TransformationFunction:
        from giskard.ml_worker.testing.registry.registry import tests_registry

        tests_registry.register(
            DatasetProcessFunctionMeta(func, name=name, tags=default_tags if not tags else (default_tags + tags),
                                       type='TRANSFORMATION', cell_level=cell_level))

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

    return configured_validate_arguments(transformation_fn)
