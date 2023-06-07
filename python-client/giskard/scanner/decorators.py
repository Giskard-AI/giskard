import re
import inspect

from .registry import DetectorRegistry


def detector(name=None, tags=None):
    if inspect.isclass(name):
        # If the decorator is used without arguments, the first argument is the class
        cls = name
        DetectorRegistry.register(_to_snake_case(cls.__name__), cls)
        return cls

    def inner(cls):
        DetectorRegistry.register(name or _to_snake_case(cls.__name__), cls, tags)
        return cls

    return inner


def _to_snake_case(string) -> str:
    s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s).lower()
