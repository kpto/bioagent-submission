from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from kg_build_system.cli.service._private.console import (
    _snapshot,
    _urls,
    config_payload,
    relations_payload,
    revision_payload,
)
from kg_build_system.iteration import (
    Beginning,
    EvaluationCreated,
    EvaluationRun,
    EventReference,
    ExternalReference,
    FindingCreated,
    ProposalCreated,
    RevisionCreated,
    append_event,
    new_event_id,
)

T = datetime(2026, 11, 19, 12, tzinfo=UTC)


def _seed(root: Path) -> dict[str, str]:
    beginning = Beginning(
        id=new_event_id(), code="BEGIN-1", subject="BEGIN-1",
        created_time=T, title="Beginning",
    )
    append_event(root, beginning)
    finding = FindingCreated(
        id=new_event_id(), code="F-1", subject="F-1",
        created_time=T + timedelta(seconds=1), title="A site is hot",
        observation="One site is hot.", evidence="row 42",
        external_references=[
            ExternalReference(type="file", name="audit.log", detail={"line": 4})
        ],
    )
    append_event(root, finding)
    proposal = ProposalCreated(
        id=new_event_id(), code="P-1", subject="edge:x",
        created_time=T + timedelta(seconds=2), title="Add a frame",
        rationale="It gives the edge a purpose.", based_revision=beginning.id,
        references=[EventReference(linkage_name="rests_on", linked_event=finding.id)],
    )
    append_event(root, proposal)
    revision = RevisionCreated(
        id=new_event_id(), code="B-1", subject="B-1",
        created_time=T + timedelta(seconds=3), title="First revision",
        based_proposals=[proposal.id],
        description={
            "message": "first",
            "numbers": "9,519 nodes / 37,325 edges; 46,844 rows",
            "detail": "Added a frame to the edge.",
        },
    )
    append_event(root, revision)
    protocol = EvaluationCreated(
        id=new_event_id(), code="E-1", subject="E-1",
        created_time=T + timedelta(seconds=4), title="Protocol",
        method="project evaluation gates",
    )
    append_event(root, protocol)
    append_event(
        root,
        EvaluationRun(
            id=new_event_id(), code="EV-1", subject="B-1",
            created_time=T + timedelta(seconds=5), title="Run B-1",
            evaluation=protocol.id, evaluated_revision=revision.id,
            result={"gates": {"audit": "passed", "counts": [1, 2]}},
        ),
    )
    return {
        "beginning": beginning.id,
        "finding": finding.id,
        "proposal": proposal.id,
        "revision": revision.id,
    }


def test_the_catalog_is_derived_from_events(tmp_path: Path) -> None:
    _seed(tmp_path)
    payload = relations_payload(tmp_path)
    kinds = {item["kind"] for item in payload["objects"]}
    assert kinds == {
        "finding", "proposal", "revision", "evaluation_design", "evaluation_run",
    }
    revision = next(item for item in payload["objects"] if item["kind"] == "revision")
    assert revision["id"] == "B-1"
    assert revision["links"] == [
        {"id": "P-1", "kind": "proposal", "role": "implements"}
    ]
    run = next(item for item in payload["objects"] if item["kind"] == "evaluation_run")
    assert {link["role"] for link in run["links"]} == {"measures", "runs"}
    assert payload["timeline"][-1]["type"] == "evaluation.run"


def test_the_revision_lineage_collapses_the_events_a_build_consumed(
    tmp_path: Path,
) -> None:
    _seed(tmp_path)
    payload = revision_payload(tmp_path)
    assert [node["code"] for node in payload["nodes"]] == ["BEGIN-1", "B-1"]
    latest = next(node for node in payload["nodes"] if node["kind"] == "latest")
    assert latest["code"] == "B-1"
    assert latest["counts"] == [
        {"noun": "finding", "text": "1 finding"},
        {"noun": "proposal", "text": "1 proposal"},
    ]
    assert latest["evaluations"] == ["EV-1"]
    edge = payload["edges"][0]
    assert (edge["from"], edge["to"]) == (
        payload["nodes"][0]["id"],
        latest["id"],
    )
    assert edge["label"] == "1 finding, 1 proposal"
    assert "31 revisions" not in payload["summary"]
    assert "1 revisions" in payload["summary"]


