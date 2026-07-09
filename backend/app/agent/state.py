from typing import Annotated, Optional, List
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state that flows through the LangGraph graph for one turn of the
    Log Interaction chat assistant.
    """
    messages: Annotated[list, add_messages]
    hcp_id: Optional[str]
    session_id: Optional[str]
    tool_calls_made: List[str]
    interaction_id: Optional[str]
