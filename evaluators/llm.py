import os
import json
import logging
from .base import Evaluator
from .rubric_prompt import build_prompt, RUBRIC_CRITERIA
from groq import Groq

logger = logging.getLogger(__name__)

class LLMEvaluator(Evaluator):
    def __init__(self):
        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            raise ValueError("LLM_API_KEY not set in environment")
        self.client = Groq(api_key=api_key)
        self.model = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

    def evaluate(self, problem_description: str, submission_content: str) -> dict:
        prompt = build_prompt(problem_description, submission_content)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=60,
            )
            raw = response.choices[0].message.content
            return self._parse_and_validate(raw)
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            raise

    def _parse_and_validate(self, raw: str) -> dict:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("LLM response is not valid JSON")

        valid_criteria = set(RUBRIC_CRITERIA)
        for item in data.get("criteria", []):
            if item.get("criterion") not in valid_criteria:
                raise ValueError(f"Unknown criterion: {item.get('criterion')}")
            if not (0 <= int(item.get("score", -1)) <= 10):
                raise ValueError("Score out of range (must be 0-10)")
        return data