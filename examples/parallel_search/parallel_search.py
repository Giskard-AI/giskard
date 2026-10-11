# /// script
# requires-python = ">=3.12"
# dependencies = ["giskard-agents>=1.0.4,<2", "mcp>=1.30,<2", "httpx>=0.28.1,<1"]
# ///
"""Run anonymous Parallel Search MCP tools through Giskard's native Tool API."""

import argparse
import asyncio
import importlib
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any
from uuid import uuid4

import httpx
from giskard.agents.tools import Tool

MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "giskard-oss/parallel-search-example"


async def load_tools(session: Any, session_id: str) -> dict[str, Tool]:
    """Adapt the server's search and fetch tools to Giskard Tools.

    Parameters
    ----------
    session : ClientSession
        An initialized MCP session that stays open while tools execute.
    session_id : str
        Stable conversation identifier shared by search and fetch calls.

    Returns
    -------
    dict[str, Tool]
        Search and fetch tools with the server's descriptions and input schemas.
        MCP errors propagate to the caller; structured output is preserved.
    """
    discovered = await session.list_tools()

    def adapt(remote: Any) -> Tool:
        async def call(**arguments: Any) -> Any:
            # Bind the name per tool and reuse one conversation ID for related calls.
            result = await session.call_tool(
                remote.name, {**arguments, "session_id": session_id}
            )
            if result.isError:
                message = "\n".join(
                    block.text for block in result.content if block.type == "text"
                )
                raise RuntimeError(f"{remote.name}: {message}")
            if result.structuredContent is not None:
                return result.structuredContent
            return "\n".join(
                block.text for block in result.content if block.type == "text"
            )

        return Tool(
            name=remote.name,
            description=remote.description or remote.name,
            parameters_schema=remote.inputSchema,
            fn=call,
        )

    tools = {
        remote.name: adapt(remote)
        for remote in discovered.tools
        if remote.name in {"web_search", "web_fetch"}
    }
    if set(tools) != {"web_search", "web_fetch"}:
        raise RuntimeError("The MCP server must expose web_search and web_fetch")
    return tools


@asynccontextmanager
async def parallel_tools() -> AsyncIterator[dict[str, Tool]]:
    """Open an anonymous HTTP MCP session and yield Giskard tools.

    Yields
    ------
    dict[str, Tool]
        Tools usable only inside this context. Each request has a 60-second
        transport timeout and each MCP response a 60-second read timeout.
    """
    # Keep the optional SDK local to this runnable example, not a library dependency.
    client_session = importlib.import_module("mcp").ClientSession
    streamable_http_client = importlib.import_module(
        "mcp.client.streamable_http"
    ).streamable_http_client

    async with (
        httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=60.0) as client,
        streamable_http_client(MCP_URL, http_client=client) as (
            read,
            write,
            _,
        ),
        client_session(
            read, write, read_timeout_seconds=timedelta(seconds=60)
        ) as session,
    ):
        await session.initialize()
        yield await load_tools(session, str(uuid4()))


async def run_example(query: str, urls: list[str]) -> dict[str, Any]:
    """Search the web and optionally fetch pages using native Tool.run.

    Parameters
    ----------
    query : str
        Search objective and keyword query.
    urls : list[str]
        Optional HTTP(S) pages to fetch after searching.

    Returns
    -------
    dict[str, Any]
        Search output and, when requested, fetch output with source excerpts.
    """
    async with parallel_tools() as tools:
        results = {
            "search": json.loads(
                await tools["web_search"].run(
                    {"objective": query, "search_queries": [query]}
                )
            )
        }
        if urls:
            results["fetch"] = json.loads(await tools["web_fetch"].run({"urls": urls}))
        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Search objective, preferably 3–6 words")
    parser.add_argument("--fetch", nargs="+", default=[], metavar="URL")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run_example(args.query, args.fetch)), indent=2))
