"""Build documentation using Sphinx.

Manages user and developer documentation with multi-language support.

Commands:
  docs user [--lang LANG]  Build user documentation (all languages or specific)
  docs user extract        Extract translatable strings
  docs user update         Update translation catalogs
  docs dev                 Build developer documentation
  docs publish             Build and prepare for GitHub Pages
"""

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = ROOT / "docs"
USER_DOCS = DOCS_DIR / "user"
DEV_DOCS = DOCS_DIR / "dev"
SUPPORTED_LOCALES = ["fr", "en", "es"]
DEFAULT_LOCALE = "en"


def build_user_docs(lang: str | None = None) -> bool:
    """Build user documentation for one or all languages."""
    languages = [lang] if lang else SUPPORTED_LOCALES
    success = True

    for locale in languages:
        print(f"Building user docs for {locale}...")
        build_dir = USER_DOCS / "_build" / "html" / locale

        result = subprocess.run(
            [
                "sphinx-build",
                "-b",
                "html",
                "-D",
                f"language={locale}",
                str(USER_DOCS / "source"),
                str(build_dir),
            ],
            check=False,
        )
        if result.returncode != 0:
            print(f"  Failed to build {locale}")
            success = False
        else:
            print(f"  Built in {build_dir}")

    return success


def extract_user_strings() -> bool:
    """Extract translatable strings from user documentation."""
    pot_dir = USER_DOCS / "_build" / "gettext"

    result = subprocess.run(
        [
            "sphinx-build",
            "-b",
            "gettext",
            str(USER_DOCS / "source"),
            str(pot_dir),
        ],
        check=False,
    )
    if result.returncode != 0:
        return False

    print(f"Extracted strings to {pot_dir}")
    return True


def update_user_catalogs() -> bool:
    """Update translation catalogs for user documentation."""
    pot_dir = USER_DOCS / "_build" / "gettext"

    if not pot_dir.exists():
        print("No gettext output found. Run 'docs user extract' first.")
        return False

    for locale in SUPPORTED_LOCALES:
        result = subprocess.run(
            [
                "sphinx-intl",
                "update",
                "-p",
                str(pot_dir),
                "-l",
                locale,
                "-d",
                str(USER_DOCS / "locales"),
            ],
            check=False,
        )
        if result.returncode != 0:
            print(f"Failed to update {locale} catalog")
            return False
        print(f"Updated {locale} catalog")

    return True


def build_dev_docs() -> bool:
    """Build developer documentation."""
    build_dir = DEV_DOCS / "_build" / "html"

    result = subprocess.run(
        [
            "sphinx-build",
            "-b",
            "html",
            str(DEV_DOCS / "source"),
            str(build_dir),
        ],
        check=False,
    )
    if result.returncode != 0:
        return False

    print(f"Built developer docs in {build_dir}")
    return True


def publish_docs() -> bool:
    """Build all user docs and prepare for GitHub Pages."""
    publish_dir = DOCS_DIR / "_publish"

    if publish_dir.exists():
        shutil.rmtree(publish_dir)
    publish_dir.mkdir()

    if not build_user_docs():
        return False

    # Copy built docs to publish directory
    for locale in SUPPORTED_LOCALES:
        src = USER_DOCS / "_build" / "html" / locale
        dst = publish_dir / locale
        if src.exists():
            shutil.copytree(src, dst)

    # Create index.html with language selector
    index_html = publish_dir / "index.html"
    index_html.write_text(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Onyva Documentation</title>
    <meta http-equiv="refresh" content="0; url={DEFAULT_LOCALE}/">
    <style>
        body {{ font-family: sans-serif; text-align: center; padding: 50px; }}
        a {{ display: inline-block; margin: 10px; padding: 10px 20px;
             background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        a:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <h1>Onyva Documentation</h1>
    <p>Select your language / Choisissez votre langue / Seleccione su idioma:</p>
    <a href="fr/">Français</a>
    <a href="en/">English</a>
    <a href="es/">Español</a>
</body>
</html>
""")

    print(f"Documentation ready for publishing in {publish_dir}")
    print("To publish to GitHub Pages, push this directory to the gh-pages branch.")
    return True


def main() -> None:
    """Run documentation commands."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # user command
    user_parser = subparsers.add_parser("user", help="Build user documentation")
    user_parser.add_argument("action", nargs="?", default="build", choices=["build", "extract", "update"])
    user_parser.add_argument("--lang", choices=SUPPORTED_LOCALES, help="Build specific language only")

    # dev command
    subparsers.add_parser("dev", help="Build developer documentation")

    # publish command
    subparsers.add_parser("publish", help="Build and prepare for GitHub Pages")

    args = parser.parse_args()

    success = False
    if args.command == "user":
        if args.action == "extract":
            success = extract_user_strings()
        elif args.action == "update":
            success = update_user_catalogs()
        else:
            success = build_user_docs(args.lang)
    elif args.command == "dev":
        success = build_dev_docs()
    elif args.command == "publish":
        success = publish_docs()

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
