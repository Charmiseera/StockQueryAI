"""
main.py — StockQuery AI FastAPI Backend (Nebius / Llama-3.3-70B)
Uses OpenAI-compatible function calling to query the SQLite inventory.
No MCP subprocess — tools are executed directly in Python.
"""

import os
import json
import asyncio
import sqlite3
from pathlib import Path

from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# ─── Config ──────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
DB_PATH = str(Path(__file__).parent.parent / "mcp_server" / "inventory.db")
MODEL   = "meta-llama/Llama-3.3-70B-Instruct"

if not NEBIUS_API_KEY or NEBIUS_API_KEY == "your-nebius-api-key-here":
    print("[WARN] NEBIUS_API_KEY not set. Add it to .env before querying.")

# ─── Nebius OpenAI-compatible client ─────────────────────────
def get_client() -> OpenAI:
    return OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=NEBIUS_API_KEY,
    )

# ─── FastAPI App ─────────────────────────────────────────────
app = FastAPI(
    title="StockQuery AI",
    description="Natural language inventory query agent powered by Llama-3.3-70B + Nebius",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic Models ─────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    tool_used: str | None
    data: list | None


# ─── SQLite Tool Implementations ─────────────────────────────
def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def _rows(cursor_rows) -> list[dict]:
    return [dict(r) for r in cursor_rows]

def query_inventory_db(product_name: str) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE name LIKE ? ORDER BY name",
        (f"%{product_name}%",)
    ).fetchall()
    conn.close()
    return _rows(rows)

def get_product_details(product_id: int) -> dict:
    conn = _conn()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}

def get_low_stock_items(threshold: int = 10) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE stock < ? ORDER BY stock ASC",
        (threshold,)
    ).fetchall()
    conn.close()
    return _rows(rows)

def get_all_categories() -> list[str]:
    conn = _conn()
    rows = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    conn.close()
    return [r["category"] for r in rows]

def get_products_by_category(category: str) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE category LIKE ? ORDER BY name",
        (category,)
    ).fetchall()
    conn.close()
    return _rows(rows)


# ─── Tool Dispatcher ─────────────────────────────────────────
TOOL_FN_MAP = {
    "query_inventory_db":    query_inventory_db,
    "get_product_details":   get_product_details,
    "get_low_stock_items":   get_low_stock_items,
    "get_all_categories":    get_all_categories,
    "get_products_by_category": get_products_by_category,
}

def execute_tool(name: str, arguments: dict):
    fn = TOOL_FN_MAP.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    return fn(**arguments)


# ─── OpenAI Tool Schemas ──────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_inventory_db",
            "description": "Search inventory for products whose name contains the given string. Use when user asks about a specific product by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "The product name or partial name to search for."}
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get full details of a single product by its numeric ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "The numeric product ID."}
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_stock_items",
            "description": "Return all products whose stock is below the given threshold. Use for restocking alerts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {"type": "integer", "description": "Stock threshold. Default is 10.", "default": 10}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_categories",
            "description": "Return a list of all distinct product categories in the inventory.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_products_by_category",
            "description": "Return all products in a specific category. Use when user asks to browse a category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "The category name to filter by."}
                },
                "required": ["category"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are StockQuery AI, an intelligent inventory assistant. "
    "You have access to tools that query a real SQLite inventory database. "
    "Always use a tool to retrieve real data before answering. "
    "Be concise and helpful. Include stock quantities and prices when listing products. "
    "If no results are found, say so clearly."
)


# ─── Agentic Loop (Tool Use) ──────────────────────────────────
async def run_query(question: str) -> QueryResponse:
    client = get_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": [{"type": "text", "text": question}]},
    ]

    tool_used   = None
    data_result = None
    max_turns   = 5  # Safety cap on tool call rounds

    def _llm_call():
        return client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

    loop = asyncio.get_event_loop()

    for _ in range(max_turns):
        response = await loop.run_in_executor(None, _llm_call)
        msg = response.choices[0].message

        # No tool call — final answer
        if not msg.tool_calls:
            return QueryResponse(
                answer=msg.content or "No response generated.",
                tool_used=tool_used,
                data=data_result if isinstance(data_result, list) else None,
            )

        # Append assistant message with tool calls
        messages.append(msg)

        # Execute each tool call
        for tc in msg.tool_calls:
            tool_used = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
                result = execute_tool(tool_used, args)
                # Store list results for the frontend table
                if isinstance(result, list) and result:
                    data_result = result
                elif isinstance(result, dict) and result:
                    data_result = [result]
            except (json.JSONDecodeError, TypeError) as e:
                result = {"error": str(e)}

            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      json.dumps(result, default=str),
            })

    return QueryResponse(
        answer="I was unable to complete the query after multiple attempts.",
        tool_used=tool_used,
        data=None,
    )


# ─── Endpoints ───────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "StockQuery AI", "model": MODEL}


@app.post("/query", response_model=QueryResponse)
async def query_inventory(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not NEBIUS_API_KEY or NEBIUS_API_KEY == "your-nebius-api-key-here":
        raise HTTPException(
            status_code=503,
            detail="NEBIUS_API_KEY not configured. Add it to your .env file."
        )

    try:
        return await run_query(request.question.strip())
    except Exception as e:
        err = str(e)
        if "401" in err or "Unauthorized" in err:
            raise HTTPException(status_code=401, detail="Invalid Nebius API key.")
        if "429" in err:
            raise HTTPException(status_code=429, detail="Rate limit reached. Please wait and retry.")
        raise HTTPException(status_code=500, detail=f"Query failed: {err}")
