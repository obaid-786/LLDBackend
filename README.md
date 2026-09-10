# LLD Practice Platform — Backend

FastAPI service that serves LLD problems and evaluates submitted designs
against a fixed rubric using a three-stage pipeline: relevance gate →
deterministic checks → LLM grading.

## Stack

| Component | Version / Choice |
|-----------|------------------|
| Framework | FastAPI 0.104.1 |
| Server | Uvicorn 0.24.0 |
| Database | MySQL (via `mysql-connector-python` 8.2.0) |
| Validation | Pydantic 2.5.0 |
| LLM provider | Groq SDK 0.4.0 |
| Config | python-dotenv 1.0.0 |
| Tests | pytest 7.4.3, pytest-cov, httpx, pytest-env |

## Project layout

```
backend/
├── main.py                     # FastAPI app, CORS, router wiring
├── routes/
│   ├── problems.py             # GET /problems, GET /problems/{id}
│   └── attempts.py             # attempts lifecycle + submit + evaluation
├── db/
│   ├── connection.py           # MySQL connection helper
│   └── seed.sql                # seeds 3 sample problems
├── models/
│   └── schemas.py              # Pydantic request/response models
├── evaluators/
│   ├── base.py                 # Evaluator ABC
│   ├── deterministic.py        # keyword + length checks
│   ├── llm.py                  # Groq rubric grading
│   ├── relevance.py            # two-stage relevance gate
│   └── rubric_prompt.py        # rubric criteria + prompt template
├── tests/                      # pytest suite (needs a live test DB)
├── requirements.txt
└── .env.example
```

## Setup

### 1. Environment

Copy `.env.example` to `.env` and fill in:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=lld_practice

LLM_API_KEY=            # Groq API key — required
LLM_MODEL=openai/gpt-oss-20b
RELEVANCE_MODEL=llama-3.1-8b-instant   # optional; defaults to this
LLM_MAX_TOKENS=700                      # optional
```

`LLM_API_KEY` is required — the app raises at request time if missing.
Get one from https://console.groq.com.

### 2. Database

Create the MySQL database and load the seed data:

```bash
mysql -u root -p -e "CREATE DATABASE lld_practice;"
mysql -u root -p lld_practice < db/seed.sql
```

Expected tables: `problems`, `attempts`, `submissions`, `evaluations`,
`rubric_scores`.

### 3. Install & run

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs (auto-generated): http://localhost:8000/docs

## API reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/` | Health / banner |
| `GET`  | `/problems` | List all problems |
| `GET`  | `/problems/{problem_id}` | Single problem by ID (404 if missing) |
| `POST` | `/attempts?problem_id=&learner_id=` | Start an attempt. **Idempotent** — returns the existing `InProgress` attempt if one exists for that learner + problem |
| `GET`  | `/attempts?learner_id=` | List completed attempts for a learner (with latest submission + evaluation) |
| `GET`  | `/attempts/{attempt_id}` | Full attempt detail incl. submission and evaluation |
| `POST` | `/attempts/{attempt_id}/submit` | Submit a design; runs the evaluation pipeline and returns the completed attempt. **409** if already submitted |

### Attempt status flow

```
InProgress → Submitted → Evaluating → Completed
                                    ↘ Failed   (LLM unavailable; deterministic scores retained)
```

A relevance-gate rejection short-circuits straight to `Completed` with a
single `Relevance` score of 0.

## Evaluation pipeline

A `POST /attempts/{id}/submit` runs three stages in order:

### 1. Relevance gate (`evaluators/relevance.py`)
Cheap two-stage filter **before** spending tokens on grading:
- **Stage 1 — heuristics (0 tokens):** rejects empty/short input, inputs with
  fewer than 3 real words, and low-entropy strings (`"aaaaaa"`, `"asdfgh"`).
- **Stage 2 — tiny LLM call:** asks a small model (`RELEVANCE_MODEL`,
  default `llama-3.1-8b-instant`) to reply with exactly `RELATED` or
  `UNRELATED`. Response is **LRU-cached** (`maxsize=512`) so identical
  submissions don't re-cost tokens.
- **Fails open:** if the gate errors, grading proceeds normally.

If rejected, no grading runs; the evaluation is closed with a single
`Relevance = 0` score and the attempt is marked `Completed`.

### 2. Deterministic checks (`evaluators/deterministic.py`)
Zero-cost structural scoring, always runs:
- keyword presence: `class`, `responsibilit`, `requirement` (10 / 0 each)
- "Sufficient detail": 10 if ≥ 80 words, else scaled `word_count // 8`

These scores are **saved before the LLM call**, so they survive LLM failures.

### 3. LLM rubric grading (`evaluators/llm.py`)
Groq chat completion with a fixed rubric (`evaluators/rubric_prompt.py`):

| Rubric criterion |
|------------------|
| Requirement Understanding |
| Class Responsibilities |
| Coupling and Cohesion |
| Encapsulation and Interfaces |
| Extensibility |

- Model: `LLM_MODEL` (default `openai/gpt-oss-20b`)
- `temperature=0.2`, `top_p=0.9`, `seed=42` for reproducibility
- `response_format={"type": "json_object"}` — structured output only
- Deterministic caps: problem description clipped to 1500 chars,
  submission clipped to 3000 chars (bounds token cost)
- Response is parsed and validated: unknown criteria are dropped,
  scores coerced to ints in `[0, 10]`, missing fields default to empty.

### Failure behaviour
If the LLM call raises, `_save_scores` has already persisted the deterministic
scores, and the evaluation is marked `Failed` with the summary:

> "AI evaluation unavailable – showing automated structural checks only."

The attempt still ends in `Completed` — the learner always sees something.

## Design notes

- **`learner_id` is a plain query param**, not a session. No auth — matches
  the frontend's localStorage-based identity. There is nothing here worth
  protecting, and the tradeoff is documented in `docs/DESIGN.md` Q2.
- **Attempts are idempotent per learner+problem** while `InProgress`, so a
  page refresh doesn't create a duplicate row.
- **Defense-in-depth coercion.** Values from the DB and the LLM are coerced
  to int/str in three independent layers (`routes/attempts.py`,
  `models/schemas.py`, `evaluators/llm.py`) because the LLM occasionally
  returns `"8/10"` or `8.0`.
- **Relevance gate is the cost-control mechanism.** Without it, garbage
  submissions still burn a full grading call.

## Testing

Backend tests use `pytest` + FastAPI's `TestClient` and run against a
**real MySQL test database** (`lld_practice_test`), not mocks.

```bash
cp .env.example .env.test       # point at a throwaway DB name
pytest
```

The session-scoped `test_db` fixture (see `tests/conftest.py`) truncates all
tables and re-seeds from `db/seed.sql` before the suite runs, then patches
`db.connection.get_connection` to hand out the test connection.

Test coverage includes:
- full flow: problem listing → attempt → submit → retrieve evaluation
- idempotent attempts, duplicate submission rejection (409)
- validation: min-length content (422), empty submissions
- LLM failure path (monkeypatched) — deterministic scores must still appear
- edge cases: nonexistent IDs (404), large inputs, special characters
- deterministic evaluator unit tests

> Note: tests exercise the pipeline end-to-end but stub the LLM via
> `monkeypatch` where failure is under test. Live-LLM tests are not part of
> the default suite (they'd be slow, flaky, and costly).