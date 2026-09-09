RUBRIC_CRITERIA = [
    "Requirement Understanding",
    "Class Responsibilities",
    "Coupling and Cohesion",
    "Encapsulation and Interfaces",
    "Extensibility",
]
PROMPT_TEMPLATE = """You are a senior software engineer evaluating a Low‑Level Design (LLD) submission.
Problem description:
{problem_description}

Candidate submission:
{submission_content}

Score the design against the following fixed rubric criteria. Provide evidence from the submission, a concern (if any), and an actionable suggestion for improvement.

Criteria:
{criteria_list}

Respond with ONLY valid JSON, exactly matching this schema:
{{
  "criteria": [
    {{
      "criterion":"string (one of the listed criteria)",
      "score": integer (0-5),
      "evidence":"short quote or paraphrase from submission",
      "concern":"one sentence or empty string",
      "suggestion": "one sentence or empty string",
      "confidence": float (0-1)
    }}
  ],
  "overall_summary":"2-3 sentence summary of the design quality"
}}
"""

def build_prompt(problem_description: str, submission_content: str) -> str:
    return PROMPT_TEMPLATE.format(
        problem_description=problem_description,
        submission_content=submission_content[:3000],  # cap to prevent token overflow
        criteria_list="\n".join(f"- {c}" for c in RUBRIC_CRITERIA),
    )