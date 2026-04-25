"""
mcp_client.py — Managed MCP Client for StockQuery Backend.

This module manages a background MCP server process (stdio) and provides 
access to its tools. The server is spawned as a subprocess.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

log = logging.getLogger(__name__)

# Path to the server script relative to this file
SERVER_SCRIPT = Path(__file__).parent.parent / "mcp_server" / "server.py"

class MCPManager:
    def __init__(self):
        self.session: ClientSession = None
        self.exit_stack = AsyncExitStack()
        self._tools = []

    async def start(self):
        """Spawn the MCP server as a subprocess and initialize the session."""
        log.info(f"[MCP-CLIENT] Starting MCP server subprocess: {SERVER_SCRIPT}")
        
        # Configure the subprocess to run the server script with MCP_TRANSPORT=stdio
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_SCRIPT)],
            env={**os.environ, "MCP_TRANSPORT": "stdio"}
        )

        try:
            # Create the stdio connection and session
            read, write = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            
            # Initialize the session
            await self.session.initialize()
            log.info("[MCP-CLIENT] MCP session initialized successfully.")
            
            # Fetch tools immediately
            await self.refresh_tools()
            
        except Exception as e:
            log.error(f"[MCP-CLIENT] Failed to start MCP server: {e}", exc_info=True)
            await self.stop()
            raise

    async def refresh_tools(self):
        """Fetch the list of tools from the server and store them."""
        if not self.session:
            return
        
        log.info("[MCP-CLIENT] Fetching tools from server...")
        result = await self.session.list_tools()
        
        # Convert MCP Tool objects to OpenAI-compatible function schemas
        self._tools = []
        for tool in result.tools:
            self._tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                }
            })
        log.info(f"[MCP-CLIENT] Loaded {len(self._tools)} tools dynamically.")

    def get_tools(self):
        """Return the list of tool schemas for the LLM."""
        return self._tools

    async def call_tool(self, tool_name: str, arguments: dict):
        """Execute a tool on the server."""
        if not self.session:
            return {"error": "MCP session not initialized"}

        log.info(f"[MCP-CLIENT] Calling '{tool_name}' | args: {arguments}")
        try:
            result = await self.session.call_tool(tool_name, arguments)
            
            if result.isError:
                error_text = str(result.content)
                log.error(f"[MCP-CLIENT] Tool error from '{tool_name}': {error_text}")
                return {"error": error_text}

            # Parse results
            parsed_items = []
            for item in result.content:
                raw = item.text if hasattr(item, "text") else ""
                try:
                    parsed_items.append(json.loads(raw))
                except (json.JSONDecodeError, TypeError):
                    parsed_items.append(raw)

            if len(parsed_items) == 1:
                return parsed_items[0]
            return parsed_items

        except Exception as e:
            log.error(f"[MCP-CLIENT] Failed to call '{tool_name}': {e}")
            return {"error": f"Tool call failed: {e}"}

    async def stop(self):
        """Cleanly shut down the session and subprocess."""
        log.info("[MCP-CLIENT] Stopping MCP server...")
        await self.exit_stack.aclose()
        self.session = None
        self._tools = []

# Global manager instance
mcp_manager = MCPManager()
