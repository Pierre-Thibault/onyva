#!/usr/bin/env python3
"""Run code quality checks.

Runs the following checks in sequence:
- Ruff linting
- Ruff formatting verification
- Basedpyright type checking
- Pytest unit tests with 100% coverage requirement
- Translation completeness (if locales/ exists)

Exit code is non-zero if any check fails.
"""

import argparse
import subprocess
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po

CHECKS = [
    (["ruff", "check", "."], "Ruff (lint)"),
    (["ruff", "format", "--check", "."], "Ruff (format)"),
    (["basedpyright", "."], "Basedpyright"),
    (["pytest", "--cov", "--cov-report=term-missing"], "Tests + Coverage"),
]

LOCALES_DIR = Path("locales")
POT_FILE = LOCALES_DIR / "messages.pot"
SUPPORTED_LOCALES = ["fr", "en", "es"]


def _msg_id_to_str(msg_id: str | tuple[str, ...] | list[str]) -> str:
    """Convert a message ID to a string for display and comparison."""
    if isinstance(msg_id, str):
        return msg_id
    return str(msg_id[0]) if msg_id else ""


def check_translations() -> bool:
    """Check for missing or unused translations.

    Returns True if all translations are complete, False otherwise.
    """
    if not POT_FILE.exists():
        print("No messages.pot found, skipping translation check")
        return True

    with open(POT_FILE, "rb") as f:
        template: Catalog = read_po(f)

    template_ids = {_msg_id_to_str(msg.id) for msg in template if msg.id}

    all_ok = True

    for locale in SUPPORTED_LOCALES:
        po_file = LOCALES_DIR / locale / "LC_MESSAGES" / "messages.po"
        if not po_file.exists():
            print(f"  {locale}: missing catalog file")
            all_ok = False
            continue

        with open(po_file, "rb") as f:
            catalog: Catalog = read_po(f)

        catalog_ids = {_msg_id_to_str(msg.id) for msg in catalog if msg.id}
        translated_ids = {_msg_id_to_str(msg.id) for msg in catalog if msg.id and msg.string}

        missing = template_ids - translated_ids
        unused = catalog_ids - template_ids

        if missing or unused:
            all_ok = False
            print(f"  {locale}:")
            if missing:
                print(f"    Missing translations: {len(missing)}")
                for msg_id in sorted(missing)[:5]:
                    preview = msg_id[:50] + "..." if len(msg_id) > 50 else msg_id
                    print(f"      - {preview}")
                if len(missing) > 5:
                    print(f"      ... and {len(missing) - 5} more")
            if unused:
                print(f"    Unused translations: {len(unused)}")
                for msg_id in sorted(unused)[:5]:
                    preview = msg_id[:50] + "..." if len(msg_id) > 50 else msg_id
                    print(f"      - {preview}")
                if len(unused) > 5:
                    print(f"      ... and {len(unused) - 5} more")
        else:
            print(f"  {locale}: OK")

    return all_ok


def main() -> None:
    """Run all code quality checks."""
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()

    failed: list[str] = []
    for cmd, name in CHECKS:
        print(f"=== {name} ===")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            failed.append(name)
        print()

    if LOCALES_DIR.exists():
        print("=== Translations ===")
        if not check_translations():
            failed.append("Translations")
        print()

    if failed:
        raise SystemExit(f"Checks failed: {', '.join(failed)}")
    print("All checks passed.")


if __name__ == "__main__":
    main()
