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
import jwt
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException, Depends, Header
from datetime import datetime, timedelta

import mcp_client
from notifications import send_low_stock_email

# ─── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BACKEND] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from mcp_client import mcp_manager

# ─── Config ──────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

NEBIUS_API_KEY   = os.getenv("NEBIUS_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
MODEL            = "meta-llama/Llama-3.3-70B-Instruct"
JWT_SECRET       = os.getenv("JWT_SECRET", "secret")
ALGORITHM        = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

if not NEBIUS_API_KEY or NEBIUS_API_KEY == "your-nebius-api-key-here":
    log.warning("NEBIUS_API_KEY not set. Add it to .env before querying.")

# ─── Nebius OpenAI-compatible client ─────────────────────────
def get_client() -> OpenAI:
    return OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=NEBIUS_API_KEY,
    )

# ─── Lifespan ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MCP session and fetch tools
    try:
        await mcp_manager.start()
        app.state.tools = mcp_manager.get_tools()
        log.info(f"Startup complete. {len(app.state.tools)} tools loaded.")
    except Exception as e:
        log.error(f"Failed to initialize MCP on startup: {e}")
        app.state.tools = []
    
    # Start the low stock monitor in the background
    asyncio.create_task(check_low_stock_task())
    
    yield
    
    # Shutdown: Cleanly close MCP subprocess
    await mcp_manager.stop()

async def check_low_stock_task():
    """Background task to check for low stock and send email alerts."""
    threshold = int(os.getenv("LOW_STOCK_THRESHOLD", 5))
    log.info(f"[NOTIFY] Starting low stock monitor (threshold={threshold})")
    
    while True:
        try:
            # Wait for 1 minute between checks for testing
            await asyncio.sleep(60) 
            
            log.info("[NOTIFY] Checking for low stock items...")
            items = await mcp_manager.call_tool("get_low_stock_items", {"threshold": threshold})
            
            if isinstance(items, list) and len(items) > 0:
                # Fetch all registered users to notify them
                users = await mcp_manager.call_tool("get_all_users", {})
                recipients = [u["email"] for u in users] if isinstance(users, list) else []
                
                log.info(f"[NOTIFY] Found {len(items)} low stock items. Notifying {len(recipients)} users...")
                await send_low_stock_email(items, recipients=recipients)
            else:
                log.info("[NOTIFY] No low stock items found.")
                
        except Exception as e:
            log.error(f"[NOTIFY] Error in low stock monitor: {e}")
            await asyncio.sleep(60) # Wait a minute before retrying on error

# ─── FastAPI App ─────────────────────────────────────────────
app = FastAPI(
    title="StockQuery AI",
    description="Natural language inventory query agent powered by Llama-3.3-70B + Nebius",
    version="2.0.0",
    lifespan=lifespan,
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

class UserAuth(BaseModel):
    email: str
    password: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except:
        return None


SYSTEM_PROMPT = (
    "You are StockQuery AI, an intelligent inventory assistant. "
    "You have tools to both READ and WRITE to a real SQLite database.\n\n"
    "CRITICAL RULES:\n"
    "1. ANALYTICS, GRAPHS & LISTS: If a user asks for a 'graph', 'chart', 'visual', 'summary', 'breakdown', or asks to 'list all categories', "
    "you MUST use 'get_inventory_analytics', 'get_category_analytics', or 'get_all_categories'. Do NOT say you lack details.\n"
    "2. OPTIONAL PARAMS: In tools like 'search_inventory', all parameters (min_price, max_price, etc.) are OPTIONAL. "
    "To show the most expensive items, just call 'search_inventory(sort_by=\"price_desc\")' and leave other fields null.\n"
    "3. WRITE (Update Stock): To update stock, you MUST use 'update_stock'. If you don't have the ID, search for it FIRST.\n"
    "4. MULTI-STEP: You are encouraged to call multiple tools in sequence without stopping (e.g., Search -> Update -> Analytics).\n"
    "5. RESPONSES: Provide a natural-language summary. Never paste raw JSON. If a list is empty, say 'No products found'.\n"
    "6. NO HALLUCINATION: Only use results from your tools. Never guess IDs."
)


# ─── Agentic Loop ─────────────────────────────────────────────
async def run_query(question: str) -> QueryResponse:
    """
    Full agentic loop using dynamic MCP tools.
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
    
    # Use dynamic tools from app state
    tools = getattr(app.state, "tools", [])

    def _llm_call():
        return client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            max_tokens=1024,
        )

    loop = asyncio.get_event_loop()

    for turn in range(max_turns):
        log.info(f"[LLM] Turn {turn + 1}/{max_turns} — calling model")
        response = await loop.run_in_executor(None, _llm_call)
        msg      = response.choices[0].message

        # Final answer
        if not msg.tool_calls:
            log.info(f"[LLM] Final answer generated (turn {turn + 1})")
            return QueryResponse(
                answer=msg.content or "No response generated.",
                tool_used=tool_used,
                data=data_result if isinstance(data_result, list) else None,
            )

        # Ensure assistant message has content string
        msg_dict = msg.model_dump()
        if msg_dict.get("content") is None:
            msg_dict["content"] = ""
        messages.append(msg_dict)

        # Route every tool call through MCPManager
        for tc in msg.tool_calls:
            tool_used = tc.function.name
            log.info(f"[LLM] Tool call requested: {tool_used}")

            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError as e:
                log.error(f"[LLM] Failed to parse tool arguments: {e}")
                args = {}

            # Execute via manager
            result = await mcp_manager.call_tool(tool_used, args)

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
async def query_inventory(request: QueryRequest, authorization: str = Header(None)):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not NEBIUS_API_KEY or NEBIUS_API_KEY == "your-nebius-api-key-here":
        raise HTTPException(
            status_code=503,
            detail="NEBIUS_API_KEY not configured. Add it to your .env file.",
        )

    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to use StockQuery AI.")
    
    try:
        response = await run_query(request.question.strip())
        
        # Save to history if user is logged in
        if user:
            await mcp_manager.call_tool("save_query_history", {
                "user_id": user["user_id"],
                "question": request.question.strip(),
                "answer": response.answer,
                "tool_used": response.tool_used
            })
            
        return response
    except Exception as e:
        err = str(e)
        log.error(f"[BACKEND] Query failed: {err}", exc_info=True)
        if "401" in err or "Unauthorized" in err:
            raise HTTPException(status_code=401, detail="Invalid Nebius API key.")
        if "429" in err:
            raise HTTPException(status_code=429, detail="Rate limit reached. Please wait and retry.")
        raise HTTPException(status_code=500, detail=f"Query failed: {err}")


@app.post("/register")
async def register(auth: UserAuth):
    hashed = pwd_context.hash(auth.password)
    res = await mcp_manager.call_tool("register_user", {"email": auth.email, "password_hash": hashed})
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/login")
async def login(auth: UserAuth):
    user = await mcp_manager.call_tool("authenticate_user", {"email": auth.email})
    if "error" in user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not pwd_context.verify(auth.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"user_id": user["id"], "email": user["email"]})
    return {"access_token": token, "token_type": "bearer", "email": user["email"]}

@app.get("/history")
async def get_history(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    history = await mcp_manager.call_tool("get_query_history", {"user_id": user["user_id"]})
    return history

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

@app.post("/test-email")
async def test_email(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    test_items = [{"name": "TEST PRODUCT", "id": 0, "stock": 1}]
    try:
        await send_low_stock_email(test_items, recipients=[user["email"]])
        return {"success": True, "message": f"Test email sent to {user['email']}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
