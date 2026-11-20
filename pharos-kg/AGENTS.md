# Agent notes

## Working

- This is a `kg-build-system` project. Graph records come from typed
  declarations in `pharos_kg/`; never write `graph.jsonl` by hand.
- Every node, edge, property, relation, binding and asset states its `Meaning`
  (a purpose with its limitations, or explicit claims), or opts out with
  `Omitted` only where the model allows it. A declaration without meaning is a
  defect, not a shortcut.
- Identity is a stable key: `PHAROS:<uniprot>`, `MONDO:<id>`, `HGNC:<id>`.
  A display label is never a key.
- An evaluation number in a document is a number the ledger records. Never
  compute one by hand or edit an event to fit a sentence.
- The ledger is the history of the graph's design: purpose, records, relations,
  bindings, sources, annotations and evaluation protocols. A refactor that
  changes no graph record is a commit, not a finding, proposal or revision.
- Design changes need a finding, a named gate and a re-run, recorded as a
  revision that names the proposals it implements.
- The record is append-only. A finding or proposal that later evidence refutes
  is withdrawn with a reason; it is never edited or deleted. An event that was
  never design history — an engineering change recorded in error — is removed
  from the ledger, not withdrawn.

## Ownership

| Path | Owner | Purpose |
| --- | --- | --- |
| `pharos_kg/` | core | the kbs declaration tree: asset, graph, relation, binding, manifest, modules |
| `tests/` | core | the declaration, plan and build tests |
| `journal/` | record | the append-only event ledger |
| `docs/` | everyone | reader-facing contract and demo |

Do not edit another owner's directory without saying so in the finding.

The declaration tree follows the framework template: one file per source
relation, one directory per node, one file per edge, inline meanings, and no
declaration docstrings.

The build is the workflow the manifest declares:

```console
uv run kbs run --project pharos_kg
```

It writes `build/` from the manifest's `output_directory`, including
`graph.jsonl`, `graph.annotated.jsonl`, `evidence.jsonl` and the plan at
`build/workflow_plan.json`.

`kbs console` serves the console from `journal/events/` and the design viewer
from that plan. Do not add a second relational model or viewer copy to
`pharos_kg/`.

## Surfaces

- `kbs` alone operates the project: `blueprint`, `workflow`, `run`, `check`,
  `view`, `console`.
- The `kbs` iteration nouns record the project's history: `finding`, `proposal`,
  `revision`, `evaluation`.
- `journal/events/` is the record. `kbs` writes it; every reader derives its
  view from it.

## Verification

```console
uv run pytest -q
uv run pyright
uv run kbs check --project pharos_kg
uv run kbs run --project pharos_kg
uv run kbs revision list --json > /dev/null
```

`kbs check` reads the argument back. `kbs run` must write every artifact the
plan declares; read its report. The framework validates each ledger event when
it is written and when the ledger is read.

## Writing

- State the current model as if it were the only one.
- Name the interface, the file and the decision.
- A document that only makes sense as a change report is a finding, a proposal
  or a revision in the ledger, not a file in the tree.
