from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import hcp, interactions, chat

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-First CRM - HCP Module",
    description="Log Interaction screen backend: structured form + LangGraph chat agent, powered by Groq (gemma2-9b-it).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relaxed for local demo; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcp.router)
app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "hcp-crm-backend"}
