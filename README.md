# AI-Powered Customer Support Copilot

An enterprise-grade AI assistant that helps customer support agents by dynamically retrieving customer profiles, billing data, past order states, previous support histories, and company policy rules to generate professional suggested replies using **LangGraph**, **ChromaDB**, and **Mem0** memory.

## Architecture Highlights
- **LangGraph Agent Workflow**: Implements state graphs to coordinate tool invocations, RAG search extraction, memory lookups, and structured OpenAI responses.
- **Mem0 Memory Service**: Manages persistent profile memories, updating them after interactions. Falls back to a local SQL database memory system if API credentials are not provided.
- **RAG Engine**: Chunks company guidelines PDF files and searches them using ChromaDB similarity matches.
- **Dual Dashboard Systems**: Includes Next.js react pages and a self-contained static HTML single-page dashboard served directly by the FastAPI server on startup for immediate testing.

---

## Folder Structure
```
AI-Copilot/
├── backend/
│   ├── app/
│   │   ├── api/            # JWT auth, user/customer endpoints, logs, upload
│   │   ├── database/       # SQLModel database schemas, mock database seeder
│   │   ├── rag/            # PDF ingestion, chunking, ChromaDB controller
│   │   ├── memory/         # Mem0 client wrapper, SQL extractor fallback
│   │   ├── tools/          # LangChain CRM operations tools
│   │   ├── agents/         # LangGraph state routers and execution nodes
│   │   ├── static/         # Self-contained premium HTML dashboard
│   │   ├── config.py       # Configuration settings
│   │   └── main.py         # Main entry point (FastAPI engine)
│   ├── requirements.txt    # Python backend package dependencies
│   └── Dockerfile          # Backend multi-stage build script
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js page configurations
│   ├── package.json        # NPM dependencies
│   └── Dockerfile          # Frontend Multi-stage compile script
├── docker-compose.yml      # Orchestrates Postgres + Backend + Frontend containers
└── .env.example            # Environment configurations template
```

---

## Getting Started

### 1. Fast Track Launch (Runs instantly using local Python dependencies)
No Node or Docker dependencies required! The FastAPI server serves a fully-functional premium dashboard at `http://localhost:8000`.

1. **Clone the repository and go to backend**:
   ```bash
   cd backend
   ```
2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Setup environment variables**:
   Create a `.env` file in the backend root based on `.env.example`:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   MEM0_API_KEY=
   ```
5. **Run the FastAPI app**:
   ```bash
   python -m backend.app.main
   ```
6. **Open browser**:
   Navigate to `http://localhost:8000`.
   - Admin login: `admin@copilot.com` / `admin123`
   - Agent login: `agent@copilot.com` / `agent123`

---

### 2. Run via Docker Compose (PostgreSQL Production mode)
Builds and runs PostgreSQL, FastAPI, and the Next.js React Dashboard.

1. Configure `.env` in the root folder with your `OPENAI_API_KEY`.
2. Start the stack:
   ```bash
   docker-compose up --build
   ```
3. Access services:
   - Next.js Web Dashboard: `http://localhost:3000`
   - FastAPI Docs (Swagger): `http://localhost:8000/docs`
