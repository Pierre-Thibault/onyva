"""Parser for text files containing data."""

import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Iterator, Literal, Sequence, cast, final

import structlog
import yaml
from marko import Markdown
from marko.block import FencedCode, Heading, Paragraph
from marko.inline import RawText
from pydantic import ValidationError

from onyva.core.models import ToDo

FIRST_TODO_HEADING_LEVEL = 2
"The heading level for the to-dos at the root."

HEADING_REGEX = re.compile(r"^(?P<id>[\w-]+)\s*:\s*(?P<title>.+)$")
"The regular expression used to extract the ID and title of the to-dos at the root level."

TAG_REGEX = re.compile(r"#([\w/-]+)")
"The regular expression used to extract tags from text."

log = structlog.get_logger()


type ParseIssueLevel = Literal["warning", "error"]
"A parsing issue level. Either a warning or an error."


@dataclass(frozen=True)
class ParseIssue:
    """A parsing issue definition."""

    level: ParseIssueLevel
    message: str
    details: MappingProxyType[str, Any]


@dataclass(frozen=True)
class ParseResult:
    """The result of parse_file."""

    todos: Sequence[ToDo]
    "The root to-dos parsed in the file."
    issues: Sequence[ParseIssue]
    "The issues while parsing. Errors and warnings."
    todo_ids: frozenset[str]
    "The set of all the ids used by to-dos."


@final
class Parser:
    """To-do parser from markdown files. Can't be used concurrently."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._document_iterator: Iterator[object] = iter([])
        self._current_todo: ToDo | None = None
        self._issues: list[ParseIssue] = []
        self._todo_ids: set[str] = set()

    def parse_file(self, file: Path) -> ParseResult:
        """Parse the markdown file and return a ParseResult. The list keeps the order of the file."""
        return self._parse_text(file.read_text())

    def _parse_text(self, text: str) -> ParseResult:
        """Parse the markdown text and return a ParseResult. The list keeps the order of the file."""
        self._document_iterator = iter(Markdown().parse(text).children)
        return ParseResult(todos=list(self._parse_todo()), issues=self._issues, todo_ids=frozenset(self._todo_ids))

    def _parse_todo(self) -> Iterator[ToDo]:
        """Parse todos from the document iterator and yield them in file order.

        Handles nested todos by tracking the current todo and its level. Yields
        each root-level todo once its full subtree has been parsed.

        Yields:
            ToDo objects in file order with a list of parsing issues.
        """
        self._current_todo = None
        current_root_todo: ToDo | None = None
        self._issues = []
        self._todo_ids = set()
        while node := self._get_next_node():
            match node:
                case Heading(level=heading_level) as heading if (
                    self._current_todo or heading_level == FIRST_TODO_HEADING_LEVEL
                ):
                    heading_todo_level = heading_level - FIRST_TODO_HEADING_LEVEL + 1
                    todo_text: str = Parser._get_text_from_element(heading)
                    if heading_todo_level > (self._current_todo.level if self._current_todo else 1) + 1:
                        self._add_parsing_issue(
                            "Missing one or more parents. To-do is ignored", level="error", todo=todo_text
                        )
                        continue
                    match = HEADING_REGEX.match(todo_text)
                    if match:
                        todo_id = match.group("id")
                        todo_title = match.group("title")
                        if todo_id in self._todo_ids:
                            self._add_parsing_issue(
                                f'ID "{todo_id}" previously used. To-do will be ignored.',
                                level="error",
                                todo_title=todo_title,
                            )
                            continue
                        self._todo_ids.add(todo_id)
                    else:
                        if heading_todo_level == 1:
                            self._current_todo = None
                            continue
                        todo_id = None
                        todo_title = todo_text
                    parent_todo = self._get_parent_todo(heading_todo_level)
                    self._current_todo = ToDo.create(todo_id=todo_id, title=todo_title, parent=parent_todo)
                    if heading_todo_level == 1:
                        if current_root_todo:
                            yield current_root_todo
                        current_root_todo = self._current_todo
                case FencedCode() as fenced_code if self._current_todo:
                    properties: dict[Any, Any] = self._get_todo_properties(fenced_code)
                    for key, value in properties.items():
                        if key in ToDo.PROPERTY_TYPES:
                            try:
                                setattr(self._current_todo, key, value)
                            except ValidationError as e:
                                self._add_parsing_issue(
                                    "Invalid property value",
                                    level="error",
                                    property=key,
                                    value=value,
                                    todo=self._current_todo.todo_id,
                                    error=str(e),
                                )
                        else:
                            self._add_parsing_issue(
                                "Unknown property",
                                level="warning",
                                property=key,
                                todo=self._current_todo.todo_id,
                                hint=Parser._did_you_mean(key, ToDo.PROPERTY_TYPES),
                            )
                case Paragraph() as paragraph if self._current_todo:
                    self._current_todo.tags.update(Parser._get_tags_from_paragraph(paragraph))
                case _:
                    pass
        if current_root_todo:
            yield current_root_todo  # Yield the last pending todo if any

    def _get_parent_todo(self, heading_todo_level: int) -> ToDo | None:
        """Find the parent todo for a new todo at the given level.

        Args:
            heading_todo_level: The todo level of the new heading (1 = root).

        Returns:
            The parent todo for the new todo, or None if it is a root-level todo.
        """
        current_todo = self._current_todo
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

    def _get_next_node(self) -> Heading | FencedCode | Paragraph | None:
        """Returns the next useful node in the document iterator.

        Returns:
            The next node in the document iterator, or None if no matching node
            is found.
        """
        for obj in self._document_iterator:
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

    def _get_todo_properties(self, fenced_code: FencedCode) -> dict[Any, Any]:
        """Get the YAML properties defined by the embedded YAML code.

        Args:
            fenced_code: FencedCode parsed by Marko.

        Returns:
            The properties as a dictionary or return an empty dictionary if the yaml value if not a dictionary.
        """
        text = Parser._get_text_from_element(fenced_code)
        if text:
            yaml_result: Any = yaml.safe_load(text)
            if isinstance(yaml_result, dict):
                return cast(dict[Any, Any], yaml_result)
            self._add_parsing_issue("The YAML was not defining to-do properties.", level="warning", code=text)
        return {}

    def _add_parsing_issue(self, message: str, /, level: ParseIssueLevel, **details: Any) -> None:
        """Log the issue, create a ParseIssue and add it to issues."""
        if level == "warning":
            log_function = log.warning
        elif level == "error":
            log_function = log.error
        else:
            raise RuntimeError("Unexpected issue level.")  # pragma: no cover
        log_function(message, **details)
        self._issues.append(ParseIssue(level=level, message=message, details=MappingProxyType(details)))

    @staticmethod
    def _get_text_from_element(node: Heading | FencedCode | Paragraph) -> str:
        """Get the text from a Marko element or return an empty string if there is no text."""
        if node.children and isinstance(node.children[0], RawText):
            return node.children[0].children
        return ""

    @staticmethod
    def _get_tags_from_paragraph(paragraph: Paragraph) -> set[str]:
        """Get the tags present in a paragraph or an empty set if none is present."""
        text = Parser._get_text_from_element(paragraph)
        return set(TAG_REGEX.findall(text))

    @staticmethod
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
