import os
import json
import logging
from .base import Evaluator
from .rubric_prompt import build_prompt, RUBRIC_CRITERIA

class LLMEvaluator(Evaluator):
    def __init__(self):
        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            raise ValueError("LLM_API_KEY not in environment")
        self.client = 