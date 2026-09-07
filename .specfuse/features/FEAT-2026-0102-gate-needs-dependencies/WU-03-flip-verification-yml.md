---
id: FEAT-2026-0102/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
oracle_env: macos_local
produces:
  - .specfuse/verification.yml
  - plugins/specfuse/skills/verification/SKILL.md
  - .specfuse/skills/verification/SKILL.md
model: sonnet
effort: medium
gate_set: code
driver_version: 0.15.0
started_at: 2026-09-07T20:00:26.670829+00:00
duration_seconds: 810.135
cost_usd: 1.447758
input_tokens: 122
output_tokens: 16340
---

# Flip this repo onto `needs:`, measure it, and reword the authoring rule

**Objective.** Make this repo's `code` set run its test suite once instead of
twice by declaring `needs: [tests]` on the `coverage` gate, record the measured
wall clock against the recorded baseline, and reword the authoring rule that
made the duplication correct.

**Context.** FEAT-2026-0102/T03; read `PLAN.md`, T01 and T02. This is the last
substantive unit **by design** — T01 and T02 landed the mechanism inert, and
this unit is the single moment the oracle changes ([FEAT-2026-0019/G1]). Be
aware that your own verification runs under the gate set you are editing: the
driver runs `verify()` after your edits, so a mistake here fails you rather
than passing silently. That is the intended safety property, not a hazard to
work around.

The two gates today, in `.specfuse/verification.yml`:

```yaml
  - name: tests
    command: "python3 -m unittest discover -s tests -v -b"
  - name: coverage
    command: "coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90"
```

After: `tests` runs the suite under `coverage run` (keeping `-v -b`, whose
reason is recorded in the file's own comment), and `coverage` becomes
`coverage report --fail-under=90` with `needs: [tests]`. The `90` floor does
not change — [FEAT-2026-0002/G1-CLOSE] is about enumerating every site that
asserts a floor, and this unit must confirm it did not strand one.

**Authoring rule.** The rule that made the duplication correct is "the
stale-artifact trap" in `plugins/specfuse/skills/verification/SKILL.md:110`,
and the header comment in `.specfuse/verification.yml`. The new statement: a
gate command must be self-contained **unless** it declares `needs:`, in which
case the runner guarantees the dependency ran, clean, in this same invocation.
The guarantee is per-invocation and never cached across attempts. `plugins/` is
the canonical copy; `.specfuse/skills/` is generated from it — do not edit the
generated copy by hand and leave the canonical one stale.

**Acceptance criteria.**

- `.specfuse/verification.yml`'s `coverage` gate carries `needs: [tests]` and its command no longer invokes `unittest discover`: `grep -c "unittest discover" .specfuse/verification.yml` returns `1`.
- The suite runs once: `bash scripts/smoke-test.sh` exits 0, and its output contains exactly one `Ran <N> tests` line.
- Distinct attribution survives the flip. Break one test locally, run the `code` set, and record that `parse_gate_failure_signature` returns `failure_class: tests` with a test-shaped signature — not `coverage`. Restore the test before reporting.
- Measured `code`-set wall clock recorded in the RESULT block, next to the 118s / 93%-duplicated baseline from `[FEAT-2026-0051/G1-CLOSE]`. Time the real set (`bash scripts/smoke-test.sh`), not a subset.
- The floor is not stranded: `grep -rn "fail-under" .specfuse/verification.yml scripts/smoke-test.sh .github/workflows/` shows `90` at every site that names it, and no site asserts it twice.
- Both copies of the verification skill carry the reworded rule and are identical: `diff plugins/specfuse/skills/verification/SKILL.md .specfuse/skills/verification/SKILL.md` reports no differences.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `specfuse/loop/loop.py` (T01); `specfuse/loop/gate_commands.py`
(T02); the `--fail-under` value itself — this unit moves where the floor is
asserted, never what it is; any other gate in the set (`lint`, `security`,
`leak-scan`, the bats suites) — only `tests` and `coverage` change; `.git/`,
secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` — as edited
by this unit — plus `bash scripts/smoke-test.sh`.

**Escalation triggers.** Emit `status: blocked` if the skills sync is
lock-file-mediated (`skills-lock.json`) and regenerating `.specfuse/skills/`
would touch entries beyond the verification skill — a broad lockfile rewrite
inside this unit is an operator decision. Also block if timing the set shows
**no** measurable improvement: that means `needs:` is not doing what T01
claims, and the right outcome is a diagnosis, not a flip that ships anyway.
</content>
