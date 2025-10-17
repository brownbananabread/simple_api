"""Tests for the NoteRepository."""

from datetime import datetime

import pytest

from simple_api.models import Note
from simple_api.repository import NoteRepository


@pytest.fixture
def repository():
    """Create a fresh repository for each test."""
    return NoteRepository()


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


class TestNoteRepository:
    """Test suite for NoteRepository."""

    def test_create_note(self, repository, sample_note):
        """Test creating a note."""
        result = repository.create(sample_note)

        assert result == sample_note
        assert repository.get(sample_note.id) == sample_note

    def test_get_existing_note(self, repository, sample_note):
        """Test retrieving an existing note."""
        repository.create(sample_note)
        result = repository.get(sample_note.id)

        assert result == sample_note
        assert result.id == sample_note.id
        assert result.title == sample_note.title

    def test_get_nonexistent_note(self, repository):
        """Test retrieving a note that doesn't exist."""
        result = repository.get("nonexistent-id")
        assert result is None

    def test_get_all_empty(self, repository):
        """Test getting all notes when repository is empty."""
        result = repository.get_all()
        assert result == []

    def test_get_all_with_notes(self, repository):
        """Test getting all notes when repository has notes."""
        note1 = Note(
            id="1",
            title="Note 1",
            content="Content 1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        note2 = Note(
            id="2",
            title="Note 2",
            content="Content 2",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        repository.create(note1)
        repository.create(note2)

        result = repository.get_all()
        assert len(result) == 2
        assert note1 in result
        assert note2 in result

    def test_update_existing_note(self, repository, sample_note):
        """Test updating an existing note."""
        repository.create(sample_note)

        updated_note = Note(
            id=sample_note.id,
            title="Updated Title",
            content="Updated content",
            created_at=sample_note.created_at,
            updated_at=datetime.now(),
            completed=True,
        )

        result = repository.update(sample_note.id, updated_note)

        assert result == updated_note
        assert result.title == "Updated Title"
        assert result.content == "Updated content"
        assert result.completed is True

    def test_update_nonexistent_note(self, repository, sample_note):
        """Test updating a note that doesn't exist."""
        result = repository.update("nonexistent-id", sample_note)
        assert result is None

    def test_delete_existing_note(self, repository, sample_note):
        """Test deleting an existing note."""
        repository.create(sample_note)
        result = repository.delete(sample_note.id)

        assert result is True
        assert repository.get(sample_note.id) is None

    def test_delete_nonexistent_note(self, repository):
        """Test deleting a note that doesn't exist."""
        result = repository.delete("nonexistent-id")
        assert result is False

    def test_exists_with_existing_note(self, repository, sample_note):
        """Test checking if a note exists when it does."""
        repository.create(sample_note)
        assert repository.exists(sample_note.id) is True

    def test_exists_with_nonexistent_note(self, repository):
        """Test checking if a note exists when it doesn't."""
        assert repository.exists("nonexistent-id") is False

    def test_create_multiple_notes(self, repository):
        """Test creating multiple notes."""
        notes = [
            Note(
                id=f"note-{i}",
                title=f"Note {i}",
                content=f"Content {i}",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(5)
        ]

        for note in notes:
            repository.create(note)

        all_notes = repository.get_all()
        assert len(all_notes) == 5

    def test_update_preserves_other_notes(self, repository):
        """Test that updating one note doesn't affect others."""
        note1 = Note(
            id="1",
            title="Note 1",
            content="Content 1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        note2 = Note(
            id="2",
            title="Note 2",
            content="Content 2",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        repository.create(note1)
        repository.create(note2)

        updated_note1 = Note(
            id="1",
            title="Updated Note 1",
            content="Updated Content 1",
            created_at=note1.created_at,
            updated_at=datetime.now(),
        )

        repository.update("1", updated_note1)

        # Check that note2 is unchanged
        retrieved_note2 = repository.get("2")
        assert retrieved_note2.title == "Note 2"
        assert retrieved_note2.content == "Content 2"

    def test_delete_preserves_other_notes(self, repository):
        """Test that deleting one note doesn't affect others."""
        note1 = Note(
            id="1",
            title="Note 1",
            content="Content 1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        note2 = Note(
            id="2",
            title="Note 2",
            content="Content 2",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        repository.create(note1)
        repository.create(note2)

        repository.delete("1")

        # Check that note2 still exists
        retrieved_note2 = repository.get("2")
        assert retrieved_note2 is not None
        assert retrieved_note2.title == "Note 2"
