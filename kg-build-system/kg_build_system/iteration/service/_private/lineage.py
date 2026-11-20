"""The revision lineage: the DAG a consumer reads from the ledger.

The main graph is the spine of builds: the beginning and every revision, with
one link per implemented proposal. Proposals, findings and withdrawals are
collapsed into the counts on the card that consumed them. A revision with no
child is a leaf; every leaf except the newest is dangling.

A focused graph starts at one revision and follows every link until it reaches a
revision again (inclusive), plus the runs that measured it, the protocol each
run used, and the external references of every member. Values keep their
structure: a JsonValue becomes an object, array or typed scalar, never a
serialised string.

The module is a render model, not a DTO: heights and wrapped title lines are
computed here once so every renderer draws the same cards.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from ...model.public.events import (
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
    typed_links,
)

CARD_W = 200
TITLE_WRAP = 34

#: One noun per counted event type. A withdrawal is its own act, so it is
#: counted apart from the record it closes.
NOUN: dict[str, str] = {
    "finding.created": "finding",
    "finding.withdrawal": "withdrawal",
    "proposal.created": "proposal",
    "proposal.withdrawal": "withdrawal",
    "evaluation.created": "protocol",
    "evaluation.run": "run",
}

COUNT_ORDER = ("finding", "proposal", "run", "protocol", "withdrawal")

NODES = re.compile(r"([\d,]+)\s*nodes")
EDGES = re.compile(r"([\d,]+)\s*edges")


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _plural(noun: str, count: int) -> str:
    return f"{count} {noun if count == 1 else noun + 's'}"


def _wrap(text: str, width: int = TITLE_WRAP) -> list[str]:
    """Break a title on spaces into lines of at most ``width`` characters."""

    words = text.split()
    if not words:
        return [""]
    lines = [words[0]]
    for word in words[1:]:
        candidate = lines[-1] + " " + word
        if len(candidate) <= width:
            lines[-1] = candidate
        else:
            lines.append(word)
    return lines


def json_tree(value: Any) -> dict[str, Any]:
    """A JsonValue as a tree a renderer draws structurally."""

    if isinstance(value, dict):
        return {
            "kind": "object",
            "entries": [
                [str(key), json_tree(item)] for key, item in sorted(value.items())
            ],
        }
    if isinstance(value, (list, tuple)):
        return {"kind": "array", "items": [json_tree(item) for item in value]}
    if value is None:
        return {"kind": "scalar", "text": "null", "tone": "muted"}
    if isinstance(value, bool):
        return {
            "kind": "scalar",
            "text": "true" if value else "false",
            "tone": "bool",
        }
    if isinstance(value, (int, float)):
        return {"kind": "scalar", "text": str(value), "tone": "number"}
    return {"kind": "scalar", "text": str(value)}


def _protocol_record(runs: list[EvaluationRun]) -> list[list[str]]:
    """What the runs of one protocol actually measured."""
    rows: list[list[str]] = []
    if not runs:
        return rows
    rows.append(["runs", str(len(runs))])
    methods: Counter[str] = Counter()
    populations: Counter[str] = Counter()
    best: dict[str, tuple[float, str]] = {}
    for run in runs:
        result = run.result if isinstance(run.result, dict) else {}
        method = result.get("method")
        if isinstance(method, str) and method:
            methods[method] += 1
        population = result.get("protocol")
        if isinstance(population, str) and population:
            populations[population] += 1
        metrics = result.get("metrics")
        if isinstance(metrics, dict):
            for key, label in (
                ("macro_auprc", "best macro"),
                ("micro_auprc", "best micro"),
            ):
                value = metrics.get(key)
                if not isinstance(value, (int, float)):
                    continue
                name = str(method or run.title)
                if key not in best or value > best[key][0]:
                    best[key] = (float(value), name)
    if methods:
        items = ", ".join(
            f"{name} ({count})" for name, count in methods.most_common(6)
        )
        if len(methods) > 6:
            items += f", +{len(methods) - 6} more"
        rows.append(["methods", items])
    if populations:
        label, count = populations.most_common(1)[0]
        text = label
        if len(populations) > 1:
            text += f" · {len(populations) - 1} variants"
        rows.append(["population", text])
    for key, label in (("macro_auprc", "best macro"), ("micro_auprc", "best micro")):
        found = best.get(key)
        if found is not None:
            rows.append([label, f"{found[0]:.4f} — {found[1]}"])
    return rows


def _structured(
    event: Event, codes: dict[str, str], runs: list[EvaluationRun] | None = None
) -> dict[str, Any]:
    """The event's own fields as labelled rows."""

    rows: list[list[Any]] = []

    def add(label: str, value: Any) -> None:
        if value is None or value == "" or value == [] or value == {}:
            return
        rows.append([label, json_tree(value)])

    if isinstance(event, ProposalCreated):
        add("based on", codes.get(event.based_revision, event.based_revision))
        add("rationale", event.rationale)
        add("change", event.change)
    elif isinstance(event, RevisionCreated):
        description = event.description if isinstance(event.description, dict) else {}
        add(
            "implements",
            ", ".join(codes.get(item, item) for item in event.based_proposals),
        )
        add("numbers", description.get("numbers"))
        add("status", description.get("status"))
        add("detail", description.get("detail"))
    elif isinstance(event, FindingCreated):
        add("observation", event.observation)
        add("evidence", event.evidence)
        add("metric", event.metric)
    elif isinstance(event, FindingWithdrawal):
        add("withdraws", codes.get(event.withdrawn_finding, event.withdrawn_finding))
        add("reason", event.reason)
    elif isinstance(event, ProposalWithdrawal):
        add("withdraws", codes.get(event.withdrawn_proposal, event.withdrawn_proposal))
        add("reason", event.reason)
    elif isinstance(event, EvaluationWithdrawal):
        add(
            "withdraws",
            codes.get(event.withdrawn_evaluation, event.withdrawn_evaluation),
        )
        add("reason", event.reason)
    elif isinstance(event, EvaluationCreated):
        add("method", event.method)
        add("metric", event.metric)
        for label, value in _protocol_record(runs or []):
            add(label, value)
    elif isinstance(event, EvaluationRun):
        add("runs", codes.get(event.evaluation, event.evaluation))
        add("measures", codes.get(event.evaluated_revision, event.evaluated_revision))
        add("result", event.result)

    if event.references:
        add(
            "references",
            "\n".join(
                f"{ref.linkage_name}  {codes.get(ref.linked_event, ref.linked_event)}"
                for ref in event.references
            ),
        )
    if event.external_references:
        add(
            "sources",
            "\n".join(
                f"{ref.type}  {ref.name}" for ref in event.external_references
            ),
        )

    return {
        "id": event.id,
        "code": event.code,
        "type": event.event_type,
        "when": _when(event.created_time),
        "title": str(event.title or ""),
        "rows": rows,
    }


