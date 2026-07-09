# Architecture — AI-First CRM: HCP Module (Log Interaction Screen)

## 1. Screen concept

The **Log Interaction** screen lets a pharmaceutical field rep record a visit/call
with a Healthcare Professional (HCP) in one of two equivalent ways:

- **Structured form** — explicit fields (interaction type, channel, notes, products,
  sentiment, samples, next steps). Good for reps who want full control.
- **Conversational chat** — the rep just describes what happened in plain English
  ("I met Dr. Mehta today, discussed CardioFlow's dosing update, she was positive
  and wants updated trial data by Friday"). The LangGraph agent turns that into the
  same structured record automatically, and can also edit past records, look up
  history, schedule follow-ups, and screen for safety/compliance issues — entirely
  through conversation.

Both entry points call the **same backend tools**, so a record logged via chat looks
identical in the database/UI to one logged via the form — the chat is simply a more
convenient interface to the same underlying operations.

## 2. Role of the LangGraph agent

The LangGraph agent is the orchestration layer sitting between the rep's natural
language and the CRM's structured data model. Concretely, it:

1. **Interprets intent** from free-form rep messages (log a visit, edit a record,
   ask for HCP history, set a reminder) using the Groq-hosted `gemma2-9b-it` LLM.
2. **Chooses and sequences tools** — a single message like "I met Dr. Rao, discussed
   GlucoBalance, she mentioned a patient had nausea, and asked for a follow-up next
   week" triggers *three* tool calls in one turn: `log_interaction`,
   `detect_adverse_event`, and `schedule_followup`.
3. **Executes tools against the database** via SQLAlchemy, inside a request-scoped
   session.
4. **Grounds itself in CRM history** through `get_hcp_context` before answering
   questions that need prior context.
5. **Loops** between the LLM ("agent" node) and tool execution ("tools" node) until
   the model has everything it needs, then produces a short natural-language
   confirmation back to the rep.
6. **Preserves conversation state** per HCP/session so multi-turn corrections work
   ("actually, change that sentiment to Positive").

This is implemented as a small `StateGraph` (see `backend/app/agent/graph.py`):

```
        START ──▶ agent ──▶ (tool_calls present?) ──▶ tools ──▶ agent ──▶ ... ──▶ END
                                     │
                                     └── no tool calls ──▶ END
```

- **`agent` node**: calls `ChatGroq` (model `gemma2-9b-it`, with
  `llama-3.3-70b-versatile` as a documented fallback) bound to the 5 tools below.
- **`tools` node**: LangGraph's prebuilt `ToolNode`, which executes whichever
  tool calls the LLM requested and feeds the results back as `ToolMessage`s.
- **`tools_condition`**: LangGraph's prebuilt router that sends control back to
  `tools` whenever the last AI message contains tool calls, and to `END` otherwise.

## 3. The five tools

All five tools live in `backend/app/agent/tools.py` as LangChain `@tool`-decorated
functions, built per-request via `build_tools(db)` so each one closes over a live
SQLAlchemy session. They are used identically by the chat agent *and* by the plain
REST endpoints backing the structured form — one implementation, two entry points.

### 3.1 `log_interaction` *(required)*
Captures a new interaction. Takes the HCP id, free-text notes, interaction type and
channel. Internally it:
1. Sends the raw text to the Groq LLM with a strict JSON-extraction prompt asking for
   a summary, products discussed, HCP sentiment, samples dropped, and next steps.
2. Parses that JSON (tolerantly — strips markdown fences, falls back gracefully if
   parsing fails) and writes a new `Interaction` row.
3. Returns the created record's id and extracted fields so the agent can reference
   it in the same turn (e.g. to run `detect_adverse_event` against it).

### 3.2 `edit_interaction` *(required)*
Modifies a single field of an already-logged interaction (`sentiment`,
`products_discussed`, `next_steps`, `summary`, etc.), and writes an
`InteractionEdit` audit row recording the field, old value, new value, and the
stated reason for the change. This is the same function the structured-form's
"Edit" button calls (`PATCH /api/interactions/{id}`), so form-based and chat-based
edits are indistinguishable in the audit trail.

### 3.3 `get_hcp_context`
Looks up an HCP's profile (specialty, institution, segment) plus their 5 most
recent interactions, so the agent can answer "what did we last discuss with
Dr. Nair?" or ground a new interaction in prior context, without the rep having to
repeat information the CRM already has.

### 3.4 `schedule_followup`
Creates a follow-up task tied to an HCP (and optionally a specific interaction),
parsing natural-language or ISO due dates ("next Friday", "2026-08-01"). Surfaced
in the sidebar's **Follow-ups** panel.

### 3.5 `detect_adverse_event`
A life-sciences-specific safety net: screens the raw interaction text for adverse
event mentions, off-label usage questions, or product complaints — all things a
real pharma company is legally required to route to pharmacovigilance/compliance.
Any signal found creates a `SafetyFlag` row (with severity and an
`requires_pv_escalation` marker for genuine adverse events) surfaced prominently in
the UI. The agent is instructed to run this automatically after every
`log_interaction` call, and the structured-form path runs it too.

## 4. Data model

- `HCP` — master record (name, specialty, institution, segment).
- `Interaction` — one logged touchpoint; holds both the raw free text and the
  LLM-extracted structured fields.
- `InteractionEdit` — append-only audit trail for `edit_interaction`.
- `FollowUp` — tasks created by `schedule_followup`.
- `SafetyFlag` — compliance/adverse-event flags created by `detect_adverse_event`.
- `ChatSession` — persists the running message history per chat session so
  multi-turn conversations (and corrections) work across requests.

## 5. Tech stack mapping

| Requirement            | Implementation |
|-------------------------|-----------------|
| React + Redux            | `frontend/` — Redux Toolkit slices for HCPs, interactions, chat |
| FastAPI                  | `backend/app/main.py` + routers |
| LangGraph                | `backend/app/agent/graph.py` |
| Groq `gemma2-9b-it`       | `backend/app/agent/llm.py`, with `llama-3.3-70b-versatile` as fallback |
| Postgres/MySQL            | SQLAlchemy models, `DATABASE_URL` driven (SQLite for zero-setup local demo, see `docker-compose.yml` for Postgres) |
| Google Inter font         | `frontend/index.html` + `index.css` |
