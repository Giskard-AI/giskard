import functools
import inspect
import sys
from typing import Callable, Optional, List, Union, Type, TypeVar

from giskard.core.validation import configured_validate_arguments
from giskard.ml_worker.testing.registry.giskard_test import GiskardTestMethod, GiskardTest


def test(_fn=None, name=None, tags: Optional[List[str]] = None):
    if sys.version_info >= (3, 10):
        import typing as t
    else:
        import typing_extensions as t
    P = t.ParamSpec("P")
    R = TypeVar("R")

    def inner(original: Union[Callable[P, R], Type[GiskardTest]]) -> Union[
        Callable[P, GiskardTest], GiskardTest, GiskardTestMethod]:
        """
        Declare output as both Callable and GiskardTest so that there's autocompletion
        for GiskardTest's methods as well as the original wrapped function arguments (for __call__)
        """
        from giskard.ml_worker.testing.registry.registry import tests_registry
        tests_registry.register(original, name=name, tags=tags)

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
    _make_all_optional(giskard_test_method)
    _set_return_type(giskard_test_method, GiskardTestMethod)

    return configured_validate_arguments(giskard_test_method)


def _make_all_optional(fn):
    from inspect import signature, Parameter
    sig = signature(fn)
    sig = sig.replace(
        parameters=[Parameter(name=par.name, kind=par.kind, default=None if inspect.Signature.empty else par.default,
                              annotation=Optional[par.annotation])
                    for par in sig.parameters.values()])
    fn.__signature__ = sig


def _set_return_type(fn, return_type):
    from inspect import signature
    sig = signature(fn)
    sig = sig.replace(return_annotation=return_type)
    fn.__signature__ = sig
