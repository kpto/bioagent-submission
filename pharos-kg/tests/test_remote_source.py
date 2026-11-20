"""The remote source step fetches, verifies and decodes a release."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import duckdb
import pytest

from pharos_kg.modules.remote_source import (
    _decode_hpo,
    _decode_opentargets,
    _download,
)
from tests.support import compile_pharos


def test_the_remote_assets_fetch_before_their_source_steps() -> None:
    plan = compile_pharos()
    steps = {step.name: step for step in plan.steps}
    assert "fetch.hpo" in steps
    assert "fetch.opentargets2609" in steps
    source = steps["source.hpo_term"]
    assert [item.declared_name for item in source.inputs] == ["ready"]
    source_names = [
        step.name for step in plan.steps if step.name.startswith("source.")
    ]
    assert len(source_names) == len(set(source_names))


def test_the_plan_records_the_release_configuration() -> None:
    plan = compile_pharos()
    steps = {step.name: step for step in plan.steps}
    payload = steps["fetch.hpo"].instruction.payload
    release = payload["release"]
    assert release["reader"] == "hpo"
    assert {table["relation"] for table in release["tables"]} == {
        "hpo_term",
        "hpo_disease_phenotype",
        "hpo_gene_phenotype",
        "mondo_xref",
    }
    assert any(
        file["file"] == "hp.obo" and len(file["sha256"]) == 64
        for file in release["files"]
    )
    assert payload["cache"].endswith("data/source/hpo")
    assert payload["members"]["hpo_term"] == "hp_term.parquet"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_download_reuses_a_verified_file_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"release bytes"
    release = {
        "files": [{
            "dataset": "hpo",
            "file": "hp.obo",
            "url": "https://example.invalid/hp.obo",
            "bytes": len(payload),
            "sha256": _digest(payload),
        }],
    }
    seeded = tmp_path / "hpo" / "hp.obo"
    seeded.parent.mkdir(parents=True)
    seeded.write_bytes(payload)

    def refuse(*_args: object, **_kwargs: object) -> None:
        pytest.fail("a verified file was downloaded again")

    monkeypatch.setattr("pharos_kg.modules.remote_source.urlopen", refuse)
    found = _download(release, tmp_path)
    assert found["hpo"]["hp.obo"] == seeded


def test_download_refuses_a_release_that_moved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = {
        "files": [{
            "dataset": "hpo",
            "file": "hp.obo",
            "url": "https://example.invalid/hp.obo",
            "bytes": 6,
            "sha256": _digest(b"good"),
        }],
    }

    def moved(_url: str, timeout: int = 0) -> io.BytesIO:
        return io.BytesIO(b"moved!")

    monkeypatch.setattr("pharos_kg.modules.remote_source.urlopen", moved)
    with pytest.raises(RuntimeError, match="pinned digest"):
        _download(release, tmp_path)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_hpo_decode_reproduces_the_declared_reading(tmp_path: Path) -> None:
    sources = tmp_path / "sources"
    _write(sources / "hp.obo", """format-version: 1.2
[Term]
id: HP:0000001
name: All

[Term]
id: HP:0000002
name: Old term
is_obsolete: true

[Term]
id: HP:0000003
name: Height
""")
    _write(sources / "mondo.obo", """[Term]
id: MONDO:0000001
xref: OMIM:100
xref: Orphanet:5

[Term]
id: MONDO:0000002
xref: DOID:4
""")
    _write(sources / "phenotype.hpoa", """#description: fixture
