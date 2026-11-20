"""The iteration ledger: load, append and verify typed events.

Example:
    ```python
    from pathlib import Path
    from kg_build_system.iteration import load_ledger, verify_ledger

    events = load_ledger(Path("."))
    assert verify_ledger(events) == []
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ...model.public.events import Event
from .._private.ids import new_id, next_code
from .._private.store import events_directory, load_events, save_event
from .._private.verify import verify_events


def load_ledger(root: Path) -> list[Event]:
    """Read every event under ``<root>/journal/events``."""

    return load_events(root)


def append_event(root: Path, event: Event) -> Path:
    """Write one event and return its file."""

    return save_event(root, event)


def verify_ledger(events: Sequence[Event]) -> list[str]:
    """Return the ledger's problems; an empty list means consistent."""

    return verify_events(events)


def ledger_directory(root: Path) -> Path:
    """The directory a project keeps its events in."""

    return events_directory(root)


def next_event_code(events: Sequence[Event], family: str) -> str:
    """The next free code for one family, such as ``F-7``."""

    return next_code(events, family)


def new_event_id() -> str:
    """An eight-character event id."""

    return new_id()


__all__ = [
    "append_event",
    "ledger_directory",
    "load_ledger",
    "new_event_id",
    "next_event_code",
    "verify_ledger",
]
