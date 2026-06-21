import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI-Powered Customer Support Copilot"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production-123456")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours
    
    # Databases
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./copilot.db")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    
    # AI API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MEM0_API_KEY: str = os.getenv("MEM0_API_KEY", "")

settings = Settings()
