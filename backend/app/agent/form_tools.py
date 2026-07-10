"""
LangGraph tools for the form-filling agent.

Tool 1 – log_interaction
  The LLM receives natural language, extracts structured fields, and returns
  them as JSON so the agent can merge them into InteractionState.
"""

import json
import traceback
from datetime import date, datetime, timedelta

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.agent.llm import EXTRACTION_PROMPT, EDIT_EXTRACTION_PROMPT, safe_invoke, safe_edit_invoke


# ── Pydantic schema for LLM extraction ───────────────────────────────────────

class InteractionExtraction(BaseModel):
    hcp_name: str = Field(default="", description="Full name of the HCP (e.g. Dr. Smith)")
    interaction_type: str = Field(default="Visit", description="Type of interaction: Visit, Call, Email, Meeting, etc.")
    channel: str = Field(default="In-person", description="Channel: In-person, Phone, Video, Email, etc.")
    interaction_date: str = Field(default="", description="ISO date string like 2026-07-09 or the date mentioned")
    interaction_time: str = Field(default="", description="Time of interaction in HH:MM format")
    products_discussed: str = Field(default="", description="Comma-separated product/drug names discussed")
    sentiment: str = Field(default="Neutral", description="Positive, Neutral, or Negative")
    samples_dropped: str = Field(default="", description="Description of samples distributed")
    materials_shared: list[str] = Field(default_factory=list, description="Array of materials shared: brochures, leaflets, PDFs, etc.")
    next_steps: str = Field(default="", description="Follow-up actions, next steps, or scheduled meetings")
    summary: str = Field(default="", description="Summary or outcomes of the interaction")
    attendees: str = Field(default="", description="Names of attendees or participants")
    raw_text: str = Field(default="", description="Original free-text notes verbatim")


# ── Tool 1: log_interaction ──────────────────────────────────────────────────

