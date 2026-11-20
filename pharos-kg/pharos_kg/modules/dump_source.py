"""A source adapter that decodes the pinned Pharos dump into relations.

The asset is the ``.sql.gz`` archive. This module plans one source step per
table the graph reads and, when the step runs, materialises that table through
the engine's reader - reusing a local Parquet cache when it is present, and
reading the archive when it is not. It keeps the declared schema: no filtering,
identity mapping, joining or aggregation happens here.

The archive URL, byte size and digest are declared in the asset and recorded in
the plan. Every extracted table writes a small cache marker beside it (archive
digest, row count, byte size and digest), so a cache is verified against the
archive it was read from without a data-side manifest.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from kg_build_system.distribution.model.public.artifacts import CoreArtifactTypes
from kg_build_system.distribution.modules.duckdb import DuckDbService
from kg_build_system.distribution.modules.runtime import (
    instruction_payload,
    skipped,
    succeeded,
)
from kg_build_system.distribution.service.public import asset_tables
from kg_build_system.kernel import (
    DisruptedExecutionContext,
    ExecutionContext,
    Instruction,
    InstructionKind,
    Output,
    Step,
)

FORMAT = "mysqldump"
SOURCE_RELATION = InstructionKind("source_relation", FORMAT)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class DumpSourceConfiguration:
    """The declared archive a dump source step may fetch and verify."""

    archive_sha256: str
    archive_bytes: int

    def to_document(self) -> dict[str, Any]:
        return {
            "archive_sha256": self.archive_sha256,
            "archive_bytes": self.archive_bytes,
        }


def _cache_root() -> Path:
    """The adapter's fallback cache when an asset names none."""
    return PROJECT_ROOT / "data" / "source" / "pharos319"


def _digest(path: Path, chunk: int = 1 << 22) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def _marker(cache: Path) -> Path:
    """The cache metadata written beside one extracted table."""
    return cache.with_suffix(".json")


def _cache_is_current(cache: Path, archive_sha256: str) -> bool:
    marker = _marker(cache)
    if not cache.exists() or not marker.exists():
        return False
    document = json.loads(marker.read_text(encoding="utf-8"))
    return (
        document.get("archive_sha256") == archive_sha256
        and document.get("sha256") == _digest(cache)
    )


_DUMP_DIGESTS: dict[tuple[str, int, float], str] = {}


def _dump_digest(dump: Path) -> str:
    key = (str(dump), dump.stat().st_size, dump.stat().st_mtime)
    if key not in _DUMP_DIGESTS:
        _DUMP_DIGESTS[key] = _digest(dump)
    return _DUMP_DIGESTS[key]


def _fetch_archive(
    dump: Path, url: str | None, sha256: str, size: int,
) -> None:
    """Fetch the declared archive and refuse bytes that do not match it."""
    if not url:
        raise FileNotFoundError(
            f"the archive {dump} is absent and the asset names no archive_url"
        )
    dump.parent.mkdir(parents=True, exist_ok=True)
    part = dump.with_name(dump.name + ".part")
    with urlopen(url, timeout=120) as response, part.open("wb") as handle:
        while block := response.read(1 << 20):
            handle.write(block)
    if part.stat().st_size != size:
        actual = part.stat().st_size
        part.unlink(missing_ok=True)
        raise RuntimeError(
            f"{dump.name}: downloaded {actual} bytes, expected {size}"
        )
    if _digest(part) != sha256:
        part.unlink(missing_ok=True)
        raise RuntimeError(
            f"{dump.name}: the archive bytes do not match the pinned digest"
        )
    part.replace(dump)


