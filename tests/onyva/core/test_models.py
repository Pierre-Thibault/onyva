"""Tests for ToDo model properties."""

from datetime import date

from onyva.core.models import (
    Priority,
    ProgressValue,
    SmartDescription,
    Status,
    ToDo,
    ToDoList,
    ToDoType,
    Tracking,
    TrackingMode,
)


def test_todo_properties() -> None:
    """Test that all ToDo properties can be set and retrieved."""

    properties: dict[str, object] = {
        "title": "Learn Python",
        "status": Status.IN_PROGRESS,
        "priority": Priority.HIGH,
        "todo_type": ToDoType.BOUNDED,
        "tracking": Tracking(mode=TrackingMode.PERFORMANCE, target=ProgressValue(unit="km", value=10.0)),
        "progress": 0.5,
        "start": date(2026, 1, 1),
        "end": date(2026, 12, 31),
        "depends_on": ["todo-1", "todo-2"],
        "before": ["todo-3"],
        "smart": SmartDescription(
            specific="Run 10km",
            measurable="Distance in km",
            actionable="Train 3 times a week",
            relevant="Improve health",
            time_bound=date(2026, 12, 31),
        ),
        "created": date(2026, 1, 1),
        "tags": {"health", "sport"},
        "parent": ToDo(to_do_id="parent-1", title="Parent"),
        "children": [ToDo(to_do_id="child-1", title="Child")],
    }
    todo = ToDo(to_do_id="todo-1", title="Initial title")

    for name, value in properties.items():
        setattr(todo, name, value)

    for name, value in properties.items():
        assert getattr(todo, name) == value, f"Property '{name}' does not match expected value"


def test_status_not_started_when_all_children_not_started() -> None:
    """Test that status is NOT_STARTED when all children are not started."""
    child1 = ToDo(to_do_id="c1", title="Child 1")
    child2 = ToDo(to_do_id="c2", title="Child 2")
    child1.status = Status.NOT_STARTED
    child2.status = Status.NOT_STARTED

    parent = ToDo(to_do_id="p1", title="Parent", children=[child1, child2])

    assert parent.status == Status.NOT_STARTED


def test_status_in_progress_when_all_children_in_progress() -> None:
    """Test that status is IN_PROGRESS when all children are in progress."""
    child1 = ToDo(to_do_id="c1", title="Child 1")
    child2 = ToDo(to_do_id="c2", title="Child 2")
    child1.status = Status.IN_PROGRESS
    child2.status = Status.IN_PROGRESS

    parent = ToDo(to_do_id="p1", title="Parent", children=[child1, child2])

    assert parent.status == Status.IN_PROGRESS


def test_status_done_when_all_children_done() -> None:
    """Test that status is DONE when all children are done."""
    child1 = ToDo(to_do_id="c1", title="Child 1")
    child2 = ToDo(to_do_id="c2", title="Child 2")
    child1.status = Status.DONE
    child2.status = Status.DONE

    parent = ToDo(to_do_id="p1", title="Parent", children=[child1, child2])

    assert parent.status == Status.DONE


def test_status_paused_when_all_children_paused() -> None:
    """Test that status is PAUSED when all children are paused."""
    child1 = ToDo(to_do_id="c1", title="Child 1")
    child2 = ToDo(to_do_id="c2", title="Child 2")
    child1.status = Status.PAUSED
    child2.status = Status.PAUSED

    parent = ToDo(to_do_id="p1", title="Parent", children=[child1, child2])

    assert parent.status == Status.PAUSED


def test_status_derived_from_children_uniform() -> None:
    """Test that status is derived from children when all have the same status."""
    child1 = ToDo(to_do_id="c1", title="Child 1")
    child2 = ToDo(to_do_id="c2", title="Child 2")
    child1.status = Status.DONE
    child2.status = Status.DONE

    parent = ToDo(to_do_id="p1", title="Parent", children=[child1, child2])

    assert parent.status == Status.DONE


def test_status_derived_from_children_mixed() -> None:
    """Test that status is IN_PROGRESS when children have mixed statuses."""
    child1 = ToDo(to_do_id="c1", title="Child 1")
    child2 = ToDo(to_do_id="c2", title="Child 2")
    child1.status = Status.DONE
    child2.status = Status.NOT_STARTED

    parent = ToDo(to_do_id="p1", title="Parent", children=[child1, child2])

    assert parent.status == Status.IN_PROGRESS


def test_status_none_when_no_children_and_no_status() -> None:
    """Test that status is None when todo has no children and no direct status."""
    todo = ToDo(to_do_id="t1", title="Todo")
    assert todo.status is None


def test_status_none_when_all_children_cancelled() -> None:
    """Test that status is None when all children are cancelled."""
    child1 = ToDo(to_do_id="c1", title="Child 1")
    child2 = ToDo(to_do_id="c2", title="Child 2")
    child1.status = Status.CANCELLED
    child2.status = Status.CANCELLED

    parent = ToDo(to_do_id="p1", title="Parent", children=[child1, child2])

    assert parent.status is None


def test_priority_derived_from_parent() -> None:
    """Test that priority is inherited from parent when not set directly."""
    parent = ToDo(to_do_id="p1", title="Parent")
    parent.priority = Priority.CAPITAL

    child = ToDo(to_do_id="c1", title="Child", parent=parent)

    assert child.priority == Priority.CAPITAL


def test_priority_defaults_to_low() -> None:
    """Test that priority defaults to LOW when not set and no parent."""
    todo = ToDo(to_do_id="t1", title="Todo")
    assert todo.priority == Priority.LOW


def test_todo_list_operations() -> None:
    """Test ToDoList sequence operations."""
    todo1 = ToDo(to_do_id="t1", title="Todo 1", tags={"work"})
    todo2 = ToDo(to_do_id="t2", title="Todo 2", tags={"personal"})

    todo_list = ToDoList([todo1])

    assert len(todo_list) == 1

    todo_list.insert(1, todo2)
    assert len(todo_list) == 2
    assert "personal" in todo_list.tags

    todo3 = ToDo(to_do_id="t3", title="Todo 3", tags={"health"})
    todo_list[0] = todo3
    assert todo_list[0] == todo3
    assert "health" in todo_list.tags

    del todo_list[0]
    assert len(todo_list) == 1
