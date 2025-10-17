from flask import Flask, jsonify, request

from simple_api.schemas import NoteCreateRequest, NoteUpdateRequest
from simple_api.service import NoteService
from simple_api.utils import validators

def register_handlers(app: Flask, note_service: NoteService) -> None:
    """Register health check endpoints."""

    @app.route("/api/v1/notes", methods=["POST"])
    def create_note():
        """Create a new note.
        ---
        tags:
          - Notes
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - title
                - content
              properties:
                title:
                  type: string
                  example: "Buy groceries"
                  minLength: 1
                  maxLength: 200
                content:
                  type: string
                  example: "Milk, eggs, bread, and coffee"
                  minLength: 1
                  maxLength: 10000
        responses:
          201:
            description: Note created successfully
            schema:
              type: object
              properties:
                id:
                  type: string
                  example: "123e4567-e89b-12d3-a456-426614174000"
                title:
                  type: string
                  example: "Buy groceries"
                content:
                  type: string
                  example: "Milk, eggs, bread, and coffee"
                created_at:
                  type: string
                  example: "2025-10-17T12:00:00"
                updated_at:
                  type: string
                  example: "2025-10-17T12:00:00"
                completed:
                  type: boolean
                  example: false
          400:
            description: Invalid request
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Validation error"
                details:
                  type: array
                  items:
                    type: object
        """
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate using Pydantic schema
        validated_data = NoteCreateRequest(**data)

        note = note_service.create_note(
            title=validated_data.title, content=validated_data.content
        )
        return jsonify(note.to_dict()), 201

    @app.route("/api/v1/notes", methods=["GET"])
    def get_all_notes():
        """Get all notes.
        ---
        tags:
          - Notes
        responses:
          200:
            description: List of all notes
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  title:
                    type: string
                  content:
                    type: string
                  created_at:
                    type: string
                  updated_at:
                    type: string
                  completed:
                    type: boolean
        """
        notes = note_service.get_all_notes()
        return jsonify([note.to_dict() for note in notes]), 200
    
    @app.route("/api/v1/notes/<note_id>", methods=["GET"])
    def get_note(note_id: str):
        """Get a specific note.
        ---
        tags:
          - Notes
        parameters:
          - name: note_id
            in: path
            type: string
            required: true
            description: The UUID of the note
            format: uuid
        responses:
          200:
            description: Note found
            schema:
              type: object
              properties:
                id:
                  type: string
                title:
                  type: string
                content:
                  type: string
                created_at:
                  type: string
                updated_at:
                  type: string
                completed:
                  type: boolean
          400:
            description: Invalid UUID format
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Invalid UUID format: abc123"
          404:
            description: Note not found
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Note not found"
        """
        # Validate UUID format
        validators.validate_uuid(note_id)

        note = note_service.get_note(note_id)
        if not note:
            return jsonify({"error": "Note not found"}), 404
        return jsonify(note.to_dict()), 200

    @app.route("/api/v1/notes/<note_id>", methods=["PUT"])
    def update_note(note_id: str):
        """Update a note.
        ---
        tags:
          - Notes
        parameters:
          - name: note_id
            in: path
            type: string
            required: true
            description: The UUID of the note
            format: uuid
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                title:
                  type: string
                  example: "Buy groceries"
                  minLength: 1
                  maxLength: 200
                content:
                  type: string
                  example: "Milk, eggs, bread, coffee, and butter"
                  minLength: 1
                  maxLength: 10000
                completed:
                  type: boolean
                  example: true
        responses:
          200:
            description: Note updated successfully
            schema:
              type: object
              properties:
                id:
                  type: string
                title:
                  type: string
                content:
                  type: string
                created_at:
                  type: string
                updated_at:
                  type: string
                completed:
                  type: boolean
          400:
            description: Invalid request
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Validation error"
                details:
                  type: array
                  items:
                    type: object
          404:
            description: Note not found
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Note not found"
        """
        # Validate UUID format
        validators.validate_uuid(note_id)

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate using Pydantic schema
        validated_data = NoteUpdateRequest(**data)

        note = note_service.update_note(
            note_id=note_id,
            title=validated_data.title,
            content=validated_data.content,
            completed=validated_data.completed,
        )

        if not note:
            return jsonify({"error": "Note not found"}), 404

        return jsonify(note.to_dict()), 200

    @app.route("/api/v1/notes/<note_id>", methods=["DELETE"])
    def delete_note(note_id: str):
        """Delete a note.
        ---
        tags:
          - Notes
        parameters:
          - name: note_id
            in: path
            type: string
            required: true
            description: The UUID of the note
            format: uuid
        responses:
          200:
            description: Note deleted successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Note deleted successfully"
          400:
            description: Invalid UUID format
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Invalid UUID format: abc123"
          404:
            description: Note not found
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Note not found"
        """
        # Validate UUID format
        validators.validate_uuid(note_id)

        success = note_service.delete_note(note_id)
        if not success:
            return jsonify({"error": "Note not found"}), 404
        return jsonify({"message": "Note deleted successfully"}), 200