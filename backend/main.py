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
from datetime import datetime, timedelta, timezone
import sys

from openai import OpenAI
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(dotenv_path=PROJECT_DIR / ".env")

import mcp_client
from auth import (
    hash_password, verify_password,
    create_access_token, generate_secure_token,
    get_current_user, require_current_user,
    send_verification_email, send_reset_email,
)

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
NEBIUS_API_KEY      = os.getenv("NEBIUS_API_KEY", "")
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
MODEL               = "meta-llama/Llama-3.3-70B-Instruct"

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
    try:
        await mcp_manager.start()
        app.state.tools = mcp_manager.get_tools()
        log.info(f"Startup complete. {len(app.state.tools)} tools loaded.")
    except Exception as e:
        log.error(f"Failed to initialize MCP on startup: {e}")
        app.state.tools = []
    yield
    await mcp_manager.stop()

# ─── FastAPI App ─────────────────────────────────────────────
app = FastAPI(
    title="StockQuery AI",
    description="Natural language inventory query agent powered by Llama-3.3-70B + Nebius",
    version="3.0.0",
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

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


SYSTEM_PROMPT = (
    "You are StockQuery AI, an intelligent inventory assistant. "
    "You have tools to both READ and WRITE to a real SQLite database.\n\n"
    "CRITICAL RULES:\n"
    "1. ANALYTICS, GRAPHS & LISTS: If a user asks for a 'graph', 'chart', 'visual', 'summary', 'breakdown', or asks to 'list all categories', "
    "you MUST use 'get_inventory_analytics', 'get_category_analytics', or 'get_all_categories'. Do NOT say you lack details.\n"
    "2. OPTIONAL PARAMS: In tools like 'search_inventory', all parameters (min_price, max_price, etc.) are OPTIONAL. "
    "To show the most expensive items, just call 'search_inventory(sort_by=\"price_desc\")' and leave other fields null.\n"
    "3. LOW STOCK: When user asks about low stock or items needing restocking, call 'get_low_stock_items' with threshold=20 "
    "(stock in this dataset ranges 10-100, so 20 is the right threshold to flag items needing attention).\n"
    "4. WRITE (Update Stock): To update stock, you MUST use 'update_stock'. If you don't have the ID, search for it FIRST.\n"
    "5. MULTI-STEP: You are encouraged to call multiple tools in sequence without stopping (e.g., Search -> Update -> Analytics).\n"
    "6. RESULT LIMIT: All list results are capped at 50 items. Tell the user this if they expect more.\n"
    "7. RESPONSES — KEEP IT SHORT: The frontend already displays full results in a data table. "
    "Your text response should be 1-2 sentences MAX: just state what was found (e.g. how many items, top item name and value). "
    "NEVER list out items with numbers or bullets. NEVER repeat data the table already shows. "
    "Examples of good responses: 'Found 50 products in Dairy, sorted by name.' or 'Top priced item is Banana at $98.43. Showing 50 results in the table.'\n"
    "8. NO HALLUCINATION: Only use results from your tools. Never guess IDs."
)


# ─── Agentic Loop ─────────────────────────────────────────────
async def run_query(question: str) -> QueryResponse:
    log.info(f"[LLM] New request: {question!r}")

    client      = get_client()
    messages    = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": question},
    ]
    tool_used   = None
    data_result = None
    max_turns   = 10
    tools = getattr(app.state, "tools", [])

    def _llm_call():
        return client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            max_tokens=512,
        )

    loop = asyncio.get_event_loop()

    for turn in range(max_turns):
        log.info(f"[LLM] Turn {turn + 1}/{max_turns} — calling model")
        response = await loop.run_in_executor(None, _llm_call)
        msg      = response.choices[0].message

        if not msg.tool_calls:
            log.info(f"[LLM] Final answer generated (turn {turn + 1})")
            return QueryResponse(
                answer=msg.content or "No response generated.",
                tool_used=tool_used,
                data=data_result if isinstance(data_result, list) else None,
            )

        msg_dict = msg.model_dump()
        if msg_dict.get("content") is None:
            msg_dict["content"] = ""
        messages.append(msg_dict)

        for tc in msg.tool_calls:
            tool_used = tc.function.name
            log.info(f"[LLM] Tool call requested: {tool_used}")

            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError as e:
                log.error(f"[LLM] Failed to parse tool arguments: {e}")
                args = {}

            result = await mcp_manager.call_tool(tool_used, args)

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


