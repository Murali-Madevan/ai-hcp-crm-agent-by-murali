from datetime import datetime
from typing import Optional

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


class InteractionCreate(BaseModel):
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


class InteractionOut(BaseModel):
    id: str
    hcp_id: str
    interaction_type: Optional[str]
    channel: Optional[str]
    interaction_date: Optional[datetime]
    raw_text: Optional[str]
    summary: Optional[str]
    products_discussed: Optional[str]
    sentiment: Optional[str]
    samples_dropped: Optional[str]
    materials_shared: Optional[str]
    next_steps: Optional[str]
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
