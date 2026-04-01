"""Tests for the check script."""

import subprocess

SCRIPT_NAME = "check"


def test_check_help(skip_if_unchanged: None) -> None:
    """Test that check --help works."""
    result = subprocess.run(
        ["uv", "run", "check", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Run code quality checks" in result.stdout


def test_check_help_short(skip_if_unchanged: None) -> None:
    """Test that check -h works."""
    result = subprocess.run(
        ["uv", "run", "check", "-h"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Ruff linting" in result.stdout
