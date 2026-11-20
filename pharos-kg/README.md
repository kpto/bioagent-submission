# Pharos KG

A knowledge graph over the **635 kinases** in the Pharos 3.19 IDG kinase family,
built with [`kg-build-system`](../kg-build-system) from typed declarations and
recorded as an append-only iteration ledger.

The project is a **pure declaration package**: the graph, its assets, relations,
bindings and workflow live in `pharos_kg/`. The framework compiles and executes
them; the ledger records why each design changed. Pharos is the stress test; the
contract is general.

Read [DESIGN.md](DESIGN.md) for the contracts and [AGENTS.md](AGENTS.md) for the
working rules. The single detailed account of the graph's argument and design is
[docs/KG.md](docs/KG.md).

## What is in the graph

| Layer | Content |
| --- | --- |
| Entities | Gene (HGNC), Protein (UniProt), Disease (MONDO/DOID), Ligand (Pharos), Biological process (GO) |
| Relations | `translates_to`, `associated_with`, `binds`, `interacts_with_experimental`, `interacts_with_predicted`, `participates_in`, `has_phenotype`, `participates_in_pathway`, `expressed_in` |
| Evidence | A sidecar keyed by `build_key`: the source files and tables, activity measurements, PMIDs and references behind each record |
| Meaning | Graph purpose, claims and limitations on every declaration |
| Standards | Biolink class/predicate annotations and OBO terms on every entity and relation |

## Quick start

### 1. View the graph

```console
uv sync
uv run kbs up --project . --port 8787
```

`chdb`, the dump reader, has no Windows wheel, so `uv sync` skips it there; the
pinned Parquet cache in `data/` needs no reader. Rebuilding from the MySQL dump
is a Linux or macOS task, and only that path imports `chdb`.

Open the console at <http://127.0.0.1:8787/console/> and the design viewer at
<http://127.0.0.1:8787/>. The console reads `journal/events/` immediately; the
viewer reads `build/workflow_plan.json`, which the build in step 2 writes. On a
fresh checkout, run step 2 once and refresh the viewer.

### 2. Build the graph and read the artifacts

```console
uv run kbs check --project pharos_kg
uv run kbs run --project pharos_kg
```

`kbs run` executes the 251-step workflow and writes `build/`:

| Artifact | What it is |
| --- | --- |
| `build/graph.jsonl` | **the scored artifact**: the shipped facts graph, 28,359 nodes and 150,856 edges |
| `build/graph.annotated.jsonl` | the audit candidate, 74,747 / 239,939, including records marked `prune` |
| `build/evidence.jsonl` | one provenance entry per shipped record, keyed by `build_key` |
| `build/workflow_plan.json` | the compiled plan the design viewer reads |
| `build/meta_graph.html` | the component and step catalogue for design review |

Score `graph.jsonl`; the annotated file and the evidence sidecar explain it, and
the plan and meta-graph describe how it was built.

The source steps reuse the three caches under `data/source/`; a missing table is
rebuilt from the pinned release after every source file is checked against the
digest its declaration records. A cold `data/` downloads the Pharos archive, the
HPO files and the Open Targets parts, verifies them and rebuilds the caches.

### 3. What it is

The graph answers one question: **why is a kinase linked to a disease, a
compound, another kinase or a biological process — and what does that link not
mean?** Every edge names its source and derivation, and every declaration states
what its use does not authorize.

It is an experimental research artifact over the 635-kinase family, not a
clinical or deployment claim. The extract is a bounded-per-target sample; scores
and confidences are release values, not probabilities.

## Commands

The declaration surface:

| Command | Purpose |
| --- | --- |
| `uv run kbs check --project pharos_kg` | Read the authored argument back |
| `uv run kbs workflow --project pharos_kg` | Compile and print the plan |
| `uv run kbs run --project pharos_kg` | Execute the plan and write every declared artifact |
| `uv run kbs up --project .` | Serve the decision console and design viewer and open them |
| `uv run kbs console --project .` | Serve both surfaces; open the console only |
| `uv run kbs view --snapshot build/workflow_plan.json` | Serve the design viewer alone |

The record surface:

| Command | Purpose |
| --- | --- |
| `uv run kbs finding add --observation … [--evidence …] [--metric …]` | Append a finding |
| `uv run kbs finding list` / `withdraw --id F-1 --reason …` | Read or withdraw a finding |
| `uv run kbs proposal create --subject … --rationale … [--based-revision B-1]` | Record a proposal |
| `uv run kbs proposal list` / `withdraw --id P-1 --reason …` | Read or withdraw a proposal |
| `uv run kbs revision record --based-proposal P-1 [--message …]` | Record a revision from the proposals it implements |
| `uv run kbs revision list` / `compare --before B-1 --after B-2` | Read revisions or compare their descriptions |
| `uv run kbs evaluation run --revision B-1 [--result JSON]` | Record an evaluation run |
| `uv run kbs evaluation list` | Read evaluation runs |

Every noun takes `--project` (default `.`) and `--json`. A revision names the
proposals it implements; a proposal names the revision it is based on; every
link points at an earlier event. A finding or proposal that later evidence
refutes is withdrawn, never edited.

## Project layout

```text
pharos_kg/                 the kbs declaration: asset, graph, relation, binding, manifest, modules
data/                      the source cache
build/                     the generated artifacts
journal/
  events/                  the append-only ledger, one JSON document per event
tests/                     the declaration, plan and build tests
docs/                      reader-facing contract
```

## Console

`kbs up --project . --port 8787` (or `kbs console`) serves the console at `/console/`, the design viewer
at `/`, the viewer snapshot at `/snapshot` and the console API on one port:

- the catalog and the event timeline are derived from `journal/events/`;
- the viewer reads `build/workflow_plan.json`, which `kbs run` writes;
- `build/meta_graph.html` is the component and step catalogue; a maintainer
  reads it when reviewing the design. The console and the viewer do not read it;
- the Iteration page is the revision lineage: one card per build, newest at
  the top, with the proposals and findings it consumed collapsed into counted
  lines. A card opens a structured detail; a revision opens its dependency diff
  (the walk stops at a revision, inclusive) with its evaluation runs and
  external references.

The console is read-only over the ledger. Recording stays on the `kbs` nouns.

## Verification

```console
uv run pytest -q
uv run pyright
uv run kbs check --project pharos_kg
uv run kbs run --project pharos_kg
uv run kbs revision list --json > /dev/null
```

The framework validates each ledger event when it is written and when the
ledger is read.

## Current state

The counts below are from the current declaration; `kbs run` reproduces them.
The built artifacts are included under `build/`.

The shipped build is **28,359 nodes and 150,856 edges** from **635 kinases**:
the keep projection of the 74,747 nodes and 239,939 edges in the annotated
candidate, with 179,215 evidence entries and 100% evidence coverage.

The current build reads the pinned Pharos 3.19 dump recorded in the asset
declaration. The design exploration and its evaluation runs are in the
ledger; `kbs console` is the reading surface.

This is an experimental knowledge graph. The extract is a bounded-per-target
sample, not the whole of Pharos. Scores and confidences are release values, not
probabilities. The declaration is the stable interface; the Pharos adapter is
replaceable.
