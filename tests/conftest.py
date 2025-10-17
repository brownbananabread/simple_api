"""Pytest configuration and shared fixtures for all tests."""

from datetime import datetime
from typing import Generator

import pytest

from simple_api.flask import create_app
from simple_api.models import Note
from simple_api.repository import NoteRepository
from simple_api.service import NoteService


@pytest.fixture(scope="session")
def app():
    """
    Create a Flask app for testing (session scope).

    This fixture creates a single app instance for the entire test session.
    """
    return create_app()


@pytest.fixture(scope="function")
def client(app):
    """
    Create a test client for each test function.

    This fixture provides a fresh test client for each test,
    ensuring test isolation.
    """
    return app.test_client()


@pytest.fixture(scope="function")
def repository() -> Generator[NoteRepository, None, None]:
    """
    Create a fresh repository for each test.

    This fixture provides an isolated repository instance
    that is cleaned up after each test.
    """
    repo = NoteRepository()
    yield repo
    # Cleanup: remove all notes after test
    for note in repo.get_all():
        repo.delete(note.id)


@pytest.fixture(scope="function")
def service(repository: NoteRepository) -> NoteService:
    """
    Create a service with a fresh repository for each test.

    This fixture provides a service instance with an isolated repository.
    """
    return NoteService(repository)


@pytest.fixture
def sample_note() -> Note:
    """
    Create a sample note for testing.

    Returns a Note instance with test data.
    """
    return Note(
        id="test-123",
        title="Test Note",
        content="Test content",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        completed=False,
    )


@pytest.fixture
def sample_notes() -> list[Note]:
    """
    Create multiple sample notes for testing.

    Returns a list of Note instances with varied test data.
    """
    return [
        Note(
            id=f"test-{i}",
            title=f"Test Note {i}",
            content=f"Test content {i}",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completed=bool(i % 2),
        )
        for i in range(5)
    ]


@pytest.fixture
def create_test_note(client):
    """
    Factory fixture to create test notes via the API.

    Returns a function that creates notes and tracks their IDs
    for automatic cleanup.

    Usage:
        note = create_test_note(title="Test", content="Content")
    """
    created_notes = []

    def _create_note(
        title: str = "Test Note", content: str = "Test content", completed: bool = False
    ):
        import json

        payload = {"title": title, "content": content}
        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )
        if response.status_code == 201:
            note = response.get_json()
            created_notes.append(note["id"])
            return note
        return None

    yield _create_note

    # Cleanup: delete all created notes
    for note_id in created_notes:
        client.delete(f"/api/v1/notes/{note_id}")


@pytest.fixture
def populated_repository(repository: NoteRepository, sample_notes: list[Note]):
    """
    Create a repository pre-populated with sample notes.

    This fixture provides a repository with existing test data.
    """
    for note in sample_notes:
        repository.create(note)
    return repository


@pytest.fixture
def auth_headers():
    """
    Provide authentication headers for testing.

    Note: Currently returns empty dict as auth is not implemented.
    Extend this when authentication is added.
    """
    return {}


@pytest.fixture
def valid_note_payload():
    """Provide a valid note creation payload."""
    return {"title": "Valid Test Note", "content": "Valid test content"}


@pytest.fixture
def invalid_note_payloads():
    """Provide various invalid note payloads for testing."""
    return [
        {},  # Empty payload
        {"title": ""},  # Empty title
        {"content": ""},  # Empty content
        {"title": "Test"},  # Missing content
        {"content": "Test"},  # Missing title
        {"title": " ", "content": " "},  # Whitespace only
        {"title": "a" * 201, "content": "Content"},  # Title too long
        {"title": "Title", "content": "a" * 10001},  # Content too long
        {"title": None, "content": "Content"},  # Null title
        {"title": "Title", "content": None},  # Null content
    ]


@pytest.fixture(autouse=True)
def reset_repository_state():
    """
    Automatically reset repository state between tests.

    This fixture runs automatically before each test to ensure
    a clean slate. It's useful for integration tests.
    """
    # Setup: nothing to do here
    yield
    # Teardown: could add cleanup logic here if needed


# Test markers for categorizing tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "api: mark test as an API test")
    config.addinivalue_line("markers", "edge_case: mark test as an edge case test")


# Pytest hooks for custom behavior
def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically.

    This hook automatically adds markers based on test location and name.
    """
    for item in items:
        # Add markers based on file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add markers based on test name
        if "security" in item.nodeid.lower():
            item.add_marker(pytest.mark.security)

        if "edge" in item.nodeid.lower():
            item.add_marker(pytest.mark.edge_case)

        if "api" in str(item.fspath).lower() or "test_routes" in str(item.fspath):
            item.add_marker(pytest.mark.api)


# Session-level fixtures for expensive operations
@pytest.fixture(scope="session", autouse=True)
def test_session_setup():
    """
    Setup that runs once per test session.

    Use this for expensive setup operations that only need
    to run once for all tests.
    """
    # Setup
    print("\n=== Starting test session ===")

    yield

    # Teardown
    print("\n=== Test session complete ===")


# Helper functions available to all tests
@pytest.fixture
def assert_note_equals():
    """
    Fixture that provides a helper function to compare notes.

    Usage:
        assert_note_equals(note1, note2)
    """

    def _compare_notes(note1: dict, note2: dict, ignore_timestamps: bool = False):
        """Compare two note dictionaries for equality."""
        assert note1["id"] == note2["id"]
        assert note1["title"] == note2["title"]
        assert note1["content"] == note2["content"]
        assert note1["completed"] == note2["completed"]

        if not ignore_timestamps:
            assert note1["created_at"] == note2["created_at"]
            assert note1["updated_at"] == note2["updated_at"]

    return _compare_notes


@pytest.fixture
def make_request(client):
    """
    Factory fixture for making API requests with common defaults.

    Usage:
        response = make_request("POST", "/api/v1/notes", data={"title": "Test"})
    """
    import json

    def _make_request(method: str, endpoint: str, data=None, headers=None):
        """Make an API request with JSON content type."""
        if headers is None:
            headers = {}

        if "content-type" not in (k.lower() for k in headers.keys()):
            headers["Content-Type"] = "application/json"

        request_data = json.dumps(data) if data else None

        if method.upper() == "GET":
            return client.get(endpoint, headers=headers)
        elif method.upper() == "POST":
            return client.post(endpoint, data=request_data, headers=headers)
        elif method.upper() == "PUT":
            return client.put(endpoint, data=request_data, headers=headers)
        elif method.upper() == "DELETE":
            return client.delete(endpoint, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    return _make_request
