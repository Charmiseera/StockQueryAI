

# 📦 StockQuery AI — Intelligent Inventory Intelligence Agent
StockQuery AI is a next-generation inventory management assistant that transforms how businesses interact with their data. By leveraging **Large Language Models (LLMs)** and the **Model Context Protocol (MCP)**, it allows users to manage stock, track categories, and receive intelligent insights using plain English — no SQL knowledge required.
---
## 🏗️ Technical Architecture
The system follows a modular, agentic architecture where the AI acts as a bridge between the user and the database.
![Technical Architecture](https://via.placeholder.com/800x400?text=Architecture+Diagram+Placeholder) 
*(Note: Replace with the generated architecture image in your local folder)*
### **High-Level Flow:**
1. **User** → Enters natural language question in **React UI**.
2. **FastAPI** → Orchestrates the request and initiates the **AI Agent**.
3. **LLM** → Decides which **MCP Tool** (e.g., `get_low_stock`) to call.
4. **MCP Server** → Executes safe SQL on the **SQLite Database**.
5. **AI Agent** → Summarizes data into a human-friendly response.
---
## 🌟 Key Features
*   **Natural Language Querying**: Talk to your data just like you would talk to a person.
*   **Intelligent Low-Stock Alerts**: A dedicated dashboard that highlights urgent restocking needs.
*   **Dynamic Data Tables**: Clean, visual representation of complex database records.
*   **Secure Authentication**: Protecting business data with JWT and encrypted passwords.
*   **Agentic Decision Making**: The AI automatically selects the best tools to answer your specific questions.
---
## 🛠️ Core Technology Stack
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React (Vite) | Modern, responsive dashboard and chat UI. |
| **Backend** | FastAPI (Python) | High-performance API orchestration. |
| **Database** | SQLite | Lightweight, reliable local data storage. |
| **AI Integration** | MCP Protocol | Secure bridge between the LLM and the Database. |
| **Intelligence** | Nebius (Llama 3.3) | The "Brain" behind natural language understanding. |
---
## 🎯 Project Objectives
### **1. Technical Objectives**
*   Implement a secure bridge between AI and structured data via MCP.
*   Build a responsive, single-page application for inventory oversight.
*   Develop a secure authentication layer using industry standards (JWT).
### **2. Performance Objectives**
*   Achieve sub-5 second response times for complex inventory queries.
*   Ensure 100% accuracy in tool selection for low-stock detection.
---
## 🔄 Project Workflow
### **Milestone 1: Requirement Analysis**
*   Identify inventory challenges and define the target user personas (Managers/Staff).
*   Finalize the technology stack and system scope.
### **Milestone 2: System Design**
*   Design the 3-tier architecture (UI–Backend–LLM).
*   Create the SQLite database schema and MCP tool definitions.
### **Milestone 3: Development & Integration**
*   Build the FastAPI server and register MCP tools.
*   Develop the React dashboard and connect it to the Backend APIs.
---
## ⚙️ Setup & Installation
### **1. Prerequisites**
*   Python 3.10+
*   Node.js 18+
*   Nebius API Key (for the LLM)
### **2. Environment Configuration**
Create a `.env` file in the root directory:
```env
NEBIUS_API_KEY=your_key_here
LOW_STOCK_THRESHOLD=5
3. Running the Application
Start the Backend:

bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
Start the Frontend:

bash
cd frontend
npm install
npm run dev
