"""Testing the markdown parser."""

from pathlib import Path
from typing import Any

import marko
import yaml

from onyva.core.models import ToDo
from onyva.core.parser import Parser


def _todo_to_dict(todo: ToDo) -> dict[str, Any]:
    """Convert a ToDo to a dictionary suitable for YAML comparison."""
    d: dict[str, Any] = todo.model_dump()
    return {
        "todo_id": d["todo_id"],
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
        "parent": todo.parent.todo_id if todo.parent else None,
        "children": [_todo_to_dict(child) for child in todo.children],
    }


_FIXTURES = Path(__file__).parent / "fixtures" / "parser"


def test_parse_text() -> None:
    parser = Parser()
    for markdown_file in _FIXTURES.glob("*.md"):
        result = parser.parse_file(markdown_file)

        actual_result = [_todo_to_dict(todo) for todo in result.todos]
        actual_yaml: str = yaml.dump(actual_result, sort_keys=False, allow_unicode=True)
        expected_yaml: str = (markdown_file.parent / (markdown_file.stem + ".yaml")).read_text()

        assert actual_yaml == expected_yaml, f"Mismatch for {markdown_file.name}"


def test_parse_issues_unknown_property() -> None:
    result = Parser().parse_file(_FIXTURES / "with_unknown_property.md")
    assert len(result.issues) == 2
    assert all(issue.level == "warning" for issue in result.issues)
    assert all(issue.message == "Unknown property" for issue in result.issues)
    assert {issue.details["property"] for issue in result.issues} == {"tittle", "xyz123abc"}


def test_parse_issues_invalid_property() -> None:
    result = Parser().parse_file(_FIXTURES / "with_invalid_property.md")
    assert len(result.issues) == 1
    assert result.issues[0].level == "error"
    assert result.issues[0].message == "Invalid property value"
    assert result.issues[0].details["property"] == "progress"


def test_parse_issues_duplicate_id() -> None:
    result = Parser().parse_file(_FIXTURES / "with_duplicate_id.md")
    assert len(result.issues) == 1
    assert result.issues[0].level == "error"
    assert result.issues[0].message == 'ID "todo-a" previously used. To-do will be ignored.'
    assert result.issues[0].details["todo_title"] == "Duplicate Todo (ignored)"


def test_parse_issues_missing_parent() -> None:
    result = Parser().parse_file(_FIXTURES / "with_missing_parent.md")
    assert len(result.issues) == 1
    assert result.issues[0].level == "error"
    assert result.issues[0].message == "Missing one or more parents. To-do is ignored"
    assert result.issues[0].details["todo"] == "too-deep : Too Deep (skipped)"


_FIXTURES_WITH_ISSUES = {"with_unknown_property", "with_invalid_property", "with_duplicate_id", "with_missing_parent"}


def test_parse_no_issues() -> None:
    parser = Parser()
    for markdown_file in _FIXTURES.glob("*.md"):
        if markdown_file.stem not in _FIXTURES_WITH_ISSUES:
            result = parser.parse_file(markdown_file)
            assert result.issues == [], f"Unexpected issues in {markdown_file.name}"


def test_get_text_from_element_no_raw_text() -> None:
    doc = marko.parse("**bold**\n")
    assert Parser._get_text_from_element(doc.children[0]) == ""  # type: ignore[arg-type]  # pyright: ignore[reportPrivateUsage]


def test_get_todo_properties_non_dict_yaml() -> None:
    parser = Parser()
    doc = marko.parse("```yaml\n- item1\n- item2\n```\n")
    assert parser._get_todo_properties(doc.children[0]) == {}  # type: ignore[arg-type]  # pyright: ignore[reportPrivateUsage]
    assert len(parser._issues) == 1  # pyright: ignore[reportPrivateUsage]
    assert parser._issues[0].level == "warning"  # pyright: ignore[reportPrivateUsage]
    assert parser._issues[0].message == "The YAML was not defining to-do properties."  # pyright: ignore[reportPrivateUsage]


def test_get_tags_from_paragraph_no_tags() -> None:
    doc = marko.parse("No hashtags here.\n")
    assert Parser._get_tags_from_paragraph(doc.children[0]) == set()  # type: ignore[arg-type]  # pyright: ignore[reportPrivateUsage]


def test_did_you_mean_no_close_match() -> None:
    assert Parser._did_you_mean("xyz123abc", ["title", "status", "priority"]) == ""  # pyright: ignore[reportPrivateUsage]


def test_get_next_node_skips_non_matching_nodes() -> None:
    parser = Parser()
    doc = marko.parse("# H1 heading\n")  # level 1 is below FIRST_TODO_HEADING_LEVEL
    parser._document_iterator = iter(doc.children)  # pyright: ignore[reportPrivateUsage]
    assert parser._get_next_node() is None  # pyright: ignore[reportPrivateUsage]


def test_get_todo_properties_empty_fenced_code() -> None:
    parser = Parser()
    doc = marko.parse("```yaml\n```\n")
    assert parser._get_todo_properties(doc.children[0]) == {}  # type: ignore[arg-type]  # pyright: ignore[reportPrivateUsage]
    assert parser._issues == []  # pyright: ignore[reportPrivateUsage]
