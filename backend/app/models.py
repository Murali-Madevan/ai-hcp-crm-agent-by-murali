import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class HCP(Base):
    """Healthcare Professional master record."""
    __tablename__ = "hcps"

    id = Column(String(36), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255))
    institution = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    segment = Column(String(50), default="B")  # e.g. A/B/C tiering
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    """A single logged interaction (call, visit, email, etc.) with an HCP."""
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=gen_id)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String(50), default="Visit")  # Visit, Call, Email, Conference
    channel = Column(String(50), default="In-person")
    interaction_date = Column(DateTime, default=datetime.utcnow)

    raw_text = Column(Text)          # original free-text / transcript entered via chat or notes field
    summary = Column(Text)           # LLM-generated summary
    products_discussed = Column(Text)  # comma separated, extracted by LLM or chosen in form
    sentiment = Column(String(20))     # Positive / Neutral / Negative, extracted by LLM
    samples_dropped = Column(String(255))  # free text description of samples given (compliance relevant)
    materials_shared = Column(Text)
    next_steps = Column(Text)

    source = Column(String(20), default="form")  # "form" or "chat"
    created_by = Column(String(100), default="rep_demo")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    edit_history = relationship("InteractionEdit", back_populates="interaction", cascade="all, delete-orphan")


class InteractionEdit(Base):
    """Audit trail every time the Edit Interaction tool changes a record."""
    __tablename__ = "interaction_edits"

    id = Column(String(36), primary_key=True, default=gen_id)
    interaction_id = Column(String(36), ForeignKey("interactions.id"), nullable=False)
    field_changed = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    edited_by = Column(String(100), default="rep_demo")
    reason = Column(String(255))
    edited_at = Column(DateTime, default=datetime.utcnow)

    interaction = relationship("Interaction", back_populates="edit_history")


class FollowUp(Base):
    """Follow-up tasks created by the agent's schedule_followup tool."""
    __tablename__ = "followups"

    id = Column(String(36), primary_key=True, default=gen_id)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=False)
    interaction_id = Column(String(36), ForeignKey("interactions.id"), nullable=True)

    task = Column(String(500), nullable=False)
    due_date = Column(DateTime)
    status = Column(String(20), default="Open")  # Open, Done, Cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    hcp = relationship("HCP", back_populates="followups")


class SafetyFlag(Base):
    """Adverse event / compliance flags raised by the detect_adverse_event tool."""
    __tablename__ = "safety_flags"

    id = Column(String(36), primary_key=True, default=gen_id)
    interaction_id = Column(String(36), ForeignKey("interactions.id"), nullable=False)
    flag_type = Column(String(50))  # "Adverse Event", "Off-label Question", "Product Complaint"
    detail = Column(Text)
    severity = Column(String(20), default="Medium")
    requires_pv_escalation = Column(Boolean, default=False)  # pharmacovigilance escalation
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    """Stores the running conversation for the chat-based interaction logging mode."""
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=gen_id)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=True)
    messages_json = Column(Text, default="[]")  # serialized list of {role, content}
    status = Column(String(20), default="active")  # active / completed
    resulting_interaction_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
