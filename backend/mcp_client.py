"""
mcp_client.py — Async MCP client for the StockQuery backend.

All database tool calls are routed through this module to the MCP server
via streamable-HTTP JSON-RPC. The backend never touches SQLite directly.

Flow: LLM tool call → call_mcp_tool() → HTTP JSON-RPC → MCP server → SQLite
"""

import json
import logging
import os

from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# ─── Config ──────────────────────────────────────────────────
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")

log = logging.getLogger(__name__)


async def call_mcp_tool(tool_name: str, arguments: dict):
    """
    Call a tool on the MCP server and return the parsed result.

    - Connects to MCP_SERVER_URL via streamable-HTTP.
    - Sends a JSON-RPC tool call with the given arguments.
    - Returns a Python dict or list parsed from the JSON response.
    - Returns {"error": "..."} on any failure so the LLM can handle it.

    Logging covers the full roundtrip:
        [MCP-CLIENT] Calling <tool> | args: {...}
        [MCP-CLIENT] Response from <tool> | <N> items  (or dict / error)
    """
    log.info(f"[MCP-CLIENT] Calling '{tool_name}' | args: {arguments}")

    try:
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

        # MCP error flag
        if result.isError:
            error_text = str(result.content)
            log.error(f"[MCP-CLIENT] Tool error from '{tool_name}': {error_text}")
            return {"error": error_text}

        # FastMCP 1.27.0 serialises list[dict] as ONE TextContent PER element.
        # We must collect ALL items, not just content[0].
        if not result.content:
            log.warning(f"[MCP-CLIENT] Empty response from '{tool_name}'")
            return []

        parsed_items = []
        for item in result.content:
            raw = item.text if hasattr(item, "text") else ""
            try:
                parsed_items.append(json.loads(raw))
            except (json.JSONDecodeError, TypeError):
                parsed_items.append(raw)

        # If every element is a dict → return as list (tool returned list[dict])
        # If only one element → unwrap scalar / dict return
        if len(parsed_items) == 1:
            result_data = parsed_items[0]
        else:
            result_data = parsed_items

        # Logging summary
        if isinstance(result_data, list):
            log.info(f"[MCP-CLIENT] '{tool_name}' returned {len(result_data)} item(s)")
        elif isinstance(result_data, dict):
            log.info(f"[MCP-CLIENT] '{tool_name}' returned dict: {list(result_data.keys())}")
        else:
            log.info(f"[MCP-CLIENT] '{tool_name}' returned: {result_data!r}")

        return result_data

    except Exception as exc:
        log.error(f"[MCP-CLIENT] Failed to call '{tool_name}': {exc}", exc_info=True)
        return {"error": f"MCP server unreachable or tool failed: {exc}"}
