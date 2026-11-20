# The design ledger

This directory is the project's append-only record of design decisions:
findings, proposals, revisions and evaluation runs. `kbs` writes it; every
reader derives its view from it.

## Model

The model is the framework's `kg_build_system.iteration`: each record is
validated against its stored shape, with unknown fields rejected and required
fields enforced. The framework also checks the three rules a record cannot
express on its own: every link resolves to an event in the set, every link
points at an event with an earlier timestamp, and a reference does not repeat an
event already named by a typed field.

- `Event.id` is eight random characters; `Event.code` is the human code
  (`F-123`, `P-8`, `B-11`, `EV-17`).
- Links in `references` are `EventReference`s with a `linkage_name`
  (`rests_on`, `replaced_by`, …).
- A revision has **no previous-revision pointer**. It lists the proposals it
  implements in `based_proposals`, which is required and at least one entry;
  a proposal is adopted when a revision lists it.
- A proposal names what it was based on in `based_revision`, which is required.
  It is a `RevisionCreated` or the special `Beginning` event (`BEGIN-1`).
- Findings and proposals are withdrawn, never updated; a correction is a new
  finding. A withdrawal names what it withdraws: `withdrawn_finding`,
  `withdrawn_proposal` or `withdrawn_evaluation`.
- A record must not repeat an assumption field in `references`: a proposal with
  `based_revision: B-1` cannot also carry a reference to `B-1`.
- A proposal always has `based_revision`, so it cannot be isolated.
- A reference is untyped: any event may relate to any other, a revision to a
  revision included, provided the target is earlier. The reference name states
  the relation the author had in mind.

## Write

New events are written by the `kbs` iteration nouns, and the framework validates
each one on write:

```console
uv run kbs finding add --observation ... --evidence ... --metric ...
uv run kbs proposal create --subject ... --rationale ...
uv run kbs revision record --based-proposal P-1 --message ...
uv run kbs evaluation run --revision B-1 --protocol ... --result ...
```

## Contents

630 events: 138 findings created, 10 withdrawn, 32 proposals created,
5 withdrawn, 32 revisions, 1 beginning, 24 evaluation protocols and 388 runs.
