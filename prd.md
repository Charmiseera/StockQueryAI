# 📄 Product Requirements Document (PRD)
## StockQuery AI — Intelligent Inventory Intelligence Agent

---

## 1. Overview

| Field | Details |
|-------|---------|
| **Project Name** | StockQuery AI |
| **Version** | 1.0.0 |
| **Author** | [Your Name] |
| **Date** | April 2026 |
| **Status** | In Development |

---

## 2. Problem Statement

Retail businesses maintain inventory data in structured SQLite databases. However, accessing this data efficiently is a major challenge for non-technical users like store managers and business owners.

### Current Pain Points

- Users must write SQL queries to retrieve any information
- Difficult to quickly check product availability or stock levels
- Decision-making (like restocking) is delayed due to data access friction
- No intelligent query understanding exists in current systems

---

## 3. Proposed Solution

**StockQuery AI** is an AI-powered Inventory Intelligence Agent that enables users to query inventory data using plain English natural language — no SQL knowledge required.

---

## 4. Goals & Objectives

| Goal | Description |
|------|-------------|
| Eliminate SQL dependency | Users can ask questions in plain English |
| Real-time inventory insights | Instant answers on stock, price, and supplier data |
| Smart decision-making | Trigger restocking alerts via low-stock detection |
| Demonstrate AI + DB integration | Real-world agent interacting with structured data via MCP |

---

## 5. Target Users

| User Type | Description |
|-----------|-------------|
| Store Managers | Need quick stock visibility without technical skills |
| Business Owners | Want inventory insights for restocking decisions |
| Operations Staff | Need to check product availability on the fly |

---

## 6. Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Database | SQLite | Lightweight, file-based, no server needed |
| Backend API | FastAPI (Python) | Fast, async, ideal for AI tool integration |
| LLM | best API(which i sbest choose that ) | Supports MCP tool use / function calling |
| Tool Protocol | MCP (Model Context Protocol) | Connects LLM to backend tools as plugins |
| Frontend UI | React (JSX) | Clean, responsive chat interface |
| Communication | REST API (JSON) | Simple and universal |

---

## 7. System Architecture

```
User (React UI)
      |
      | HTTP POST /query
      v
FastAPI Backend
      |
      | Sends query + MCP config
      v
 LLM (via API)
      |
      | Decides which tool to call
      v
MCP Server (Python)
      |
      | Executes tool function
      v
SQLite Database (inventory.db)
      |
      | Returns structured data
      v
Claude LLM
      |
      | Generates human-readable response
      v
FastAPI → React UI → User sees answer
```

---

## 8. Modules & Features

### 8.1 Module 1 — Inventory Database

**Technology:** SQLite

**Tables:**

`products` table:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Unique product ID |
| name | TEXT | Product name |
| category | TEXT | Category (Electronics, Food, etc.) |
| stock | INTEGER | Current stock quantity |
| price | REAL | Unit price |
| supplier | TEXT | Supplier name |

**Seed Data:** Minimum 20 products across at least 4 categories.

---

### 8.2 Module 2 — MCP Server (Tool Layer)

**Technology:** Python + MCP SDK

**Tools to implement:**

| Tool Function | Input | Output | Description |
|--------------|-------|--------|-------------|
| `query_inventory_db(product_name)` | Product name string | Product record(s) | Search product by name |
| `get_product_details(product_id)` | Product ID integer | Single product record | Get full details of one product |
| `get_low_stock_items(threshold)` | Stock threshold integer | List of products | Find all products below threshold |
| `get_all_categories()` | None | List of categories | Return all distinct categories |
| `get_products_by_category(category)` | Category string | List of products | Filter products by category |

**MCP Server responsibilities:**
- Register all tools with the MCP protocol
- Connect to `inventory.db` on startup
- Handle tool call requests from Claude
- Return structured JSON responses

---

### 8.3 Module 3 — Backend API

**Technology:** FastAPI (Python)

**Endpoints:**

| Method | Endpoint | Description |
|--------|---------|-------------|
| POST | `/query` | Accept user query, call Claude + MCP, return response |
| GET | `/health` | Health check |

