from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProblemOut(BaseModel):
    id: int
    title: str
    description: str
    constraints: Optional[str] = None
    difficulty: Optional[str] = None

class SubmitRequest(BaseModel):
    content: str = Field(..., min_length=20, max_length=20000)
    format: str = Field(default="text")  #text or code for stretch

class RubricScoreOut(BaseModel):
    criterion: str
    score: int
    evidence: str
    concern: Optional[str] = None
    suggestion: Optional[str] = None

class EvaluationOut(BaseModel):
    id: int
    status: str
    overall_summary: Optional[str] = None
    scores: List[RubricScoreOut] = []

class AttemptOut(BaseModel):
    id: int
    problem_id: int
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
    submission_content: Optional[str] = None
    evaluation: Optional[EvaluationOut] = None