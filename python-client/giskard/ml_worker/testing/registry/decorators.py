import inspect
import sys
from typing import Callable, Optional, List, Union, Type, TypeVar

from giskard.ml_worker.testing.registry.giskard_test import GiskardTestMethod, GiskardTest


def test(_fn=None, name=None, tags: Optional[List[str]] = None):
    if sys.version_info >= (3, 10):
        import typing as t
    else:
        import typing_extensions as t
    P = t.ParamSpec("P")
    R = TypeVar("R")

    def inner(func: Union[Callable[P, R], Type[GiskardTest]]) \
            -> Union[Callable[P, GiskardTest], GiskardTest, GiskardTestMethod]:
        """
        Declare output as both Callable and GiskardTest so that there's autocompletion
        for GiskardTest's methods as well as the original wrapped function arguments (for __call__)
        """
        from giskard.ml_worker.testing.registry.registry import tests_registry
        tests_registry.register(func, name=name, tags=tags)
        if inspect.isclass(func) and issubclass(func, GiskardTest):
            return func
        return GiskardTestMethod(func)

    if callable(_fn):
        return inner(_fn)
    else:
        return inner
