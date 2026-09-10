import re
import logging
from fastapi import APIRouter, HTTPException, Query
from db.connection import get_connection
from models.schemas import SubmitRequest, AttemptOut, EvaluationOut, RubricScoreOut
from evaluators.deterministic import DeterministicEvaluator
from evaluators.llm import LLMEvaluator
from evaluators.relevance import check_relevance, NOT_RELATED_MESSAGE

router = APIRouter()
logger = logging.getLogger("attempts")


def _coerce_score(value) -> int:
    """Coerce anything into an integer 0-10 (defense-in-depth)."""
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


def _clip(s: str, n: int) -> str:
    """Cap input length passed to the LLM to bound token cost."""
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + "…"


def _save_scores(cursor, evaluation_id, criteria):
    """Save rubric scores with explicit type coercion."""
    for c in criteria:
        cursor.execute(
            """INSERT INTO rubric_scores
               (evaluation_id, criterion, score, evidence, concern, suggestion)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                evaluation_id,
                _coerce_text(c.get("criterion", "Unknown")),
                _coerce_score(c.get("score")),
                _coerce_text(c.get("evidence")),
                _coerce_text(c.get("concern")),
                _coerce_text(c.get("suggestion")),
            ),
        )


def _row_to_rubric_score(row: dict) -> RubricScoreOut:
    """Build a RubricScoreOut from a DB row with explicit coercion."""
    return RubricScoreOut(
        criterion=_coerce_text(row.get("criterion")),
        score=_coerce_score(row.get("score")),
        evidence=_coerce_text(row.get("evidence")),
        concern=_coerce_text(row.get("concern")),
        suggestion=_coerce_text(row.get("suggestion")),
    )


@router.post("/attempts")
def start_attempt(problem_id: int = Query(...), learner_id: str = Query(...)):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    # 1. Check if an InProgress attempt already exists for this problem/learner
    cur.execute(
        """SELECT id FROM attempts 
           WHERE problem_id = %s AND learner_id = %s AND status = 'InProgress' 
           ORDER BY id DESC LIMIT 1""",
        (problem_id, learner_id),
    )
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return {"id": existing["id"], "status": "InProgress"}

    cur.execute(
        "INSERT INTO attempts (problem_id, learner_id, status) VALUES (%s, %s, 'InProgress')",
        (problem_id, learner_id),
    )
    conn.commit()
    attempt_id = cur.lastrowid
    cur.close()
    conn.close()
    return {"id": attempt_id, "status": "InProgress"}


@router.get("/attempts", response_model=list[AttemptOut])
def list_attempts(learner_id: str = Query(...)):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""SELECT a.*, p.title as problem_title, p.description as problem_description
       FROM attempts a
       JOIN problems p ON a.problem_id = p.id
       WHERE a.learner_id = %s
         AND a.status != 'InProgress'
       ORDER BY a.id DESC""",
    (learner_id,),)

    attempts = cur.fetchall()
    result = []

    for att in attempts:
        cur.execute(
            "SELECT * FROM submissions WHERE attempt_id = %s ORDER BY id DESC LIMIT 1",
            (att["id"],),
        )
        sub = cur.fetchone()
        ev_out = None
        if sub:
            cur.execute(
                "SELECT * FROM evaluations WHERE submission_id = %s ORDER BY id DESC LIMIT 1",
                (sub["id"],),
            )
            ev = cur.fetchone()
            if ev:
                cur.execute(
                    "SELECT criterion, score, evidence, concern, suggestion "
                    "FROM rubric_scores WHERE evaluation_id = %s",
                    (ev["id"],),
                )
                scores = cur.fetchall()
                ev_out = EvaluationOut(
                    id=int(ev["id"]),
                    status=str(ev["status"]),
                    overall_summary=ev["overall_summary"],
                    scores=[_row_to_rubric_score(s) for s in scores],
                )

        result.append(
            AttemptOut(
                id=int(att["id"]),
                problem_id=int(att["problem_id"]),
                problem_title=att.get("problem_title"),
                problem_description=att.get("problem_description"),
                status=str(att["status"]),
                started_at=att["started_at"],
                submitted_at=att.get("submitted_at"),
                submission_content=sub["content"] if sub else None,
                evaluation=ev_out,
            )
        )

    cur.close()
    conn.close()
    return result