def _when(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


def _size_of(event: RevisionCreated) -> str:
    """The build's graph size, when its record states one."""

    numbers = (
        event.description.get("numbers")
        if isinstance(event.description, dict)
        else None
    )
    if not numbers:
        return ""
    text = str(numbers)
    nodes, edges = NODES.search(text), EDGES.search(text)
    if nodes and edges:
        return f"{nodes.group(1)} nodes · {edges.group(1)} edges"
    return _short(text.split(";")[0], 36)


def _counts(events: list[Event]) -> list[dict[str, Any]]:
    """One line per event type, in a fixed order and with its noun."""

    tally = Counter(NOUN[event.event_type] for event in events if event.event_type in NOUN)
    return [
        {"noun": noun, "text": _plural(noun, tally[noun])}
        for noun in COUNT_ORDER
        if tally[noun]
    ]


def _height(title_lines: int, counts: int, evaluated: bool) -> int:
    return 34 + (title_lines - 1) * 10 + counts * 10 + (10 if evaluated else 0)


def _tip(events: list[Event]) -> str:
    if not events:
        return "No event sits on this link."
    lines = [
        f"{event.code}  {event.event_type}\n    {_short(str(event.title or ''), 66)}"
        for event in events[:14]
    ]
    if len(events) > 14:
        lines.append(f"… {len(events) - 14} more")
    return "\n".join(lines)


def _group(event_type: str) -> str:
    if event_type.endswith(".withdrawal"):
        return "withdrawal"
    return event_type.split(".", 1)[0]


def lineage(events: list[Event], *, focus: str | None = None) -> dict[str, Any]:
    """The revision DAG, its collapsed counts and one focused diff.

    ``focus`` names a revision id; the result then carries that revision's
    dependency graph. Without it the result carries only the spine, so a
    consumer asks for a diff when the reader opens one.
    """

    by_id = {event.id: event for event in events}
    codes = {event.id: event.code for event in events}
    revisions = sorted(
        (event for event in events if isinstance(event, RevisionCreated)),
        key=lambda event: event.created_time,
    )
    beginning = next(
        (event for event in events if isinstance(event, Beginning)), None
    )
    stops = {event.id for event in revisions}
    if beginning is not None:
        stops.add(beginning.id)

    edges_out: dict[str, list[str]] = defaultdict(list)
    link_labels: dict[tuple[str, str], str] = {}
    link_kinds: dict[tuple[str, str], str] = {}
    for event in events:
        for name, target in typed_links(event):
            edges_out[event.id].append(target)
            link_labels[(event.id, target)] = name
            link_kinds[(event.id, target)] = "typed"
        for reference in event.references:
            edges_out[event.id].append(reference.linked_event)
            link_labels[(event.id, reference.linked_event)] = reference.linkage_name
            link_kinds[(event.id, reference.linked_event)] = "reference"

    def expand(start: str) -> set[str]:
        """Every non-revision event reachable from ``start`` before a build."""

        seen: set[str] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            for nxt in edges_out.get(node, []):
                if nxt in stops or nxt in seen:
                    continue
                seen.add(nxt)
                stack.append(nxt)
        return seen

    runs_by_revision: dict[str, list[EvaluationRun]] = defaultdict(list)
    for event in events:
        if isinstance(event, EvaluationRun):
            runs_by_revision[event.evaluated_revision].append(event)

    # A link is one implemented proposal: its build of origin, the build that
    # implements it, and everything the proposal was built from. That whole
    # set is the collapsed node the card counts.
    links: dict[tuple[str, str], set[str]] = {}
    for child in revisions:
        for proposal_id in child.based_proposals:
            proposal = by_id.get(proposal_id)
            if not isinstance(proposal, ProposalCreated):
                continue
            base = proposal.based_revision
            if base not in stops:
                continue
            links.setdefault((base, child.id), set()).update(
                {proposal_id} | expand(proposal_id)
            )

    children: dict[str, list[str]] = defaultdict(list)
    for base, child in links:
        children[base].append(child)
    incoming: dict[str, set[str]] = defaultdict(set)
    for (_, child), through in links.items():
        incoming[child] |= through
    dangling = {
        revision.id
        for revision in revisions
        if not children.get(revision.id) and revision is not revisions[-1]
    }

    newest = revisions[-1].id if revisions else None
    spine: list[Event] = []
    if beginning is not None:
        spine.append(beginning)
    spine.extend(revisions)

    nodes: list[dict[str, Any]] = []
    for event in spine:
        size = _size_of(event) if isinstance(event, RevisionCreated) else ""
        if isinstance(event, Beginning):
            kind = "beginning"
        elif event.id in dangling:
            kind = "dangling"
        elif event.id == newest:
            kind = "latest"
        else:
            kind = "revision"
        detail = (
            f"{event.code}  {event.event_type}\n"
            f"    {_short(str(event.title or ''), 66)}\n"
            f"    {_when(event.created_time)}"
        )
        if size:
            detail += f"\n    {size}"
        if event.external_references:
            detail += "\n    source: " + "; ".join(
                f"{reference.type} {reference.name}"
                for reference in event.external_references
            )
        if event.id in dangling:
            detail += "\n\nDangling: no revision descends from this one."
        elif event.id == newest:
            detail += "\n\nLatest revision."
        collapsed = sorted(
            (by_id[item] for item in incoming.get(event.id, set())),
            key=lambda item: (item.created_time, item.code),
        )
        lines = _counts(collapsed)
        title_lines = _wrap(str(event.title or ""))
        evaluations = [
            run.code
            for run in sorted(
                runs_by_revision.get(event.id, []),
                key=lambda item: item.created_time,
            )
        ]
        nodes.append(
            {
                "id": event.id,
                "code": event.code,
                "type": event.event_type,
                "kind": kind,
                "when": _when(event.created_time),
                "title": str(event.title or ""),
                "title_lines": title_lines,
                "counts": lines,
                "evaluations": evaluations,
                "h": _height(len(title_lines), len(lines), bool(evaluations)),
                "detail": detail,
            }
        )

    edges: list[dict[str, Any]] = []
    for (base, child), through in links.items():
        collapsed = sorted(
            (by_id[item] for item in through),
            key=lambda event: (event.created_time, event.code),
        )
        edges.append(
            {
                "from": base,
                "to": child,
                "label": ", ".join(line["text"] for line in _counts(collapsed)),
                "kind": "typed",
                "detail": _tip(collapsed),
                "count": len(collapsed),
            }
        )
    for event in spine:
        for reference in event.references:
            target = by_id.get(reference.linked_event)
            if isinstance(target, (RevisionCreated, Beginning)):
                edges.append(
                    {
                        "from": event.id,
                        "to": target.id,
                        "label": reference.linkage_name,
                        "kind": "reference",
                        "detail": f"{reference.linkage_name}  {target.code}",
                        "count": 0,
                    }
                )

    runs_by_evaluation: dict[str, list[EvaluationRun]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    for event in events:
        if not isinstance(event, EvaluationRun):
            continue
        targets = [event.evaluation]
        targets += [
            reference.linked_event
            for reference in event.references
            if reference.linkage_name == "design"
        ]
        for target in targets:
            if event.id in seen[target]:
                continue
            seen[target].add(event.id)
            runs_by_evaluation[target].append(event)
    details = {
        event.id: _structured(event, codes, runs_by_evaluation.get(event.id, []))
        for event in events
    }
    result: dict[str, Any] = {
        "nodes": nodes,
        "edges": edges,
        "collapsed": len(set().union(*links.values())) if links else 0,
        "details": details,
        "summary": _summary(nodes, edges, links),
    }
    if focus is not None and focus in stops:
        result["focus"] = _focused(
            focus,
            by_id=by_id,
            edges_out=edges_out,
            link_labels=link_labels,
            link_kinds=link_kinds,
            stops=stops,
            runs_by_revision=runs_by_revision,
            details=details,
        )
    return result


def _summary(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]], links: dict[Any, Any]
) -> str:
    revisions = len([node for node in nodes if node["kind"] != "beginning"])
    dangling = len([node for node in nodes if node["kind"] == "dangling"])
    collapsed = len(set().union(*links.values())) if links else 0
    return (
        f"{revisions} revisions · {len(edges)} links · "
        f"{dangling} dangling · {collapsed} events collapsed"
    )


