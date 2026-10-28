---
id: FEAT-2026-0224/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - tests/test_layout_end_to_end.py
  - tests/test_layout.py
  - specfuse/loop/layout.py
  - specfuse/loop/arm_eval.py
model: sonnet
effort: medium
gate_set: code
oracle_env: macos_local
---

# T01 — walking skeleton: `layout.yml` loads, and `layout get` answers every key

**Objective.** The thinnest path end to end. `python3 -m specfuse.loop.layout get
<key>` reads an optional `.specfuse/layout.yml` and prints the resolved value for
`decisions.style`, `decisions.location` and `decisions.link`, with today's defaults
when the file or the block is absent. This makes the oracle module exist and run; it
does not build validation or links well.

**Context.** `FEAT-2026-0224/T01`, the walking skeleton and the only unit permitted to
stub. Write `tests/test_layout_end_to_end.py` **first**, with classes:

- `NoLayoutGetIsToday` — no `layout.yml` in a temp repo: `get` prints `adr`,
  `docs/adr`, `{path}` (PLAN decision 7), exit 0.
- `EntriesLayoutGet` — the clause-2 `layout.yml`: `get` prints `entries`,
  `docs/decisions`, `{location}/decisions.md#{id}`.
- `EntriesLinkRenders` — `unittest.skip("owned by FEAT-2026-0224/T03")`.
- `NoLayoutGoldens` — `unittest.skip("owned by FEAT-2026-0224/T04")`.
- `LintChecksDecisionLinks` — `unittest.skip("owned by FEAT-2026-0224/T05")`.
- `InvalidLayoutIsReported` — `unittest.skip("owned by FEAT-2026-0224/T02")`.
- `TemplateFollowsStyle` — `unittest.skip("owned by FEAT-2026-0224/T07")`.

Every invocation is a subprocess of `sys.executable -m specfuse.loop.layout` with
`cwd` = the temp repo (or `--repo <dir>`), never an installed console script.

`specfuse/loop/layout.py`: parse with `specfuse.loop._miniyaml`; a frozen dataclass
`Layout` with a `decisions` field; `load(repo_root) -> Layout`; per-style defaults
exactly as PLAN decision 7; `get(layout, key) -> str` raising `KeyError` on an
unknown key (CLI: exit 2, message naming the valid keys); `main(argv)` with a `get`
subcommand and `--repo` (default cwd). Must not import `specfuse.loop.loop`. Module
docstring names this feature and states the "no file = today" contract.

Register `layout.py` in `arm_eval.py`'s non-judge module registry with a one-line
reason ("resolves layout.yml for lint_roadmap and skills; no arm/close/merge verdict
reads it"). This edit fires `judge_editing` at arm (PLAN decision 3) — expected.

Stubbable here, and only here: validation (T02 — accept any string), links (T03).

**Acceptance criteria.**

1. `tests/test_layout_end_to_end.py::NoLayoutGetIsToday` and `::EntriesLayoutGet`
   fail on HEAD (module absent) and pass after; every other oracle class is skipped,
   each naming its owner.
2. `tests/test_layout.py` covers: file absent; file present with no `decisions:`
   block; `style: entries` with `location` and `link` omitted (defaults applied);
   unknown key → `get` exits 2 naming `decisions.style`, `decisions.location`,
   `decisions.link`; and `grep -n "specfuse.loop.loop\|from .loop\|import loop"
   specfuse/loop/layout.py` returns nothing.
3. `python3 -m unittest tests.test_judge_path_registry -b` passes with `layout.py`
   registered as non-judge.

**Do not touch.** `lint_roadmap.py` (T05), skills (T06, T07), templates (T07).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_judge_path_registry -b`.

**Escalation triggers.** If `_miniyaml` cannot parse a `link` value containing `{`
and `#` without quoting, stop and escalate — the documented syntax would need quotes,
which is a user-facing decision.
