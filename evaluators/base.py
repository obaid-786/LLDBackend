from abc import abstractmethod,ABC


class Evaluator(ABC):
    # Base class for all evaluators.
    @abstractmethod
    def evaluate(self, problem_description: str, submission_content: str) -> dict:
        """
        Evaluate the submission against the problem description.
        Args:
            problem_description (str): The description of the problem.
            submission (str): The submission to be evaluated.
        return a dict with keys:
          - 'criteria': list of dicts with keys: criterion, score, evidence, concern, suggestion, confidence
          - 'overall_summary': str
        """
        raise NotImplementedError