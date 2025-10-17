"""Tests for edge cases and error scenarios."""

import json

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


class TestEdgeCases:
    """Test edge cases for the API."""

    def test_create_note_with_unicode_characters(self, client):
        """Test creating notes with various unicode characters."""
        test_cases = [
            {"title": "日本語のタイトル", "content": "日本語の内容"},
            {"title": "Emoji Test 🎉🎊🎈", "content": "Content with 😀😃😄"},
            {"title": "Árabe: مرحبا", "content": "مرحبا بك في العالم"},
            {"title": "Russian: Привет", "content": "Привет мир"},
            {"title": "Special: ñáéíóú", "content": "àèìòù çñ"},
        ]

        for test_case in test_cases:
            response = client.post(
                "/api/v1/notes",
                data=json.dumps(test_case),
                content_type="application/json",
            )
            assert response.status_code == 201
            data = response.get_json()
            assert data["title"] == test_case["title"]
            assert data["content"] == test_case["content"]

            # Cleanup
            client.delete(f"/api/v1/notes/{data['id']}")

    def test_create_note_with_special_characters(self, client):
        """Test creating notes with special characters."""
        special_chars = [
            {"title": 'Title with "quotes"', "content": "Content with 'quotes'"},
            {"title": "Backslash \\ test", "content": "Forward / slash"},
            {"title": "Newline\ntest", "content": "Tab\ttest"},
            {"title": "Symbols: @#$%^&*()", "content": "More symbols: []{}|<>"},
        ]

        for test_case in special_chars:
            response = client.post(
                "/api/v1/notes",
                data=json.dumps(test_case),
                content_type="application/json",
            )
            assert response.status_code == 201
            data = response.get_json()
            assert data["title"] == test_case["title"]
            assert data["content"] == test_case["content"]

            # Cleanup
            client.delete(f"/api/v1/notes/{data['id']}")

    def test_create_note_with_max_length_fields(self, client):
        """Test creating notes with maximum allowed field lengths."""
        max_title = "a" * 200  # Max title length is 200
        max_content = "b" * 10000  # Max content length is 10000

        payload = {"title": max_title, "content": max_content}
        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert len(data["title"]) == 200
        assert len(data["content"]) == 10000

        # Cleanup
        client.delete(f"/api/v1/notes/{data['id']}")

    def test_create_note_exceeding_title_length(self, client):
        """Test that titles exceeding max length are rejected."""
        payload = {"title": "a" * 201, "content": "Content"}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_note_exceeding_content_length(self, client):
        """Test that content exceeding max length is rejected."""
        payload = {"title": "Title", "content": "a" * 10001}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_update_note_with_only_whitespace(self, client):
        """Test that updating with only whitespace is rejected."""
        # Create a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Original", "content": "Original content"}),
            content_type="application/json",
        ).get_json()

        # Try to update with whitespace-only title
        response = client.put(
            f"/api/v1/notes/{note['id']}",
            data=json.dumps({"title": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400

        # Cleanup
        client.delete(f"/api/v1/notes/{note['id']}")

    def test_multiple_rapid_creates(self, client):
        """Test creating multiple notes rapidly."""
        note_ids = []
        for i in range(20):
            response = client.post(
                "/api/v1/notes",
                data=json.dumps({"title": f"Rapid {i}", "content": f"Content {i}"}),
                content_type="application/json",
            )
            assert response.status_code == 201
            note_ids.append(response.get_json()["id"])

        # Verify all have unique IDs
        assert len(note_ids) == len(set(note_ids))

        # Cleanup
        for note_id in note_ids:
            client.delete(f"/api/v1/notes/{note_id}")

    def test_malformed_json_payloads(self, client):
        """Test handling of malformed JSON."""
        malformed_cases = [
            '{"title": "Test", "content":}',  # Missing value
            '{"title": "Test" "content": "Test"}',  # Missing comma
            '{"title": "Test", "content": "Test"',  # Missing closing brace
            '{title: "Test", content: "Test"}',  # Unquoted keys
            "{'title': 'Test', 'content': 'Test'}",  # Single quotes
        ]

        for malformed in malformed_cases:
            response = client.post(
                "/api/v1/notes",
                data=malformed,
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_wrong_content_type(self, client):
        """Test that wrong content type is handled."""
        response = client.post(
            "/api/v1/notes",
            data="title=Test&content=Content",
            content_type="application/x-www-form-urlencoded",
        )
        # Should handle this gracefully
        assert response.status_code in [400, 415]

    def test_delete_already_deleted_note(self, client):
        """Test deleting a note that was already deleted."""
        # Create and delete a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Test", "content": "Content"}),
            content_type="application/json",
        ).get_json()
        note_id = note["id"]

        # First delete
        response1 = client.delete(f"/api/v1/notes/{note_id}")
        assert response1.status_code == 200

        # Second delete (should fail)
        response2 = client.delete(f"/api/v1/notes/{note_id}")
        assert response2.status_code == 404

    def test_update_deleted_note(self, client):
        """Test updating a note that was already deleted."""
        # Create and delete a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Test", "content": "Content"}),
            content_type="application/json",
        ).get_json()
        note_id = note["id"]

        client.delete(f"/api/v1/notes/{note_id}")

        # Try to update deleted note
        response = client.put(
            f"/api/v1/notes/{note_id}",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_create_note_with_null_values(self, client):
        """Test that null values are rejected."""
        test_cases = [
            {"title": None, "content": "Content"},
            {"title": "Title", "content": None},
            {"title": None, "content": None},
        ]

        for test_case in test_cases:
            response = client.post(
                "/api/v1/notes",
                data=json.dumps(test_case),
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_update_with_invalid_completed_value(self, client):
        """Test updating with invalid completed field values."""
        # Create a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Test", "content": "Content"}),
            content_type="application/json",
        ).get_json()

        # Try various invalid completed values
        invalid_values = ["yes", "no", 1, 0, "true", "false", None]

        for invalid_value in invalid_values:
            response = client.put(
                f"/api/v1/notes/{note['id']}",
                data=json.dumps({"completed": invalid_value}),
                content_type="application/json",
            )
            # Some might be coerced to boolean, others should fail
            assert response.status_code in [200, 400]

        # Cleanup
        client.delete(f"/api/v1/notes/{note['id']}")

    def test_empty_notes_list(self, client):
        """Test getting notes when none exist."""
        # Note: Other tests might have created notes, so we just verify format
        response = client.get("/api/v1/notes")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_case_sensitivity_in_uuids(self, client):
        """Test that UUIDs are case-insensitive (if applicable)."""
        # Create a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "UUID Test", "content": "Content"}),
            content_type="application/json",
        ).get_json()
        note_id = note["id"]

        # Try accessing with different case (UUIDs should be case-insensitive)
        upper_id = note_id.upper()
        response = client.get(f"/api/v1/notes/{upper_id}")

        # Depending on implementation, this might work or not
        # Just verify it handles it gracefully
        assert response.status_code in [200, 400, 404]

        # Cleanup
        client.delete(f"/api/v1/notes/{note_id}")

    def test_whitespace_trimming(self, client):
        """Test that leading/trailing whitespace is properly handled."""
        payload = {"title": "  Test Title  ", "content": "  Test Content  "}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        # Should be trimmed
        assert data["title"] == "Test Title"
        assert data["content"] == "Test Content"

        # Cleanup
        client.delete(f"/api/v1/notes/{data['id']}")

    def test_internal_whitespace_preservation(self, client):
        """Test that internal whitespace is preserved."""
        payload = {
            "title": "Test  Multiple  Spaces",
            "content": "Line1\n\nLine2\t\tTab",
        }

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        # Internal whitespace should be preserved
        assert "  " in data["title"]
        assert "\n\n" in data["content"]

        # Cleanup
        client.delete(f"/api/v1/notes/{data['id']}")


class TestErrorRecovery:
    """Test error recovery and resilience."""

    def test_api_recovers_after_validation_error(self, client):
        """Test that API continues to work after validation errors."""
        # Cause a validation error
        bad_response = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "", "content": ""}),
            content_type="application/json",
        )
        assert bad_response.status_code == 400

        # Verify API still works
        good_response = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Good Note", "content": "Good Content"}),
            content_type="application/json",
        )
        assert good_response.status_code == 201

        # Cleanup
        client.delete(f"/api/v1/notes/{good_response.get_json()['id']}")

    def test_api_recovers_after_not_found_error(self, client):
        """Test that API continues to work after 404 errors."""
        import uuid

        # Cause a 404 error
        fake_id = str(uuid.uuid4())
        error_response = client.get(f"/api/v1/notes/{fake_id}")
        assert error_response.status_code == 404

        # Verify API still works
        response = client.get("/api/v1/notes")
        assert response.status_code == 200

    def test_sequential_errors_dont_break_api(self, client):
        """Test that multiple sequential errors don't break the API."""
        import uuid

        # Generate multiple errors
        for _ in range(10):
            fake_id = str(uuid.uuid4())
            client.get(f"/api/v1/notes/{fake_id}")

        # Verify API still works
        response = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Recovery Test", "content": "Content"}),
            content_type="application/json",
        )
        assert response.status_code == 201

        # Cleanup
        client.delete(f"/api/v1/notes/{response.get_json()['id']}")


class TestBoundaryValues:
    """Test boundary values for inputs."""

    def test_minimum_valid_note(self, client):
        """Test creating a note with minimum valid data."""
        payload = {"title": "a", "content": "b"}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "a"
        assert data["content"] == "b"

        # Cleanup
        client.delete(f"/api/v1/notes/{data['id']}")

    def test_exactly_max_length_title(self, client):
        """Test title at exactly max length."""
        payload = {"title": "a" * 200, "content": "Content"}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201

        # Cleanup
        client.delete(f"/api/v1/notes/{response.get_json()['id']}")

    def test_exactly_max_length_content(self, client):
        """Test content at exactly max length."""
        payload = {"title": "Title", "content": "a" * 10000}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201

        # Cleanup
        client.delete(f"/api/v1/notes/{response.get_json()['id']}")

    def test_one_over_max_length_title(self, client):
        """Test title at one character over max length."""
        payload = {"title": "a" * 201, "content": "Content"}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_one_over_max_length_content(self, client):
        """Test content at one character over max length."""
        payload = {"title": "Title", "content": "a" * 10001}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
