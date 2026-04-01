"""Pytest configuration for script tests with hash-based caching."""

import hashlib
import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "src" / "scripts"
CACHE_FILE = Path(__file__).parent / ".script_hashes.json"


def get_script_hash(script_name: str) -> str:
    """Compute hash of a script file."""
    script_path = SCRIPTS_DIR / f"{script_name}.py"
    if not script_path.exists():
        return ""
    content = script_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def load_hashes() -> dict[str, str]:
    """Load cached hashes from file."""
    if not CACHE_FILE.exists():
        return {}
    return dict(json.loads(CACHE_FILE.read_text()))


def save_hashes(hashes: dict[str, str]) -> None:
    """Save hashes to cache file."""
    CACHE_FILE.write_text(json.dumps(hashes, indent=2))


def script_changed(script_name: str) -> bool:
    """Check if a script has changed since last successful test."""
    cached = load_hashes()
    current = get_script_hash(script_name)
    return cached.get(script_name) != current


def mark_script_tested(script_name: str) -> None:
    """Mark a script as successfully tested by updating its hash."""
    cached = load_hashes()
    cached[script_name] = get_script_hash(script_name)
    save_hashes(cached)


@pytest.fixture
def skip_if_unchanged(request: pytest.FixtureRequest) -> None:
    """Skip test if the script hasn't changed since last successful run."""
    module = request.module  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    script_name: str | None = getattr(module, "SCRIPT_NAME", None)  # pyright: ignore[reportUnknownArgumentType]
    if script_name and not script_changed(script_name):
        pytest.skip(f"Script {script_name} unchanged since last test")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo[None],  # type: ignore[type-arg]
) -> Generator[None, Any, None]:
    """Update hash cache when script tests pass."""
    outcome = yield
    report: Any = outcome.get_result()  # pyright: ignore[reportUnknownMemberType]

    if report.when == "call" and report.passed:
        module = getattr(item, "module", None)
        script_name: str | None = getattr(module, "SCRIPT_NAME", None) if module else None
        if script_name:
            mark_script_tested(script_name)
