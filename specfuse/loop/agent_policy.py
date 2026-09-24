#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""
Specfuse agent-policy schema linter.

Validates a project's ``.specfuse/agent-policy.yml`` structurally: the
operator's priorities for what the loop works on (bug/feature queue order,
gate-review dial per feature, triage automation dial) and its budgets and
escalation contact points.

Sibling of ``lint_monitoring.py`` (unrelated schema, not an extension of it)
and, like it, parses only with ``_miniyaml`` — the package has zero runtime
dependencies. Deliberately not imported by and not importing
``lint_monitoring`` — two validators over unrelated schemas sharing a helper
couples them for no gain (``[FEAT-2026-0072/T01]`` precedent).

Unlike monitoring, an agent-policy file is NOT opt-in structurally at the
schema level — every required top-level key must be present in whatever file
is handed to the validator. (Whether the *live* ``.specfuse/agent-policy.yml``
existing at all is itself optional is a decision for the caller, e.g. T03's
triage wiring; this module only validates files that are handed to it.)

Exit 0 = clean, 1 = an ERROR finding is present (WARN-only is still exit 0).

Usage:  lint_agent_policy.py [path/to/agent-policy.yml]
"""

from __future__ import annotations

import re
from pathlib import Path

from . import _miniyaml
from .lint_roadmap import roadmap_statuses

__all__ = (
    "load_policy",
    "resolve_triage_auto",
    "resolve_bug_automerge",
    "bug_lane_limits",
    "bug_lane_ci_wait_seconds",
    "validate_agent_policy",
    "main",
    "SEVERITY_VALUES",
    "read_severity_label",
    "resolve_severity_aliases",
    "resolve_required_checks",
    "DEFAULT_SEVERITY_ALIASES",
    "AUTOMERGE_VALUES",
    "GATE_REVIEW_VALUES",
    "PROVIDER_VALUES",
)

_DONE_OR_ABANDONED = frozenset({"done", "abandoned"})

SEVERITY_VALUES = frozenset({"low", "medium", "high", "critical"})
AUTOMERGE_VALUES = frozenset({"off", "on"})
GATE_REVIEW_VALUES = frozenset({"human", "auto"})
PROVIDER_VALUES = frozenset({"discord", "slack", "teams", "none"})

REQUIRED_TOP_LEVEL_FIELDS = ("version", "queue", "rules", "budgets", "escalation")

_FEAT_ID_RE = re.compile(r"^FEAT-\d{4}-\d{4}$")

_REQUIRED_BUDGET_FIELDS = ("max_tokens_per_run", "max_open_prs", "max_items_per_day")
_REQUIRED_ESCALATION_FIELDS = ("webhook_env", "assignee", "quiet_hours", "sla_hours")
_ESCALATION_KNOWN_KEYS = frozenset(_REQUIRED_ESCALATION_FIELDS) | {
    "provider",
    "silence_hours",
}

# An environment-variable-NAME reference, not a secret value — same shape
# check and same rationale as lint_monitoring._ENV_VAR_NAME_RE: structural
# only, not a secret detector (that is leak-scan's job). A pasted webhook
# URL trips it on `:`, `/`, and `.`.
_ENV_VAR_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_DEFAULT_PATH = Path(".specfuse/agent-policy.yml")

DEFAULT_MAX_DIFF_LINES = 150
DEFAULT_MAX_MERGES_PER_DAY = 3
# Path prefixes the bug lane accepts as test evidence (#1418). A tuple, so the
# default cannot be mutated by a caller. `tests/` alone was hardcoded in
# bug_lane until it made the guardrail unsatisfiable — and therefore the whole
# lane inert — on any repository laying tests out differently.
DEFAULT_TEST_PATHS = ("tests/",)
#: `bug_lane_run.CI_WAIT_SECONDS`'s policy-facing spelling (FEAT-2026-0108/T04).
#: Minutes, not seconds, because that is the unit an operator reasons in --
#: "our CI takes 8 minutes" -- and `budgets` is where run-shaped time limits
#: already live (`max_tokens_per_run` et al.).
DEFAULT_CI_WAIT_MINUTES = 10


def load_policy(path: str | Path | None = None) -> dict:
    """Load and parse *path* (default ``.specfuse/agent-policy.yml``).

    Raises ``FileNotFoundError`` when the path is absent — a missing policy
    file and an empty queue are different declared states, and a caller must
    be able to tell them apart rather than receive silently-defaulted output.
    """
    p = Path(path) if path is not None else _DEFAULT_PATH
    if not p.is_file():
        raise FileNotFoundError(f"{p}: agent-policy file does not exist")
    return _miniyaml.parse(p.read_text())


def resolve_triage_auto(path: str | Path | None = None) -> bool:
    """Resolve `rules.triage.auto` for `apply_triage`'s `auto` argument.

    Returns `False` (the safe default, matching `apply_triage`'s own
    default) when the policy file is absent or the key is absent. Returns
    `True` only when the key is exactly boolean `true` -- no truthy-string
    coercion.
    """
    try:
        policy = load_policy(path)
    except FileNotFoundError:
        return False

    rules = policy.get("rules") if isinstance(policy, dict) else None
    if not isinstance(rules, dict):
        return False
    triage = rules.get("triage")
    if not isinstance(triage, dict):
        return False
    return triage.get("auto") is True


def resolve_escalation_assignee(path: str | Path | None = None) -> str:
    """Resolve `escalation.assignee` for `escalation.emit_escalation` (#1762).

    Returns `""` -- meaning "file the issue unassigned" -- when the policy
    file is absent, the key is absent, or the value is not a string. Empty is
    the safe default here in a way a username never is: `emit_escalation`
    previously defaulted to the literal `specfuse-operator`, which is
    assignable on no repository, so `gh issue create` exited 1 on that flag
    and every escalation was lost while the caller reported success.

    The key was validated by `validate_agent_policy` and read by nothing
    before this, so an operator who wrote `assignee: ""` was overridden by a
    placeholder they never chose.
    """
    try:
        policy = load_policy(path)
    except FileNotFoundError:
        return ""

    escalation = policy.get("escalation") if isinstance(policy, dict) else None
    if not isinstance(escalation, dict):
        return ""
    assignee = escalation.get("assignee")
    if not isinstance(assignee, str):
        return ""
    return assignee.strip()


def resolve_bug_automerge(path: str | Path | None = None) -> bool:
    """Resolve `rules.bugs.automerge` for the bug-lane merge guardrails.

    Returns `False` (the safe default) when the policy file is absent, the
    key is absent, or the value is anything other than the exact string
    `"on"` -- including the boolean `True`, which is not the declared
    spelling (the schema's `AUTOMERGE_VALUES` are `"off"` / `"on"` strings).
    """
    try:
        policy = load_policy(path)
    except FileNotFoundError:
        return False

    rules = policy.get("rules") if isinstance(policy, dict) else None
    if not isinstance(rules, dict):
        return False
    bugs = rules.get("bugs")
    if not isinstance(bugs, dict):
        return False
    return bugs.get("automerge") == "on"


def bug_lane_limits(path: str | Path | None = None) -> dict:
    """Resolve `rules.bugs.max_diff_lines` / `max_merges_per_day`.

    Returns the documented defaults (150, 3) when the policy file is absent
    or either key is absent.
    """
    limits = {
        "max_diff_lines": DEFAULT_MAX_DIFF_LINES,
        "max_merges_per_day": DEFAULT_MAX_MERGES_PER_DAY,
        "test_paths": list(DEFAULT_TEST_PATHS),
    }

    try:
        policy = load_policy(path)
    except FileNotFoundError:
        return limits

    rules = policy.get("rules") if isinstance(policy, dict) else None
    bugs = rules.get("bugs") if isinstance(rules, dict) else None
    if not isinstance(bugs, dict):
        return limits

    max_diff_lines = bugs.get("max_diff_lines")
    if isinstance(max_diff_lines, int) and not isinstance(max_diff_lines, bool):
        limits["max_diff_lines"] = max_diff_lines

    max_merges_per_day = bugs.get("max_merges_per_day")
    if isinstance(max_merges_per_day, int) and not isinstance(max_merges_per_day, bool):
        limits["max_merges_per_day"] = max_merges_per_day

    # A declared list of non-empty strings replaces the default outright rather
    # than extending it: an operator naming their layout means "these are my test
    # paths", not "these as well as tests/". A malformed value leaves the default
    # in place, so a typo cannot silently widen or disable the guardrail.
    test_paths = bugs.get("test_paths")
    if isinstance(test_paths, list) and test_paths and all(
        isinstance(entry, str) and entry.strip() for entry in test_paths
    ):
        limits["test_paths"] = list(test_paths)

    return limits


def bug_lane_ci_wait_seconds(path: str | Path | None = None) -> int:
    """Resolve `budgets.ci_wait_minutes` as seconds for `pr_ci_conclusion`'s
    deadline (FEAT-2026-0108/T04).

    Returns `DEFAULT_CI_WAIT_MINUTES * 60` when the policy file is absent, the
    key is absent, or the value is not a positive int -- a malformed override
    must not shrink the wait to zero and turn every fresh PR's guaranteed
    first-read pending into an immediate `ci_pending` decline.
    """
    minutes = DEFAULT_CI_WAIT_MINUTES

    try:
        policy = load_policy(path)
    except FileNotFoundError:
        return minutes * 60

    budgets = policy.get("budgets") if isinstance(policy, dict) else None
    if isinstance(budgets, dict):
        value = budgets.get("ci_wait_minutes")
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            minutes = value

    return minutes * 60


def _positive_int_budget(path: "str | Path | None", key: str) -> "int | None":
    """`budgets.<key>` when it is a usable positive int, else None (#3340).

    Defensive for the same reason `bug_lane_ci_wait_seconds` is: a malformed
    override must not become a cap. Zero or a negative would end a run before
    it dispatched anything, and a bool is an int in Python — `max_items: true`
    would otherwise cap the run at one item.
    """
    try:
        policy = load_policy(path)
    except (FileNotFoundError, OSError):
        return None
    budgets = policy.get("budgets") if isinstance(policy, dict) else None
    if not isinstance(budgets, dict):
        return None
    value = budgets.get(key)
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def resolve_max_tokens(flag: "int | None",
                       path: "str | Path | None" = None) -> "int | None":
    """The run's token cap: the flag if given, else `budgets.max_tokens_per_run`.

    The flag wins because it is the narrower, more deliberate statement — an
    operator typing `--max-tokens` for one run should not have to edit the
    policy file to be heard.
    """
    if flag is not None:
        return flag
    return _positive_int_budget(path, "max_tokens_per_run")


def resolve_max_items(flag: "int | None",
                      path: "str | Path | None" = None) -> "int | None":
    """The run's item cap, from the flag or `budgets.max_items_per_day`.

    NOTE THE SEMANTICS, which #3340 flags and this does not fix: the policy key
    is named *per_day* and is applied here *per run*. Enforcing it across runs
    within a day needs state that survives a process, which is a feature rather
    than this fix. Applied per-run it is a strictly tighter bound than the name
    promises — a day of runs can still exceed it — so it caps the unbounded-run
    risk without claiming the daily accounting the name implies.
    """
    if flag is not None:
        return flag
    return _positive_int_budget(path, "max_items_per_day")


def resolve_required_checks(path: "str | Path | None" = None) -> tuple:
    """`rules.bugs.required_checks` as a tuple of check names, or `()` (#3373).

    The names that must be **present and passing** before the bug lane may
    auto-merge. Empty when absent or unusable, so a deployment that never
    declared it behaves exactly as before: any `success` conclusion is accepted.

    Why it exists. `evaluate_merge_guardrails` accepted any `success`, and a
    repository whose PR job is a deliberate fast lane — excluding a test group
    that guards committed expectations — gave a `success` that **could not
    fail** on that class of defect. A bug-lane PR merged under `automerge: "on"`
    and left `main` red for an hour.

    The split those repositories rely on assumes every change already passed
    the full gate set before its PR opened. That holds for driver work-unit
    PRs and does **not** hold for bug-lane PRs, where a headless session
    chooses which tests to run. This key is how a repository points the lane at
    the complete check rather than the fast one.

    A string is accepted as a one-element list — the common single-check case —
    and anything else unusable resolves to `()`. Requiring nothing is the
    pre-existing behaviour; inventing a requirement from a malformed value
    would block every merge on a typo.
    """
    try:
        policy = load_policy(path)
    except (FileNotFoundError, OSError):
        return ()
    rules = policy.get("rules") if isinstance(policy, dict) else None
    bugs = rules.get("bugs") if isinstance(rules, dict) else None
    raw = bugs.get("required_checks") if isinstance(bugs, dict) else None
    if isinstance(raw, str):
        name = raw.strip()
        return (name,) if name else ()
    if not isinstance(raw, list):
        return ()
    return tuple(str(n).strip() for n in raw if str(n).strip())


#: What each `fix_scope` costs to dispatch, as `(model, effort)` (#3391).
#:
#: `small` is the historical default, so an issue diagnosed as a small fix is
#: dispatched exactly as every bug was before this existed. `large` is the only
#: entry that spends more: a fix whose direction has consequences is where a
#: cheaper session produced coherent, wrong work.
#:
#: `external` deliberately keeps the cheap profile. The fix lives outside this
#: repository, so the session's job is to recognise that and stop — paying for
#: a stronger model to reach the same refusal buys nothing.
DEFAULT_MODEL_BY_FIX_SCOPE = {
    "small": ("sonnet", "medium"),
    "large": ("opus", "high"),
    "external": ("sonnet", "medium"),
}


def resolve_model_by_fix_scope(path: "str | Path | None" = None) -> dict:
    """`rules.bugs.model_by_fix_scope` merged over `DEFAULT_MODEL_BY_FIX_SCOPE`.

    A deployment chooses what each scope costs it: `large: [sonnet, high]` for
    one that would rather not spend on Opus, and so on. Merged rather than
    replaced, so naming one scope does not silently drop the others.

    Every unusable value falls back to the shipped pair for that scope rather
    than raising or disabling dispatch — an unreadable policy must not decide
    that no bug can be worked on. An unknown scope name is ignored: it is a
    typo, and inventing a profile for it would route nothing while looking
    configured.
    """
    resolved = dict(DEFAULT_MODEL_BY_FIX_SCOPE)
    try:
        policy = load_policy(path)
    except (FileNotFoundError, OSError):
        return resolved
    rules = policy.get("rules") if isinstance(policy, dict) else None
    bugs = rules.get("bugs") if isinstance(rules, dict) else None
    raw = bugs.get("model_by_fix_scope") if isinstance(bugs, dict) else None
    if not isinstance(raw, dict):
        return resolved
    for scope, value in raw.items():
        if scope not in resolved:
            continue
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            continue
        model, effort = (str(v).strip() for v in value)
        if model and effort:
            resolved[scope] = (model, effort)
    return resolved


def resolve_max_open_prs(path: "str | Path | None" = None) -> "int | None":
    """`budgets.max_open_prs`, or None when unset or unusable (#3340).

    The ceiling on how many pull requests may be open in the repository before
    the lanes that open more stop dispatching. Required by the schema, proposed
    from evidence by `policy_proposals`, reported on by `policy_review` — and,
    until now, read by nothing that could act on it, so a policy declaring it
    beside `automerge: "on"` described a ceiling that did not exist.

    No flag counterpart: unlike the token and item caps there is no
    `--max-open-prs`, because this is a property of the repository's state
    rather than of one run's appetite.

    Defensive in the same shape as `resolve_max_tokens`: a malformed, zero,
    negative or boolean value resolves to unbounded rather than to a cap. A cap
    of 0 would suppress every pull-request-opening lane permanently, which is
    never what a typo means.
    """
    return _positive_int_budget(path, "max_open_prs")


def describe_budget_sources(**caps) -> str:
    """One line naming each effective cap and where it came from (#3340).

    A run that is capped and does not say so is only marginally better than one
    that is not capped: the operator cannot tell which of the two they have.
    Each value is a `(value, source)` pair, source being `flag`, `policy` or
    `none`.

    `max_items` carries an explicit `per run` (#3340). The policy key it comes
    from is named `max_items_per_day` and is applied per run -- enforcing it
    across a day needs state that survives a process. Printing `max_items=62
    (policy)` against that key invites the reading the name suggests, and the
    wrong reading is the unsafe one: a day of runs can exceed the number the
    operator believes they set. Only this cap is annotated, because only this
    one has a name promising something wider than it delivers; an unset cap
    prints `unbounded` and needs no qualifier.
    """
    parts = []
    for name, (value, source) in sorted(caps.items()):
        rendered = "unbounded" if value is None else str(value)
        qualifier = " per run" if name == "max_items" and value is not None else ""
        parts.append(f"{name}={rendered} ({source}{qualifier})")
    return "budgets: " + ", ".join(parts)


#: `SEVERITY_VALUES` as a ranking, lowest first (#3339). The set says which
#: values are legal; a floor needs to know which are *higher*. Kept beside it
#: and pinned equal by test, so a value added to one and not the other is a
#: failure rather than an unfilterable severity.
SEVERITY_ORDER = ("low", "medium", "high", "critical")

#: Severity is read from a `severity:<value>` label. Nothing defined a source
#: before #3339: the triage marker carries `category` and `confidence` only.
SEVERITY_LABEL_PREFIX = "severity:"

#: Word synonyms for `SEVERITY_VALUES`, shipped so every operator does not
#: hand-write the same six lines (#3355).
#:
#: #3339 declined to map `severity:minor` to `low`, calling it "inventing policy
#: on an operator's behalf". That was too wide, and the same conflation was
#: caught once already at FEAT-2026-0113's gate-2 arm checkpoint: **where the
#: floor sits** (`rules.bugs.min_severity`) is the operator's decision because it
#: gates unattended action, but **what an English word means** is a published
#: vocabulary. Specfuse already ships one of those in `DEFAULT_SEVERITY_RUBRIC`.
#:
#: **Numbered and lettered schemes are deliberately absent, and that exclusion is
#: load-bearing rather than an oversight.** `P0`/`P1`, `S1`/`S2` and `sev1`/`sev2`
#: encode **priority**, a different axis from severity -- `P0` commonly means
#: "drop everything" irrespective of how severe the defect is -- and the mapping
#: varies per organisation. An operator whose repository uses them declares them
#: under `rules.bugs.severity_aliases`, because that is a real judgment about
#: their own scheme and belongs to them.
#:
#: An explicit in-vocabulary label always wins: `read_severity_label` checks
#: `SEVERITY_VALUES` before it consults any alias, so nothing here can redefine
#: `severity:high`.
DEFAULT_SEVERITY_ALIASES = {
    "blocker": "critical",
    "urgent": "critical",
    "major": "high",
    "normal": "medium",
    "moderate": "medium",
    "minor": "low",
    "trivial": "low",
}


def read_severity_label(labels, aliases=None) -> "tuple[str | None, str | None]":
    """`(severity, aliased_from)` for the first readable `severity:<value>`
    label, or `(None, None)` (#3339, #3349).

    A value in `SEVERITY_VALUES` reads directly and `aliased_from` is None. A
    value outside it reads only when *aliases* maps it to a vocabulary value,
    in which case `aliased_from` is the label's own word — so a caller can say
    which of the operator's labels a decision came from rather than reporting
    a rank the label does not literally carry.

    **The vocabulary always wins over an alias.** An alias is a way to make an
    unknown word readable, never a way to redefine `severity:high`.

    `severity:minor` exists in the wild and is not in the vocabulary. #3339
    refused to map it to `low` on its own, and that refusal stands: nothing
    here infers a mapping. The only reason an out-of-vocabulary label reads at
    all is that an operator declared what it means.
    """
    aliases = aliases or {}
    for label in labels or ():
        text = str(label).strip().lower()
        if not text.startswith(SEVERITY_LABEL_PREFIX):
            continue
        value = text[len(SEVERITY_LABEL_PREFIX):].strip()
        if value in SEVERITY_VALUES:
            return value, None
        mapped = aliases.get(value)
        if mapped in SEVERITY_VALUES:
            return mapped, value
    return None, None



def meets_severity_floor(severity: "str | None",
                         floor: "str | None",
                         via: "str | None" = None) -> "tuple[bool, str]":
    """Whether *severity* clears *floor*, and why not when it does not (#3339).

    Two rules, and the second is the one that keeps this safe to ship:

    * **No floor admits everything.** A deployment that never declared
      `min_severity` behaves exactly as it did, including for unlabelled
      issues. This change cannot quietly stop an existing lane advertising.
    * **With a floor, unreadable severity fails closed.** The issue names this
      as the safe default. It does mean a repo that declares a floor and labels
      nothing advertises nothing — which is why the refusal carries a reason
      the run reports, so an empty lane is explained rather than mysterious.
    """
    if floor is None:
        return True, ""
    if SEVERITY_ORDER.index(floor) == 0:
        # A floor at the bottom of the vocabulary excludes nothing: no severity
        # is below `low`. Failing closed on unlabelled issues here would read an
        # operator's "accept everything" as "accept nothing" -- which is exactly
        # what it did to this repo's own policy (`min_severity: low`, no
        # severity labels anywhere) before this branch existed.
        return True, ""
    if severity is None:
        return False, (
            f"no severity label (floor is {floor}); add a "
            f"`{SEVERITY_LABEL_PREFIX}<{'|'.join(SEVERITY_ORDER)}>` label, or "
            f"declare what this repo's own labels mean under "
            f"`rules.bugs.severity_aliases`"
        )
    if SEVERITY_ORDER.index(severity) < SEVERITY_ORDER.index(floor):
        # `via` names the operator's own label when an alias produced this
        # rank (#3349). Reporting the rank alone would read as a label the
        # issue does not carry, and an operator checking the issue would not
        # find it.
        source = f"severity {severity}"
        if via:
            source = f"severity {severity} (via `{SEVERITY_LABEL_PREFIX}{via}`)"
        return False, f"{source} is below the {floor} floor"
    return True, ""


def resolve_min_severity(path: "str | Path | None" = None) -> "str | None":
    """`rules.bugs.min_severity`, or None when unset or unusable (#3339).

    An unknown value resolves to None rather than to a floor: the validator
    already reports it as an ERROR, and guessing a floor from a typo would
    filter on something the operator did not ask for.
    """
    try:
        policy = load_policy(path)
    except (FileNotFoundError, OSError):
        return None
    rules = policy.get("rules") if isinstance(policy, dict) else None
    bugs = rules.get("bugs") if isinstance(rules, dict) else None
    value = bugs.get("min_severity") if isinstance(bugs, dict) else None
    return value if value in SEVERITY_VALUES else None


def resolve_severity_aliases(path: "str | Path | None" = None) -> dict:
    """`rules.bugs.severity_aliases` as `{label_word: severity}` (#3349).

    **Returns `DEFAULT_SEVERITY_ALIASES` extended and overridden by whatever the
    policy declares, key by key** (#3355). An absent, unusable, or
    nothing-legal key therefore resolves to the shipped table rather than to an
    empty map — that is the behaviour change #3355 exists to make, and the
    reason a repository labelling `severity:major` now reads without any
    operator configuration at all.

    An operator-declared entry wins over a shipped one for the same word, so a
    project whose `major` genuinely means `critical` says so and is believed.
    Entries are filtered rather than raised on: the validator already reports a
    bad target as an ERROR, and a single typo should not discard the mappings
    beside it — including the shipped ones.

    Keys are lower-cased to match how `read_severity_label` reads a label; a
    key that is itself in `SEVERITY_VALUES` is dropped, since the vocabulary
    wins there and keeping it would suggest otherwise.
    """
    try:
        policy = load_policy(path)
    except (FileNotFoundError, OSError):
        return dict(DEFAULT_SEVERITY_ALIASES)
    rules = policy.get("rules") if isinstance(policy, dict) else None
    bugs = rules.get("bugs") if isinstance(rules, dict) else None
    raw = bugs.get("severity_aliases") if isinstance(bugs, dict) else None
    if not isinstance(raw, dict):
        return dict(DEFAULT_SEVERITY_ALIASES)
    resolved = dict(DEFAULT_SEVERITY_ALIASES)
    for key, value in raw.items():
        word = str(key).strip().lower()
        if not word or word in SEVERITY_VALUES:
            continue
        if value in SEVERITY_VALUES:
            resolved[word] = value
    return resolved


def validate_agent_policy(path: str | Path | None = None) -> list[str]:
    """Validate *path* (default ``.specfuse/agent-policy.yml``); return findings.

    Empty list means valid. A missing file, a parse failure, and a non-mapping
    top level are each reported as findings, never a silent ``[]``.
    """
    p = Path(path) if path is not None else _DEFAULT_PATH
    if not p.is_file():
        return [f"ERROR: {p}: file does not exist"]

    try:
        parsed = _miniyaml.parse(p.read_text())
    except _miniyaml.MiniYAMLError as exc:
        return [f"ERROR: {p}: could not parse as YAML: {exc}"]

    if not isinstance(parsed, dict):
        return [f"ERROR: {p}: top level must be a mapping"]

    findings: list[str] = []

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in parsed:
            findings.append(f"ERROR: missing top-level '{field}' key")

    unknown = set(parsed) - set(REQUIRED_TOP_LEVEL_FIELDS)
    for key in sorted(unknown):
        findings.append(f"ERROR: unknown top-level key '{key}'")

    if "version" in parsed:
        findings.extend(_check_version(parsed["version"]))
    if "queue" in parsed:
        findings.extend(_check_queue(parsed["queue"]))
    if "rules" in parsed:
        findings.extend(_check_rules(parsed["rules"]))
    if "budgets" in parsed:
        findings.extend(_check_budgets(parsed["budgets"]))
    if "escalation" in parsed:
        findings.extend(_check_escalation(parsed["escalation"]))

    if "queue" in parsed and isinstance(parsed["queue"], list):
        findings.extend(_check_queue_against_roadmap(parsed["queue"]))

    return findings


def _check_queue_against_roadmap(queue: list) -> list[str]:
    """Cross-check queue entries against roadmap.md's FEAT-ID status.

    ERROR when a queue entry has no roadmap row at all (unresolvable, a
    human must fix it). WARN when its status is done/abandoned (normal
    backlog evolution; /groom-backlog proposes removal). No finding for
    planned/active/blocked/deferred — deferred is a legitimate parked slot,
    per the roadmap's own status legend. Skipped without error when
    roadmap.md is absent, so a policy file may exist before a roadmap does.
    """
    statuses = roadmap_statuses()
    if not statuses:
        return []

    findings: list[str] = []
    for entry in queue:
        if not isinstance(entry, str) or not _FEAT_ID_RE.match(entry):
            continue
        status = statuses.get(entry)
        if status is None:
            findings.append(f"ERROR: queue: {entry!r} has no row in roadmap.md")
        elif status in _DONE_OR_ABANDONED:
            findings.append(
                f"WARN: queue: {entry!r} is roadmap status {status!r}"
            )
    return findings


def _check_version(version: object) -> list[str]:
    if version != 1:
        return [f"ERROR: 'version' must equal 1 (got {version!r})"]
    return []


def _check_queue(queue: object) -> list[str]:
    if not isinstance(queue, list):
        return ["ERROR: 'queue' must be a list of FEAT-YYYY-NNNN strings"]

    findings: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(queue):
        if not isinstance(entry, str) or not _FEAT_ID_RE.match(entry):
            findings.append(
                f"ERROR: queue[{index}]: {entry!r} does not match "
                f"FEAT-YYYY-NNNN"
            )
            continue
        if entry in seen:
            findings.append(f"ERROR: queue: duplicate entry {entry!r}")
        seen.add(entry)
    return findings


def _check_rules(rules: object) -> list[str]:
    if not isinstance(rules, dict):
        return ["ERROR: 'rules' must be a mapping"]

    findings: list[str] = []
    for section in ("bugs", "features", "triage"):
        if section not in rules:
            findings.append(f"ERROR: missing 'rules.{section}' key")

    if "bugs" in rules:
        findings.extend(_check_rules_bugs(rules["bugs"]))
    if "features" in rules:
        findings.extend(_check_rules_features(rules["features"]))
    if "triage" in rules:
        findings.extend(_check_rules_triage(rules["triage"]))
    return findings


def _check_rules_bugs(bugs: object) -> list[str]:
    if not isinstance(bugs, dict):
        return ["ERROR: 'rules.bugs' must be a mapping"]

    findings: list[str] = []
    preempt = bugs.get("preempt")
    if not isinstance(preempt, bool):
        findings.append(
            f"ERROR: 'rules.bugs.preempt' must be a bool (got {preempt!r})"
        )

    min_severity = bugs.get("min_severity")
    if min_severity not in SEVERITY_VALUES:
        findings.append(
            f"ERROR: 'rules.bugs.min_severity' has unknown value "
            f"{min_severity!r} — must be one of {sorted(SEVERITY_VALUES)}"
        )

    if "severity_aliases" in bugs:
        aliases = bugs["severity_aliases"]
        if not isinstance(aliases, dict):
            findings.append(
                f"ERROR: 'rules.bugs.severity_aliases' must be a mapping of "
                f"label word to severity (got {aliases!r})"
            )
        else:
            for key, value in aliases.items():
                word = str(key).strip().lower()
                if word in SEVERITY_VALUES:
                    findings.append(
                        f"ERROR: 'rules.bugs.severity_aliases' aliases "
                        f"{key!r}, which is already a severity value — the "
                        f"vocabulary wins and the alias would never apply"
                    )
                elif value not in SEVERITY_VALUES:
                    findings.append(
                        f"ERROR: 'rules.bugs.severity_aliases.{key}' points at "
                        f"{value!r} — must be one of {sorted(SEVERITY_VALUES)}"
                    )

    automerge = bugs.get("automerge")
    if automerge not in AUTOMERGE_VALUES:
        findings.append(
            f"ERROR: 'rules.bugs.automerge' has unknown value {automerge!r} "
            f"— must be one of {sorted(AUTOMERGE_VALUES)}"
        )

    if "max_diff_lines" in bugs:
        max_diff_lines = bugs["max_diff_lines"]
        if (
            not isinstance(max_diff_lines, int)
            or isinstance(max_diff_lines, bool)
            or max_diff_lines <= 0
        ):
            findings.append(
                f"ERROR: 'rules.bugs.max_diff_lines' must be an int > 0 "
                f"(got {max_diff_lines!r})"
            )

    if "max_merges_per_day" in bugs:
        max_merges_per_day = bugs["max_merges_per_day"]
        if (
            not isinstance(max_merges_per_day, int)
            or isinstance(max_merges_per_day, bool)
            or max_merges_per_day <= 0
        ):
            findings.append(
                f"ERROR: 'rules.bugs.max_merges_per_day' must be an int > 0 "
                f"(got {max_merges_per_day!r})"
            )

    # Validated rather than silently ignored (#1418). `bug_lane_limits` falls back
    # to the default on a malformed value, so without this an operator's declared
    # layout would be dropped with no signal — the same silent-inertness the
    # hardcoded prefix caused. An empty list is rejected too: it would refuse
    # every merge, which is a misconfiguration and not a way to disable the check.
    if "test_paths" in bugs:
        test_paths = bugs["test_paths"]
        if (
            not isinstance(test_paths, list)
            or not test_paths
            or not all(isinstance(e, str) and e.strip() for e in test_paths)
        ):
            findings.append(
                f"ERROR: 'rules.bugs.test_paths' must be a non-empty list of "
                f"non-empty path prefixes (got {test_paths!r})"
            )

    return findings


def _check_rules_features(features: object) -> list[str]:
    if not isinstance(features, dict):
        return ["ERROR: 'rules.features' must be a mapping"]

    findings: list[str] = []
    gate_review = features.get("gate_review")
    if gate_review not in GATE_REVIEW_VALUES:
        findings.append(
            f"ERROR: 'rules.features.gate_review' has unknown value "
            f"{gate_review!r} — must be one of {sorted(GATE_REVIEW_VALUES)}"
        )

    wip_limit = features.get("wip_limit")
    if not isinstance(wip_limit, int) or isinstance(wip_limit, bool) or wip_limit < 1:
        findings.append(
            f"ERROR: 'rules.features.wip_limit' must be an int >= 1 "
            f"(got {wip_limit!r})"
        )

    if "overrides" in features:
        findings.extend(_check_feature_overrides(features["overrides"]))
    return findings


def _check_feature_overrides(overrides: object) -> list[str]:
    if not isinstance(overrides, dict):
        return ["ERROR: 'rules.features.overrides' must be a mapping"]

    findings: list[str] = []
    for feat_id, value in overrides.items():
        if not _FEAT_ID_RE.match(str(feat_id)):
            findings.append(
                f"ERROR: rules.features.overrides: key {feat_id!r} does not "
                f"match FEAT-YYYY-NNNN"
            )
        if value not in GATE_REVIEW_VALUES:
            findings.append(
                f"ERROR: rules.features.overrides[{feat_id!r}]: unknown "
                f"value {value!r} — must be one of {sorted(GATE_REVIEW_VALUES)}"
            )
    return findings


def _check_rules_triage(triage: object) -> list[str]:
    if not isinstance(triage, dict):
        return ["ERROR: 'rules.triage' must be a mapping"]

    auto = triage.get("auto")
    if not isinstance(auto, bool):
        return [f"ERROR: 'rules.triage.auto' must be a bool (got {auto!r})"]
    return []


def _check_budgets(budgets: object) -> list[str]:
    if not isinstance(budgets, dict):
        return ["ERROR: 'budgets' must be a mapping"]

    findings: list[str] = []
    for field in _REQUIRED_BUDGET_FIELDS:
        if field not in budgets:
            findings.append(f"ERROR: missing 'budgets.{field}' key")
            continue
        value = budgets[field]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            findings.append(
                f"ERROR: 'budgets.{field}' must be an int > 0 (got {value!r})"
            )
    return findings


def _check_escalation(escalation: object) -> list[str]:
    if not isinstance(escalation, dict):
        return ["ERROR: 'escalation' must be a mapping"]

    findings: list[str] = []

    unknown = set(escalation) - _ESCALATION_KNOWN_KEYS
    for key in sorted(unknown):
        findings.append(f"ERROR: unknown 'escalation.{key}' key")

    for field in ("webhook_env", "assignee", "quiet_hours"):
        if field not in escalation:
            findings.append(f"ERROR: missing 'escalation.{field}' key")
            continue
        if not isinstance(escalation[field], str):
            findings.append(
                f"ERROR: 'escalation.{field}' must be a string "
                f"(got {escalation[field]!r})"
            )

    webhook_env = escalation.get("webhook_env")
    if (
        isinstance(webhook_env, str)
        and webhook_env
        and not _ENV_VAR_NAME_RE.match(webhook_env)
    ):
        findings.append(
            f"ERROR: 'escalation.webhook_env' must be an "
            f"environment-variable NAME, not a value (got {webhook_env!r})"
        )

    if "provider" in escalation:
        provider = escalation["provider"]
        if provider not in PROVIDER_VALUES:
            findings.append(
                f"ERROR: 'escalation.provider' has unknown value "
                f"{provider!r} — must be one of {sorted(PROVIDER_VALUES)}"
            )

    if "sla_hours" not in escalation:
        findings.append("ERROR: missing 'escalation.sla_hours' key")
    else:
        sla_hours = escalation["sla_hours"]
        if not isinstance(sla_hours, int) or isinstance(sla_hours, bool) or sla_hours <= 0:
            findings.append(
                f"ERROR: 'escalation.sla_hours' must be an int > 0 "
                f"(got {sla_hours!r})"
            )

    if "silence_hours" in escalation:
        silence_hours = escalation["silence_hours"]
        if (
            not isinstance(silence_hours, int)
            or isinstance(silence_hours, bool)
            or silence_hours <= 0
        ):
            findings.append(
                f"ERROR: 'escalation.silence_hours' must be an int > 0 "
                f"(got {silence_hours!r})"
            )
    return findings


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Specfuse agent-policy schema linter.",
        usage="lint_agent_policy.py [path/to/agent-policy.yml]",
    )
    parser.add_argument(
        "path", nargs="?", default=None,
        help="Path to agent-policy.yml (default .specfuse/agent-policy.yml).",
    )
    args = parser.parse_args()
    findings = validate_agent_policy(args.path)
    for finding in findings:
        print(finding)
    return 1 if any(f.startswith("ERROR: ") for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
