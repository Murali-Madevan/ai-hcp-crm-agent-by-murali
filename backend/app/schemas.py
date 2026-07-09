from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    institution: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    segment: Optional[str] = "B"


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class InteractionBase(BaseModel):
    hcp_id: str
    interaction_type: Optional[str] = "Visit"
    channel: Optional[str] = "In-person"
    interaction_date: Optional[datetime] = None
    raw_text: Optional[str] = None
    summary: Optional[str] = None
    products_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    samples_dropped: Optional[str] = None
    materials_shared: Optional[str] = None
    next_steps: Optional[str] = None


class InteractionCreate(InteractionBase):
    source: Optional[str] = "form"


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    channel: Optional[str] = None
    interaction_date: Optional[datetime] = None
    raw_text: Optional[str] = None
    summary: Optional[str] = None
    products_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    samples_dropped: Optional[str] = None
    materials_shared: Optional[str] = None
    next_steps: Optional[str] = None
    reason: Optional[str] = None  # why the edit was made (for audit trail)


class InteractionOut(InteractionBase):
    id: str
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FollowUpOut(BaseModel):
    id: str
    hcp_id: str
    interaction_id: Optional[str] = None
    task: str
    due_date: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


class SafetyFlagOut(BaseModel):
    id: str
    interaction_id: str
    flag_type: str
    detail: str
    severity: str
    requires_pv_escalation: bool

    class Config:
        from_attributes = True


class ChatMessageIn(BaseModel):
    session_id: Optional[str] = None
    hcp_id: Optional[str] = None
    message: str


class ChatMessageOut(BaseModel):
    session_id: str
    reply: str
    tool_calls: List[str] = []
    interaction_id: Optional[str] = None
    followups: List[FollowUpOut] = []
    safety_flags: List[SafetyFlagOut] = []
