import functools
import inspect
import sys
from typing import Callable, Optional, List, Union, Type, TypeVar

from giskard.core.core import TestFunctionMeta
from giskard.ml_worker.testing.registry.decorators_utils import make_all_optional_or_suite_input, set_return_type
from giskard.ml_worker.testing.registry.giskard_test import GiskardTestMethod, GiskardTest


def test(
    _fn=None,
    name=None,
    tags: Optional[List[str]] = None,
    debug_description: str = "This debugging session opens one by one all the examples that make the test fail.",
):
    if sys.version_info >= (3, 10):
        import typing as t
    else:
        import typing_extensions as t
    P = t.ParamSpec("P")
    R = TypeVar("R")

    def inner(
        original: Union[Callable[P, R], Type[GiskardTest]]
    ) -> Union[Callable[P, GiskardTest], GiskardTest, GiskardTestMethod]:
        """
        Declare output as both Callable and GiskardTest so that there's autocompletion
        for GiskardTest's methods as well as the original wrapped function arguments (for __call__)
        """
        from giskard.ml_worker.testing.registry.registry import tests_registry

        tests_registry.register(
            TestFunctionMeta(original, name=name, tags=tags, debug_description=debug_description, type="TEST")
        )

        if inspect.isclass(original) and issubclass(original, GiskardTest):
            return original

        return _wrap_test_method(original)

    if callable(_fn):
        # in case @test decorator was used without parenthesis
        return functools.wraps(_fn)(inner(_fn))
    else:
        return inner


def _wrap_test_method(original):
    giskard_test_method = functools.wraps(original)(GiskardTestMethod(original))
    make_all_optional_or_suite_input(giskard_test_method)
    set_return_type(giskard_test_method, GiskardTestMethod)
    return giskard_test_method()
