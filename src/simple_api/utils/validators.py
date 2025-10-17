"""Validation utilities."""

import uuid

from simple_api.utils import errors


def validate_uuid(note_id: str) -> str:
    """
    Validate that a string is a valid UUID.

    Args:
        note_id: The string to validate

    Returns:
        The validated UUID string

    Raises:
        InvalidUUIDError: If the string is not a valid UUID
    """
    try:
        # Try to parse as UUID to validate format
        uuid.UUID(note_id)
        return note_id
    except ValueError:
        raise errors.InvalidUUIDError(f"Invalid UUID format: {note_id}")
