# AI-First CRM — HCP Module

> An intelligent CRM module for pharmaceutical field representatives to log and manage interactions with Healthcare Professionals (HCPs) — powered by AI.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/AI%20Agent-LangGraph-1C3C6E)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/LLM-Groq-FF6C37)](https://groq.com)

---

## Overview

The **HCP CRM Module** enables pharmaceutical sales reps to log their field interactions with healthcare professionals through two equivalent entry points:

1. **Structured form** — explicit fields for interaction type, channel, notes, products discussed, sentiment, samples, and next steps.
2. **Conversational AI chat** — describe the visit in plain English; a LangGraph-powered agent automatically extracts structured data, logs the interaction, screens for adverse events, schedules follow-ups, and can edit past records or pull up HCP history — all through natural conversation.

Both paths produce identical, auditable CRM records.

---

## Features

- **Dual-entry interaction logging** — form-based and chat-based, same underlying tools
- **AI-powered summarization** — Groq LLM extracts structured fields from free-text notes
- **HCP context lookup** — instant access to HCP profile and last 5 interactions
- **Interaction editing** — modify any field with full audit trail
- **Follow-up scheduling** — natural-language due dates
- **Adverse event detection** — automatic pharmacovigilance/compliance screening
- **Safety flagging** — severity-graded compliance flags
- **Multi-turn chat** — persistent conversation per session

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Vite + React)            │
│  ┌──────────────┐  ┌──────────────────────────────┐ │
│  │ Structured   │  │   Chat Panel (LangGraph       │ │
│  │ Form         │  │   Agent Interface)            │ │
│  └──────────────┘  └──────────────────────────────┘ │
│                │                     │                │
│         Axios REST /  POST /api/chat                │
└────────────────┼─────────────────────┼──────────────┘
                 │                     │
┌────────────────┼─────────────────────┼──────────────┐
│           FastAPI Backend (port 8000)                │
│                 │                     │               │
│  ┌──────────────┴─────────────────────┴──────────┐ │
│  │           LangGraph Agent                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐   │ │
│  │  │  Agent   │──▶   Tools   │──▶   Agent    │   │ │
│  │  │  (LLM)   │  │  (DB ops) │  │  (LLM)     │   │ │
│  │  └──────────┘  └──────────┘  └────────────┘   │ │
│  └────────────────────────────────────────────────┘ │
│               │                                      │
│  ┌────────────┴─────────────────────────────────┐   │
│  │        5 LangChain Tools                     │   │
│  │  log_interaction │ edit_interaction          │   │
│  │  get_hcp_context │ schedule_followup         │   │
│  │  detect_adverse_event                        │   │
│  └──────────────────────────────────────────────┘   │
│                        │                              │
│  ┌─────────────────────┴─────────────────────────┐  │
│  │          SQLAlchemy ORM                        │  │
│  │  HCP │ Interaction │ InteractionEdit          │  │
│  │  FollowUp │ SafetyFlag │ ChatSession          │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### LangGraph Agent Flow

```
User Message → Agent Node (Groq LLM interprets intent)
                     │
                     ▼
            Tool calls needed?
                     │
            ┌────────┴────────┐
            ▼                  ▼
         Tools Node        END → Reply
      (executes DB ops)
            │
            ▼
         Agent Node
      (processes results)
            │
            ▼
       (back to check)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Redux Toolkit, Vite, Axios |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **AI Agent** | LangGraph (StateGraph), LangChain Core |
| **LLM** | Groq — `gemma2-9b-it`, fallback `llama-3.3-70b-versatile` |
| **Database** | SQLAlchemy 2.0 (SQLite local, Postgres/MySQL production) |
| **Font** | Google Inter |

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Groq API key](https://console.groq.com) (free tier available)

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

**Edit `backend/.env`** and set your Groq API key:

```env
GROQ_API_KEY=gsk_your_key_here
```

Seed demo data and start the server:

```bash
python seed.py
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

---

## Usage

1. **Select an HCP** from the dropdown in the header.
2. **Structured Form tab** — fill in details and click "Log Interaction".
3. **Chat with Agent tab** — type in plain English, e.g.:
   - *"I met Dr. Anjali Mehta today, discussed CardioFlow's new dosing data — she was positive and asked for updated trial data by Friday."*
   - *"What did we last discuss with Dr. Mehta?"*
   - *"Change the sentiment on that last interaction to Positive."*
   - *"Remind me to follow up next week."*
4. **Right sidebar** — view recent interactions, open follow-ups, and safety/compliance flags.

---

## Deployment

### Frontend (Vercel)

See `frontend/vercel.json`. Connect your repo to Vercel with:

- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Environment Variable:** `VITE_API_BASE_URL` = your Render backend URL

### Backend (Render)

See `render.yaml` at the project root. Deploy as a **Web Service**:

- **Root Directory:** `backend`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:** `GROQ_API_KEY`, `DATABASE_URL`, `FRONTEND_ORIGIN`

---

## Project Structure

```
ai-crm-hcp-module/
├── backend/
│   ├── app/
│   │   ├── agent/            # LangGraph graph, tools, LLM wrapper
│   │   ├── routers/          # FastAPI routes (hcp, interactions, chat)
│   │   ├── main.py           # App entry point
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── config.py         # Environment settings
│   │   └── database.py       # DB engine / session
│   ├── seed.py               # Demo HCP data populator
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React UI components
│   │   ├── store/            # Redux state slices
│   │   └── api/              # Axios API client
│   ├── package.json
│   └── vite.config.js
├── render.yaml               # Render deployment config
└── docs/architecture.md      # Full architecture write-up
```

---

## License

MIT