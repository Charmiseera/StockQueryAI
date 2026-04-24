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
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

# ─── Config ──────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
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

class TTSRequest(BaseModel):
    text: str

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

def search_inventory(
    name: str = None,
    category: str = None,
    max_price: float = None,
    min_price: float = None,
    stock_threshold: int = None,
    sort_by: str = None
) -> list[dict]:
    """Search inventory with multiple filters and sorting."""
    conn = _conn()
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if stock_threshold is not None:
        query += " AND stock <= ?"
        params.append(stock_threshold)

    if sort_by == "price_asc":
        query += " ORDER BY price ASC"
    elif sort_by == "price_desc":
        query += " ORDER BY price DESC"
    elif sort_by == "stock_asc":
        query += " ORDER BY stock ASC"
    elif sort_by == "stock_desc":
        query += " ORDER BY stock DESC"
    else:
        query += " ORDER BY name ASC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return _rows(rows)

def get_inventory_analytics() -> dict:
    """Get high-level statistics about the entire inventory."""
    conn = _conn()
    stats = conn.execute("""
        SELECT 
            COUNT(*) as total_products,
            SUM(stock) as total_items,
            ROUND(SUM(price * stock), 2) as total_inventory_value,
            ROUND(AVG(price), 2) as average_price
        FROM products
    """).fetchone()
    
    extremes = conn.execute("""
        SELECT 
            (SELECT name FROM products ORDER BY price DESC LIMIT 1) as most_expensive,
            (SELECT name FROM products ORDER BY price ASC LIMIT 1) as cheapest
    """).fetchone()
    
    conn.close()
    return {**dict(stats), **dict(extremes)}

def get_category_analytics() -> list[dict]:
    """Get summaries of each product category."""
    conn = _conn()
    rows = conn.execute("""
        SELECT 
            category, 
            COUNT(*) as product_count, 
            SUM(stock) as total_stock,
            ROUND(AVG(price), 2) as avg_price
        FROM products 
        GROUP BY category
        ORDER BY product_count DESC
    """).fetchall()
    conn.close()
    return _rows(rows)

def get_product_details(product_id: int) -> dict:
    """Get full details of a single product."""
    conn = _conn()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ─── Tool Dispatcher ─────────────────────────────────────────
TOOL_FN_MAP = {
    "search_inventory":      search_inventory,
    "get_inventory_analytics": get_inventory_analytics,
    "get_category_analytics": get_category_analytics,
    "get_product_details":   get_product_details,
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
            "name": "search_inventory",
            "description": "Search for products with optional filters for name, category, price, and stock levels. Supports sorting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Filter by product name (partial match)."},
                    "category": {"type": "string", "description": "Filter by exact category name."},
                    "max_price": {"type": "number", "description": "Maximum price threshold."},
                    "min_price": {"type": "number", "description": "Minimum price threshold."},
                    "stock_threshold": {"type": "integer", "description": "Filter items with stock less than or equal to this value."},
                    "sort_by": {
                        "type": "string", 
                        "enum": ["price_asc", "price_desc", "stock_asc", "stock_desc"],
                        "description": "Sort results by price or stock."
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory_analytics",
            "description": "Get high-level stats like total inventory value, total item count, average price, and extremes.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_analytics",
            "description": "Get a breakdown of the inventory by category, including counts and average prices.",
            "parameters": {"type": "object", "properties": {}},
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

@app.post("/tts")
async def generate_tts(request: TTSRequest):
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        raise HTTPException(status_code=503, detail="ElevenLabs credentials not configured.")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": request.text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    async def audio_stream():
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=headers, json=data) as response:
                if response.status_code != 200:
                    print(f"[ElevenLabs Error] {response.status_code}")
                    return
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")
