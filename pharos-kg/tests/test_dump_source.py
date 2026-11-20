"""The dump step fetches, verifies, caches and reuses one table at a time."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path

import pytest

from pharos_kg.modules import dump_source


def test_a_cached_table_is_used_without_reading_the_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = tmp_path / "disease.parquet"
    cache.write_bytes(b"cached")
    dump = tmp_path / "absent.sql.gz"

    def refuse(*_args: object, **_kwargs: object) -> None:
        pytest.fail("the step fetched an archive although a cached table exists")

    monkeypatch.setattr(dump_source, "urlopen", refuse)
    path = dump_source._materialise_table(
        dump,
        "disease",
        cache,
        archive_sha256="unused-while-the-archive-is-absent",
        archive_bytes=0,
        url="https://example.invalid/pharos319.sql.gz",
    )
    assert path == cache


def test_absent_archive_and_cache_fetches_the_declared_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"archive bytes"
    digest = hashlib.sha256(payload).hexdigest()
    dump = tmp_path / "nested" / "pharos319.sql.gz"
    requested: list[str] = []

    def respond(url: str, timeout: int = 0) -> io.BytesIO:
        requested.append(url)
        return io.BytesIO(payload)

    def stop(*_args: object, **_kwargs: object) -> bool:
        raise RuntimeError("stop before extraction")

    monkeypatch.setattr(dump_source, "urlopen", respond)
    monkeypatch.setattr(dump_source, "_cache_is_current", stop)

    with pytest.raises(RuntimeError, match="stop before extraction"):
        dump_source._materialise_table(
            dump,
            "disease",
            tmp_path / "disease.parquet",
            archive_sha256=digest,
            archive_bytes=len(payload),
            url="https://example.invalid/pharos319.sql.gz",
        )

    assert requested == ["https://example.invalid/pharos319.sql.gz"]
    assert dump.read_bytes() == payload
    assert not dump.with_name(dump.name + ".part").exists()


def test_a_fetched_archive_with_the_wrong_digest_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"moved release"

    def respond(_url: str, timeout: int = 0) -> io.BytesIO:
        return io.BytesIO(payload)

    monkeypatch.setattr(dump_source, "urlopen", respond)
    dump = tmp_path / "pharos319.sql.gz"
    with pytest.raises(RuntimeError, match="pinned digest"):
        dump_source._materialise_table(
            dump,
            "disease",
            tmp_path / "disease.parquet",
            archive_sha256=hashlib.sha256(b"other").hexdigest(),
            archive_bytes=len(payload),
            url="https://example.invalid/pharos319.sql.gz",
        )
    assert not dump.exists()


def test_an_extracted_table_writes_its_cache_marker(tmp_path: Path) -> None:
    pytest.importorskip("chdb", reason="the MySQLDump reader has no Windows wheel")
    sql = """CREATE TABLE `disease` (
  `id` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
);
INSERT INTO `disease` VALUES (1, 'x'), (2, 'y');
"""
    dump = tmp_path / "pharos319.sql.gz"
    dump.write_bytes(gzip.compress(sql.encode()))
    digest = hashlib.sha256(dump.read_bytes()).hexdigest()
    cache = tmp_path / "disease.parquet"

    path = dump_source._materialise_table(
        dump,
        "disease",
        cache,
        archive_sha256=digest,
        archive_bytes=dump.stat().st_size,
    )

    assert path == cache
    marker = dump_source._marker(cache)
    assert marker.is_file()
    assert dump_source._cache_is_current(cache, digest)
    recorded = json.loads(marker.read_text(encoding="utf-8"))
    assert recorded["archive_sha256"] == digest
    assert recorded["table"] == "disease"
    assert recorded["rows"] == 2
    assert recorded["sha256"] == hashlib.sha256(cache.read_bytes()).hexdigest()
