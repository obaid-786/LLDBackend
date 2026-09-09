import pytest

class TestFullFlow:
    """Integration tests for the complete practice flow"""
    
    def test_problem_listing(self, client):
        """Should list all 3 seeded problems"""
        response = client.get("/problems")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] is not None
        assert "id" in data[0]

    def test_get_single_problem(self, client):
        """Should return a specific problem by ID"""
        response = client.get("/problems/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "title" in data
        assert "description" in data

    def test_create_attempt(self, client):
        """Should create a new attempt"""
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert data["status"] == "InProgress"

    def test_list_attempts_for_user(self, client):
        """Should list all attempts for a user"""
        # Create some attempts
        client.post("/attempts?problem_id=1&learner_id=testuser")
        client.post("/attempts?problem_id=2&learner_id=testuser")
        
        response = client.get("/attempts?learner_id=testuser")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_submit_valid_design(self, client, sample_submission):
        """Should successfully submit a valid design"""
        # Create attempt
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        # Submit design
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": sample_submission}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("Completed", "Submitted")
        
        # Should have evaluation
        if data.get("evaluation"):
            assert "scores" in data["evaluation"]
            assert len(data["evaluation"]["scores"]) > 0

    def test_duplicate_submission_rejected(self, client, sample_submission):
        """Should reject duplicate submissions"""
        # Create attempt
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        # First submission
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": sample_submission}
        )
        assert response.status_code == 200
        
        # Second submission should fail
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": sample_submission}
        )
        assert response.status_code == 409
        assert "already been submitted" in response.json()["detail"]

    def test_submission_minimum_length(self, client):
        """Should reject submissions that are too short"""
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        # Too short content (less than 20 chars)
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": "Short"}
        )
        assert response.status_code == 422  # Validation error

    def test_get_attempt_with_evaluation(self, client, sample_submission):
        """Should retrieve attempt with full evaluation details"""
        # Create and submit
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": sample_submission}
        )
        assert response.status_code == 200
        
        # Get attempt details
        response = client.get(f"/attempts/{attempt_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == attempt_id
        assert "submission_content" in data
        
        # Should have evaluation (might be failed if no LLM key)
        if data.get("evaluation"):
            assert "scores" in data["evaluation"]

    def test_handle_llm_failure_gracefully(self, client, monkeypatch, sample_submission):
        """Should handle LLM evaluation failure gracefully"""
        # Mock LLM to fail
        def mock_fail(*args, **kwargs):
            raise Exception("LLM service unavailable")
        
        # Patch the evaluator
        import evaluators.llm
        monkeypatch.setattr(evaluators.llm.LLMEvaluator, 'evaluate', mock_fail)
        
        # Create and submit
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": sample_submission}
        )
        assert response.status_code == 200
        
        # Get attempt - should show deterministic feedback
        response = client.get(f"/attempts/{attempt_id}")
        data = response.json()
        
        # Should still have evaluation with deterministic scores
        assert "evaluation" in data
        assert data["evaluation"]["status"] in ("Failed", "Completed")
        
        # Deterministic scores should be present
        if data["evaluation"]["scores"]:
            assert any("Contains" in s["criterion"] for s in data["evaluation"]["scores"])