"""Tests for validation and error handling."""

import json

import pytest

from simple_api.utils import errors, validators
from simple_api.flask import create_app


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestUUIDValidation:
    """Test UUID validation."""

    def test_valid_uuid(self):
        """Test that valid UUIDs pass validation."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        result = validators.validate_uuid(valid_uuid)
        assert result == valid_uuid

    def test_invalid_uuid_raises_error(self):
        """Test that invalid UUIDs raise InvalidUUIDError."""
        with pytest.raises(errors.InvalidUUIDError) as exc_info:
            validators.validate_uuid("not-a-uuid")
        assert "Invalid UUID format" in str(exc_info.value)

    def test_empty_string_raises_error(self):
        """Test that empty string raises InvalidUUIDError."""
        with pytest.raises(errors.InvalidUUIDError):
            validators.validate_uuid("")

    def test_random_string_raises_error(self):
        """Test that random strings raise InvalidUUIDError."""
        with pytest.raises(errors.InvalidUUIDError):
            validators.validate_uuid("abc123")


class TestRequestValidation:
    """Test request validation with Pydantic."""

    def test_create_note_with_empty_title(self, client):
        """Test that empty title is rejected."""
        payload = {"title": "", "content": "Test content"}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Validation error"
        assert "details" in data

    def test_create_note_with_whitespace_only_title(self, client):
        """Test that whitespace-only title is rejected."""
        payload = {"title": "   ", "content": "Test content"}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Validation error"

    def test_create_note_with_empty_content(self, client):
        """Test that empty content is rejected."""
        payload = {"title": "Test Title", "content": ""}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Validation error"

    def test_create_note_with_whitespace_only_content(self, client):
        """Test that whitespace-only content is rejected."""
        payload = {"title": "Test Title", "content": "   "}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Validation error"

    def test_create_note_with_title_too_long(self, client):
        """Test that title exceeding max length is rejected."""
        payload = {"title": "a" * 201, "content": "Test content"}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Validation error"

    def test_create_note_with_content_too_long(self, client):
        """Test that content exceeding max length is rejected."""
        payload = {"title": "Test Title", "content": "a" * 10001}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Validation error"

    def test_create_note_trims_whitespace(self, client):
        """Test that leading/trailing whitespace is trimmed."""
        payload = {"title": "  Test Title  ", "content": "  Test content  "}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "Test Title"
        assert data["content"] == "Test content"

    def test_update_note_with_empty_title(self, client):
        """Test that updating with empty title is rejected."""
        # Create a note first
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Original", "content": "Original content"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Try to update with empty title
        response = client.put(
            f"/notes/{note_id}",
            data=json.dumps({"title": ""}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Validation error"

    def test_update_note_with_invalid_uuid(self, client):
        """Test that updating with invalid UUID is rejected."""
        response = client.put(
            "/notes/invalid-uuid",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid UUID format" in data["error"]

    def test_get_note_with_invalid_uuid(self, client):
        """Test that getting with invalid UUID is rejected."""
        response = client.get("/notes/invalid-uuid")

        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid UUID format" in data["error"]

    def test_delete_note_with_invalid_uuid(self, client):
        """Test that deleting with invalid UUID is rejected."""
        response = client.delete("/notes/invalid-uuid")

        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid UUID format" in data["error"]


class TestErrorHandlers:
    """Test global error handlers."""

    def test_404_error_handler(self, client):
        """Test 404 error handler."""
        response = client.get("/nonexistent")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Not found"

    def test_405_method_not_allowed(self, client):
        """Test 405 error handler."""
        response = client.post("/health")

        assert response.status_code == 405
        data = response.get_json()
        assert data["error"] == "Method not allowed"

    def test_empty_request_body(self, client):
        """Test error when request body is empty."""
        response = client.post("/notes", content_type="application/json")

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestMaxContentLength:
    """Test max content length validation."""

    def test_very_large_payload_rejected(self, client):
        """Test that very large payloads are rejected."""
        # Create a payload larger than 1MB (default MAX_CONTENT_LENGTH)
        large_content = "x" * (2 * 1024 * 1024)  # 2MB
        payload = {"title": "Test", "content": large_content}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        # Flask returns 413 for payload too large
        assert response.status_code == 413
