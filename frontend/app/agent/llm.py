"""
LLM interface for the form-filling agent.

Provides a real LLM (ChatGroq) bound to the five form tools.

* ``llm_invoke(messages)`` — for the graph agent node.  Returns ``AIMessage``
  with either ``tool_calls`` or a final text reply.

* ``safe_invoke(messages)`` / ``safe_edit_invoke(messages)`` — for the
  ``log_interaction`` and ``edit_interaction`` tools to perform structured
  extraction.  Returns raw text (the LLM is prompted to emit JSON).

Raises ``RuntimeError`` if ``GROQ_API_KEY`` is not set or is a placeholder.
No keyword routing, no regex fallback, no simulation.
"""

import os
import json
import traceback

from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage


# ── Cached LLM instances ──────────────────────────────────────────────────────

_llm = None
_bound_llm = None


def get_llm() -> ChatGroq:
    """Return a configured ``ChatGroq`` instance (cached after first call)."""
    global _llm
    if _llm is None:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        print(f"\n========== LLM INIT ==========")
        print(f"GROQ_API_KEY from env: |{api_key}|")
        mask = (api_key[:8] + "..." + api_key[-4:]) if api_key and api_key != "your-groq-api-key-here" else api_key
        print(f"GROQ_API_KEY (masked): {mask}")
        print(f"GROQ_MODEL: {model}")
        print(f"GROQ_API_KEY length: {len(api_key) if api_key else 0}")
        print(f"==============================\n")

        if not api_key or api_key == "your-groq-api-key-here":
            raise RuntimeError(
                "GROQ_API_KEY is not configured.  Set GROQ_API_KEY in your "
                ".env file or environment variables."
            )

        _llm = ChatGroq(api_key=api_key, model=model)
    return _llm


def get_bound_llm() -> ChatGroq:
    """Return the LLM with ``FORM_TOOLS`` bound via ``bind_tools()``.

    The LLM will use the tools' docstrings and Pydantic parameter schemas
    to decide when to emit ``tool_calls``.
    """
    global _bound_llm
    if _bound_llm is None:
        from app.agent.form_tools import FORM_TOOLS  # lazy import avoids circularity
        _bound_llm = get_llm().bind_tools(FORM_TOOLS)
    return _bound_llm


# ── Graph entry point ─────────────────────────────────────────────────────────

