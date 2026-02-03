import pytest
import uuid
from http import HTTPStatus

class TestHistoryAPI:
    """Test suite for the history API using the Flask test client."""

    def test_history_valid_session_id(self, client):
        """Test 1: Ensure /history returns correct data for a valid session ID. new sessions return 201 and existing ones return 200."""
        session_id = str(uuid.uuid4())
        # First request with session id (201)
        response = client.get('/history', query_string={'session_id': session_id}, headers={'Origin': 'http://example.com'})
        assert response.status_code == HTTPStatus.CREATED
        data = response.get_json()
        assert "session_id" in data 
        assert "history" in data 
        assert data["session_id"] == session_id
        assert len(data["history"]) >= 1, "A new session should have a welcome message."

        # second request with same session ID
        response2 = client.get('/history', query_string={'session_id': session_id}, headers={'Origin': 'http://example.com'})
        assert response2.status_code == HTTPStatus.OK

    def test_history_invalid_session_id_format(self, client):
        """Test 2: History - Invalid Session ID Format"""
        response = client.get('/history', query_string={'session_id': 'invalid-uuid-format'}, headers={'Origin': 'http://example.com'})

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.get_json()
        assert data["error"] == "Invalid session id format"

    def test_history_response_structure_validation(self, client):
        """Test 3: Validate the structure of a message object in the history"""
        session_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get('/history', query_string={'session_id': session_id})
        data = response.get_json()
        
        if data.get("history") and len(data["history"]) > 0:
            message = data["history"][0]
            assert "content" in message
            assert "type" in message