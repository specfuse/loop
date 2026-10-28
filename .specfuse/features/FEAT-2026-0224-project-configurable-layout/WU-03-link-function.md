---
id: FEAT-2026-0224/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - tests/test_layout_link.py
  - tests/test_layout_end_to_end.py
  - specfuse/loop/layout.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.29.1
started_at: 2026-10-28T00:41:57.567183+00:00
duration_seconds: 35.045
cost_usd: 0.168622
input_tokens: 10
output_tokens: 3858
---

# T03 — one function renders a decision link, and one checks it

**Objective.** Oracle clause 2 goes green. Link building and link checking for a
decision are deterministic code in `layout.py`, not prose in a skill, so
`block-feature` and `lint_roadmap` cannot disagree.

**Context.** Two public functions, sharing one parser of the `link` template:

- `render_link(layout, *, target, label, from_dir, domain=None) -> str` — `target` is
  a repo-relative path for `adr` style (fills `{path}`) and an id for `entries`
  (fills `{id}`); returns `[label](href)` where a repo-relative href is made relative
  to `from_dir` (e.g. `.specfuse` → `../docs/…`). An `http(s)://` result is returned
  unrelativised. A placeholder the call does not supply (e.g. `{domain}` with no
  `domain`) raises `ValueError` naming it.
- `split_link(href) -> (path, fragment | None, is_url)` — the one parser T05 uses to
  strip a fragment before the file check.

CLI: `python3 -m specfuse.loop.layout link --target T --label L [--from DIR]
[--domain D]` prints the rendered link (default `--from .specfuse`).

Tests in `tests/test_layout_link.py`:
- No layout: `target=docs/adr/0007-event-schema-versioning.md`,
  `label="ADR-0007: event-schema versioning"` renders exactly
  `[ADR-0007: event-schema versioning](../docs/adr/0007-event-schema-versioning.md)`
  — the example in `plugins/specfuse/skills/block-feature/SKILL.md:83`.
- Entries `{location}/decisions.md#{id}` → `../docs/decisions/decisions.md#D-0007`.
- Entries `{location}/{domain}.yaml#{id}` with `domain=billing` →
  `../docs/decisions/billing.yaml#D-0007`; without `domain` → `ValueError`.
- `https://wiki.example.com/decisions/{id}` → URL unchanged, not relativised.
- `split_link` on a path, a path with fragment, a bare fragment and a URL.

Un-skip `EntriesLinkRenders` in the oracle module (clause 2's link half, via the CLI).

**Acceptance criteria.**

1. `tests/test_layout_link.py` and
   `tests/test_layout_end_to_end.py::EntriesLinkRenders` fail on HEAD and pass after.
2. The no-layout ADR case is asserted against the literal string from
   `block-feature/SKILL.md:83`, not a recomputed value; and `grep -c "def render_link\|def split_link" specfuse/loop/layout.py` = 2, and no
   other module in `specfuse/` defines a decision-link renderer.

**Do not touch.** `lint_roadmap.py` (T05), `block-feature` (T06).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_layout -b`.

**Escalation triggers.** If relativising from `from_dir` disagrees with how
`lint_roadmap` resolves hrefs (`doc.path.parent / href`), stop — the two must use the
same base.
