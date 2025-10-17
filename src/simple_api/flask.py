import os

from flasgger import Swagger  # type: ignore[import-untyped]
from flask import Flask

from simple_api.middleware import logger
from simple_api.repository import NoteRepository
from simple_api.routes import exception, health, notes
from simple_api.service import NoteService
from simple_api.utils import security, swagger

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = os.environ.get("SERVER_PORT", 3000)
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 1024 * 1024))  # 1MB default

LOG = logger.setup(level=LOG_LEVEL)


def create_app():
    """Create the Flask application."""
    app = Flask(__name__)

    # Set max content length to prevent large payloads
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # Security configuration (CORS, headers, rate limiting)
    security.configure_security(app)

    # Request/Response logging middleware
    logger.RequestResponseLogger(app)

    # Swagger configuration
    Swagger(app, config=swagger.CONFIG, template=swagger.TEMPLATE)

    note_repository = NoteRepository()
    note_service = NoteService(note_repository)

    # Register blueprints
    notes.register_handlers(app, note_service)
    health.register_handlers(app)
    exception.register_error_handlers(app)

    return app
