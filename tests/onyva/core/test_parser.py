"""Testing the markdown parser."""

from pathlib import Path
from typing import Any

import marko
import yaml

from onyva.core.models import ToDo
from onyva.core.parser import (
    _did_you_mean,  # pyright: ignore[reportPrivateUsage]
    _get_next_node,  # pyright: ignore[reportPrivateUsage]
    _get_tags_from_paragraph,  # pyright: ignore[reportPrivateUsage]
    _get_text_from_element,  # pyright: ignore[reportPrivateUsage]
    _get_todo_properties,  # pyright: ignore[reportPrivateUsage]
    parse_file,
)


def _todo_to_dict(todo: ToDo) -> dict[str, Any]:
    """Convert a ToDo to a dictionary suitable for YAML comparison."""
    d: dict[str, Any] = todo.model_dump()
    return {
        "to_do_id": d["to_do_id"],
        "title": d["title"],
        "status": str(todo.status) if todo.status else None,
        "priority": str(todo.priority),
        "todo_type": str(d["todo_type"]),
        "tracking": {"mode": str(d["tracking"]["mode"]), "target": d["tracking"]["target"]},
        "progress": d["progress"],
        "start": d["start"],
        "end": d["end"],
        "depends_on": d["depends_on"],
        "before": d["before"],
        "smart": d["smart"],
        "created": d["created"],
        "tags": sorted(todo.tags),
        "parent": todo.parent.to_do_id if todo.parent else None,
        "children": [_todo_to_dict(child) for child in todo.children],
    }


def test_parse_text() -> None:
    for markdown_file in (Path(__file__).parent / "fixtures" / "parser").glob("*.md"):
        # Parse each markdown file:
        todo_list: list[ToDo] = parse_file(markdown_file)

        # Prepare the todo list for the comparison with expected yaml file:
        actual_result = [_todo_to_dict(todo) for todo in todo_list]

        # Get the actual yaml from the parser:
        actual_yaml: str = yaml.dump(actual_result, sort_keys=False, allow_unicode=True)

        # Get the expected yaml from our file:
        expected_yaml: str = (markdown_file.parent / (markdown_file.stem + ".yaml")).read_text()

        # Compare to see if it matches:
        assert actual_yaml == expected_yaml, f"Mismatch for {markdown_file.name}"


def test_get_text_from_element_no_raw_text() -> None:
    doc = marko.parse("**bold**\n")
    assert _get_text_from_element(doc.children[0]) == ""  # type: ignore[arg-type]


def test_get_todo_properties_non_dict_yaml() -> None:
    doc = marko.parse("```yaml\n- item1\n- item2\n```\n")
    assert _get_todo_properties(doc.children[0]) == {}  # type: ignore[arg-type]


def test_get_tags_from_paragraph_no_tags() -> None:
    doc = marko.parse("No hashtags here.\n")
    assert _get_tags_from_paragraph(doc.children[0]) == set()  # type: ignore[arg-type]


def test_did_you_mean_no_close_match() -> None:
    assert _did_you_mean("xyz123abc", ["title", "status", "priority"]) == ""


def test_get_next_node_skips_non_matching_nodes() -> None:
    doc = marko.parse("# H1 heading\n")  # level 1 is below FIRST_TODO_HEADING_LEVEL
    assert _get_next_node(iter(doc.children)) is None


def test_get_todo_properties_empty_fenced_code() -> None:
    doc = marko.parse("```yaml\n```\n")
    assert _get_todo_properties(doc.children[0]) == {}  # type: ignore[arg-type]
