"""
The LangGraph agent that powers the conversational side of the Log Interaction
screen.

Role of the agent
------------------
Field reps can either fill in the structured form OR just talk to the agent in
plain English ("I met Dr. Mehta today, discussed CardioFlow's new dosing data,
she seemed positive and asked for updated trial data by Friday"). The
LangGraph agent is the orchestration layer that:

  1. Understands free-form rep input using the Groq gemma2-9b-it LLM.
  2. Decides which of the 5 tools to call (it may call several in one turn -
     e.g. log_interaction AND detect_adverse_event AND schedule_followup).
  3. Executes those tools against the CRM database.
  4. Turns tool results back into a natural, confirmatory reply to the rep,
     and loops until no further tool calls are needed.
  5. Keeps enough state (hcp_id, session_id, which interaction was created)
     to support multi-turn edits ("actually change the sentiment to Positive").

Graph shape
-----------
        START -> agent -> (conditional) -> tools -> agent -> ... -> END
                    |
                    +--(no tool calls)--> END
"""
from typing import Optional

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, AIMessage

from app.agent.state import AgentState
from app.agent.tools import build_tools
from app.agent.llm import get_llm, llm_configured

SYSTEM_PROMPT = """You are the AI assistant embedded in the "Log Interaction" screen \
of a life-sciences CRM used by pharmaceutical field representatives. Your job is to \
help the rep log, edit, and follow up on interactions with Healthcare Professionals \
(HCPs) through natural conversation, instead of filling a long form.

Guidelines:
- If the rep describes a visit/call, use the log_interaction tool with the full \
  free text they gave you as raw_text so the tool's own extraction step can \
  summarize it. Don't try to summarize it yourself first.
- Always also call detect_adverse_event on the same raw text after logging an \
  interaction, passing the interaction_id you got back, as a compliance safety net.
- If the rep asks about history/context ("what did we last discuss"), use \
  get_hcp_context.
- If the rep asks to change/correct something already logged, use edit_interaction.
- If the rep mentions something to do later ("send her the new data", "follow up \
  next week"), use schedule_followup.
- You may call multiple tools in sequence within the same turn when appropriate.
- After tools run, reply to the rep in 1-3 friendly, concise sentences confirming \
  what was recorded. If a safety flag was raised, clearly mention it needs \
  compliance/pharmacovigilance review.
- If required info (like which HCP) is missing, ask a short clarifying question \
  instead of guessing.
"""


def build_graph(db):
    tools = build_tools(db)
    llm_with_tools = get_llm().bind_tools(tools) if llm_configured() else None

    def agent_node(state: AgentState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        if llm_configured():
            response = llm_with_tools.invoke(messages)
        else:
            # Offline demo mode: no live Groq key configured.
            response = AIMessage(
                content=(
                    "[offline mode - set GROQ_API_KEY to enable the live gemma2-9b-it agent] "
                    "I can't call tools without a configured LLM, but the rest of the CRM "
                    "(structured form, DB, tool endpoints) works normally."
                )
            )
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


def run_turn(db, messages: list, hcp_id: Optional[str] = None, session_id: Optional[str] = None):
    """Run one user turn through the compiled graph and return the final state."""
    app_graph = build_graph(db)
    initial_state: AgentState = {
        "messages": messages,
        "hcp_id": hcp_id,
        "session_id": session_id,
        "tool_calls_made": [],
        "interaction_id": None,
    }
    final_state = app_graph.invoke(initial_state)
    return final_state
