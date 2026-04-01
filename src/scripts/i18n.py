"""Internationalization commands using Babel.

Manage translation catalogs for the application.
Supported locales: fr, en, es.

Typical workflow:
  i18n extract    # Extract strings from source code
  i18n init-all   # Create catalogs for all locales
  # ... translate the .po files ...
  i18n compile    # Compile to .mo for production
"""

import argparse
import subprocess
from pathlib import Path

LOCALES_DIR = Path("locales")
POT_FILE = LOCALES_DIR / "messages.pot"
SUPPORTED_LOCALES = ["fr", "en", "es"]


def extract(_args: argparse.Namespace) -> None:
    """Extract translatable strings from source code."""
    LOCALES_DIR.mkdir(exist_ok=True)
    subprocess.run(
        ["pybabel", "extract", "-o", str(POT_FILE), "src/"],
        check=True,
    )
    print(f"Extracted strings to {POT_FILE}")


def init(locale: str) -> None:
    """Initialize a new locale catalog."""
    if not POT_FILE.exists():
        print("No messages.pot found. Run 'i18n extract' first.")
        raise SystemExit(1)
    subprocess.run(
        ["pybabel", "init", "-i", str(POT_FILE), "-d", str(LOCALES_DIR), "-l", locale],
        check=True,
    )
    print(f"Initialized catalog for {locale}")


def update(_args: argparse.Namespace) -> None:
    """Update all locale catalogs with new strings."""
    if not POT_FILE.exists():
        print("No messages.pot found. Run 'i18n extract' first.")
        raise SystemExit(1)
    subprocess.run(
        ["pybabel", "update", "-i", str(POT_FILE), "-d", str(LOCALES_DIR)],
        check=True,
    )
    print("Updated all catalogs")


def compile_catalogs(_args: argparse.Namespace) -> None:
    """Compile all locale catalogs to .mo files."""
    subprocess.run(
        ["pybabel", "compile", "-d", str(LOCALES_DIR)],
        check=True,
    )
    print("Compiled all catalogs")


def init_all(_args: argparse.Namespace) -> None:
    """Initialize catalogs for all supported locales (fr, en, es)."""
    for locale in SUPPORTED_LOCALES:
        locale_dir = LOCALES_DIR / locale
        if not locale_dir.exists():
            init(locale)
        else:
            print(f"Catalog for {locale} already exists, skipping")


def main() -> None:
    """Run i18n commands."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("extract", help=extract.__doc__)
    sub.set_defaults(func=extract)

    sub = subparsers.add_parser("init-all", help=init_all.__doc__)
    sub.set_defaults(func=init_all)

    sub = subparsers.add_parser("update", help=update.__doc__)
    sub.set_defaults(func=update)

    sub = subparsers.add_parser("compile", help=compile_catalogs.__doc__)
    sub.set_defaults(func=compile_catalogs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
