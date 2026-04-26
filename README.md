📦 StockQuery AI — Intelligent Inventory Assistant
StockQuery AI is a modern, AI-powered inventory management assistant that allows users to query and manage stock data using plain English. Built with FastAPI, React, and the Model Context Protocol (MCP), it leverages advanced LLMs to bridge the gap between natural language and structured data.

🚀 Features
Natural Language Queries: Ask questions like "Which products are low in stock?" or "Show me all dairy products" and get instant answers.
Smart Tool Use: Automatically decides when to search, filter, or fetch analytics using MCP tools.
Inventory Analytics: Generates summaries and breakdowns of stock levels and categories.
Stock Updates: Supports updating stock quantities directly through the chat interface.
Text-to-Speech (TTS): Integration with ElevenLabs for audible AI responses.
Data Visualization: Displays raw data in interactive tables alongside AI responses.
🛠️ Tech Stack
Layer	Technology
Frontend	React (JSX), Vite, Axios, Recharts
Backend	FastAPI (Python), Uvicorn
LLM Gateway	Nebius (Llama-3.3-70B)
Protocol	Model Context Protocol (MCP)
Database	SQLite
Voice	ElevenLabs API
📂 Project Structure
text
StockQueryAI/
├── backend/            # FastAPI Backend
│   ├── main.py         # Primary API and Agentic Loop
│   ├── mcp_client.py   # Manages the MCP server connection
│   ├── seed_db.py      # Database initialization script
│   └── requirements.txt
├── frontend/           # React Frontend
│   ├── src/            # App components and logic
│   └── package.json
├── mcp_server/         # MCP Server (Tool Layer)
│   ├── server.py       # Tool implementations (SQL logic)
│   └── inventory.db    # SQLite Database (generated)
└── .env                # API Keys & Configuration
⚙️ Getting Started
1. Prerequisites
Python 3.10+
Node.js 18+
Nebius API Key (or compatible OpenAI-style endpoint)
2. Environment Setup
Create a .env file in the root directory and add your keys:

env
NEBIUS_API_KEY=your-nebius-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key  # Optional
ELEVENLABS_VOICE_ID=your-voice-id            # Optional
3. Backend Setup
bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
# Install dependencies
pip install -r backend/requirements.txt
# Seed the database
python backend/seed_db.py
4. Frontend Setup
bash
cd frontend
npm install
🏃 Running the Application
Start the Backend
From the root directory:

bash
python backend/main.py
The backend will automatically spawn the MCP server as a managed subprocess.

Start the Frontend
In a new terminal:

bash
cd frontend
npm run dev
Open http://localhost:5173 in your browser.

🧩 How it Works (Architecture)
User Input: User types a question in the React UI.
FastAPI Endpoint: The backend receives the query and starts an agentic loop.
LLM Decision: The LLM (Llama 3.3) analyzes the query and decides which MCP tool to call.
MCP Execution: The MCPManager routes the call to the mcp_server, which executes the raw SQL on inventory.db.
Human Response: The LLM processes the database results and generates a natural language summary.
UI Render: The frontend displays the text, tables, and (optionally) plays the voice audio.
🧪 Example Queries
"What categories do we have?"
"Find products with less than 10 units in stock."
"What is the most expensive item in the electronics category?"
"Update the stock for Basmati Rice to 50 units."
Document Version: 1.0 | Built with ❤️ for Efficient Inventory Management.
