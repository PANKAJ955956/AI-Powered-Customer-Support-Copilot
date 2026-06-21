from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database.connection import init_db
from backend.app.rag.pipeline import seed_default_kb
from backend.app.api.routes import router as api_router
import logging

# Configure basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Enterprise RAG Customer Support agentic Copilot backend server"
)

# CORS configuration for local UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the dashboard domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing database schemas...")
    init_db()
    logger.info("Seeding knowledge base FAQs...")
    seed_default_kb()
    logger.info("Application startup check complete.")

from fastapi.staticfiles import StaticFiles

# Include routers
app.include_router(api_router, prefix="/api")

# Serve static dashboard UI
app.mount("/", StaticFiles(directory="backend/app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
