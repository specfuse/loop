# Getting started

This walks you from an empty project to a feature delivered by the loop, then
shows what to do when a run halts. It assumes you've read the one-minute pitch in
the [README](../README.md); for the full contracts see
[`methodology.md`](methodology.md) and for the interactive operations see
[`skills.md`](skills.md).

The driver is pure-stdlib Python; it installs from PyPI, and the interactive
skills ship as a Claude Code plugin. You install the tooling once, then scaffold
each project you want to drive with one command.

---

## 1. Install the tooling and scaffold your project

Install the umbrella package — it pulls the driver (`specfuse-loop>=0.3.0`) as a
dependency and puts the `specfuse`, `specfuse-loop`, and `specfuse-lint` commands
on your PATH. It's a command-line app, so **pipx** is the recommended installer
(isolated environment, no `--break-system-packages` on PEP 668 / externally-
managed Pythons):

```bash
pipx install specfuse           # recommended
# or, inside a virtualenv you control:
python3 -m pip install specfuse
```

> On Debian/Ubuntu/macOS-Homebrew Pythons a bare `pip install` into the system
> interpreter is blocked (`externally-managed-environment`). Use `pipx` (or a
> venv) — that's what puts `specfuse-loop` / `specfuse-lint` on PATH for the gate
> commands to find.

