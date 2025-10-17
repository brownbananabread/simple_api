"""Business logic layer for notes."""

import uuid
from datetime import datetime
from typing import List, Optional

from simple_api.models import Note
from simple_api.repository import NoteRepository


class NoteService:
    """Service for managing note business logic."""

    def __init__(self, repository: NoteRepository):
        """Initialize the service with a repository."""
        self._repository = repository

    def create_note(self, title: str, content: str) -> Note:
        """Create a new note."""
        now = datetime.now()
        note = Note(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            created_at=now,
            updated_at=now,
            completed=False,
        )
        return self._repository.create(note)

    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a note by ID."""
        return self._repository.get(note_id)

    def get_all_notes(self) -> List[Note]:
        """Get all notes."""
        return self._repository.get_all()

    def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Optional[Note]:
        """Update an existing note."""
        note = self._repository.get(note_id)
        if not note:
            return None

        # Update only provided fields
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if completed is not None:
            note.completed = completed

        note.updated_at = datetime.now()
        return self._repository.update(note_id, note)

    def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        return self._repository.delete(note_id)
