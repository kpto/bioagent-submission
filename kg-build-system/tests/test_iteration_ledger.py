from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from kg_build_system.iteration import (
    Beginning,
    EventReference,
    FindingCreated,
    ProposalCreated,
    RevisionCreated,
    append_event,
    ledger_directory,
    load_ledger,
    new_event_id,
    next_event_code,
    verify_ledger,
)

T = datetime(2026, 11, 19, 12, tzinfo=UTC)


def _finding(code: str, when: datetime, **extra: object) -> FindingCreated:
    return FindingCreated(
        id=new_event_id(),
        code=code,
        subject=code,
        created_time=when,
        title=code,
        observation="Observed.",
        **extra,
    )


def test_an_event_round_trips_through_the_ledger(tmp_path: Path) -> None:
    beginning = Beginning(
        id=new_event_id(),
        code="BEGIN-1",
        subject="BEGIN-1",
        created_time=T,
        title="Beginning",
    )
    append_event(tmp_path, beginning)
    assert load_ledger(tmp_path) == [beginning]


def test_a_new_project_writes_its_ledger_under_the_journal(tmp_path: Path) -> None:
    append_event(tmp_path, _finding("F-1", T))
    journal = tmp_path / "journal" / "events"
    assert ledger_directory(tmp_path) == journal
    assert len(list(journal.glob("*.json"))) == 1


def test_an_unknown_field_is_refused() -> None:
    with pytest.raises(ValidationError):
        FindingCreated(
            id=new_event_id(),
            code="F-1",
            subject="F-1",
            created_time=T,
            title="F-1",
            observation="Observed.",
            state="accepted",
        )


def test_codes_increment_per_family() -> None:
    events = [_finding("F-1", T), _finding("F-2", T)]
    assert next_event_code(events, "finding") == "F-3"
    assert next_event_code(events, "proposal") == "P-1"


def test_a_dangling_reference_is_reported() -> None:
    event = _finding(
        "F-2",
        T + timedelta(seconds=1),
        references=[EventReference(linkage_name="rests_on", linked_event="deadbeef")],
    )
    assert any(
        "does not resolve" in problem for problem in verify_ledger([_finding("F-1", T), event])
    )


def test_a_link_must_point_at_an_earlier_event() -> None:
    earlier = _finding("F-1", T)
    later = _finding(
        "F-2",
        T - timedelta(seconds=1),
        references=[EventReference(linkage_name="rests_on", linked_event=earlier.id)],
    )
    assert any("is not earlier" in problem for problem in verify_ledger([earlier, later]))


def test_a_reference_may_not_repeat_a_typed_link() -> None:
    beginning = Beginning(
        id=new_event_id(),
        code="BEGIN-1",
        subject="BEGIN-1",
        created_time=T,
        title="Beginning",
    )
    proposal = ProposalCreated(
        id=new_event_id(),
        code="P-1",
        subject="P-1",
        created_time=T + timedelta(seconds=1),
        title="P-1",
        rationale="Because.",
        based_revision=beginning.id,
        references=[EventReference(linkage_name="rests_on", linked_event=beginning.id)],
    )
    assert any(
        "duplicates a typed link" in problem
        for problem in verify_ledger([beginning, proposal])
    )


def test_a_revision_without_proposals_is_refused() -> None:
    with pytest.raises(ValidationError):
        RevisionCreated(
            id=new_event_id(),
            code="B-1",
            subject="B-1",
            created_time=T,
            title="B-1",
            based_proposals=[],
            description={},
        )