#version: fixture
#tracker: fixture
#date: fixture
DatabaseID\tDiseaseName\tQualifier\tHPO_ID\tReference\tEvidence\tOnset\tFrequency\tSex\tModifier\tAspect\tBiocuration
OMIM:1\tOne\t\tHP:0000003\tOMIM:1\tTAS\t\t1/2\t\t\tP\tcurator
OMIM:1\tOne\tNOT\tHP:0000001\tOMIM:1\tIEA\t\t\t\t\tP\tcurator
""")
    _write(sources / "genes_to_phenotype.txt",
           "ncbi_gene_id\tgene_symbol\thpo_id\thpo_name\tfrequency\tdisease_id\n"
           "10\tGENE\tHP:0000003\tHeight\t-\tOMIM:1\n")
    cache = tmp_path / "cache"
    cache.mkdir()
    tables = {
        "hp_term.parquet": {"rows": 2},
        "mondo_xref.parquet": {"rows": 2},
        "disease_phenotype.parquet": {"rows": 2},
        "gene_phenotype.parquet": {"rows": 1},
    }
    _decode_hpo(
        {"hpo": {path.name: path for path in sources.iterdir()}},
        cache,
        set(tables),
        tables,
    )
    connection = duckdb.connect()
    try:
        assert connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY hpo_id",
            [str(cache / "hp_term.parquet")],
        ).fetchall() == [
            ("HP:0000001", "All"),
            ("HP:0000003", "Height"),
        ]
        assert connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY source_id",
            [str(cache / "mondo_xref.parquet")],
        ).fetchall() == [
            ("OMIM:100", "MONDO:0000001"),
            ("ORPHA:5", "MONDO:0000001"),
        ]
        assert connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY hpo_id",
            [str(cache / "disease_phenotype.parquet")],
        ).fetchall() == [
            ("OMIM:1", "NOT", "HP:0000001", "IEA", ""),
            ("OMIM:1", "", "HP:0000003", "TAS", "1/2"),
        ]
        assert connection.execute(
            "SELECT * FROM read_parquet(?)",
            [str(cache / "gene_phenotype.parquet")],
        ).fetchall() == [(10, "HP:0000003", "-", "OMIM:1")]
    finally:
        connection.close()


def test_opentargets_decode_projects_and_unnests(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    for name in ("association_by_datatype_direct", "target", "disease"):
        (raw / name).mkdir(parents=True)
    connection = duckdb.connect()
    try:
        connection.execute(
            "CREATE TABLE association (diseaseId VARCHAR, targetId VARCHAR, "
            "aggregationType VARCHAR, aggregationValue VARCHAR, "
            "associationScore DOUBLE, evidenceCount BIGINT)"
        )
        connection.executemany(
            "INSERT INTO association VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("MONDO_1", "ENSG1", "datatypeId", "literature", 0.5, 2),
                ("MONDO_1", "ENSG1", "overall", "overall", 0.9, 3),
            ],
        )
        connection.execute(
            f"COPY association TO '{raw / 'association_by_datatype_direct' / 'part.parquet'}'"
            " (FORMAT PARQUET)"
        )
        connection.execute(
            "CREATE TABLE target (id VARCHAR, proteinIds STRUCT(id VARCHAR, source VARCHAR)[])"
        )
        connection.execute(
            "INSERT INTO target VALUES ('ENSG1', [{'id': 'P1', 'source': 'uniprot'}, "
            "{'id': 'P2', 'source': 'trembl'}])"
        )
        connection.execute(
            f"COPY target TO '{raw / 'target' / 'part.parquet'}' (FORMAT PARQUET)"
        )
        connection.execute("CREATE TABLE disease (id VARCHAR, name VARCHAR)")
        connection.execute("INSERT INTO disease VALUES ('MONDO_1', 'One')")
        connection.execute(
            f"COPY disease TO '{raw / 'disease' / '00000000.parquet'}' (FORMAT PARQUET)"
        )
    finally:
        connection.close()

    cache = tmp_path / "cache"
    cache.mkdir()
    tables = {
        "association.parquet": {"rows": 1},
        "target_protein.parquet": {"rows": 2},
        "disease.parquet": {"rows": 1},
    }
    _decode_opentargets(
        {
            name: {path.name: path for path in (raw / name).iterdir()}
            for name in ("association_by_datatype_direct", "target", "disease")
        },
        cache,
        set(tables),
        tables,
    )
    connection = duckdb.connect()
    try:
        assert connection.execute(
            "SELECT * FROM read_parquet(?)",
            [str(cache / "association.parquet")],
        ).fetchall() == [("MONDO:1", "ENSG1", "literature", 0.5, 2)]
        assert connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY protein_id",
            [str(cache / "target_protein.parquet")],
        ).fetchall() == [
            ("ENSG1", "P1", "uniprot"),
            ("ENSG1", "P2", "trembl"),
        ]
        assert connection.execute(
            "SELECT * FROM read_parquet(?)",
            [str(cache / "disease.parquet")],
        ).fetchall() == [("MONDO:1", "One")]
    finally:
        connection.close()
