---
gate: 1
status: awaiting_review
feature_oracle: "python3 -m unittest tests.test_layout_end_to_end -v -b"
cost_budget_usd: 26.00
broad_run:
  tree: 04a24dd524a776f36a93b93e0f4a66c1afa7b26c:054923b0bea95ba720a9a42a693f4da9e9ea960f:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:1a99cf5b086cf7d21d38df7b39124d1fafd56826:243d8e82854c7b3f2eebefd227ea009bf7a342ea:27968248a450a842ccd187b7dce0fb0ded934866:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:61870de6daffa7805d95dacfc69772c1b19f3f8b:6a5f803b704e8325954fe471657909999d8ab0d8:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:9911f793735215d5ac45527509272c1afc5de7fe:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:fa2f4f88657587b6e3b560977858810846b1d366
  ran_at: 2026-10-28T01:50:24.414177+00:00
  ok: true
  failing: []
---

# Gate 1 — a project can declare its decision records, and nothing changes without one

## Definition of done

**Stated as an outcome.** Driven through `python3 -m specfuse.loop.layout` and
`lint_roadmap` against fixture repositories:

1. With no `.specfuse/layout.yml`, `layout get` prints today's default for every
   `decisions.*` key (`adr`, `docs/adr`, `{path}`); the rendered blocker link, the
   `lint_roadmap` findings on fixture roadmaps and the rendered roadmap template are
   byte-identical to HEAD's.
2. With `decisions: {style: entries, location: docs/decisions, link:
   "{location}/decisions.md#{id}"}`, `layout get` returns those values and
   `layout link` renders `[D-0007: …](../docs/decisions/decisions.md#D-0007)` from
   `.specfuse/`.
3. `lint_roadmap` accepts that Blocked-by link when `docs/decisions/decisions.md`
   carries the anchor, reports an ERROR naming the anchor when it does not, and an
   ERROR when a decision link's target is outside `decisions.location`.
4. A layout with an absolute path, `..`, a Windows drive or backslash form, or a
   symlink escaping the repository is an ERROR; a `paths:` block is a WARN naming the
   authoring follow-up.
5. With the entries style, the rendered roadmap template's Blocked-by example uses an
   entries link, and that example passes `lint_roadmap`.

The `feature_oracle` proves 1–5 end to end. It is red on the current tree (the module
does not exist); `FEAT-2026-0224/T01` is the walking skeleton that creates it and
turns clause 1's `get` half and clause 2's `get` half green, with every other clause
`unittest.skip` naming its owner (T02, T03, T04, T05, T07). A skip surviving to the
close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Goldens before consumers.** T04 records `lint_roadmap` findings on HEAD's
  behaviour; T05 may not start until T04 is `done` (graph edge). A golden regenerated
  inside T05 proves nothing.
- **From source, with a positive control** (`[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE]`).
  Every criterion invokes `python3 -m specfuse.loop.layout`, never an installed
  console script; every "no findings" assertion is paired with a fixture that fires.
- **Exemption scope** (`[FEAT-2026-0058/G1-CLOSE]`). The location check's scope unit
  is "a Blocked-by link that is not a FEAT ref and not an http(s) URL, only when
  `decisions:` is declared" — T05 states it as a criterion.
- **Expected `judge_editing` halt.** T01 edits `arm_eval.py`'s registry (PLAN
  decision 3).

## Reflection notes

<Written by the human at review time.>
