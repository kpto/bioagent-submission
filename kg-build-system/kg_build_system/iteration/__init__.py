"""The iteration ledger: typed events, their links and their verification.

A project keeps one JSON document per event under ``journal/events``. The
model validates one record; the verifier checks the links across records.

Example:
    ```python
    from pathlib import Path
    from kg_build_system.iteration import load_ledger, verify_ledger

    events = load_ledger(Path("."))
    assert verify_ledger(events) == []
    ```
"""

from __future__ import annotations

from .model.public.events import (
    Beginning,
    EvaluationCreated,
    EvaluationRun,
    EvaluationWithdrawal,
    Event,
    EventReference,
    ExternalReference,
    FindingCreated,
    FindingWithdrawal,
    ProposalCreated,
    ProposalWithdrawal,
    RevisionCreated,
    typed_links,
)
from .service.public.ledger import (
    append_event,
    ledger_directory,
    load_ledger,
    new_event_id,
    next_event_code,
    verify_ledger,
)
from .service.public.lineage import revision_lineage

__all__ = [
    "Beginning",
    "EvaluationCreated",
    "EvaluationRun",
    "EvaluationWithdrawal",
    "Event",
    "EventReference",
    "ExternalReference",
    "FindingCreated",
    "FindingWithdrawal",
    "ProposalCreated",
    "ProposalWithdrawal",
    "RevisionCreated",
    "append_event",
    "ledger_directory",
    "load_ledger",
    "new_event_id",
    "next_event_code",
    "revision_lineage",
    "typed_links",
    "verify_ledger",
]
