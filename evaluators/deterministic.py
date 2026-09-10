from ast import keyword

from .base import Evaluator

REQUIRED_KEYWORDS = ["class", "responsibilit", "requirement"]

class DeterministicEvaluator(Evaluator):
    def evaluate(self, problem_description :str, submission_content:str)-> dict:
        text_lower = submission_content.lower()
        criteria = []
# checking the presence of keywords
        for keyword in REQUIRED_KEYWORDS:
            present = keyword in text_lower
            criteria.append({
                "criterion": f"Contains '{keyword}' section",
                "score": 10 if present else 0,  # <-- Changed from 5 to 10
                "evidence": "Found in submission" if present else "Not found",
                "concern": "" if present else f"Missing explicit mention of {keyword}.",
                "suggestion": "" if present else f"Add a section describing {keyword}.",
                "confidence": 1.0,})

        word_count = len(submission_content.split())
        length_score = 10 if word_count >= 80 else max(0, word_count // 8) # <-- Scale to 10
        criteria.append({
            "criterion": "Sufficient detail",
            "score": length_score,
            "evidence":f"{word_count} words",
            "concern": "" if word_count >= 80 else "subbmisiion is brief, may lack depth",
            "suggestion": "" if word_count >= 80 else "expand on responsibility and trade-offs",
            "confidence": 1.0
        })
        return {"criteria": criteria,"overall_summary": "Automated structural evalution is done"}