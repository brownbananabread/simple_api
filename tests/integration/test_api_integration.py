"""Integration tests for the complete API."""

import json
import time
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


class TestCompleteAPIWorkflow:
    """Test complete workflows through the API."""

    def test_full_note_lifecycle(self, client):
        """Test complete note lifecycle: create -> read -> update -> delete."""
        # Create a note
        create_payload = {"title": "Integration Test Note", "content": "Original content"}
        create_response = client.post(
            "/api/v1/notes",
            data=json.dumps(create_payload),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        note = create_response.get_json()
        note_id = note["id"]

        # Verify note was created with correct data
        assert note["title"] == "Integration Test Note"
        assert note["content"] == "Original content"
        assert note["completed"] is False
        assert "created_at" in note
        assert "updated_at" in note

        # Read the note back
        get_response = client.get(f"/api/v1/notes/{note_id}")
        assert get_response.status_code == 200
        retrieved_note = get_response.get_json()
        assert retrieved_note["id"] == note_id
        assert retrieved_note["title"] == note["title"]

        # Update the note
        update_payload = {
            "title": "Updated Title",
            "content": "Updated content",
            "completed": True,
        }
        update_response = client.put(
            f"/api/v1/notes/{note_id}",
            data=json.dumps(update_payload),
            content_type="application/json",
        )
        assert update_response.status_code == 200
        updated_note = update_response.get_json()
        assert updated_note["title"] == "Updated Title"
        assert updated_note["content"] == "Updated content"
        assert updated_note["completed"] is True

        # Verify update persisted
        get_after_update = client.get(f"/api/v1/notes/{note_id}")
        assert get_after_update.status_code == 200
        assert get_after_update.get_json()["completed"] is True

        # Delete the note
        delete_response = client.delete(f"/api/v1/notes/{note_id}")
        assert delete_response.status_code == 200

        # Verify note is deleted
        get_after_delete = client.get(f"/api/v1/notes/{note_id}")
        assert get_after_delete.status_code == 404

    def test_multiple_notes_management(self, client):
        """Test managing multiple notes simultaneously."""
        # Create multiple notes
        notes = []
        for i in range(5):
            payload = {"title": f"Note {i}", "content": f"Content {i}"}
            response = client.post(
                "/api/v1/notes",
                data=json.dumps(payload),
                content_type="application/json",
            )
            assert response.status_code == 201
            notes.append(response.get_json())

        # Verify all notes in list
        list_response = client.get("/api/v1/notes")
        assert list_response.status_code == 200
        all_notes = list_response.get_json()
        assert len(all_notes) >= 5

        # Update each note
        for note in notes:
            update_payload = {"completed": True}
            update_response = client.put(
                f"/api/v1/notes/{note['id']}",
                data=json.dumps(update_payload),
                content_type="application/json",
            )
            assert update_response.status_code == 200

        # Verify all are completed
        for note in notes:
            get_response = client.get(f"/api/v1/notes/{note['id']}")
            assert get_response.get_json()["completed"] is True

        # Delete all notes
        for note in notes:
            delete_response = client.delete(f"/api/v1/notes/{note['id']}")
            assert delete_response.status_code == 200

    def test_note_search_and_filter_operations(self, client):
        """Test retrieving specific notes from a collection."""
        # Create notes with different properties
        note1 = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Urgent Task", "content": "High priority"}),
            content_type="application/json",
        ).get_json()

        note2 = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Regular Task", "content": "Normal priority"}),
            content_type="application/json",
        ).get_json()

        # Mark one as completed
        client.put(
            f"/api/v1/notes/{note1['id']}",
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )

        # Get all notes and verify state
        all_notes = client.get("/api/v1/notes").get_json()

        # Find our notes in the list
        found_note1 = next(n for n in all_notes if n["id"] == note1["id"])
        found_note2 = next(n for n in all_notes if n["id"] == note2["id"])

        assert found_note1["completed"] is True
        assert found_note2["completed"] is False

        # Cleanup
        client.delete(f"/api/v1/notes/{note1['id']}")
        client.delete(f"/api/v1/notes/{note2['id']}")

    def test_concurrent_updates(self, client):
        """Test handling concurrent updates to the same note."""
        # Create a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Concurrent Test", "content": "Original"}),
            content_type="application/json",
        ).get_json()
        note_id = note["id"]

        # Perform multiple updates in sequence (simulating concurrent access)
        update1 = client.put(
            f"/api/v1/notes/{note_id}",
            data=json.dumps({"content": "Update 1"}),
            content_type="application/json",
        )
        assert update1.status_code == 200

        update2 = client.put(
            f"/api/v1/notes/{note_id}",
            data=json.dumps({"content": "Update 2"}),
            content_type="application/json",
        )
        assert update2.status_code == 200

        # Final state should reflect the last update
        final_note = client.get(f"/api/v1/notes/{note_id}").get_json()
        assert final_note["content"] == "Update 2"

        # Cleanup
        client.delete(f"/api/v1/notes/{note_id}")

    def test_timestamp_consistency(self, client):
        """Test that timestamps are consistent and properly updated."""
        # Create a note
        create_response = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Timestamp Test", "content": "Content"}),
            content_type="application/json",
        )
        note = create_response.get_json()
        note_id = note["id"]
        original_created_at = note["created_at"]
        original_updated_at = note["updated_at"]

        # Verify created_at and updated_at are initially equal
        assert original_created_at == original_updated_at

        # Wait a bit to ensure timestamp difference
        time.sleep(0.1)

        # Update the note
        update_response = client.put(
            f"/api/v1/notes/{note_id}",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        updated_note = update_response.get_json()

        # Verify created_at didn't change but updated_at did
        assert updated_note["created_at"] == original_created_at
        assert updated_note["updated_at"] != original_updated_at
        assert datetime.fromisoformat(
            updated_note["updated_at"]
        ) > datetime.fromisoformat(original_updated_at)

        # Cleanup
        client.delete(f"/api/v1/notes/{note_id}")

    def test_error_recovery_flow(self, client):
        """Test that the API recovers gracefully from errors."""
        # Try to get a non-existent note
        import uuid

        fake_id = str(uuid.uuid4())
        error_response = client.get(f"/api/v1/notes/{fake_id}")
        assert error_response.status_code == 404

        # Verify we can still create notes after an error
        create_response = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "After Error", "content": "Content"}),
            content_type="application/json",
        )
        assert create_response.status_code == 201
        note_id = create_response.get_json()["id"]

        # Cleanup
        client.delete(f"/api/v1/notes/{note_id}")

    def test_bulk_operations(self, client):
        """Test bulk operations on notes."""
        # Create multiple notes
        note_ids = []
        for i in range(10):
            response = client.post(
                "/api/v1/notes",
                data=json.dumps({"title": f"Bulk {i}", "content": f"Content {i}"}),
                content_type="application/json",
            )
            note_ids.append(response.get_json()["id"])

        # Verify all were created
        all_notes = client.get("/api/v1/notes").get_json()
        assert len([n for n in all_notes if n["id"] in note_ids]) == 10

        # Bulk update all to completed
        for note_id in note_ids:
            client.put(
                f"/api/v1/notes/{note_id}",
                data=json.dumps({"completed": True}),
                content_type="application/json",
            )

        # Verify all are completed
        all_notes = client.get("/api/v1/notes").get_json()
        for note_id in note_ids:
            note = next(n for n in all_notes if n["id"] == note_id)
            assert note["completed"] is True

        # Bulk delete
        for note_id in note_ids:
            delete_response = client.delete(f"/api/v1/notes/{note_id}")
            assert delete_response.status_code == 200

        # Verify all are deleted
        all_notes_after = client.get("/api/v1/notes").get_json()
        assert len([n for n in all_notes_after if n["id"] in note_ids]) == 0


