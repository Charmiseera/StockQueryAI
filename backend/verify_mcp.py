import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'mcp_server', 'server.py')

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=[DB_PATH]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print("Tools available via MCP:")
            for t in tools.tools:
                print(f"- {t.name}: {t.description}")
            
            result = await session.call_tool("query_inventory_db", {"product_name": "Pro"})
            print("\nResult for query_inventory_db('Pro'):")
            print(result)

if __name__ == "__main__":
    asyncio.run(main())
