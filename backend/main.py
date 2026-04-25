"""
main.py — StockQuery AI FastAPI Backend (Nebius / Llama-3.3-70B)

Architecture:
  User → POST /query → LLM (Nebius) → tool call → MCP client
       → MCP server (port 8001) → SQLite → response → LLM → answer

The backend NEVER touches the database directly.
All data access is routed through the MCP server via JSON-RPC.
"""

import os
import json
import asyncio
import logging
from pathlib import Path

from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

import mcp_client

# ─── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BACKEND] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

NEBIUS_API_KEY   = os.getenv("NEBIUS_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
MODEL            = "meta-llama/Llama-3.3-70B-Instruct"

if not NEBIUS_API_KEY or NEBIUS_API_KEY == "your-nebius-api-key-here":
    log.warning("NEBIUS_API_KEY not set. Add it to .env before querying.")

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
    version="2.0.0",
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


# ─── Tool Schemas (sent to LLM) ───────────────────────────────
# These match the tools registered on the MCP server exactly.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_inventory",
            "description": (
                "Search products with optional filters: name (partial), category (partial), "
                "price range (min_price/max_price), stock ceiling (stock_threshold), and sort order. "
                "Use for price-range queries, multi-filter queries, or sorting."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name":            {"type": "string",  "description": "Partial product name to search for."},
                    "category":        {"type": "string",  "description": "Category name (partial match, case-insensitive)."},
                    "max_price":       {"type": "number",  "description": "Only return products priced at or below this value."},
                    "min_price":       {"type": "number",  "description": "Only return products priced at or above this value."},
                    "stock_threshold": {"type": "integer", "description": "Only return products with stock <= this value."},
                    "sort_by": {
                        "type": "string",
                        "enum": ["price_asc", "price_desc", "stock_asc", "stock_desc"],
                        "description": "Sort results by price or stock level.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_products_by_category",
            "description": (
                "Return ALL products in a specific category. "
                "Use this when the user asks to list or show all products in a category "
                "(e.g. 'show me all electronics', 'list all snacks')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category name (e.g. Electronics, Snacks, Dairy, Grains, Personal Care)."},
                },
                "required": ["category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_stock_items",
            "description": (
                "Return all products whose stock is below a threshold (default 10). "
                "Use this for 'low stock', 'running out', or 'restock' queries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {"type": "integer", "description": "Stock level below which a product is considered low. Default is 10."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get the full record of a single product by its numeric ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "The numeric product ID."},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_inventory_db",
            "description": "Search products by name (partial match). Use when user asks about a specific product by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Product name to search for."},
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory_analytics",
            "description": (
                "Call this for ANY question about total inventory value, total stock, "
                "average price, most expensive product, cheapest product, or overall statistics. "
                "Takes no parameters. Always call this for analytics/stats/summary questions."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_analytics",
            "description": (
                "Call this for ANY question about category breakdown, products per category, "
                "stock per category, or category-level statistics. "
                "Takes no parameters. Always call this for category analytics questions."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

SYSTEM_PROMPT = (
    "You are StockQuery AI, an intelligent inventory assistant backed by a real SQLite database. "
    "Rules you MUST follow:\n"
    "1. Always call exactly ONE tool to retrieve data, then immediately write your final answer. "
    "Do NOT call multiple tools in sequence unless the user explicitly asks for combined data.\n"
    "2. After receiving tool results, write a SHORT natural-language summary. "
    "NEVER paste raw JSON, arrays, or code blocks into your answer. "
    "The frontend renders a table separately — your text answer should be a brief summary only "
    "(e.g. 'Found 5 electronics products. Here are the details:').\n"
    "3. If a tool returns an empty list [], say: 'No products found matching your criteria.'\n"
    "4. Include key facts (name, price, stock) in your summary when listing products.\n"
    "5. Never guess or hallucinate product data.\n"
    "6. For analytics or statistics questions (total value, total stock, averages, category breakdown), "
    "you MUST call get_inventory_analytics or get_category_analytics. "
    "These tools take no parameters — call them immediately without asking for clarification."
)


# ─── Agentic Loop ─────────────────────────────────────────────
async def run_query(question: str) -> QueryResponse:
    """
    Full agentic loop:
    1. Send question + tool schemas to LLM.
    2. LLM returns tool calls.
    3. Each tool call is routed through mcp_client → MCP server → DB.
    4. Tool results are fed back to LLM.
    5. LLM produces a final natural-language answer.

    Logging at every stage:
        [BACKEND] LLM request
        [MCP-CLIENT] tool call (in mcp_client)
        [MCP-SERVER] DB query (in server)
        [BACKEND] final answer
    """
    log.info(f"[LLM] New request: {question!r}")

    client      = get_client()
    messages    = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": question},
    ]
    tool_used   = None
    data_result = None
    max_turns   = 10  # Increased for stability
    def _llm_call():
        return client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

    loop = asyncio.get_event_loop()

    for turn in range(max_turns):
        log.info(f"[LLM] Turn {turn + 1}/{max_turns} — calling model")
        response = await loop.run_in_executor(None, _llm_call)
        msg      = response.choices[0].message

        # ── No tool call on this turn ────────────────────────────
        # Turn 0 special case: if the LLM skipped tool use entirely on the
        # FIRST turn for an analytics question, force-call the right tool
        # and re-ask. Llama-3.3-70B sometimes refuses to call no-arg tools.
        if not msg.tool_calls and turn == 0 and tool_used is None:
            q_lower = question.lower()
            forced_tool = None
            forced_args = {}

            analytics_kw = (
                "total", "value", "worth", "statistic", "analytic",
                "average", "avg", "summary", "overview", "expensive",
                "cheapest", "report", "how many product",
            )
            category_kw = (
                "category breakdown", "by category", "per category",
                "categories", "category analytics", "category report",
            )

            if any(kw in q_lower for kw in category_kw):
                forced_tool = "get_category_analytics"
            elif any(kw in q_lower for kw in analytics_kw):
                forced_tool = "get_inventory_analytics"

            if forced_tool:
                log.info(f"[LLM] Model skipped tool on turn 1 — forcing '{forced_tool}'")
                forced_result = await mcp_client.call_mcp_tool(forced_tool, forced_args)
                tool_used   = forced_tool
                data_result = [forced_result] if isinstance(forced_result, dict) else forced_result

                # Inject a synthetic tool exchange so the LLM can answer
                import uuid
                fake_id = f"forced_{uuid.uuid4().hex[:8]}"
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": fake_id,
                        "type": "function",
                        "function": {
                            "name": forced_tool,
                            "arguments": "{}",
                        },
                    }],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": fake_id,
                    "content": json.dumps(forced_result, default=str),
                })
                continue  # re-prompt LLM with the injected data

        # Final answer (no tool call, data already fetched or genuinely empty)
        if not msg.tool_calls:
            log.info(f"[LLM] Final answer generated (turn {turn + 1})")
            return QueryResponse(
                answer=msg.content or "No response generated.",
                tool_used=tool_used,
                data=data_result if isinstance(data_result, list) else None,
            )

        # Ensure assistant message has content string (some providers dislike None)
        msg_dict = msg.model_dump()
        if msg_dict.get("content") is None:
            msg_dict["content"] = ""
        messages.append(msg_dict)

        # Route every tool call through MCP
        for tc in msg.tool_calls:
            tool_used = tc.function.name
            log.info(f"[LLM] Tool call requested: {tool_used}")

            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError as e:
                log.error(f"[LLM] Failed to parse tool arguments: {e}")
                args = {}

            # ── MCP call (never touches DB directly) ──────────
            result = await mcp_client.call_mcp_tool(tool_used, args)
            # ──────────────────────────────────────────────────

            # Persist list/dict results for the frontend table
            if isinstance(result, list) and result:
                data_result = result
            elif isinstance(result, dict) and result and "error" not in result:
                data_result = [result]

            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      json.dumps(result, default=str),
            })

    log.warning("[LLM] Exhausted max turns without final answer")
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
            detail="NEBIUS_API_KEY not configured. Add it to your .env file.",
        )

    try:
        return await run_query(request.question.strip())
    except Exception as e:
        err = str(e)
        log.error(f"[BACKEND] Query failed: {err}", exc_info=True)
        if "401" in err or "Unauthorized" in err:
            raise HTTPException(status_code=401, detail="Invalid Nebius API key.")
        if "429" in err:
            raise HTTPException(status_code=429, detail="Rate limit reached. Please wait and retry.")
        raise HTTPException(status_code=500, detail=f"Query failed: {err}")


@app.post("/tts")
async def generate_tts(request: TTSRequest):
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        raise HTTPException(status_code=503, detail="ElevenLabs credentials not configured.")

    url     = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {
        "Accept":       "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key":   ELEVENLABS_API_KEY,
    }
    data = {
        "text":     request.text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
    }

    async def audio_stream():
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=headers, json=data) as resp:
                if resp.status_code != 200:
                    log.error(f"[ElevenLabs] Error {resp.status_code}")
                    return
                async for chunk in resp.aiter_bytes():
                    yield chunk

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")
