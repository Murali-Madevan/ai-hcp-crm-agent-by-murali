"""
Router for the LangGraph-based form-filling agent.

POST /api/agent/chat
    Accepts a natural-language message from the rep, runs the LangGraph
    graph (which executes ``log_interaction`` to extract structured data),
    and returns the AI reply together with the updated ``InteractionState``.
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatSession
from app.agent.state import InteractionState, EMPTY_INTERACTION_STATE
from app.agent.form_tools import FORM_TOOLS

router = APIRouter(prefix="/api/agent", tags=["Agent"])

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    hcp_id: str = ""


class ChatResponse(BaseModel):
    reply: str
    form_data: InteractionState
    session_id: str
    tool_calls: List[str] = []


# ── Compiled graph (lazy singleton) ───────────────────────────────────────────

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        from app.agent.form_graph import build_form_graph
        _graph = build_form_graph(tools=FORM_TOOLS)
    return _graph


# ── Session helpers ───────────────────────────────────────────────────────────
# The ChatSession.messages_json column stores a JSON object:
#   { "form_data": { ... }, "history": [ {"role":"user","content":"..."}, ... ] }
# - history contains only user messages and AI text replies (no tool artefacts)
# - form_data is the accumulated InteractionState from all previous turns

def _load_session(db: Session, session_id: Optional[str], hcp_id: str) -> tuple:
    """Load or create a ChatSession, returning (session, form_data, history)."""
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(hcp_id=hcp_id, messages_json="{}")
        db.add(session)
        db.commit()
        db.refresh(session)

    raw = session.messages_json or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    loaded = data.get("form_data", {})  # type: ignore[arg-type]
    # Merge loaded data over EMPTY state to ensure all keys exist
    # (handles old sessions that predate newer fields like interaction_time, attendees)
    form_data = {**dict(EMPTY_INTERACTION_STATE), **loaded}
    history = data.get("history", [])
    return session, form_data, history


def _save_session(
    session: ChatSession,
    form_data: dict,
    history: list,
    db: Session,
) -> None:
    """Persist form_data + clean history back to the ChatSession row."""
    session.messages_json = json.dumps({
        "form_data": form_data,
        "history": history,
    })
    db.commit()


def _clean_conversation(messages: list) -> list:
    """Extract only user and assistant (with text content) messages.

    Strips tool-call messages, tool results, and empty AIMessages — the
    graph doesn't need them replayed in subsequent turns.
    """
    out = []
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in ("human", "user") and content:
                out.append({"role": "user", "content": content})
            elif role in ("ai", "assistant") and content:
                out.append({"role": "assistant", "content": content})
        elif hasattr(msg, "type"):
            role = msg.type
            content = msg.content or ""
            if role in ("human", "user") and content:
                out.append({"role": "user", "content": content})
            elif role in ("ai", "assistant") and content:
                out.append({"role": "assistant", "content": content})
    return out


def _extract_reply(messages: list) -> str:
    """Return the text of the last AIMessage with content."""
    for msg in reversed(messages):
        if isinstance(msg, dict):
            if msg.get("role") in ("ai", "assistant") and msg.get("content"):
                return msg["content"]
        elif hasattr(msg, "type") and msg.type in ("ai", "assistant") and msg.content:
            return msg.content
    return ""


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    import traceback
    print("\n" + "=" * 70)
    print("========== CHAT ENDPOINT CALLED ==========")
    print(f"Message (first 200): {payload.message[:200]}")
    print(f"Session ID: {payload.session_id}")
    print(f"HCP ID: {payload.hcp_id}")
    print("=" * 70)

    try:
        session, form_data, history = _load_session(db, payload.session_id, payload.hcp_id)
        print(f"\n[ENDPOINT] Session loaded: id={session.id}")
        print(f"[ENDPOINT] Existing form_data: {form_data}")
        print(f"[ENDPOINT] History length: {len(history)}")

        user_msg = {"role": "user", "content": payload.message}

        graph_input = {
            "messages": history + [user_msg],
            "form_data": dict(form_data),
            "hcp_id": payload.hcp_id,
            "session_id": session.id,
            "clear_form": False,
        }

        print(f"\n[ENDPOINT] Graph input prepared")
        print(f"[ENDPOINT]   messages count: {len(graph_input['messages'])}")
        print(f"[ENDPOINT]   form_data keys: {list(graph_input['form_data'].keys())}")
        print(f"[ENDPOINT] Calling _get_graph().invoke()...")

        result = _get_graph().invoke(graph_input)

        print(f"\n[ENDPOINT] Graph invocation COMPLETE")
        print(f"[ENDPOINT]   Result messages count: {len(result.get('messages', []))}")
        filled_form = {k: v for k, v in result.get('form_data', {}).items() if v}
        print(f"[ENDPOINT]   Result form_data filled keys: {list(filled_form.keys())}")
        print(f"[ENDPOINT]   Result form_data: {json.dumps(result.get('form_data', {}), indent=2)}")
        print(f"[ENDPOINT]   Result clear_form: {result.get('clear_form')}")

        reply = _extract_reply(result["messages"])
        clean_history = _clean_conversation(result["messages"])

        print(f"\n[ENDPOINT] Reply extracted (first 150): {reply[:150] if reply else '(empty)'}")
        print(f"[ENDPOINT] Clean history count: {len(clean_history)}")

        _save_session(session, result["form_data"], clean_history, db)
        print("[ENDPOINT] Session saved to DB")

        response = ChatResponse(
            reply=reply,
            form_data=result["form_data"],
            session_id=session.id,
            tool_calls=[],
        )
        filled_response = {k: v for k, v in response.form_data.items() if v}
        print(f"\n[ENDPOINT] Returning response")
        print(f"[ENDPOINT]   reply: {reply[:100]}...")
        print(f"[ENDPOINT]   form_data filled fields: {list(filled_response.keys())}")
        print(f"[ENDPOINT]   session_id: {session.id}")

        # Log the actual JSON that will be sent to the frontend
        response_json = response.model_dump_json()
        print(f"\n[ENDPOINT] FULL RESPONSE JSON sent to frontend:")
        print(json.dumps(json.loads(response_json), indent=2))
        print(f"[ENDPOINT] END OF RESPONSE JSON")
        print("=" * 70 + "\n")
        return response

    except Exception as e:
        print(f"\n!!!!! ERROR in chat endpoint: {type(e).__name__}: {e}")
        traceback.print_exc()
        print(f"!!!!! END ERROR\n")
        raise