def _focused(
    revision_id: str,
    *,
    by_id: dict[str, Event],
    edges_out: dict[str, list[str]],
    link_labels: dict[tuple[str, str], str],
    link_kinds: dict[tuple[str, str], str],
    stops: set[str],
    runs_by_revision: dict[str, list[EvaluationRun]],
    details: dict[str, Any],
) -> dict[str, Any]:
    """Everything the selected revision depends on, stopping at a revision.

    The selected build is the root. Runs that measured it and the protocol each
    run used hang below it as the outcome branch; external references hang off
    the member that carries them. Every edge points from the dependency to the
    event that uses it, so the graph reads upward into the selected revision.
    """

    members = {revision_id}
    stack = [revision_id]
    pairs: set[tuple[str, str, str, str]] = set()
    while stack:
        node_id = stack.pop()
        for target in edges_out.get(node_id, []):
            label = link_labels.get((node_id, target), "")
            kind = link_kinds.get((node_id, target), "typed")
            # The focused graph reads in the same direction as the lineage:
            # from the dependency it needs to the event that needs it.
            pairs.add((target, node_id, label, kind))
            if target in members:
                continue
            members.add(target)
            if target in stops:
                continue
            stack.append(target)

    nodes: list[dict[str, Any]] = []

    def add(event: Event, group: str) -> None:
        title_lines = _wrap(str(event.title or ""))
        nodes.append(
            {
                "id": event.id,
                "code": event.code,
                "type": event.event_type,
                "group": group,
                "when": _when(event.created_time),
                "title": str(event.title or ""),
                "title_lines": title_lines,
                "h": _height(len(title_lines), 0, False),
            }
        )

    for member in members:
        event = by_id[member]
        add(event, _group(event.event_type))

    edges: list[dict[str, Any]] = [
        {"from": source, "to": target, "label": label, "kind": kind}
        for source, target, label, kind in sorted(pairs)
        if source in members and target in members
    ]

    known = {node["id"] for node in nodes}
    for run in sorted(
        runs_by_revision.get(revision_id, []), key=lambda item: item.created_time
    ):
        if run.id not in known:
            add(run, "evaluation")
            known.add(run.id)
            edges.append(
                {
                    "from": run.id,
                    "to": revision_id,
                    "label": "measures",
                    "kind": "outcome",
                }
            )
        protocol = by_id.get(run.evaluation)
        if isinstance(protocol, EvaluationCreated) and protocol.id not in known:
            add(protocol, "evaluation")
            known.add(protocol.id)
            edges.append(
                {
                    "from": protocol.id,
                    "to": run.id,
                    "label": "runs",
                    "kind": "typed",
                }
            )

    for member in members:
        event = by_id[member]
        for index, reference in enumerate(event.external_references):
            ext_id = f"ext:{event.id}:{index}"
            title_lines = _wrap(reference.name)
            nodes.append(
                {
                    "id": ext_id,
                    "code": reference.type,
                    "type": "external",
                    "group": "external",
                    "when": "",
                    "title": reference.name,
                    "title_lines": title_lines,
                    "h": _height(len(title_lines), 0, False),
                }
            )
            edges.append(
                {
                    "from": ext_id,
                    "to": event.id,
                    "label": reference.type,
                    "kind": "external",
                }
            )
            details[ext_id] = {
                "id": ext_id,
                "code": reference.type,
                "type": "external_reference",
                "when": "",
                "title": reference.name,
                "rows": [
                    ["attached to", json_tree(event.code)],
                    ["type", json_tree(reference.type)],
                    ["name", json_tree(reference.name)],
                    ["detail", json_tree(reference.detail)],
                ],
            }

    return {"nodes": nodes, "edges": edges}


__all__ = ["CARD_W", "TITLE_WRAP", "json_tree", "lineage"]
