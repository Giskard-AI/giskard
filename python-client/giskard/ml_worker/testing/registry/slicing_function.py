import inspect
import pickle
import sys
from pathlib import Path
from typing import Callable, Optional, List, Union, Type

import pandas as pd

from giskard.core.core import CallableMeta
from giskard.ml_worker.core.savable import Savable
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry

SlicingFunctionType = Callable[[pd.Series], bool]

default_tags = ['filter']


class SlicingFunction(Savable[SlicingFunctionType, CallableMeta]):
    func: SlicingFunctionType = None
    row_level: bool = True

    @classmethod
    def _get_name(cls) -> str:
        return 'slices'

    def __init__(self, func: SlicingFunctionType, row_level=True):
        self.func = func
        self.row_level = row_level
        test_uuid = get_object_uuid(func)
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            meta = tests_registry.register(CallableMeta(func, tags=default_tags, type='SLICE'))
        super().__init__(func, meta)

    def __call__(self, row_or_df: Union[pd.Series, pd.DataFrame]):
        return self.func(row_or_df)

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
        assert meta is not None, f"Cannot find test function {uuid}"
        return meta

    @classmethod
    def _get_meta_class(cls):
        return CallableMeta


def slicing_function(_fn=None, row_level=True, name=None, tags: Optional[List[str]] = None):
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
