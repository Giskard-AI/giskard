"""Offline coverage for native MCP tool dispatch and session ownership."""

import asyncio
import json
import sys
from contextlib import asynccontextmanager
from datetime import timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from examples.parallel_search import parallel_search as example


def _remote(name):
    return SimpleNamespace(
        name=name,
        description=f"Remote {name}",
        inputSchema={"type": "object", "properties": {"urls": {"type": "array"}}},
    )


def _result(payload=None, text="", error=False):
    return SimpleNamespace(
        isError=error,
        structuredContent=payload,
        content=[SimpleNamespace(type="text", text=text)],
    )


def _session(result):
    return SimpleNamespace(
        list_tools=AsyncMock(
            return_value=SimpleNamespace(
                tools=[_remote("web_search"), _remote("web_fetch"), _remote("other")]
            )
        ),
        call_tool=AsyncMock(return_value=result),
    )


async def test_native_dispatch_preserves_schema_output_and_conversation():
    payload = {"results": [{"url": "https://example.org", "excerpts": ["Evidence"]}]}
    session = _session(_result(payload=payload))
    tools = await example.load_tools(session, "conversation")
    assert set(tools) == {"web_search", "web_fetch"}
    assert tools["web_fetch"].parameters_schema == _remote("web_fetch").inputSchema
    assert tools["web_search"].description == "Remote web_search"
    search = {"objective": "Find evidence", "search_queries": ["find evidence source"]}
    assert json.loads(await tools["web_search"].run(search)) == payload
    assert (
        json.loads(await tools["web_fetch"].run({"urls": ["https://example.org"]}))
        == payload
    )
    assert session.call_tool.call_args_list[0].args == (
        "web_search",
        {**search, "session_id": "conversation"},
    )
    assert session.call_tool.call_args_list[1].args == (
        "web_fetch",
        {"urls": ["https://example.org"], "session_id": "conversation"},
    )
    assert "session_id" not in search


async def test_text_fallback_and_mcp_error():
    session = _session(_result(text='{"results": []}'))
    tools = await example.load_tools(session, "conversation")
    assert await tools["web_search"].run({}) == '{"results": []}'
    session.call_tool.return_value = _result(text="Rate limit exceeded", error=True)
    with pytest.raises(RuntimeError, match="web_fetch: Rate limit exceeded"):
        await tools["web_fetch"].run({"urls": ["https://example.org"]})


async def test_cancellation_and_timeout_propagate():
    session = _session(_result())
    tools = await example.load_tools(session, "conversation")
    for error in [asyncio.CancelledError(), TimeoutError("MCP timeout")]:
        session.call_tool.side_effect = error
        with pytest.raises(type(error)):
            await tools["web_search"].run({})


async def test_missing_required_tool_fails_discovery():
    session = _session(_result())
    session.list_tools.return_value = SimpleNamespace(tools=[_remote("web_search")])
    with pytest.raises(RuntimeError, match="must expose web_search and web_fetch"):
        await example.load_tools(session, "conversation")


async def test_cli_path_searches_then_fetches(monkeypatch):
    session = _session(_result(payload={"results": [{"excerpts": ["Evidence"]}]}))
    tools = await example.load_tools(session, "conversation")

    @asynccontextmanager
    async def opened():
        yield tools

    monkeypatch.setattr(example, "parallel_tools", opened)
    output = await example.run_example("find evidence source", ["https://example.org"])
    assert output["search"]["results"][0]["excerpts"] == ["Evidence"]
    assert output["fetch"] == output["search"]
    assert [c.args[0] for c in session.call_tool.call_args_list] == [
        "web_search",
        "web_fetch",
    ]
    assert set(await example.run_example("find evidence source", [])) == {"search"}


async def test_session_uses_anonymous_endpoint_user_agent_timeout_and_cleanup(
    monkeypatch,
):
    requests = []
    clients = []
    closed = []
    session = _session(_result(payload={"results": []}))
    session.initialize = AsyncMock()
    original_client = httpx.AsyncClient

    def http_client(**kwargs):
        return original_client(
            **kwargs,
            transport=httpx.MockTransport(
                lambda request: (requests.append(request), httpx.Response(200))[1]
            ),
            trust_env=False,
        )

    monkeypatch.setattr(example.httpx, "AsyncClient", http_client)

    @asynccontextmanager
    async def transport(url, *, http_client):
        clients.append(http_client)
        assert http_client.timeout.read == 60.0
        await http_client.post(url, json={"method": "initialize"})
        try:
            yield "read", "write", None
        finally:
            closed.append("transport")

    @asynccontextmanager
    async def client_session(read, write, *, read_timeout_seconds):
        assert (read, write) == ("read", "write")
        assert read_timeout_seconds == timedelta(seconds=60)
        try:
            yield session
        finally:
            closed.append("session")

    mcp = ModuleType("mcp")
    # Populate dynamic module exports without inventing static ModuleType attributes.
    mcp.__dict__["ClientSession"] = client_session
    streamable = ModuleType("mcp.client.streamable_http")
    streamable.__dict__["streamable_http_client"] = transport
    monkeypatch.setitem(sys.modules, "mcp", mcp)
    monkeypatch.setitem(sys.modules, "mcp.client", ModuleType("mcp.client"))
    monkeypatch.setitem(sys.modules, "mcp.client.streamable_http", streamable)
    with pytest.raises(ValueError, match="caller failure"):
        async with example.parallel_tools() as tools:
            assert set(tools) == {"web_search", "web_fetch"}
            session.initialize.assert_awaited_once()
            raise ValueError("caller failure")
    assert str(requests[0].url) == "https://search.parallel.ai/mcp"
    assert requests[0].headers["user-agent"] == "giskard-oss/parallel-search-example"
    assert "authorization" not in requests[0].headers
    assert closed == ["session", "transport"]
    assert clients[0].is_closed
