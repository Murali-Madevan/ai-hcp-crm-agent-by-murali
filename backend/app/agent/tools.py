"""
The five sales-related tools exposed to the LangGraph agent.

1. log_interaction        - captures/creates a new HCP interaction, using the LLM
                             (Groq gemma2-9b-it) to summarize free text and extract
                             structured entities (products discussed, sentiment,
                             samples dropped, next steps).
2. edit_interaction       - modifies a previously logged interaction and keeps a
                             full audit trail of every change (field, old/new value,
                             reason).
3. get_hcp_context        - looks up an HCP's profile plus their recent interaction
                             history, so the agent/LLM can ground its answers
                             ("what did we last discuss with Dr. Rao?").
4. schedule_followup      - creates a follow-up task/reminder tied to an HCP and
                             (optionally) a specific interaction.
5. detect_adverse_event   - runs the raw interaction text through the LLM looking
                             for adverse-event mentions, off-label questions, or
                             product complaints, and raises a SafetyFlag that would
                             route to pharmacovigilance/compliance in a real system.

Tools are produced by `build_tools(db)` so each one closes over a request-scoped
SQLAlchemy session.
"""
import json
from datetime import datetime
from typing import Optional, List

from dateutil import parser as dateparser
from langchain_core.tools import tool

from app.agent.llm import safe_invoke, llm_configured
from app.models import HCP, Interaction, InteractionEdit, FollowUp, SafetyFlag


# ---------------------------------------------------------------------------
# LLM helper prompts
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """You are a life-sciences CRM assistant. A pharmaceutical \
field representative has just described an interaction with a Healthcare \
Professional (HCP). Extract structured information and respond with ONLY a \
JSON object (no markdown, no commentary) with these exact keys:

{
  "summary": "1-3 sentence neutral summary of what happened",
  "products_discussed": "comma separated product/drug names mentioned, or empty string",
  "sentiment": "Positive, Neutral, or Negative - the HCP's reaction to the discussion",
  "samples_dropped": "short description of any samples given, or empty string",
  "next_steps": "short description of any agreed next steps, or empty string"
}
"""

AE_DETECTION_SYSTEM_PROMPT = """You are a pharmacovigilance and compliance screening \
assistant for a life-sciences CRM. Read the field rep's interaction notes and decide \
whether it contains any of the following, responding with ONLY a JSON object:

{
  "adverse_event_detected": true/false,
  "off_label_question_detected": true/false,
  "product_complaint_detected": true/false,
  "detail": "short factual explanation citing the relevant phrase(s), or empty string",
  "severity": "Low, Medium, or High"
}

An adverse event is any mention that a patient experienced a side effect, unexpected \
reaction, or worsening condition possibly related to a medication. An off-label \
question is the HCP asking about a use not in the approved label. Be conservative but \
do not miss genuine safety signals.
"""


