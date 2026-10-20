"""Resource limits for rendering templates under the strict policy.

The Jinja2 sandbox stops templates from reaching dangerous Python APIs, but
not from exhausting resources: ``{{ "x" * 10**10 }}``, nested loops over
``range(100000)`` or ``"x"|center(10**9)`` can freeze or crash the process
rendering them. When the ``"strict"`` template policy is active (see
:mod:`~giskard.agents.templates.policy`), compiling and rendering a template
is therefore bounded by:

- a **render timeout**, in seconds (``GISKARD_TEMPLATE_RENDER_TIMEOUT``,
  default ``5``). The deadline is checked cooperatively on every loop
  iteration, call, filter, attribute access, operator and output, so it
  applies equally to sync and async renders and never leaves a runaway render
  running in a background thread;
- a **maximum size**, in characters, of the rendered output and of every
  value the template computes (``GISKARD_TEMPLATE_MAX_OUTPUT_SIZE``, default
  ``2_000_000``). Operations that amplify their input (``*``, ``**``, ``+``,
  ``%``, padding, formatting, ``replace``, ``join``) are checked *before*
  they allocate, and the values a render computes may not add up to more than
  ten times the limit.

Setting either value to ``0`` disables that limit. Templates rendered under
the default ``"permissive"`` policy are written by trusted authors and are not
limited.

These limits are a best-effort guard against accidental and malicious
blow-ups, not a hard memory bound: services rendering untrusted templates at
scale should also run them in a memory-limited process.
"""

import os
import re
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from jinja2.exceptions import SecurityError

from .policy import get_template_policy

_TIMEOUT_ENV_VAR = "GISKARD_TEMPLATE_RENDER_TIMEOUT"
_MAX_SIZE_ENV_VAR = "GISKARD_TEMPLATE_MAX_OUTPUT_SIZE"

DEFAULT_RENDER_TIMEOUT = 5.0
DEFAULT_MAX_OUTPUT_SIZE = 2_000_000

# The values computed during a render may add up to this many times the
# maximum output size. Bounds lazy pipelines such as
# ``range(100000)|map("center", 1000000)|list`` where each value is in bounds.
_ALLOCATION_RATIO = 10

# Width and precision of a printf-style conversion: "%-10.3f", "%(name)*s"...
_PERCENT_SPEC = re.compile(r"%(?:\([^)]*\))?[#0\- +]*(\d+|\*)?(?:\.(\d+|\*))?")
_DIGITS = re.compile(r"\d+")

# String methods and filters whose output size grows with their integer
# arguments. Other integers (offsets, counts, compared values) are left alone.
_PADDING_OPERATIONS = frozenset({"center", "ljust", "rjust", "zfill"})

# String methods and filters checked by check_str_operation.
STR_OPERATIONS = _PADDING_OPERATIONS | {
    "expandtabs",
    "indent",
    "join",
    "replace",
    "wordwrap",
}


class TemplateResourceLimitError(SecurityError):
    """Raised when compiling or rendering a template exceeds a resource limit."""


class TemplateRenderTimeoutError(TemplateResourceLimitError):
    """Raised when rendering a template takes longer than the render timeout."""


class TemplateOutputTooLargeError(TemplateResourceLimitError):
    """Raised when a template produces an output or value above the size limit."""


def _read_env(name: str, default: float, cast: type[float] | type[int]) -> Any:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = cast(raw)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {raw!r}") from None
    if value < 0:
        raise ValueError(f"{name} must be positive, or 0 to disable; got {raw!r}")
    return value


# Process-wide, like the template policy, so that threads started after
# set_template_limits() is called honour it.
_render_timeout: float = _read_env(_TIMEOUT_ENV_VAR, DEFAULT_RENDER_TIMEOUT, float)
_max_output_size: int = _read_env(_MAX_SIZE_ENV_VAR, DEFAULT_MAX_OUTPUT_SIZE, int)


def get_template_limits() -> tuple[float, int]:
    """Return the limits applied to templates rendered under the strict policy.

    Returns
    -------
    tuple[float, int]
        The render timeout in seconds and the maximum output size in
        characters. ``0`` means the limit is disabled.
    """
    return _render_timeout, _max_output_size


def set_template_limits(
    *, render_timeout: float | None = None, max_output_size: int | None = None
) -> None:
    """Set the process-wide limits applied to templates under the strict policy.

    Parameters
    ----------
    render_timeout : float, optional
        Maximum duration of a render, in seconds; ``0`` disables the timeout.
        Left unchanged when omitted.
    max_output_size : int, optional
        Maximum size, in characters, of the rendered output and of every value
        the template computes; ``0`` disables the cap. Left unchanged when
        omitted.
    """
    global _render_timeout, _max_output_size
    if render_timeout is not None:
        if render_timeout < 0:
            raise ValueError("render_timeout must be positive, or 0 to disable")
        _render_timeout = render_timeout
    if max_output_size is not None:
        if max_output_size < 0:
            raise ValueError("max_output_size must be positive, or 0 to disable")
        _max_output_size = max_output_size


