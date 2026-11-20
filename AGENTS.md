# Working in this submission

This folder is a competition submission. It contains four things:

| Path | What it is |
| --- | --- |
| `kg-build-system/` | the framework: the design language, the build engine and the `opencode-kbs` plugin |
| `pharos-kg/` | the worked graph: a pure declaration package for the framework, over the Pharos 3.19 kinase family |
| `demo/` | four messy exports and a lab lead's `PURPOSE.md`, for the same method on a new domain |
| `docs/` | the figures used by the README |

Read `README.md` first for the argument and the exact prompts. This file is the
agent's short guide to what the workspace can do.

## First: confirm OpenCode V2

Before the menu, before installing anything, and before any command, check the
host you are running in:

- `OPENCODE=1` (or the session otherwise identifying itself as OpenCode) means
  you are inside OpenCode.
- `opencode --version` must report a **v2.x** version.

If either check fails, warn the user:

> This plugin is for OpenCode V2; you appear to be running **<host/version>**.
> Some commands may not work here.

Do not block the rest of the menu solely on this check; state the risk and let
the user decide whether to continue.

## Submission navigation

**Magic keyword: `Menu please`.** If a user message contains the phrase
`Menu please` (case-insensitive) — alone or inside a sentence — reply with the
six choices below and wait. Do not start a build, open a viewer or change a file
until the user chooses.

When the user opens this folder, offer the same menu:

> **What would you like?**
>
> 1. **What is this?** — a guided read of this README, one section at a time.
> 2. **Show me the graph** — open the viewer and console with `kbs up`.
> 3. **I mean the actual graph** — explain each bundled artifact, its path and its job in the competition.
> 4. **The graph format is not quite right...** — name the format; I take the author role and change the declarations.
> 5. **I don't trust you; I want to build it myself** — show `kbs check` and `kbs run`, then step aside.
> 6. **I still don't trust you; make a new graph for me** — move the session to `demo/`, run `/kbs_init`, then stop and ask.
>
> Which would you like?

Then follow the choice:

- **1. What is this?** Act as a reading guide for this README, not as a tour of
  `kbs`. Start with the one-paragraph overview and **What I built**, then stop.
  Use the README's own sections as the map: **What I built** → **The approach**
  → **The proof** → **Try it**. After each section, offer whatever paths are
  useful — go deeper, move on, jump to a named section, or stop — and accept any
  other direction the user takes. Do not present a fixed menu or force a single
  path. Inside a section, reveal its opening paragraph, then its figure or table,
  then its detail only on request.
- **2. Show me the graph.** If `pharos-kg/build/workflow_plan.json` is present,
  start the viewer and console; otherwise build first. Give both URLs and leave
  them running for the session.
- **3. I mean the actual graph.** Explain the bundled artifacts against the
  competition, not as a file listing. Do not rebuild; read what is there.

  | Artifact | What it is | Competition job |
  | --- | --- | --- |
  | `pharos-kg/build/graph.jsonl.gz` | 28,359 nodes / 150,856 edges, the keep projection | **the scored graph file**; this is the graph a judge reads or consumes |
  | `pharos-kg/build/graph.annotated.jsonl.gz` | 74,747 / 239,939 candidates, including records marked `prune` | **accuracy and pruning**: every candidate and the keep/prune decision |
  | `pharos-kg/build/evidence.jsonl.gz` | 179,215 evidence records keyed by `build_key` | **usability and trust**: why a node or edge exists, traceable to its source row |
  | `pharos-kg/build/evidence_manifest.json` | evidence counts, coverage and missing totals | **evidence completeness**: proves the sidecar covers every shipped record |
  | `pharos-kg/build/workflow_plan.json` | the compiled 251-step plan | **standards and generalisation**: the build is declared, inspectable and rerunnable |
  | `pharos-kg/build/build_report.json` | the execution report | **reproducibility**: what ran, what published, what failed |
  | `pharos-kg/build/meta_graph.html` / `.json` | the component and step catalogue | **architecture and generalisation**: how the build is assembled for a reviewer |

  All paths are relative to the submission root; the files are in
  `pharos-kg/build/`. The first three are gzip-compressed in `full`; `gunzip`
  them before reading. A request maps to node and edge keys and their `build_key`;
  explain that mapping through the evidence sidecar.
- **4. The graph format is not quite right.** Ask for the exact format and who
  consumes it. Take the KG-author role immediately: edit the declarations under
  `pharos_kg/`, then run `kbs check` and the build. Do not write a post-build
  script.
- **5. I don't trust you; I want to build it myself.** Show the commands and step
  aside. Do not run them unless asked.
- **6. I still don't trust you; make a new graph for me.** Do this in order:
  1. Move the OpenCode session to `demo/`.
  2. In `demo/`, run `/kbs_init` with no task and let it create the project.
  3. Stop and report. Say: **“For this demo I will read `PURPOSE.md` as the
     task. `/kbs_auto` will be on, so I will make the design decisions and
     create a KG revision. Shall I proceed?”**
  4. Wait for the user's affirmation. Do not read `PURPOSE.md`, design, build or
     create a revision before they affirm.
  5. On affirmation, turn `/kbs_auto` on with `PURPOSE.md` as the task; it runs
     the demo and records the revision.


