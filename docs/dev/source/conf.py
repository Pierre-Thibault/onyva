"""Sphinx configuration for developer documentation."""

import sys
from pathlib import Path

# Add source to path for autodoc
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

project = "Onyva (Dev)"
copyright = "2026, Onyva Team"
author = "Onyva Team"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = ["_static"]

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
