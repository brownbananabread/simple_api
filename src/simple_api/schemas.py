"""Pydantic schemas for request/response validation."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class NoteCreateRequest(BaseModel):
    """Schema for creating a note."""

    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(..., min_length=1, max_length=10000, description="Note content")

    @field_validator("title", "content")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that strings are not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()


class NoteUpdateRequest(BaseModel):
    """Schema for updating a note."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Note title")
    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="Note content")
    completed: Optional[bool] = Field(None, description="Completion status")

    @field_validator("title", "content")
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that strings are not empty or whitespace only."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Field cannot be empty or whitespace only")
            return v.strip()
        return v

    def model_post_init(self, __context) -> None:
        """Validate that at least one field is provided."""
        if self.title is None and self.content is None and self.completed is None:
            raise ValueError("At least one field (title, content, or completed) must be provided")