def _materialise_table(
    dump: Path,
    table: str,
    cache: Path,
    *,
    archive_sha256: str,
    archive_bytes: int,
    url: str | None = None,
) -> Path:
    """Return a Parquet file for one dump table, extracting it if needed."""
    if not dump.exists():
        if cache.exists():
            return cache
        _fetch_archive(dump, url, archive_sha256, archive_bytes)
    if _dump_digest(dump) != archive_sha256:
        raise RuntimeError(
            f"{dump.name}: the archive does not match the pinned digest;"
            " the release moved and this cache cannot be rebuilt from it"
        )
    if _cache_is_current(cache, archive_sha256):
        return cache
    try:
        import chdb  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError(
            f"{table!r}: no usable cache, and this table cannot be rebuilt here."
            " The dump reader is chdb, which publishes no Windows wheel; a"
            " pinned Parquet cache needs no reader. Rebuild on Linux or macOS,"
            " or ship the cache the asset names."
        ) from error
    import pyarrow.parquet as pq  # type: ignore[import-not-found]

    cache.parent.mkdir(parents=True, exist_ok=True)
    literal = "'" + str(dump).replace("'", "''") + "'"
    target = "'" + str(cache).replace("'", "''") + "'"
    chdb.query(
        f"SELECT * FROM file({literal}, MySQLDump) INTO OUTFILE {target} "
        f"FORMAT Parquet SETTINGS input_format_mysql_dump_table_name='{table}', "
        "output_format_parquet_compression_method='zstd'",
        "CSV",
    )
    if not cache.exists():
        raise RuntimeError(f"the reader wrote no table for {table!r}")
    rows = pq.ParquetFile(cache).metadata.num_rows
    _marker(cache).write_text(
        json.dumps({
            "archive_sha256": archive_sha256,
            "archive_bytes": archive_bytes,
            "table": table,
            "rows": rows,
            "bytes": cache.stat().st_size,
            "sha256": _digest(cache),
        }, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return cache


class DumpSourcePlanner:
    """Plan one source step for every dump-backed table the graph reads."""

    component_id = "pharos_dump"
    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def __init__(self, configuration: DumpSourceConfiguration) -> None:
        self.configuration = configuration

    def plan(self, blueprint: Any, context: Any) -> Sequence[Step]:
        del context
        steps: list[Step] = []
        for table in asset_tables(blueprint):
            layout = table.asset.layout
            if layout is None or (layout.format or layout.kind) != FORMAT:
                continue
            name = table.relation_name
            dump = layout.locator
            if dump is None:
                raise ValueError(f"{name}: the dump asset states no locator")
            source_table = layout.members.get(name)
            if source_table is None:
                raise ValueError(f"{name}: the dump asset names no table for it")
            cache_root = Path(str(layout.properties.get("cache") or _cache_root()))
            steps.append(Step(
                component=self.component_id,
                name=f"source.{name}",
                inputs=(),
                outputs=(Output(CoreArtifactTypes.table(name)),),
                instruction=Instruction(SOURCE_RELATION, {
                    "relation": table.relation,
                    "table": source_table,
                    "dump": str(dump),
                    "cache": str(cache_root / f"{source_table}.parquet"),
                    "archive_url": layout.properties.get("archive_url"),
                    **self.configuration.to_document(),
                }),
            ))
        return tuple(steps)


class DumpSourceExecutor:
    """Register one dump table as the relation its declaration describes."""

    kinds: tuple[InstructionKind, ...] = (SOURCE_RELATION,)
    resources = (DuckDbService,)

    def execute(
        self,
        context: ExecutionContext | DisruptedExecutionContext,
        instruction: Instruction,
    ) -> Any:
        if isinstance(context, DisruptedExecutionContext):
            return skipped(context)
        payload = instruction_payload(instruction)
        table = str(payload["table"])
        dump = Path(str(payload["dump"]))
        cache = Path(str(payload["cache"]))
        declared_url = payload.get("archive_url")
        url = str(declared_url) if declared_url else None
        declared_bytes = payload.get("archive_bytes")
        if not isinstance(declared_bytes, int):
            raise TypeError("the dump step declares no archive byte size")
        path = _materialise_table(
            dump,
            table,
            cache,
            archive_sha256=str(payload["archive_sha256"]),
            archive_bytes=declared_bytes,
            url=url,
        )
        service = context.resources.get(DuckDbService)
        literal = "'" + str(path).replace("'", "''") + "'"
        relation = service.relations.materialize(
            str(payload["relation"]),
            f"SELECT * FROM read_parquet({literal})",
        )
        return succeeded(context, relation)


__all__ = [
    "DumpSourceConfiguration",
    "DumpSourceExecutor",
    "DumpSourcePlanner",
    "SOURCE_RELATION",
]
