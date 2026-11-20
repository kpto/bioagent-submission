"""The pinned releases behind the HPO and Open Targets assets.

The asset declaration and its release are one fact: a reader, the files it
downloads, and the tables it decodes. Keeping them here means the workflow plan
can record exactly what will be fetched and verified, and a deleted cache can be
rebuilt without reading a second manifest from the data directory.

Each file states the URL, byte size and SHA-256 the release was read from. Each
table states the relation it serves, its cache file and the row count the reader
produced. A release whose bytes moved is refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReleaseFile:
    """One file of a release: where it comes from and what it must be."""

    dataset: str
    file: str
    url: str
    bytes: int
    sha256: str

    def to_document(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "file": self.file,
            "url": self.url,
            "bytes": self.bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class ReleaseTable:
    """One declared reading of a release: relation, cache file and row count."""

    relation: str
    file: str
    rows: int

    def to_document(self) -> dict[str, Any]:
        return {"relation": self.relation, "file": self.file, "rows": self.rows}


@dataclass(frozen=True, slots=True)
class Release:
    """A pinned release and the reading the asset declares."""

    reader: str
    files: tuple[ReleaseFile, ...]
    tables: tuple[ReleaseTable, ...]
    assumptions: tuple[str, ...]

    def to_document(self) -> dict[str, Any]:
        return {
            "reader": self.reader,
            "files": [item.to_document() for item in self.files],
            "tables": [item.to_document() for item in self.tables],
            "assumptions": list(self.assumptions),
        }


HPO_RELEASE = Release(
    reader="hpo",
    files=(
        ReleaseFile('hpo', 'genes_to_phenotype.txt', 'https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/genes_to_phenotype.txt', 20821704, '507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c'),
        ReleaseFile('hpo', 'hp.obo', 'https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/hp.obo', 10863613, '93dace952fcb3ec4728818857f6ba76bc2d5312f4d83266519b8694b8e798f22'),
        ReleaseFile('hpo', 'mondo.obo', 'https://purl.obolibrary.org/obo/mondo/mondo.obo', 53442278, 'b5a3d848578694601dffb1c2866798d4f6f4b4a12c315030c4d4c62ffe4e7e22'),
        ReleaseFile('hpo', 'phenotype.hpoa', 'https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/phenotype.hpoa', 35816037, 'e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72'),
    ),
    tables=(
        ReleaseTable('hpo_term', 'hp_term.parquet', 19894),
        ReleaseTable('hpo_disease_phenotype', 'disease_phenotype.parquet', 286651),
        ReleaseTable('hpo_gene_phenotype', 'gene_phenotype.parquet', 333983),
        ReleaseTable('mondo_xref', 'mondo_xref.parquet', 20670),
    ),
    assumptions=(
        'Every annotation row is kept, including NOT-qualified rows; the qualifier is a column so the declaration can state how it is read.',
        'No identifier is rewritten: phenotype.hpoa and MONDO cross-references are published as they stand and joined in a declaration.',
        'Obsolete HP terms are excluded from the term table because the release marks them obsolete; no annotation row is dropped by that choice.',
    ),
)


OPENTARGETS_RELEASE = Release(
    reader="opentargets",
    files=(
        ReleaseFile('association_by_datatype_direct', 'part-00000-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00000-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 52058481, '4a1f84c472894c256253d63f600bc8f5660e68b859a74571d573a8fdaa0bc377'),
        ReleaseFile('association_by_datatype_direct', 'part-00001-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00001-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58426776, 'e4c4b07b637055042c3ae66df23f0f64ed8737bf0300207bb8708701014c0dd1'),
        ReleaseFile('association_by_datatype_direct', 'part-00002-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00002-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58189772, '08ac48b85275111faa023e7501939572d7982cf35c8ff778e585c8862f1bc828'),
        ReleaseFile('association_by_datatype_direct', 'part-00003-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00003-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 57227429, '11ca8af4ff2ed8314529122fd552d5acf1cc52cb614c9dbfbfe31f4c29483eb5'),
        ReleaseFile('association_by_datatype_direct', 'part-00004-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00004-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58125231, 'cc50d8c5e1464cf7617dd2764b2636e391a244e2494f01f2e5071c8e9c1a4a7a'),
        ReleaseFile('association_by_datatype_direct', 'part-00005-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00005-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58215982, '4161aa89957a875a0186d14de50ae294c58555a6c4203518a2cacfe92686afda'),
        ReleaseFile('association_by_datatype_direct', 'part-00006-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00006-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58278193, 'a0337dc085c4b8d7796735481133c3ab13e07f243f52e0465a3f07f2079c8924'),
        ReleaseFile('association_by_datatype_direct', 'part-00007-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00007-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58303610, '116733c10c5caf139767d52511d6d5a4776452360e058d4a48ea82f3b63036b9'),
        ReleaseFile('association_by_datatype_direct', 'part-00008-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00008-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 56975147, 'd7cfaaaa13b27b7339e24bf1bca03af0dac3d4f893ca2a51c2be3b36cba3772a'),
        ReleaseFile('association_by_datatype_direct', 'part-00009-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00009-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58460071, 'b94293a8f0cfb6e72612b8b65df8487d3909b5df9adf72249dbd8ea9b82d0755'),
        ReleaseFile('association_by_datatype_direct', 'part-00010-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00010-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 57746599, 'd150dfad0c5329503841bfbc4a74b6ae34a67c7bf202d8eda09afdc7f60ec891'),
        ReleaseFile('association_by_datatype_direct', 'part-00011-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00011-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 57702684, '3c12768defcf48a611da570598a95f24c0873bd5d8dd26a2ab665a5f8f1b629b'),
        ReleaseFile('association_by_datatype_direct', 'part-00012-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00012-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58593460, '80057389fe6ef48b20565940b2e4f047828d930a6ad88eaaeae945dfce85ded0'),
        ReleaseFile('association_by_datatype_direct', 'part-00013-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00013-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 58188358, 'cead318de8d7db1ccc6ceb3b92f4be9f1cc237076a38b71b15bcffb1d0df1701'),
        ReleaseFile('association_by_datatype_direct', 'part-00014-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/association_by_datatype_direct/part-00014-3d8673e2-3337-48a5-97f4-a27c4a57b281-c000.zstd.parquet', 53744618, '0b256095374c10f9c450f5c45c166bdfdc268441895656a1d479085d52dfc123'),
        ReleaseFile('target', 'part-00000-ddfc1f8c-60a1-40fe-885a-2c1dd3f9a9c1-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/target/part-00000-ddfc1f8c-60a1-40fe-885a-2c1dd3f9a9c1-c000.zstd.parquet', 7165956, '80186f1c9919d5d1351f009253480fad93b3bb3e2de506d8948ed2126ac48cab'),
        ReleaseFile('target', 'part-00001-ddfc1f8c-60a1-40fe-885a-2c1dd3f9a9c1-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/target/part-00001-ddfc1f8c-60a1-40fe-885a-2c1dd3f9a9c1-c000.zstd.parquet', 7196171, 'a777ec38d5fbf6e6475d85158141c0a01f2c32cadc7f8769256eaab6e034e702'),
        ReleaseFile('target', 'part-00002-ddfc1f8c-60a1-40fe-885a-2c1dd3f9a9c1-c000.zstd.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/target/part-00002-ddfc1f8c-60a1-40fe-885a-2c1dd3f9a9c1-c000.zstd.parquet', 7270990, '3621b2510eb3f9da9b533f40559b4f4de390fffc57935726a2b0eebcc40aa028'),
        ReleaseFile('disease', '00000000.parquet', 'https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/disease/00000000.parquet', 6346458, 'a89b8b8b89bad168016e6ff8302d2bcc8d9b7f9cbb35c459ef847c36a4f17aed'),
    ),
    tables=(
        ReleaseTable('ot_association', 'association.parquet', 7495759),
        ReleaseTable('ot_target_protein', 'target_protein.parquet', 526681),
        ReleaseTable('ot_disease', 'disease.parquet', 45896),
    ),
    assumptions=(
        'Parquet is read with its own types; no value is recast except associationScore to DOUBLE and evidenceCount to BIGINT.',
        'Nested arrays are published as link tables; no row is dropped by that normalisation.',
        'The first underscore of an identifier is written as a colon so that MONDO_0005148 reads MONDO:0005148; no other character changes.',
    ),
)


RELEASES = {
    release.reader: release
    for release in (HPO_RELEASE, OPENTARGETS_RELEASE)
}


__all__ = [
    "HPO_RELEASE",
    "OPENTARGETS_RELEASE",
    "RELEASES",
    "Release",
    "ReleaseFile",
    "ReleaseTable",
]
