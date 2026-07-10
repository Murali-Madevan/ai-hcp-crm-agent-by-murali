"""
LangGraph StateGraph for the AI-driven form-filling assistant.

ReAct pattern ::

    START ──▶ agent ──▶ tools_condition ──▶ tools ──▶ agent ──▶ ... ──▶ END
                            │
                            └── (no tool calls) ──▶ END

*agent*   calls ``ChatGroq.bind_tools(FORM_TOOLS).invoke(messages)`` to decide
          the next action.  After a ``ToolMessage`` it merges the extraction
          result into ``form_data``, then asks the LLM for a text response.

*tools*   LangGraph's ``ToolNode`` — executes whatever tool the LLM selected
          and feeds the result back as a ``ToolMessage``.

**No keyword routing.  No if/else intent detection.  No regex fallback.**
"""

import json

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import ToolMessage

from app.agent.state import FormAgentState, EMPTY_INTERACTION_STATE
from app.agent.form_tools import FORM_TOOLS
from app.agent.llm import llm_invoke, build_system_prompt


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_form_graph(tools: list | None = None):
    """Build and return a compiled ``StateGraph(FormAgentState)``.

    Parameters
    ----------
    tools : list of :class:`langchain_core.tools.Tool`, optional
        Injected into the ``ToolNode``.  Defaults to ``FORM_TOOLS``.
    """
    if tools is None:
        tools = FORM_TOOLS

    def agent_node(state: FormAgentState) -> dict:
        messages = list(state["messages"])
        form = dict(state["form_data"])

        print(f"\n===== AGENT NODE =====")
        print(f"Messages count: {len(messages)}")
        for i, m in enumerate(messages):
            mtype = type(m).__name__
            if isinstance(m, dict):
                mrole = m.get("role", "?")
                mcontent = str(m.get("content", ""))[:100]
                print(f"  msg[{i}] dict role={mrole} content='{mcontent}'")
            else:
                mcontent = str(getattr(m, 'content', ''))[:100]
                mtc = hasattr(m, 'tool_calls') and getattr(m, 'tool_calls', [])
                print(f"  msg[{i}] {mtype} content='{mcontent}' tool_calls={bool(mtc)}")
        print(f"Form data filled keys: {{k for k,v in form.items() if v}}")

        # ── Post-tool: handle clear / merge result ──────────────────────
        if messages and isinstance(messages[-1], ToolMessage):
            print(f"\n[AGENT] Last message IS a ToolMessage")
            try:
                data = json.loads(messages[-1].content or "{}")
                print(f"Tool output parsed keys: {list(data.keys())}")
                if data.get("_action") == "clear":
                    print("Clear action detected, resetting form...")
                    ai_msg = llm_invoke(
                        _with_context(messages, dict(EMPTY_INTERACTION_STATE))
                    )
                    return {
                        "messages": [ai_msg],
                        "form_data": dict(EMPTY_INTERACTION_STATE),
                        "clear_form": True,
                    }
            except Exception as e:
                print(f"Tool output parse error: {e}")

            form = _merge_tool_into_form(messages[-1], form)
            print(f"[AGENT] After merge, form filled keys: {{k for k,v in form.items() if v}}")
        else:
            print(f"\n[AGENT] Last message is NOT ToolMessage, calling LLM directly")

        # Ask the LLM (bound to tools) what to do next
        print(f"\n[AGENT] Calling llm_invoke (bind_tools) with {len(_with_context(messages, form))} messages...")
        ai_msg = llm_invoke(_with_context(messages, form))
        print(f"\n[AGENT] AI response received")
        print(f"  type: {type(ai_msg).__name__}")
        print(f"  has tool_calls: {hasattr(ai_msg, 'tool_calls') and len(ai_msg.tool_calls) > 0}")
        if hasattr(ai_msg, 'tool_calls') and ai_msg.tool_calls:
            for tc in ai_msg.tool_calls:
                print(f"  Tool call: name={tc.get('name', '?')} args={json.dumps(tc.get('args', {}))[:300]}")
        print(f"  text content (first 150): {str(ai_msg.content)[:150]}")
        print(f"========================\n")
        return {"messages": [ai_msg], "form_data": form}

    tool_node = ToolNode(tools)

    graph = StateGraph(FormAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# ── Context builder ───────────────────────────────────────────────────────────

def _with_context(messages: list, form: dict) -> list:
    """Prepend a system message that tells the LLM the current form state.

    This is the only way the LLM knows what fields have already been filled
    when deciding whether to call ``log_interaction`` or ``edit_interaction``.
    """
    return [{"role": "system", "content": build_system_prompt(form)}] + list(messages)


# ── Merge helper ──────────────────────────────────────────────────────────────

def _merge_tool_into_form(tool_msg: object, form: dict) -> dict:
    """Merge a tool's JSON output into form_data.

    Every key present in the tool output that matches a known
    ``InteractionState`` field and has a truthy value is merged into
    the form (overwriting or adding as needed).

    Read-only tool outputs (validate, summarize) carry keys like ``report``,
    ``valid``, ``complete`` that don't match any ``InteractionState`` field,
    so they leave *form* untouched.
    """
    raw: str = ""
    if isinstance(tool_msg, ToolMessage):
        raw = tool_msg.content or ""
    elif isinstance(tool_msg, str):
        raw = tool_msg
    else:
        return form

    try:
        data = json.loads(raw)
    except Exception:
        return form

    from app.agent.state import InteractionState
    known_keys = set(InteractionState.__annotations__.keys())

    print(f"\n" + "=" * 70)
    print(f"===== MERGE TOOL INTO FORM =====")
    print(f"known_keys (from InteractionState): {sorted(known_keys)}")
    print(f"Tool output data keys: {list(data.keys())}")
    print(f"Tool output data values:")
    for k, v in data.items():
        print(f"  {k} = '{v}' (len={len(str(v)) if v else 0}, truthy={bool(v)})")

    filled_before = {k: v for k, v in form.items() if v}
    print(f"\nForm filled BEFORE merge: {filled_before}")
    print(f"Form has keys: {list(form.keys())}")

    result = dict(form)
    for key, val in data.items():
        is_known = key in known_keys
        if not is_known:
            print(f"SKIPPED key='{key}' (not in known_keys)")
            continue
        if not val:
            print(f"SKIPPED key='{key}' (falsy value)")
            continue

        old_val = result.get(key, "")
        if isinstance(val, list):
            new_val = ", ".join(str(v).strip() for v in val if v)
        else:
            new_val = str(val).strip()
        result[key] = new_val
        print(f"UPDATED: '{old_val}' -> '{new_val}'")

    filled_after = {k: v for k, v in result.items() if v}
    print(f"\nForm filled AFTER merge: {filled_after}")
    print(f"Fields that changed:")
    for k in known_keys:
        if form.get(k) != result.get(k):
            print(f"  {k}: '{form.get(k)}' -> '{result.get(k)}'")
    print(f"=================================")
    print("=" * 70 + "\n")
    return result
