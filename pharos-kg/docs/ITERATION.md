# Design iteration

The project treats a design change as an experiment with a named gate, recorded
as a sequence of typed events.

## The loop

```text
observe (a run, a failed gate or a reader's question)
  -> finding add
  -> proposal create
  -> change the declarations
  -> kbs check -> pytest -> kbs run
  -> revision record (names the proposals it implements)
  -> evaluation run (records the measured result for that revision)
```

## Findings

A finding is an event in `journal/events/`. It states what was seen, the
evidence and the metric a later change must move:

```console
uv run kbs finding add \
  --observation "Tbio pages time out at 50 rows" \
  --evidence "download log" \
  --metric "manifest target count = 635"
```

A finding that later evidence refutes is withdrawn, never edited:

```console
uv run kbs finding withdraw --id F-7 --reason "the fetch reran cleanly"
```

## Proposals

A proposal names the change and the revision it is based on. With no
`--based-revision` it uses the latest recorded revision, or the beginning:

```console
uv run kbs proposal create \
  --subject edge:associated_with \
  --rationale "Add the evidence source to the edge properties."
```

A proposal is not an edit. It is adopted by the revision that names it, or
withdrawn with a reason.

## Revisions

A revision names at least one proposal it implements and a description of what
changed:

```console
uv run kbs revision record \
  --based-proposal P-12 \
  --message "Evidence source on associated_with; audit and QA re-run"
```

```console
uv run kbs revision list
uv run kbs revision compare --before B-3 --after B-4
```

A revision is the tuple `(data manifest, blueprint fingerprint, build, eval)`
described in the event. The event records the decision; the artifacts record the
measurement.

## Evaluations

Evaluation is a record, not a command of this checkout. A protocol states its
method and metric; a run records the measured result and the revision it
measured:

```console
uv run kbs evaluation run --revision B-4 --protocol "PPI threshold" \
  --result '{"status": "passed", "metric": 0.0}'
uv run kbs evaluation list
```

A recorded run is evidence about one revision. It is never rewritten; a re-run
is a new event.

## Gates

| Gate | Command | Pass condition |
| --- | --- | --- |
| declarations | `uv run kbs check --project pharos_kg` | the argument reads back; every declaration states its meaning |
| philosophy and build tests | `uv run pytest -q` | the declaration, plan and build tests pass |
| build | `uv run kbs run --project pharos_kg` | no unresolved failure; evidence entries with no source table = 0 |

A change is accepted only with a gate and a re-run. A change that cannot name a
gate is an observation, not a decision.

## Verification

The framework validates each event when it is written and when the ledger is
read: every link resolves, every link points at an earlier event, and a named
reference does not repeat a typed field. `uv run kbs revision list` is the
read-back.
