"""Logging configuration using structlog."""

import logging
from typing import cast

import structlog

from onyva.core.config import settings


def configure_logging() -> None:
    """Configure structlog based on settings."""
    log_format = cast(str, settings.LOG_FORMAT)
    log_level = cast(str, settings.LOG_LEVEL)

    if log_format == "json":
        renderer: structlog.typing.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    level = getattr(logging, log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )
