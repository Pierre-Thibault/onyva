"""Data models for the onyva application."""

from collections.abc import Iterable
from datetime import date, datetime
from enum import StrEnum
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, PrivateAttr

type ProgressUnit = str
"""The progress unit. For example: km, %, pages"""

type Tag = str
"""A tag. For example: persnnal, spanish"""

type ToDoId = str
"""To-do ID. Defined by the user to be unique"""


class Priority(StrEnum):
    """To-do priorities."""

    OPTIONAL = "optional"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CAPITAL = "capital"


class ProgressValue(BaseModel):
    """A progression value to the goal. For example: 12km, 20%, 30 pages. Should use the same unit as the parent."""

    unit: ProgressUnit
    value: float


class SmartDescription(BaseModel):
    """The smart description of a to-do."""

    specific: str
    """A clear definition of success"""

    measurable: str
    """How to measure progress"""

    actionable: str
    """What to do to reach the goal"""

    relevant: str
    """Why is it important"""

    time_bound: date | datetime
    """A clear deadline."""


class Status(StrEnum):
    """Current status of the to-do."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TrackingMode(StrEnum):
    """Tracking type for to-dos."""

    CUMULATIVE = "cumulative"
    """Each step bring us closer"""

    PERFORMANCE = "performance"
    """A performance to reach. For example, running 10km."""

    FIXED = "fixed"
    """Ends at specific date. For example, a language class."""


class Tracking(BaseModel):
    """How to track the progress of the to-do."""

    mode: TrackingMode
    target: ProgressValue | None


class ToDoType(StrEnum):
    """To-do type."""

    BOUNDED = "bounded"
    """The to-do ends at a specific date"""

    OPEN = "open"
    """The to-do has not a defined ending"""


class ToDo(BaseModel):
    """A to-do item with optional hierarchy, tracking, and metadata."""

    model_config = ConfigDict(validate_assignment=True)

    todo_id: ToDoId | None
    title: str
    _status: Status | None = PrivateAttr(default=None)
    _priority: Priority | None = PrivateAttr(default=None)
    todo_type: ToDoType = ToDoType.OPEN
    tracking: Tracking = Tracking(mode=TrackingMode.CUMULATIVE, target=None)
    progress: float = 0.0
    start: date | datetime | None = None
    end: date | datetime | None = None
    depends_on: list[ToDoId] = []
    before: list[ToDoId] = []
    smart: SmartDescription | None = None
    created: date | datetime | None = None
    tags: set[Tag] = set()
    parent: Self | None = None
    _children: list[Self] = PrivateAttr(default_factory=list)

    PROPERTY_TYPES: ClassVar[set[str]] = {
        "title",
        "status",
        "priority",
        "todo_type",
        "tracking",
        "progress",
        "start",
        "end",
        "depends_on",
        "before",
        "smart",
        "created",
        "tags",
    }
    """Names of fields that can be set from a data file.

    Used by the parser to validate property names from YAML blocks. Fields
    managed by the application (todo_id, parent, children) are excluded.
    """

    @property
    def children(self) -> list[Self]:
        """The children of the to-do. Read-only: use add_child to add children."""
        return self._children

    @property
    def level(self) -> int:
        """The level of the todo. The root is at level 1."""
        return self.parent.level + 1 if self.parent else 1

    def add_child(self, child: Self) -> None:
        """Add a child to the to-do and set its parent."""
        child.parent = self
        self._children.append(child)

    @classmethod
    def create(cls, *, children: list[Self] | None = None, **kwargs: object) -> Self:
        """Create a ToDo, optionally with children."""
        todo = cls(**kwargs)  # pyright: ignore[reportArgumentType]
        if todo.parent is not None:
            todo.parent._children.append(todo)
        for child in children or []:
            todo.add_child(child)
        return todo

    @property
    def status(self) -> Status | None:
        """The status of the to-do.

        Of it has no direct status, looks that the status of its direct children. If all the children are having the
        same status and this status is NOT_STARTED, IN_PROGRESS, DONE or PAUSED, return that status. Otherwise, if any
        children is IN_PROGRESS or DONE, return IN_PROGRESS.
        """
        if self._status:
            return self._status
        if not self.children:
            return None
        for status in [Status.NOT_STARTED, Status.IN_PROGRESS, Status.DONE, Status.PAUSED]:
            if all(child.status == status for child in self.children):
                return status
        for status in [Status.IN_PROGRESS, Status.DONE]:
            if any(child.status == status for child in self.children):
                return Status.IN_PROGRESS
        # CANCELLED is intentionally excluded: a mix of CANCELLED and other statuses
        # (or all CANCELLED) returns None, leaving the parent without a derived status.
        return None

    @status.setter
    def status(self, status: Status | None) -> None:
        self._status = status

    @property
    def priority(self) -> Priority:
        """The priority of the to-do.

        If it has no direct priority, return the status search its ancestors or LOW.
        """
        if self._priority:
            return self._priority
        if self.parent:
            return self.parent.priority
        return Priority.LOW

    @priority.setter
    def priority(self, priority: Priority | None) -> None:
        self._priority = priority


def get_tags_from_todos(todos: Iterable[ToDo]) -> dict[Tag, list[ToDo]]:
    """Returns all the todos associated to a particular tag from todos."""
    result: dict[Tag, list[ToDo]] = {}
    for todo in todos:
        for tag in todo.tags:
            result.setdefault(tag, []).append(todo)
    return result
