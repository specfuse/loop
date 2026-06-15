# GATE-02-REVIEW — FEAT-2026-0020 (Public-readiness prep)

Written by `FEAT-2026-0020/G1-PLAN` at the gate-1 → gate-2 boundary. Summarizes what
gate 1 produced, what gate 2's drafted substantive WUs should produce, and the
operator decisions to settle **before arming** gate 2 (`/arm-gate`).

---

## Gate-1 summary

Gate 1 (Audit) ran six substantive WUs (T01–T06) producing `AUDIT.md` across five audit
classes plus a post-remediation rescan, then closed via the two-WU intermediate sequence
(`G1-CLOSE-INTERMEDIATE` + this `G1-PLAN`). Secrets scan: zero findings (`gitleaks`
v8.30.1 over 261 commits). Personal-refs + cross-pollination converged on one private-org
cluster and a leaked `INIT-2026-0001-F06` folder, both redacted in-place by operator
commits (`7b3267c`, `b5d5404`); license headers brought to 31/31 via
`insert-license-headers.py`. The `gh` issue/PR surface was audited + remediated entirely
out-of-loop (the `gh`↔`claude -p` auth bug). **Audit verdict: `red — see open actions`** —
the one open action is the deferred phase-2 commit-history rewrite
(`history-scrub/scrub-history.sh`), carried into gate 2's flip-readiness. Gate-1
substantive cost: **$3.02 actual vs $7.80 planned** (−61.3%; every WU under budget — the
scan-and-triage WUs were over-estimated against an implementation-WU baseline).

## Gate-2 substantive WUs

Nine substantive WUs drafted (`status: draft`). Hygiene/config/detector WUs (T01–T06) do
not block each other — gate 1 is the barrier — so each carries `depends_on: []`. T07 wires
the detector; T08 references all outputs; T09 is the operator checkpoint.

- **T01 — `WU-01-readme-polish.md`** — Add a 60-second pitch (first 15 lines) + a
  copy-pasteable `## Quickstart` to `README.md`. Preserve existing suite framing. Content
  WU, red-test exempt.
- **T02 — `WU-02-contributing.md`** — Expand the existing `CONTRIBUTING.md` with how to run
  tests/gates locally, the PR workflow, and the methodology-dogfood expectation
  (changes go through `.specfuse/features/`). Content WU, red-test exempt.
