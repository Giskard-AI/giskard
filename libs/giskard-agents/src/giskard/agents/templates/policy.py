"""Template security policy.

Templates are rendered in a Jinja2 sandbox, which blocks private and internal
Python attributes but still lets a template call any public method of the
objects it receives — including pydantic APIs such as ``parse_file`` (reads
files from disk, optionally unpickling them) or ``model_validate_json``.

That is fine when templates are written by the person running them, which is
the default (``"permissive"``) policy. Services that render templates authored
by untrusted users should enable the ``"strict"`` policy, under which templates
can only *read data*:

- pydantic models expose their fields (including extra fields), computed fields
  and properties defined on the model's own classes; methods and the inherited
  ``BaseModel`` API are blocked;
- methods of other objects are blocked, except the built-in methods of plain
  data types (``str``, ``list``, ``dict``, ...) and Jinja's loop helpers;
- classes and classmethods are never reachable;
- known mutable builtins (lists, dicts, sets) cannot be modified.

The policy is enabled process-wide with :func:`set_template_policy` (or the
``GISKARD_TEMPLATE_POLICY`` environment variable), or for a scope with
:func:`strict_templates`.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cached_property
from types import BuiltinMethodType
from typing import Any, Literal, cast, get_args
from weakref import WeakKeyDictionary

from jinja2.runtime import LoopContext
from jinja2.sandbox import modifies_known_mutable
from jinja2.utils import Cycler
from pydantic import BaseModel

TemplatePolicy = Literal["permissive", "strict"]

_POLICY_ENV_VAR = "GISKARD_TEMPLATE_POLICY"


def _validate_policy(policy: str) -> TemplatePolicy:
    if policy not in get_args(TemplatePolicy):
        raise ValueError(
            f"Unknown template policy {policy!r}; expected one of {get_args(TemplatePolicy)}"
        )
    return cast(TemplatePolicy, policy)


# Process-wide default. A ContextVar alone would not do: a value set at startup
# is not inherited by threads started afterwards, which would silently fall
# back to the permissive policy.
_default_policy: TemplatePolicy = _validate_policy(
    os.environ.get(_POLICY_ENV_VAR, "permissive").strip().lower()
)
_policy_override: ContextVar[TemplatePolicy | None] = ContextVar(
    "giskard_template_policy", default=None
)


def get_template_policy() -> TemplatePolicy:
    """Return the template policy in effect for the current context."""
    return _policy_override.get() or _default_policy


def set_template_policy(policy: TemplatePolicy) -> None:
    """Set the process-wide template policy.

    Parameters
    ----------
    policy : {"permissive", "strict"}
        ``"strict"`` restricts templates to reading data; use it whenever
        templates may come from untrusted users.
    """
    global _default_policy
    _default_policy = _validate_policy(policy)


@contextmanager
def strict_templates() -> Iterator[None]:
    """Render templates with the strict policy within this scope."""
    token = _policy_override.set("strict")
    try:
        yield
    finally:
        _policy_override.reset(token)


# Built-in data types whose built-in methods (``str.split``, ``dict.items``, ...)
# templates may call; mutating ones are rejected by ``modifies_known_mutable``.
_DATA_TYPES = (str, bytes, int, float, list, tuple, dict, set, frozenset)
# Jinja runtime helpers whose public methods are part of the template language.
_JINJA_HELPERS = (LoopContext, Cycler)


# Weak keys so dynamically created models (e.g. tool argument models) can be
# garbage-collected.
_model_data_cache: WeakKeyDictionary[type[BaseModel], frozenset[str]] = (
    WeakKeyDictionary()
)


def _model_data_attrs(model_cls: type[BaseModel]) -> frozenset[str]:
    """Names of the fields, computed fields and own properties of a model."""
    attrs = _model_data_cache.get(model_cls)
    if attrs is None:
        names: set[str] = set()
        # Walk base-first so a subclass definition overrides its bases'; skip
        # pydantic's own classes.
        for klass in reversed(model_cls.__mro__):
            if klass in BaseModel.__mro__:
                continue
            for name, member in vars(klass).items():
                if isinstance(member, (property, cached_property)):
                    names.add(name)
                else:
                    names.discard(name)
        names.update(model_cls.model_fields, model_cls.model_computed_fields)
        attrs = _model_data_cache[model_cls] = frozenset(names)
    return attrs


def is_strictly_safe_attribute(obj: Any, attr: str, value: Any) -> bool:
    """Decide whether a template may access ``obj.attr`` under the strict policy.

    Parameters
    ----------
    obj : Any
        The object the attribute is read from.
    attr : str
        The attribute name.
    value : Any
        The attribute value, already resolved.

    Returns
    -------
    bool
        ``True`` when the access is a plain data read.
    """
    if isinstance(value, type) or isinstance(getattr(value, "__self__", None), type):
        return False
    if isinstance(obj, BaseModel):
        return not callable(value) and (
            attr in _model_data_attrs(type(obj)) or attr in (obj.model_extra or {})
        )
    if modifies_known_mutable(obj, attr):
        return False
    if not callable(value):
        return True
    if isinstance(obj, _JINJA_HELPERS):
        return True
    return isinstance(value, BuiltinMethodType) and isinstance(obj, _DATA_TYPES)
