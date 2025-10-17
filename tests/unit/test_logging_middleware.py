"""Tests for the request/response logging middleware."""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from simple_api.middleware.logger import RequestResponseLogger, get_logger, log_route, setup


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/test", methods=["GET", "POST"])
    def test_route():
        return {"message": "success"}, 200

    @app.route("/error")
    def error_route():
        return {"error": "Something went wrong"}, 500

    @app.route("/health")
    def health_route():
        return {"status": "healthy"}, 200

    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestLoggerSetup:
    """Test logger setup functions."""

    def test_setup_creates_logger(self):
        """Test that setup creates a logger with correct configuration."""
        logger = setup(level="INFO")
        assert logger.name == "simple_api"
        assert logger.level == logging.INFO

    def test_setup_with_debug_level(self):
        """Test setup with DEBUG level."""
        logger = setup(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_with_numeric_level(self):
        """Test setup with numeric log level."""
        logger = setup(level=logging.WARNING)
        assert logger.level == logging.WARNING

    def test_get_logger_creates_namespaced_logger(self):
        """Test that get_logger creates properly namespaced loggers."""
        setup()
        logger = get_logger("test_module")
        assert logger.name == "simple_api.test_module"


class TestRequestResponseLogger:
    """Test the RequestResponseLogger middleware."""

    def test_middleware_initialization_with_app(self, app):
        """Test that middleware can be initialized with an app."""
        logger = RequestResponseLogger(app)
        assert logger.app == app
        assert logger.logger.name == "simple_api.request_response"

    def test_middleware_initialization_without_app(self):
        """Test that middleware can be initialized without an app."""
        logger = RequestResponseLogger()
        assert logger.app is None
        assert logger.logger.name == "simple_api.request_response"

    def test_init_app(self, app):
        """Test the init_app method."""
        logger = RequestResponseLogger()
        logger.init_app(app)
        assert hasattr(app, "before_request_funcs")
        assert hasattr(app, "after_request_funcs")

    @patch("simple_api.middleware.logger.get_logger")
    def test_info_level_logging(self, mock_get_logger, app, client):
        """Test that INFO level logs basic request info."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = True
        mock_get_logger.return_value = mock_logger

        RequestResponseLogger(app)
        response = client.get("/test")

        assert response.status_code == 200
        # Should log the response
        assert mock_logger.info.called or mock_logger.error.called or mock_logger.warning.called

    @patch("simple_api.middleware.logger.get_logger")
    def test_error_response_logging(self, mock_get_logger, app, client):
        """Test that 5xx errors are logged with error level."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = True
        mock_get_logger.return_value = mock_logger

        RequestResponseLogger(app)
        response = client.get("/error")

        assert response.status_code == 500
        assert mock_logger.error.called

    @patch("simple_api.middleware.logger.get_logger")
    def test_request_with_json_body(self, mock_get_logger, app, client):
        """Test logging of request with JSON body at DEBUG level."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.side_effect = lambda level: level == logging.DEBUG
        mock_get_logger.return_value = mock_logger

        RequestResponseLogger(app)
        response = client.post(
            "/test",
            data=json.dumps({"name": "test", "value": 123}),
            content_type="application/json",
        )

        assert response.status_code == 200
        # At DEBUG level, should log request details
        assert mock_logger.debug.called

    @patch("simple_api.middleware.logger.get_logger")
    def test_before_request_captures_timing(self, mock_get_logger, app, client):
        """Test that before_request captures start time."""
        from flask import g

        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = False
        mock_get_logger.return_value = mock_logger

        RequestResponseLogger(app)

        with app.test_request_context("/test"):
            app.preprocess_request()
            assert hasattr(g, "start_time")
            assert hasattr(g, "request_info")

    @patch("simple_api.middleware.logger.get_logger")
    def test_after_request_calculates_duration(self, mock_get_logger, app, client):
        """Test that after_request calculates duration correctly."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = True
        mock_get_logger.return_value = mock_logger

        RequestResponseLogger(app)
        response = client.get("/test")

        assert response.status_code == 200
        # Check that duration was logged in the message
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        duration_logged = any("Duration:" in str(call) and "ms" in str(call) for call in log_calls)
        assert duration_logged

    @patch("simple_api.middleware.logger.get_logger")
    def test_4xx_errors_logged_as_warning(self, mock_get_logger, app, client):
        """Test that 4xx errors are logged as warnings."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = True
        mock_get_logger.return_value = mock_logger

        @app.route("/notfound")
        def notfound():
            return {"error": "Not found"}, 404

        RequestResponseLogger(app)
        response = client.get("/notfound")

        assert response.status_code == 404
        assert mock_logger.warning.called


class TestLogRouteDecorator:
    """Test the log_route decorator."""

    def test_decorator_logs_route_execution(self, app):
        """Test that decorator logs route execution."""

        @app.route("/decorated")
        @log_route
        def decorated_route():
            return {"status": "ok"}, 200

        with patch("simple_api.middleware.logger.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.return_value = False
            mock_get_logger.return_value = mock_logger

            client = app.test_client()
            response = client.get("/decorated")

            assert response.status_code == 200
            assert mock_logger.info.called

    def test_decorator_logs_exceptions(self, app):
        """Test that decorator logs exceptions."""

        @app.route("/failing")
        @log_route
        def failing_route():
            raise ValueError("Test error")

        with patch("simple_api.middleware.logger.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.return_value = False
            mock_get_logger.return_value = mock_logger

            client = app.test_client()

            with pytest.raises(ValueError):
                client.get("/failing")

            assert mock_logger.error.called

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @log_route
        def test_function():
            """Test docstring."""
            return "result"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring."


class TestMiddlewareIntegration:
    """Integration tests for the logging middleware."""

    def test_full_request_cycle(self, app, client):
        """Test a complete request/response cycle with logging."""
        setup(level="INFO")
        RequestResponseLogger(app)

        response = client.post(
            "/test",
            data=json.dumps({"name": "integration test", "value": 42}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "success"

    def test_multiple_requests(self, app, client):
        """Test multiple requests are logged correctly."""
        setup(level="INFO")
        RequestResponseLogger(app)

        response1 = client.get("/test")
        response2 = client.post("/test", data=json.dumps({"test": "data"}), content_type="application/json")
        response3 = client.get("/error")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 500

    def test_debug_level_includes_more_details(self, app, client):
        """Test that DEBUG level includes request and response bodies."""
        setup(level="DEBUG")

        with patch("simple_api.middleware.logger.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.side_effect = lambda level: level in [
                logging.DEBUG,
                logging.INFO,
            ]
            mock_get_logger.return_value = mock_logger

            RequestResponseLogger(app)

            response = client.post(
                "/test",
                data=json.dumps({"key": "value"}),
                content_type="application/json",
            )

            assert response.status_code == 200
            # At DEBUG level, should have debug logs for request/response details
            assert mock_logger.debug.call_count >= 1
