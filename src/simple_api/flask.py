import os

from flask import Flask, jsonify

from simple_api.utils.logger import setup_logger
from simple_api.utils.metadata import NAME, VERSION

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = os.environ.get("SERVER_PORT", 3000)

LOG = setup_logger(level=LOG_LEVEL)


def create_app():
    """Create the Flask application."""
    app = Flask(__name__)

    LOG.info(f"Running {NAME} (v{VERSION}) on {SERVER_HOST}:{SERVER_PORT}")

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "simple_api"}), 200

    @app.route("/", methods=["GET"])
    def index():
        """Index endpoint."""
        return jsonify({"service": "simple_api", "version": VERSION}), 200

    return app
