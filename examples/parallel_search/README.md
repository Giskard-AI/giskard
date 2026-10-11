# Parallel Search MCP tools

Use free web search and page fetching through Giskard's native `Tool.run` with
[Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp).
Anonymous search uses Fast mode. No Parallel account, API key or LLM provider is
needed for this example; the free endpoint has rate limits.

From the repository root, with Python 3.12+ and [uv](https://docs.astral.sh/uv/):

```bash
uv run --script examples/parallel_search/parallel_search.py \
  "Giskard agent evaluation checks" --fetch https://docs.giskard.ai/oss/checks
```

`uv` installs the script's declared dependencies in an isolated environment. The
example discovers `web_search` and `web_fetch` over Streamable HTTP, preserves
their input schemas, and executes them through Giskard tools. The printed JSON
contains source URLs and excerpts. Search and fetch share one conversation ID.
The example makes live network calls only when run explicitly. Importing it and
the adapter tests in `make test-examples` are offline.

`parallel_tools()` manages the HTTP client and MCP session. Execute tools within
its `async with` block; they cannot be used after it closes. MCP errors propagate
to the caller, as do cancellation and timeouts. This example directly dispatches
tools; it does not select a model or generate an LLM answer.
