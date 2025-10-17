import json
import logging
import sys
import time
from functools import wraps

from flask import g, request


def setup(level="INFO"):
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    logger = logging.getLogger("simple_api")
    logger.setLevel(level)

    # Only add handlers if none exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Don't propagate to root logger to avoid duplicate logs
    logger.propagate = False

    # Disable Werkzeug's default request logging to prevent duplicate logs
    # since we have our own RequestResponseLogger middleware
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.ERROR)  # Only show errors, not access logs

    return logger


def get_logger(name: str):
    """Get a logger with the given name under the simple_api namespace."""
    return logging.getLogger(f"simple_api.{name}")


class RequestResponseLogger:
    """Middleware to log requests and responses based on log level."""

    def __init__(self, app=None):
        self.app = app
        self.logger = get_logger("request_response")
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the Flask application for logging."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        """Log request and start timing."""
        g.start_time = time.time()

        # Always capture basic info
        g.request_info = {
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
        }

        # At DEBUG level, capture additional request details
        if self.logger.isEnabledFor(logging.DEBUG):
            g.request_info.update(
                {
                    "headers": dict(request.headers),
                    "query_params": dict(request.args),
                }
            )

            # Safely get request body
            if request.is_json:
                try:
                    g.request_info["body"] = request.get_json()
                except Exception:
                    g.request_info["body"] = None
            elif request.form:
                g.request_info["body"] = dict(request.form)
            else:
                # For other content types, get raw data (be careful with large bodies)
                content_length = request.content_length or 0
                if content_length > 0 and content_length < 10000:  # Limit to 10KB
                    g.request_info["body"] = request.get_data(as_text=True)

            self.logger.debug(
                f"Request: {request.method} {request.path} | "
                f"Headers: {json.dumps(g.request_info.get('headers', {}), default=str)} | "
                f"Body: {json.dumps(g.request_info.get('body'), default=str)[:500]}"  # Limit body log length
            )

    def after_request(self, response):
        """Log response based on log level."""
        if hasattr(g, "start_time"):
            duration = round((time.time() - g.start_time) * 1000, 2)  # Convert to ms
        else:
            duration = 0

        status_code = response.status_code

        # INFO level: Log basic request info with response status and duration
        if self.logger.isEnabledFor(logging.INFO):
            log_message = (
                f"{g.request_info['method']} {g.request_info['path']} | "
                f"Status: {status_code} | "
                f"Duration: {duration}ms | "
                f"IP: {g.request_info['remote_addr']}"
            )

            # Use appropriate log level based on status code
            if status_code >= 500:
                self.logger.error(log_message)
            elif status_code >= 400:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)

        # DEBUG level: Also log response details
        if self.logger.isEnabledFor(logging.DEBUG):
            response_data = None
            has_data = False

            # Try to get response data if it's JSON
            if response.is_json:
                try:
                    response_data = response.get_json()
                    has_data = True
                except Exception:
                    pass

            # For non-JSON responses, get a preview of the data
            if not has_data and response.content_length:
                if response.content_length < 1000:  # Only for small responses
                    try:
                        response_data = response.get_data(as_text=True)[:500]  # Limit length
                        has_data = True
                    except Exception:
                        response_data = "<binary data>"
                        has_data = True

            self.logger.debug(
                f"Response: Status {status_code} | "
                f"Headers: {dict(response.headers)} | "
                f"Body: {json.dumps(response_data, default=str)[:500] if has_data else 'None'}"
            )

        return response


def log_route(func):
    """Decorator to log individual route execution (optional alternative to middleware)."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(f"route.{func.__name__}")
        start_time = time.time()

        # Log at INFO level
        logger.info(f"Executing {func.__name__} | Method: {request.method} | Path: {request.path}")

        # Log request details at DEBUG level
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request args: {dict(request.args)}")
            if request.is_json:
                logger.debug(f"Request JSON: {request.get_json()}")

        try:
            result = func(*args, **kwargs)
            duration = round((time.time() - start_time) * 1000, 2)
            logger.info(f"Completed {func.__name__} in {duration}ms")
            return result
        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Error in {func.__name__} after {duration}ms: {str(e)}", exc_info=True)
            raise

    return wrapper
