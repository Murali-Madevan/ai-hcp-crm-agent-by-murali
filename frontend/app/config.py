import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////tmp/hcp_crm.db")
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    FRONTEND_ORIGIN_ALT: str = os.getenv("FRONTEND_ORIGIN_ALT", "https://ai-hcp-crm-agent-by-murali.vercel.app")


settings = Settings()


def get_cors_origins() -> list[str]:
    origins = [settings.FRONTEND_ORIGIN]
    if settings.FRONTEND_ORIGIN_ALT:
        origins.append(settings.FRONTEND_ORIGIN_ALT)
    return origins
