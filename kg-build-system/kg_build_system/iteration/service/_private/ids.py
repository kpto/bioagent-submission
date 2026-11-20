"""Identifiers and codes for a new event."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from ...model.public.events import Event

#: One code prefix per event kind.
PREFIX = {
    "beginning": "BEGIN",
    "finding": "F",
    "finding.withdrawal": "FW",
    "proposal": "P",
    "proposal.withdrawal": "PW",
    "revision": "B",
    "evaluation": "E",
    "evaluation.run": "EV",
    "evaluation.withdrawal": "EW",
}


def new_id() -> str:
    """An eight-character event id."""

    return uuid.uuid4().hex[:8]


def next_code(events: Sequence[Event], family: str) -> str:
    """The next free code for one family, such as ``F-7``."""

    prefix = PREFIX[family]
    highest = 0
    head = f"{prefix}-"
    for event in events:
        if not event.code.startswith(head):
            continue
        tail = event.code[len(head) :]
        if tail.isdigit():
            highest = max(highest, int(tail))
    return f"{prefix}-{highest + 1}"


__all__ = ["PREFIX", "new_id", "next_code"]
