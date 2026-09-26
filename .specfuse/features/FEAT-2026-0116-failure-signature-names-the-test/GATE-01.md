---
gate: 1
status: passed
feature_oracle: "python3 -m unittest tests.test_failure_signature_names_the_test -v -b"
cost_budget_usd: 35.00
baseline:
  sha: 8cd8e4508c82f73ac2fdbb883900d49117239f7d
  probed_at: 2026-09-26T17:40:41.245423+00:00
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:20416d5069e1abc4f39e755ecf525f09240a5199:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:45fc1aec6b9cb8bfc5073ad076dacada7201b19e:4acc6dfc5e8cece358c167d876515eba4a39a500:560c0be20a8e47a0c76f567ff4bce78a94bed00f:5ff66b6e4d8a264f23709ea60706111a4c59ed11:662a4042ebada7ecfb668af3ebbaf7002ce2d4b3:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:a122d1db4fd063b79f10e884eb141d8209a59054:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d664745f3d8e8d366a9f5029d78452efa5fda16f:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  entry_sha: 8cd8e4508c82f73ac2fdbb883900d49117239f7d
  source: attributed:FEAT-2026-0116/T01
  failing: []
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:10ec69d429658102712a4743f899c45f5dc482b1:1164a5e093576c14cf2476fd8b809247ef2672c5:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:20416d5069e1abc4f39e755ecf525f09240a5199:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:45fc1aec6b9cb8bfc5073ad076dacada7201b19e:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:7d6ae5b2325e3c5c7c68771242767939deda2e5e:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d664745f3d8e8d366a9f5029d78452efa5fda16f:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-09-26T18:21:27.504032+00:00
  ok: true
  failing: []
---

# Gate 1 — the failure signature names the failing test

## Definition of done

For a `tests` gate failure on any runner the loop meets (unittest, pytest,
Maven surefire, vitest/jest, dotnet test, dart test, bats), the
`attempt_outcome` carries `failing_tests`, the sorted set of failing test ids,
and `failure_signature` is derived from that set — never from a run-level
summary line. Two consecutive attempts that fail on different sets are not a
`spinning_signature_repeat`; two that fail on the same set are. Every
spinning-family escalation payload carries the last attempt's class, signature
and failing set.

The `feature_oracle` above is that claim, executable. It is **red on the tree
this gate starts from** (the module does not exist), and T01 — the walking
skeleton — is what makes it green. Its first case is #3414 verbatim: two Maven
reports whose tails read `FAIL: Tests run: …` and whose failing lines name
`WrittenSubtreeCensusTest.writtenSubtreesMatchesTheCommittedCensus` and
`CleanScopeCoverageTest.everyDeclaredCleanScopeCoversItsOwnDirectoriesWithoutTouchingAnEarlierSibling`
respectively; the oracle asserts the two signatures differ and neither is
`Tests`. T02 adds the end-to-end case through `loop.run()`.

Also required for the gate to close:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are staged (feature-local `LEARNINGS-pending.md`).
- Documentation reflects what was actually built, canonical and mirror.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is the feature's terminal gate, so its closing sequence is a single `close`
unit and the terminal verdict is written by a fresh judge session.

## The sites

| surface | today | after this gate |
| --- | --- | --- |
| `parse_gate_failure_signature`, class `tests` | first regex match in the 15-line tail | sorted failing ids from the per-runner extractor over report + full log |
| `attempt_outcome` payload | no failing-test field | `failing_tests: [...]` (additive) |
| `detect_spinning_signature_repeat` | `(class, signature)` equality | failing-set equality; excerpt match as fallback |
| `spinning_detected` / repeat escalation payloads | no class/signature | last attempt's class, signature, failing set |

No switch: there is no behaviour an operator would want to keep.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** T02 narrows when the
  detector fires. Before arming, run
  `python3 -m unittest tests.test_attempt_outcome_emission tests.test_spinning_rearm_gate tests.test_replay_spin tests.test_surefire_run_level_signature tests.test_failure_signature_fail_prefix tests.test_maven_failure_excerpt -v -b`
  on the tree this gate starts from and paste the result here; T01's and T02's
  last criteria name the modules that must keep passing.
- **Flag-scope table (§3).** None: no flag.
- **Escalation-predicate satisfiability (§2).** No check is raised; PLAN.md
  records zero.

## Reflection notes

<Written by the human at review time.>
