import os
import traceback
from typing import Tuple

from flask import Flask, Response, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from simple_api.utils import errors, logger

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

LOG = logger.setup(level=LOG_LEVEL)


def register_error_handlers(app: Flask) -> None:
    """Register all error handlers for the Flask app.

    These handlers catch exceptions and HTTP errors throughout the application
    and return consistent JSON error responses. Error responses are documented
    in individual endpoint Swagger specifications.
    """

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> Tuple[Response, int]:
        """Handle Pydantic validation errors.

        Returns a 400 Bad Request with validation error details.
        Response format:
        {
            "error": "Validation error",
            "details": [
                {
                    "field": "field_name",
                    "message": "error message",
                    "type": "error_type"
                }
            ]
        }
        """
        LOG.warning(f"Validation error: {error}")

        errors = []
        for err in error.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            errors.append({"field": field, "message": err["msg"], "type": err["type"]})

        return (
            jsonify({"error": "Validation error", "details": errors}),
            400,
        )

    @app.errorhandler(errors.InvalidUUIDError)
    def handle_invalid_uuid(error: errors.InvalidUUIDError) -> Tuple[Response, int]:
        """Handle invalid UUID errors.

        Returns a 400 Bad Request when an invalid UUID format is provided.
        Response format: {"error": "Invalid UUID format: <uuid>"}
        """
        LOG.warning(f"Invalid UUID: {error}")
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(errors.PayloadTooLargeError)
    def handle_payload_too_large(
        error: errors.PayloadTooLargeError,
    ) -> Tuple[Response, int]:
        """Handle payload too large errors.

        Returns a 413 Payload Too Large when request exceeds MAX_CONTENT_LENGTH.
        Response format: {"error": "Payload too large"}
        """
        LOG.warning(f"Payload too large: {error}")
        return jsonify({"error": str(error)}), 413

    @app.errorhandler(400)
    def handle_bad_request(error: HTTPException) -> Tuple[Response, int]:
        """Handle 400 Bad Request errors.

        Catches general bad request errors from Flask.
        Response format: {"error": "Bad request", "details": <description>}
        """
        LOG.warning(f"Bad request: {error}")
        return (
            jsonify(
                {
                    "error": "Bad request",
                    "details": error.description if error.description else None,
                }
            ),
            400,
        )

    @app.errorhandler(404)
    def handle_not_found(error: HTTPException) -> Tuple[Response, int]:
        """Handle 404 Not Found errors.

        Returns when a requested resource or endpoint does not exist.
        Response format: {"error": "Not found"}
        """
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error: HTTPException) -> Tuple[Response, int]:
        """Handle 405 Method Not Allowed errors.

        Returns when an HTTP method is not supported for the endpoint.
        Response format: {"error": "Method not allowed", "details": <message>}
        """
        LOG.warning(f"Method not allowed: {error}")
        return (
            jsonify(
                {
                    "error": "Method not allowed",
                    "details": "The method is not allowed for the requested URL.",
                }
            ),
            405,
        )

    @app.errorhandler(413)
    def handle_request_entity_too_large(error: HTTPException) -> Tuple[Response, int]:
        """Handle 413 Request Entity Too Large errors.

        Returns when request payload exceeds MAX_CONTENT_LENGTH configuration.
        Response format: {"error": "Payload too large", "details": <message>}
        """
        LOG.warning(f"Request entity too large: {error}")
        return (
            jsonify(
                {
                    "error": "Payload too large",
                    "details": "Request payload exceeds maximum allowed size",
                }
            ),
            413,
        )

    @app.errorhandler(415)
    def handle_unsupported_media_type(error: HTTPException) -> Tuple[Response, int]:
        """Handle 415 Unsupported Media Type errors.

        Returns when Content-Type header is not application/json.
        Response format: {"error": "Unsupported media type", "details": <message>}
        """
        LOG.warning(f"Unsupported media type: {error}")
        return (
            jsonify(
                {
                    "error": "Unsupported media type",
                    "details": "Content-Type must be application/json",
                }
            ),
            415,
        )

    @app.errorhandler(500)
    def handle_internal_server_error(error: Exception) -> Tuple[Response, int]:
        """Handle 500 Internal Server Error.

        Catches server-side errors. Full stack trace is logged but not exposed.
        Response format: {"error": "Internal server error", "details": <generic message>}
        """
        LOG.error(f"Internal server error: {error}")
        LOG.error(traceback.format_exc())

        # Don't expose internal error details in production
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "details": "An unexpected error occurred. Please try again later.",
                }
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> Tuple[Response, int]:
        """Handle any unexpected errors.

        Catch-all handler for unhandled exceptions. Logs full error and returns generic message.
        Response format: {"error": "Internal server error", "details": <generic message>}
        """
        LOG.error(f"Unexpected error: {error}")
        LOG.error(traceback.format_exc())

        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "details": "An unexpected error occurred. Please try again later.",
                }
            ),
            500,
        )
