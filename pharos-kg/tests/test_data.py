"""Contract tests for the pinned dump and the graph it produces.

The asset is the MySQL dump; ``data/source/pharos319`` is one reading of it.
The archive digest is declared in ``pharos_kg/asset/pharos_source.py``; the
cache is disposable and rebuilds from that declaration. These tests skip when
the cache is absent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pharos_kg.asset.pharos_source import ARCHIVE_BYTES, ARCHIVE_SHA256, PharosDump
from pharos_kg.modules.dump_source import _cache_is_current

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source" / "pharos319"
GRAPH = ROOT / "build" / "graph.jsonl"

pytestmark = pytest.mark.skipif(
    not (CACHE / "target.parquet").exists(),
    reason="the pinned dump cache is absent; the build's dump step fetches it",
)


def _records() -> list[dict]:
    if not GRAPH.exists():
        pytest.skip("run `kbs run --project pharos_kg` first")
    return [
        json.loads(line)
        for line in GRAPH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_the_declared_archive_and_the_read_tables() -> None:
    assert len(ARCHIVE_SHA256) == 64
    assert ARCHIVE_BYTES == 2_257_847_063
    layout = PharosDump.options.layout
    assert layout is not None
    for member in layout.members.values():
        assert (CACHE / f"{member}.parquet").exists(), member


def test_every_cached_table_has_a_marker() -> None:
    for path in sorted(CACHE.glob("*.parquet")):
        assert _cache_is_current(path, ARCHIVE_SHA256), path.name


def test_kinase_slice_is_the_kinase_family() -> None:
    import duckdb

    con = duckdb.connect()
    count = con.execute(
        f"SELECT count(*) FROM read_parquet('{CACHE}/target.parquet') "
        "WHERE fam = 'Kinase'"
    ).fetchone()[0]
    assert count == 635
    linked = con.execute(
        f"""SELECT count(DISTINCT tp.target_id)
            FROM read_parquet('{CACHE}/t2tc.parquet') tp
            JOIN read_parquet('{CACHE}/target.parquet') t ON t.id = tp.target_id
            WHERE t.fam = 'Kinase'"""
    ).fetchone()[0]
    assert linked == 635


def test_every_edge_endpoint_resolves() -> None:
    records = _records()
    nodes = {row["build_key"] for row in records if row["kind"] == "node"}
    dangling = [
        row["build_key"]
        for row in records
        if row["kind"] == "edge"
        and (
            row["source_build_key"] not in nodes
            or row["target_build_key"] not in nodes
        )
    ]
    assert dangling == []


def test_disease_keys_prefer_a_curie() -> None:
    diseases = [
        row["build_key"]
        for row in _records()
        if row["kind"] == "node" and row["type"] == "disease"
    ]
    curies = [key for key in diseases if key.startswith(("MONDO:", "DOID:"))]
    assert len(curies) / max(1, len(diseases)) > 0.5


def test_every_binding_edge_has_a_measurement_summary() -> None:
    for row in _records():
        if row["kind"] == "edge" and row["type"] == "binds":
            assert isinstance(row["count"], int)
            assert row["count"] >= 0
            assert "mean_p_activity" in row
