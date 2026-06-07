---
id: FEAT-2026-0003/T06
type: implementation
model: claude-sonnet-4-6
status: draft
---

# GitHubBackend(Backend) implementation — label-transition state backend

**Objective.** Implement `GitHubBackend(Backend)` in a new
`.specfuse/scripts/gh_backend.py` that emits feature
start/complete signals as GitHub issue label transitions
(observable by the orchestrator), and wire it into the
`make_backend(feat_fm)` factory landed in T05. Fully offline
testable via an injectable `gh` runner — no network call in this
WU's verification.

**Context.** Handoff brief §3.4 names the deliverable: *"At
minimum: emit feature started/completed signals the orchestrator
can observe (issue label transitions and/or the per-feature
event log)."* Handoff §"Seams to respect" requires *"Keep the
GitHub state-backend behind loop's existing `Backend` seam —
subclass/extend it, don't fork the driver."* T05 widened the
seam (`on_feature_start`, `on_gate_passed`,
`on_feature_complete`) and added a `make_backend(feat_fm)`
factory; this WU subclasses `Backend` and selects the subclass
when the feature's PLAN.md frontmatter declares
`source_issue_url` (the marker `adopt_feature.py` writes for
orchestrator-dispatched features per gate 2).

Read `.specfuse/scripts/gh_features.py` lines 22-36 — the
injectable `runner` pattern with a `_default_runner` that shells
to `gh` and a unit-test stub path. Mirror it exactly: same
signature shape, same `subprocess.run([...], check=True,
capture_output=True, text=True)` form, same bandit-clean
argument-list invocation. Read `.specfuse/scripts/adopt_feature.py`
to confirm where `source_issue_url` is written in PLAN.md
frontmatter (the URL identifies the issue this feature was
adopted from).

Read `[FEAT-2026-0003/G2-LESSONS]` on bundling: this WU is
exactly one new file + one new test module + one call to T05's
factory; no bundle, no hygiene WU needed.

**Label scheme (declared explicitly, per
`[FEAT-2026-0003/G1-LESSONS]` "specify the exact fields/keys"
rule).** The transitions are:

- `on_feature_start`: ensure `loop:in-progress` is added to the
  issue; remove `loop:complete` if present (re-entry safety).
- `on_gate_passed`: no label transition for v0.1 (gate-level
  observability stays in the per-feature event log; revisit if
  the orchestrator surfaces a gate-progress need). Hook is
  called but does nothing — documented as a no-op v0.1 stub.
- `on_feature_complete`: ensure `loop:complete` is added;
  remove `loop:in-progress` if present.

The `loop:in-progress` / `loop:complete` label namespace is
chosen to be distinct from `specfuse:feature` (the pickable
label set in gate 1) so a downstream orchestrator can query
`label:loop:in-progress` without conflating with discovery.

**Acceptance criteria.**
1. New file `.specfuse/scripts/gh_backend.py` exists with a class
   `GitHubBackend(Backend)` that overrides exactly three
   methods: `on_feature_start`, `on_gate_passed`,
   `on_feature_complete`. The signatures match T05's no-op
   defaults exactly. `set_wu` and `set_gate` are inherited
   unchanged from `Backend` (frontmatter writes happen
   identically — the GitHub angle is additive).
2. `GitHubBackend.__init__(self, repo: str, issue_number: int,
   runner=None)` stores `repo` (e.g. "owner/repo"),
   `issue_number` (int), and a `runner` callable defaulting to
   a module-level `_default_runner(args: list[str]) -> None`
   that shells out to `gh` with the argument list (bandit-clean,
   `check=True`, `capture_output=True`, `text=True`).
3. `on_feature_start` calls `runner(["gh", "issue", "edit",
   str(issue_number), "--repo", repo, "--add-label",
   "loop:in-progress", "--remove-label", "loop:complete"])`.
   `on_feature_complete` calls the symmetric `--add-label
   loop:complete --remove-label loop:in-progress`. The
   `--remove-label` for a label not present is tolerated (gh's
   behavior — if it errors, the runner raises and the call
   fails loudly; do NOT swallow).
4. `on_gate_passed` is a documented no-op v0.1 stub (one-line
   docstring naming why) — the call signature matches the
   inherited base.
5. `make_backend(feat_fm)` in `.specfuse/scripts/loop.py` is
   updated to return a `GitHubBackend(repo, number, runner=None)`
   instance when `feat_fm` contains a non-empty `source_issue_url`
   that parses to a `https://github.com/<owner>/<repo>/issues/<n>`
   shape; otherwise returns plain `Backend()`. URL parsing is
   strict (a regex; no `urllib.parse` heroics required) — the
   pattern is documented in a one-line comment.
6. `tests/test_gh_backend.py` (new file) tests:
   - `GitHubBackend` with a stub `runner` records the exact
     argument lists fired by each lifecycle method.
   - `on_gate_passed` calls the runner zero times.
   - `make_backend({})` returns a plain `Backend` (regression
     guard for T05's contract).
   - `make_backend({"source_issue_url":
     "https://github.com/owner/repo/issues/287"})` returns a
     `GitHubBackend` configured for `("owner/repo", 287)`.
   - A malformed `source_issue_url` (e.g. "not-a-url") still
     returns plain `Backend()` rather than raising — degraded
     fallback is safer than a crashed run.
7. The `code` gate set in `.specfuse/verification.yml` passes
   (tests, lint, security, coverage --fail-under=70). The new
   module is fully covered by `tests/test_gh_backend.py` — no
   gh network call fires.

**Do not touch.** Exactly THREE files change: `gh_backend.py`
(new), `tests/test_gh_backend.py` (new), `loop.py`
(`make_backend` body — same function landed in T05, single
edit). Hard boundaries:

- `gh_features.py`, `adopt_feature.py`, `lint_plan.py`,
  `_miniyaml.py` — untouched.
- `Backend` class signatures in loop.py — added in T05, do NOT
  modify here (only `make_backend`'s body changes).
- Any binding rule under `.specfuse/rules/`.
- Any skill under `.specfuse/skills/`.
- Generated directories, secrets, `.env`, `.git/`.
- The driver owns git. Do not run `git`.

Numeric bound: **exactly three files changed** (one new module,
one new test file, one function-body edit in loop.py).

**Verification.** The `code` gate set
(`.specfuse/verification.yml`'s tests, lint, security,
coverage). Per `[FEAT-2026-0003/G1-LESSONS]` (offline-first):
no network call. Per `[FEAT-2026-0003/G2-LESSONS]` failure-mode
rule: include a malformed-URL test that asserts graceful
fallback to plain `Backend()` — the rejection direction, not
just the happy path.

**Escalation triggers.**
- The `Backend` seam shape from T05 is incompatible with the
  GitHubBackend implementation (e.g. lifecycle hooks lack a
  signature this WU needs). Block; do NOT modify the T05 seam.
- `gh issue edit --add-label --remove-label` behavior is not
  what this WU assumes (e.g. `--remove-label` on a missing
  label raises non-zero). Block with the observed `gh` error
  text; the label-scheme decision is then a review question.
- `make_backend`'s detection rule produces ambiguous results
  for a real adopted feature (e.g. `source_issue_url` is
  present but malformed in some way `adopt_feature.py`
  actually writes). Block; the URL contract belongs upstream
  in adopt_feature.py, not patched downstream.
