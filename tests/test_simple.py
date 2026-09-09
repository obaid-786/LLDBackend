import pytest

def test_database_has_tables(client):
    """Verify that the test database has tables"""
    response = client.get("/problems")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # Should have 3 seeded problems

def test_problem_has_expected_fields(client):
    """Verify problem fields are correct"""
    response = client.get("/problems/1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "title" in data
    assert "description" in data
    assert data["title"] is not None