def test_the_detail_value_is_a_structure_not_a_string(tmp_path: Path) -> None:
    _seed(tmp_path)
    payload = revision_payload(tmp_path)
    run = next(
        detail
        for detail in payload["details"].values()
        if detail["code"] == "EV-1"
    )
    result = next(value for label, value in run["rows"] if label == "result")
    assert result["kind"] == "object"
    gates = dict(result["entries"])["gates"]
    assert gates["kind"] == "object"
    counts = dict(gates["entries"])["counts"]
    assert counts["kind"] == "array"
    assert [item["text"] for item in counts["items"]] == ["1", "2"]

    revision = next(
        detail
        for detail in payload["details"].values()
        if detail["code"] == "B-1"
    )
    numbers = next(value for label, value in revision["rows"] if label == "numbers")
    assert numbers == {
        "kind": "scalar",
        "text": "9,519 nodes / 37,325 edges; 46,844 rows",
    }


def test_a_focused_diff_stops_at_revisions_and_keeps_references(
    tmp_path: Path,
) -> None:
    ids = _seed(tmp_path)
    payload = revision_payload(tmp_path, focus=ids["revision"])
    focus = payload["focus"]
    codes = {node["code"] for node in focus["nodes"]}
    assert {"B-1", "P-1", "F-1", "EV-1", "E-1", "file"} <= codes
    kinds = {(edge["label"], edge["kind"]) for edge in focus["edges"]}
    assert ("implements", "typed") in kinds
    assert ("based_revision", "typed") in kinds
    assert ("rests_on", "reference") in kinds
    assert ("measures", "outcome") in kinds
    assert ("runs", "typed") in kinds
    assert ("file", "external") in kinds

    by_code = {node["code"]: node["id"] for node in focus["nodes"]}
    implements = next(
        edge for edge in focus["edges"] if edge["label"] == "implements"
    )
    assert (implements["from"], implements["to"]) == (
        by_code["P-1"], by_code["B-1"],
    )
    based = next(
        edge for edge in focus["edges"] if edge["label"] == "based_revision"
    )
    assert (based["from"], based["to"]) == (
        by_code["BEGIN-1"], by_code["P-1"],
    )
    measures = next(
        edge for edge in focus["edges"] if edge["label"] == "measures"
    )
    assert (measures["from"], measures["to"]) == (
        by_code["EV-1"], by_code["B-1"],
    )
    external_edge = next(
        edge for edge in focus["edges"] if edge["kind"] == "external"
    )
    assert (external_edge["from"], external_edge["to"]) == (
        by_code["file"], by_code["F-1"],
    )
    external = next(
        detail
        for detail in payload["details"].values()
        if detail["type"] == "external_reference"
    )
    assert external["rows"][0][1] == {"kind": "scalar", "text": "F-1"}


def test_the_config_names_the_ledger(tmp_path: Path) -> None:
    payload = config_payload(tmp_path)
    assert payload["project"] == tmp_path.name
    assert payload["dataDir"].endswith("journal/events")


def test_the_snapshot_is_resolved_under_the_project_root(tmp_path: Path) -> None:
    build = tmp_path / "data" / "build"
    build.mkdir(parents=True)
    document = {"format": "kg-viewer-snapshot", "version": 1, "workflow": {}}
    (build / "workflow_plan.json").write_text(
        json.dumps(document), encoding="utf-8"
    )
    body, content_type = _snapshot(tmp_path)
    assert content_type == "application/json"
    assert json.loads(body) == document


def test_a_missing_snapshot_serves_the_empty_document(tmp_path: Path) -> None:
    body, _ = _snapshot(tmp_path)
    assert json.loads(body) == {"format": "kg-viewer-snapshot", "version": 1}


def test_a_wildcard_bind_reports_the_local_and_network_addresses() -> None:
    local, network = _urls("0.0.0.0", 8000, "/console/")
    assert local == "http://127.0.0.1:8000/console/"
    assert network is None or network.startswith("http://")


def test_a_named_bind_reports_the_one_address() -> None:
    assert _urls("127.0.0.1", 8000, "/console/") == (
        "http://127.0.0.1:8000/console/",
        None,
    )
