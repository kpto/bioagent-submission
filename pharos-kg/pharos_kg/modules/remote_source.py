"""Fetch and cache a release published as files, then read its declared tables.

The Pharos dump is one archive; the HPO and Open Targets assets are releases
published as several files. This module is their source step. It keeps the
declared reading in the asset's cache, downloads the pinned release only when a
table is missing, verifies every source file against the digest the asset
declaration records, and decodes the release into the parquet tables the asset
declares. The framework's source step still performs the scan.

The release is declared beside the asset, not in a data-side manifest, and the
module's configuration is written into the instruction payload so the workflow
plan records exactly what will be fetched, verified and decoded.

The decode is the asset's declared reading, not a graph transformation: the
declaration states the columns, the projection and the reader's assumptions. The
graph relations still select, join and aggregate after this step.

A cache that is present is authoritative: the module does not download, and it
does not rewrite a table. A rebuild after a deleted cache verifies the release
bytes and the resulting row counts; a release whose bytes moved is refused, so a
re-decode cannot silently describe a different release.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, cast
from urllib.request import urlopen

from kg_build_system.distribution.modules.duckdb import DuckDbSourcePlanner
from kg_build_system.distribution.modules.runtime import (
    instruction_payload,
    skipped,
    succeeded,
)
from kg_build_system.distribution.service.public import asset_tables
from kg_build_system.kernel import (
    ArtifactPattern,
    ArtifactType,
    DisruptedExecutionContext,
    ExecutionContext,
    Input,
    Instruction,
    InstructionKind,
    Output,
    Step,
)

from pharos_kg.asset.release import Release

FETCH = InstructionKind("remote_source", "files")
# The component is this module's own name, not the framework's generic source
# slot. DefaultToolchain has no explicit source-planner option, so manifest.py
# removes the generic DuckDbSourcePlanner after composition; see the workaround
# note there.
COMPONENT = "remote_source"
READY = "remote_source"
HPO = "hpo"
OPENTARGETS = "opentargets"
DOWNLOAD_TIMEOUT = 120
BLOCK = 1 << 20


@dataclass(frozen=True, slots=True)
class RemoteSourceConfiguration:
    """The module's declared input: one asset and the release it reads."""

    asset: str
    release: Release

    def to_document(self) -> dict[str, Any]:
        return {"asset": self.asset, "release": self.release.to_document()}


def _asset_cache_members(
    blueprint: Any, name: str,
) -> tuple[Path, dict[str, str]]:
    """Resolve the cache directory and member files from the asset declaration."""
    for table in asset_tables(blueprint):
        layout = table.asset.layout
        if table.asset.name != name or layout is None or not layout.locator:
            continue
        return Path(layout.locator), {
            str(relation): str(file)
            for relation, file in dict(layout.members).items()
        }
    raise ValueError(
        f"{name}: the asset declares no cache locator and members"
    )


class RemoteSourcePlanner:
    """Plan one fetch step and make the asset's source steps wait for it."""

    component_id = COMPONENT
    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def __init__(self, configuration: RemoteSourceConfiguration) -> None:
        self.configuration = configuration

    def plan(self, model: Any, context: Any) -> tuple[Step, ...]:
        cache, members = _asset_cache_members(model, self.configuration.asset)
        ready = ArtifactType.of(READY, self.configuration.asset)
        fetch = Step(
            component=self.component_id,
            name=f"fetch.{self.configuration.asset}",
            inputs=(),
            outputs=(Output(ready),),
            instruction=Instruction(FETCH, cast(Any, {
                **self.configuration.to_document(),
                "cache": str(cache),
                "members": members,
            })),
        )
        steps: list[Step] = [fetch]
        for step in DuckDbSourcePlanner().plan(model, context):
            relation = step.name.removeprefix("source.")
            if relation not in members:
                continue
            steps.append(replace(
                step,
                inputs=(
                    Input(
                        ArtifactPattern.of(
                            READY, self.configuration.asset,
                        ),
                        None,
                        "ready",
                    ),
                ),
            ))
        return tuple(steps)


