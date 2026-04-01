"""Tests for the docs script."""

import subprocess

SCRIPT_NAME = "docs"


def test_docs_help(skip_if_unchanged: None) -> None:
    """Test that docs --help works."""
    result = subprocess.run(
        ["uv", "run", "docs", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Build documentation using Sphinx" in result.stdout


def test_docs_help_short(skip_if_unchanged: None) -> None:
    """Test that docs -h works."""
    result = subprocess.run(
        ["uv", "run", "docs", "-h"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "docs/_build/html" in result.stdout
