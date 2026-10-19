from datetime import datetime
from functools import cached_property
from pathlib import Path

import pytest
from giskard.agents.templates import (
    MessageTemplate,
    PromptsManager,
    get_template_policy,
    set_template_policy,
    strict_templates,
)
from jinja2.exceptions import SecurityError
from pydantic import BaseModel, ConfigDict, computed_field


class Item(BaseModel):
    name: str

    @property
    def shout(self) -> str:
        return self.name.upper()

    @computed_field
    @property
    def size(self) -> int:
        return len(self.name)

    def greet(self) -> str:
        return f"hello {self.name}"


class Bag(BaseModel):
    items: list[Item]

    @property
    def first(self) -> Item:
        return self.items[0]


def _render(template: str, **kwargs) -> str:
    content = MessageTemplate(role="user", content_template=template).render(**kwargs)
    return content.text or ""


@pytest.fixture(autouse=True)
def permissive_default():
    """Isolate tests from GISKARD_TEMPLATE_POLICY in the environment."""
    previous = get_template_policy()
    set_template_policy("permissive")
    yield
    set_template_policy(previous)


@pytest.fixture
def bag() -> Bag:
    return Bag(items=[Item(name="apple"), Item(name="pear")])


@pytest.fixture
def secret_file(tmp_path) -> Path:
    path = tmp_path / "secret.json"
    path.write_text('{"items": [{"name": "leaked"}]}')
    return path


class Rich(BaseModel):
    model_config = ConfigDict(extra="allow")

    path: Path
    ts: datetime

    @cached_property
    def cached(self) -> int:
        return 3


@pytest.fixture
def rich(secret_file) -> Rich:
    return Rich.model_validate(
        {"path": secret_file, "ts": datetime(2020, 1, 1), "note": "extra"}
    )


def test_permissive_policy_keeps_method_calls(bag, secret_file):
    assert _render("{{ bag.first.greet() }}", bag=bag) == "hello apple"
    assert "leaked" in _render(
        "{{ bag.parse_file(path).first.name }}", bag=bag, path=str(secret_file)
    )


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("{{ bag.items[1].name }}", "pear"),
        ("{{ bag.first.shout }}", "APPLE"),
        ("{{ bag.first.size }}", "5"),
        (
            "{% for i in bag.items %}{{ loop.index }}:{{ i.name }} {% endfor %}",
            "1:apple 2:pear ",
        ),
        ("{{ bag.items | map(attribute='name') | join(',') }}", "apple,pear"),
        ("{{ 'a,b'.split(',') | length }}", "2"),
        ("{{ {'k': 'v'}.items() | list | length }}", "1"),
        ("{{ rich.note }}", "extra"),
        ("{{ rich.cached }}", "3"),
        ("{{ rich.path.name }}", "secret.json"),
        ("{{ rich.ts.year }}", "2020"),
        ("{% for x in [1, 2] %}{{ loop.cycle('a', 'b') }}{% endfor %}", "ab"),
    ],
)
def test_strict_policy_allows_data_reads(bag, rich, template, expected):
    with strict_templates():
        assert _render(template, bag=bag, rich=rich) == expected


@pytest.mark.parametrize(
    "template",
    [
        "{{ bag.parse_file(path) }}",
        "{{ bag.parse_raw('{}') }}",
        "{{ bag.model_validate_json('{}') }}",
        "{{ bag.model_construct() }}",
        "{{ bag.model_copy() }}",
        "{{ bag.model_dump() }}",
        "{{ bag.schema_json() }}",
        "{{ bag.first.greet() }}",
        "{{ bag.items.append(1) }}",
        "{{ {}.update(a=1) }}",
        "{{ rich.path.read_text() }}",
        "{{ rich.path.write_text('x') }}",
        "{{ rich.ts.now() }}",
        "{{ {}.fromkeys('ab') }}",
    ],
)
def test_strict_policy_blocks_method_calls(bag, rich, secret_file, template):
    with strict_templates(), pytest.raises(SecurityError):
        _render(template, bag=bag, rich=rich, path=str(secret_file))


async def test_strict_policy_applies_to_file_templates(bag, secret_file, tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "attack.j2").write_text("{{ bag.parse_file(path) }}")
    manager = PromptsManager(default_prompts_path=prompts)
    with strict_templates(), pytest.raises(SecurityError):
        await manager.render_template(
            "attack.j2", {"bag": bag, "path": str(secret_file)}
        )


def test_strict_templates_scope_is_restored(bag):
    with strict_templates():
        assert get_template_policy() == "strict"
    assert get_template_policy() == "permissive"
    assert _render("{{ bag.first.greet() }}", bag=bag) == "hello apple"


def test_set_template_policy_is_process_wide(bag):
    set_template_policy("strict")
    with pytest.raises(SecurityError):
        _render("{{ bag.first.greet() }}", bag=bag)


def test_set_template_policy_rejects_unknown_value():
    with pytest.raises(ValueError, match="Unknown template policy"):
        set_template_policy("paranoid")  # pyright: ignore[reportArgumentType]
