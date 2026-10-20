import inspect
import json
from collections.abc import Awaitable, Callable
from functools import wraps
from pathlib import Path
from types import BuiltinMethodType, MethodType
from typing import Any, Literal, Protocol, cast, runtime_checkable

from giskard.llm import chat
from jinja2 import BaseLoader, StrictUndefined, Template, nodes, pass_context
from jinja2.exceptions import TemplateNotFound
from jinja2.ext import Extension
from jinja2.loaders import FileSystemLoader, PrefixLoader
from jinja2.runtime import Context, Markup
from jinja2.sandbox import (
    SandboxedEnvironment,
    SandboxedEscapeFormatter,
    SandboxedFormatter,
)
from jinja2.utils import generate_lorem_ipsum
from jinja2.visitor import NodeTransformer
from pydantic import BaseModel

from .limits import (
    STR_OPERATIONS,
    RenderBudget,
    check_binop,
    check_format_spec,
    check_lipsum,
    check_percent_format,
    check_str_operation,
    check_time,
    current_budget,
    limit_iteration,
    render_budget,
)
from .policy import get_template_policy, is_strictly_safe_attribute


@runtime_checkable
class LLMFormattable(Protocol):
    """Protocol for objects that can format themselves for LLM consumption."""

    def _repr_prompt_(self) -> str:
        """Format the object for LLM consumption.

        Returns
        -------
        str
            The formatted string representation of the object.
        """
        ...


class Trusted(str):
    """A string that is rendered into prompts verbatim, without escaping.

    Prompt templates escape every interpolated value by default (see
    :func:`_finalize_value`). Values wrapped in ``Trusted`` opt out of that
    escaping, and must therefore never be derived from untrusted input.
    """


def _render_value(value: Any) -> str:
    if isinstance(value, LLMFormattable):
        value = value._repr_prompt_()
    elif isinstance(value, BaseModel):
        return json.dumps(value.model_dump(mode="json"), indent=4)
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _finalize_value(value: Any) -> str:
    """Render an interpolated template expression, escaping it by default.

    Prompts embed untrusted data (agent outputs, traces, documents) inside
    pseudo-XML markers such as ``<AGENT ANSWER>...</AGENT ANSWER>``. The
    environment renders prompts with ``autoescape=False``, so unescaped data
    could contain a literal closing marker and inject instructions into the
    judge. Escaping ``&``, ``<`` and ``>`` for every value makes the markers
    unforgeable while keeping the text human- and model-readable; a template
    that genuinely needs raw output opts out with :class:`Trusted` (available
    in templates as the ``trusted`` filter).

    Parameters
    ----------
    value : Any
        The interpolated value. ``None`` renders as an empty string.

    Returns
    -------
    str
        The rendered text, escaped unless the value is :class:`Trusted`.
    """
    text = value if isinstance(value, Trusted) else _escape(_render_value(value))
    if (budget := current_budget()) is not None:
        budget.add_output(text)
    return text


def trusted(value: Any) -> Trusted:
    """Mark a value as safe to render verbatim, bypassing prompt escaping.

    Only use on values that cannot be influenced by untrusted input, such as
    generated output-format instructions.

    Parameters
    ----------
    value : Any
        The trusted value. Rendered like a normal template expression;
        ``None`` renders as an empty string.

    Returns
    -------
    Trusted
        The rendered text, exempt from escaping.
    """
    return value if isinstance(value, Trusted) else Trusted(_render_value(value))


def fence(value: Any) -> Trusted:
    """Escape a value explicitly.

    Kept for backwards compatibility with templates written before escaping
    became the default; :func:`_finalize_value` now escapes every interpolated
    value, so this filter is a no-op in practice.

    Parameters
    ----------
    value : Any
        The (untrusted) value to embed in a prompt. ``None`` renders as an
        empty string.

    Returns
    -------
    Trusted
        The escaped text, marked so it is not escaped a second time.
    """
    return Trusted(_escape(_render_value(value)))


# Internal filters inserted by _LimitTransformer.
_LOOP_FILTER = "_giskard_limit_loop"
_VALUE_FILTER = "_giskard_limit_value"
_TEXT_FILTER = "_giskard_limit_text"

# Filters whose work grows with their integer arguments.
_INT_ARG_FILTERS = frozenset({"batch", "slice"})


class LimitedTemplate(Template):
    """Template whose renders are bounded under the strict policy.

    See :mod:`~giskard.agents.templates.limits` for the limits applied.
    """

    def render(self, *args: Any, **kwargs: Any) -> str:
        with render_budget() as budget:
            return _check_output(budget, super().render(*args, **kwargs))

    async def render_async(self, *args: Any, **kwargs: Any) -> str:
        with render_budget() as budget:
            return _check_output(budget, await super().render_async(*args, **kwargs))


def _check_output(budget: RenderBudget | None, output: str) -> str:
    if budget is not None:
        budget.check_size(len(output), "an output")
    return output


