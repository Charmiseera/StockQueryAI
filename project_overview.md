# 🤖 StockQuery AI — Project Deep Dive

## What Is It?

**StockQuery AI** is a production-grade, multi-tenant AI inventory intelligence platform. Non-technical users — store managers, business owners — query a **PostgreSQL** inventory database using **plain English**. No SQL required.

A user types: *"Which products are low in stock?"* The AI understands the intent, calls the right MCP tool, queries PostgreSQL (scoped to that user's data), and returns a human-readable answer with an interactive table.

---

## 🏗️ Architecture (v3.0)

```
React Frontend (Vite)
        │ JWT Bearer Token
        ▼
FastAPI Backend ─────────────────────────────────────────────────┐
        │                                                         │
        │  auth/dependencies.py: CurrentUser (JWT validated)      │
        ▼                                                         │
ai/agent.py (Agentic LLM Loop)                                   │
        │  injects user_id into every tool call                   │
        ▼                                                         │
mcp_bridge/client_manager.py (stdio subprocess)                  │
        │  JSON-RPC                                               │
        ▼                                                         │
mcp_server/server.py ◄───────────────────────────────────────────┘
        │  SQLAlchemy ORM — WHERE product.user_id = current_user
        ▼
PostgreSQL (single source of truth)
        │
        ▼
LLM → Human-readable answer → FastAPI → React UI
```

> **Security guarantee**: Every MCP tool query is filtered by `user_id`. The AI can only ever see and modify the data of the authenticated user. Cross-tenant data leakage is architecturally impossible.

---

## 🛠️ Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **LLM** | Llama-3.3-70B via Nebius API | OpenAI-compatible endpoint |
| **Tool Protocol** | MCP (Model Context Protocol) | Subprocess stdio JSON-RPC |
| **Backend API** | FastAPI 0.115 (Python 3.11) | Async, modular routers |
| **Database** | PostgreSQL 15 | Single source of truth |
| **ORM** | SQLAlchemy 2.0 | Declarative models + sessions |
| **Auth** | JWT (HS256) + bcrypt | Access tokens, 60-min expiry |
| **Rate Limiting** | slowapi | 30 req/min on /query, 10 on /login |
| **TTS** | ElevenLabs API | Streaming audio response |
| **Frontend** | React 18 + Vite | Chat UI + dashboard |
| **Charts** | Recharts | Analytics visualization |
| **Containerization** | Docker + Docker Compose | Full stack, prod-ready |

---

## 📁 File Structure

```
StockQueryAI/
│
├── backend/                        ← FastAPI Application
│   ├── main.py                     ← App entry + router wiring + lifespan
│   ├── requirements.txt            ← Python dependencies
│   ├── seed_db.py                  ← PostgreSQL seeder (demo user + 1000 products)
│   ├── ai/
│   │   └── agent.py                ← Multi-turn agentic LLM loop
│   ├── auth/
│   │   ├── security.py             ← bcrypt + JWT create/decode
│   │   └── dependencies.py         ← CurrentUser FastAPI dependency
│   ├── db/
│   │   ├── connection.py           ← SQLAlchemy engine + SessionLocal
│   │   ├── models.py               ← User, Product, StockAuditLog, ChatHistory
│   │   └── migrations.py           ← create_all() schema bootstrap
│   ├── mcp_bridge/
│   │   └── client_manager.py       ← MCP subprocess lifecycle manager
│   └── routes/
│       ├── auth.py                 ← /auth/register, /auth/login
│       ├── history.py              ← /history (GET, POST, DELETE)
│       ├── inventory.py            ← /inventory CRUD + stats + audit
│       ├── query.py                ← /query (JWT-protected, auto-saves history)
│       ├── tts.py                  ← /tts (ElevenLabs streaming)
│       └── users.py                ← /users/me
│
├── mcp_server/
│   └── server.py                   ← 10 MCP tools, all PostgreSQL via SQLAlchemy
│
├── frontend/                       ← React + Vite Application
│   └── src/
│       ├── App.jsx                 ← Main app shell + routing
│       └── components/             ← Chat, Analytics, Products, AuditLog
│
├── tests/
│   ├── conftest.py                 ← SQLAlchemy in-memory fixtures
│   ├── test_auth_security.py       ← Unit: bcrypt, JWT, password strength
│   ├── test_db_migrations.py       ← Unit: schema, tenant isolation, audit log
│   └── test_integration.py         ← Integration: full HTTP flow (30+ tests)
│
├── .env                            ← Secrets (never committed)
├── .env.example                    ← Template for new developers
├── docker-compose.yml              ← Full-stack: db → backend → frontend
├── Dockerfile.backend              ← Python 3.11-slim, seed + uvicorn
└── Dockerfile.frontend             ← Node 20 build → Nginx serve
```

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|---------|------|-------------|
| `GET` | `/health` | ❌ | Status check |
| `POST` | `/auth/register` | ❌ | Create account |
| `POST` | `/auth/login` | ❌ | Login → JWT |
| `GET` | `/users/me` | ✅ JWT | Current user profile |
| `POST` | `/query` | ✅ JWT | **Core**: NL → AI answer (saves to history) |
| `POST` | `/tts` | ❌ | Text → ElevenLabs audio stream |
| `GET` | `/inventory/products` | ✅ JWT | Paginated product list |
| `POST` | `/inventory/products` | ✅ JWT | Create product |
| `PUT` | `/inventory/products/{id}` | ✅ JWT | Update product |
| `DELETE`| `/inventory/products/{id}` | ✅ JWT | Delete product |
| `GET` | `/inventory/stats` | ✅ JWT | Dashboard stats |
| `GET` | `/inventory/audit` | ✅ JWT | Stock change audit log |
| `POST` | `/inventory/ingest` | ✅ JWT | Bulk CSV ingest |
| `GET` | `/history` | ✅ JWT | Chat history (last 100) |
| `POST` | `/history/message` | ✅ JWT | Save one message |
| `DELETE`| `/history` | ✅ JWT | Clear all history |

---

## 🧰 MCP Tools (10 total, all PostgreSQL, all `user_id`-scoped)

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `query_inventory_db` | `user_id, product_name` | Full-text search by name |
| `get_product_details` | `user_id, product_id` | Fetch single product by ID |
| `search_inventory` | `user_id, name?, category?, min_price?, max_price?, stock_threshold?, sort_by?` | Advanced filtered search |
| `get_low_stock_items` | `user_id, threshold=10` | Items below stock threshold |
| `get_all_categories` | `user_id` | Distinct category list |
| `get_products_by_category` | `user_id, category` | Filter by category |
| `get_products_by_names` | `user_id, names[]` | Batch name lookup |
| `get_inventory_analytics` | `user_id` | Total value, avg price, extremes |
| `get_category_analytics` | `user_id` | Per-category breakdown |
| `update_stock` | `user_id, new_quantity, product_id? OR product_name?` | **Write** — update stock + audit log |

---

## 🔐 Security Model

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT HS256, 60-min expiry, bcrypt passwords |
| Authorization | `CurrentUser` dependency on every protected route |
| Tenant isolation | Every DB query: `WHERE product.user_id = current_user.id` |
| Rate limiting | slowapi: 30/min on /query, 10/min on /login, 5/min on /register |
| No data leakage | MCP tools receive user_id and filter at query time — AI cannot escape its scope |
| Audit trail | Every stock change via AI or UI writes a `StockAuditLog` row |

---

## 🤖 Agentic Loop (ai/agent.py)

Multi-turn loop (up to 10 turns):

1. User question → message history with SYSTEM_PROMPT
2. LLM called with all 10 MCP tool definitions
3. If LLM returns `tool_calls` → `user_id` injected → executed via MCP → result appended → loop
4. If LLM returns text content → final answer
5. Both user question and AI answer **automatically persisted** to `chat_history` table

---

## 🐳 Docker Deployment

```bash
# One-command full-stack start
docker-compose up --build

# Stack order (enforced by healthchecks):
# PostgreSQL → ready → Backend (seed_db.py runs) → ready → Frontend
```

Services:
- `db` — PostgreSQL 15 (port 5433) with `pg_isready` healthcheck
- `backend` — FastAPI (port 8000), runs `seed_db.py` on every start
- `frontend` — Nginx serving React build (port 80)

---

## 🚀 Local Development

```bash
# 1. Start PostgreSQL
docker-compose up db -d

# 2. Backend
cd backend
pip install -r requirements.txt
python seed_db.py          # seeds demo@stockquery.ai / demo123
uvicorn main:app --reload --port 8080  # → http://localhost:8080/docs

# 3. Frontend
cd frontend
npm install
npm run dev                # → http://localhost:5173
```

---

## 🧪 Test Suite

```bash
cd backend
pip install pytest httpx pytest-asyncio
pytest ../tests/ -v

# 3 test modules, 35+ tests:
# test_auth_security.py  — unit: JWT, bcrypt, password rules
# test_db_migrations.py  — unit: schema correctness, tenant isolation
# test_integration.py    — integration: full HTTP flow, all endpoints
```

---

## 📊 Data

- **Source**: `backend/inventory_1000.csv` (1,000 real grocery products)
- **Demo user**: `demo@stockquery.ai` / `demo123`
- **Seeding**: `seed_db.py` is idempotent — safe to re-run
- **Categories**: Dairy, Grains, Snacks, Electronics, Personal Care, Household, and more

---

## 📌 Status (v3.0.0 — Production-Ready)

| Feature | Status |
|---------|--------|
| Natural language queries (10 MCP tools) | ✅ |
| Multi-turn agentic loop | ✅ |
| PostgreSQL single source of truth | ✅ |
| Multi-tenant user isolation | ✅ |
| JWT auth + bcrypt passwords | ✅ |
| Inventory CRUD + audit log | ✅ |
| Chat history persistence | ✅ |
| Visual analytics / charts | ✅ |
| Text-to-speech (ElevenLabs) | ✅ |
| Rate limiting (slowapi) | ✅ |
| Docker deployment (full stack) | ✅ |
| Integration test suite (35+ tests) | ✅ |
| Cloud deployment | ⬜ Next |