class RemoteSourceExecutor:
    """Download a release when a table is missing, verify it, and decode it."""

    kinds: tuple[InstructionKind, ...] = (FETCH,)
    resources: tuple[Any, ...] = ()

    def execute(
        self,
        context: ExecutionContext | DisruptedExecutionContext,
        instruction: Instruction,
    ) -> Any:
        if isinstance(context, DisruptedExecutionContext):
            return skipped(context)
        payload = instruction_payload(instruction)
        cache = Path(str(payload["cache"]))
        declared_members = payload.get("members")
        members: dict[str, str] = {}
        if isinstance(declared_members, Mapping):
            members = {
                str(relation): str(file)
                for relation, file in declared_members.items()
            }
        missing = {
            file for file in members.values() if not (cache / file).is_file()
        }
        if not missing:
            return succeeded(context, {
                "asset": str(payload.get("asset") or ""),
                "rebuilt": [],
                "cached": True,
            })
        release = payload.get("release")
        if not isinstance(release, Mapping):
            raise TypeError("the fetch step declares no release")
        declared_tables = release.get("tables")
        tables: dict[str, Mapping[str, Any]] = {}
        if isinstance(declared_tables, list):
            for table in declared_tables:
                if isinstance(table, Mapping) and "file" in table:
                    tables[str(table["file"])] = table
        sources = _download(release, cache / ".sources")
        reader = str(release.get("reader") or "")
        if reader == HPO:
            _decode_hpo(sources, cache, missing, tables)
        elif reader == OPENTARGETS:
            _decode_opentargets(sources, cache, missing, tables)
        else:
            raise ValueError(f"unknown remote reader {reader!r}")
        return succeeded(context, {
            "asset": str(payload.get("asset") or ""),
            "rebuilt": sorted(missing),
            "cached": False,
        })


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


def _literal(value: Any) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(BLOCK):
            digest.update(block)
    return digest.hexdigest()


def _download(
    release: Mapping[str, Any], root: Path,
) -> dict[str, dict[str, Path]]:
    """Download every release file and return them by dataset and name."""
    found: dict[str, dict[str, Path]] = {}
    for row in release.get("files", ()):
        if not isinstance(row, Mapping):
            continue
        dataset = str(row["dataset"])
        name = str(row["file"])
        url = str(row["url"])
        size = int(row["bytes"])
        digest = str(row["sha256"])
        directory = root / dataset
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / name
        if not (
            target.is_file()
            and target.stat().st_size == size
            and _digest(target) == digest
        ):
            part = target.with_name(target.name + ".part")
            with urlopen(url, timeout=DOWNLOAD_TIMEOUT) as response, part.open(
                "wb"
            ) as handle:
                while block := response.read(BLOCK):
                    handle.write(block)
            if part.stat().st_size != size:
                actual = part.stat().st_size
                part.unlink(missing_ok=True)
                raise RuntimeError(
                    f"{name}: downloaded {actual} bytes, expected {size}"
                )
            if _digest(part) != digest:
                part.unlink(missing_ok=True)
                raise RuntimeError(
                    f"{name}: the release bytes do not match the pinned digest;"
                    " the release moved and this cache cannot be rebuilt from it"
                )
            part.replace(target)
        found.setdefault(dataset, {})[name] = target
    return found


# ---------------------------------------------------------------------------
# HPO
# ---------------------------------------------------------------------------


def _obo_terms(path: Path) -> Iterable[tuple[str, str, bool, tuple[str, ...]]]:
    """Yield (id, name, obsolete, xrefs) for every [Term] block."""
    term_id: str | None = None
    name = ""
    obsolete = False
    xrefs: list[str] = []

    def emit() -> tuple[str, str, bool, tuple[str, ...]] | None:
        if not term_id:
            return None
        return term_id, name or term_id, obsolete, tuple(xrefs)

    with path.open(encoding="utf-8") as handle:
        in_term = False
        for raw in handle:
            line = raw.strip()
            if line == "[Term]":
                if in_term:
                    row = emit()
                    if row:
                        yield row
                term_id, name, obsolete, xrefs = None, "", False, []
                in_term = True
                continue
            if line.startswith("["):
                if in_term:
                    row = emit()
                    if row:
                        yield row
                term_id, name, obsolete, xrefs = None, "", False, []
                in_term = False
                continue
            if not in_term:
                continue
            if line.startswith("id: "):
                term_id = line[4:].strip()
            elif line.startswith("name: "):
                name = line[6:].strip()
            elif line.startswith("is_obsolete: true"):
                obsolete = True
            elif line.startswith("xref: "):
                xrefs.append(line[6:].split(" ", 1)[0])
        if in_term:
            row = emit()
            if row:
                yield row