async def _check_awaited(budget: RenderBudget, result: Awaitable[Any]) -> Any:
    return budget.check_value(await result)


def _limit_filter(name: str, func: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a filter so that it is bounded by the render budget.

    Jinja calls filters directly rather than through the sandbox, so each one
    is wrapped. The wrapper keeps the filter's ``pass_*`` and async-variant
    markers.
    """
    lead = 1 if hasattr(func, "jinja_pass_arg") else 0

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        budget = current_budget()
        if budget is None or len(args) <= lead:
            return func(*args, **kwargs)
        value, rest = args[lead], args[lead + 1 :]
        if name == "format":
            check_percent_format(budget, str(value), rest or tuple(kwargs.values()))
        elif name == "join":
            separator = rest[0] if rest else kwargs.get("d", "")
            (value,) = check_str_operation(budget, name, str(separator), (value,), {})
        elif name in STR_OPERATIONS:
            # These filters stringify their input, so weigh its text.
            rest = check_str_operation(budget, name, str(value), rest, kwargs)
        else:
            budget.check_time()
            if name in _INT_ARG_FILTERS:
                budget.check_int_args(*rest, *kwargs.values())
        result = func(*args[:lead], value, *rest, **kwargs)
        if inspect.isawaitable(result):
            return _check_awaited(budget, result)
        return budget.check_value(result)

    return wrapper


# The internal filters below take the context only so that Jinja cannot
# constant-fold them at compile time: they must run on every render.


@pass_context
def _limit_loop(context: Context, iterable: Any) -> Any:
    return limit_iteration(current_budget(), iterable)


@pass_context
def _limit_value(context: Context, value: Any) -> Any:
    if (budget := current_budget()) is not None:
        budget.check_value(value)
    return value


@pass_context
def _limit_text(context: Context, text: str) -> Trusted:
    # Trusted: literal template text is output verbatim, and counted by
    # _finalize_value like any other output.
    return Trusted(text)


class _LimitedFilters(dict[str, Any]):
    """Filter registry wrapping filters as they are registered."""

    def __setitem__(self, name: str, func: Any) -> None:
        super().__setitem__(name, _limit_filter(name, func))


class _LimitedFormatter(SandboxedFormatter):
    """Sandboxed ``str.format`` formatter bounded by the render budget."""

    def format_field(self, value: Any, format_spec: str) -> Any:
        if (budget := current_budget()) is not None:
            check_format_spec(budget, format_spec)
        return super().format_field(value, format_spec)


class _LimitedEscapeFormatter(_LimitedFormatter, SandboxedEscapeFormatter):
    pass


class _LimitTransformer(NodeTransformer):
    """Route loops and concatenations through the render budget.

    A loop with an empty body, a ``~`` concatenation and literal template
    text call no sandbox hook, so they are wrapped in internal filters that
    do.
    """

    def visit_Output(self, node: nodes.Output) -> nodes.Node:
        node = cast(nodes.Output, self.generic_visit(node))
        node.nodes = [
            nodes.Filter(
                nodes.Const(child.data),
                _TEXT_FILTER,
                [],
                [],
                None,
                None,
                lineno=child.lineno,
            )
            if isinstance(child, nodes.TemplateData)
            else child
            for child in node.nodes
        ]
        return node

    def visit_For(self, node: nodes.For) -> nodes.Node:
        node = cast(nodes.For, self.generic_visit(node))
        node.iter = nodes.Filter(
            node.iter, _LOOP_FILTER, [], [], None, None, lineno=node.lineno
        )
        return node

    def visit_Concat(self, node: nodes.Concat) -> nodes.Node:
        node = cast(nodes.Concat, self.generic_visit(node))
        return nodes.Filter(node, _VALUE_FILTER, [], [], None, None, lineno=node.lineno)


class PromptSandboxedEnvironment(SandboxedEnvironment):
    """Sandbox that also enforces the active template policy.

    The policy is read at render time, so environments created before
    :func:`~giskard.agents.templates.policy.set_template_policy` is called
    still honour it. Under the strict policy, compiling and rendering are also
    bounded in time and size (see :mod:`~giskard.agents.templates.limits`).
    """

    template_class = LimitedTemplate
    intercepted_binops = frozenset({"*", "**", "+", "%"})

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.filters = _LimitedFilters(
            (name, _limit_filter(name, func)) for name, func in self.filters.items()
        )
        # Internal filters do their own accounting: register them unwrapped.
        dict.update(
            self.filters,
            {
                _LOOP_FILTER: _limit_loop,
                _VALUE_FILTER: _limit_value,
                _TEXT_FILTER: _limit_text,
            },
        )

    def _parse(
        self, source: str, name: str | None, filename: str | None
    ) -> nodes.Template:
        tree = super()._parse(source, name, filename)
        return cast(nodes.Template, _LimitTransformer().visit(tree))

    def _generate(
        self,
        source: nodes.Template,
        name: str | None,
        filename: str | None,
        defer_init: bool = False,
    ) -> str:
        # Code generation folds constant expressions, calling filters and
        # finalize on literals: bound it like a render.
        with render_budget():
            return super()._generate(source, name, filename, defer_init)

    def is_safe_attribute(self, obj: Any, attr: str, value: Any) -> bool:
        return super().is_safe_attribute(obj, attr, value) and (
            get_template_policy() != "strict"
            or is_strictly_safe_attribute(obj, attr, value)
        )

    def getattr(self, obj: Any, attribute: str) -> Any:
        check_time()
        return super().getattr(obj, attribute)

    def getitem(self, obj: Any, argument: Any) -> Any:
        check_time()
        return super().getitem(obj, argument)

    def call_binop(self, context: Context, operator: str, left: Any, right: Any) -> Any:
        if (budget := current_budget()) is None:
            return super().call_binop(context, operator, left, right)
        check_binop(budget, operator, left, right)
        return budget.check_value(super().call_binop(context, operator, left, right))

    def wrap_str_format(self, value: Any) -> Callable[..., str] | None:
        # Mirrors SandboxedEnvironment.wrap_str_format, with formatters that
        # check each field spec once its nested fields are resolved.
        if not isinstance(
            value, (MethodType, BuiltinMethodType)
        ) or value.__name__ not in ("format", "format_map"):
            return None
        fmt = value.__self__
        if not isinstance(fmt, str):
            return None
        formatter = (
            _LimitedEscapeFormatter(self, escape=fmt.escape)
            if isinstance(fmt, Markup)
            else _LimitedFormatter(self)
        )
        is_format_map = value.__name__ == "format_map"

        @wraps(value)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            if is_format_map:
                if kwargs:
                    raise TypeError("format_map() takes no keyword arguments")
                if len(args) != 1:
                    raise TypeError(
                        f"format_map() takes exactly one argument ({len(args)} given)"
                    )
                kwargs, args = args[0], ()
            return type(fmt)(formatter.vformat(fmt, args, kwargs))

        return wrapper

    def call(
        __self,  # noqa: N805  # mirrors SandboxedEnvironment.call
        __context: Context,
        __obj: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if (budget := current_budget()) is None:
            return super().call(__context, __obj, *args, **kwargs)
        owner = getattr(__obj, "__self__", None)
        if isinstance(owner, str):
            args = check_str_operation(budget, __obj.__name__, owner, args, kwargs)
        else:
            budget.check_time()
            if __obj is generate_lorem_ipsum:
                check_lipsum(budget, args, kwargs)
        return budget.check_value(super().call(__context, __obj, *args, **kwargs))


_inline_env = PromptSandboxedEnvironment(
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    undefined=StrictUndefined,
    autoescape=False,
    finalize=_finalize_value,
)
_inline_env.filters["fence"] = fence
_inline_env.filters["trusted"] = trusted


class MessageExtension(Extension):
    """Custom Jinja2 extension for parsing {% message role %}...{% endmessage %} blocks."""

    tags = {"message"}

    def __init__(self, environment):
        super().__init__(environment)
        if not hasattr(environment, "_collected_messages"):
            environment._collected_messages = []  # pyright: ignore[reportAttributeAccessIssue]

    def parse(self, parser):
        """Parse a {% message role %}...{% endmessage %} block."""
        lineno = next(parser.stream).lineno
        role_node = parser.parse_expression()
        if isinstance(role_node, nodes.Name):
            role_node = nodes.Const(role_node.name)
        body = parser.parse_statements(("name:endmessage",), drop_needle=True)
        call_node = self.call_method("_handle_message", [role_node])

        return nodes.CallBlock(call_node, [], [], body).set_lineno(lineno)

    async def _handle_message(
        self, role: Literal["user", "assistant", "system", "developer"], caller
    ):
        """Handle a message block by rendering its content and storing it."""
        content = (await caller()).strip()
        self.environment._collected_messages.append(chat.message(content, role))  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        return ""


class PromptsLoader(PrefixLoader):
    def get_loader(self, template: str) -> tuple[BaseLoader, str]:
        try:
            prefix, name = template.split(self.delimiter, 1)
        except ValueError:
            prefix = "__default__"
            name = template

        try:
            loader = self.mapping[prefix]
        except KeyError as e:
            raise TemplateNotFound(template) from e

        return loader, name


def create_message_environment(
    loader_mapping: dict[str, Path],
) -> PromptSandboxedEnvironment:
    """Create a Jinja2 environment with MessageExtension."""
    env = PromptSandboxedEnvironment(
        loader=PromptsLoader(
            {
                namespace: FileSystemLoader(path)
                for namespace, path in loader_mapping.items()
            },
            delimiter="::",
        ),
        extensions=[MessageExtension],
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
        autoescape=False,
        enable_async=True,
        finalize=_finalize_value,
    )
    env.filters["fence"] = fence
    env.filters["trusted"] = trusted
    return env
