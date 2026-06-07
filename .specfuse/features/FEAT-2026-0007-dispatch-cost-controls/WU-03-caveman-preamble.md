---
id: FEAT-2026-0007/T03
type: implementation
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# Tier-gated caveman preamble

**Objective.** When the dispatched WU's `effort` is `low` or `medium`, the
prompt preamble includes an inline terseness directive (caveman-style) so
the dispatched session avoids prose narration, end-of-turn summaries, and
filler — reducing output tokens (billed at output rate, no cache benefit).
For `high`, `xhigh`, `max` the preamble is unchanged (reasoning out loud
helps quality at those tiers).

**Context.** This is `FEAT-2026-0007/T03`. `PROMPT_PREAMBLE` is defined at
`loop.py:415` and concatenated with the WU body in `dispatch()`. The
dispatched session's output is consumed only by the driver (RESULT block
parser + verification gates), so prose is dead bytes. Depends on T02
(`effort` field). The terseness directive must NOT alter:
the fenced `result` block contract (`.specfuse/rules/result-contract.md`),
code blocks, or quoted error strings — the parser depends on those being
verbatim. The directive is inlined as a Python string constant; do not
import or reference `.claude/skills/caveman/SKILL.md` (skills are not
reachable from inside a dispatched session). Honor `result-contract.md`
and `never-touch.md`.

**Acceptance criteria.**
1. New module-level constant `CAVEMAN_DIRECTIVE` in `loop.py` — a multi-line
   string — instructs the session to: drop articles, filler, pleasantries,
   and hedging; avoid narration between tool calls; omit any end-of-turn
   summary; write code blocks and the RESULT block normally; quote error
   strings exactly.
2. `dispatch()` selects the preamble at call time: `PROMPT_PREAMBLE + "\n\n"
   + CAVEMAN_DIRECTIVE` when `wu.effort in {"low", "medium"}`, else
   `PROMPT_PREAMBLE` alone.
3. The existing RESULT-block parsing tests in `tests/` still pass — the
   directive must not break the fenced-block contract.
4. One new unit test asserts the preamble-selection logic returns the
   caveman-augmented preamble for `low` and `medium`, and the unchanged
   preamble for `high`, `xhigh`, `max`.
5. `WU.template.md`'s frontmatter notes — under the `effort:` field doc
   added by T02 — gain a sentence: "low/medium also enable a terseness
   directive in the dispatched session; high+ leave it off."

**Do not touch.** Exactly 3 files change: `.specfuse/scripts/loop.py`,
`.specfuse/templates/WU.template.md`, and one new test file under `tests/`
(suggested `tests/test_loop_caveman_preamble.py`). No edits to:
`.claude/skills/caveman/SKILL.md` or any other skill, binding rules,
`.specfuse/verification.yml`, existing WU files, secrets, `.git/`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`.

**Escalation triggers.** Stop and emit `status: blocked` if any existing
test asserts the verbatim text of `PROMPT_PREAMBLE` such that introducing
the directive would mass-fail unrelated tests — flag the conflict rather
than rewriting those tests in scope.
