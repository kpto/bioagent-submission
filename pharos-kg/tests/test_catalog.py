"""The console catalog is the ledger read as objects and as a timeline."""

from __future__ import annotations

from pathlib import Path

from kg_build_system.cli.service._private.console import relations_payload
from kg_build_system.iteration import load_ledger

ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict:
    return relations_payload(ROOT)


def test_the_catalog_and_timeline_read_the_whole_ledger() -> None:
    payload = _payload()
    assert len(payload["timeline"]) == len(load_ledger(ROOT))
    assert {item["kind"] for item in payload["objects"]} == {
        "finding",
        "proposal",
        "revision",
        "evaluation_design",
        "evaluation_run",
    }
    assert payload["objects"]


def test_catalog_links_resolve_within_the_catalog() -> None:
    payload = _payload()
    identifiers = {item["id"] for item in payload["objects"]}
    for item in payload["objects"]:
        assert item["title"]
        assert item["created"]
        for link in item["links"]:
            # The beginning is the root of the graph, not a catalog object.
            assert link["id"] in identifiers or link["id"] == "BEGIN-1", (
                item["id"],
                link,
            )


def test_a_revision_object_names_the_proposals_it_implements() -> None:
    payload = _payload()
    revisions = [item for item in payload["objects"] if item["kind"] == "revision"]
    assert revisions
    for revision in revisions:
        assert revision["links"]
        assert {link["role"] for link in revision["links"]} == {"implements"}
        assert {link["kind"] for link in revision["links"]} == {"proposal"}


def test_the_timeline_is_chronological() -> None:
    payload = _payload()
    stamps = [item["timestamp"] for item in payload["timeline"]]
    assert stamps == sorted(stamps)
