---
gate: 2
status: open
feature_oracle: "python3 -m unittest tests.test_tiered_verification_e2e -q"
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:3e1ed273ab9179bbc8a1519961dcece15f51277e:5ff66b6e4d8a264f23709ea60706111a4c59ed11:629a93007eb5d89ba590da86413732226f1940df:7c38895c82f96fa8ba6b8f1cbee7aedddab3bec7:831280d4f4defc99cf113cf1968b467da7b51390:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:863d8cb380c6778e41ebdf2c44ce04ef3367e8b4:97bcab1bc7244262cec901f46035f51dfdd07278:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d4c9482c61e5ab32c45191fb1d2080539c9e6666:d7a119faadbd9fe577b4091c5fb908e6760d9adb:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:efde0847dce23ff89ddf38ac07d88f490cad8d66
  ran_at: 2026-09-08T17:45:06.105827+00:00
  ok: true
  failing: []
---

# Gate 2 — the per-attempt tier, and the once-per-gate backstop that makes it safe

Gate 1 removed work: the `code` set stopped running at gate entry. Gate 2 is
the first gate of this feature that must also prove the removed work is **still
done somewhere** — narrowing what runs per attempt is only safe if the full set
still runs, once, before the gate closes. That pairing is the whole gate.

Scope, per `PLAN.md` and the roadmap's `**Goal.**`: per attempt, the unit's
declared tests, tests touching changed files, lint, and the feature oracle;
once per gate before the close, the full suite with coverage, bats, leak-scan
and security.

## What this is worth, measured on this tree

Measured in the `G1-PLAN` session that drafted this gate, on gate 1's head,
under `.venv`, unsandboxed (the sandbox falsely reds roughly a dozen
git/network tests in this repo, so a sandboxed run is not a measurement of the
code):

| Selection | Modules | Tests | Wall clock |
|---|---|---|---|
| Full `code` set (`RETROSPECTIVE.md`, gate 1) | — | — | **169.4s** |
| Full unittest suite alone (`RETROSPECTIVE.md`, gate 1) | 393 | 3788 | 146.1s |
| Every test module importing the driver (import-graph proxy) | 153 | 1704 | **61.8s** |
| A gate-1 unit's own declared test modules (T01+T02+T03) | 3 | 14 | **3.9s** |
| `ruff check specfuse .specfuse/scripts tests scripts` | — | — | **0.05s** |

So the narrow tier is roughly **6s against 169.4s** — and the two numbers that
decide the design are the middle two. An import-graph rule narrows the suite
only 146.1s → 61.8s, because `specfuse/loop/loop.py` is one ~9k-line module
that 153 of 393 test modules import: module granularity caps the precision.
The unit's own declared tests narrow it to 3.9s. Whatever rule gate 2 adopts
for "tests touching changed files" has to beat 61.8s to be worth building, or
it is buying 58% where declaration already buys 97%.

## Definition of done

- **A gate declaration in `verification.yml` carries a tier.** Each entry in
  the `code` list may declare which tier it runs in. An entry that declares
  nothing keeps today's behaviour exactly — it runs on every attempt *and* in
  the broad run. Opting a gate **out** of the per-attempt run is an explicit
  declaration, never a default, so a gate added later is never silently
  demoted.
- **A per-attempt verification runs only the narrow tier.** The gates declared
  per-gate-only are observed not to execute on an attempt — asserted on the
  real dispatch path, by their absence from the run, not by reading the
  config.
- **The `tests` gate narrows rather than disappears.** Per attempt it runs a
  selected subset; per gate it runs whole, under `coverage run`, exactly as it
  does today. One gate entry, one name, two commands — not two gate lists.
- **The selection rule is declared, fail-safe, and auditable.** The per-attempt
  test selection is the union of the unit's own declared test paths and
  whatever the changed-file rule resolves. A changed path the rule cannot
  resolve, or an empty selection, falls back to the **full** gate command. The
  tier fails safe (runs more), never open (runs nothing).
