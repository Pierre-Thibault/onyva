"""Sphinx configuration for user documentation."""

project = "Onyva"
copyright = "2026, Onyva Team"
author = "Onyva Team"

extensions = [
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = ["_static"]

# Internationalization
language = "en"
locale_dirs = ["../locales/"]
gettext_compact = False
gettext_uuid = True
