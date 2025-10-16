"""Tests for the NoteService."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from simple_api.models import Note
from simple_api.repository import NoteRepository
from simple_api.service import NoteService


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    return MagicMock(spec=NoteRepository)


@pytest.fixture
def service(mock_repository):
    """Create a service with a mock repository."""
    return NoteService(mock_repository)


@pytest.fixture
def sample_note():
    """Create a sample note for testing."""
    return Note(
        id="test-123",
        title="Test Note",
        content="Test content",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        completed=False,
    )


class TestNoteService:
    """Test suite for NoteService."""

    def test_create_note(self, service, mock_repository):
        """Test creating a note."""
        title = "New Note"
        content = "New content"

        # Mock the repository to return the created note
        expected_note = Note(
            id="generated-id",
            title=title,
            content=content,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completed=False,
        )
        mock_repository.create.return_value = expected_note

        result = service.create_note(title, content)

        # Verify repository.create was called once
        assert mock_repository.create.call_count == 1

        # Verify the created note has correct properties
        created_note = mock_repository.create.call_args[0][0]
        assert created_note.title == title
        assert created_note.content == content
        assert created_note.completed is False
        assert created_note.id is not None  # UUID should be generated

        # Verify result
        assert result == expected_note

    def test_get_note_existing(self, service, mock_repository, sample_note):
        """Test getting an existing note."""
        mock_repository.get.return_value = sample_note

        result = service.get_note(sample_note.id)

        mock_repository.get.assert_called_once_with(sample_note.id)
        assert result == sample_note

    def test_get_note_nonexistent(self, service, mock_repository):
        """Test getting a note that doesn't exist."""
        mock_repository.get.return_value = None

        result = service.get_note("nonexistent-id")

        mock_repository.get.assert_called_once_with("nonexistent-id")
        assert result is None

    def test_get_all_notes_empty(self, service, mock_repository):
        """Test getting all notes when there are none."""
        mock_repository.get_all.return_value = []

        result = service.get_all_notes()

        mock_repository.get_all.assert_called_once()
        assert result == []

    def test_get_all_notes_with_data(self, service, mock_repository):
        """Test getting all notes when there are some."""
        notes = [
            Note(
                id=f"{i}",
                title=f"Note {i}",
                content=f"Content {i}",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(3)
        ]
        mock_repository.get_all.return_value = notes

        result = service.get_all_notes()

        mock_repository.get_all.assert_called_once()
        assert result == notes
        assert len(result) == 3

    def test_update_note_all_fields(self, service, mock_repository, sample_note):
        """Test updating all fields of a note."""
        mock_repository.get.return_value = sample_note

        updated_note = Note(
            id=sample_note.id,
            title="Updated Title",
            content="Updated Content",
            created_at=sample_note.created_at,
            updated_at=datetime.now(),
            completed=True,
        )
        mock_repository.update.return_value = updated_note

        result = service.update_note(
            sample_note.id,
            title="Updated Title",
            content="Updated Content",
            completed=True,
        )

        mock_repository.get.assert_called_once_with(sample_note.id)
        assert mock_repository.update.call_count == 1
        assert result == updated_note

    def test_update_note_partial_title_only(self, service, mock_repository, sample_note):
        """Test updating only the title of a note."""
        mock_repository.get.return_value = sample_note
        mock_repository.update.return_value = sample_note

        result = service.update_note(sample_note.id, title="New Title")

        mock_repository.get.assert_called_once_with(sample_note.id)
        # Verify the note was updated with only the title changed
        updated_note = mock_repository.update.call_args[0][1]
        assert updated_note.title == "New Title"
        assert updated_note.content == sample_note.content  # Unchanged
        assert updated_note.completed == sample_note.completed  # Unchanged

    def test_update_note_partial_content_only(self, service, mock_repository, sample_note):
        """Test updating only the content of a note."""
        mock_repository.get.return_value = sample_note
        mock_repository.update.return_value = sample_note

        result = service.update_note(sample_note.id, content="New Content")

        updated_note = mock_repository.update.call_args[0][1]
        assert updated_note.title == sample_note.title  # Unchanged
        assert updated_note.content == "New Content"
        assert updated_note.completed == sample_note.completed  # Unchanged

    def test_update_note_partial_completed_only(self, service, mock_repository, sample_note):
        """Test updating only the completed status of a note."""
        mock_repository.get.return_value = sample_note
        mock_repository.update.return_value = sample_note

        result = service.update_note(sample_note.id, completed=True)

        updated_note = mock_repository.update.call_args[0][1]
        assert updated_note.title == sample_note.title  # Unchanged
        assert updated_note.content == sample_note.content  # Unchanged
        assert updated_note.completed is True

    def test_update_note_nonexistent(self, service, mock_repository):
        """Test updating a note that doesn't exist."""
        mock_repository.get.return_value = None

        result = service.update_note("nonexistent-id", title="New Title")

        mock_repository.get.assert_called_once_with("nonexistent-id")
        mock_repository.update.assert_not_called()
        assert result is None

    def test_update_note_updates_timestamp(self, service, mock_repository, sample_note):
        """Test that updating a note updates the updated_at timestamp."""
        original_updated_at = sample_note.updated_at
        mock_repository.get.return_value = sample_note
        mock_repository.update.return_value = sample_note

        service.update_note(sample_note.id, title="New Title")

        updated_note = mock_repository.update.call_args[0][1]
        assert updated_note.updated_at > original_updated_at

    def test_delete_note_existing(self, service, mock_repository):
        """Test deleting an existing note."""
        mock_repository.delete.return_value = True

        result = service.delete_note("test-123")

        mock_repository.delete.assert_called_once_with("test-123")
        assert result is True

    def test_delete_note_nonexistent(self, service, mock_repository):
        """Test deleting a note that doesn't exist."""
        mock_repository.delete.return_value = False

        result = service.delete_note("nonexistent-id")

        mock_repository.delete.assert_called_once_with("nonexistent-id")
        assert result is False

    def test_create_note_generates_unique_ids(self, service, mock_repository):
        """Test that creating multiple notes generates unique IDs."""
        mock_repository.create.side_effect = lambda note: note

        note1 = service.create_note("Note 1", "Content 1")
        note2 = service.create_note("Note 2", "Content 2")

        # Extract the created notes from mock calls
        created_note1 = mock_repository.create.call_args_list[0][0][0]
        created_note2 = mock_repository.create.call_args_list[1][0][0]

        assert created_note1.id != created_note2.id

    def test_create_note_sets_timestamps(self, service, mock_repository):
        """Test that creating a note sets created_at and updated_at timestamps."""
        mock_repository.create.side_effect = lambda note: note

        before = datetime.now()
        service.create_note("Test", "Content")
        after = datetime.now()

        created_note = mock_repository.create.call_args[0][0]
        assert before <= created_note.created_at <= after
        assert before <= created_note.updated_at <= after
        assert created_note.created_at == created_note.updated_at


class TestNoteServiceIntegration:
    """Integration tests for NoteService with real repository."""

    @pytest.fixture
    def real_service(self):
        """Create a service with a real repository."""
        repository = NoteRepository()
        return NoteService(repository)

    def test_full_crud_cycle(self, real_service):
        """Test a complete CRUD cycle."""
        # Create
        note = real_service.create_note("Test Note", "Test Content")
        assert note.id is not None
        assert note.title == "Test Note"
        assert note.content == "Test Content"
        assert note.completed is False

        # Read
        retrieved = real_service.get_note(note.id)
        assert retrieved == note

        # Update
        updated = real_service.update_note(
            note.id, title="Updated", content="Updated Content", completed=True
        )
        assert updated.title == "Updated"
        assert updated.content == "Updated Content"
        assert updated.completed is True

        # Delete
        success = real_service.delete_note(note.id)
        assert success is True

        # Verify deletion
        deleted = real_service.get_note(note.id)
        assert deleted is None

    def test_get_all_returns_all_notes(self, real_service):
        """Test that get_all returns all created notes."""
        note1 = real_service.create_note("Note 1", "Content 1")
        note2 = real_service.create_note("Note 2", "Content 2")
        note3 = real_service.create_note("Note 3", "Content 3")

        all_notes = real_service.get_all_notes()

        assert len(all_notes) == 3
        assert note1 in all_notes
        assert note2 in all_notes
        assert note3 in all_notes