> **Windows: Git-Bash is required.** The driver runs natively on Windows (no WSL),
> but it routes gate commands through **Git-Bash** so a target repo's
> `verification.yml` (`&&`, `exit 1 || exit 0`, `bats`, globs) runs unchanged.
> Install [Git for Windows](https://gitforwindows.org/) — it ships `bash.exe`, no
> admin and no WSL feature needed — before running the loop. The driver prefers
> the Git-for-Windows `bash.exe` over the `C:\Windows\System32\bash.exe` WSL
> launcher; it also normalizes `python3` gate tokens to your Windows interpreter
> and resolves the `claude` CLI via `PATHEXT`, so gate commands authored on
> POSIX run as-is.

Enable the skills plugin in Claude Code (one-time):

```
/plugin marketplace add specfuse/specfuse
/plugin install specfuse@specfuse
```

Then scaffold the repo you want to drive:

```bash
specfuse init /path/to/your-project        # add --dry-run to preview, writes nothing
```

This writes `.specfuse/` (templates, rules, the durable docs, `verification.yml`,
and an empty `features/`) into your project and merge-safely wires `.claude/`
(`CLAUDE.md`, `settings.json` enabling the `specfuse@specfuse` plugin) plus a
`.gitignore` snippet. It refuses if `.specfuse/` already exists — use
`specfuse upgrade /path/to/your-project` to overlay a newer scaffold in place
without touching your authored files. (The skills come from the plugin, not from
files copied into your repo.)

> **Don't gitignore `.specfuse/`.** The loop's durable state lives there and must
> be committed for the loop to work.

> **Self-provisioning.** Every `specfuse-loop` run first version-syncs `.specfuse/`
> from the installed package (missing → scaffold, older → overlay, equal → no-op,
> never downgrades). So `pip install -U specfuse` followed by a run keeps the
> scaffold current — `specfuse upgrade` is the explicit equivalent. Disable with
> `--no-autosync` or `autosync: false` in `.specfuse/config`.

## 2. Match verification to your stack

`specfuse init` seeds `.specfuse/verification.yml`. Open it and make the `code`
gate set run *your* project's checks:

```yaml
code:
  - name: tests
    command: "pytest -q"
  - name: coverage
    command: "coverage report --fail-under=90"
  - name: lint
    command: "ruff check ."
  - name: security
    command: "bandit -r src -ll"
```

These commands are the **exit oracle**: the driver re-runs them itself after every
work unit and *they* decide whether the unit is done — the agent's own self-report
is advisory only ([methodology §5](methodology.md)). Keep this set in lock-step
with your GitHub branch protection, or an agent can pass locally and still be
unmergeable.

If your repo already has CI worth deriving from, run **`/derive-verification`** in
Claude Code instead of editing by hand — it inspects your CI and tooling and
drafts the file for you.

## 3. Author your first feature

Two ways to create a feature folder under `.specfuse/features/`:

- **Interactively (recommended):** run **`/pick-feature`** to choose from your
  roadmap, then **`/draft-feature`**. Draft-feature asks framing questions, then
  proposes a gate skeleton and gate 1's work units, writing only on your accept.
- **By hand:** start from the bare templates in `.specfuse/templates/`
  (`PLAN`, `GATE`, `WU`) and fill in a small first feature. (The
  `specfuse/loop` source repo also carries a worked example,
  `FEAT-2026-0001-health-endpoint`, if you want a complete reference to copy
  from.)

A feature folder holds:

| File | Owns | Who writes it |
|------|------|---------------|
| `PLAN.md` | the *shape*: gate order, WU membership, dependency edges, feature status | you / `draft-feature` (gate 1); `plan-next` (later gates) |
| `GATE-NN.md` | one gate's status and definition of done | you / the planner |
| `WU-*.md` | a single work unit: frontmatter + the prompt a fresh session receives | you / `draft-feature` / `plan-next` |

`draft-feature` writes the folder but doesn't commit it or switch branches, so
the loop will refuse to start until the folder is on its branch and committed.
Let the driver do both for you:

```bash
specfuse-loop --prepare      # create the PLAN.md `branch:`, commit the folder, then run
```

(Or by hand: `git checkout -b <branch>` from `PLAN.md`'s frontmatter, then
`git add` + `git commit` the feature folder.)

## 4. Validate before running

```bash
specfuse-lint .specfuse/features/FEAT-YYYY-NNNN-your-feature
```

The linter checks structure: every WU has the five mandatory sections, the closing
sequence is present and well-formed, dependencies resolve, IDs are well-formed.
Fix anything it flags before dispatching — it's far cheaper than a failed
dispatch.

## 5. Dry-run, then run

```bash
specfuse-loop --dry-run     # show the gate walked, in dep order, no dispatch
specfuse-loop               # the real thing
```

With no `--feature` flag the driver picks the single `active` feature. For each
ready work unit it:

1. marks the WU `in_progress`,
2. dispatches a **fresh** `claude -p` session with that unit's model and prompt,
3. runs the unit's verification **itself** as the exit oracle,
4. on pass, makes **one squashed commit** carrying the `Feature: FEAT-.../TNN`
   trailer.

A failed gate is discarded and re-dispatched to a fresh session carrying the
failure evidence, up to three attempts, then the unit is escalated to
`blocked_human` and the gate halts.

> **One driver per working tree.** The driver holds an exclusive lock on
> `.specfuse/.loop.lock`. A second driver on the same checkout exits immediately.
> To run two features at once, use separate `git worktree` checkouts. `--dry-run`
> is exempt.

## 6. The gate boundary — where you come back in

A gate ends with a **closing sequence** that runs automatically: it writes a
retrospective, promotes durable lessons to `LEARNINGS.md`, reconciles docs, and —
crucially — **drafts the next gate's work units** (as `draft`) so the next gate is
waiting for you to review.

Two things can happen at the boundary:

- **The gate auto-closes.** On a clean, on-plan gate the deterministic predicate
  (`gate_eval.py`) closes it without a reflective session — but `plan-next` still
  drafts the next gate, so the human review step still fires
  ([methodology §3](methodology.md)).
- **The driver halts with `awaiting_review`.** The next gate's WUs are in `draft`
  and the driver will refuse to execute them until you arm them. **Arming is the
  human checkpoint and is deliberately not automated.**

Run **`/arm-gate`**. It walks each drafted WU — accept / revise / reject — flips
the ones you accept to `pending`, marks the finished gate `passed`, and prints the
resume command. Read the `GATE-NN-REVIEW.md` the planner wrote first: it's
weighted toward where the planner was *least* certain.

Then re-run `specfuse-loop`. Repeat until the terminal gate is `done`.

## 7. Wrap up

When the terminal gate is `done`, run **`/wrap-feature`**: it pushes the feature
branch, opens a PR, optionally watches CI, and points at the next pick. Then
**`/roadmap-archive`** moves the finished feature's detail out of the active
roadmap.

---

## Operating a running loop

The driver runs unattended within a gate, but real runs hit snags. The map:

| Symptom | What it means | Do this |
|---------|---------------|---------|
| Driver halts, a WU is `blocked_human` | A unit failed three attempts or hit an escalation trigger | Run **`/gate-status`** for a diagnosis (root cause, options, recommended action) |
| You fixed the blocker (creds, dep, spec) | The WU is still `blocked_human` | Run **`/unblock-wu`** to re-arm it (`blocked_human → pending`, attempts reset), then re-run |
| Driver exits "could not acquire lock" | Another driver owns this checkout | Find/stop the other driver, or use a separate `git worktree` |
| A gate is `awaiting_review` | Normal gate boundary | Run **`/arm-gate`** (§6) |
| The feature isn't worth finishing | — | Run **`/abandon-feature`** — flips every WU/gate/PLAN/roadmap surface cleanly |
| A WU "passed" but wrote no code | Hollow pass | Tighten the WU's acceptance criteria and verification; see [`authoring-work-units`](skills.md) |

**Where the durable state lives** (nothing important is in a context window):

- `PLAN.md` / `GATE-NN.md` / `WU-*.md` frontmatter — current status of everything.
- `events.jsonl` (per feature) — the event log; every dispatch emits an
  `attempt_outcome`.
- `RETROSPECTIVE.md` — feature-local raw observations from each close.
- `LEARNINGS.md` (repo root of `.specfuse/`) — cross-feature durable lessons, read
  at planning time so each plan is better than the last. Run
  **`/learnings-suggest`** periodically to mine recurring failures into new
  entries.

When in doubt after a halt, start with **`/gate-status`** — it reads all of the
above and tells you where you stand.

## Fixing a bug (not a feature)

Bugs don't go through the feature methodology. Run **`/fix-bug`** with the issue
number or report: it's 1 bug = 1 branch = 1 PR, test-first. It refuses and
proposes promoting to a feature if the work turns out large or risky.

## Next

- [`methodology.md`](methodology.md) — the full gate-cycle contract.
- [`skills.md`](skills.md) — every skill, by lifecycle phase.
- [`concepts/ralph-lineage.md`](concepts/ralph-lineage.md) — why the loop is
  shaped the way it is.