def llm_invoke(messages: list) -> AIMessage:
    """Call the tool-bound LLM and return the resulting ``AIMessage``.

    The LLM decides — based on the conversation and tool schema — whether
    to respond with ``tool_calls`` or a plain text reply.
    """
    print(f"\n===== LLM_INVOKE =====")
    print(f"Messages count: {len(messages)}")
    for i, m in enumerate(messages):
        role = m.get("role", type(m).__name__) if isinstance(m, dict) else type(m).__name__
        content_preview = ""
        if isinstance(m, dict):
            content_preview = str(m.get("content", ""))[:100]
        elif hasattr(m, "content"):
            content_preview = str(m.content)[:100]
        print(f"  msg[{i}] role={role} content='{content_preview}'")
    try:
        result = get_bound_llm().invoke(messages)
        print(f"LLM response type: {type(result).__name__}")
        print(f"LLM has tool_calls: {hasattr(result, 'tool_calls') and len(result.tool_calls) > 0}")
        if hasattr(result, 'tool_calls') and result.tool_calls:
            for tc in result.tool_calls:
                print(f"  Tool call: name={tc.get('name', '?')} args={json.dumps(tc.get('args', {}))[:200]}")
        print(f"LLM response content (first 150): {str(result.content)[:150]}")
        print(f"======================")
        return result
    except Exception as e:
        print(f"\n!!!!! LLM_INVOKE ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        print(f"!!!!! ================\n")
        raise


# ── Tool-internal extraction wrappers ─────────────────────────────────────────

def safe_invoke(messages: list, temperature: float = 0.2) -> str:
    """Call the LLM for structured extraction and return the response text.

    Used by the ``log_interaction`` tool.  The LLM should return JSON
    matching ``InteractionExtraction`` as instructed by ``EXTRACTION_PROMPT``.
    """
    print(f"\n===== SAFE_INVOKE (extraction) =====")
    print(f"Messages count: {len(messages)}")
    for i, m in enumerate(messages):
        role = m.get("role", "?") if isinstance(m, dict) else type(m).__name__
        content_len = len(str(m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")))
        print(f"  msg[{i}] role={role} content_length={content_len}")
    print(f"Calling LLM...")
    result = get_llm().invoke(messages, temperature=temperature)
    print(f"LLM returned. Response length: {len(str(result.content))}")
    print(f"FULL response content:")
    print(str(result.content))
    print(f"====================================")
    return result.content


def safe_edit_invoke(messages: list, temperature: float = 0.2) -> str:
    """Call the LLM for edit extraction and return the response text.

    Used by the ``edit_interaction`` tool.  The LLM should return JSON
    matching ``EditExtraction`` as instructed by ``EDIT_EXTRACTION_PROMPT``.
    """
    print(f"\n===== SAFE_EDIT_INVOKE =====")
    print(f"Messages: {len(messages)}")
    result = get_llm().invoke(messages, temperature=temperature)
    print(f"Safe edit response (first 400): {str(result.content)[:400]}")
    print(f"=============================")
    return result.content


# ── System prompt for the agent LLM (prepended before every call) ─────────────

def build_system_prompt(form_data: dict) -> str:
    """Build the system message that tells the LLM the current form state."""
    filled = {k: v for k, v in form_data.items() if v}
    return (
        "You are an AI assistant in a CRM for pharmaceutical field "
        "representatives.  Your job is to help the rep log interactions "
        "with Healthcare Professionals (HCPs) through natural conversation.\n\n"

        "CRITICAL RULES:\n"
        "1. When the user describes an interaction with an HCP (e.g. 'I met with Dr. X and discussed Y'), "
        "you MUST call the 'log_interaction' tool with the user's COMPLETE message as the 'notes' parameter. "
        "This is the ONLY way to extract structured data from the conversation.\n"
        "2. After a tool executes, respond conversationally to the user.\n"
        "3. If the user wants to change specific fields, call 'edit_interaction'.\n"
        "4. If the user wants to reset the form, call 'clear_interaction'.\n\n"

        "Available tools:\n"
        "- log_interaction(notes: str): Extract ALL structured fields from the user's free-text notes. "
        "Call this FIRST when the user describes an HCP interaction.\n"
        "- edit_interaction(changes: str): Update specific form fields.\n"
        "- clear_interaction(): Reset the form to empty.\n"
        "- validate_interaction(form_data_json: str): Check which required fields are missing.\n"
        "- summarize_interaction(form_data_json: str): Build a human-readable summary.\n\n"

        "Current interaction form data:\n"
        f"{json.dumps(form_data, indent=2)}\n\n"
        f"Already filled fields: {list(filled.keys()) if filled else 'none'}"
    )


# ── Extraction prompts (consumed inside log_interaction / edit_interaction) ───

EXTRACTION_PROMPT = """You are a CRM assistant for pharmaceutical field representatives. Today's date is {today_date} and the current time is {current_time}.

Extract the following fields from the representative's notes and return ONLY a JSON object (no markdown, no commentary, no trailing commas) with these exact keys:

{
  "hcp_name": "...",
  "interaction_type": "...",
  "channel": "...",
  "interaction_date": "...",
  "interaction_time": "...",
  "products_discussed": "...",
  "sentiment": "...",
  "samples_dropped": "...",
  "materials_shared": [...],
  "next_steps": "...",
  "summary": "...",
  "attendees": "...",
  "raw_text": "..."
}

EXTRACTION RULES (follow these exactly for EVERY field):

1. hcp_name — Full name of the doctor/HCP. Extract the complete name including title (Dr., Professor, etc.). NEVER leave blank if a doctor is mentioned.

2. interaction_type — Infer from context: "met with" = "Visit", "called" = "Call", "emailed" = "Email", "meeting" = "Meeting". Default to "Visit" if unclear.

3. channel — Infer from context: in-person meeting = "In-person", phone call = "Phone", video call = "Video", email = "Email". Default to "In-person" if unclear. "Met with" implies "In-person" unless stated otherwise.

4. interaction_date — ISO format YYYY-MM-DD. TODAY is {today_date}. If user says "today" → use {today_date}. If "yesterday" → use {yesterday}. If "next Friday" → compute from today. If "next week" → use 7 days from today. If a specific date is given (e.g. "July 9th") → use that date with correct year. NEVER leave blank if any temporal reference exists.

5. interaction_time — HH:MM format (24-hour). If user mentions a time → extract it. If NO time is mentioned → use {current_time} (the current time). NEVER leave blank — always provide a reasonable time.

6. products_discussed — Comma-separated list of ALL products, drugs, treatments, therapies, or diseases discussed. Include brand names (CardioFlow) and conditions (hypertension). NEVER leave blank if any clinical topic is mentioned.

7. sentiment — One of: "Positive", "Neutral", "Negative". "very positive", "enthusiastic", "excited", "pleased" → "Positive". "neutral", "okay", "fine" → "Neutral". "negative", "concerned", "worried", "upset" → "Negative". NEVER leave blank — always pick one based on tone.

8. samples_dropped — Describe any samples left with the doctor. If the notes mention leaving boxes, packs, or samples → describe them. If NO samples are mentioned → empty string "".

9. materials_shared — JSON array of ALL materials shared. Each material is a separate string item. Recognize: "brochure"/"brochures", "leaflet"/"leaflets", "patient education material", "PDF"/"PDFs", "clinical paper", "dosage guide", "efficacy data", "clinical studies", "data sheets", etc. Example: ["brochures", "patient education material", "efficacy data"]. Extract even if briefly mentioned. NEVER return an empty array if any material is referenced.

10. next_steps — Extract ALL follow-up actions: scheduled meetings, emails to send, data to provide, reminders, callbacks. Include all details (who, what, when). NEVER leave blank if future actions are mentioned.

11. summary — A concise paragraph summarizing the interaction: what was discussed, the doctor's reaction, any requests or feedback from the doctor. This should capture the OUTCOME of the interaction.

12. attendees — List ALL participants: the HCP (doctor name) and any other people mentioned. At minimum, include the doctor's name. Never leave blank — always include the HCP name.

13. raw_text — Copy the ENTIRE original notes text here verbatim. Do not modify, truncate, or summarize this field.

CRITICAL INSTRUCTIONS:
- You MUST populate EVERY field. Only leave a field as "" if the information is genuinely impossible to infer.
- Be aggressive in inference. "met with" → interaction_type "Visit", channel "In-person". "today" → today's date. Positive language → sentiment "Positive".
- The doctor's name is always an attendee — NEVER leave attendees blank.
- If no time is mentioned, use {current_time}.
- If no date is mentioned but it's implied (e.g. "today" or recent context), use {today_date}.
"""

EDIT_EXTRACTION_PROMPT = """You are a CRM assistant. The user wants to update
specific fields in an interaction record.  Return ONLY a JSON object with
exactly the fields the user explicitly asked to change — leave out every
other field.  Valid field keys:

  hcp_name, interaction_type, channel, interaction_date, summary,
  products_discussed, sentiment, samples_dropped, materials_shared, next_steps

Example:
  User: "Change the sentiment to Negative"
  Response: {"sentiment": "Negative"}

  User: "The doctor is actually Dr. Chen, and it was a virtual visit"
  Response: {"hcp_name": "Dr. Chen", "channel": "Virtual"}
"""
