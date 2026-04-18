"""
Testing the markdown parser.
"""

from pathlib import Path

import yaml

from onyva.core.models import ToDo
from onyva.core.parser import ParsingError, ParsingWarning, parse_file


def test_parse_text() -> None:
    for markdown_file in (Path(__file__).parent / "fixtures" / "parser").glob("*.md"):
        # Parse each markdown file:
        todo_list: list[ToDo]
        warnings_and_errors: list[ParsingWarning | ParsingError]
        todo_list, warnings_and_errors = parse_file(markdown_file)

        assert not warnings_and_errors

        # Prepare the todo list for the comparison with expected yaml file:
        actual_result: list[dict[str, object]] = []
        for todo in todo_list:
            # Transform the todo in a dict
            todo_dict: dict[str, object] = todo.model_dump()
            # Fix some keys:
            todo_dict["parent"] = todo.parent.to_do_id if todo.parent else None
            todo_dict["tags"] = sorted(todo.tags)
            actual_result.append(todo_dict)

        # Get the actual yaml from the parser:
        actual_yaml: str = yaml.dump(actual_result)

        # Get the expected yaml from our file:
        expected_yaml: str = (markdown_file.parent / (markdown_file.stem + ".yaml")).read_text()

        # Compare to see if it matches:
        assert actual_yaml == expected_yaml
