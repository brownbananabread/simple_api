"""Tests for the data models."""

from datetime import datetime

from simple_api.models import Note


class TestNoteModel:
    """Test suite for the Note model."""

    def test_note_creation(self):
        """Test creating a Note instance."""
        now = datetime.now()
        note = Note(
            id="test-123",
            title="Test Note",
            content="Test content",
            created_at=now,
            updated_at=now,
            completed=False,
        )

        assert note.id == "test-123"
        assert note.title == "Test Note"
        assert note.content == "Test content"
        assert note.created_at == now
        assert note.updated_at == now
        assert note.completed is False

    def test_note_to_dict(self):
        """Test converting a note to a dictionary."""
        now = datetime.now()
        note = Note(
            id="test-123",
            title="Test Note",
            content="Test content",
            created_at=now,
            updated_at=now,
            completed=True,
        )

        result = note.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "test-123"
        assert result["title"] == "Test Note"
        assert result["content"] == "Test content"
        assert result["created_at"] == now.isoformat()
        assert result["updated_at"] == now.isoformat()
        assert result["completed"] is True

    def test_note_from_dict(self):
        """Test creating a note from a dictionary."""
        now = datetime.now()
        data = {
            "id": "test-123",
            "title": "Test Note",
            "content": "Test content",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "completed": True,
        }

        note = Note.from_dict(data)

        assert note.id == "test-123"
        assert note.title == "Test Note"
        assert note.content == "Test content"
        assert note.created_at == now
        assert note.updated_at == now
        assert note.completed is True

    def test_note_from_dict_without_completed(self):
        """Test creating a note from dict without completed field."""
        now = datetime.now()
        data = {
            "id": "test-123",
            "title": "Test Note",
            "content": "Test content",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        note = Note.from_dict(data)

        assert note.completed is False  # Default value

    def test_note_round_trip_conversion(self):
        """Test converting note to dict and back."""
        original = Note(
            id="test-123",
            title="Test Note",
            content="Test content",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completed=True,
        )

        # Convert to dict and back
        dict_data = original.to_dict()
        restored = Note.from_dict(dict_data)

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.content == original.content
        assert restored.completed == original.completed
        # Timestamps should be equal (within microsecond precision)
        assert abs((restored.created_at - original.created_at).total_seconds()) < 0.001
        assert abs((restored.updated_at - original.updated_at).total_seconds()) < 0.001

    def test_note_with_empty_strings(self):
        """Test note with empty title and content."""
        now = datetime.now()
        note = Note(
            id="test-123",
            title="",
            content="",
            created_at=now,
            updated_at=now,
            completed=False,
        )

        assert note.title == ""
        assert note.content == ""

    def test_note_with_special_characters(self):
        """Test note with special characters in title and content."""
        now = datetime.now()
        note = Note(
            id="test-123",
            title="Test 🎉 Note with émojis & spëcial chars!",
            content="Content with\nnewlines\tand\ttabs",
            created_at=now,
            updated_at=now,
        )

        assert "🎉" in note.title
        assert "\n" in note.content
        assert "\t" in note.content

    def test_note_with_long_content(self):
        """Test note with very long content."""
        now = datetime.now()
        long_content = "a" * 10000

        note = Note(
            id="test-123",
            title="Long Note",
            content=long_content,
            created_at=now,
            updated_at=now,
        )

        assert len(note.content) == 10000

    def test_note_equality(self):
        """Test that two notes with same data are equal."""
        now = datetime.now()
        note1 = Note(
            id="test-123",
            title="Test",
            content="Content",
            created_at=now,
            updated_at=now,
        )
        note2 = Note(
            id="test-123",
            title="Test",
            content="Content",
            created_at=now,
            updated_at=now,
        )

        assert note1 == note2

    def test_note_default_completed_is_false(self):
        """Test that completed defaults to False."""
        note = Note(
            id="test-123",
            title="Test",
            content="Content",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert note.completed is False

    def test_note_to_dict_preserves_all_fields(self):
        """Test that to_dict preserves all fields."""
        now = datetime.now()
        note = Note(
            id="abc-123",
            title="My Title",
            content="My Content",
            created_at=now,
            updated_at=now,
            completed=True,
        )

        result = note.to_dict()

        # Verify all fields are present
        assert len(result) == 6
        assert "id" in result
        assert "title" in result
        assert "content" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "completed" in result

    def test_note_from_dict_with_extra_fields(self):
        """Test from_dict ignores extra fields."""
        now = datetime.now()
        data = {
            "id": "test-123",
            "title": "Test",
            "content": "Content",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "completed": False,
            "extra_field": "should be ignored",
        }

        note = Note.from_dict(data)

        assert note.id == "test-123"
        assert not hasattr(note, "extra_field")

    def test_note_iso_format_timestamps(self):
        """Test that timestamps are properly converted to ISO format."""
        note = Note(
            id="test",
            title="Test",
            content="Content",
            created_at=datetime(2025, 10, 17, 12, 30, 45),
            updated_at=datetime(2025, 10, 17, 12, 30, 45),
        )

        result = note.to_dict()

        assert "2025-10-17" in result["created_at"]
        assert "12:30:45" in result["created_at"]