def _write_rows(
    target: Path,
    columns: tuple[tuple[str, str], ...],
    rows: Iterable[tuple[Any, ...]],
    order_by: str,
) -> None:
    import duckdb

    temp = target.with_name(target.name + ".tmp")
    temp.unlink(missing_ok=True)
    connection = duckdb.connect()
    try:
        shape = ", ".join(f'"{name}" {kind}' for name, kind in columns)
        connection.execute(f"CREATE TABLE rows ({shape})")
        placeholders = ", ".join("?" for _ in columns)
        connection.executemany(f"INSERT INTO rows VALUES ({placeholders})", rows)
        connection.execute(
            f"COPY (SELECT * FROM rows ORDER BY {order_by}) TO {_literal(temp)}"
            " (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        connection.close()
    temp.replace(target)


def _decode_hpo(
    sources: Mapping[str, Mapping[str, Path]],
    cache: Path,
    missing: set[str],
    tables: Mapping[str, Mapping[str, Any]],
) -> None:
    paths = sources.get(HPO, {})
    if "hp_term.parquet" in missing:
        rows = (
            (term_id, name)
            for term_id, name, obsolete, _ in _obo_terms(paths["hp.obo"])
            if not obsolete
        )
        _write_rows(
            cache / "hp_term.parquet",
            (("hpo_id", "VARCHAR"), ("name", "VARCHAR")),
            rows,
            "hpo_id",
        )
    if "mondo_xref.parquet" in missing:
        rows = []
        for mondo_id, _, _, xrefs in _obo_terms(paths["mondo.obo"]):
            for xref in xrefs:
                if xref.startswith("OMIM:"):
                    rows.append((xref, mondo_id))
                elif xref.startswith("Orphanet:"):
                    rows.append(("ORPHA:" + xref.split(":", 1)[1], mondo_id))
        _write_rows(
            cache / "mondo_xref.parquet",
            (("source_id", "VARCHAR"), ("mondo_id", "VARCHAR")),
            sorted(rows),
            "source_id, mondo_id",
        )
    if "disease_phenotype.parquet" in missing:
        _copy(
            cache / "disease_phenotype.parquet",
            f"""SELECT coalesce(column00, '') AS disease_id,
                       coalesce(column02, '') AS qualifier,
                       coalesce(column03, '') AS hpo_id,
                       coalesce(column05, '') AS evidence,
                       coalesce(column07, '') AS frequency
                FROM read_csv({_literal(paths['phenotype.hpoa'])},
                              delim='\\t', header=false, skip=5, all_varchar=true)
                ORDER BY disease_id, hpo_id, evidence, frequency""",
        )
    if "gene_phenotype.parquet" in missing:
        _copy(
            cache / "gene_phenotype.parquet",
            f"""SELECT CAST(ncbi_gene_id AS BIGINT) AS ncbi_gene_id,
                       hpo_id,
                       coalesce(frequency, '') AS frequency,
                       coalesce(disease_id, '') AS disease_id
                FROM read_csv({_literal(paths['genes_to_phenotype.txt'])},
                              delim='\\t', header=true, all_varchar=true)
                ORDER BY ncbi_gene_id, hpo_id, disease_id, frequency""",
        )
    _check_rows(cache, missing, tables)


def _decode_opentargets(
    sources: Mapping[str, Mapping[str, Path]],
    cache: Path,
    missing: set[str],
    tables: Mapping[str, Mapping[str, Any]],
) -> None:
    if "association.parquet" in missing:
        parts = sorted(
            str(path)
            for path in sources.get("association_by_datatype_direct", {}).values()
        )
        _copy(
            cache / "association.parquet",
            f"""SELECT replace(diseaseId, '_', ':') AS disease_id,
                       targetId AS ensembl_id,
                       aggregationValue AS datatype,
                       CAST(associationScore AS DOUBLE) AS score,
                       CAST(evidenceCount AS BIGINT) AS evidence_count
                FROM read_parquet({parts})
                WHERE aggregationType = 'datatypeId'
                ORDER BY disease_id, ensembl_id, datatype""",
        )
    if "target_protein.parquet" in missing:
        parts = sorted(
            str(path) for path in sources.get("target", {}).values()
        )
        _copy(
            cache / "target_protein.parquet",
            f"""SELECT t.id AS ensembl_id,
                       p.id AS protein_id,
                       p.source AS source
                FROM read_parquet({parts}) AS t,
                     unnest(t.proteinIds) AS u(p)
                ORDER BY ensembl_id, protein_id, source""",
        )
    if "disease.parquet" in missing:
        parts = sorted(
            str(path) for path in sources.get("disease", {}).values()
        )
        _copy(
            cache / "disease.parquet",
            f"""SELECT replace(id, '_', ':') AS disease_id, name
                FROM read_parquet({parts})
                ORDER BY disease_id""",
        )
    _check_rows(cache, missing, tables)


def _copy(target: Path, query: str) -> None:
    import duckdb

    temp = target.with_name(target.name + ".tmp")
    temp.unlink(missing_ok=True)
    connection = duckdb.connect()
    try:
        connection.execute(
            f"COPY ({query}) TO {_literal(temp)}"
            " (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        connection.close()
    temp.replace(target)


def _check_rows(
    cache: Path,
    missing: set[str],
    tables: Mapping[str, Mapping[str, Any]],
) -> None:
    """Refuse a decode whose row count does not match the declared reading."""
    import duckdb

    connection = duckdb.connect()
    try:
        for file in sorted(missing):
            expected = tables.get(file, {}).get("rows")
            if expected is None:
                continue
            row = connection.execute(
                f"SELECT count(*) FROM read_parquet({_literal(cache / file)})"
            ).fetchone()
            actual = row[0] if row else 0
            if int(actual) != int(expected):
                raise RuntimeError(
                    f"{file}: decoded {actual} rows, the asset declares {expected}"
                )
    finally:
        connection.close()


__all__ = [
    "FETCH",
    "RemoteSourceConfiguration",
    "RemoteSourceExecutor",
    "RemoteSourcePlanner",
]
