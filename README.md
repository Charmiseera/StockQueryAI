<div align="center">

# ⚡ StockQuery AI

### AI-Powered Inventory Intelligence Platform

**Ask your inventory anything. In plain English.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-36%20Passing-22c55e?style=flat-square&logo=pytest)](./tests)
[![License](https://img.shields.io/badge/License-MIT-f59e0b?style=flat-square)](LICENSE)

</div>

---

## 🧠 What Is StockQuery AI?

**StockQuery AI** is a full-stack SaaS platform that transforms how retailers manage their inventory. Instead of digging through spreadsheets, users simply **ask questions in plain English** and get instant, AI-powered answers grounded in their real stock data.

> *"Which products are running low on stock?"*
> *"What's my total inventory value in the Dairy category?"*
> *"Show me all products supplied by FreshFarm Ltd. with less than 10 units."*

The platform combines a **Llama-3.3-70B language model**, a **Model Context Protocol (MCP) tool layer** that gives the AI live read/write access to the database, and a **premium React dashboard** — all packaged in a production-ready Docker stack.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **Natural Language Queries** | Ask inventory questions in plain English — AI translates to real-time database lookups |
| 📊 **Live Dashboard** | KPI cards, category breakdown charts, low-stock alerts, total inventory value |
| 📁 **CSV / XLSX Import** | Drag-and-drop bulk import with fuzzy column detection and conflict resolution (skip / update / replace) |
| 🔍 **Advanced Product Search** | Filter by name, category, supplier with real-time pagination |
| 🗂️ **Full Inventory CRUD** | Create, read, update, delete products with stock audit logging |
| 🔐 **JWT Authentication** | Secure register/login with bcrypt hashing, token expiry, and per-user data isolation |
| 🔊 **Text-to-Speech** | AI answers can be read aloud via ElevenLabs TTS integration |
| 📈 **Analytics Page** | Category distribution, stock value breakdown, trend insights |
| 👤 **User Settings** | Profile management, business name, account preferences |
| 🧹 **Clean Onboarding** | New users see a guided empty state — no fake data, no confusion |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│     Vite + Vanilla CSS  ·  Nginx (port 80)          │
└─────────────────────┬───────────────────────────────┘
                      │  HTTP (proxied by Nginx)
┌─────────────────────▼───────────────────────────────┐
│                  FastAPI Backend                     │
│         JWT Auth  ·  SlowAPI Rate Limiting          │
│                                                     │
│  ┌──────────────┐   ┌──────────────────────────┐   │
│  │  REST Routes  │   │    AI Agentic Loop        │   │
│  │  /auth        │   │    Llama-3.3-70B (Nebius) │   │
│  │  /inventory   │   │    MCP Tool Bridge        │   │
│  │  /query       │   │    (live DB read/write)   │   │
│  │  /history     │   └──────────────────────────┘   │
│  │  /users       │                                   │
│  └──────────────┘                                   │
└─────────────────────┬───────────────────────────────┘
                      │  SQLAlchemy ORM
┌─────────────────────▼───────────────────────────────┐
│                  PostgreSQL 15                       │
│      Users · Products · ChatHistory · AuditLogs     │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| **Framework** | FastAPI 0.138 (Python 3.11) |
| **Database** | PostgreSQL 15 via SQLAlchemy 2.0 |
| **Auth** | JWT (python-jose) + bcrypt password hashing |
| **AI Model** | Llama-3.3-70B via Nebius AI Studio / Groq |
| **AI Protocol** | Model Context Protocol (MCP) — tool-based DB access |
| **Rate Limiting** | SlowAPI (per-IP, per-route) |
| **File Parsing** | Custom CSV/XLSX parser with fuzzy column aliasing |
| **TTS** | ElevenLabs API |
| **Validation** | Pydantic v2 |

### Frontend
| Layer | Technology |
|---|---|
| **Framework** | React 18 + Vite 6 |
| **Routing** | State-based (single-bundle, zero flash) |
| **HTTP Client** | Axios with JWT interceptor |
| **Charts** | Recharts |
| **Styling** | Vanilla CSS — custom design system (neon-green / graphite dark theme) |
| **Build & Serve** | Nginx (multi-stage Docker build) |

### Infrastructure
| Layer | Technology |
|---|---|
| **Containerisation** | Docker + Docker Compose |
| **Reverse Proxy** | Nginx (static assets + API proxy) |
| **Testing** | pytest — 36 integration tests (no real DB required) |
| **Deployment** | Railway / any Docker host |

---

## 📸 Pages

| Page | Description |
|---|---|
| **Landing** | Hero section with product pitch, feature highlights, and CTA |
| **Register / Login** | Auth forms with validation and error states |
| **Dashboard** | KPI summary, category chart, low-stock alerts (or onboarding for new users) |
| **AI Assistant** | Conversational interface with query history and TTS playback |
| **Product Manager** | Full CRUD table — add, edit, delete, search, filter, paginate |
| **Import Inventory** | Drag-and-drop CSV/XLSX uploader with preview and conflict resolution |
| **Analytics** | Bar charts, category breakdown, inventory value insights |
| **Settings** | Profile editor and account preferences |

---

## 🚀 Quick Start (Local)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- API key from [Groq](https://groq.com) (free) or [Nebius AI Studio](https://studio.nebius.ai)

### 1. Clone the repo
```bash
git clone https://github.com/Charmiseera/StockQueryAI.git
cd StockQueryAI
```

### 2. Configure environment
```bash
cp .env.example .env
```

Edit `.env` with your keys:
```env
# Generate a strong key:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_generated_secret_key

GROQ_API_KEY=your_groq_api_key
NEBIUS_API_KEY=your_nebius_api_key        # optional alternative LLM
ELEVENLABS_API_KEY=your_elevenlabs_key    # optional — for TTS
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

### 3. Start everything
```bash
docker-compose up --build
```

### 4. Open the app

| Service | URL |
|---|---|
| **App** | http://localhost |
| **API Docs** | http://localhost:8080/docs |
| **Health** | http://localhost:8080/health |

> **First launch:** Register a new account. The dashboard starts empty — import a CSV to populate your inventory and start asking questions.

---

## 🧪 Tests

```bash
# 36 integration tests — no Docker or real DB required (uses in-memory SQLite)
python -m pytest tests/test_integration.py -v
```

**Coverage:**
- ✅ Auth — register, login, duplicate detection, weak passwords, logout
- ✅ JWT protection — all protected routes reject missing/invalid tokens
- ✅ Inventory CRUD — create, read, update, delete with user isolation
- ✅ CSV import — skip / update / replace modes, malformed files, missing columns
- ✅ Chat history — save, retrieve, clear, multi-user isolation
- ✅ AI queries — empty inventory handling, fuzzy typo tolerance, pagination

```
===================== 36 passed in 19.54s =====================
```

---

## 📡 API Reference

> All endpoints require `Authorization: Bearer <token>` except `/auth/*` and `/health`.

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Login → returns JWT access token |
| `POST` | `/auth/logout` | Invalidate current session |

### Inventory
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/inventory/products` | List products (paginated, filterable) |
| `POST` | `/inventory/products` | Create a product |
| `PUT` | `/inventory/products/{id}` | Update a product |
| `DELETE` | `/inventory/products/{id}` | Delete a product |
| `GET` | `/inventory/stats` | Dashboard KPIs (totals, value, low stock) |
| `GET` | `/inventory/categories` | Get distinct categories |
| `POST` | `/inventory/preview` | Preview CSV/XLSX before import |
| `POST` | `/inventory/import` | Bulk import CSV/XLSX |
| `GET` | `/inventory/sample-csv` | Download sample CSV template |

### AI & History
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Ask a natural language inventory question |
| `GET` | `/history` | Retrieve query conversation history |
| `DELETE` | `/history` | Clear query history |

### Users
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me` | Get authenticated user profile |
| `PUT` | `/users/me` | Update profile |

---

## 📁 Project Structure

```
StockQueryAI/
├── backend/
│   ├── ai/
│   │   └── agent.py              # Agentic LLM loop (Llama-3.3-70B + MCP tools)
│   ├── auth/
│   │   ├── dependencies.py       # JWT bearer dependency injection
│   │   └── security.py           # bcrypt password utilities
│   ├── db/
│   │   ├── connection.py         # SQLAlchemy engine + session factory
│   │   ├── migrations.py         # Schema migration runner
│   │   └── models.py             # ORM models (User, Product, ChatHistory, AuditLog)
│   ├── mcp_bridge/
│   │   └── client_manager.py     # MCP subprocess lifecycle manager
│   ├── routes/
│   │   ├── auth.py               # /auth endpoints
│   │   ├── history.py            # /history endpoints
│   │   ├── inventory.py          # /inventory endpoints (CRUD + import)
│   │   ├── query.py              # /query AI endpoint (rate limited)
│   │   ├── tts.py                # /tts ElevenLabs text-to-speech
│   │   └── users.py              # /users profile endpoints
│   ├── utils/
│   │   └── import_parser.py      # CSV/XLSX parser with fuzzy column detection
│   ├── main.py                   # FastAPI app entrypoint + lifespan
│   ├── seed_db.py                # Manual demo data seeder (opt-in)
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Landing.jsx        # Public landing page
│       │   ├── Login.jsx          # Sign-in form
│       │   ├── Register.jsx       # Sign-up form
│       │   ├── Dashboard.jsx      # KPI cards + charts + onboarding
│       │   ├── Analytics.jsx      # Inventory analytics charts
│       │   ├── ProductManager.jsx # CRUD product table
│       │   ├── ImportInventory.jsx # CSV/XLSX drag-and-drop importer
│       │   ├── Settings.jsx       # User settings page
│       │   └── Sidebar.jsx        # Navigation sidebar
│       ├── App.jsx                # Root component + state-based routing
│       └── index.css              # Design tokens + global styles
│
├── mcp_server/
│   └── server.py                 # MCP tool server (inventory read/write tools)
│
├── tests/
│   ├── test_integration.py       # 36 end-to-end integration tests
│   ├── test_auth_security.py     # Auth security edge cases
│   └── test_db_migrations.py     # DB migration tests
│
├── Dockerfile.backend            # Python 3.11-slim backend image
├── Dockerfile.frontend           # Node 20 + Nginx multi-stage image
├── docker-compose.yml            # Full stack orchestration
└── .env.example                  # Environment variable template
```

---

## 🔐 Security Design

- **Per-user data isolation** — every query is scoped to `current_user.id`, zero cross-user data leakage enforced at ORM level
- **bcrypt** password hashing (adaptive cost)
- **JWT** with configurable expiry via `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Rate limiting** on AI endpoint to prevent LLM API abuse
- **Pydantic v2** input validation on all request bodies and path parameters
- **CORS** configured via `ALLOWED_ORIGINS` env var — no hardcoded origins, production-safe
- `.env`, datasets, virtual environments excluded from git

---

## ☁️ Deployment — Vercel (Frontend) + Render (Backend)

### Step 1 — Deploy Backend on Render

1. Go to [render.com](https://render.com) → **New** → **Blueprint**
2. Connect your GitHub repo — Render will detect `render.yaml` automatically
3. It creates:
   - A **PostgreSQL** database (`stockquery-db`)
   - A **Web Service** (`stockquery-backend`) using `Dockerfile.backend`
4. In the backend service → **Environment** → add manually:
   ```
   GROQ_API_KEY=your_key
   NEBIUS_API_KEY=your_key
   ELEVENLABS_API_KEY=your_key      # optional
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ```
5. Copy your Render backend URL: `https://stockquery-backend.onrender.com`

### Step 2 — Deploy Frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project** → Import your GitHub repo
2. Set **Root Directory** to `frontend`
3. Vercel auto-detects Vite. Build settings should be:
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add **Environment Variable**:
   ```
   VITE_API_URL=https://stockquery-backend.onrender.com
   ```
5. Click **Deploy** → your app is live at `https://your-app.vercel.app`

### Step 3 — Update CORS

Go back to Render → backend service → **Environment** → update:
```
ALLOWED_ORIGINS=https://your-app.vercel.app
```
Render will redeploy automatically.

> **Note:** Render free tier spins down after 15 min of inactivity. First request after idle takes ~30s to wake up.

---

## 📄 License

MIT © 2025 [Charmiseera](https://github.com/Charmiseera)

---

<div align="center">
  <b>Built with FastAPI · React · PostgreSQL · Llama-3.3-70B · MCP · Docker</b>
</div>
