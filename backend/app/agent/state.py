from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class InteractionState(TypedDict):
    """Thirteen fields matching the Interaction Details form and DB model.

    This is the SINGLE source of truth for the form.  The frontend
    Redux store mirrors these exact keys.  The LangGraph graph
    reads/writes this as ``FormAgentState.form_data``.  Every tool
    receives and returns field values using these keys — no
    transformation layer.
    """

    hcp_name: str
    interaction_type: str
    channel: str
    interaction_date: str
    interaction_time: str
    raw_text: str
    summary: str
    products_discussed: str
    sentiment: str
    samples_dropped: str
    materials_shared: str
    next_steps: str
    attendees: str


# ── Default empty state (used by Redux initial state and graph reset) ──────────

EMPTY_INTERACTION_STATE: InteractionState = {
    "hcp_name": "",
    "interaction_type": "Visit",
    "channel": "In-person",
    "interaction_date": "",
    "interaction_time": "",
    "raw_text": "",
    "summary": "",
    "products_discussed": "",
    "sentiment": "",
    "samples_dropped": "",
    "materials_shared": "",
    "next_steps": "",
    "attendees": "",
}


class FormAgentState(TypedDict):
    """State that flows through the LangGraph StateGraph.

    Nodes
        ``messages`` — conversation history (automatically merged by add_messages)
        ``form_data`` — the canonical InteractionState that every tool reads/writes
        ``hcp_id`` — the selected HCP id, set once at session start
        ``session_id`` — ChatSession UUID, persisted across turns
        ``clear_form`` — set to ``True`` by ``submit_interaction``; the router
                         reads this after the graph finishes and tells the
                         frontend to reset to ``EMPTY_INTERACTION_STATE``
    """

    messages: Annotated[list, add_messages]
    form_data: InteractionState
    hcp_id: Optional[str]
    session_id: Optional[str]
    clear_form: bool
