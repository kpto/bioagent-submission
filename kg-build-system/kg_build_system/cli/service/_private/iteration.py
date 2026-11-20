"""The iteration command surface: findings, proposals, revisions, evaluations.

Groups are nouns; their subcommands are verbs. Every command appends or reads
typed events in the project's ledger under ``journal/events``.

Example:
    ```python
    from kg_build_system.cli.service._private.iteration import (
        add_iteration_commands,
    )
    ```
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from kg_build_system.iteration import (
    Beginning,
    EvaluationCreated,
    EvaluationRun,
    EvaluationWithdrawal,
    Event,
    ExternalReference,
    FindingCreated,
    FindingWithdrawal,
    ProposalCreated,
    ProposalWithdrawal,
    RevisionCreated,
    append_event,
    load_ledger,
    new_event_id,
    next_event_code,
    verify_ledger,
)

BEGINNING_CODE = "BEGIN-1"
DEFAULT_PROTOCOL_CODE = "E-1"


def _text(value: Any) -> str:
    if value is None:
        return ""
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return str(value)


def _first_line(value: Any) -> str:
    return next(
        (line.strip() for line in str(value or "").splitlines() if line.strip()), ""
    )


def _compact(value: Any) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{key}={_compact(item)}" for key, item in value.items())
    if isinstance(value, list):
        return f"{len(value)} items"
    return _text(value)


def _print_rows(title: str, rows: list[dict[str, Any]]) -> None:
    print(f"{title}: {len(rows)}")
    for row in rows:
        code = str(row.get("code") or "")
        state = "withdrawn" if row.get("withdrawn") else ""
        label = _first_line(row.get("title") or row.get("observation"))
        print(f"  {code}  {state}  {label}".rstrip())


def _render(arguments: argparse.Namespace, result: Any) -> int:
    if result is None:
        return 0
    failed = isinstance(result, dict) and result.get("ok") is False
    if getattr(arguments, "json", False):
        print(json.dumps(result, indent=2, default=str, sort_keys=True))
        return 1 if failed else 0
    if failed:
        print(f"error: {result.get('error') or 'command failed'}", file=sys.stderr)
        return 1
    if not isinstance(result, dict):
        print(result)
        return 0
    rows = result.get("rows")
    if isinstance(rows, list) and result.get("view"):
        _print_rows(str(result["view"]), rows)
        return 0
    for key, value in result.items():
        if key in {"ok", "error"} or value is None or value == "":
            continue
        if isinstance(value, dict):
            print(f"{key}:")
            for inner, item in value.items():
                print(f"  {inner}: {_text(item)}")
        else:
            print(f"{key}: {_text(value)}")
    return 0


def _run(arguments: argparse.Namespace) -> int:
    handler = getattr(arguments, "handler", None)
    if handler is None:
        return 2
    try:
        result = handler(arguments)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return _render(arguments, result)


def _source(command: str) -> list[ExternalReference]:
    return [ExternalReference(type="cli", name=f"kbs {command}")]


def _find(events: list[Event], code: str) -> Event | None:
    return next((event for event in events if event.code == code), None)


def _append(
    root: Path, events: list[Event], event: Event, key: str
) -> dict[str, Any]:
    problems = verify_ledger([*events, event])
    if problems:
        return {"ok": False, "error": "; ".join(problems)}
    path = append_event(root, event)
    payload = event.model_dump(mode="json")
    payload["path"] = str(path)
    return {"ok": True, key: payload}


def _ensure_beginning(root: Path, events: list[Event]) -> Beginning:
    for event in events:
        if isinstance(event, Beginning):
            return event
    beginning = Beginning(
        id=new_event_id(),
        code=BEGINNING_CODE,
        subject=BEGINNING_CODE,
        created_time=datetime.now(UTC) - timedelta(seconds=1),
        title="Beginning",
        external_references=_source("init"),
    )
    append_event(root, beginning)
    events.insert(0, beginning)
    return beginning


def _withdrawn(events: list[Event], family: type[Event]) -> set[str]:
    ids: set[str] = set()
    for event in events:
        if isinstance(event, FindingWithdrawal) and family is FindingCreated:
            ids.add(event.withdrawn_finding)
        if isinstance(event, ProposalWithdrawal) and family is ProposalCreated:
            ids.add(event.withdrawn_proposal)
        if isinstance(event, EvaluationWithdrawal) and family is EvaluationCreated:
            ids.add(event.withdrawn_evaluation)
    return ids


def command_finding_add(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    events = load_ledger(root)
    _ensure_beginning(root, events)
    code = next_event_code(events, "finding")
    event = FindingCreated(
        id=new_event_id(),
        code=code,
        subject=code,
        created_time=datetime.now(UTC),
        title=args.title or _first_line(args.observation),
        observation=args.observation,
        evidence=args.evidence,
        metric=args.metric,
        external_references=_source("finding add"),
    )
    return _append(root, events, event, "finding")


def command_finding_list(args: argparse.Namespace) -> dict[str, Any]:
    events = load_ledger(Path(args.root))
    withdrawn = _withdrawn(events, FindingCreated)
    rows = [
        {
            "code": event.code,
            "title": event.title,
            "observation": event.observation,
            "withdrawn": event.id in withdrawn,
        }
        for event in events
        if isinstance(event, FindingCreated)
    ]
    return {"ok": True, "view": "findings", "rows": rows}


def command_finding_withdraw(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    events = load_ledger(root)
    target = _find(events, args.id)
    if not isinstance(target, FindingCreated):
        return {"ok": False, "error": f"finding {args.id} not found"}
    event = FindingWithdrawal(
        id=new_event_id(),
        code=next_event_code(events, "finding.withdrawal"),
        subject=target.subject,
        created_time=datetime.now(UTC),
        title=f"Withdraw {target.code}",
        withdrawn_finding=target.id,
        reason=args.reason,
        external_references=_source("finding withdraw"),
    )
    return _append(root, events, event, "withdrawal")


def command_proposal_create(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    events = load_ledger(root)
    beginning = _ensure_beginning(root, events)
    code = next_event_code(events, "proposal")
    if args.based_revision:
        target: Event | None = _find(events, args.based_revision)
        if target is None:
            return {"ok": False, "error": f"revision {args.based_revision} not found"}
    else:
        revisions = [event for event in events if isinstance(event, RevisionCreated)]
        target = revisions[-1] if revisions else beginning
    event = ProposalCreated(
        id=new_event_id(),
        code=code,
        subject=args.subject,
        created_time=datetime.now(UTC),
        title=args.title or _first_line(args.rationale),
        rationale=args.rationale,
        based_revision=target.id,
        external_references=_source("proposal create"),
    )
    payload = _append(root, events, event, "proposal")
    if payload.get("ok"):
        payload["based_revision"] = target.code
    return payload


def command_proposal_list(args: argparse.Namespace) -> dict[str, Any]:
    events = load_ledger(Path(args.root))
    withdrawn = _withdrawn(events, ProposalCreated)
    by_id = {event.id: event for event in events}
    rows = [
        {
            "code": event.code,
            "title": event.title,
            "subject": event.subject,
            "based_revision": getattr(
                by_id.get(event.based_revision), "code", event.based_revision
            ),
            "withdrawn": event.id in withdrawn,
        }
        for event in events
        if isinstance(event, ProposalCreated)
    ]
    return {"ok": True, "view": "proposals", "rows": rows}


def command_proposal_withdraw(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    events = load_ledger(root)
    target = _find(events, args.id)
    if not isinstance(target, ProposalCreated):
        return {"ok": False, "error": f"proposal {args.id} not found"}
    event = ProposalWithdrawal(
        id=new_event_id(),
        code=next_event_code(events, "proposal.withdrawal"),
        subject=target.subject,
        created_time=datetime.now(UTC),
        title=f"Withdraw {target.code}",
        withdrawn_proposal=target.id,
        reason=args.reason,
        external_references=_source("proposal withdraw"),
    )
    return _append(root, events, event, "withdrawal")


def command_revision_record(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    events = load_ledger(root)
    proposals: list[ProposalCreated] = []
    for code in args.based_proposal:
        target = _find(events, code)
        if not isinstance(target, ProposalCreated):
            return {"ok": False, "error": f"proposal {code} not found"}
        proposals.append(target)
    if not proposals:
        return {"ok": False, "error": "at least one --based-proposal is required"}
    code = next_event_code(events, "revision")
    event = RevisionCreated(
        id=new_event_id(),
        code=code,
        subject=args.subject or code,
        created_time=datetime.now(UTC),
        title=args.message or "Revision",
        based_proposals=[proposal.id for proposal in proposals],
        description={"message": args.message} if args.message else {},
        external_references=_source("revision record"),
    )
    return _append(root, events, event, "revision")


def command_revision_list(args: argparse.Namespace) -> dict[str, Any]:
    events = load_ledger(Path(args.root))
    by_id = {event.id: event for event in events}
    rows = [
        {
            "code": event.code,
            "title": event.title,
            "based_on": ", ".join(
                getattr(by_id.get(item), "code", item) for item in event.based_proposals
            ),
            "description": _compact(event.description),
        }
        for event in events
        if isinstance(event, RevisionCreated)
    ]
    return {"ok": True, "view": "revisions", "rows": rows}


def command_revision_compare(args: argparse.Namespace) -> dict[str, Any]:
    events = load_ledger(Path(args.root))
    before = _find(events, args.before)
    after = _find(events, args.after)
    if not isinstance(before, RevisionCreated):
        return {"ok": False, "error": f"revision {args.before} not found"}
    if not isinstance(after, RevisionCreated):
        return {"ok": False, "error": f"revision {args.after} not found"}
    return {
        "ok": True,
        "before": before.code,
        "after": after.code,
        "before_description": _compact(before.description),
        "after_description": _compact(after.description),
    }


def command_evaluation_run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    events = load_ledger(root)
    revision = _find(events, args.revision)
    if not isinstance(revision, RevisionCreated):
        return {"ok": False, "error": f"revision {args.revision} not found"}
    protocol = _find(events, args.protocol)
    if protocol is None:
        protocol = EvaluationCreated(
            id=new_event_id(),
            code=args.protocol,
            subject=args.protocol,
            created_time=datetime.now(UTC) - timedelta(seconds=1),
            title="Evaluation protocol",
            method="project evaluation gates",
            external_references=_source("evaluation run"),
        )
        append_event(root, protocol)
        events.append(protocol)
    if not isinstance(protocol, EvaluationCreated):
        return {"ok": False, "error": f"{args.protocol} is not an evaluation protocol"}
    result = None
    if args.result:
        try:
            result = json.loads(args.result)
        except json.JSONDecodeError as error:
            return {"ok": False, "error": f"--result is not JSON: {error.msg}"}
    event = EvaluationRun(
        id=new_event_id(),
        code=next_event_code(events, "evaluation.run"),
        subject=args.revision,
        created_time=datetime.now(UTC),
        title=args.title or f"Evaluation of {revision.code}",
        evaluation=protocol.id,
        evaluated_revision=revision.id,
        result=result,
        external_references=_source("evaluation run"),
    )
    return _append(root, events, event, "run")


def command_evaluation_list(args: argparse.Namespace) -> dict[str, Any]:
    events = load_ledger(Path(args.root))
    by_id = {event.id: event for event in events}
    rows = [
        {
            "code": event.code,
            "title": event.title,
            "revision": getattr(
                by_id.get(event.evaluated_revision), "code", event.evaluated_revision
            ),
            "protocol": getattr(by_id.get(event.evaluation), "code", event.evaluation),
            "result": _compact(event.result),
        }
        for event in events
        if isinstance(event, EvaluationRun)
    ]
    return {"ok": True, "view": "evaluations", "rows": rows}


def _project_argument(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--project",
        dest="root",
        metavar="PROJECT",
        default=".",
        help="project directory",
    )
    command.add_argument("--json", action="store_true", help="print JSON")


def _leaf(
    parent: Any,
    name: str,
    handler: Any,
    *,
    help: str,
) -> argparse.ArgumentParser:
    command = parent.add_parser(name, help=help)
    _project_argument(command)
    command.set_defaults(handler=handler, command_handler=_run)
    return command


def add_iteration_commands(sub: Any) -> None:
    """Add the iteration nouns to an existing subparser registry."""

    finding = sub.add_parser("finding", help="record, list or withdraw a finding")
    finding_sub = finding.add_subparsers(dest="action", required=True)
    add = _leaf(finding_sub, "add", command_finding_add, help="append a finding")
    add.add_argument("--observation", required=True)
    add.add_argument("--evidence")
    add.add_argument("--metric")
    add.add_argument("--title")
    _leaf(finding_sub, "list", command_finding_list, help="list findings")
    withdraw = _leaf(
        finding_sub, "withdraw", command_finding_withdraw, help="withdraw a finding"
    )
    withdraw.add_argument("--id", required=True)
    withdraw.add_argument("--reason", required=True)

    proposal = sub.add_parser("proposal", help="create, list or withdraw a proposal")
    proposal_sub = proposal.add_subparsers(dest="action", required=True)
    create = _leaf(
        proposal_sub, "create", command_proposal_create, help="record a proposal"
    )
    create.add_argument("--subject", required=True)
    create.add_argument("--rationale", required=True)
    create.add_argument("--based-revision")
    create.add_argument("--title")
    _leaf(proposal_sub, "list", command_proposal_list, help="list proposals")
    withdraw = _leaf(
        proposal_sub, "withdraw", command_proposal_withdraw, help="withdraw a proposal"
    )
    withdraw.add_argument("--id", required=True)
    withdraw.add_argument("--reason", required=True)

    revision = sub.add_parser("revision", help="record, list or compare revisions")
    revision_sub = revision.add_subparsers(dest="action", required=True)
    record = _leaf(
        revision_sub, "record", command_revision_record,
        help="record a revision from the proposals it implements",
    )
    record.add_argument("--based-proposal", action="append", required=True)
    record.add_argument("--message")
    record.add_argument("--subject")
    _leaf(revision_sub, "list", command_revision_list, help="list revisions")
    compare = _leaf(
        revision_sub, "compare", command_revision_compare,
        help="compare two recorded revisions",
    )
    compare.add_argument("--before", required=True)
    compare.add_argument("--after", required=True)

    evaluation = sub.add_parser("evaluation", help="record or list evaluation runs")
    evaluation_sub = evaluation.add_subparsers(dest="action", required=True)
    run = _leaf(
        evaluation_sub, "run", command_evaluation_run,
        help="record an evaluation run for a revision",
    )
    run.add_argument("--revision", required=True)
    run.add_argument("--protocol", default=DEFAULT_PROTOCOL_CODE)
    run.add_argument("--result", help="the run's result as JSON")
    run.add_argument("--title")
    _leaf(evaluation_sub, "list", command_evaluation_list, help="list evaluation runs")


__all__ = ["add_iteration_commands"]
