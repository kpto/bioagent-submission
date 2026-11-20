# KG design in kg-build-system

A graph is an argument. You change it by declaring, not by transforming data.

## The model in one screen

```
records      graph/        what the graph asserts, each with a Meaning
relations    relation/     what the domain contains: source or derived
bindings     binding/      how a relation fulfils a record: grain, identity, coverage
workflow     manifest.py   the steps that build and publish the graph
             modules/      project-local steps and adapters
```

## Rules

**1. Meaning first.** Every declaration states a purpose, claims and limitations.
A purpose is one expected use, with a user. A claim is a contextless assertion. A
limitation says what the use does not authorize.

```
Wrong: purpose = "Store the source rows."
Right: purpose = "Answer which sites an operator should inspect first, for that operator";
       limitation = "A reported link is not a mechanism or a decision."
```

Never write a purpose to fill a field. If there is nothing to state, use
`Omitted` where the model allows it.

**2. Identity is a stable key.** A CURIE or an accession is identity; a label is
display. Do not invent a key from a name when a source states one.

**3. An adapter decodes; it does not transform.** An adapter is a module that
contributes one step whose output is the table a source relation names. It keeps
the source's grain, identity and absence. Filtering, joining, identity mapping,
inference, aggregation and unit changes are declared relations, stages or steps,
so the plan shows them.

```
Wrong: the adapter drops nulls and joins a lookup before publishing.
Right: the adapter publishes rows as the source states them; a derived relation
       joins, and a stage or step does the rest.
```

**4. If behaviour is not a step, the design does not contain it.** The plan is
the documentation. A script that runs after the build is outside the design; a
planner and executor that contribute a step are the normal extension. The
pipeline is arbitrarily interceptable — add, replace or remove steps — but an
interception changes the graph only through a declaration.

**5. A target is a consumer, not a stage.** The framework ships file, Neo4j and
meta-graph targets and no canonical pipeline shape. Add a target only when the
graph's purpose names who consumes it.

```
Wrong: "Add FilePlanner and Neo4jPlanner so the graph is complete."
Right: "A reader diffs files in git, so file; nobody queries a database, so no Neo4j."
```

**6. Policy is not in SQL.** A threshold or exclusion is a rule module and an
annotator step, not a `HAVING` clause or a filter hidden in a relation. The
shipped graph is the projection of the annotated graph.

## Where to look

| Question | Read |
|---|---|
| A declaration and its meaning | `kg_build_system/distribution/languages/topology/model/public/declarations.py`; the project's record package (`<package>/graph/`) |
| Meaning vocabulary | `kg_build_system/distribution/languages/meaning/model/public` |
| Relations and row sources | the project's `<package>/relation/`; `languages/data/` |
| Bindings | the project's `<package>/binding/`; `languages/binding/service/_private/factories.py` |
| Steps, artifacts, extension | `kernel/model/public/workflow.py`; `distribution/modules/file/service/_private/planner.py`; `service/internal/assembly.py` |
| Worked example | `kbs init --fixture`; `tests/typecheck/authoring.py`; the framework's `reference_project/` |
| Rules to obey | `kbs guide`, `PHILOSOPHY.md`, the project's `AGENTS.md`, each directory's `README.md` |

Run `kbs guide` first. Read the directory `README.md` before writing in that
directory. Read a worked example before inventing a pattern. Grep the source
last, not first.

Read the framework from the checkout this project depends on — the one in the
workspace, or the path its `pyproject.toml` names. Do not read another copy of
the framework on the machine, and keep scratch files inside the project.

## Recipes

**Bring in a source.** Declare the asset (`asset/`), write the adapter as a
module step (`modules/`), declare the source relation over its table
(`relation/source/`), then bind it. No transformation in the adapter.

**Add a record or an edge.** One file under `graph/<name>/`, its purpose and
limitations inline, a binding whose purpose names the record use and how the
relation answers it, then the tests.

**Add behaviour.** A derived relation, a private stage, or a planner + executor
that contributes a step. The plan must show it; a one-use helper is inlined.

**Add a target.** Name the consumer, add the target to `manifest.py`, and say in
the plan review who reads it. No consumer, no target. Then run
`uv run kbs run --project project`; a declared target that is not executed is not
an output. Read the report and the artifact it names.

**Keep the ledger.** Record each decision as you take it; the chat is not the
record. `uv run kbs finding add --observation "<what you found>" --evidence
"<what you saw>"`, then `uv run kbs proposal create --subject "<the
declaration>" --rationale "<what changes and why>"`. A revision records the
proposal it implements: `uv run kbs revision record --based-proposal P-1
--message "<what changed>"`. A correction becomes a new event or a withdrawal,
not a silent edit.

**Work in stages.** Read and propose, then declare one layer, then the next. End
each turn with what you did, what you recorded, what you assumed and one
question or next command. Do not try to finish the graph in one turn.

At the first stage boundary, tell the user that `/kbs_auto <task>` lets the
agent finish the remaining work without questions and leave the revision for
them to record.

In the plugin's autonomous mode these stages are internal: finish them, run the
gates, and stop after the task is complete. Do not create a revision; report what
would be recorded and leave it to the user.

**Talk at the reader's level.** Report what the graph can answer and what it
cannot, in the user's words. Name assets, relations, bindings, adapters and
steps only when the user asks how it works or when a choice needs their
decision; otherwise the report is a few sentences about the domain.

## Before you report done

- `kbs check` reads the argument back; if it sounds like a data dictionary, fix
  the meaning.
- `pytest` runs the philosophy gate; a failure means change the declaration, not
  the test.
- `kbs workflow` shows the plan; every step must be one you can name.
- `uv run kbs run --project project` executes the plan; a plan that is not run is
  not a graph. Read its report and the artifact it names.
- For every target, name its consumer.
- The decisions are in the iteration ledger (`uv run kbs revision list`), not
  only in the conversation.
- If you edited a built artifact, revert it and change the declaration instead.
