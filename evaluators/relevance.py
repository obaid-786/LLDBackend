"""
Two-stage relevance gate (Groq).
Stage 1: free heuristics (no tokens).
Stage 2: tiny LLM call on a small fast model, LRU-cached.
If unrelated, caller must NOT run any grading.
"""
import os
import re
import logging
from functools import lru_cache
from groq import Groq

logger = logging.getLogger("relevance")

NOT_RELATED_MESSAGE = "The answer is not related to this question. No score awarded."

_client = None


def _client_singleton():
    global _client
    if _client is None:
        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            raise ValueError("LLM_API_KEY not set in environment")
        _client = Groq(api_key=api_key)
    return _client


# ---------- Stage 1: free junk filter (0 tokens) ----------
def _looks_like_junk(answer: str) -> bool:
    if not answer or len(answer.strip()) < 10:
        return True
    words = re.findall(r"[A-Za-z]{2,}", answer)
    if len(words) < 3:
        return True
    stripped = answer.lower().replace(" ", "")
    if len(set(stripped)) < 4:            # "aaaaaa", "asdfgh", "...."
        return True
    return False


# ---------- Stage 2: tiny LLM check ----------
_REL_SYSTEM = (
    "You decide if an ANSWER addresses a QUESTION. "
    "Reply with exactly one word: RELATED or UNRELATED. "
    "No punctuation, no explanation."
)


@lru_cache(maxsize=512)
def _ask_llm_cached(question: str, answer: str) -> bool:
    resp = _client_singleton().chat.completions.create(
        model=os.environ.get("RELEVANCE_MODEL", "llama-3.1-8b-instant"),
        temperature=0,
        max_tokens=2,                     # only "RELATED" / "UNRELATED"
        messages=[
            {"role": "system", "content": _REL_SYSTEM},
            {"role": "user", "content":
                f"QUESTION: {question}\nANSWER: {answer[:1500]}"},
        ],
        timeout=15,
    )
    token = (resp.choices[0].message.content or "").strip().upper()
    return token.startswith("RELATED")


def check_relevance(question: str, answer: str):
    """Return (is_related, reason). reason is '' when related."""
    if _looks_like_junk(answer):
        return False, NOT_RELATED_MESSAGE
    try:
        if not _ask_llm_cached(question.strip(), answer.strip()):
            return False, NOT_RELATED_MESSAGE
    except Exception as e:
        # Fail open: if the gate errors, let normal grading run.
        logger.warning(f"relevance check failed, allowing grading: {e}")
    return True, ""