@tool
def log_interaction(notes: str) -> str:
    """
    Extract structured interaction data from the representative's free-text notes.

    Call this tool when the user describes an interaction with an HCP.
    The notes parameter must be the complete user message containing the
    interaction details.

    Returns a JSON string with all extracted InteractionExtraction fields.
    """
    print(f"\n" + "=" * 70)
    print(f"===== LOG_INTERACTION TOOL CALLED =====")
    print(f"Notes: {notes}")
    print(f"Notes length: {len(notes)}")

    # Inject today's date and current time into the prompt for date/time inference
    today = date.today()
    now = datetime.now()
    today_str = today.isoformat()
    time_str = now.strftime("%H:%M")
    yesterday_str = (today - timedelta(days=1)).isoformat()

    prompt = EXTRACTION_PROMPT.replace("{today_date}", today_str).replace("{yesterday}", yesterday_str).replace("{current_time}", time_str)

    print(f"\n----- STEP 1: FULL PROMPT SENT TO LLM -----")
    print(f"System prompt length: {len(prompt)}")
    print(f"System prompt content:")
    print(prompt)
    print(f"\nUser message: Extract the fields from these notes:\n\n{notes}")
    print(f"----- END OF PROMPT -----\n")

    extraction_messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Extract the fields from these notes:\n\n{notes}"},
    ]

    raw = safe_invoke(extraction_messages)

    print(f"\n----- STEP 2: RAW LLM RESPONSE -----")
    print(f"Response length: {len(raw)}")
    print(f"Response content:")
    print(raw)
    print(f"----- END OF RAW RESPONSE -----\n")

    try:
        parsed = json.loads(raw)
        print(f"\n----- STEP 3: PARSED JSON -----")
        print(json.dumps(parsed, indent=2))
        print(f"Parsed keys: {list(parsed.keys())}")
        print(f"----- END OF PARSED JSON -----\n")

        # Overwrite raw_text with original notes (in case LLM modified it)
        parsed["raw_text"] = notes

        print(f"\n----- STEP 4: VALIDATED InteractionExtraction -----")
        validated = InteractionExtraction(**parsed)
        validated_json = validated.model_dump_json()
        print(validated_json)
        print(f"----- END OF VALIDATED -----\n")
    except (json.JSONDecodeError, Exception) as e:
        print(f"\n!!!!! EXTRACTION PARSE ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        validated = InteractionExtraction(raw_text=notes)
        validated_json = validated.model_dump_json()
        print(f"Falling back to raw_text only: {validated_json}")

    print(f"\n----- STEP 5: FINAL JSON RETURNED BY log_interaction -----")
    print(validated_json)
    print(f"----- END OF FINAL JSON -----")
    print(f"===== LOG_INTERACTION COMPLETE =====")
    print("=" * 70 + "\n")
    return validated_json


# ── Tool 2: edit_interaction ──────────────────────────────────────────────────

class EditExtraction(BaseModel):
    hcp_name: str = Field(default="")
    interaction_type: str = Field(default="")
    channel: str = Field(default="")
    interaction_date: str = Field(default="")
    summary: str = Field(default="")
    products_discussed: str = Field(default="")
    sentiment: str = Field(default="")
    samples_dropped: str = Field(default="")
    materials_shared: str = Field(default="")
    next_steps: str = Field(default="")


@tool
def edit_interaction(changes: str) -> str:
    """
    Update specific fields in the interaction form.

    The user describes what they want to change (e.g. "change the sentiment
    to Negative").  Only fields explicitly mentioned are returned — the
    merge logic will leave every other field unchanged.

    Returns a JSON string containing only the fields to update.
    """
    edit_messages = [
        {"role": "system", "content": EDIT_EXTRACTION_PROMPT},
        {"role": "user", "content": f"Extract the field updates from this request:\n\n{changes}"},
    ]

    raw = safe_edit_invoke(edit_messages)

    try:
        parsed = json.loads(raw)
        # Only keep fields that are part of EditExtraction
        valid_keys = set(EditExtraction.model_fields.keys())
        filtered = {k: v for k, v in parsed.items() if k in valid_keys and v}
        if filtered:
            return json.dumps(filtered)
    except (json.JSONDecodeError, Exception):
        pass

    return json.dumps({})


# ── Tool 4: validate_interaction ──────────────────────────────────────────────

_REQUIRED_FIELDS = ["hcp_name", "interaction_date", "products_discussed", "sentiment"]
_ALL_FORM_FIELDS = [
    "hcp_name", "interaction_type", "channel", "interaction_date",
    "raw_text", "summary", "products_discussed", "sentiment",
    "samples_dropped", "materials_shared", "next_steps",
]


@tool
def validate_interaction(form_data_json: str) -> str:
    """
    Validate the current interaction form data for completeness.

    Checks which fields are filled, identifies missing required fields,
    and returns a validation report under the ``report`` key.
    """
    try:
        data = json.loads(form_data_json)
    except Exception:
        return json.dumps({
            "valid": False,
            "filled": {},
            "missing_required": _REQUIRED_FIELDS,
            "report": "Could not parse form data.",
        })

    filled = {f: bool(data.get(f)) for f in _ALL_FORM_FIELDS}
    missing_required = [f for f in _REQUIRED_FIELDS if not filled[f]]

    if not missing_required:
        summary = "All required fields are filled."
    else:
        labels = [f.replace("_", " ") for f in missing_required]
        summary = f"Missing required field{'s' if len(labels) > 1 else ''}: {', '.join(labels)}."

    return json.dumps({
        "valid": len(missing_required) == 0,
        "filled": filled,
        "missing_required": missing_required,
        "report": summary,
    })


# ── Tool 5: summarize_interaction ─────────────────────────────────────────────

_SUMMARY_KEY_FIELDS = ["hcp_name", "interaction_date", "products_discussed", "sentiment"]


def _build_form_summary(data: dict) -> str:
    """Build a human-readable narrative from form data fields."""
    parts = []

    if data.get("hcp_name") and data.get("interaction_date"):
        parts.append(f"Interaction with {data['hcp_name']} on {data['interaction_date']}")
    elif data.get("hcp_name"):
        parts.append(f"Interaction with {data['hcp_name']}")

    type_ch = []
    if data.get("interaction_type"):
        type_ch.append(data["interaction_type"])
    if data.get("channel"):
        type_ch.append(data["channel"])
    if type_ch:
        parts.append(f"Type: {' / '.join(type_ch)}")

    if data.get("products_discussed"):
        parts.append(f"Products discussed: {data['products_discussed']}")

    if data.get("sentiment"):
        parts.append(f"Sentiment: {data['sentiment']}")

    if data.get("summary"):
        parts.append(f"Notes: {data['summary']}")

    if data.get("samples_dropped"):
        parts.append(f"Samples dropped: {data['samples_dropped']}")

    if data.get("materials_shared"):
        parts.append(f"Materials shared: {data['materials_shared']}")

    if data.get("next_steps"):
        parts.append(f"Next steps: {data['next_steps']}")

    return " | ".join(parts) if parts else "No interaction data available to summarize."


@tool
def summarize_interaction(form_data_json: str) -> str:
    """
    Generate a human-readable summary of the current interaction form data.

    Builds a narrative from the filled fields — HCP name, date, products,
    sentiment, samples, materials, and next steps.  Returns a JSON object
    with a ``report`` string and a ``complete`` boolean indicating whether
    enough key fields are present.
    """
    try:
        data = json.loads(form_data_json)
    except Exception:
        return json.dumps({
            "report": "No form data available to summarize.",
            "complete": False,
        })

    summary = _build_form_summary(data)
    filled_count = sum(1 for f in _SUMMARY_KEY_FIELDS if data.get(f))

    return json.dumps({
        "report": summary,
        "complete": filled_count >= 2,
    })


# ── Tool 3: clear_interaction ─────────────────────────────────────────────────

@tool
def clear_interaction() -> str:
    """
    Reset the interaction form to its empty state.

    Call this when the user wants to start over, clear all fields,
    or discard the current form data entirely.
    """
    return json.dumps({"_action": "clear"})


# ── Tool registry ─────────────────────────────────────────────────────────────

FORM_TOOLS = [log_interaction, edit_interaction, clear_interaction, validate_interaction, summarize_interaction]