- **T03 — `WU-03-security-and-conduct.md`** — `SECURITY.md` (disclosure channel +
  supported-versions) and `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1 unmodified),
  bundled per the per-WU sizing rule. Content WU, red-test exempt.
- **T04 — `WU-04-github-templates.md`** — `.github/ISSUE_TEMPLATE/` ×3 (bug, feature,
  methodology-question) + `.github/pull_request_template.md`. Config/content, red-test
  exempt.
- **T05 — `WU-05-dependabot.md`** — `.github/dependabot.yml` for `github-actions` + `pip`,
  weekly. Config WU, red-test exempt.
- **T06 — `WU-06-leak-scan-script.md`** — **The leak-prevention guard core** (operator-
  requested deliverable). `.specfuse/scripts/leak_scan.py`: one detector
  (`scan_text`/`scan_staged`) for secrets (`gitleaks`), `/Users/<user>/` path shapes,
  emails, private hostnames, and a denylist; allowlist exempts `INIT-2026-0001`; **only
  structural regexes committed** (literal org-names never inlined). Real implementation
  WU — red→green test + symbol-existence + coverage ≥ 90%. **Not** red-test exempt.
- **T07 — `WU-07-leak-scan-wiring.md`** — Wire T06 into its callers: a repo-tracked
  `pre-commit` hook (read-only, sandbox-safe, installed via `core.hooksPath`, `--no-verify`
  documented) + a `leak-scan` gate in `.specfuse/verification.yml` mirrored into
  `scripts/smoke-test.sh` and `ci.yml`. Hook is an executable artifact → §11 shellcheck +
  `bash -n` + bats happy-path.
- **T08 — `WU-08-flip-checklist.md`** — `FLIP-CHECKLIST.md`: ordered flip steps, each with
  owner + rollback; pre-flip steps gate on T01–T07 outputs and the gate-1 deferred
  history-rewrite open action. Markdown runbook, red-test exempt.
- **T09 — `WU-09-flip-rehearsal.md`** — Operator runs the checklist (dry-run rehearsal);
  records per-step disposition. **`blocked_human` by design** — the flip is operator-side;
  a dispatched session cannot reach the `gh`/GitHub-UI surface. Red-test exempt.

Closing: **`G2-CLOSE` is terminal** (single-WU `close`, not `close-intermediate`) and now
`depends_on` every substantive WU T01–T09. Its identity (`id`/`file`) is unchanged from the
pre-existing scaffold.

## Open verifications (operator decisions before arming)

1. **File-bundle confirmation.** T03 bundles `SECURITY.md` + `CODE_OF_CONDUCT.md` into one
   WU (both small, standard). Confirm the bundle, or split into two WUs at arming.
2. **T06 sizing — split or keep.** The leak-guard was split into detector (T06) +
   wiring (T07) to respect the per-WU sizing rule (`/authoring-work-units` §6). Gate 1's
   retrospective flagged over-bundling as a sizing risk. Confirm the 2-WU split, or
   re-bundle / split further (e.g. separate the allowlist) at arming.
3. **SECURITY.md disclosure channel (legal/maintainer review).** Decide the exact channel
   text **before** dispatching T03: **GitHub Security Advisories** (private vulnerability
   reporting, enable in repo settings) **OR** a direct project email fallback **OR** both.
   The same value fills the Contributor Covenant 2.1 enforcement-contact in T03. T03 blocks
   if this is unchecked at dispatch (it must not invent an address). ☐ unchecked.
4. **FLIP-CHECKLIST PyPi-tag scope (cross-feature with FEAT-2026-0019).** Decide whether
   `FLIP-CHECKLIST.md` (T08) **stops at the GitHub visibility flip** or **includes
   FEAT-2026-0019's first PyPi tag step**. The roadmap sequencing constraint is "0020 must
   precede 0019's first PyPi tag" — see Cross-feature note below. T08 blocks if undecided.
   ☐ unchecked.
5. **Gate-1 deferred history rewrite (the one open action).** Gate 1 closed `red` because
   the phase-2 commit-history rewrite (`scrub-history.sh`, `RETROSPECTIVE.md` §"What the
   loop did NOT verify" entries 5–6) is not yet run. Confirm whether it must be **closed
   before** the gate-2 flip rehearsal (T09), or accepted as residual risk and documented in
   the checklist. ☐ unchecked.

## Cross-feature note — FEAT-2026-0019 coupling

The roadmap names a one-directional sequencing constraint: **0020 must precede 0019's first
PyPi tag** (a public wheel is coherent only on a public repo whose history is clean).
Gate 1's retrospective surfaced **no** ordering tension requiring PyPi-tag *tooling* to land
in 0020 — the tooling belongs in 0019. The only coupling is Open Verification #4: whether
the *checklist* should enumerate the PyPi-tag step as a downstream pointer. Per
`GATE-02.md` escalation trigger 2, gate 2 does **not** pull 0019 implementation scope in;
T08 only references the step if the operator opts in.

## Cross-repo / cross-surface contracts (verify against source before arming)

Per `/authoring-work-units` §8 — values that live in another system, drafted here and
flagged for confirmation against the authoritative source. Each is `☐ unchecked` until the
operator verifies it at arming.

| Contract value | Drafted in | Authoritative source | Status |
|----------------|-----------|----------------------|--------|
| Issue-template front-matter keys (`name`, `about`/`description`, `labels`) + optional issue-forms `.yml` schema | T04 | GitHub issue-template / issue-forms docs | ☐ |
| Any `labels:` referenced by issue/PR templates (must exist or be created GitHub-side) | T04 | The repo's GitHub label set | ☐ |
| Dependabot `package-ecosystem` identifiers (`github-actions`, `pip`) + `schedule` schema | T05 | Dependabot `dependabot.yml` docs | ☐ |
| Dependabot `pip` `directory:` (assumes `pyproject.toml` at `/`) | T05 | The repo's manifest location | ☐ |
| `gitleaks protect --staged` invocation shape for the staged surface | T06 | `gitleaks` 8.30.1 CLI (on PATH) | ☐ |
| SECURITY.md / Covenant contact channel | T03 | Operator decision (Open Verification #3) | ☐ |

---

*Existence/lint checks for this drafting WU pass: nine `WU-0N-*.md` gate-2 files present,
this review file non-empty, PLAN.md gate-2 `work_units` carry real `FEAT-2026-0020/T01..T09`
ids beyond the `G2-CLOSE` scaffold, and `lint_plan.py` is clean on the feature folder.*
