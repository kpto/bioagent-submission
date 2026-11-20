"""The graph rules a single event cannot check."""

from __future__ import annotations

from collections.abc import Sequence

from ...model.public.events import Event, typed_links


def verify_events(events: Sequence[Event]) -> list[str]:
    """Return the ledger's problems; an empty list means consistent."""

    problems: list[str] = []
    known = {event.id: event for event in events}
    for event in events:
        for reference in event.references:
            target = known.get(reference.linked_event)
            if target is None:
                problems.append(
                    f"{event.code}: reference {reference.linked_event} does not resolve"
                )
            elif target.created_time >= event.created_time:
                problems.append(f"{event.code}: reference {target.code} is not earlier")
        for name, target_id in typed_links(event):
            target = known.get(target_id)
            if target is None:
                problems.append(f"{event.code}: {name} {target_id} does not resolve")
            elif target.created_time >= event.created_time:
                problems.append(f"{event.code}: {name} {target.code} is not earlier")
        assumed = {target for _, target in typed_links(event)}
        for reference in event.references:
            if reference.linked_event in assumed:
                problems.append(
                    f"{event.code}: reference {reference.linked_event} "
                    "duplicates a typed link"
                )
    return problems


__all__ = ["verify_events"]
