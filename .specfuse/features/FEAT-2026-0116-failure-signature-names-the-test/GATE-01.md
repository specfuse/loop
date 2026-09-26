---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_failure_signature_names_the_test -v -b"
cost_budget_usd: 35.00
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