**Request Body (`/query`):**
```json
{
  "question": "Which products are low in stock?"
}
```

**Response:**
```json
{
  "answer": "The following products are low in stock: ...",
  "tool_used": "get_low_stock_items",
  "data": [...]
}
```

**Backend responsibilities:**
- Receive user query from frontend
- Pass query + MCP server config to Claude API
- Handle Claude's tool call → MCP → DB round trip
- Return final answer to frontend

---

### 8.4 Module 4 — LLM Integration (Claude + MCP)

**Technology:** Claude API + MCP protocol

**How it works:**
1. Backend sends user query to Claude with MCP server URL configured
2. Claude reads the list of available MCP tools
3. Claude decides which tool to call based on intent
4. MCP server executes the tool and returns data
5. Claude generates a human-readable response from the data

**Sample Query Handling:**

| User Query | Tool Called |
|-----------|-------------|
| "Which products are low in stock?" | `get_low_stock_items(10)` |
| "Tell me about product ID 5" | `get_product_details(5)` |
| "Do you have Basmati Rice?" | `query_inventory_db("Basmati Rice")` |
| "Show me all electronics" | `get_products_by_category("Electronics")` |

---

### 8.5 Module 5 — Frontend UI

**Technology:** React (JSX)

**Features:**
- Chat-style interface for natural language input
- Displays AI-generated text response
- Optionally shows raw data table returned by tool
- Loading indicator while query is processing
- Sample question buttons for quick testing

---

## 9. Project Folder Structure

```
stockquery-ai/
│
├── mcp_server/
│   ├── server.py            ← MCP server with all tool functions
│   └── inventory.db         ← SQLite database (auto-generated)
│
├── backend/
│   ├── main.py              ← FastAPI app + /query endpoint
│   ├── seed_db.py           ← Script to populate the database
│   └── requirements.txt     ← Python dependencies
│
├── frontend/
│   ├── src/
│   │   └── App.jsx          ← React chat UI
│   └── package.json
│
└── .env                     ← ANTHROPIC_API_KEY (never commit this)
```

---

## 10. Build Order (Step-by-Step)

| Step | Module | Task |
|------|--------|------|
| 1 | Setup | Install Python, Node.js, VS Code |
| 2 | Database | Create SQLite schema + seed 20+ products |
| 3 | MCP Server | Write tool functions + register with MCP |
| 4 | Backend | Build FastAPI `/query` endpoint |
| 5 | LLM Integration | Connect Claude API with MCP server URL |
| 6 | Frontend | Build React chat UI |
| 7 | Testing | End-to-end test with sample queries |

---

## 11. Sample User Queries (Test Cases)

| # | Query | Expected Tool | Expected Output |
|---|-------|--------------|----------------|
| 1 | "Which products are low in stock?" | `get_low_stock_items` | List of items below threshold |
| 2 | "What is the price of Sugar?" | `query_inventory_db` | Product name + price |
| 3 | "Show me all dairy products" | `get_products_by_category` | Filtered product list |
| 4 | "Give me details of product 7" | `get_product_details` | Full product record |
| 5 | "What categories do you have?" | `get_all_categories` | List of categories |

---

## 12. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Response Time | < 5 seconds per query |
| Database Size | Support up to 10,000 products |
| Uptime | Local dev environment (no SLA required for v1) |
| Security | API key stored in `.env`, never hardcoded |

---

## 13. Out of Scope (v1.0)

- User authentication / login
- Multi-user support
- Real-time stock updates
- Barcode/QR scanning
- Mobile native app
- Cloud deployment

---

## 14. Future Enhancements (v2.0)

- Add `update_stock(product_id, quantity)` tool for write operations
- Dashboard with charts for stock levels
- Email/SMS alerts for low-stock items
- CSV import/export for bulk data
- Multi-language support

---

## 15. Dependencies

### Python (backend + MCP)
```
fastapi
uvicorn
anthropic
mcp
python-dotenv
sqlite3 (built-in)
```

### Node.js (frontend)
```
react
vite
axios
```

---

*Document Version: 1.0 | Last Updated: April 2026*