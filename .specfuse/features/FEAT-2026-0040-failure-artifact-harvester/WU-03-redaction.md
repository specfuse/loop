---
id: FEAT-2026-0040/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - specfuse/monitor/redaction.py
  - tests/test_artifact_redaction.py
produces_driver_helper:
  - redact_artifact
model: sonnet
effort: medium
gate_set: code
driver_version: 0.6.0
started_at: 2026-07-28T19:46:23.943831+00:00
duration_seconds: 228.185
cost_usd: 0.654674
input_tokens: 34
output_tokens: 8423
---

# Redact artifact text at the boundary, before anything can leave the process

**Objective.** Ship `redact_artifact`: every text field of a `FailureArtifact`
passes through a redaction pass before the artifact can be serialized, logged, or
sent anywhere.

**Context.** Correlation ID `FEAT-2026-0040/T03`. Depends on `T01` for
`FailureArtifact`. Independent of `T02` — fingerprints and redaction are separate
properties of the same artifact.

The harvester reads dead-lettered message bodies, exception messages, and log lines
from a customer's production environment and puts them in a GitHub issue. Whatever
was in that message body goes with it. Connection strings, tokens, and personal data
routinely appear in exactly those places, which is why the roadmap specifies "a
redaction pass before any artifact text lands in an issue."

**Build new — this is the §1 verdict, and the reason matters.** `PLAN.md` records
both halves. `redact_leak_findings` exists at `loop.py:2097` but is **marker-gated**:
it returns text unchanged unless the literal string `"leak-scan"` appears, because
its job is stopping captured hook stderr from self-poisoning the event log. On an
exception message it is a no-op — wrong threat model.

More decisively: its pattern source `leak_scan.py` lives **only** under
`.specfuse/scripts/` and is deliberately absent from `specfuse/loop/data/`, because
`leak_*` is specfuse-internal tooling that must not ship to scaffolded projects
(issue #55). **This harvester runs in consumer repositories, where that file does not
exist.** Importing it would produce something that works in this repo and crashes in
every project that installs it. Do not import from `leak_scan`, and do not vendor it.

**Reuse exactly one thing: the `<redacted:sha8>` convention.** Replacing a match with
a short stable digest of the value keeps the audit signal — the same secret is
recognisable across occurrences — without the live value surviving. For a
deduplicating harvester that property is not cosmetic: it is how "this token appeared
in 40 messages" stays answerable.

**A positive control is required, for the reason 0072 recorded.** A redaction pattern
that matches nothing passes a "no secrets in the output" assertion perfectly. The
control asserts the pattern *fires* on a purpose-built secret held as an in-memory
string, so a clean result is evidence the redactor works rather than evidence the
regex is dead.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`. `security-boundaries.md` governs what
may be read and emitted here.

**Acceptance criteria.**

1. `tests/test_artifact_redaction.py::TestRedaction::test_planted_secret_is_redacted_at_the_boundary`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/monitor/redaction.py` defines `redact_artifact(artifact)` returning a
   `FailureArtifact` whose text fields have been redacted.
3. An artifact whose observed text contains a planted secret yields no occurrence of
   that secret in **any** field of the returned artifact.
4. A redacted value is replaced by a stable short digest in the `<redacted:sha8>`
   shape, not by a fixed placeholder — two occurrences of the same secret redact to
   the same token, and two different secrets redact to different tokens.
5. **Positive control:** the redaction pattern produces at least one match against a
   purpose-built secret defined as a string literal in the test module. The secret is
   **not** written to any file on disk.
6. `grep -n "leak_scan" specfuse/monitor/redaction.py` returns no match — the module
   does not import repo-internal tooling that is absent in consumer projects.
7. Text containing no secret passes through unchanged — redaction does not mangle an
   ordinary exception message.
8. The failure **signature** used for fingerprinting survives redaction unchanged, or
   the test names which part is redacted and why. A redactor that alters the
   signature silently breaks T02's dedupe.
9. `python3 -m pytest tests/test_artifact_redaction.py -q` exits zero after this WU's
   edits (the same file named in criterion 1).
10. `python3 -c "from specfuse.monitor.redaction import redact_artifact"` exits zero.

**Do not touch.** `specfuse/monitor/artifact.py` — T01 owns it. `loop.py`'s
`redact_leak_findings` and anything under `.specfuse/scripts/leak_*` — this WU
deliberately does not reuse them and must not modify them. Files owned by T02.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus the scoped red/green run in criteria 1 and 9, the
symbol-existence import in criterion 10, the positive control in criterion 5, and the
grep in criterion 6 — an accidental `leak_scan` import passes every gate in *this*
repo and fails in every consumer.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: a
pattern broad enough to catch the secret shapes named in the Context cannot avoid
matching ordinary exception text, which would fail criterion 7 — report the conflict
rather than narrowing until both pass vacuously; redacting the observed text
necessarily alters the failure signature, making criteria 8 and 3 mutually
unsatisfiable; or the test fixture's planted secret trips this repo's own pre-commit
leak-scan, in which case report it rather than weakening the fixture until it is no
longer a realistic secret. If `specfuse/monitor/redaction.py` is absent from the
files you edited, emit `status: blocked` — do not claim complete.