def value_weight(value: Any) -> int:
    """Estimate the size of a value once rendered as text.

    Containers count every reference to an item, so ``[s] * 1000`` weighs a
    thousand times ``s`` even though the list only holds one string.

    Parameters
    ----------
    value : Any
        The value to weigh.

    Returns
    -------
    int
        Approximately the length of ``str(value)``.
    """
    if isinstance(value, (str, bytes)):
        return len(value)
    memo: dict[int, int] = {}

    def weigh(item: Any) -> int:
        if isinstance(item, (str, bytes)):
            return len(item)
        if not isinstance(item, (list, tuple, set, frozenset, dict)):
            return 1
        key = id(item)
        if key not in memo:
            memo[key] = 0  # Guards against reference cycles.
            if isinstance(item, dict):
                children = [w for kv in item.items() for w in map(weigh, kv)]
            else:
                children = [weigh(child) for child in item]
            memo[key] = len(children) + sum(children)
        return memo[key]

    return weigh(value)


@dataclass
class RenderBudget:
    """Resources left to the render in progress."""

    deadline: float | None
    max_size: int | None
    output_size: int = 0
    allocated: int = 0

    def check_time(self) -> None:
        """Raise if the render deadline has passed."""
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise TemplateRenderTimeoutError(
                f"Template rendering exceeded the {_render_timeout:g}s timeout"
                f" (set {_TIMEOUT_ENV_VAR} to change it)."
            )

    def check_size(self, size: int, what: str = "a value") -> None:
        """Raise if ``size`` is above the size limit."""
        if self.max_size is not None and size > self.max_size:
            raise TemplateOutputTooLargeError(
                f"Template produced {what} of size {size}, above the limit of"
                f" {self.max_size} (set {_MAX_SIZE_ENV_VAR} to change it)."
            )

    def check_int_args(self, *args: Any) -> None:
        """Raise if an integer argument is above the size limit.

        Used for operations whose output size grows with an integer argument,
        such as padding widths or ``lipsum`` paragraph counts.
        """
        for arg in args:
            if isinstance(arg, tuple):
                self.check_int_args(*arg)
            elif isinstance(arg, int) and not isinstance(arg, bool):
                self.check_size(arg, "an integer argument")

    def check_value(self, value: Any) -> Any:
        """Check a value computed by the template and return it unchanged."""
        self.check_time()
        if self.max_size is not None:
            weight = value_weight(value)
            self.check_size(weight)
            self.allocated += weight
            if self.allocated > self.max_size * _ALLOCATION_RATIO:
                raise TemplateOutputTooLargeError(
                    f"Template computed values adding up to more than"
                    f" {_ALLOCATION_RATIO} times the size limit of"
                    f" {self.max_size} (set {_MAX_SIZE_ENV_VAR} to change it)."
                )
        return value

    def add_output(self, text: str) -> None:
        """Account for a chunk of rendered output."""
        self.check_time()
        self.output_size += len(text)
        self.check_size(self.output_size, "an output")


_budget: ContextVar[RenderBudget | None] = ContextVar(
    "giskard_template_budget", default=None
)


def current_budget() -> RenderBudget | None:
    """Return the budget of the render in progress, if it is limited."""
    return _budget.get()


def check_time() -> None:
    """Raise if the render in progress, if limited, has passed its deadline."""
    if (budget := _budget.get()) is not None:
        budget.check_time()


@contextmanager
def render_budget() -> Iterator[RenderBudget | None]:
    """Bound the compilations and renders made within this scope.

    Yields ``None``, leaving the scope unbounded, unless the strict policy is
    active. Nested scopes (includes, imports, renders from within a render)
    share the outermost budget, so the limits apply to the whole render.
    """
    existing = _budget.get()
    if existing is not None or get_template_policy() != "strict":
        yield existing
        return
    budget = RenderBudget(
        deadline=time.monotonic() + _render_timeout if _render_timeout else None,
        max_size=_max_output_size or None,
    )
    token = _budget.set(budget)
    try:
        yield budget
    finally:
        _budget.reset(token)


