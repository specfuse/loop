---
id: FEAT-2026-0041/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces:
  - specfuse/monitor/diagnosis.py
  - tests/test_diagnosis.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T20:01:30.157491+00:00
duration_seconds: 652.781
cost_usd: 1.346094
input_tokens: 50
output_tokens: 9506
---

# The diagnosis contract: one renderer, one parser, one marker

**Objective.** Ship `specfuse/monitor/diagnosis.py` owning the diagnosis comment
format — a `Diagnosis` model, a renderer that produces the comment body with an
embedded machine-readable marker, and a parser that reads one back — so both entry
points and FEAT-2026-0042 share one contract rather than a convention.

**Context.** Correlation ID `FEAT-2026-0041/T01`. Read `PLAN.md` first — it records
why the contract lives in code rather than skill prose, the existing-mechanism search
that found no prior renderer, and the two reuse obligations below. Do not reopen those
decisions.

**Follow `issues.py`, do not invent a second convention.** That module already owns
this exact shape: `_MARKER_TEMPLATE = "<!-- specfuse:finding fingerprint={fingerprint} -->"`,
`_marker()`, `_parse_meta()`, and the documented rule that the marker in the body,
re-checked client-side, is the sole authority. Mirror it. A diagnosis marker that
looks different from a finding marker is a second dialect for a reader to learn.

**Reuse the redactor; do not copy it.** `specfuse/monitor/redaction.py` owns
`_redact_text(text)` and `_SECRET_PATTERNS` (connection strings, AWS key IDs, bearer
tokens, credential-shaped assignments) with digest-keyed replacement so repeats of one
secret redact identically. Diagnosis prose is agent-written text quoting logs and
source, so it is exactly the input those patterns exist for. `_redact_text` is
module-private: **promote it to a public name** and update `redact_artifact`'s internal
call. Do not duplicate the patterns — two redaction routines drift, and the one that
stops catching a shape does so silently.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The contract

A `Diagnosis` carries `root_cause`, `evidence`, `candidate_fix`, `confidence`, and
`fix_scope`. `fix_scope` is one of `small` / `large` / `external` and nothing else.
`confidence` is a bounded numeric or a small closed vocabulary — choose one and state
the choice in the module docstring; FEAT-2026-0042 gates on it, so an unbounded free
string is not acceptable.

Render produces a human-readable comment body with the structured fields carried in an
embedded marker. Parse recovers a `Diagnosis` from that body. Round-trip fidelity is
the property that matters: `parse(render(d)) == d` for every legal `d`.

Prose fields pass through redaction **on render**, at the boundary, before anything can
leave the process — the same posture `redact_artifact` takes.

This module does **not** call `gh`, does not post anything, and does not touch the
network. It formats and parses. The skill posts.

**Acceptance criteria.**

1. `tests/test_diagnosis.py::TestDiagnosis::test_render_parse_roundtrip_preserves_fix_scope`
   exists and **fails on HEAD before this WU runs** (`specfuse/monitor/diagnosis.py`
   does not exist, which counts as red).
2. That test asserts `parse(render(d)) == d` for a diagnosis of each legal
   `fix_scope`, and it passes after this WU's edits.
3. A test asserts an illegal `fix_scope` is rejected at construction or render with a
   named error — not silently coerced, and not accepted for a parser downstream to
   discover.
4. A test asserts diagnosis prose containing a secret-shaped value is redacted **on
   render**: the rendered body contains `<redacted:` and does not contain the secret.
   Use at least two distinct `_SECRET_PATTERNS` shapes, one being a connection string.
5. A test asserts the same secret appearing twice redacts to the **same** token and two
   distinct secrets redact to **distinct** tokens — the digest-keyed property, held as
   a test rather than inherited by assumption.
6. A test asserts parse returns a clear negative (None or a named exception, your
   choice — state it in the docstring) on a body with no marker, and on a body whose
   marker is present but malformed. Both, separately.
7. The redactor is **promoted, not duplicated**: assert with
   `grep -n "_SECRET_PATTERNS\|def .*redact" specfuse/monitor/redaction.py specfuse/monitor/diagnosis.py`
   and quote the output — `diagnosis.py` must show no pattern list of its own.
   `redact_artifact` still passes its existing tests.
8. `specfuse/monitor/diagnosis.py` does not import `gh`-invoking code and makes no
   subprocess or network call. Assert with
   `grep -n "^from \|^import \|subprocess\|requests\|urllib" specfuse/monitor/diagnosis.py`
   and quote it.
9. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `plugins/specfuse/skills/` and `.specfuse/skills/` — T02 owns the
skill. `specfuse/monitor/issues.py` beyond nothing at all: this WU adds no
comment-posting helper, per `PLAN.md`'s scope boundary. Anything under
`.specfuse/features/` other than this feature's folder.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (≥90%), `leak-scan`. Criteria 4–5 are the load-bearing ones —
a redaction test that only checks "some redaction happened" would pass while the
digest-keying is broken, so assert the token identity relation, not just presence.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
promoting `_redact_text` would break an existing `redact_artifact` caller in a way this
WU cannot fix within its own file set; a bounded `confidence` representation cannot be
chosen without knowing FEAT-2026-0042's gate semantics (state the ambiguity, do not
guess a threshold); or round-trip fidelity cannot hold for legal prose because the
marker encoding collides with comment syntax. Do **not** invoke `gh` from this work
unit under any circumstance — it is sandboxed, `gh` will fail with an invalid-token or
TLS error, and that failure is a sandbox artifact rather than a defect in your work.
Only T04 carries the sandbox escape.
