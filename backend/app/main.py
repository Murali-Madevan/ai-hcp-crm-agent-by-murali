from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import hcp, interactions, form_agent

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-First CRM — HCP Module",
    description="Backend API for logging pharmaceutical field interactions with Healthcare Professionals.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcp.router)
app.include_router(interactions.router)
app.include_router(form_agent.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "hcp-crm-backend"}