# ─── Health ───────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "StockQuery AI", "model": MODEL}


# ─── Auth Endpoints ───────────────────────────────────────────
@app.post("/register")
async def register(req: RegisterRequest):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    existing = await mcp_manager.call_tool("get_user_by_email", {"email": req.email})
    if "error" not in existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    pw_hash  = hash_password(req.password)
    ver_tok  = generate_secure_token()
    result   = await mcp_manager.call_tool("register_user", {
        "email": req.email,
        "password_hash": pw_hash,
        "verification_token": ver_tok,
    })
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    email_sent = send_verification_email(req.email, ver_tok)
    return {
        "success": True,
        "message": "Account created. Please check your email to verify your account.",
        "email_sent": email_sent,
        # DEV ONLY — remove in production:
        "dev_token": ver_tok if not email_sent else None,
    }


@app.post("/login")
async def login(req: LoginRequest):
    user = await mcp_manager.call_tool("get_user_by_email", {"email": req.email})
    if "error" in user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user["is_verified"]:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    token = create_access_token({"user_id": user["id"], "email": user["email"]})
    return {"access_token": token, "token_type": "bearer", "email": user["email"]}


@app.get("/verify-email")
async def verify_email(token: str):
    result = await mcp_manager.call_tool("verify_user_email", {"token": token})
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "message": "Email verified! You can now log in."}


@app.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    user = await mcp_manager.call_tool("get_user_by_email", {"email": req.email})
    # Always return success to prevent email enumeration
    if "error" in user:
        return {"success": True, "message": "If that email exists, a reset link has been sent."}

    reset_tok = generate_secure_token()
    expiry    = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    await mcp_manager.call_tool("set_reset_token", {
        "email": req.email,
        "token": reset_tok,
        "expiry": expiry,
    })

    email_sent = send_reset_email(req.email, reset_tok)
    return {
        "success": True,
        "message": "If that email exists, a reset link has been sent.",
        "email_sent": email_sent,
        # DEV ONLY — remove in production:
        "dev_token": reset_tok if not email_sent else None,
    }


@app.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    new_hash = hash_password(req.new_password)
    result   = await mcp_manager.call_tool("reset_user_password", {
        "token": req.token,
        "new_password_hash": new_hash,
    })
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "message": "Password reset successfully. You can now log in."}


@app.get("/me")
async def get_me(user=Depends(require_current_user)):
    return {"user_id": user["user_id"], "email": user["email"]}


@app.get("/history")
async def get_history(user=Depends(require_current_user)):
    return await mcp_manager.call_tool("get_query_history", {"user_id": user["user_id"]})


# ─── Query Endpoint ───────────────────────────────────────────
@app.post("/query", response_model=QueryResponse)
async def query_inventory(request: QueryRequest, authorization: str = Header(None)):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not NEBIUS_API_KEY or NEBIUS_API_KEY == "your-nebius-api-key-here":
        raise HTTPException(status_code=503, detail="NEBIUS_API_KEY not configured.")

    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")

    try:
        response = await run_query(request.question.strip())
        # Save to history
        await mcp_manager.call_tool("save_query_history", {
            "user_id":  user["user_id"],
            "question": request.question.strip(),
            "answer":   response.answer,
            "tool_used": response.tool_used,
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


# ─── TTS Endpoint ─────────────────────────────────────────────
@app.post("/tts")
async def generate_tts(request: TTSRequest, user=Depends(require_current_user)):
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
                    return
                async for chunk in resp.aiter_bytes():
                    yield chunk

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")
