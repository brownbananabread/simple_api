"""Data access layer for notes."""

from typing import Dict, List, Optional

from simple_api.models import Note


class NoteRepository:
    """Repository for managing note data storage."""

    def __init__(self):
        """Initialize the repository with in-memory storage."""
        self._notes: Dict[str, Note] = {}

    def create(self, note: Note) -> Note:
        """Create a new note."""
        self._notes[note.id] = note
        return note

    def get(self, note_id: str) -> Optional[Note]:
        """Get a note by ID."""
        return self._notes.get(note_id)

    def get_all(self) -> List[Note]:
        """Get all notes."""
        return list(self._notes.values())

    def update(self, note_id: str, note: Note) -> Optional[Note]:
        """Update an existing note."""
        if note_id not in self._notes:
            return None
        self._notes[note_id] = note
        return note

    def delete(self, note_id: str) -> bool:
        """Delete a note by ID."""
        if note_id not in self._notes:
            return False
        del self._notes[note_id]
        return True

    def exists(self, note_id: str) -> bool:
        """Check if a note exists."""
        return note_id in self._notes
