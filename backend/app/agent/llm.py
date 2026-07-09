"""
Wraps the Groq-hosted LLMs used by the LangGraph agent.

Primary model: gemma2-9b-it  (fast, cheap -> used for the main conversational agent
                               and for structured extraction/summarization tasks)
Fallback model: llama-3.3-70b-versatile (used only if the primary model errors out,
                               e.g. rate limit, or for more complex reasoning if configured)

If no GROQ_API_KEY is configured (e.g. running this repo without a key), we fall back
to a small deterministic stub so the rest of the system (routes, DB, UI) can still be
exercised end to end in a demo/offline environment.
"""
from langchain_groq import ChatGroq

from app.config import settings


def get_llm(temperature: float = 0.2, use_fallback: bool = False):
    model_name = settings.GROQ_FALLBACK_MODEL if use_fallback else settings.GROQ_MODEL
    return ChatGroq(
        api_key=settings.GROQ_API_KEY or "missing-key",
        model=model_name,
        temperature=temperature,
    )


def llm_configured() -> bool:
    return bool(settings.GROQ_API_KEY)


def safe_invoke(messages, temperature: float = 0.2):
    """
    Invoke the primary Groq model, retrying on the fallback model on failure.
    Returns plain string content. Falls back to a canned response if no API key
    is configured at all, so the demo still runs without a Groq subscription.
    """
    if not llm_configured():
        return _offline_stub(messages)

    try:
        llm = get_llm(temperature=temperature)
        return llm.invoke(messages).content
    except Exception:
        try:
            llm = get_llm(temperature=temperature, use_fallback=True)
            return llm.invoke(messages).content
        except Exception as exc:
            return f"[LLM error, both models failed: {exc}]"


def _offline_stub(messages) -> str:
    """A minimal offline fallback so the app is demoable without a live Groq key."""
    last_user = ""
    for m in reversed(messages):
        role = getattr(m, "type", None) or (m.get("role") if isinstance(m, dict) else None)
        if role in ("human", "user"):
            last_user = getattr(m, "content", None) or m.get("content", "")
            break
    return (
        "[offline-stub reply — set GROQ_API_KEY to enable real gemma2-9b-it responses] "
        f"Received: {last_user[:200]}"
    )
