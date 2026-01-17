"""
Logging Configuration
Centralized logging setup for APIC.
"""

import logging
import sys
from typing import Optional

from config.settings import settings


def setup_logging(
    level: Optional[str] = None,
    log_format: Optional[str] = None,
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format
    """
    # Determine log level
    if level is None:
        level = "DEBUG" if settings.DEBUG else "INFO"

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Default format
    if log_format is None:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    # APIC loggers
    logging.getLogger("apic").setLevel(log_level)
    logging.getLogger("apic.agents").setLevel(log_level)
    logging.getLogger("apic.services").setLevel(log_level)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {level}")
