# Pharos KG — design and contracts

## Thesis

This project is not a Pharos demo. It is a **declarative knowledge graph**,
proved on the hardest available case: the Pharos kinase family, where identity,
evidence and precedence are contested.

Pharos is the test case. The contract is general.

Three rules follow:

1. The graph is built from typed declarations by `kg-build-system`. Nothing
   writes graph records by hand.
2. Every record is backed by a source row in the evidence sidecar, not by model
   prose.
3. Every design change is an event in the iteration ledger: a finding, a
   proposal, the revision that implements it and the evaluation that measured
   it.

## Layers

```text
data/source/pharos319.sql.gz    the pinned Pharos 3.19 MySQL dump (the asset)
data/source/pharos319/*.parquet one reading of it (the adaptor's cache)
        |
pharos_kg/               typed declarations: asset, graph, relation, binding, manifest, modules
        |
kg-build-system          blueprint -> workflow plan -> every declared artifact
        |
journal/events/          the append-only ledger: findings, proposals, revisions, evaluations
```

The project has one operation surface, `kbs`:

```console
uv run kbs check --project pharos_kg
uv run kbs workflow --project pharos_kg
uv run kbs run --project pharos_kg
uv run kbs console --project .
uv run kbs finding add --observation ...
uv run kbs proposal create --subject ... --rationale ...
uv run kbs revision record --based-proposal P-1
uv run kbs evaluation run --revision B-1
```

The declaration surface is `blueprint`, `workflow`, `run` and `check`; the
record surface is the iteration nouns. There is no project wrapper around them.

## Data contract

The asset is the MySQL dump NCATS publishes for Pharos 3.19. The declared dump
source step fetches the archive when neither it nor a cached table is present,
decodes the tables the declarations consume through chdb's `MySQLDump` reader and
writes them to `data/source/pharos319/*.parquet`. The Parquet directory is a
cache of one reading; each extracted table carries a marker with the archive
digest, its row count and its own digest.

The dump archive digest is declared in `pharos_kg/asset/pharos_source.py`;
each cache table carries its own marker.
The HPO files and the Open Targets parts are pinned in
`pharos_kg/asset/release.py`. Each source step fetches its release only when a
table is missing, verifies every source file against the declared digest,
decodes the declared reading, and checks the table's row count against the
declaration.

The graph is built from these tables through typed declarations, not from files:

| Record | Read from | Key |
| --- | --- | --- |
| protein | `target`, `t2tc`, `protein` | `PHAROS:<uniprot>` |
| gene | `xref` (HGNC) | `HGNC:<id>` |
| disease | `disease` | `MONDO:`/`DOID:`/`UMLS:`/`MESH:`/`OMIM:`/`NAME:<slug>` |
| ligand | `ncats_ligands` | `PHAROS:<identifier>` |
| biological process | `go`, `goa` | `GO:<id>` |
| phenotype | `phenotype` | `MP:<id>` |
| pathway | `pathway` | source database CURIE |
| anatomical entity | `expression` | `UBERON:<id>` |

Every relation's grain, identity, evidence and limitations are declared in
`pharos_kg/relation/`; every edge states what it does not mean in
`pharos_kg/graph/`.

## Build contract

```text
build/graph.jsonl            the shipped facts, one JSON object per record
build/graph.annotated.jsonl  every candidate, with the annotation fields
build/evidence.jsonl         occurrence evidence keyed by build_key
build/workflow_plan.json     the compiled plan
build/build_report.json      the execution report
build/meta_graph.json/html   the component and step catalogue
```

A graph record has `kind` (`node`/`edge`), `type`, `build_key`, properties, and
for an edge `source_build_key` / `target_build_key`.

Every artifact is a step or a target of the workflow. The evidence sidecar is an
`EvidencePlanner`/`EvidenceExecutor` step after the facts output; canonical
record order is written by the output step; the plan is written by `kbs run`.
No code edits a built file after the plan executes. The meta-graph is read by a
maintainer or agent reviewing the component and step catalogue; the console and
the design viewer read the plan, not the meta-graph.

`evidence.jsonl` is keyed by `build_key` and carries the asset files and tables
its binding read, the record's locating values and the source evidence. It is
what makes occurrence-level explanation possible without embedding evidence in
the graph.

## Evaluation record

Evaluation is a record, not a command of this project. Each protocol and run is
an event in `journal/events/` with its measured revision, method and result.
The numbers a document quotes are those events; this checkout does not ship a
second runner that could drift from them.

A design change is recorded as a finding, then a proposal, then a revision that
names the proposals it implements. Evaluation runs are recorded against the
revision. A result that cannot be reproduced from its recorded protocol is not a
result.

## Iteration record contract

The ledger under `journal/events/` is one JSON document per event, named by its
eight-character id. Codes are family-scoped (`F-1`, `P-1`, `B-1`, `E-1`,
`EV-1`). A record is flat: a link is an event id, never a nested object.

| Event | Carries |
| --- | --- |
| `finding.created` | observation, evidence, metric |
| `finding.withdrawal` | withdrawn finding, reason |
| `proposal.created` | rationale, based revision |
| `proposal.withdrawal` | withdrawn proposal, reason |
| `revision.created` | the proposals it implements, description |
| `evaluation.created` | method, metric |
| `evaluation.run` | protocol, measured revision, result |
| `evaluation.withdrawal` | withdrawn protocol, reason |

The framework verifies the graph on every write: every link resolves, every link
points at an earlier event, and a named reference never repeats a typed link.
A withdrawal is a new event, never an edit.

## Generalisation rules

- `pharos_kg/` imports only the standard library, the `kg_build_system` public
  model and the project's own package.
- Domain vocabulary lives in `pharos_kg/` and in the data adapter. The core
  speaks `build_key`, `derivation`, `source`, `evidence`, `revision`.
- The plan and the evidence sidecar must be readable without the Python
  project. That is why they are JSON artifacts, not a service.
- Run the same extractor on `reference_project` in the test suite. A Pharos-only
  field in the engine is a defect.

## Non-goals for this revision

- No chat UI, no copilot inside the graph. The console is the reading surface
  and reads the same ledger the `kbs` nouns write.
- No fabricated metrics. A protocol that cannot run is recorded as `skipped`
  with the reason, never as a number.
- No claim that the slice is all of Pharos. The sampling rule is stated in the
  manifest and in every evaluation event.