class TestAPIHealthAndStatus:
    """Test API health and status endpoints integration."""

    def test_health_check_during_operations(self, client):
        """Test that health check works during normal operations."""
        # Create a note
        client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Test", "content": "Content"}),
            content_type="application/json",
        )

        # Check health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.get_json()["status"] == "healthy"

    def test_index_endpoint_provides_correct_info(self, client):
        """Test that index endpoint provides correct API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.get_json()
        assert "service" in data
        assert "version" in data
        assert data["service"] == "simple_api"


class TestDataPersistence:
    """Test data persistence across operations."""

    def test_data_survives_multiple_requests(self, client):
        """Test that data persists across multiple requests."""
        # Create a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Persistence Test", "content": "Original"}),
            content_type="application/json",
        ).get_json()
        note_id = note["id"]

        # Make multiple read requests
        for _ in range(5):
            response = client.get(f"/api/v1/notes/{note_id}")
            assert response.status_code == 200
            assert response.get_json()["title"] == "Persistence Test"

        # Cleanup
        client.delete(f"/api/v1/notes/{note_id}")

    def test_updates_are_persisted(self, client):
        """Test that updates are properly persisted."""
        # Create a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Update Test", "content": "Version 1"}),
            content_type="application/json",
        ).get_json()
        note_id = note["id"]

        # Perform multiple updates
        versions = ["Version 2", "Version 3", "Version 4"]
        for version in versions:
            client.put(
                f"/api/v1/notes/{note_id}",
                data=json.dumps({"content": version}),
                content_type="application/json",
            )

            # Verify each update persisted
            response = client.get(f"/api/v1/notes/{note_id}")
            assert response.get_json()["content"] == version

        # Cleanup
        client.delete(f"/api/v1/notes/{note_id}")
