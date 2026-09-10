from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


def _to_int(v) -> int:
    """Coerce anything into an int. '34', 34.0, '34/5' → 34."""
    if v is None:
        return 0
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        m = re.search(r'\d+', v)
        if m:
            return int(m.group())
    return 0


def _to_score_int(v) -> int:
    """Coerce anything into an integer between 0 and 10."""
    return max(0, min(10, _to_int(v)))


def _to_text(v) -> str:
    return "" if v is None else str(v)


class ProblemOut(BaseModel):
    id: int
    title: str
    description: str
    constraints: Optional[str] = None
    difficulty: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v):
        return _to_int(v)


class SubmitRequest(BaseModel):
    content: str = Field(..., min_length=20, max_length=20000)
    format: str = Field(default="text")


class RubricScoreOut(BaseModel):
    criterion: str
    score: int
    evidence: str = ""
    concern: Optional[str] = None
    suggestion: Optional[str] = None

    @field_validator("score", mode="before")
    @classmethod
    def coerce_score(cls, v):
        return _to_score_int(v)

    @field_validator("evidence", "concern", "suggestion", mode="before")
    @classmethod
    def coerce_text(cls, v):
        return _to_text(v)


class EvaluationOut(BaseModel):
    id: int
    status: str
    overall_summary: Optional[str] = None
    scores: List[RubricScoreOut] = []

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v):
        return _to_int(v)


class AttemptOut(BaseModel):
    id: int
    problem_id: int
    problem_title: Optional[str] = None
    problem_description: Optional[str] = None
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
    submission_content: Optional[str] = None
    evaluation: Optional[EvaluationOut] = None

    @field_validator("id", "problem_id", mode="before")
    @classmethod
    def coerce_ints(cls, v):
        return _to_int(v)