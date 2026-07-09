from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interaction, FollowUp, SafetyFlag
from app.schemas import InteractionCreate, InteractionOut, InteractionUpdate, FollowUpOut, SafetyFlagOut
from app.agent.tools import build_tools

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])


@router.get("/", response_model=List[InteractionOut])
def list_interactions(hcp_id: str = None, db: Session = Depends(get_db)):
    q = db.query(Interaction).order_by(Interaction.interaction_date.desc())
    if hcp_id:
        q = q.filter(Interaction.hcp_id == hcp_id)
    return q.all()


@router.get("/{interaction_id}", response_model=InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.post("/", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    """
    Structured-form submission path. Uses the exact same `log_interaction`
    LangGraph tool the chat agent uses, so both entry points (form and chat)
    go through identical LLM summarization/extraction logic.
    """
    tools = {t.name: t for t in build_tools(db)}
    log_interaction_tool = tools["log_interaction"]

    result = log_interaction_tool.invoke(
        {
            "hcp_id": payload.hcp_id,
            "raw_text": payload.raw_text or "",
            "interaction_type": payload.interaction_type,
            "channel": payload.channel,
            "source": "form",
        }
    )
    import json

    parsed = json.loads(result)
    if "error" in parsed:
        raise HTTPException(status_code=400, detail=parsed["error"])

    interaction = db.query(Interaction).filter(Interaction.id == parsed["interaction_id"]).first()

    # Allow the structured form to override/augment any LLM-extracted fields
    # explicitly provided by the rep.
    for field in ["products_discussed", "sentiment", "samples_dropped", "materials_shared", "next_steps"]:
        value = getattr(payload, field, None)
        if value:
            setattr(interaction, field, value)
    db.commit()
    db.refresh(interaction)

    # Run the compliance safety net on every new interaction too.
    detect_tool = tools["detect_adverse_event"]
    detect_tool.invoke({"interaction_text": payload.raw_text or "", "interaction_id": interaction.id})

    return interaction


@router.patch("/{interaction_id}", response_model=InteractionOut)
def update_interaction(interaction_id: str, payload: InteractionUpdate, db: Session = Depends(get_db)):
    """Structured-form edit path, using the same `edit_interaction` tool as the chat agent."""
    tools = {t.name: t for t in build_tools(db)}
    edit_tool = tools["edit_interaction"]

    updates = payload.model_dump(exclude_unset=True, exclude={"reason"})
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    import json

    for field, value in updates.items():
        result = edit_tool.invoke(
            {
                "interaction_id": interaction_id,
                "field": field,
                "new_value": str(value),
                "reason": payload.reason or "Edited via structured form",
            }
        )
        parsed = json.loads(result)
        if "error" in parsed:
            raise HTTPException(status_code=400, detail=parsed["error"])

    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    return interaction


@router.get("/{interaction_id}/history")
def get_edit_history(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return [
        {
            "field_changed": e.field_changed,
            "old_value": e.old_value,
            "new_value": e.new_value,
            "reason": e.reason,
            "edited_at": e.edited_at,
        }
        for e in interaction.edit_history
    ]


@router.get("/followups/all", response_model=List[FollowUpOut])
def list_followups(db: Session = Depends(get_db)):
    return db.query(FollowUp).order_by(FollowUp.due_date).all()


@router.get("/safety-flags/all", response_model=List[SafetyFlagOut])
def list_safety_flags(db: Session = Depends(get_db)):
    return db.query(SafetyFlag).order_by(SafetyFlag.created_at.desc()).all()
