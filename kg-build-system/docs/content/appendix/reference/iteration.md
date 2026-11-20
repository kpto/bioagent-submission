---
title: Iteration ledger
summary: The typed events kbs appends for findings, proposals, revisions and evaluations, how links are stored, and the rules the ledger verifies.
section: reference
perspective: reference
order: 181
status: normative
verified: 2026-11-19
sources:
  - kg_build_system/iteration/model/public/events.py
  - kg_build_system/iteration/service/public/ledger.py
  - kg_build_system/cli/service/_private/iteration.py
---

> [!lede]
> The project keeps an append-only ledger of typed events under
> `journal/events/`. `kbs` appends and reads it through four nouns: `finding`,
> `proposal`, `revision` and `evaluation`. The ledger is not the graph language
> and it is not the design viewer.

## Surface

| Command | Job |
| --- | --- |
| `kbs finding add` / `list` / `withdraw` | Append, read or withdraw a finding. |
| `kbs proposal create` / `list` / `withdraw` | Record, read or withdraw a proposal. |
| `kbs revision record` / `list` / `compare` | Record a revision from the proposals it implements. |
| `kbs evaluation run` / `list` | Record an evaluation run for a revision. |

Every command takes `--project <dir>` (default `.`) and `--json`. Human output is
key/value text; `--json` prints the same result as JSON. A failed command writes
`error: …` to stderr and exits non-zero.

## Events

| Event | Carries |
| --- | --- |
| `beginning` | The root before any build. |
| `finding.created` | observation, evidence, metric |
| `finding.withdrawal` | withdrawn finding, reason |
| `proposal.created` | rationale, based revision |
| `proposal.withdrawal` | withdrawn proposal, reason |
| `revision.created` | based proposals, description |
| `evaluation.created` | method, metric |
| `evaluation.run` | protocol, measured revision, result |
| `evaluation.withdrawal` | withdrawn protocol, reason |

A record is flat: a link is an event id, never a nested object. `references`
holds named relations (`rests_on`, …); the typed fields are `based_revision`,
`based_proposals`, `withdrawn_finding`, `withdrawn_proposal`,
`withdrawn_evaluation`, `evaluation` and `evaluated_revision`.

A revision names at least one proposal it implements. A proposal names the
revision it is based on, or the beginning.

## Storage

One JSON document per event, named by its eight-character id:

```text
journal/events/<id>.json
```

`kbs init` creates the directory. Codes are family-scoped (`F-1`, `P-1`, `B-1`,
`E-1`, `EV-1`), and the ledger derives the next free code.

## Rules

The model validates one record: required fields, types, patterns and unknown
fields rejected. The ledger verifies the graph:

- every link resolves to an event in the ledger;
- every link points at an earlier `created_time`;
- a reference may not point at an event a typed field already names.

A command refuses to append an event that would break a rule.

## Details

Every event carries an eight-character `id`, a family-scoped `code`, a
`subject`, a `created_time`, a `title`, named `references` and
`external_references`. A command records its own provenance as an external
reference of type `cli`, so an event written from the shell says which command
wrote it.

`kbs` creates the beginning event on the first write; a proposal with no
`--based-revision` uses the latest revision, or the beginning when none exists.
A command verifies the whole ledger after appending and refuses the event if a
rule would break, so a failed command leaves the ledger unchanged.

## Console

`kbs console --project PATH` serves the console at `/console/`, the design viewer
as a separate page at `/`, the snapshot at `/snapshot` and the API on one port.
The console opens on the Iteration page; it has no viewer tab. The console builds
its catalog from the ledger: revisions, findings, proposals, evaluation protocols
and evaluation runs, with the event timeline ordered by time. The snapshot is
resolved under the project root (`build/workflow_plan.json`, then
`data/build/workflow_plan.json`, then `viewer.snapshot.json`), or named
explicitly with `--snapshot PATH`. `kbs console --dev` starts the source dev servers for both pages behind the same
origin, with the ledger API and snapshot still served by kbs. The console reads;
the `kbs` nouns write.

The Iteration page is the revision lineage. The main graph has one card per
build: the beginning at the bottom, the newest build at the top, and one link
per proposal a later build implements. A card's counts are the proposals,
findings and withdrawals that build consumed; the latest build breathes, and a
dangling build (no revision descends from it) is dashed. Clicking a card opens
one universal detail panel whose fields are structured values, never serialised
text. A revision also opens its focused diff in a near-full-width dialog: every
dependency, with the walk stopping at a revision (inclusive), the runs that
measured it and its external references. The diff is a graph surface of its own:
it opens fitted to the dialog, and pans, zooms and fits on its own controls.
Named references are dotted, external references finely dashed, and outcomes
gold.
