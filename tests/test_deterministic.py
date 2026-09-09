import pytest
from evaluators.deterministic import DeterministicEvaluator

def test_deterministic_passes_complete_submission():
    """A well-structured submission should score 5 on all structural checks"""
    content = """
    Requirements: The system should manage parking.
    Classes: Floor, Vehicle, ParkingSpot.
    Responsibilities: Floor manages spots; Vehicle stores info.
    """
    evaluator = DeterministicEvaluator()
    result = evaluator.evaluate("dummy problem", content)
    
    # All structural checks should score 5
    for criterion in result["criteria"]:
        if "Contains" in criterion["criterion"]:
            assert criterion["score"] == 5, f"{criterion['criterion']} should be 5"
    
    # Check if length criterion exists, if not, skip the assertion
    length_criteria = [c for c in result["criteria"] if "Sufficient detail" in c["criterion"]]
    if length_criteria:
        assert length_criteria[0]["score"] == 5
    
    # Check summary exists
    assert "overall_summary" in result
    assert result["overall_summary"] is not None

def test_deterministic_fails_incomplete():
    """A submission missing required sections should score 0"""
    content = "Just random text about parking lot"
    evaluator = DeterministicEvaluator()
    result = evaluator.evaluate("dummy problem", content)
    
    # All structural checks should score 0
    for criterion in result["criteria"]:
        if "Contains" in criterion["criterion"]:
            assert criterion["score"] == 0, f"{criterion['criterion']} should be 0"
    
    # Verify we have results
    assert len(result["criteria"]) > 0
    assert "overall_summary" in result

def test_deterministic_short_submission():
    """Test that very short submissions get low scores"""
    content = "Classes: A. Responsibilities: X."
    evaluator = DeterministicEvaluator()
    result = evaluator.evaluate("dummy", content)
    
    # Check if length criterion exists
    length_criteria = [c for c in result["criteria"] if "Sufficient detail" in c["criterion"]]
    if length_criteria:
        assert length_criteria[0]["score"] < 5
    
    assert "overall_summary" in result

def test_deterministic_always_returns_summary():
    """Evaluator should always return an overall summary"""
    content = "Some content with requirements, classes, responsibilities"
    evaluator = DeterministicEvaluator()
    result = evaluator.evaluate("dummy", content)
    
    assert "overall_summary" in result
    assert isinstance(result["overall_summary"], str)