def _extract_json(raw: str) -> dict:
    """Best-effort parse of the LLM's JSON reply, tolerant of stray text/markdown fences."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {}


def build_tools(db):
    """Return the 5 LangChain tools, each bound to the given DB session."""

    @tool
    def log_interaction(
        hcp_id: str,
        raw_text: str,
        interaction_type: str = "Visit",
        channel: str = "In-person",
        source: str = "chat",
    ) -> str:
        """Log a new HCP interaction. Give the HCP's id, the free-text description of
        what happened during the visit/call (raw_text), the interaction_type
        (Visit, Call, Email, Conference) and the channel (In-person, Phone, Video,
        Email). The LLM will summarize the text and extract products discussed,
        sentiment, samples dropped and next steps automatically. Returns a JSON
        string describing the created interaction."""
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        extracted = {}
        if raw_text:
            reply = safe_invoke(
                [
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": raw_text},
                ]
            )
            extracted = _extract_json(reply)

        interaction = Interaction(
            hcp_id=hcp_id,
            interaction_type=interaction_type,
            channel=channel,
            raw_text=raw_text,
            summary=extracted.get("summary") or (raw_text[:200] if raw_text else ""),
            products_discussed=extracted.get("products_discussed", ""),
            sentiment=extracted.get("sentiment", "Neutral"),
            samples_dropped=extracted.get("samples_dropped", ""),
            next_steps=extracted.get("next_steps", ""),
            source=source,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return json.dumps(
            {
                "interaction_id": interaction.id,
                "hcp_name": hcp.name,
                "summary": interaction.summary,
                "products_discussed": interaction.products_discussed,
                "sentiment": interaction.sentiment,
                "samples_dropped": interaction.samples_dropped,
                "next_steps": interaction.next_steps,
                "llm_used": llm_configured(),
            }
        )

    @tool
    def edit_interaction(
        interaction_id: str,
        field: str,
        new_value: str,
        reason: str = "Correction requested by rep",
    ) -> str:
        """Edit a field of a previously logged interaction. Valid fields:
        interaction_type, channel, summary, products_discussed, sentiment,
        samples_dropped, materials_shared, next_steps, raw_text. Every edit is
        recorded in an audit trail with the old value, new value and reason.
        Returns a JSON string confirming the change."""
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        if not hasattr(interaction, field):
            return json.dumps({"error": f"'{field}' is not an editable field"})

        old_value = getattr(interaction, field)
        setattr(interaction, field, new_value)
        interaction.updated_at = datetime.utcnow()

        edit = InteractionEdit(
            interaction_id=interaction_id,
            field_changed=field,
            old_value=str(old_value) if old_value is not None else "",
            new_value=new_value,
            reason=reason,
        )
        db.add(edit)
        db.commit()

        return json.dumps(
            {
                "interaction_id": interaction_id,
                "field": field,
                "old_value": old_value,
                "new_value": new_value,
                "reason": reason,
            }
        )

    @tool
    def get_hcp_context(hcp_id: Optional[str] = None, hcp_name: Optional[str] = None) -> str:
        """Look up an HCP's profile (specialty, institution, segment) plus their
        5 most recent logged interactions, for grounding the conversation. Provide
        either hcp_id or hcp_name (partial, case-insensitive match on name)."""
        query = db.query(HCP)
        if hcp_id:
            hcp = query.filter(HCP.id == hcp_id).first()
        elif hcp_name:
            hcp = query.filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        else:
            return json.dumps({"error": "Provide hcp_id or hcp_name"})

        if not hcp:
            return json.dumps({"error": "HCP not found"})

        recent = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.interaction_date.desc())
            .limit(5)
            .all()
        )

        return json.dumps(
            {
                "hcp_id": hcp.id,
                "name": hcp.name,
                "specialty": hcp.specialty,
                "institution": hcp.institution,
                "segment": hcp.segment,
                "recent_interactions": [
                    {
                        "date": str(i.interaction_date),
                        "type": i.interaction_type,
                        "summary": i.summary,
                        "products_discussed": i.products_discussed,
                        "sentiment": i.sentiment,
                    }
                    for i in recent
                ],
            }
        )

    @tool
    def schedule_followup(
        hcp_id: str, task: str, due_date: Optional[str] = None, interaction_id: Optional[str] = None
    ) -> str:
        """Create a follow-up task/reminder for an HCP, e.g. 'send updated efficacy
        data' or 'schedule lunch-and-learn'. due_date can be a natural-language or
        ISO date string (e.g. 'next Friday', '2026-08-01'); if omitted no due date
        is set. Optionally link the follow-up to the interaction that generated it."""
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        parsed_due = None
        if due_date:
            try:
                parsed_due = dateparser.parse(due_date, fuzzy=True)
            except Exception:
                parsed_due = None

        followup = FollowUp(
            hcp_id=hcp_id,
            interaction_id=interaction_id,
            task=task,
            due_date=parsed_due,
        )
        db.add(followup)
        db.commit()
        db.refresh(followup)

        return json.dumps(
            {
                "followup_id": followup.id,
                "hcp_name": hcp.name,
                "task": followup.task,
                "due_date": str(followup.due_date) if followup.due_date else None,
                "status": followup.status,
            }
        )

    @tool
    def detect_adverse_event(interaction_text: str, interaction_id: Optional[str] = None) -> str:
        """Scan interaction text for adverse events, off-label usage questions, or
        product complaints, which in a real pharma CRM must be escalated to
        pharmacovigilance/compliance. If a real signal is found, a SafetyFlag record
        is created (linked to interaction_id if provided). Always call this on every
        logged interaction's raw text as a safety net."""
        reply = safe_invoke(
            [
                {"role": "system", "content": AE_DETECTION_SYSTEM_PROMPT},
                {"role": "user", "content": interaction_text},
            ]
        )
        result = _extract_json(reply)

        flags_created = []
        flag_map = [
            ("adverse_event_detected", "Adverse Event", True),
            ("off_label_question_detected", "Off-label Question", False),
            ("product_complaint_detected", "Product Complaint", False),
        ]
        for key, label, requires_pv in flag_map:
            if result.get(key):
                flag = SafetyFlag(
                    interaction_id=interaction_id or "unlinked",
                    flag_type=label,
                    detail=result.get("detail", ""),
                    severity=result.get("severity", "Medium"),
                    requires_pv_escalation=requires_pv,
                )
                if interaction_id:
                    db.add(flag)
                    db.commit()
                    db.refresh(flag)
                    flags_created.append(
                        {
                            "flag_id": flag.id,
                            "flag_type": flag.flag_type,
                            "severity": flag.severity,
                            "requires_pv_escalation": flag.requires_pv_escalation,
                        }
                    )
                else:
                    flags_created.append({"flag_type": label, "note": "no interaction_id, not persisted"})

        return json.dumps({"flags_created": flags_created, "raw_analysis": result})

    return [log_interaction, edit_interaction, get_hcp_context, schedule_followup, detect_adverse_event]
