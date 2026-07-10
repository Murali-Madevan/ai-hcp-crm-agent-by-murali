import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(String(36), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255))
    institution = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    segment = Column(String(50), default="B")
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=gen_id)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String(50), default="Visit")
    channel = Column(String(50), default="In-person")
    interaction_date = Column(DateTime, default=datetime.utcnow)

    raw_text = Column(Text)
    summary = Column(Text)
    products_discussed = Column(Text)
    sentiment = Column(String(20))
    samples_dropped = Column(String(255))
    materials_shared = Column(Text)
    next_steps = Column(Text)

    source = Column(String(20), default="form")
    created_by = Column(String(100), default="rep_demo")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=gen_id)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=True)
    messages_json = Column(Text, default="[]")
    status = Column(String(20), default="active")
    resulting_interaction_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
