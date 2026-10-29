---
id: FEAT-LOOP-2026-0224/T07
type: implementation
status: done
attempts: 2
planned_cost_usd: 3.00
produces:
  - specfuse/loop/data/roadmap.template.md
  - .specfuse/roadmap.template.md
  - specfuse/loop/scaffold.py
  - specfuse/loop/layout.py
  - plugins/specfuse/skills/attention/SKILL.md
  - .specfuse/skills/attention/SKILL.md
  - plugins/specfuse/skills/gate-status/SKILL.md
  - .specfuse/skills/gate-status/SKILL.md
  - plugins/specfuse/skills/groom-backlog/SKILL.md
  - .specfuse/skills/groom-backlog/SKILL.md
  - plugins/specfuse/skills/pick-feature/SKILL.md
  - .specfuse/skills/pick-feature/SKILL.md
  - plugins/specfuse/skills/roadmap-add/SKILL.md
  - .specfuse/skills/roadmap-add/SKILL.md
  - docs/methodology.md
  - docs/skills.md
  - tests/test_layout_no_layout_goldens.py
  - tests/test_layout_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.29.1
started_at: 2026-10-28T01:30:36.254269+00:00
duration_seconds: 142.708
cost_usd: 0.670664
input_tokens: 56
output_tokens: 12726
---

# T07 — the roadmap template and blocker wording follow `decisions.style`

**Objective.** Oracle clause 5 and clause 1's template half go green: the roadmap
template is rendered through the layout when seeded, and no skill or doc tells an
entries-style project its blockers are ADRs.

**Context.** `layout.render_roadmap_template(text, layout) -> str`: with the default
layout returns `text` unchanged (byte-identical); with `entries`, replaces the
Blocked-by example (`roadmap.template.md:37`) and the paragraph at line 39 with an
entries example built by `render_link` and wording that names the style. The
template marks the replaceable region with HTML comments
(`<!-- layout:decisions-example -->` … `<!-- /layout:decisions-example -->`) so the
render is a region swap, not a string search. `scaffold.py`'s user-seed write of
`roadmap.md` (line ~628, create-if-absent) passes the template through it. Edit
`specfuse/loop/data/roadmap.template.md` and copy to `.specfuse/roadmap.template.md`
(canonical direction for data: `.specfuse/` → `specfuse/loop/data/`; whichever you
edit first, both must be byte-equal).

Wording, style-neutral ("a decision awaiting approval — an ADR or a decision entry,
per `layout.yml`"), in canonical `plugins/` then `.specfuse/` copies:
`attention/SKILL.md:120`, `gate-status/SKILL.md:63`, `groom-backlog/SKILL.md:156`,
`pick-feature/SKILL.md:52`, `roadmap-add/SKILL.md:38`; and `docs/methodology.md:29`,
`docs/skills.md:52` (found by the replaced-wording grep, PLAN existing-mechanism
search).

Add to `tests/test_layout_no_layout_goldens.py`: no layout →
`render_roadmap_template` output equals the committed template bytes, and a fresh
`init_specfuse` seed of `roadmap.md` equals HEAD's seed. Un-skip
`TemplateFollowsStyle`: entries layout → rendered template contains no `docs/adr`
and its Blocked-by example, placed in a fixture roadmap with the target file and
anchor present, passes `lint_roadmap`.

**Acceptance criteria.**

1. `tests/test_layout_end_to_end.py::TemplateFollowsStyle` fails on HEAD and passes
   after; the two new golden cases pass; `tests.test_layout_end_to_end` has no
   `unittest.skip` left.
2. `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b`
   passes.
3. `grep -rn "an ADR" plugins/specfuse/skills/{attention,gate-status,groom-backlog,pick-feature,roadmap-add}/SKILL.md docs/methodology.md docs/skills.md`
   returns nothing.

**Do not touch.** `block-feature` (T06). `lint_roadmap.py` (T05). `upgrade_specfuse`'s
handling of an existing `roadmap.md` (project-owned; never re-rendered).

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync tests.test_layout_no_layout_goldens -b`.

**Escalation triggers.** If the region markers would change the seeded `roadmap.md`
bytes for a no-layout project, keep the markers out of the rendered output (strip
them) rather than accept a seed change — escalate if neither is possible.
