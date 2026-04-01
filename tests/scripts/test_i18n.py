"""Tests for the i18n script."""

import subprocess

SCRIPT_NAME = "i18n"


def test_i18n_help(skip_if_unchanged: None) -> None:
    """Test that i18n --help works."""
    result = subprocess.run(
        ["uv", "run", "i18n", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Internationalization commands using Babel" in result.stdout


def test_i18n_help_short(skip_if_unchanged: None) -> None:
    """Test that i18n -h works."""
    result = subprocess.run(
        ["uv", "run", "i18n", "-h"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "extract" in result.stdout
    assert "init-all" in result.stdout
    assert "update" in result.stdout
    assert "compile" in result.stdout


def test_i18n_invalid_command(skip_if_unchanged: None) -> None:
    """Test that invalid command shows error."""
    result = subprocess.run(
        ["uv", "run", "i18n", "invalid"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_i18n_subcommand_help(skip_if_unchanged: None) -> None:
    """Test that subcommand --help works."""
    result = subprocess.run(
        ["uv", "run", "i18n", "extract", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
