"""Tests for the API routes."""

import json
from datetime import datetime

import pytest

from simple_api.flask import create_app


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestHealthAndIndexEndpoints:
    """Test health and index endpoints."""

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "simple_api"

    def test_index_endpoint(self, client):
        """Test the index endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()
        assert "service" in data
        assert "version" in data
        assert data["service"] == "simple_api"

    def test_health_endpoint_wrong_method(self, client):
        """Test that health endpoint rejects non-GET methods."""
        response = client.post("/health")
        assert response.status_code == 405

    def test_404_error_handler(self, client):
        """Test the 404 error handler."""
        response = client.get("/nonexistent")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Not found"


class TestNotesRoutes:
    """Test notes CRUD routes."""

    def test_create_note_success(self, client):
        """Test creating a note successfully."""
        payload = {"title": "Test Note", "content": "Test content"}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "Test Note"
        assert data["content"] == "Test content"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_note_missing_title(self, client):
        """Test creating a note without a title."""
        payload = {"content": "Test content"}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Validation error"

    def test_create_note_missing_content(self, client):
        """Test creating a note without content."""
        payload = {"title": "Test Note"}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Validation error"

    def test_create_note_missing_both(self, client):
        """Test creating a note without title and content."""
        payload = {}

        response = client.post(
            "/notes", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        # Empty payload triggers "Request body is required" check
        assert data["error"] == "Request body is required"

    def test_create_note_no_json_body(self, client):
        """Test creating a note with no JSON body."""
        response = client.post("/notes", content_type="application/json")

        assert response.status_code == 400
        data = response.get_json()
        # No body triggers Flask's 400 Bad Request
        assert data["error"] == "Bad request"

    def test_create_note_invalid_json(self, client):
        """Test creating a note with invalid JSON."""
        response = client.post(
            "/notes", data="invalid json", content_type="application/json"
        )

        assert response.status_code == 400

    def test_get_all_notes_empty(self, client):
        """Test getting all notes when there are none."""
        response = client.get("/notes")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_all_notes_with_data(self, client):
        """Test getting all notes when there are some."""
        # Create some notes
        client.post(
            "/notes",
            data=json.dumps({"title": "Note 1", "content": "Content 1"}),
            content_type="application/json",
        )
        client.post(
            "/notes",
            data=json.dumps({"title": "Note 2", "content": "Content 2"}),
            content_type="application/json",
        )

        response = client.get("/notes")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert any(note["title"] == "Note 1" for note in data)
        assert any(note["title"] == "Note 2" for note in data)

    def test_get_note_success(self, client):
        """Test getting a specific note by ID."""
        # Create a note
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Test Note", "content": "Test content"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Get the note
        response = client.get(f"/notes/{note_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == note_id
        assert data["title"] == "Test Note"
        assert data["content"] == "Test content"

    def test_get_note_not_found(self, client):
        """Test getting a note that doesn't exist."""
        # Use a valid UUID that doesn't exist
        import uuid
        nonexistent_id = str(uuid.uuid4())
        response = client.get(f"/notes/{nonexistent_id}")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Note not found"

    def test_update_note_all_fields(self, client):
        """Test updating all fields of a note."""
        # Create a note
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Original Title", "content": "Original content"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Update the note
        update_payload = {
            "title": "Updated Title",
            "content": "Updated content",
            "completed": True,
        }
        response = client.put(
            f"/notes/{note_id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == note_id
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"
        assert data["completed"] is True

    def test_update_note_partial_title(self, client):
        """Test updating only the title of a note."""
        # Create a note
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Original Title", "content": "Original content"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Update only title
        update_payload = {"title": "New Title"}
        response = client.put(
            f"/notes/{note_id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "New Title"
        assert data["content"] == "Original content"  # Unchanged
        assert data["completed"] is False  # Unchanged

    def test_update_note_partial_content(self, client):
        """Test updating only the content of a note."""
        # Create a note
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Original Title", "content": "Original content"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Update only content
        update_payload = {"content": "New content"}
        response = client.put(
            f"/notes/{note_id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Original Title"  # Unchanged
        assert data["content"] == "New content"

    def test_update_note_partial_completed(self, client):
        """Test updating only the completed status of a note."""
        # Create a note
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Original Title", "content": "Original content"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Update only completed status
        update_payload = {"completed": True}
        response = client.put(
            f"/notes/{note_id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["completed"] is True
        assert data["title"] == "Original Title"  # Unchanged
        assert data["content"] == "Original content"  # Unchanged

    def test_update_note_not_found(self, client):
        """Test updating a note that doesn't exist."""
        # Use a valid UUID that doesn't exist
        import uuid
        nonexistent_id = str(uuid.uuid4())
        update_payload = {"title": "Updated Title"}
        response = client.put(
            f"/notes/{nonexistent_id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Note not found"

    def test_update_note_no_data(self, client):
        """Test updating a note with no data."""
        # Create a note
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Test", "content": "Test"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Try to update with no data (empty object)
        response = client.put(
            f"/notes/{note_id}", data=json.dumps({}), content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        # Empty object triggers "Request body is required" check
        assert data["error"] == "Request body is required"

    def test_update_note_null_body(self, client):
        """Test updating a note with null body."""
        # Create a note
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Test", "content": "Test"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Try to update with null body
        response = client.put(f"/notes/{note_id}", content_type="application/json")

        assert response.status_code == 400
        data = response.get_json()
        # No body triggers Flask's Bad Request
        assert data["error"] == "Bad request"

    def test_delete_note_success(self, client):
        """Test deleting a note successfully."""
        # Create a note
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Test Note", "content": "Test content"}),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Delete the note
        response = client.delete(f"/notes/{note_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Note deleted successfully"

        # Verify it's deleted
        get_response = client.get(f"/notes/{note_id}")
        assert get_response.status_code == 404

    def test_delete_note_not_found(self, client):
        """Test deleting a note that doesn't exist."""
        # Use a valid UUID that doesn't exist
        import uuid
        nonexistent_id = str(uuid.uuid4())
        response = client.delete(f"/notes/{nonexistent_id}")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Note not found"

    def test_full_crud_flow(self, client):
        """Test a complete CRUD flow through the API."""
        # Create
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "CRUD Test", "content": "Testing CRUD"}),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        note_id = create_response.get_json()["id"]

        # Read
        read_response = client.get(f"/notes/{note_id}")
        assert read_response.status_code == 200
        assert read_response.get_json()["title"] == "CRUD Test"

        # Update
        update_response = client.put(
            f"/notes/{note_id}",
            data=json.dumps({"title": "Updated CRUD Test", "completed": True}),
            content_type="application/json",
        )
        assert update_response.status_code == 200
        assert update_response.get_json()["title"] == "Updated CRUD Test"
        assert update_response.get_json()["completed"] is True

        # Delete
        delete_response = client.delete(f"/notes/{note_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        final_response = client.get(f"/notes/{note_id}")
        assert final_response.status_code == 404

    def test_create_multiple_notes_have_unique_ids(self, client):
        """Test that multiple created notes have unique IDs."""
        response1 = client.post(
            "/notes",
            data=json.dumps({"title": "Note 1", "content": "Content 1"}),
            content_type="application/json",
        )
        response2 = client.post(
            "/notes",
            data=json.dumps({"title": "Note 2", "content": "Content 2"}),
            content_type="application/json",
        )

        id1 = response1.get_json()["id"]
        id2 = response2.get_json()["id"]

        assert id1 != id2

    def test_timestamps_are_valid_iso_format(self, client):
        """Test that timestamps are in valid ISO format."""
        response = client.post(
            "/notes",
            data=json.dumps({"title": "Test", "content": "Test"}),
            content_type="application/json",
        )

        data = response.get_json()
        created_at = data["created_at"]
        updated_at = data["updated_at"]

        # Should be parseable as ISO format
        datetime.fromisoformat(created_at)
        datetime.fromisoformat(updated_at)

    def test_update_changes_updated_at_timestamp(self, client):
        """Test that updating a note changes the updated_at timestamp."""
        # Create
        create_response = client.post(
            "/notes",
            data=json.dumps({"title": "Test", "content": "Test"}),
            content_type="application/json",
        )
        original_updated_at = create_response.get_json()["updated_at"]
        note_id = create_response.get_json()["id"]

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.1)

        # Update
        update_response = client.put(
            f"/notes/{note_id}",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        new_updated_at = update_response.get_json()["updated_at"]

        assert new_updated_at != original_updated_at
        assert (
            datetime.fromisoformat(new_updated_at)
            > datetime.fromisoformat(original_updated_at)
        )