Ask once. If the user says "show me" or "go", give the one-paragraph summary and
point to `README.md`; do not start a build or a viewer until they ask for one.

## 1. Build the Pharos graph

Work in `pharos-kg/`:

```console
cd pharos-kg
uv sync
uv run kbs check --project pharos_kg
uv run kbs run --project pharos_kg
```

`kbs run` writes `build/`:

| Artifact | What it is |
| --- | --- |
| `build/graph.jsonl` | **the scored graph**: 28,359 nodes and 150,856 edges, the keep projection |
| `build/graph.annotated.jsonl` | the audit candidate, 74,747 / 239,939, including records marked `prune` |
| `build/evidence.jsonl` | one provenance entry per shipped record, keyed by `build_key` |
| `build/workflow_plan.json` | the compiled plan the design viewer reads |
| `build/meta_graph.html` | the component and step catalogue for design review |

The caches under `data/source/` mean a normal run downloads nothing. A cold
`data/` downloads and verifies each pinned release before building. Never edit
`build/` or the parquet cache by hand.

## 2. View the graph

From `pharos-kg/`, after at least one build:

```console
uv run kbs up --project . --port 8787
```

- the console is at `http://127.0.0.1:8787/console/` and reads `journal/events/`;
- the design viewer is at `http://127.0.0.1:8787/` and reads
  `build/workflow_plan.json`;
- `--no-open` is for a remote shell; `kbs console` serves the same two surfaces
  without opening both.

Tell the user the two URLs and leave the server running for the session.

## 3. Try the demo

`demo/` is deliberately not a framework project. It is the raw input:

```text
demo/isolates.csv
demo/antibiotics.csv
demo/susceptibility.csv
demo/resistance_genes.json
demo/PURPOSE.md
```

Open `demo/` as the OpenCode workspace (a new session there is the reliable
way), make sure the plugin is installed from the framework's plugin directory if
`/kbs_init` is not available, then say:

```
/kbs_init read PURPOSE.md for what I want
```

The agent reads the files, proposes the graph and its readers, and stops for
correction. After the user accepts, it declares and builds one layer at a time.
`/kbs_auto <task>` lets it finish the remaining work without asking between
layers and records the revision when the gates pass.
Do not copy the Pharos declarations into the demo; the point is the same method
on a new domain.

## 4. Explain the design or an edge

From `pharos-kg/`:

```console
uv run kbs check --project pharos_kg      # the authored argument, in one report
uv run kbs workflow --project pharos_kg   # the compiled plan
uv run kbs revision list                  # the design ledger
```

- `pharos-kg/docs/KG.md` is the detailed account of the graph's argument,
  evidence and limits.
- `pharos-kg/README.md` is the entry point.
- To explain a record, read `build/graph.jsonl` for the record and
  `build/evidence.jsonl` for its provenance, or open the console. Use the
  record's `build_key`; a label is never an identity.
- The annotated graph is not the asserted graph. Do not cite a `prune` record as
  part of the KG.

## 5. Edit the Pharos KG design for format X

If the user chooses this, ask for format X and its consumer if they are not
stated: the schema, the file or endpoint, and who reads it. Then:

1. **Ask before installing the plugin.** If it is not already installed, add
   the framework's `plugin/` directory to `~/.config/opencode/opencode.jsonc` with
   `frameworkUrl` pointing at the included framework directory. Do not edit the
   global config without the user's consent.
2. **Move to `pharos-kg/`.** It is already a framework project, so do not
   run `/kbs_init` again; use the design skill.
3. **Edit the design, not a script.** Decide whether X is a target (a named
   consumer) or a step in the existing workflow. Add the planner and executor
   that contribute the step under `pharos_kg/modules/`, declare the target in
   `pharos_kg/manifest.py`, and let the plan carry its configuration. The plan
   is the documentation; do not add a post-build script.
4. **Record the design change.** Record a finding and a proposal; a revision
   records it when approved.
5. **Run the gates:** `kbs check`, `kbs workflow`, `kbs run`; read the report,
   open the output, and add a test for its shape.
6. **A format with no named consumer is not a target.** Ask who reads it, or
   keep the conversion inside a step used by a named reader. If X needs a new
   property or record, state that in the proposal.

## Rules

- Build with `kbs`. There is no project-specific build script, no `ops/`, no
  `eval/` and no post-build rewriting.
- `pharos-kg/` is a pure declaration package: change the declaration tree
  (`asset/`, `graph/`, `relation/`, `binding/`, `manifest.py`) or a module under
  `modules/` when behaviour must change, or the tests; never
  `build/graph.jsonl`.
- The ledger in `pharos-kg/journal/events/` is append-only. A design change
  needs a finding, a proposal and (when approved) a revision. Do not record
  refactoring that changes no graph record.
- Do not edit the framework directory unless the user asks; it is the framework, not
  part of the graph.
- `demo/` is a data folder. A new project belongs in its own workspace, not in
  `pharos-kg/`.
- Keep the scored artifact small and honest: `pharos-kg/build/graph.jsonl`.
