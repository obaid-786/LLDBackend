import pytest

class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_nonexistent_attempt(self, client):
        """Should return 404 for nonexistent attempt"""
        response = client.get("/attempts/99999")
        assert response.status_code == 404

    def test_nonexistent_problem(self, client):
        """Should return 404 for nonexistent problem"""
        response = client.get("/problems/99999")
        assert response.status_code == 404

    def test_submit_to_completed_attempt(self, client, sample_submission):
        """Should reject submission to completed attempt"""
        # Create and submit
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": sample_submission}
        )
        assert response.status_code == 200
        
        # Try to submit again
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": "Another submission with enough length here"}
        )
        assert response.status_code == 409

    def test_empty_submission_rejected(self, client):
        """Should reject empty submissions"""
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": ""}
        )
        assert response.status_code == 422  # min_length validation

    def test_very_large_submission(self, client):
        """Should handle very large submissions (within limits)"""
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        # Create a large submission (near 20000 chars)
        large_content = "A" * 19000
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": large_content}
        )
        assert response.status_code in (200, 422)

    def test_special_characters_in_submission(self, client):
        """Should handle special characters in submission"""
        response = client.post("/attempts?problem_id=1&learner_id=testuser")
        assert response.status_code == 200
        attempt_id = response.json()["id"]
        
        content_with_special = """
        Classes: Car, Bike, Truck 🚗
        Requirements: Handle ½ price rates
        */
        """
        
        response = client.post(
            f"/attempts/{attempt_id}/submit",
            json={"content": content_with_special}
        )
        assert response.status_code in (200, 422)

    def test_get_history_for_new_user(self, client):
        """Should return empty list for user with no attempts"""
        response = client.get("/attempts?learner_id=brandnewuser")
        assert response.status_code == 200
        data = response.json()
        assert data == [] or len(data) == 0