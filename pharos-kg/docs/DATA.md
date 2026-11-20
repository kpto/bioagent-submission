# The source

## Asset

The asset is the MySQL dump NCATS publishes for Pharos 3.19 (TCRD 6.13.4):

```text
https://opendata.ncats.nih.gov/public/pharos/archive/pharos319.sql.gz
2,257,847,063 bytes
sha256 86ebfffdd5fd03bcc23ef43a31251d40572ccd7feec62dadd3215f276f8b0953
```

The declared dump source step fetches the archive when neither it nor a cached
table is present, and decodes the tables the declarations consume with chdb's
native `MySQLDump` reader. The fetched archive is checked against the declared
digest, and each cache table's marker against that archive digest.

The Parquet files under `data/source/pharos319` are one reading of the archive,
not the asset. Each extracted table carries a marker with the archive digest,
its row count and its own digest. The committed cache carries markers backfilled
from the reading that produced it; a cache-only checkout trusts those tables,
and a marker makes a later change to a table detectable. A table extracted anew
writes a fresh marker. The adaptor re-reads a table only when the
archive digest or the cached file changed.

The archive digest is declared in `pharos_kg/asset/pharos_source.py`. Each
extracted table writes a small marker beside it with the archive digest, row
count, byte size and table digest, so the dump step knows whether the cache is
current without a data-side manifest.

## Remote releases

HPO and Open Targets are published as several files. Their source steps in
`pharos_kg/modules/remote_source.py` fetch the pinned files, verify each one
against the digest its asset declaration records, decode the declared reading into
`data/source/hpo` and `data/source/opentargets2609`, and leave the scan to the
framework's source step. A cached table is authoritative; the release is fetched
only when a table is missing. A release whose bytes moved is refused.

`HPO_RELEASE` and `OPENTARGETS_RELEASE` in `pharos_kg/asset/release.py` record
the source files, their URLs and digests, each table's row count and the
reader's assumptions. The workflow plan carries that configuration, so the
fetch step is auditable without opening the data directory.

## Tables

| Relation | Tables |
| --- | --- |
| protein, target slice | `target`, `t2tc`, `protein` |
| gene | `xref` (HGNC) |
| disease | `disease` |
| ligand, binding | `ncats_ligands`, `ncats_ligand_activity` |
| biological process | `go`, `goa` |
| protein interaction | `ncats_ppi` |
| phenotype | `phenotype` |
| pathway | `pathway` |
| anatomical entity | `expression` |

## Identities

| Entity | Key | Fallback |
| --- | --- | --- |
| protein | `PHAROS:<UniProt>` | none; a target without UniProt is excluded |
| gene | `HGNC:<id>` | no gene node; the protein remains |
| disease | `MONDO:<id>` | `DOID:`, `UMLS:`, `MESH:`, `OMIM:`, then `NAME:<slug>` |
| ligand | `PHAROS:<identifier>` | none |
| GO term | `GO:<id>` | none |
| phenotype | `MP:<id>` | none |
| pathway | the database's CURIE, such as `Reactome:R-HSA-164843` | none; a row with no identifier is absent |
| anatomical entity | `UBERON:<id>` | none |

A name is never a primary key. A name-derived disease key is a last resort and
is recorded as a limitation in the graph semantics.

## Reproducibility

- The archive is pinned by digest; a new release is a new asset, not a change
  in parsing.
- Each extracted table has a marker with the archive digest, row count, byte
  size and table digest.
- `uv run kbs run --project pharos_kg` re-reads a table only on a cache miss;
  a missing table is rebuilt from the pinned release and its row count is
  checked.
- The dump step fetches the archive only when neither it nor a cached table is
  present; the HPO and Open Targets steps do the same for their releases.
- Do not compare metrics across releases.

## Limits

- A dump is a release snapshot. Absence is not evidence that a relation does
  not exist.
- Activity values are as the release states them; assay types differ and are
  not converted.
- A phenotype observation is usually in a model organism, not in a human
  carrier.
- Pathway membership is a database's curation; different databases draw
  different boundaries.
