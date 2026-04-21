"""Parser for text files containing data."""

import difflib
import re
from pathlib import Path
from typing import Any, Iterable, Iterator, cast

import structlog
import yaml
from marko import Markdown
from marko.block import FencedCode, Heading, Paragraph
from marko.inline import RawText
from pydantic import ValidationError

from onyva.core.models import ToDo  # pragma: no cover

FIRST_TODO_HEADING_LEVEL = 2
"The heading level for the to-dos at the root."

HEADING_REGEX = re.compile(r"^(?P<id>[\w-]+)\s*:\s*(?P<title>.+)$")
"The regular expression used to extract the ID and title of the to-dos at the root level."

TAG_REGEX = re.compile(r"#([\w/-]+)")
"The regular expression used to extract tags from text."

log = structlog.get_logger()


def parse_file(file: Path) -> list[ToDo]:
    """Parse the markdown file and return a list of ToDo. The list keeps the order of the file."""
    return _parse_text(file.read_text())


def _parse_text(text: str) -> list[ToDo]:
    """Parse the markdown text and return a list of ToDo. The list keeps the order of the file."""
    document_iterator: Iterator[object] = iter(Markdown().parse(text).children)
    return list(_parse_todo(document_iterator))


def _parse_todo(document_iterator: Iterator[object]) -> Iterator[ToDo]:
    """Parse todos from the document iterator and yield them in file order.

    Handles nested todos by tracking the current todo and its level. Yields
    each root-level todo once its full subtree has been parsed.

    Args:
        document_iterator: An iterator over the top-level nodes of the Marko document.

    Yields:
        ToDo objects in file order.
    """

    def yield_todo_if_exists(todo: ToDo | None) -> Iterator[ToDo]:
        """Yield todo if todo exist."""
        if todo:
            yield todo

    current_todo: ToDo | None = None
    current_root_todo: ToDo | None = None
    while node := _get_next_node(document_iterator):
        match node:
            case Heading(level=heading_level) as heading if current_todo or heading_level == FIRST_TODO_HEADING_LEVEL:
                heading_todo_level = heading_level - FIRST_TODO_HEADING_LEVEL + 1
                todo_text: str = _get_text_from_element(heading)
                if heading_todo_level > (current_todo.level if current_todo else 1) + 1:
                    log.error("Missing one or more parents. To-do is ignored", todo=todo_text)
                    continue
                match = HEADING_REGEX.match(todo_text)
                if not match:
                    continue
                match_id = match.group("id")
                match_title = match.group("title")
                parent_todo = _get_parent_todo(current_todo, heading_todo_level)
                current_todo = ToDo.create(to_do_id=match_id, title=match_title, parent=parent_todo)
                if heading_todo_level == 1:
                    yield from yield_todo_if_exists(current_root_todo)
                    current_root_todo = current_todo
            case FencedCode() as fenced_code if current_todo:
                properties: dict[Any, Any] = _get_todo_properties(fenced_code)
                for key, value in properties.items():
                    if key in ToDo.PROPERTY_TYPES:
                        try:
                            setattr(current_todo, key, value)
                        except ValidationError as e:
                            log.error(
                                "Invalid property value",
                                property=key,
                                value=value,
                                todo=current_todo.to_do_id,
                                error=str(e),
                            )
                    else:
                        log.warning(
                            "Unknown property",
                            property=key,
                            todo=current_todo.to_do_id,
                            hint=_did_you_mean(key, ToDo.PROPERTY_TYPES),
                        )
            case Paragraph() as paragraph if current_todo:
                current_todo.tags.update(_get_tags_from_paragraph(paragraph))
            case _:
                pass
    yield from yield_todo_if_exists(current_root_todo)  # Yield the last pending todo if any


def _get_parent_todo(current_todo: ToDo | None, heading_todo_level: int) -> ToDo | None:
    """Find the parent todo for a new todo at the given level.

    Args:
        current_todo: The last todo that was parsed, or None if none yet.
        heading_todo_level: The todo level of the new heading (1 = root).

    Returns:
        The parent todo for the new todo, or None if it is a root-level todo.
    """
    if not current_todo:
        if heading_todo_level != 1:  # pragma: no cover
            raise RuntimeError("Logical error in managing to-do parent.")
        return None
    current_todo_level = current_todo.level
    if heading_todo_level == current_todo_level:
        return current_todo.parent
    elif heading_todo_level == current_todo_level + 1:
        return current_todo
    elif heading_todo_level < current_todo_level:
        for _ in range(current_todo_level - heading_todo_level):
            current_todo = current_todo.parent
            if current_todo is None:  # pragma: no cover
                raise RuntimeError("Current to-do level was not expected to be None.")
        return current_todo.parent
    else:  # pragma: no cover
        raise AssertionError("Logical error in managing to-do parent. heading_level is too big.")


def _get_next_node(document_iterator: Iterator[object]) -> Heading | FencedCode | Paragraph | None:
    """Returns the next useful node in the document iterator.

    Args:
        document_iterator: An iterator over the top-level nodes of the Marko document.

    Returns:
        The next node in the document iterator, or None if no matching node
        is found.
    """
    for obj in document_iterator:
        match obj:
            case Heading(level=level) as heading if level >= FIRST_TODO_HEADING_LEVEL:
                return heading
            case FencedCode(lang="yaml") as fenced_code:
                return fenced_code
            case Paragraph() as paragraph:
                return paragraph
            case _:
                pass
    return None


def _get_text_from_element(node: Heading | FencedCode | Paragraph) -> str:
    """Get the text from a Marko element or return an empty string if there is no text."""
    if node.children and isinstance(node.children[0], RawText):
        return node.children[0].children
    return ""


def _get_todo_properties(fenced_code: FencedCode) -> dict[Any, Any]:
    """Get the YAML properties defined by the embedded YAML code.

    Args:
        fenced_code: FencedCode parsed my Marko.

    Returns:
        The properties as a dictionary or return an empty dictionary if the yaml value if not a dictionary.
    """
    text = _get_text_from_element(fenced_code)
    if text:
        yaml_result: Any = yaml.safe_load(text)
        if isinstance(yaml_result, dict):
            return cast(dict[Any, Any], yaml_result)
        log.warning("The YAML was not defining to-do properties.", code=text)
    return {}


def _get_tags_from_paragraph(paragraph: Paragraph) -> set[str]:
    """Get the tags present in a paragraph or an empty set if none is present."""
    text = _get_text_from_element(paragraph)
    return set(TAG_REGEX.findall(text))


def _did_you_mean(key: str, valid_keys: Iterable[str]) -> str:
    """Find the closest match for an unknown key among valid keys.

    Args:
        key: The unknown key to find a match for.
        valid_keys: The collection of valid keys to search in.

    Returns:
        A suggestion string like " Did you mean 'foo'?" or an empty string
        if no close match is found.
    """
    matches = difflib.get_close_matches(key, valid_keys, n=1)
    return f" Did you mean '{matches[0]}'?" if matches else ""
