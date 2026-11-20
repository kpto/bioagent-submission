# opencode-kbs

The OpenCode entry point for a `kg-build-system` project.

It adds two commands: `/kbs_init` and `/kbs_auto`.

```
/kbs_init                    # read the workspace, propose, wait for correction
/kbs_init <what you want>    # treat the request as the purpose and start
```

Run it in a **workspace**. Data may already be there; the command refuses only
when the workspace is already a kg-build-system project.

- **Without text**, the agent reads what is present or named, proposes what the
  graph is *for* — the question it answers, who reads it, the records and
  relations, and what it must not claim — records the proposal, and waits for
  your correction.
- **With text**, the agent treats what you wrote as the purpose you have already
  chosen. It records it as accepted, starts the first layer in that same turn,
  and asks only when a missing fact blocks it: the data, the scope, or who reads
  it.

### Autonomous mode

```
/kbs_auto <task>     # finish the task
/kbs_auto on         # continue the current task
/kbs_auto off        # leave the mode
```

In autonomous mode the agent declares, builds, runs and tests without asking for
approval to edit or continue. It finishes the task, records the proposals and the
revision they implement, and reports the revision code.

Then it hands over a fixed sequence:

1. clone the framework into `kg-build-system/`;
2. `kbs init graph` — copy the project template and create the records;
3. `uv sync` in `graph/`;
4. start `kbs console` in the background and give the user its URL — the
   iteration ledger is `/console/` (Findings, Proposals, Revisions, Evaluations),
   for decision review only;
5. `kbs check --project project`, `kbs workflow --project project`, and — once a
   target exists — `kbs run --project project`;
6. start `kbs view` in the background on port 8786 and give the user its URL —
   the graph is at `/`;
7. `pytest -q`, which on a fresh project fails on the two design-record tests by
   design: the template demands an answered `START-HERE.md` and a graph purpose.
8. write the proposal into `START-HERE.md` section 1 and the graph declaration's
   purpose and limitations, mark it as proposed until the user confirms it, and
   record it with `kbs proposal create`.

The console stays running for the session so the user can watch the ledger fill
with findings, proposals and revisions. The viewer stays running beside it; after
a design change, rerun `kbs workflow`; after a target exists, run `kbs run` and
refresh it.

The run is a conversation, not one prompt. Each stage ends with what was done,
what was recorded, what was assumed and one question or next command; the agent
does not try to finish the graph in one turn.

The layout it produces:

```
<project>/
  kg-build-system/   the framework checkout
  graph/             the project: project/, journal/, tests/
```

The plugin does not build the graph itself. It fixes the first interaction so
the agent meets the framework's own order, and the framework's checks are what
decide whether the project is valid.

## Install

Add the plugin directory to the global `opencode.jsonc`:

```jsonc
{
  "plugins": [
    "<path-to>/kg-build-system/plugin"
  ]
}
```

Options (all optional):

```jsonc
{
  "plugins": [
    {
      "package": "<path-to>/kg-build-system/plugin",
      "options": {
        "frameworkUrl": "<path-to>/kg-build-system",
        "frameworkDirectory": "kg-build-system",
        "projectDirectory": "graph"
      }
    }
  ]
}
```

The plugin’s built-in default is a placeholder, so set `frameworkUrl` when installing.
A local directory is copied by `/kbs_init`; a published checkout is cloned.

## Why a command and not a skill

A skill is advertised and the model chooses it; a command is a deliberate entry
point the user invokes. `/kbs_init` is the first step of the user story, so it is
a command. The design skill — how to change declarations rather than artifacts —
belongs on top of it: it is attached when design work starts, while the five
invariants ride every request.

## Viewer ↔ session queue

The console has no OpenCode dependency. It accepts `POST /api/request` with
`{ text, sessionID?, kind?, subject? }` and writes one file into
`.kbs/requests/<id>.json` under the project root. The plugin polls that
directory, claims a file by renaming it to `.processing`, prompts the session
(`sessionID` if given, otherwise the newest root session in the project), and
renames it to `.done.json` (or `.failed.json` with the error logged).

This is the bridge the viewer uses later: it posts a request, and the session
answers with the graph and the declarations in context.
