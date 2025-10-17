"""
Logger utilities for the Simple API application.

This module provides backwards compatibility by re-exporting from the middleware package.
The logger functionality has been moved to simple_api.middleware.logger.
"""

from simple_api.middleware.logger import get_logger, setup

__all__ = ["setup", "get_logger"]
