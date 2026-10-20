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
- classes, classmethods and modules are never reachable, and their
  attributes cannot be read;
- items looked up with ``x[key]`` (or ``x.key`` falling back to an item) are
  checked too: modules, classes and callables stored in containers are
  blocked;
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
from types import BuiltinMethodType, ModuleType
from typing import Any, Literal, cast, get_args
from weakref import WeakKeyDictionary

from jinja2.runtime import LoopContext
from jinja2.runtime import TemplateReference as JinjaTemplateReference
from jinja2.sandbox import modifies_known_mutable
from jinja2.utils import Cycler
from pydantic import BaseModel

TemplatePolicy = Literal["permissive", "strict"]

_POLICY_ENV_VAR = "GISKARD_TEMPLATE_POLICY"


def _validate_policy(policy: str) -> TemplatePolicy:
    if isinstance(policy, str):
        policy = policy.strip().lower()
    if policy not in get_args(TemplatePolicy):
        raise ValueError(
            f"Unknown template policy {policy!r}; expected one of {get_args(TemplatePolicy)}"
        )
    return cast(TemplatePolicy, policy)


# Process-wide default. A ContextVar alone would not do: a value set at startup
# is not inherited by threads started afterwards, which would silently fall
# back to the permissive policy.
_default_policy: TemplatePolicy = _validate_policy(
    os.environ.get(_POLICY_ENV_VAR, "permissive")
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
        templates may come from untrusted users. Case and surrounding
        whitespace are ignored, as for ``GISKARD_TEMPLATE_POLICY``.
    """
    global _default_policy
    _default_policy = _validate_policy(policy)


@contextmanager
def strict_templates() -> Iterator[None]:
    """Render templates with the strict policy within this scope.

    The override is stored in a :class:`~contextvars.ContextVar`, so it
    follows ``await`` and :func:`asyncio.to_thread` (which copies the current
    context), but not a plain :class:`threading.Thread` or
    ``loop.run_in_executor`` started inside the scope: renders there fall
    back to the process-wide policy. Use :func:`set_template_policy` when
    renders may happen in such threads.
    """
    token = _policy_override.set("strict")
    try:
        yield
    finally:
        _policy_override.reset(token)


# Built-in data types whose built-in methods (``str.split``, ``dict.items``, ...)
# templates may call; mutating ones are rejected by ``modifies_known_mutable``.
_DATA_TYPES = (str, bytes, int, float, list, tuple, dict, set, frozenset)
# Jinja runtime helpers whose public methods (and, for ``self``, blocks) are
# part of the template language.
_JINJA_HELPERS = (LoopContext, Cycler, JinjaTemplateReference)
# Values that are never handed to a strict template, nor read from: classes
# expose constructors and class-level state, and modules expose everything
# they import (``os.environ``, ``sys.modules``, ...).
_OPAQUE_TYPES = (type, ModuleType)


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


def _is_opaque(value: Any) -> bool:
    """Whether ``value`` is a class, a classmethod or a module."""
    return isinstance(value, _OPAQUE_TYPES) or isinstance(
        getattr(value, "__self__", None), type
    )


def _is_builtin_data_method(obj: Any, attr: str, value: Any) -> bool:
    """Whether ``value`` is ``obj.attr`` resolving to a data type's own method.

    Subclasses of the data types are accepted (e.g. ``StrEnum`` members), but
    only for methods they inherit unchanged: numpy scalars subclass ``float``
    and ``str`` yet add methods such as ``tofile`` and ``dump`` that write
    files.
    """
    if not isinstance(value, BuiltinMethodType) or value.__self__ is not obj:
        return False
    base = next((t for t in _DATA_TYPES if isinstance(obj, t)), None)
    if base is None:
        return False
    builtin = vars(base).get(attr)
    resolved = next(
        (vars(klass)[attr] for klass in type(obj).__mro__ if attr in vars(klass)),
        None,
    )
    return builtin is not None and resolved is builtin


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
    if isinstance(obj, _OPAQUE_TYPES) or _is_opaque(value):
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
    return _is_builtin_data_method(obj, attr, value)


def is_strictly_safe_item(obj: Any, key: Any, value: Any) -> bool:
    """Decide whether a template may access ``obj[key]`` under the strict policy.

    Item lookups bypass attribute checks, so containers must not hand out
    what an attribute read would refuse.

    Parameters
    ----------
    obj : Any
        The object the item is read from.
    key : Any
        The item key.
    value : Any
        The item value, already resolved.

    Returns
    -------
    bool
        ``True`` when the access is a plain data read.
    """
    if isinstance(obj, _OPAQUE_TYPES) or _is_opaque(value):
        return False
    return not callable(value) or isinstance(obj, _JINJA_HELPERS)
