---
gate: 1
status: passed
feature_oracle: "python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e -v -b"
cost_budget_usd: 40.00
broad_run:
  tree: 05c7d35dfced49fc45a5b1bae48deefa91e7d587:06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:45fc1aec6b9cb8bfc5073ad076dacada7201b19e:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:76d80fe022b7a6d17a55a3aa02047f136c9f4f45:79b3349ea5b92de69b7eaafa8e8762a22f2751e9:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:a54ed5c3b1f12d731a871c686abc7804d121cf31:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d664745f3d8e8d366a9f5029d78452efa5fda16f:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-09-26T19:38:15.130601+00:00
  ok: true
  failing: []
---

# Gate 1 — a re-close measures only what failed

## Definition of done

When a gate's `close` is re-armed after a first close ran, the second close's
re-verification worklist lists every `narrow` criterion the first close proved
green as carried forward, unless the gate diff since that entry's
`proved_at_sha` touches a path the entry covers — those, every `broad` entry,
every failed or unverified entry, and the `feature_oracle` are re-measured. The
second close's `## Measurements` states how many criteria were carried and how
many re-measured, and the judge's bundle shows each carried entry with the sha
it was proved at.

The `feature_oracle` above is that claim, executable. It is **red on the tree
this gate starts from** (the module does not exist), and T01 — the walking
skeleton — is what makes it green. It drives `loop.run()` twice over one
feature: the first close's stubbed session writes `GATE-01-CRITERIA.md` with
two narrow passes and one broad pass and records `not_met`; the test re-arms
the close (`attempts: 0`, `re_arm_count` bumped) and runs again; the oracle
asserts the second dispatch's prompt lists both narrow entries under "Carried
forward" and the broad entry under "Re-verify", and that the entries on disk
still read `pass` with their original `proved_at_sha`.

Also required for the gate to close:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are staged (feature-local `LEARNINGS-pending.md`).
- Documentation reflects what was actually built, canonical and mirror.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is the feature's terminal gate, so its closing sequence is a single `close`
unit and the terminal verdict is written by a fresh judge session.

## The sites and the switch

| surface | today | after this gate |
| --- | --- | --- |
| `_precreate_criteria_state_stub` re-arm reset (#3279) | resets every entry with `attempt > current` | resets `broad` entries and invalidated `narrow` entries only |
| `build_reverification_worklist` | carries narrow passes, ignores the tree | carries narrow passes whose `covers:` paths are untouched since `proved_at_sha` |
| criteria entry | no `covers:` | driver-seeded `covers:` (unit `produces:` + oracle test path) |
| close `## Measurements` / judge bundle | no carry accounting | `carried: N, re-measured: M`; carried entries listed with sha |
| `verification.yml` `defaults.carry_forward_narrow_greens` | absent | `false` restores today's reset; absent means on |

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** T01 flips a default (a
  re-armed close keeps narrow greens). Before arming, run
  `python3 -m unittest tests.test_rearm_clears_stale_criteria_state tests.test_criteria_worklist tests.test_loop_criteria_skeleton tests.test_lint_closing_criteria tests.test_judge_module -v -b`
  on the tree this gate starts from and paste the result here;
  `tests/test_rearm_clears_stale_criteria_state.py` encodes today's reset and
  is expected to need a narrow/broad split — T01's criterion 4 says how.
- **Flag-scope table (§3).** The table above is it.
- **Escalation-predicate satisfiability (§2).** No check is raised; PLAN.md
  records zero.

## Reflection notes

<Written by the human at review time.>
