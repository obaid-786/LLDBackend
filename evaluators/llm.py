import os
import re
import json
import logging
from .base import Evaluator
from .rubric_prompt import build_prompt, RUBRIC_CRITERIA
from groq import Groq

logger = logging.getLogger(__name__)

_client = None


def _client_singleton():
    global _client
    if _client is None:
        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            raise ValueError("LLM_API_KEY not set in environment")
        _client = Groq(api_key=api_key)
    return _client


def _coerce_score(value) -> int:
    """Coerce whatever the LLM returns into a 0-10 int."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(0, min(10, int(value)))
    if isinstance(value, str):
        m = re.search(r'\d+', value)
        if m:
            return max(0, min(10, int(m.group())))
    return 0


def _coerce_text(value) -> str:
    return "" if value is None else str(value)


class LLMEvaluator(Evaluator):
    def __init__(self):
        self.client = _client_singleton()
        self.model = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
        self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "700"))

    def evaluate(self, problem_description: str, submission_content: str) -> dict:
        prompt = build_prompt(problem_description, submission_content)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                top_p=0.9,
                max_tokens=self.max_tokens,
                seed=42,
                response_format={"type": "json_object"},
                timeout=60,
            )

            usage = getattr(response, "usage", None)
            if usage is not None:
                logger.info(
                    f"LLM usage model={self.model} "
                    f"prompt={getattr(usage, 'prompt_tokens', '?')} "
                    f"completion={getattr(usage, 'completion_tokens', '?')} "
                    f"total={getattr(usage, 'total_tokens', '?')}"
                )

            raw = response.choices[0].message.content
            logger.info(f"Raw LLM response snippet: {raw[:300]}")
            return self._parse_and_validate(raw)
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            raise

    def _parse_and_validate(self, raw: str) -> dict:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM response is not valid JSON: {e}")

        valid_criteria = set(RUBRIC_CRITERIA)
        cleaned = []

        for item in data.get("criteria", []):
            criterion = item.get("criterion")
            if criterion not in valid_criteria:
                logger.warning(f"Skipping unknown criterion: {criterion}")
                continue

            cleaned.append({
                "criterion": criterion,
                "score": _coerce_score(item.get("score")),
                "evidence": _coerce_text(item.get("evidence")),
                "concern": _coerce_text(item.get("concern")),
                "suggestion": _coerce_text(item.get("suggestion")),
            })

        if not cleaned:
            raise ValueError("LLM returned no valid criteria")

        return {
            "criteria": cleaned,
            "overall_summary": _coerce_text(
                data.get("overall_summary") or "Evaluation complete."
            ),
        }