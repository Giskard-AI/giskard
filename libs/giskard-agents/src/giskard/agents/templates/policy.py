"""Template security policy.

Templates are rendered in a Jinja2 sandbox, which blocks private and internal
Python attributes but still lets a template call any public method of the
objects it receives — including pydantic APIs such as ``parse_file`` (reads
files from disk, optionally unpickling them) or ``model_validate_json``.

That is fine when templates are written by the person running them, which is
the default (``"permissive"``) policy. Services that render templates authored
by untrusted users should enable the ``"strict"`` policy, under which templates
can only *read data*:

- pydantic models expose their fields, computed fields and properties defined
  on the model class; methods and the inherited ``BaseModel`` API are blocked;
- classes and classmethods are never reachable;
- known mutable builtins (lists, dicts, sets) cannot be modified.

The policy is enabled process-wide with :func:`set_template_policy` (or the
``GISKARD_TEMPLATE_POLICY`` environment variable), or for a scope with
:func:`strict_templates`.
"""

import inspect
import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Literal, cast, get_args

from jinja2.sandbox import modifies_known_mutable
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


def _is_model_data(model_cls: type[BaseModel], attr: str) -> bool:
    if attr in model_cls.model_fields or attr in model_cls.model_computed_fields:
        return True
    # Properties declared on the model's own classes (not pydantic's).
    for klass in model_cls.__mro__:
        if klass is BaseModel:
            return False
        if attr in vars(klass):
            return isinstance(vars(klass)[attr], property)
    return False


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
    if isinstance(value, type) or (
        inspect.ismethod(value) and isinstance(value.__self__, type)
    ):
        return False
    if isinstance(obj, BaseModel):
        return not callable(value) and _is_model_data(type(obj), attr)
    return not modifies_known_mutable(obj, attr)
