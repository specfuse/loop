---
feature_id: FEAT-2026-0116
title: The failure signature names the failing test, so a unit that fixed one failure and hit another is progress, not a spin
slug: failure-signature-names-the-test
branch: feat/FEAT-2026-0116-failure-signature-names-the-test
roadmap_goal: A `tests` failure's signature is the set of failing test ids on every runner the loop meets, and the spinning detector treats a changed set as progress, so `spinning_signature_repeat` fires on a real repeat and never on a run-level summary.
autonomy_default: auto
status: active
planned_cost_usd: 19.00
---

# Plan: the failure signature names the failing test

The spinning family — `spinning_signature_repeat`, `spinning_detected`,
`deterministic_refusal_repeat` — is a third of the human waits on driver >= 0.19
(25 of 76) and 41% of the idle that follows an escalation
(`reviews/2026-09-26-impact-assessment/`, private). #3414 shows the detector
firing on a unit that was advancing: two attempts, two *different* failing tests,
one signature, `"Tests"`, because a Maven project's post-processed report prints
`FAIL: Tests run: …` and the unittest regex `^FAIL: (\S+)` takes the first word.
$19.15 over two attempts, both discarded, one attempt of budget unused. Other
shapes lose the identity the same way: a package-qualified surefire line
(`[ERROR] com.x.FooTest.bar:12`) misses `_SUREFIRE_FAILING_TEST_RE` because that
regex wants an uppercase first letter; pytest, vitest, dotnet and dart have no
parser at all and fall to "the first keyword line", cut at 100 characters. And
`spinning_detected`'s escalation payload carries no class or signature, which is
why a third of the corpus's spinning escalations record `None`.

This feature makes the signature for `failure_class: tests` the sorted set of
failing test ids, extracted per runner from the gate report and, when the report
tail lost them, from the persisted full log (`work/gate-logs/`, #3300); puts
that set on the `attempt_outcome` as `failing_tests`; and makes the repeat
detector compare the sets, so a changed set is progress. `replay_spin.py` runs
the new rule over the recorded corpus so the close can say how many past
`spinning_signature_repeat` escalations would not have fired.

**What this is not.** It does not change what `spinning_detected` means
(attempt budget exhausted) or the re-arm reproduction gate; it makes both
carry the evidence they were missing.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n "def parse_gate_failure_signature\|_SUREFIRE_FAILING_TEST_RE\|def detect_spinning_signature_repeat\|def extract_failure_excerpt\|def persist_gate_output\|def select_gate_report_lines" specfuse/loop/loop.py; grep -n "def " specfuse/loop/replay_spin.py`
- **Verdict:** found the per-class regex table in `parse_gate_failure_signature`, the surefire hoist in `extract_failure_excerpt`, the persisted full log, and `replay_spin.py`; extending all four, building the per-runner failing-test extractor new.
- **Detail.** The parser runs on at most 15 tail lines plus pinned verdict lines
  (`select_gate_report_lines`), so a runner whose failing-test lines sit above
  the summary loses them before the regex runs — the full log is where they
  survive. FEAT-2026-0110's narrow selection maps test files to runner arguments
  and has no output parser; nothing there is reusable.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero. The detector fires on a strict subset of what it fires on today (equal
  failing sets, or equal signature and excerpt when no set could be extracted);
  no new escalation is introduced. `deterministic_refusal_repeat` is untouched.

## Assumptions taken by default (answers-supplied drafting, 2026-09-26)

- **Autonomy `auto`.** Single gate; the judge writes the terminal verdict.
- **Signature = sorted failing ids, joined, capped at 100 characters with a
  stable hash tail when longer.** The `failing_tests` list is the full set; the
  string stays human-readable for `learnings-suggest` clustering.
- **Repeat = same failing set.** When neither attempt yields a set, fall back
  to today's comparison plus an excerpt match (#3414's cheaper alternative).

## Task graph

```yaml
# Single gate, single terminal close: 3 substantive WUs is under the ceremony
# proportionality threshold (docs/methodology.md §6).
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0116/T01
        file: WU-01-failing-tests-per-runner.md
        depends_on: []
      # hygiene (gate 1 broad run, 2026-09-26): bandit B324 on the sha1
      # truncation tail; T01H marks it usedforsecurity=False.
      - id: FEAT-2026-0116/T01H
        file: WU-01H-signature-hash-not-for-security.md
        depends_on: [FEAT-2026-0116/T01]
      - id: FEAT-2026-0116/T02
        file: WU-02-repeat-means-same-failing-set.md
        depends_on: [FEAT-2026-0116/T01]
      - id: FEAT-2026-0116/T03
        file: WU-03-document-and-replay.md
        depends_on: [FEAT-2026-0116/T02]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0116/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0116/T01, FEAT-2026-0116/T01H, FEAT-2026-0116/T02, FEAT-2026-0116/T03]
```

## Scope boundary — explicitly OUT

- **Non-`tests` classes.** `lint`, `security`, `coverage`, `other` keep their
  signatures; only the `None` payload gap is closed for them.
- **The re-arm reproduction gate** (`tests/test_spinning_rearm_gate.py`): it
  compares whatever signature was recorded; a more precise signature makes it
  stricter for free, and that is the intent.
- **A per-project signature knob.** #3414 offers it as the cheaper fix; the
  per-runner extractor removes the need.
- **No consumer repository is edited.** The Maven fixture in the oracle is a
  copied report shape, not a clone.

## Post-merge checklist

Observable only across repositories and over time (`close-discipline.md` §2).

- [ ] Over the next ten features closed in this repo and the generator, count
      `human_escalation` events with reason `spinning_signature_repeat` and,
      for each, whether the two attempts' `failing_tests` were equal (baseline:
      7 such escalations on driver >= 0.19, at least one on a progressing unit).
- [ ] Count spinning-family escalations whose payload lacks
      `failure_signature` (baseline: 12 of 25).

## Notes

- Dependencies live here, not in WU frontmatter.
