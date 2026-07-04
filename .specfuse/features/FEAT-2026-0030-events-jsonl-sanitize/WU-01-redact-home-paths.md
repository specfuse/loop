---
id: FEAT-2026-0030/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.75
produces: tests/test_events_redaction.py
produces_driver_helper: _redact_home_paths
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.3.6
started_at: 2026-07-04T15:36:46.818307+00:00
duration_seconds: 362.77
cost_usd: 1.192855
input_tokens: 13855
output_tokens: 9853
---

# Redact absolute home paths from event payloads at the flush chokepoint

**Objective.** Sanitize every `events.jsonl` write so agent-authored absolute
home-directory paths cannot reach the audit log (and therefore cannot trip the
pre-commit leak-scan and halt the gate), while preserving the audit signal.

**Context.** This is `FEAT-2026-0030/T01`. The loop driver buffers events via
`build_event` and writes them with `flush_events` (`specfuse/loop/loop.py:473`).
Agent-authored note fields — `agent_blocked_reason`, `failure_excerpt`, per-attempt
`notes` — flow into event payloads and get written verbatim. When such a field
quotes an absolute home path (e.g. a checkout location the agent grepped), the
repo's structural leak-scan flags it (`user-path`) and rejects the bookkeeping
commit. Observed live on FEAT-2026-0029/T01 (driver 0.3.6). The existing
`redact_leak_findings` helper (loop.py:1281, the #76 fix) only redacts text shaped
like a leak-scan FINDINGS label — a raw home path in an ordinary note never routes
through it. This WU adds the general chokepoint.

**Load-bearing constraint — self-contained, no repo-internal import.** The driver
(`loop.py`) ships in the pip package; `.specfuse/scripts/leak_scan.py` is
repo-internal and is NOT copied into target projects (issue #55, LEARNINGS
`leak_guard_specfuse_internal`). The redaction MUST be implemented with a
driver-local regex — do **not** `import` or `subprocess` `leak_scan.py`.

**Load-bearing constraint — commit-safe source (do not skip).** The driver commits
this WU's staged diff through the repo's pre-commit structural leak-scan **without
`--no-verify`**. That scan flags the pattern `/Users/<seg>/` (regex
`/Users/[^/\s]+/`) anywhere in the staged diff — including your new source and test
files. A naive redaction regex or test fixture will therefore get this WU's own
commit rejected and halt the gate (the source-code form of the very self-poison
this feature fixes). So NO contiguous `/Users/<seg>/` (or `/home/<seg>/`) literal
may appear in the committed source. Concretely:

- **Match regex:** write it so the source contains no literal `/Users/` substring.
  `re.compile(r"/(?:Users|home)/[^/\s]+/")` matches both macOS and Linux home
  prefixes at runtime yet contains no `/Users/` literal (it reads `/(?:Users|…`),
  so it is safe on the staged scan. Do NOT write `r"/Users/[^/\s]+/"` — that
  literal self-trips.
- **Test fixtures + assertions:** never embed a contiguous `/Users/<seg>/` literal.
  Build home-path inputs by concatenation, e.g. `HOME = "/Users/" + "alice/x"`
  (the trailing quote breaks the segment+slash the scanner needs), and assert
  absence via the compiled pattern (`assert not PAT.search(out)`), not via a
  literal `assertNotIn("/Users/alice/x", out)` (which self-trips).
- Note this differs from `leak_scan.py`'s OWN test files, which embed literals and
  were committed with `--no-verify` — you cannot rely on that here, because the
  driver's WU commit does not pass `--no-verify`.

Reference the binding rules under `.specfuse/rules/` (`result-contract.md`,
`never-touch.md`, `security-boundaries.md`); honor them rather than restating.

**Acceptance criteria.**

1. **Red test (fails on HEAD):** `tests/test_events_redaction.py::test_home_path_redacted_before_flush`
   builds an event whose `payload` (e.g. an `agent_blocked_reason`) contains a
   macOS home path constructed by concatenation (per the commit-safe note above —
   do not embed the literal), calls `flush_events` to a tmp path, reads the written
   JSONL back, and asserts the compiled home-path pattern no longer matches it. It
   fails on HEAD because no redaction exists.
2. A driver-local helper `_redact_home_paths(value)` recursively walks a JSON-ish
   value (dict / list / str / scalar) and, in every string leaf, replaces absolute
   home prefixes — `/Users/<name>/` (macOS) and `/home/<name>/` (Linux) — with a
   stable placeholder (e.g. `<redacted-home>/`). Non-matching text is preserved
   verbatim; the function is idempotent (running it twice changes nothing further).
3. `flush_events` applies `_redact_home_paths` to each event before writing, so the
   red test in AC1 passes. Additional table-driven cases pass: a `/home/<name>/`
   path is redacted; a nested-dict payload is redacted at depth; a list-of-strings
   value is redacted element-wise; a payload with no home path is written byte-for-
   byte unchanged; the audit fields (`correlation_id`, `event_type`, `source`,
   `failure_class`) survive unchanged.
4. **Dogfood integration:** a test (or the same test) writes an event carrying a
   home-path note through `flush_events` into a tmp file, and asserts that content
   contains no `user-path`-flagged token — i.e. it would pass this repo's
   `python3 .specfuse/scripts/leak_scan.py --staged`. (Invoke leak_scan against the
   produced file/text; do not couple the driver code to it.)
5. **Symbol + self-containment checks:**
   `python3 -c "from specfuse.loop.loop import _redact_home_paths, flush_events"`
   exits 0, and the driver source added/edited by this WU contains no reference to
   `leak_scan` (grep-checkable).
6. **Commit-safe source (enables this WU's own commit):** the files this WU stages
   (`specfuse/loop/loop.py`, `tests/test_events_redaction.py`) contain no contiguous
   `/Users/<seg>/` or `/home/<seg>/` literal — verify with the repo hook itself:
   after staging, `python3 .specfuse/scripts/leak_scan.py --staged` exits 0. (This
   is the same check the driver's commit will run; if it fails, this WU cannot
   commit. See the commit-safe note above for the regex/fixture construction.)

**Do not touch.** `.specfuse/scripts/leak_scan.py` (its allowlist and the existing
`redact_leak_findings` helper are out of scope — do not import, prune, or unify),
`lint_plan.py`, other features' files, `.git/`, secrets, generated dirs. The driver
owns all git. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests`), `coverage` (≥ 90%), `lint`
(`ruff check`), `security` (`bandit`). Plus the AC5 symbol/self-containment checks.

**Escalation triggers.** If `flush_events` cannot be made the single chokepoint
because some events.jsonl writes bypass it, emit `status: blocked` naming the bypass
rather than scattering redaction. If `_redact_home_paths` cannot be added to
`specfuse/loop/loop.py`, emit `status: blocked` — do not claim complete. Blocked is
a respectable outcome (`result-contract.md` rule 4).
