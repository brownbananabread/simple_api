"""Data models for the application."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Note:
    """Note model representing a todo item."""

    id: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    completed: bool = False

    def to_dict(self) -> dict:
        """Convert note to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        """Create note from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed=data.get("completed", False),
        )
