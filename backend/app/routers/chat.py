import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.database import get_db
from app.models import ChatSession, FollowUp, SafetyFlag
from app.schemas import ChatMessageIn, ChatMessageOut, FollowUpOut, SafetyFlagOut
from app.agent.graph import run_turn

router = APIRouter(prefix="/api/chat", tags=["Chat Agent"])


def _load_history(session: ChatSession):
    raw = json.loads(session.messages_json or "[]")
    messages = []
    for m in raw:
        if m["role"] == "human":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "ai":
            messages.append(AIMessage(content=m["content"]))
    return messages


def _save_history(db: Session, session: ChatSession, messages: list):
    serialized = []
    for m in messages:
        if isinstance(m, HumanMessage):
            serialized.append({"role": "human", "content": m.content})
        elif isinstance(m, AIMessage) and isinstance(m.content, str) and m.content:
            serialized.append({"role": "ai", "content": m.content})
        # ToolMessage / intermediate tool-call AI messages are intentionally
        # not persisted long-term to keep the stored transcript readable;
        # the DB rows they created (Interaction, FollowUp, SafetyFlag) are the
        # durable record.
    session.messages_json = json.dumps(serialized)
    db.commit()


@router.post("/", response_model=ChatMessageOut)
def chat_turn(payload: ChatMessageIn, db: Session = Depends(get_db)):
    if payload.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == payload.session_id).first()
    else:
        session = None

    if not session:
        session = ChatSession(hcp_id=payload.hcp_id)
        db.add(session)
        db.commit()
        db.refresh(session)

    history = _load_history(session)
    history.append(HumanMessage(content=payload.message))

    final_state = run_turn(db, history, hcp_id=payload.hcp_id, session_id=session.id)
    result_messages = final_state["messages"]

    # Collect which tools were invoked and any interaction created, for the UI.
    tool_calls_made = []
    interaction_id = None
    for m in result_messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                tool_calls_made.append(tc["name"])
        if isinstance(m, ToolMessage):
            try:
                parsed = json.loads(m.content)
                if isinstance(parsed, dict) and parsed.get("interaction_id"):
                    interaction_id = parsed["interaction_id"]
            except Exception:
                pass

    final_reply = ""
    for m in reversed(result_messages):
        if isinstance(m, AIMessage) and isinstance(m.content, str) and m.content:
            final_reply = m.content
            break

    if interaction_id:
        session.resulting_interaction_id = interaction_id

    _save_history(db, session, result_messages)

    followups = db.query(FollowUp).filter(FollowUp.hcp_id == payload.hcp_id).all() if payload.hcp_id else []
    safety_flags = (
        db.query(SafetyFlag).filter(SafetyFlag.interaction_id == interaction_id).all() if interaction_id else []
    )

    return ChatMessageOut(
        session_id=session.id,
        reply=final_reply,
        tool_calls=tool_calls_made,
        interaction_id=interaction_id,
        followups=[FollowUpOut.model_validate(f) for f in followups],
        safety_flags=[SafetyFlagOut.model_validate(f) for f in safety_flags],
    )
