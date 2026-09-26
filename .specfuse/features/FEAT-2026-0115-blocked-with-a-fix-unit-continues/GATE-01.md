---
gate: 1
status: awaiting_review
feature_oracle: "python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b"
cost_budget_usd: 40.00
baseline:
  sha: 932e8687fdb8488be4274b4c0b994277386b55b1
  probed_at: 2026-09-26T16:53:07.231764+00:00
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:19e6172a5f8ed4e64796dcbec75a5c167dfaa326:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:7236c0b74a800bb48cc28ab6dc46543c53a4dc90:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:9d592b0fb98f8caf8cbe2b603e967434ec0199bf:9f955f7d0d0875a1252a7fedb2e56a6960f4abda:a122d1db4fd063b79f10e884eb141d8209a59054:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d664745f3d8e8d366a9f5029d78452efa5fda16f:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  entry_sha: 932e8687fdb8488be4274b4c0b994277386b55b1
  source: attributed:FEAT-2026-0115/T04
  failing: []
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:45fc1aec6b9cb8bfc5073ad076dacada7201b19e:4acc6dfc5e8cece358c167d876515eba4a39a500:560c0be20a8e47a0c76f567ff4bce78a94bed00f:5ff66b6e4d8a264f23709ea60706111a4c59ed11:662a4042ebada7ecfb668af3ebbaf7002ce2d4b3:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:9f955f7d0d0875a1252a7fedb2e56a6960f4abda:a122d1db4fd063b79f10e884eb141d8209a59054:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d664745f3d8e8d366a9f5029d78452efa5fda16f:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-09-26T17:24:07.775667+00:00
  ok: true
  failing: []
---

# Gate 1 — a block that names its fix unit continues the gate

## Definition of done

A work unit whose session reports `status: blocked` with `blocked_next:` naming
a drafted fix unit file does not stop the gate: the driver validates the draft,
inserts it into the gate ahead of the blocked unit, flips it to `pending`,
re-arms the blocked unit behind it, records a `fix_unit_inserted` event and a
progress line, commits the bookkeeping, and dispatches the fix unit next — with
no `human_escalation`. A draft the stop classes refuse, a third insertion for
the same unit, or a feature under `review` escalates as today with the reason
named in the brief.

The `feature_oracle` above is that claim, executable. It is **red on the tree
this gate starts from** (the module does not exist), and T01 — the walking
skeleton — is what makes it green. It drives `loop.run()` with a stubbed
dispatch: the first dispatch of T01 writes `WU-05-fix.md` (`status: draft`,
`provenance: agent`, five sections) and returns a blocked RESULT with
`blocked_next: {kind: fix_unit, file: WU-05-fix.md, id: FEAT-X/T05}`; the oracle
asserts the next dispatch is T05, then T01 again, that the feature ends with
both `done`, that `events.jsonl` carries `fix_unit_inserted` and no
`human_escalation`, and that `PLAN.md`'s graph lists T05 with T01 depending on
it.

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
| `agent_reported_blocked` handler in `run()` | reset tree, `blocked_human`, escalate, return 1 | if `blocked_next:` validates: insert, re-arm, continue; else today |
| `REPLAN_OPTION_SCOPE["agent_reported_blocked"]` | no option offered | brief names the drafted fix and the arming command when insertion was refused |
| `gate_eval.evaluate_auto_close` | reads `replan` as off-plan | also reads `fix_unit_inserted` |
| `verification.yml` `defaults.fix_unit_insertion` | absent | `false` ignores the key; absent means on |
| `defaults.max_fix_units_per_unit` | absent | default 2 |

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** T01 changes what a
  blocked RESULT does. Before arming, run
  `python3 -m unittest tests.test_spinout_brief_end_to_end tests.test_spinout_brief_replan_option tests.test_replan_end_to_end tests.test_arm_eval tests.test_arm_txn -v -b`
  on the tree this gate starts from and paste the result here; T01's criterion
  4 names the modules that must keep passing unchanged.
- **Flag-scope table (§3).** The table above is it.
- **Escalation-predicate satisfiability (§2).** No check is raised; PLAN.md
  records zero.

## Reflection notes

<Written by the human at review time.>
