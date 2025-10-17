import os

from flask import Flask, jsonify

from simple_api.middleware import logger
from simple_api.utils import metadata

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

LOG = logger.setup(level=LOG_LEVEL)


def register_handlers(app: Flask) -> None:
    """Register health check endpoints."""

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint.
        ---
        tags:
          - Health
        responses:
          200:
            description: Service is healthy
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: "healthy"
                service:
                  type: string
                  example: "simple_api"
        """
        return jsonify({"status": "healthy", "service": "simple_api"}), 200

    @app.route("/", methods=["GET"])
    def index():
        """Service information endpoint.
        ---
        tags:
          - Health
        responses:
          200:
            description: Service information
            schema:
              type: object
              properties:
                service:
                  type: string
                  example: "simple_api"
                version:
                  type: string
                  example: "0.1.1"
        """
        return jsonify({"service": "simple_api", "version": metadata.VERSION}), 200
