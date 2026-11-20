"""The committed iteration ledger: its shape and its graph rules."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from kg_build_system.iteration import (
    Beginning,
    EvaluationCreated,
    EvaluationRun,
    EvaluationWithdrawal,
    Event,
    FindingCreated,
    FindingWithdrawal,
    ProposalCreated,
    ProposalWithdrawal,
    RevisionCreated,
    load_ledger,
    verify_ledger,
)

ROOT = Path(__file__).resolve().parents[1]


def _events() -> list[Event]:
    return load_ledger(ROOT)


def test_the_ledger_loads_and_has_no_problems() -> None:
    events = _events()
    assert events
    assert verify_ledger(events) == []


def test_the_history_has_one_beginning_and_its_recorded_families() -> None:
    events = _events()
    counts = Counter(event.event_type for event in events)
    beginnings = [event for event in events if isinstance(event, Beginning)]
    assert len(beginnings) == 1
    assert beginnings[0].code == "BEGIN-1"
    assert counts["revision.created"] >= 1
    assert counts["proposal.created"] >= 1
    assert counts["finding.created"] >= counts["proposal.created"]
    assert counts["evaluation.run"] >= 1


def test_codes_are_unique_and_family_scoped() -> None:
    events = _events()
    codes = [event.code for event in events]
    assert len(codes) == len(set(codes))
    families = {
        Beginning: "BEGIN",
        FindingCreated: "F",
        FindingWithdrawal: "FW",
        ProposalCreated: "P",
        ProposalWithdrawal: "PW",
        RevisionCreated: "B",
        EvaluationCreated: "E",
        EvaluationRun: "EV",
        EvaluationWithdrawal: "EW",
    }
    for event in events:
        prefixes = {
            prefix for kind, prefix in families.items() if isinstance(event, kind)
        }
        assert len(prefixes) == 1, event.code
        assert event.code.startswith(f"{next(iter(prefixes))}-")


def test_every_revision_names_the_proposals_it_implements() -> None:
    events = _events()
    proposals = {
        event.id: event for event in events if isinstance(event, ProposalCreated)
    }
    revisions = [event for event in events if isinstance(event, RevisionCreated)]
    assert revisions
    for revision in revisions:
        assert revision.based_proposals
        for proposal_id in revision.based_proposals:
            proposal = proposals.get(proposal_id)
            assert proposal is not None, revision.code
            assert proposal.created_time < revision.created_time


def test_every_withdrawal_names_an_earlier_event_of_its_family() -> None:
    events = _events()
    by_id = {event.id: event for event in events}
    for event in events:
        if isinstance(event, FindingWithdrawal):
            assert isinstance(by_id[event.withdrawn_finding], FindingCreated)
        elif isinstance(event, ProposalWithdrawal):
            assert isinstance(by_id[event.withdrawn_proposal], ProposalCreated)
        elif isinstance(event, EvaluationWithdrawal):
            assert isinstance(by_id[event.withdrawn_evaluation], EvaluationCreated)


def test_an_evaluation_run_names_a_revision_and_a_protocol() -> None:
    events = _events()
    by_id = {event.id: event for event in events}
    runs = [event for event in events if isinstance(event, EvaluationRun)]
    assert runs
    for run in runs:
        assert isinstance(by_id[run.evaluated_revision], RevisionCreated)
        assert isinstance(by_id[run.evaluation], EvaluationCreated)
        assert by_id[run.evaluation].created_time < run.created_time
