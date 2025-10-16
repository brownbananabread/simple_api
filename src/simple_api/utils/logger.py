import logging
import sys


def setup_logger(level="INFO"):
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    logger = logging.getLogger("simple_api")
    logger.setLevel(level)

    # Only add handlers if none exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Don't propagate to root logger to avoid duplicate logs
    logger.propagate = False

    return logger
