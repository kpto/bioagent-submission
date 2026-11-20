"""Read and write one event per file under a project's journal directory."""

from __future__ import annotations

import json
from pathlib import Path

from ...model.public.events import EVENT_BY_TYPE, Event

#: Where a project keeps its ledger, relative to the project root.
JOURNAL = Path("journal") / "events"


def events_directory(root: Path) -> Path:
    """The directory a project's events live in."""

    return root / JOURNAL


def load_events(root: Path) -> list[Event]:
    directory = events_directory(root)
    events: list[Event] = []
    if not directory.exists():
        return events
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cls = EVENT_BY_TYPE.get(str(data.get("event_type")))
        if cls is None:
            raise ValueError(
                f"{path.name}: unknown event_type {data.get('event_type')!r}"
            )
        try:
            events.append(cls.model_validate(data))
        except Exception as error:
            raise ValueError(f"{path.name}: {error}") from error
    events.sort(key=lambda event: (event.created_time, event.code))
    return events


def save_event(root: Path, event: Event) -> Path:
    directory = events_directory(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{event.id}.json"
    path.write_text(
        json.dumps(event.model_dump(mode="json"), indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


__all__ = ["JOURNAL", "events_directory", "load_events", "save_event"]
