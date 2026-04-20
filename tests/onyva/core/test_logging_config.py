"""Tests for logging configuration."""

import pytest
from unittest.mock import patch

from onyva.core.logging_config import configure_logging


def test_configure_logging_console() -> None:
    """Test console logging configuration."""
    with patch("onyva.core.logging_config.settings") as mock_settings:
        mock_settings.LOG_FORMAT = "console"
        mock_settings.LOG_LEVEL = "DEBUG"
        configure_logging()


def test_configure_logging_json() -> None:
    """Test JSON logging configuration."""
    with patch("onyva.core.logging_config.settings") as mock_settings:
        mock_settings.LOG_FORMAT = "json"
        mock_settings.LOG_LEVEL = "INFO"
        configure_logging()


def test_configure_logging_invalid_level() -> None:
    """Test that an invalid LOG_LEVEL raises ValueError."""
    with patch("onyva.core.logging_config.settings") as mock_settings:
        mock_settings.LOG_FORMAT = "console"
        mock_settings.LOG_LEVEL = "VERBOS"
        with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
            configure_logging()