- **The broad set runs exactly once per gate, before the closing sequence
  dispatches, and a red broad run halts the gate.** Not after the close, not
  as advice: a gate whose broad run is red does not reach its close. This is
  the criterion that makes the narrowing safe rather than merely cheap.
- **The broad run is recorded on the gate and keyed on the tree**, reusing
  T02's `HEAD^{tree}` primitive, so a driver restart at an unchanged tree does
  not re-run 169.4s of gates it already ran. A moved tree re-runs it.
- **The once-per-gate attribution bound says what the mechanism actually
  does.** `GATE-01.md`'s "at most once per gate" is corrected to the bound
  `gate_baseline_check`'s tree/sha dedup really holds, and the differing-tree
  case gets the test it has never had. See T07 — the decision on which side
  moves is recorded in `GATE-02-REVIEW.md`, not left to the unit.
- Absent-key and flag behaviour is preserved: a `verification.yml` with no
  tier declarations anywhere behaves byte-identically to today.
- Per-criterion state and the narrow/broad oracle contract:
  `close-discipline.md` §5.

## This gate's oracle

```
python3 -m unittest tests.test_tiered_verification_e2e -q
```

Red on HEAD by construction — the module does not exist. T04 is the tracer
bullet that makes it green, and the only unit permitted to leave stubs behind
it.

**How this advances gate 1's oracle.** Gate 1's oracle
(`tests.test_lazy_baseline_e2e`) asserts a negative *at one moment*: on a green
gate entry the `code` set is not executed. A driver that then runs all sixteen
gates on every attempt satisfies it completely — and that is precisely the
driver gate 1 shipped. Gate 2's oracle strengthens that in two directions gate
1's could not reach:

1. **From one moment to every attempt.** Gate 1's claim is the n=1 case of
   "the broad set does not run per attempt". Gate 2's oracle asserts it across
   several attempts within one dispatched gate, which is a universal claim
   where gate 1's was existential.
2. **From removal to liveness.** Gate 1 only ever removed work, so it carried
   no obligation to prove anything still happens. Gate 2's oracle must assert
   the broad set *does* run — once, before the close — and that a red broad run
   halts the gate. That is a liveness property gate 1's oracle has no shape
   for, and it is the half that makes narrowing safe rather than merely cheap.

It also closes a hole gate 1's own close named: because narrowing makes a
per-attempt failure both cheaper and more likely, the oracle must drive a
narrow-tier attempt that **fails** and observe attribution fire. Gate 1's
retrospective records attribution firing **zero** times in production; gate 2's
oracle is the first surface that exercises that path as part of the gate's own
exit condition.

As in gate 1, the oracle must assert on **observable effects** of the real
dispatch path — which gate commands executed, in which tier, and whether the
gate reached its close — not on a selector helper returning the right list in
isolation. A feature about running less verification, whose oracle only checked
a selector function, would be its own hollow pass.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default flip (§4).** T04 changes what the driver runs
  on every attempt of every unit in every feature. It may not be armed on
  "mechanical, nothing design-open" — run the exact command T04's tests gate
  will run and paste the result into `GATE-02-REVIEW.md`.
- **Flag scope (§3).** T04 introduces a tier declaration in
  `verification.yml`. Its absent-key behaviour is a definition-of-done bullet
  above precisely because a silent default here changes every project that
  upgrades.
- **Predicate satisfiability (§2).** This gate raises no check to `ERROR` and
  flips no `WARNING` to blocking. The adjacent risk is under-testing, not a
  false positive, which is what the fail-safe fallback and the once-per-gate
  broad run exist to bound.
- **Review-summary obligation.** Gate 3 is armed from here, and gate 2's
  `plan-next` must draft **gate 3's own `feature_oracle`** along with its
  units (#3262), and state how it advances this gate's. `GATE-03.md`'s
  atomicity constraint — `[FEAT-2026-0019/G1]`, one unit, not several — is
  restated in that unit's body and is binding on the draft.

## Reflection notes

<Written by the human at review time. Whether the narrow tier ever let a
regression reach the broad run, how much wall clock the tier actually saved
across the gate's attempts, and whether the declared-tests rule needed the
changed-file selector at all.>