def check_binop(budget: RenderBudget, operator: str, left: Any, right: Any) -> None:
    """Raise if a binary operation would produce a value above the size limit.

    Parameters
    ----------
    budget : RenderBudget
        The budget of the render in progress.
    operator : str
        The Jinja operator symbol (``"*"``, ``"**"``, ``"+"`` or ``"%"``).
    left, right : Any
        The operands.
    """
    budget.check_time()
    sequences = (str, bytes, list, tuple)
    if operator == "*":
        if isinstance(left, int) and isinstance(right, int):
            # Repeated squaring would grow integers without bound.
            budget.check_size((left.bit_length() + right.bit_length()) // 8)
        for seq, count in ((left, right), (right, left)):
            if isinstance(seq, sequences) and isinstance(count, int):
                budget.check_size(value_weight(seq) * count)
    elif operator == "**":
        # Floats overflow on their own; integers would grow without bound,
        # except for bases whose powers stay within -1..1.
        if (
            isinstance(left, int)
            and isinstance(right, int)
            and right > 0
            and abs(left) > 1
        ):
            budget.check_size(left.bit_length() * right // 8)
    elif operator == "+":
        if isinstance(left, sequences) and isinstance(right, sequences):
            budget.check_size(value_weight(left) + value_weight(right))
    elif operator == "%" and isinstance(left, str):
        check_percent_format(budget, left, right)


def check_percent_format(budget: RenderBudget, fmt: str, args: Any) -> None:
    """Raise if a printf-style format could pad beyond the size limit.

    Widths and precisions come from the format string or, with ``*``, from
    the arguments.
    """
    star = False
    for spec in _PERCENT_SPEC.finditer(fmt):
        for number in spec.groups():
            if number == "*":
                star = True
            elif number:
                budget.check_int_args(int(number))
    if star:
        budget.check_int_args(args)


def check_format_spec(budget: RenderBudget, spec: str) -> None:
    """Raise if a resolved ``str.format`` field spec could pad beyond the limit.

    Nested fields such as ``{:>{width}}`` are already substituted in ``spec``.
    """
    budget.check_int_args(*(int(n) for n in _DIGITS.findall(spec)))


def _arg(args: tuple[Any, ...], kwargs: dict[str, Any], index: int, name: str) -> Any:
    if len(args) > index:
        return args[index]
    return kwargs.get(name)


def check_str_operation(
    budget: RenderBudget,
    name: str,
    text: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[Any, ...]:
    """Raise if a string method or filter would produce a value above the limit.

    Parameters
    ----------
    budget : RenderBudget
        The budget of the render in progress.
    name : str
        The method or filter name, e.g. ``"replace"``.
    text : str
        The string operated on (the separator for ``join``).
    args : tuple
        The positional arguments, after ``text``.
    kwargs : dict
        The keyword arguments.

    Returns
    -------
    tuple
        The positional arguments to call the operation with. ``join`` may
        consume an iterator to weigh it, in which case the items are returned
        as a list.
    """
    budget.check_time()
    if name in _PADDING_OPERATIONS:
        budget.check_int_args(*args, *kwargs.values())
    if name == "replace":
        old, new = _arg(args, kwargs, 0, "old"), _arg(args, kwargs, 1, "new")
        if isinstance(old, str) and isinstance(new, str):
            count = text.count(old) if old else len(text) + 1
            limit = _arg(args, kwargs, 2, "count")
            if isinstance(limit, int) and limit >= 0:
                count = min(count, limit)
            budget.check_size(len(text) + count * max(len(new) - len(old), 0))
    elif name == "expandtabs":
        tabsize = _arg(args, kwargs, 0, "tabsize")
        tabsize = tabsize if isinstance(tabsize, int) else 8
        budget.check_size(len(text) + text.count("\t") * tabsize)
    elif name == "wordwrap":
        width = _arg(args, kwargs, 0, "width")
        width = width if isinstance(width, int) and width > 0 else 79
        wrapstring = _arg(args, kwargs, 2, "wrapstring")
        wrapstring = wrapstring if isinstance(wrapstring, str) else "\n"
        # Two consecutive wrapped lines hold more than ``width`` characters.
        lines = 2 * len(text) // width + text.count("\n") + 1
        budget.check_size(len(text) + lines * len(wrapstring))
    elif name == "indent":
        width = _arg(args, kwargs, 0, "width")
        width = len(width) if isinstance(width, str) else width
        if isinstance(width, int):
            budget.check_size(len(text) + (text.count("\n") + 1) * width)
    elif name == "join" and args and not isinstance(args[0], str):
        items = args[0]
        if hasattr(items, "__iter__") and not isinstance(items, (list, tuple)):
            items = list(items)
        if isinstance(items, (list, tuple)):
            budget.check_size(value_weight(items) + len(text) * len(items))
            args = (items, *args[1:])
    return args


def check_lipsum(
    budget: RenderBudget, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> None:
    """Raise if ``lipsum(n, html, min, max)`` could exceed the size limit."""
    budget.check_int_args(*args, *kwargs.values())
    paragraphs = _arg(args, kwargs, 0, "n")
    words = _arg(args, kwargs, 3, "max")
    paragraphs = paragraphs if isinstance(paragraphs, int) else 5
    words = words if isinstance(words, int) else 100
    budget.check_size(paragraphs * words)


def limit_iteration(budget: RenderBudget | None, iterable: Any) -> Any:
    """Check the render deadline on every item of a ``{% for %}`` loop."""
    if budget is None or not hasattr(iterable, "__iter__"):
        return iterable
    return _checked_iter(budget, iterable)


def _checked_iter(budget: RenderBudget, iterable: Any) -> Iterator[Any]:
    for item in iterable:
        budget.check_time()
        yield item
