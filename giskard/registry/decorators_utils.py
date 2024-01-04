import inspect
from typing import Optional, Union, Callable


def make_all_optional_or_suite_input(fn: Callable):
    from inspect import signature, Parameter
    from giskard.core.suite import SuiteInput

    sig = signature(fn)
    sig = sig.replace(
        parameters=[
            Parameter(
                name=par.name,
                kind=par.kind,
                default=None if par.default == inspect.Signature.empty else par.default,
                annotation=Optional[Union[SuiteInput, par.annotation]],
            )
            for par in sig.parameters.values()
        ]
    )
    fn.__signature__ = sig

    fn.__annotations__ = {k: Optional[Union[SuiteInput, v]] for k, v in fn.__annotations__.items()}


def set_return_type(fn: Callable, return_type: type):
    from inspect import signature

    sig = signature(fn)
    sig = sig.replace(return_annotation=return_type)
    fn.__signature__ = sig

    annotations = fn.__annotations__.copy()
    annotations["return"] = return_type
    fn.__annotations__ = annotations


def validate_arg_type(fn: Callable, pos: int, arg_type: type):
    from inspect import signature

    sig = signature(fn)
    if len(sig.parameters) <= pos:
        raise TypeError(f"Required arg {pos} of {fn.__name__} to be {arg_type}, but none was defined")
    elif list(sig.parameters.values())[0].annotation not in [inspect._empty, arg_type]:
        raise TypeError(
            f"Required arg {pos} of {fn.__name__} to be {arg_type}, but {list(sig.parameters.values())[0].annotation} was defined"
        )


def drop_arg(fn: Callable, pos: int):
    from inspect import signature

    sig = signature(fn)
    if len(sig.parameters) <= pos:
        return

    sig = sig.replace(parameters=[par for idx, par in enumerate(sig.parameters.values()) if idx != pos])
    fn.__signature__ = sig

    fn.__annotations__ = {k: v for k, v in fn.__annotations__.items() if k in sig.parameters or k == "return"}


def insert_arg(fn: Callable, pos: int, param: inspect.Parameter):
    from inspect import signature

    sig = signature(fn)
    parameters = [par for par in sig.parameters.values()]
    parameters.insert(pos, param)

    sig = sig.replace(parameters=parameters)
    fn.__signature__ = sig

    fn.__annotations__ = {k: v for k, v in fn.__annotations__.items() if k in sig.parameters or k == "return"}
