---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_progress_lines_end_to_end -v -b"
baseline:
  sha: fce5a393ff2821a0d50393c7e2c1d0a12b3f03ea
  probed_at: 2026-09-14T00:14:16.233181+00:00
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:3e1ed273ab9179bbc8a1519961dcece15f51277e:469f5a5045272287ff018c76696b3b05496d49d8:5ff66b6e4d8a264f23709ea60706111a4c59ed11:62cf11034f93aeb4422e624323f72a3f2f1bde8d:74a860f5ced9fba1950b8b0ab37b2402d2ae203d:764f3615ab36287de03ddb147c0182b4145e20fb:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:a32e8963721b36864c84ad7270d4b865fb7b2498:ba4e2ff68ff80b36054d003c5116bc9d9b3d3b1e:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  entry_sha: fce5a393ff2821a0d50393c7e2c1d0a12b3f03ea
  source: attributed:FEAT-2026-0106/T01
  failing: []
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:3e1ed273ab9179bbc8a1519961dcece15f51277e:5ff66b6e4d8a264f23709ea60706111a4c59ed11:62cf11034f93aeb4422e624323f72a3f2f1bde8d:764f3615ab36287de03ddb147c0182b4145e20fb:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:84637dd49a7692422a382aa2a935ef852a89a5ca:97bcab1bc7244262cec901f46035f51dfdd07278:b37abd23368ec1eafe7ac27bb03aa41f66a8a5b2:ba4e2ff68ff80b36054d003c5116bc9d9b3d3b1e:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:c27f4a5cc366b6aee765aeb37809923422c578ee:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-09-14T01:44:51.233125+00:00
  ok: true
  failing: []
---

# Gate 1 — progress lines replace unconditional reflection

## Definition of done

After a gate runs, `PROGRESS.md` in the feature folder carries one entry per
dispatched work unit, written by the driver from what the session already
returns. A gate that stayed on-plan closes without writing reflective prose;
a gate that went off-plan still gets it in full.

The `feature_oracle` above is the executable proof. It is **red today**:
`tests/test_progress_lines_end_to_end.py` does not exist. T01 is the tracer
bullet that makes it runnable and green; T02–T03 make each half correct.

Also required, as for every gate:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

Note the ordering hazard this gate creates for itself: T03 makes reflective
sections conditional, and this gate's own close is the first close to run
under that rule. If this gate stays on-plan, its own retrospective is the
first one the feature suppresses. That is the intended behaviour and also the
sharpest possible test of whether `PROGRESS.md` is a good enough substitute —
the close should say which it was.

## What this gate must not break

`judge.py:237-238` reads `RETROSPECTIVE.md` and slices `## Measurements` into
the judge's evidence bundle. Measurements are **not** reflective prose and do
not become conditional. A gate whose reflective sections were skipped must
still produce a retrospective the judge can take measurements from, or the
verdict path loses its evidence.

`assert_learnings_appended_or_noop` makes at least one added `LEARNINGS.md`
line the success signal of every close. This gate does not change that guard —
bounding `LEARNINGS.md` is deliberately out of scope (PLAN.md) — so a close
that skips reflective prose still appends its lesson or says nothing
generalizes.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** T03 changes when an
  existing obligation applies rather than flipping a default value or a
  severity, so no probe is required by §4. If the implementation turns out to
  need a `verification.yml` default to carry the opt-out, the probe applies to
  that unit.
- **Flag-scope table (§3).** T03 introduces the condition that selects between
  reflective and non-reflective closes. Confirm it carries a flag-scope table
  naming every closing requirement in the registry and whether the condition
  gates it.
- **Escalation-predicate satisfiability (§2).** No check is raised to `ERROR`
  in this gate.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and
why, anything the close got wrong. This is your record, not the agent's.>
