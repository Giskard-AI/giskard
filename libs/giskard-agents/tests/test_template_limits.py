import tempfile
import time
from pathlib import Path

import pytest
from giskard.agents.templates import (
    MessageTemplate,
    PromptsManager,
    TemplateOutputTooLargeError,
    TemplateRenderTimeoutError,
    TemplateResourceLimitError,
    get_template_limits,
    get_template_policy,
    set_template_limits,
    set_template_policy,
)
from giskard.agents.templates.limits import value_weight
from jinja2.exceptions import SecurityError

NESTED_LOOPS = (
    "{% for i in range(100000) %}{% for j in range(100000) %}{% endfor %}{% endfor %}"
)


def _render(template: str, **kwargs) -> str:
    content = MessageTemplate(role="user", content_template=template).render(**kwargs)
    return content.text or ""


@pytest.fixture(autouse=True)
def strict_with_short_timeout():
    """Render strictly with a short timeout, whatever the environment says."""
    previous_policy = get_template_policy()
    previous_timeout, previous_size = get_template_limits()
    set_template_policy("strict")
    set_template_limits(render_timeout=0.5, max_output_size=2_000_000)
    yield
    set_template_policy(previous_policy)
    set_template_limits(render_timeout=previous_timeout, max_output_size=previous_size)


@pytest.fixture
def prompts_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def test_errors_are_security_errors():
    assert issubclass(TemplateRenderTimeoutError, TemplateResourceLimitError)
    assert issubclass(TemplateOutputTooLargeError, TemplateResourceLimitError)
    assert issubclass(TemplateResourceLimitError, SecurityError)


def test_timeout_stops_nested_empty_loops():
    start = time.monotonic()
    with pytest.raises(TemplateRenderTimeoutError, match="timeout"):
        _render(NESTED_LOOPS)
    assert time.monotonic() - start < 2


async def test_timeout_applies_to_file_templates(prompts_dir):
    (prompts_dir / "loops.j2").write_text(NESTED_LOOPS)
    manager = PromptsManager(default_prompts_path=prompts_dir)
    with pytest.raises(TemplateRenderTimeoutError):
        await manager.render_template("loops.j2")


@pytest.mark.parametrize(
    "template",
    [
        '{{ "x" * 10**9 }}',
        '{{ ["x" * 1000000] * 1000 }}',
        "{{ 2 ** 999999999 }}",
        '{{ "%0999999999d" % 1 }}',
        '{{ "%*d"|format(999999999, 1) }}',
        '{{ "{:>999999999}".format(1) }}',
        '{{ "{:>{w}}".format(1, w=999999999) }}',
        '{{ "x"|center(999999999) }}',
        '{{ "x".ljust(10**9) }}',
        '{{ ("a\\n" * 1000000)|indent(1000) }}',
        '{{ ("\\t" * 1000000).expandtabs(100) }}',
        '{{ ("x" * 1000000)|replace("", "yyyyyyyy") }}',
        '{{ ("x" * 1000000).replace("", "yyyyyyyy") }}',
        '{{ (["x" * 1000000] * 2)|join("") }}',
        '{{ "".join(["x" * 1000000] * 2) }}',
        '{{ range(100000)|map("center", 1000000)|list|length }}',
        "{{ [1]|batch(999999999, 0)|list }}",
        "{{ lipsum(100000, max=1000) }}",
        '{% set ns = namespace(x="ab") %}'
        "{% for i in range(64) %}{% set ns.x = ns.x ~ ns.x %}{% endfor %}",
    ],
)
def test_size_limit_blocks_amplification(template):
    start = time.monotonic()
    with pytest.raises(TemplateOutputTooLargeError):
        _render(template)
    assert time.monotonic() - start < 2


async def test_size_limit_applies_to_file_templates(prompts_dir):
    (prompts_dir / "big.j2").write_text('{{ "x"|center(999999999) }}')
    manager = PromptsManager(default_prompts_path=prompts_dir)
    with pytest.raises(TemplateOutputTooLargeError):
        await manager.render_template("big.j2")


def test_size_limit_applies_to_rendered_output():
    set_template_limits(max_output_size=100)
    with pytest.raises(TemplateOutputTooLargeError, match="output"):
        _render("{{ text }}", text="x" * 101)
    with pytest.raises(TemplateOutputTooLargeError, match="output"):
        _render("{% for i in range(101) %}x{% endfor %}")
    assert _render("{{ text }}", text="x" * 100) == "x" * 100


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        (
            "{% for i in range(3) %}{{ loop.index }}/{{ loop.length }} {% endfor %}",
            "1/3 2/3 3/3 ",
        ),
        ('{{ "order 123456789: %s" % 1 }}', "order 123456789: 1"),
        ('{{ "%5.2f"|format(3.14159) }}', " 3.14"),
        ('{{ "%*d"|format(3, 1) }}', "  1"),
        ('{{ "{:>3}".format(1) }}', "  1"),
        ("{{ [1, 2]|join(',') }}", "1,2"),
        ('{{ "a" ~ "b" }}', "ab"),
        ("{{ 'ab' * 2 }}", "abab"),
        ("{{ 2 ** 10 }}", "1024"),
        ("{{ [5000000, 6000000]|join(',') }}", "5000000,6000000"),
    ],
)
def test_limits_keep_normal_templates_working(template, expected):
    assert _render(template) == expected


def test_permissive_policy_is_not_limited():
    set_template_policy("permissive")
    set_template_limits(max_output_size=10)
    assert _render("{{ 'x' * 20 }}") == "x" * 20


def test_zero_disables_limits():
    set_template_limits(render_timeout=0, max_output_size=0)
    assert _render("{{ 'x' * 3000000 }}") == "x" * 3_000_000


def test_compile_time_constant_folding_is_limited():
    # Jinja folds filters with literal arguments while compiling the template.
    start = time.monotonic()
    with pytest.raises(TemplateOutputTooLargeError):
        MessageTemplate(
            role="user", content_template='{{ "x"|center(999999999) }}'
        ).render()
    assert time.monotonic() - start < 2


def test_set_template_limits_rejects_negative_values():
    with pytest.raises(ValueError):
        set_template_limits(render_timeout=-1)
    with pytest.raises(ValueError):
        set_template_limits(max_output_size=-1)


def test_value_weight_counts_shared_references():
    text = "x" * 100
    assert value_weight(text) == 100
    assert value_weight([text] * 10) == 10 + 10 * 100
    # One per key and value, plus their own weights.
    assert value_weight({"k": [text]}) == 2 + 1 + (1 + 100)
