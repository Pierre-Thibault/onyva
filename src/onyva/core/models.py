from collections.abc import Iterable, MutableSequence
from datetime import date, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel

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
    """Tracking type for to-dos"""

    CUMULATIVE = "cumulative"
    """Each step bring us closer"""

    PERFORMANCE = "performance"
    """A performance to reach. For example, running 10km."""

    FIXED = "fixed"
    """Ends at specific date. For example, a language class."""


class Tracking(BaseModel):
    """How to track the progress of the to-do"""

    mode: TrackingMode
    target: ProgressValue | None


class ToDoType(StrEnum):
    """To-do type"""

    BOUNDED = "bounded"
    """The to-do ends at a specific date"""

    OPEN = "open"
    """The to-do has not a defined ending"""


class ToDo(BaseModel):
    to_do_id: ToDoId
    title: str
    _status: Status | None = None
    _priority: Priority | None = None
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
    children: list[Self] = []

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


class ToDoList(MutableSequence[ToDo]):
    """A sequence of to-dos with their used tags

    All the to-dos belonging together are in the list.
    """

    tags: set[Tag]
    _data: list[ToDo]

    def __init__(self, iterable: Iterable[ToDo] = ()) -> None:
        super().__init__()
        self._data = list(iterable)
        self._update_tags()

    def _update_tags(self) -> None:
        self.tags = set()
        for to_do in self:
            self.tags.update(to_do.tags)

    # -- abstract methods to implement --
    def __getitem__(self, index: int) -> ToDo:  # type: ignore[override]
        return self._data[index]

    def __setitem__(self, index: int, value: ToDo) -> None:  # type: ignore[override]
        self._data[index] = value
        self._update_tags()

    def __delitem__(self, index: int) -> None:  # type: ignore[override]
        del self._data[index]
        self._update_tags()

    def __len__(self) -> int:
        return len(self._data)

    def insert(self, index: int, value: ToDo) -> None:
        self._data.insert(index, value)
        self.tags.update(value.tags)
