---
id: FEAT-2026-0064/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - scripts/bump_version.py
  - specfuse/loop/changelog.py
  - tests/test_changelog_release_wiring.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-04T14:43:21.010611+00:00
duration_seconds: 1164.828
cost_usd: 2.884429
input_tokens: 398
output_tokens: 43176
---

# Cutting a version stamps the section, and freezes it

**Objective.** Wire the CHANGELOG into `scripts/bump_version.py`: cutting a version
stamps `Unreleased` with the version, the date, and the umbrella version that ships
it — and a stamped section becomes immutable. Make the tag convention and the
version-source list configuration, not hardcode.

**Context.** Correlation ID `FEAT-2026-0064/T03`. Read `PLAN.md` first — it records
the umbrella decision and the portability requirement. T01 owns the parser; this WU
calls it.

**`bump_version.py` is already the atomic release point.** It sets all four version
sources — `pyproject.toml`, `DRIVER_VERSION`, `.specfuse/VERSION`,
`specfuse/loop/data/VERSION` — in one place. The CHANGELOG stamp belongs in the same
transaction: a version that exists in four files and not in the changelog is a release
nobody can read about.

**The umbrella version is required, not optional.** Releasing `specfuse-loop` alone
documents half a release: `pipx upgrade specfuse` resolves through the umbrella
package, so a driver version nobody can install is not a release. This repository
cannot bump the umbrella — that is a different repo — but it can refuse to stamp a
section that does not say which umbrella version ships this driver. Make it a required
input to the stamp, so the omission is impossible rather than merely discouraged.

**A stamped section is immutable, and that must be enforced.** The whole value is that
a consumer can trust a released section describes that release. If a later append can
land inside a shipped section — a close running after the bump, or a human tidying —
the document becomes a moving record of the past. Appends go to `Unreleased`; a write
targeting a stamped section is refused.

**It ships in the scaffold, so this repo's conventions are not a target project's.**
The tag convention (`v*`) and the four-source version list are ours. Both must be
configuration a target project can set. This is the part most likely to be skipped,
because the feature works locally without it — and the part that decides whether every
downstream project inherits a release process shaped like this one.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_changelog_release_wiring.py::TestChangelogReleaseWiring::test_stamped_section_refuses_a_later_append`
   exists and **fails on HEAD before this WU runs** (no stamp exists, which counts as
   red).
2. That test stamps `Unreleased`, then attempts an append targeting the stamped
   section and asserts it is refused with a message naming `Unreleased` as the only
   writable section. It passes after this WU's edits.
3. A test asserts stamping writes the version, the date, **and** the umbrella version,
   and that stamping **without** an umbrella version is refused — the omission must be
   impossible, not merely discouraged.
4. A test asserts a stamp leaves a fresh empty `Unreleased` section above the one just
   frozen, so the next append has a home without anyone creating it by hand.
5. A test asserts `bump_version.py` stamps as part of the same run that sets the four
   version sources — a version present in four files and absent from the changelog is
   the failure this criterion prevents.
6. **Portability.** A test asserts the tag convention and the version-source list are
   read from configuration with this repo's values as defaults, and that a target
   project supplying different ones is honoured. Assert on the config path, not on a
   hardcoded `v*`.
7. A test asserts stamping is idempotent or refuses a second stamp of the same
   version — whichever is chosen, state it in the docstring; a release script that
   silently double-stamps corrupts the document it exists to protect.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`. **Run any named suite in-process via `unittest.defaultTestLoader`,
   never by shelling out to `pytest`** — `tests/test_no_pytest_subprocess.py` fails
   the build if you reach for it.

**Do not touch.** `CHANGELOG.md`'s schema and the entry classes — T01's.
`close-discipline.md` and `fix-bug` — T02 owns the collection points. `git tag`,
`git push`, and PyPI upload: `bump_version.py` gains a CHANGELOG step, not a release
pipeline. The umbrella repository, which this feature cannot reach.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criteria 2 and 6 are
load-bearing: a mutable released section makes the whole document untrustworthy, and a
hardcoded tag convention exports this repo's release process to every project that
installs the scaffold.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
immutability cannot be enforced without the parser exposing something T01 does not
(that is an escalation, not a quiet edit to T01's module); the umbrella version cannot
be made a required input without `bump_version.py` growing an interactive prompt,
which would break its use in a script; or the version-source list cannot be
configured without changing what `bump_version.py` sets today, which would put an
existing release surface at risk for a portability gain.
