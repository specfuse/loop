---
id: FEAT-2026-0025/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
produces: .specfuse/scripts/learnings_query.py
oracle_env: macos_local
---

# CLI wrapper + load-whole threshold fallback

**Objective.** Expose the T01 retrieval primitive as a command-line tool a planning
consumer can call, and add a size-threshold fallback so slicing only engages once
`LEARNINGS.md` is big enough to matter.

**Context.** This is `FEAT-2026-0025/T02` (depends on T01's `parse_entries` / `rank`
in `.specfuse/scripts/learnings_query.py`). Gate 2 will have the planning skills
call this CLI to load the relevant slice. Below a threshold the whole file is
cheaper and safer to load verbatim (no relevance risk), so the tool must say so
rather than always slicing. Reference the binding rules under `.specfuse/rules/`;
honor them.

**Acceptance criteria.**

1. **Red test (fails on HEAD):** `tests/test_learnings_query.py::test_cli_below_threshold_signals_load_whole`
   invokes the module's CLI (via `subprocess`/`runpy`) against a small LEARNINGS
   fixture (entry count below the threshold) and asserts the output is the
   `load-whole` signal, not a ranked slice. Fails on HEAD because the CLI /
   threshold do not exist.
2. `should_load_whole(entries: list[dict], threshold: int) -> bool` returns `True`
   when `len(entries) < threshold`. The threshold has a module-level default
   (choose a sensible value, e.g. 40 entries, and name it a named constant) and is
   overridable via a `--threshold` CLI flag.
3. A CLI entrypoint (`python3 .specfuse/scripts/learnings_query.py "<query>"
   [--top N] [--threshold K]`) prints, when at/above threshold, the top-N ranked
   entries (each entry's `raw` bullet) via T01's `rank`; when below threshold, prints
   a single stable `load-whole` sentinel line (e.g. `LEARNINGS-LOAD-WHOLE`) that a
   consumer can detect. Reads the query from argv; reads `LEARNINGS.md` from the
   repo by default with an optional `--file` override for testing.
4. The red test passes after this WU. Additional cases pass: at/above threshold with
   a query returns a ranked slice (not the sentinel); `--top` bounds the count;
   `--threshold 0` forces slice mode even on a tiny file; a missing/empty
   `LEARNINGS.md` exits non-zero with a clear message (does not crash with a
   traceback).
5. **Symbol + CLI checks:** `python3 -c "import importlib.util,pathlib; s=importlib.util.spec_from_file_location('lq', pathlib.Path('.specfuse/scripts/learnings_query.py')); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert callable(m.should_load_whole)"`
   exits 0, and `python3 .specfuse/scripts/learnings_query.py "test" --file <tmp>`
   runs without error.

**Do not touch.** T01's `parse_entries`/`rank` semantics (build ON them — extend the
same module; do not rewrite the ranker), `.specfuse/LEARNINGS.md` content, the
driver and linter internals, other WUs' files, `.git/`, secrets. The driver owns
all git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` (`tests`,
`coverage` ≥ 90%, `lint`, `security`). Plus the AC5 symbol/CLI checks. If this WU
emits an operator-facing runnable, note it is a Python CLI (not a shell script), so
`/authoring-work-units` §11 (shellcheck/bats) does not apply — Python unit tests are
the oracle.

**Escalation triggers.** If T01's module is absent or does not expose
`parse_entries`/`rank`, emit `status: blocked` — there is nothing to wrap. If the
CLI cannot be added to `.specfuse/scripts/learnings_query.py`, emit `status:
blocked` — do not claim complete. Blocked is a respectable outcome
(`result-contract.md` rule 4).
