import inspect
from typing import Callable, Optional, List, Union, Type

import pandas as pd

from giskard.core.core import CallableMeta
from giskard.ml_worker.core.savable import Savable
from giskard.ml_worker.testing.registry.registry import get_object_uuid, tests_registry

SliceFunctionType = Callable[[pd.Series], bool]

default_tags = ['filter']


class SliceFunction(Savable[SliceFunctionType, CallableMeta]):
    func: SliceFunctionType = None
    row_level: bool = True

    @classmethod
    def _get_name(cls) -> str:
        return 'slices'

    def __init__(self, func: SliceFunctionType, row_level=True):
        self.func = func
        self.row_level = row_level
        test_uuid = get_object_uuid(func)
        meta = tests_registry.get_test(test_uuid)
        if meta is None:
            meta = tests_registry.register(CallableMeta(func, tags=default_tags, type='SLICE'))
        super().__init__(func, meta)

    def __call__(self, row_or_df: Union[pd.Series, pd.DataFrame]):
        return self.func(row_or_df)


def slicing_function(_fn=None, row_level=True, name=None, tags: Optional[List[str]] = None):
    def inner(func: Union[SliceFunctionType, Type[SliceFunction]]) -> SliceFunction:

        from giskard.ml_worker.testing.registry.registry import tests_registry

        tests_registry.register(CallableMeta(func, name=name, tags=default_tags if not tags else (default_tags + tags)))
        if inspect.isclass(func) and issubclass(func, SliceFunction):
            return func
        return SliceFunction(func, row_level)

    if callable(_fn):
        return inner(_fn)
    else:
        return inner