@router.get("/attempts/{attempt_id}", response_model=AttemptOut)
def get_attempt(attempt_id: int):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM attempts WHERE id = %s", (attempt_id,))
    att = cur.fetchone()
    if not att:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Also fetch problem title/description for the single-attempt view
    cur.execute(
        "SELECT title, description FROM problems WHERE id = %s",
        (att["problem_id"],),
    )
    problem_row = cur.fetchone() or {}

    cur.execute(
        "SELECT * FROM submissions WHERE attempt_id = %s ORDER BY id DESC LIMIT 1",
        (attempt_id,),
    )
    sub = cur.fetchone()
    ev_out = None
    if sub:
        cur.execute(
            "SELECT * FROM evaluations WHERE submission_id = %s ORDER BY id DESC LIMIT 1",
            (sub["id"],),
        )
        ev = cur.fetchone()
        if ev:
            cur.execute(
                "SELECT criterion, score, evidence, concern, suggestion "
                "FROM rubric_scores WHERE evaluation_id = %s",
                (ev["id"],),
            )
            scores = cur.fetchall()
            ev_out = EvaluationOut(
                id=int(ev["id"]),
                status=str(ev["status"]),
                overall_summary=ev["overall_summary"],
                scores=[_row_to_rubric_score(s) for s in scores],
            )

    cur.close()
    conn.close()
    return AttemptOut(
        id=int(att["id"]),
        problem_id=int(att["problem_id"]),
        problem_title=problem_row.get("title"),
        problem_description=problem_row.get("description"),
        status=str(att["status"]),
        started_at=att["started_at"],
        submitted_at=att.get("submitted_at"),
        submission_content=sub["content"] if sub else None,
        evaluation=ev_out,
    )


@router.post("/attempts/{attempt_id}/submit")
def submit_attempt(attempt_id: int, body: SubmitRequest):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT status, problem_id FROM attempts WHERE id = %s", (attempt_id,))
    att = cur.fetchone()
    if not att:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Attempt not found")
    if att["status"] in ("Submitted", "Evaluating", "Completed"):
        cur.close()
        conn.close()
        raise HTTPException(status_code=409, detail="This attempt has already been submitted")

    # Save the submission
    cur.execute(
        "INSERT INTO submissions (attempt_id, format, content) VALUES (%s, %s, %s)",
        (attempt_id, body.format, body.content),
    )
    conn.commit()
    submission_id = cur.lastrowid

    cur.execute(
        "UPDATE attempts SET status='Submitted', submitted_at=NOW() WHERE id=%s",
        (attempt_id,),
    )
    cur.execute(
        "INSERT INTO evaluations (submission_id, status) VALUES (%s, 'Pending')",
        (submission_id,),
    )
    conn.commit()
    evaluation_id = cur.lastrowid

    cur.execute(
        "SELECT title, description FROM problems WHERE id = %s",
        (att["problem_id"],),
    )
    row = cur.fetchone()
    problem_title = row["title"]
    problem_desc = row["description"]

    # ------------------------------------------------------------------
    # RELEVANCE GATE
    # ------------------------------------------------------------------
    related, reason = check_relevance(
        f"{problem_title}\n{problem_desc}", body.content
    )

    if not related:
        _save_scores(
            cur,
            evaluation_id,
            [
                {
                    "criterion": "Relevance",
                    "score": 0,
                    "evidence": "",
                    "concern": reason,
                    "suggestion": "Read the problem carefully and answer the question asked.",
                }
            ],
        )
        cur.execute(
            "UPDATE evaluations SET status='Completed', overall_summary=%s, "
            "completed_at=NOW() WHERE id=%s",
            (reason, evaluation_id),
        )
        cur.execute("UPDATE attempts SET status='Completed' WHERE id=%s", (attempt_id,))
        conn.commit()
        cur.close()
        conn.close()
        return get_attempt(attempt_id)
    # ------------------------------------------------------------------

    # 1. Deterministic checks
    det_result = DeterministicEvaluator().evaluate(problem_desc, body.content)
    _save_scores(cur, evaluation_id, det_result["criteria"])
    conn.commit()

    # 2. LLM grading
    try:
        cur.execute(
            "UPDATE evaluations SET status='Evaluating' WHERE id=%s",
            (evaluation_id,),
        )
        conn.commit()
        llm_result = LLMEvaluator().evaluate(
            _clip(problem_desc, 1500),
            _clip(body.content, 3000),
        )
        _save_scores(cur, evaluation_id, llm_result["criteria"])
        cur.execute(
            "UPDATE evaluations SET status='Completed', overall_summary=%s, "
            "completed_at=NOW() WHERE id=%s",
            (llm_result["overall_summary"], evaluation_id),
        )
        cur.execute("UPDATE attempts SET status='Completed' WHERE id=%s", (attempt_id,))
    except Exception as e:
        logger.warning(f"LLM evaluation failed for evaluation {evaluation_id}: {e}")
        cur.execute(
            "UPDATE evaluations SET status='Failed', overall_summary=%s WHERE id=%s",
            (
                "AI evaluation unavailable – showing automated structural checks only.",
                evaluation_id,
            ),
        )
        cur.execute("UPDATE attempts SET status='Completed' WHERE id=%s", (attempt_id,))

    conn.commit()
    cur.close()
    conn.close()

    return get_attempt(attempt_id)