import { execFile } from "node:child_process"
import { existsSync, readdirSync } from "node:fs"
import { readdir, readFile, rename } from "node:fs/promises"
import { join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { promisify } from "node:util"

import { Plugin, Skill } from "@opencode/plugin"

/**
 * The entry point for a kg-build-system project.
 *
 * It teaches four things the source cannot say by itself: the design skill is
 * attached when design work starts, five invariants ride every request, generated artifacts
 * are protected by the project's permissions, and a failed `kbs check` or test
 * run is fed back to the session that caused it.
 */

type Options = {
  frameworkUrl?: string
  frameworkDirectory?: string
  projectDirectory?: string
}

const DEFAULT_URL = "https://github.com/your-org/kg-build-system"
const DEFAULT_FRAMEWORK_DIRECTORY = "kg-build-system"
const DEFAULT_PROJECT_DIRECTORY = "graph"
const REQUEST_POLL_MS = 1000
const CHECK_COOLDOWN_MS = 30_000
const SKILL_ID = "kg-design"

const INVARIANTS = `This is a kg-build-system project. Change declarations, never generated build artifacts.
Every declaration states a Meaning: a purpose with a user, claims and limitations.
An adapter decodes only; every transformation is a declared relation, stage or step.
A target is a consumer: add it only when the graph's purpose names who consumes it.
Read only this workspace and the sources the user names; use the framework checkout inside it.
Run \`kbs check\` and the project tests before reporting done.`

const AUTONOMY = `AUTONOMOUS MODE. Work the user's request to completion without asking for approval between layers.
- Read the data and make the semantic decisions yourself; state an assumption instead of asking, unless a missing fact blocks you.
- Declare sources, records, edges, derived relations and the target; run \`kbs check\`, \`kbs workflow\`, \`kbs run --project project\` and \`pytest\`; reconcile the outputs.
- Do not ask for approval to edit, declare, or continue. Finish the task.
- Fix a failure by changing the declaration, never the test or a built artifact; rerun until the gates pass.
- Record findings and proposals as you go.
- Record findings and proposals as you go. When the task is finished and the gates pass, create the proposal(s) the change needs and record the revision that implements them; report its code. Do not stop before the revision is recorded.`

type QueuedRequest = {
  id?: string
  text?: unknown
  sessionID?: unknown
  kind?: string
  subject?: string
}

type SessionLike = { id?: string; parentID?: string }

type CommandResult = { code: number; output: string }

const execFileAsync = promisify(execFile)

type KbsProject = { root: string; package: string }

function findProject(directory: string): KbsProject | undefined {
  for (const root of [join(directory, "graph"), directory]) {
    if (!existsSync(join(root, "journal", "events"))) continue
    let entries: string[]
    try {
      entries = readdirSync(root)
    } catch {
      continue
    }
    const packages = entries.filter((name) =>
      existsSync(join(root, name, "manifest.py")),
    )
    const name = packages.includes("project") ? "project" : packages[0]
    if (name) return { root, package: name }
  }
  return undefined
}

function projectRoot(directory: string): string | undefined {
  return findProject(directory)?.root
}

function tail(text: string, limit = 2000): string {
  const value = text.trim()
  return value.length <= limit ? value : `…${value.slice(-limit)}`
}

async function runCommand(cwd: string, args: string[]): Promise<CommandResult> {
  try {
    const result = await execFileAsync("uv", args, {
      cwd,
      timeout: 120_000,
      maxBuffer: 4 * 1024 * 1024,
    })
    return { code: 0, output: `${result.stdout ?? ""}${result.stderr ?? ""}` }
  } catch (error) {
    const failure = error as {
      code?: unknown
      stdout?: unknown
      stderr?: unknown
      message?: unknown
    }
    const code = typeof failure.code === "number" ? failure.code : 1
    return {
      code,
      output: String(`${failure.stdout ?? ""}${failure.stderr ?? ""}${failure.message ?? ""}`),
    }
  }
}

async function hasChanges(root: string): Promise<boolean> {
  try {
    const result = await execFileAsync("git", ["status", "--porcelain"], {
      cwd: root,
      timeout: 10_000,
      maxBuffer: 1_000_000,
    })
    return Boolean(result.stdout.trim())
  } catch {
    // Not a repository: run the check rather than skip it.
    return true
  }
}

async function projectFailure(
  root: string,
  packageName: string,
): Promise<string | undefined> {
  const check = await runCommand(root, [
    "run",
    "kbs",
    "check",
    "--project",
    packageName,
  ])
  if (check.code !== 0) {
    return `kbs check failed\n${tail(check.output)}`
  }
  const tests = await runCommand(root, ["run", "pytest", "-q"])
  if (tests.code !== 0) {
    return `project tests failed\n${tail(tests.output)}`
  }
  return undefined
}

async function newestSession(ctx: any, directory: string): Promise<string | undefined> {
  const page = await ctx.session.list({ directory, limit: 20 })
  const sessions: SessionLike[] = page?.data ?? []
  const root = sessions.find((session) => !session.parentID)
  return (root ?? sessions[0])?.id
}

function failed(claimed: string): string {
  return claimed.replace(/\.processing$/, ".failed.json")
}

function done(claimed: string): string {
  return claimed.replace(/\.processing$/, ".done.json")
}

async function handleRequest(ctx: any, directory: string, file: string): Promise<void> {
  const record = JSON.parse(await readFile(file, "utf8")) as QueuedRequest
  const text = typeof record.text === "string" ? record.text.trim() : ""
  if (!text) throw new Error("request has no text")
  let sessionID = typeof record.sessionID === "string" ? record.sessionID : undefined
  if (!sessionID) sessionID = await newestSession(ctx, directory)
  if (!sessionID) throw new Error("no session in this project to prompt")
  await ctx.session.prompt({ sessionID, text, delivery: "queue" })
}

async function scan(ctx: any, directory: string, requests: string): Promise<void> {
  let names: string[]
  try {
    names = await readdir(requests)
  } catch {
    return
  }
  for (const name of names) {
    if (
      !name.endsWith(".json") ||
      name.endsWith(".done.json") ||
      name.endsWith(".failed.json")
    ) {
      continue
    }
    const file = join(requests, name)
    const claimed = file.replace(/\.json$/, ".processing")
    try {
      await rename(file, claimed)
    } catch {
      // Another plugin instance claimed it first.
      continue
    }
    try {
      await handleRequest(ctx, directory, claimed)
      await rename(claimed, done(claimed))
    } catch (error) {
      await rename(claimed, failed(claimed)).catch(() => undefined)
      console.error(`[kbs] request failed: ${String(error)}`)
    }
  }
}

function instructions(
  frameworkUrl: string,
  frameworkDirectory: string,
  projectDirectory: string,
  request: string,
): string {
  const stated = request.trim()
  const conversation = `This is a conversation, not one request with one answer. Work in stages:
read and propose, then declare one layer, then the next. At the end of each
stage, stop and report what you did, what you recorded, what you assumed, and
what you need confirmed. Never try to finish the whole graph in one turn.`
  const audience = `Talk to the user in their domain, not in this framework's vocabulary. Say "the
file", "the rows", "the question", "the reader", "what it cannot tell you". Do
not say source relation, binding, derived relation, target, manifest, blueprint
or START-HERE in conversation; when you must name one, translate it in the same
sentence ("a step that joins the loans to the members"). A high-level question
is "who is this for, and what would they do with it?" - ask it only when the
data cannot answer it; otherwise propose and let them correct you. Put the
framework's words in the declarations and the plan, not in the chat.`
  const opening = stated
    ? `Initialise a kg-build-system project in this workspace.

The user states what they want:

  ${stated}

Treat that as the purpose they have already chosen. Do not ask them to restate
or confirm it. Read the data, record the purpose and its limitations, and start
the first layer of the graph in this turn. Ask at most one question, and only if
a missing fact blocks you - the data, the scope, or who reads it. Otherwise state
the assumption and proceed. If no data is present and the request names no
source, propose two or three public sources, say what each covers and its
licence, and fetch only after the user agrees.`
    : `Initialise a kg-build-system project in this workspace.

A graph is an argument, so start with the argument. Read before you ask.

1. Look at what is here, and at anything the user named: files, formats, what
   one row or record is, what identifies it, how the inputs connect, what is
   missing or contradictory.
2. Propose, in plain language and with evidence from what you saw: the question
   this data can answer, who would read the result, the records and relations
   you would declare, and what the graph must not claim. Do not ask the user to
   supply a specification; draft it and let them correct you.
3. Ask at most one question, and only if two materially different graphs are
   possible. Otherwise proceed and state what you assumed. If there is no data
   and the request says nothing, ask one open question: what are you trying to
   find out, and where is the data? If the request names a question but no
   source, propose two or three public sources, say what each covers and its
   licence, and fetch only after the user agrees; keep the raw response under
   \`data/source/\`.`
  return `${opening}

${conversation}

${audience}

This is a declaration-first framework. The declaration is the product and the
build is replaceable. Read its philosophy after step 1 with
\`uv run --project ${frameworkDirectory} kbs guide\`.

Preconditions:
1. If this is already a kg-build-system project (\`${projectDirectory}/\`,
   \`.kbs/\`, or a \`pyproject.toml\` declaring \`kg-build-system\`), stop and say
   so. Other files are input; do not delete or move them.
2. If \`uv\` is not on PATH, stop and say so.

Steps, in order:
1. If ${frameworkUrl} is a local directory, copy it:
   \`cp -R \"${frameworkUrl}\" ${frameworkDirectory}\`
   Otherwise clone it:
   \`git clone ${frameworkUrl} ${frameworkDirectory}\`
   Use that checkout for all framework reading; do not read another copy of
   the framework on the host.
2. \`uv run --project ${frameworkDirectory} kbs init ${projectDirectory}\`
3. Write \`opencode.json\` in this directory (the workspace root) with edit-deny
   rules for \`${projectDirectory}/build/*\` and
   \`${projectDirectory}/exports/*\`, copying the shape from
   \`${projectDirectory}/.opencode/opencode.json\`. This is how generated
   artifacts become read-only for the rest of the session.
4. \`cd ${projectDirectory} && uv sync\`
4b. Start the decision console in the background and give the user its URL:
   \`cd ${projectDirectory} && mkdir -p .kbs && setsid uv run kbs console --project . --host 127.0.0.1 --port 8787 --no-open > .kbs/console.log 2>&1 < /dev/null &\`
   The iteration ledger is at \`http://127.0.0.1:8787/console/\` (Findings,
   Proposals, Revisions and Evaluations). It is for decision review, not for
   reading the graph. Keep it running for the session; the user watches it while
   you work. If 8787 is taken, pick the next free port and report it. Use
   \`--host 0.0.0.0\` only when the user needs to reach it from another machine.
5. \`uv run kbs check --project project\`
6. \`uv run kbs workflow --project project\`
6b. Start the design viewer in the background and give the user its URL:
   \`cd ${projectDirectory} && mkdir -p .kbs && setsid uv run kbs view --snapshot build/workflow_plan.json --host 127.0.0.1 --port 8786 --no-open > .kbs/view.log 2>&1 < /dev/null &\`
   The graph is at \`http://127.0.0.1:8786/\`. Keep it running beside the
   console; the console is for decisions and the viewer is for the graph. If
   8786 is taken, pick the next free port and report it. After a design change,
   rerun \`uv run kbs workflow --project project\` and tell the user to refresh
   the viewer.
6c. When the project has a target, \`uv run kbs run --project project\` executes
   the declared plan and writes the artifact the target names. On a fresh
   scaffold with no target there is nothing to write. Read the report; if it
   fails, fix the declaration it names.
7. \`uv run pytest -q\`

Step 7 is expected to fail on a fresh project: the template's tests demand an
answered START-HERE.md and a graph declaration with a purpose. That failure is
the next task, not a defect.

Then write the purpose into the project:
- fill section 1 of \`START-HERE.md\`: the question, the reader, what it must not
  claim, and who consumes it. If the user stated the purpose, record it as
  accepted; otherwise mark it proposed and say so;
- replace the placeholder purpose in \`${projectDirectory}/project/graph/graph.py\`
  with the same purpose, keeping the declaration's existing shape;
- add a limitation for the thing it must not claim;
- record the purpose in the ledger (below); if the user stated it, record it as
  accepted rather than proposed;
- rerun \`uv run pytest -q\`. Stop when it is green, or when only the user can
  decide what to write. Never edit the tests, the template or the records to
  make a check pass.

Record decisions as you take them; chat is not the record. From
\`${projectDirectory}/\`:
- \`uv run kbs finding add --observation "<what you found>" --evidence "<what you saw>" --metric "<the gate it must move>"\`
- \`uv run kbs proposal create --subject "<the declaration>" --rationale "<what changes and why>"\`
- \`uv run kbs revision record --based-proposal P-1 --message "<what changed>"\` when the change is made
- \`uv run kbs evaluation run --revision B-1 --result '{"status": "passed"}'\` after the gates run
- \`uv run kbs revision list\` or \`uv run kbs finding list\` to read what is recorded
A proposal is adopted by the revision that names it, or withdrawn; there is no
separate accept step. Record the proposal before you build on it. Record the
user's correction as a new event, never as a silent edit.

Rules:
- Talk in the user's domain, not the framework's. Say what the graph answers,
  what it cannot answer, and what you need from them. Do not explain assets,
  relations, bindings, adapters, planners or steps unless they ask how it works.
  Do not narrate each declaration as you make it; work, then report the outcome.
- Report every command with its exit status. Stop at the first failure and quote
  the failing output rather than retrying with a different command.
- Never edit a built artifact, generated view or lockfile to make a step
  pass. If a check fails, read the declaration it names and change that.
- Do not invent files the template does not contain. The template is the
  starting point; the user's graph is written later.
- Add a target only when the purpose names a consumer; no consumer, no target.
- Leave the console running for the whole session. Do not stop it at the end of a
  turn; it is how the user watches the decisions arrive.
- A plan that is not run is not a graph. Once a target exists,
  \`uv run kbs run --project project\` must produce the artifact it names.
- End each turn with: what the user can now see or decide, what you recorded in
  one line, what you assumed, both URLs if they are running (decisions and
  graph), and the one question or next command. Keep it short; it is a report to
  the user, not a changelog. Then wait. Do not report the work as finished while
  a decision is still theirs.
- At the first stage boundary, tell the user they can say
  \`/kbs_auto <task>\` to let you finish the remaining work autonomously; it
  records the revision when the gates pass.`
}

export default Plugin.define({
  id: "kbs",
  async setup(ctx) {
    const options = (ctx.options ?? {}) as Options
    const frameworkUrl = options.frameworkUrl ?? DEFAULT_URL
    const frameworkDirectory =
      options.frameworkDirectory ?? DEFAULT_FRAMEWORK_DIRECTORY
    const projectDirectory =
      options.projectDirectory ?? DEFAULT_PROJECT_DIRECTORY
    const directory = ctx.location.directory

    const skillFile = fileURLToPath(
      new URL("../skills/kg-design/SKILL.md", import.meta.url),
    )
    let skillContent = ""
    try {
      skillContent = await readFile(skillFile, "utf8")
    } catch (error) {
      console.error(`[kbs] skill not found: ${String(error)}`)
    }
    if (skillContent && (ctx as any).skill?.transform) {
      await (ctx as any).skill.transform((editor: any) => {
        editor.add({
          id: Skill.ID.make(SKILL_ID),
          name: Skill.Name.make("KG design"),
          description:
            "How to change a kg-build-system graph: declarations, meanings, workflow steps, adapters and targets",
          path: Skill.Info.fields.path.make(skillFile),
          content: skillContent,
        })
      })
    }

    // The skill is a manual, not a mantra: attach it where design work starts
    // and after a session loses its history, not on every prompt. The five
    // invariants in `context` are what ride every request.
    const skillAttached = new Set<string>()
    const autonomous = new Set<string>()
    const designPrompt = /\b(node|edge|relation|binding|module|target|schema|meaning|declar\w*|adapter|record|graph)\b/i

    await ctx.session.hook("prompt", (event: any) => {
      if (!projectRoot(directory)) return
      const key = String(
        event.sessionID ?? event.prompt?.sessionID ?? event.session?.id ?? "default",
      )
      const text = typeof event.prompt?.text === "string" ? event.prompt.text : ""
      if (skillAttached.has(key) && !designPrompt.test(text)) return
      const skills = (event.prompt.skills ??= [])
      if (!Array.isArray(skills)) return
      if (!skills.some((item: any) => item?.id === SKILL_ID)) {
        skills.push({ id: SKILL_ID })
      }
      skillAttached.add(key)
    })

    await ctx.session.hook("context", (event: any) => {
      if (!projectRoot(directory)) return
      if (Array.isArray(event.system)) {
        event.system.push({ type: "text", text: INVARIANTS })
      }
    })

    await ctx.command.transform((editor) => {
      editor.add({
        name: "kbs_init",
        description:
          "Initialise a kg-build-system project; with a request, start from the purpose the user states",
        execute: async ({ sessionID, prompt, delivery }) => {
          const projectPath = join(directory, projectDirectory)
          let declaredProject = false
          try {
            declaredProject = (
              await readFile(join(directory, "pyproject.toml"), "utf8")
            ).includes("kg-build-system")
          } catch {
            declaredProject = false
          }
          if (
            existsSync(projectPath) ||
            existsSync(join(directory, ".kbs")) ||
            declaredProject
          ) {
            throw new Error(
              `/kbs_init expects a workspace without a kg-build-system project; ${projectPath} is already in use`,
            )
          }
          const input: any = {
            sessionID,
            text: instructions(
              frameworkUrl,
              frameworkDirectory,
              projectDirectory,
              prompt.text,
            ),
            delivery,
          }
          input.skills = [{ id: SKILL_ID }]
          await ctx.session.prompt(input)
        },
      })

      editor.add({
        name: "kbs_auto",
        description:
          "Finish the current task without asking for approval and record its revision",
        execute: async ({ sessionID, prompt, delivery }) => {
          const project = findProject(directory)
          if (!project) {
            throw new Error(
              "/kbs_auto expects a kg-build-system project; run /kbs_init first",
            )
          }
          const key = String(sessionID)
          const text =
            typeof prompt.text === "string" ? prompt.text.trim() : ""

          if (text.toLowerCase() === "off") {
            autonomous.delete(key)
            await ctx.session.instructions.entry
              .remove({ sessionID, key: "kbs-autonomy" })
              .catch(() => undefined)
            await ctx.session.prompt({
              sessionID,
              text: "Autonomous mode is off.",
              delivery,
            })
            return
          }

          autonomous.add(key)
          await ctx.session.instructions.entry.put({
            sessionID,
            key: "kbs-autonomy",
            value: AUTONOMY,
          })

          const task = text.toLowerCase() === "on" ? "" : text
          await ctx.session.prompt({
            sessionID,
            text: task
              ? `Autonomous mode is on. Work this request to completion:\n\n${task}\n\nDo not stop between layers or ask for approval to edit. Finish the task and record its revision.`
              : "Autonomous mode is on. Continue the current task; finish it without asking for approval to edit, and record its revision.",
            skills: [{ id: SKILL_ID }],
            delivery,
          })
        },
      })
    })

    const timer = setInterval(() => {
      const root = projectRoot(directory) ?? directory
      void scan(ctx, root, join(root, ".kbs", "requests"))
    }, REQUEST_POLL_MS)

    const lastFailure = new Map<string, string>()
    const lastRun = new Map<string, number>()
    const controller = new AbortController()
    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({
          types: ["session.idle"],
          signal: controller.signal,
        })) {
          const sessionID = (event as { sessionID?: string }).sessionID
          if (!sessionID) continue
          const project = findProject(directory)
          if (!project) continue
          const now = Date.now()
          if ((lastRun.get(sessionID) ?? 0) + CHECK_COOLDOWN_MS > now) continue
          lastRun.set(sessionID, now)
          let parentID: string | undefined
          try {
            const info = await ctx.session.get({ sessionID })
            parentID = (info as { parentID?: string }).parentID
          } catch {
            continue
          }
          if (parentID) continue
          if (!(await hasChanges(project.root))) continue
          const failure = await projectFailure(project.root, project.package)
          if (!failure) {
            lastFailure.delete(sessionID)
            await ctx.session.instructions.entry
              .remove({ sessionID, key: "kbs-check" })
              .catch(() => undefined)
            continue
          }
          if (lastFailure.get(sessionID) === failure) continue
          lastFailure.set(sessionID, failure)
          await ctx.session.instructions.entry.put({
            sessionID,
            key: "kbs-check",
            value: failure,
          })
        }
      } catch {
        // The subscription ended because the plugin unloaded.
      }
    })()

    return () => {
      clearInterval(timer)
      controller.abort()
    }
  },
})
