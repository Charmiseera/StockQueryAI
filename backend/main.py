"""
main.py — StockQuery AI FastAPI Backend (Nebius / Llama-3.3-70B)

Architecture:
  User → POST /query → LLM (Nebius) → tool call → MCP client
       → MCP server (port 8001) → SQLite → response → LLM → answer

The backend NEVER touches the database directly.
All data access is routed through the MCP server via JSON-RPC.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
import sqlite3

# Ensure backend/ is on the path so `import mcp_client` works
# regardless of the working directory uvicorn is launched from.
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

import mcp_client

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

SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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
    
    yield
    
    # Shutdown: Cleanly close MCP subprocess
    await mcp_manager.stop()

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

class ProductIngest(BaseModel):
    name: str
    category: str
    stock: int
    price: float
    supplier: str | None = "Unknown"

class IngestRequest(BaseModel):
    mode: str  # "append" or "replace"
    products: list[ProductIngest]

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


SYSTEM_PROMPT = (
    "You are StockQuery AI, an intelligent inventory assistant. "
    "You have tools to both READ and WRITE to a real SQLite database.\n\n"
    "CRITICAL RULES:\n"
    "1. ANALYTICS, GRAPHS & LISTS: If a user asks for a 'graph', 'chart', 'visual', 'summary', 'breakdown', or asks to 'list all categories', "
    "you MUST use 'get_inventory_analytics', 'get_category_analytics', or 'get_all_categories'. Do NOT say you lack details.\n"
    "2. OPTIONAL PARAMS: In tools like 'search_inventory', all parameters (min_price, max_price, etc.) are OPTIONAL. "
    "To show the most expensive items, just call 'search_inventory(sort_by=\"price_desc\")' and leave other fields null.\n"
    "3. WRITE (Update Stock): To update stock, use 'update_stock'. You can provide the 'product_name' directly without needing to search for its ID first.\n"
    "4. MULTI-STEP: You are encouraged to call multiple tools in sequence without stopping (e.g., Search -> Update -> Analytics).\n"
    "5. RESPONSES: Provide a natural-language summary. Never paste raw JSON. If a list is empty, say 'No products found'.\n"
    "6. NO HALLUCINATION: Only use results from your tools. Never guess IDs."
)


# ─── Agentic Loop ─────────────────────────────────────────────
async def run_query(question: str, current_user: dict) -> QueryResponse:
    """
    Full agentic loop using dynamic MCP tools.
    """
    log.info(f"[LLM] New request: {question!r} from user {current_user['id']}")

    client      = get_client()
    
    # Implicitly pass user_id so LLM doesn't have to worry about it
    sys_prompt = SYSTEM_PROMPT + (
        f"\n7. Important: Your tools implicitly filter by user_id. You do not need to provide it."
        f"\n8. NEVER explain or echo a tool's description. If you need data, output a valid JSON tool call immediately."
        f"\n9. If asked for items by category (e.g. 'fruits', 'vegetables', 'dairy'), you MUST use 'get_products_by_category' for EACH category name. Do not assume 'Fruits & Veg' is one category if they are separate in the database."
    )
    
    messages    = [
        {"role": "system", "content": sys_prompt},
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
            if tool_used is None:
                tool_used = tc.function.name
            elif tc.function.name not in tool_used:
                tool_used += f", {tc.function.name}"
                
            log.info(f"[LLM] Tool call requested: {tc.function.name}")

            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError as e:
                log.error(f"[LLM] Failed to parse tool arguments: {e}")
                args = {}

            # Inject the current user's ID into the tool arguments
            args["user_id"] = current_user["id"]

            # Execute via manager
            result = await mcp_manager.call_tool(tc.function.name, args)

            # Persist list/dict results for the frontend table
            if isinstance(result, list) and result:
                if data_result is None:
                    data_result = []
                data_result.extend(result)
            elif isinstance(result, dict) and result and "error" not in result:
                if data_result is None:
                    data_result = []
                data_result.append(result)

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


# ─── Auth Helpers ──────────────────────────────────────────────
def get_db_connection():
    db_path = Path(__file__).parent.parent / "mcp_server" / "inventory.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

import bcrypt

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    
    if user is None:
        raise credentials_exception
    return dict(user)

# ─── Endpoints ───────────────────────────────────────────────
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    conn = get_db_connection()
    existing_user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (user.username, user.email)).fetchone()
    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already registered")
        
    hashed_password = get_password_hash(user.password)
    conn.execute(
        "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
        (user.username, user.email, hashed_password)
    )
    conn.commit()
    conn.close()
    return {"message": "User created successfully"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (form_data.username, form_data.username)).fetchone()
    conn.close()
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"]}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "StockQuery AI", "model": MODEL}


@app.post("/query", response_model=QueryResponse)
async def query_inventory(request: QueryRequest, current_user: dict = Depends(get_current_user)):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not NEBIUS_API_KEY or NEBIUS_API_KEY == "your-nebius-api-key-here":
        raise HTTPException(
            status_code=503,
            detail="NEBIUS_API_KEY not configured. Add it to your .env file.",
        )

    try:
        return await run_query(request.question.strip(), current_user)
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


@app.post("/ingest")
async def ingest_dataset(request: IngestRequest, current_user: dict = Depends(get_current_user)):
    """
    Ingest a dataset of products from the frontend.
    Supports replacing the entire DB or appending to it.
    """
    try:
        db_path = Path(__file__).parent.parent / "mcp_server" / "inventory.db"
        conn = sqlite3.connect(db_path)
        
        # Ensure schema exists just in case
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT    NOT NULL,
                category TEXT    NOT NULL,
                stock    INTEGER NOT NULL DEFAULT 0,
                price    REAL    NOT NULL DEFAULT 0.0,
                supplier TEXT    NOT NULL DEFAULT 'Unknown',
                user_id  INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        if request.mode == "replace":
            log.info(f"[BACKEND] Replace mode requested. Clearing existing products for user {current_user['id']}.")
            conn.execute("DELETE FROM products WHERE user_id = ?", (current_user["id"],))
            
        inserted = 0
        for p in request.products:
            # Check if name is non-empty
            if not p.name.strip():
                continue
                
            conn.execute(
                "INSERT INTO products (name, category, stock, price, supplier, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                (p.name[:200], p.category[:100], p.stock, round(p.price, 2), p.supplier[:100] if p.supplier else "Unknown", current_user["id"])
            )
            inserted += 1
            
        conn.commit()
        conn.close()
        log.info(f"[BACKEND] Successfully ingested {inserted} products (mode: {request.mode}).")
        return {"status": "ok", "message": f"Successfully ingested {inserted} products.", "inserted": inserted}
    except Exception as e:
        log.error(f"[BACKEND] Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        log.error(f"[BACKEND] Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

