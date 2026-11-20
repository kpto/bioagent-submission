"""Typed events of the iteration ledger.

A record is flat: links are event ids, so one event is one JSON document and a
whole ledger validates record by record before the graph rules run.

Example:
    ```python
    from kg_build_system.iteration.model.public.events import FindingCreated

    event = FindingCreated(
        id="a1b2c3d4",
        code="F-1",
        subject="F-1",
        created_time=...,  # a datetime
        title="One site is hot",
        observation="The site is hot.",
    )
    ```
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from kg_build_system.kernel import JsonValue


class ExternalReference(BaseModel):
    """Where an event came from outside the ledger."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    name: str = Field(min_length=1)
    detail: JsonValue | None = None


class EventReference(BaseModel):
    """A named relation to another event, stored as its id."""

    model_config = ConfigDict(extra="forbid")

    linkage_name: str = Field(min_length=1)
    linked_event: str = Field(pattern=r"^[A-Za-z0-9]{8}$")


class Event(BaseModel):
    """The fields every event carries."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z0-9]{8}$")
    code: str = Field(pattern=r"^[A-Z]+-[0-9]+$")
    subject: str = Field(min_length=1)
    created_time: datetime
    title: JsonValue
    references: list[EventReference] = Field(default_factory=list)
    external_references: list[ExternalReference] = Field(default_factory=list)
    event_type: str


class Beginning(Event):
    event_type: str = "beginning"


class FindingCreated(Event):
    event_type: str = "finding.created"
    observation: JsonValue
    evidence: JsonValue | None = None
    metric: JsonValue | None = None


class FindingWithdrawal(Event):
    event_type: str = "finding.withdrawal"
    withdrawn_finding: str = Field(pattern=r"^[A-Za-z0-9]{8}$")
    reason: JsonValue


class ProposalCreated(Event):
    event_type: str = "proposal.created"
    rationale: JsonValue
    #: Stored as an event id; resolves to a revision or the beginning.
    based_revision: str = Field(pattern=r"^[A-Za-z0-9]{8}$")
    change: JsonValue | None = None


class ProposalWithdrawal(Event):
    event_type: str = "proposal.withdrawal"
    withdrawn_proposal: str = Field(pattern=r"^[A-Za-z0-9]{8}$")
    reason: JsonValue


class RevisionCreated(Event):
    event_type: str = "revision.created"
    based_proposals: list[str] = Field(min_length=1)
    description: JsonValue


class EvaluationCreated(Event):
    event_type: str = "evaluation.created"
    method: JsonValue
    metric: JsonValue | None = None


class EvaluationWithdrawal(Event):
    event_type: str = "evaluation.withdrawal"
    withdrawn_evaluation: str = Field(pattern=r"^[A-Za-z0-9]{8}$")
    reason: JsonValue


class EvaluationRun(Event):
    event_type: str = "evaluation.run"
    evaluation: str = Field(pattern=r"^[A-Za-z0-9]{8}$")
    evaluated_revision: str = Field(pattern=r"^[A-Za-z0-9]{8}$")
    result: JsonValue | None = None


EVENT_CLASSES: tuple[type[Event], ...] = (
    Beginning,
    FindingCreated,
    FindingWithdrawal,
    ProposalCreated,
    ProposalWithdrawal,
    RevisionCreated,
    EvaluationCreated,
    EvaluationWithdrawal,
    EvaluationRun,
)

EVENT_BY_TYPE: dict[str, type[Event]] = {
    cls.model_fields["event_type"].default: cls for cls in EVENT_CLASSES
}


def typed_links(event: Event) -> list[tuple[str, str]]:
    """The typed links of an event, as (name, target event id)."""

    found: list[tuple[str, str]] = []
    if isinstance(event, ProposalCreated):
        found.append(("based_revision", event.based_revision))
    if isinstance(event, FindingWithdrawal):
        found.append(("withdrawn_finding", event.withdrawn_finding))
    if isinstance(event, ProposalWithdrawal):
        found.append(("withdrawn_proposal", event.withdrawn_proposal))
    if isinstance(event, EvaluationWithdrawal):
        found.append(("withdrawn_evaluation", event.withdrawn_evaluation))
    if isinstance(event, RevisionCreated):
        found.extend(("implements", proposal) for proposal in event.based_proposals)
    if isinstance(event, EvaluationRun):
        found.append(("runs", event.evaluation))
        found.append(("measures", event.evaluated_revision))
    return found


__all__ = [
    "Beginning",
    "EVENT_BY_TYPE",
    "EVENT_CLASSES",
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
    "typed_links",
]
