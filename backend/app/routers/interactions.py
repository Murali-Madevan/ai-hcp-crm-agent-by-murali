from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interaction
from app.schemas import InteractionCreate, InteractionOut, InteractionUpdate

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


@router.post("/", response_model=InteractionOut, status_code=201)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    interaction = Interaction(**payload.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.patch("/{interaction_id}", response_model=InteractionOut)
def update_interaction(interaction_id: str, payload: InteractionUpdate, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in updates.items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction
