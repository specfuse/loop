#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""
Specfuse loop driver — single-repo, exploded-layout edition.

A "dumb driver, smart spec" loop in the Ralph tradition. Intelligence lives in the
work-unit files and the verification gates, never here. Per feature, per gate, the
driver:

  1. reads the task GRAPH from PLAN.md (gate order, WU membership, dependencies),
  2. finds the next ready work units in the current gate,
  3. dispatches each as a FRESH `claude -p` session with its declared model,
     handing it the WU file's prompt body,
  4. acts as the exit oracle by running the WU's verification ITSELF,
  5. on pass: makes one squashed, trailer-carrying commit per WU,
  6. on fail: re-dispatches a fresh session carrying the failure evidence, up to
     MAX_ATTEMPTS, then escalates (blocked_human) and halts the gate,
  7. when every WU in the gate is done — including the closing sequence
     (retrospective -> lessons -> docs -> plan-next) — marks the gate
     awaiting_review and stops for human reflection.

Ownership (one fact, one home):
  - PLAN.md  owns the SHAPE   : gates, which WUs are in them, dependency edges.
  - GATE-NN  owns the GATE    : gate status + definition of done + reflection.
  - WU-*.md  owns ITSELF      : type, model, status, attempts + the prompt body.

Durable state lives in those files, git history, and the per-feature event log —
never in a context window. Each dispatch is a fresh session. That is the Ralph
property, kept at work-unit granularity because units are crafted to land in one pass.

Two things differ in the orchestrator and are isolated behind `Backend`:
  - STATE BACKEND : status in WU/GATE files here; GitHub issue labels + registry there.
  - DISPATCH      : subprocess here; inbox + polling loop there.
Swap those; everything else is portable.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# The strict mini-YAML reader lives alongside this script; add its dir to
# sys.path so this script remains zero-install (stdlib only). The reader
# implements exactly the documented subset the loop authors with; see
# `_miniyaml.py` for the grammar and the fail-loud rejections.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _miniyaml  # noqa: E402

SPECFUSE_DIR = Path(".specfuse")
FEATURES_DIR = SPECFUSE_DIR / "features"
VERIFICATION_PATH = SPECFUSE_DIR / "verification.yml"
DRIVER_VERSION = "0.2.0"
MAX_ATTEMPTS = 3  # spinning threshold: 3 failed verification cycles -> escalate

# How to launch a fresh agent. {model} and {effort} are filled per WU; prompt is piped on stdin.
CLAUDE_CMD = ["claude", "-p", "--model", "{model}", "--effort", "{effort}"]

VALID_EFFORT = frozenset({"low", "medium", "high", "xhigh", "max"})

# Family aliases accepted in WU frontmatter's `model:` field.
# The CLI resolves them to the latest concrete model at dispatch time;
# the loop passes the value verbatim — no expansion here.
MODEL_ALIASES = frozenset({"sonnet", "opus", "haiku"})

# Defaults applied by load_wu when `model` or `effort` are absent from WU frontmatter.
# A WU that declares either field explicitly overrides these. Keys cover every VALID_TYPES value.
MODEL_BY_TYPE = {
    "implementation": "sonnet",
    "retrospective":  "sonnet",
    "lessons":        "sonnet",
    "docs":           "sonnet",
    "plan-next":      "opus",
    "close":          "opus",
}
EFFORT_BY_TYPE = {
    "implementation": "medium",
    "retrospective":  "low",
    "lessons":        "low",
    "docs":           "low",
    "plan-next":      "high",
    "close":          "high",
}

# Which verification gate set (a key in verification.yml) applies to each WU type.
GATES_FOR_TYPE = {
    "implementation": "code",
    "retrospective": "doc",
    "lessons": "doc",
    "docs": "doc",
    "plan-next": "plannext",
    # `close` collapses the four closing ceremonies into one session (single-gate only).
    # Reuses the `plannext` gate set: lint_plan.py verifies structural integrity post-close.
    "close": "plannext",
}

# Statuses the driver will dispatch. `draft` is excluded on purpose: plan-next
# writes the next gate's WUs as drafts, and a human must arm them first.
DISPATCHABLE = {"pending", "ready"}
DONE = "done"

# --------------------------------------------------------------------------- #
# Data model                                                                  #
# --------------------------------------------------------------------------- #


@dataclass
class WorkUnit:
    wu_id: str
    file: Path
    depends_on: list[str]      # from the PLAN.md graph
    type: str                  # from the WU file frontmatter
    model: str
    status: str
    attempts: int
    title: str
    body: str                  # the prompt handed to the session
    effort: str = "medium"     # low|medium|high|xhigh|max — passed as --effort to claude -p


@dataclass
class GateNode:
    number: int
    file: Path
    status: str                # from the GATE file frontmatter
    refs: list[dict] = field(default_factory=list)  # [{id, file, depends_on}]


# --------------------------------------------------------------------------- #
# Frontmatter helpers                                                         #
# --------------------------------------------------------------------------- #

FM = re.compile(r"^---\s*$")


def read_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text)."""
    lines = path.read_text().splitlines()
    if not lines or not FM.match(lines[0]):
        return {}, path.read_text()
    j = 1
    while j < len(lines) and not FM.match(lines[j]):
        j += 1
    fm = _miniyaml.parse("\n".join(lines[1:j])) or {}
    body = "\n".join(lines[j + 1 :])
    return fm, body


def write_frontmatter_field(path: Path, key: str, value) -> None:
    """Replace (or insert) a single key in a file's YAML frontmatter, leaving the
    body untouched. This is the whole reason the exploded layout is nicer than one
    shared file: status writes are clean single-file edits, not regex surgery."""
    lines = path.read_text().splitlines()
    if not lines or not FM.match(lines[0]):
        raise ValueError(f"{path} has no frontmatter")
    j = 1
    while j < len(lines) and not FM.match(lines[j]):
        j += 1
    block = lines[1:j]
    pat = re.compile(rf"^{re.escape(key)}:")
    for idx, line in enumerate(block):
        if pat.match(line):
            block[idx] = f"{key}: {value}"
            break
    else:
        block.append(f"{key}: {value}")
    new = ["---", *block, "---", *lines[j + 1 :]]
    path.write_text("\n".join(new) + "\n")


# --------------------------------------------------------------------------- #
# Plan / gate / WU loading                                                    #
# --------------------------------------------------------------------------- #


def find_feature(arg: str | None) -> Path:
    if arg:
        d = FEATURES_DIR / arg if not arg.startswith(".") else Path(arg)
        if not (d / "PLAN.md").exists():
            sys.exit(f"No PLAN.md under {d}")
        return d
    actives = []
    for d in sorted(FEATURES_DIR.glob("*/")):
        plan = d / "PLAN.md"
        if plan.exists():
            fm, _ = read_frontmatter(plan)
            if fm.get("status") == "active":
                actives.append(d)
    if len(actives) == 1:
        return actives[0]
    if not actives:
        sys.exit("No active feature. Set a feature's PLAN.md status to 'active'.")
    sys.exit(f"Multiple active features; pass --feature. Found: "
             f"{[d.name for d in actives]}")


def load_graph(feature_dir: Path) -> tuple[dict, list[GateNode]]:
    """Parse PLAN.md: feature frontmatter + the `gates` graph block."""
    fm, body = read_frontmatter(feature_dir / "PLAN.md")
    m = re.search(r"```ya?ml\s*\n(.*?)\n```", body, re.DOTALL)
    if not m:
        sys.exit("PLAN.md has no ```yaml graph block.")
    graph = _miniyaml.parse(m.group(1)) or {}
    gates: list[GateNode] = []
    for g in graph.get("gates", []):
        gate_file = feature_dir / g["file"]
        gfm, _ = read_frontmatter(gate_file) if gate_file.exists() else ({}, "")
        gates.append(
            GateNode(
                number=g["gate"],
                file=gate_file,
                status=gfm.get("status", "open"),
                refs=g.get("work_units", []) or [],
            )
        )
    return fm, gates


def load_wu(feature_dir: Path, ref: dict) -> WorkUnit:
    path = feature_dir / ref["file"]
    fm, body = read_frontmatter(path)
    title_m = re.search(r"^#\s+(.*)$", body, re.MULTILINE)
    wu_type = fm.get("type", "implementation")
    effort = fm.get("effort")
    if effort is None:
        effort = EFFORT_BY_TYPE.get(wu_type, "medium")
    elif effort not in VALID_EFFORT:
        raise ValueError(
            f"{path}: invalid effort '{effort}' — must be one of "
            f"{sorted(VALID_EFFORT)}"
        )
    wu_model = fm.get("model")
    if wu_model is None:
        wu_model = MODEL_BY_TYPE.get(wu_type, "claude-sonnet-4-6")
    return WorkUnit(
        wu_id=ref["id"],
        file=path,
        depends_on=list(ref.get("depends_on", []) or []),
        type=wu_type,
        model=wu_model,
        effort=effort,
        status=fm.get("status", "pending"),
        attempts=int(fm.get("attempts", 0)),
        title=title_m.group(1).strip() if title_m else ref["id"],
        body=body.strip(),
    )


# --------------------------------------------------------------------------- #
# State backend seam                                                          #
# --------------------------------------------------------------------------- #


class Backend:
    """All status mutation goes through here. The orchestrator subclasses this to
    write GitHub issue labels and registry frontmatter instead of these files —
    nothing above this line changes."""

    def set_wu(self, wu: WorkUnit, key: str, value) -> None:
        write_frontmatter_field(wu.file, key, value)
        setattr(wu, "status" if key == "status" else key, value)  # keep memory in sync

    def set_gate(self, gate: GateNode, status: str) -> None:
        write_frontmatter_field(gate.file, "status", status)
        gate.status = status

    def on_feature_start(self, feature_id: str, feat_fm: dict) -> None:
        """Called once per run(), before any dispatch, even on no-op polls."""

    def on_gate_passed(self, feature_id: str, gate_number: int) -> None:
        """Called after a gate's WUs are all done and the gate flips to awaiting_review."""

    def on_feature_complete(self, feature_id: str) -> None:
        """Called when all gates are passed and the feature is fully complete."""


def make_backend(feat_fm: dict) -> Backend:
    """Factory: returns GitHubBackend when source_issue_url is a GitHub issue URL."""
    source_url = feat_fm.get("source_issue_url", "") or ""
    # Pattern: https://github.com/<owner>/<repo>/issues/<number>
    _m = re.match(r"^https://github\.com/([^/]+/[^/]+)/issues/(\d+)$", source_url)
    if _m:
        from gh_backend import GitHubBackend  # noqa: E402
        return GitHubBackend(repo=_m.group(1), issue_number=int(_m.group(2)))
    return Backend()


# --------------------------------------------------------------------------- #
# Event log (per feature)                                                      #
# --------------------------------------------------------------------------- #


def build_event(event_type: str, correlation_id: str, payload: dict) -> dict:
    """Build a single event record. Pure — no I/O. Buffered in memory during a
    WU's lifecycle and flushed to disk at outcome time so a `git reset --hard`
    between attempts doesn't silently lose events that were appended."""
    return {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "event_type": event_type,
        "source": "driver",
        "source_version": DRIVER_VERSION,
        "payload": payload,
    }


def flush_events(events_path: Path, events: list) -> None:
    """Append a batch of buffered events to the JSONL log."""
    if not events:
        return
    with events_path.open("a") as fh:
        for evt in events:
            fh.write(json.dumps(evt) + "\n")


# --------------------------------------------------------------------------- #
# Git                                                                          #
# --------------------------------------------------------------------------- #


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def require_git_ready() -> None:
    """Driver squashes per WU on top of HEAD, so the repo needs an initial commit."""
    in_repo = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                             capture_output=True, text=True)
    if in_repo.returncode != 0:
        sys.exit("Not a git repository. Run `git init` from the repo root first.")
    has_head = subprocess.run(["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True)
    if has_head.returncode != 0:
        sys.exit("Git repository has no commits yet. The driver squashes per work "
                 "unit on top of HEAD; create an initial commit first "
                 "(e.g., `git commit --allow-empty -m 'init'`).")


def ensure_feature_branch(feat_fm: dict) -> None:
    """Ensure HEAD is on the feature's declared branch, creating it if needed.

    The methodology assigns each feature its own branch (PLAN.md frontmatter's
    `branch` field). Without this, per-WU squash commits land on whatever
    branch the user happened to be on, violating per-feature isolation.

    Idempotent: no-op if already on the declared branch. If the branch
    doesn't exist locally, creates it from the current HEAD (`git checkout -B`).
    """
    branch = feat_fm.get("branch")
    if not branch:
        return  # not declared — defensive (lint_plan normally requires it)
    current = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True,
    ).stdout.strip()
    if current == branch:
        return
    exists = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        capture_output=True, text=True,
    ).returncode == 0
    if exists:
        git("checkout", branch)
        print(f"Switched to feature branch '{branch}' (was on '{current}').")
    else:
        git("checkout", "-B", branch)
        print(f"Created feature branch '{branch}' from '{current}'.")


def acquire_tree_lock(specfuse_dir: Path):
    """Open .specfuse/.loop.lock and acquire a non-blocking exclusive flock.

    Returns the open file object; caller keeps it alive for the process
    lifetime — the kernel auto-releases on fd close or process exit (SIGKILL
    included), so no stale-lock cleanup is ever needed.
    Raises BlockingIOError if another process already holds the lock.
    """
    lock_path = specfuse_dir / ".loop.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = lock_path.open("w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fd.close()
        raise
    return fd


def write_cost_to_wu(backend, wu: WorkUnit, cum_usage: dict) -> None:
    """Write cumulative cost/token/duration fields to the WU's frontmatter at
    outcome time. duration_seconds is always written when present; cost/token
    fields are written only when a positive cost_usd or non-zero token counts
    were captured."""
    if "duration_seconds" in cum_usage:
        backend.set_wu(wu, "duration_seconds",
                       round(cum_usage["duration_seconds"], 3))
    if cum_usage.get("cost_usd", 0) <= 0 and not cum_usage.get("input_tokens") \
            and not cum_usage.get("output_tokens"):
        return
    backend.set_wu(wu, "cost_usd", round(cum_usage["cost_usd"], 6))
    backend.set_wu(wu, "input_tokens", cum_usage["input_tokens"])
    backend.set_wu(wu, "output_tokens", cum_usage["output_tokens"])


def gate_budget_usd(gate_file: Path) -> float | None:
    """Return the optional cumulative-cost ceiling declared on a GATE.md.

    Reads `cost_budget_usd` from the GATE file's frontmatter. Returns the float
    when set, None when the field is absent. A present-but-non-numeric value is
    a configuration error and raises ValueError naming the gate file — the
    fail-loud posture matches verify()'s missing-gate-set treatment.
    """
    fm, _ = read_frontmatter(gate_file)
    if "cost_budget_usd" not in fm:
        return None
    val = fm["cost_budget_usd"]
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(
            f"{gate_file}: cost_budget_usd must be numeric, got {val!r}"
        )
    return float(val)


def gate_spent_usd(plan: dict, gate: dict, feature_dir: Path) -> float:
    """Sum cost_usd across the gate's done WUs (closing-sequence included).

    Reads each WU file's frontmatter from `gate["work_units"]` and adds
    `cost_usd` when the WU's status is "done". WUs whose frontmatter omits
    cost_usd — cost tracking off, or the attempt didn't record a cost —
    contribute 0.0. `plan` is the feature frontmatter dict and is accepted for
    signature symmetry with the broader gate-budget helpers; the spent total
    is derived from WU files alone.
    """
    del plan  # signature symmetry — sum is derived from WU files only
    total = 0.0
    for ref in gate.get("work_units") or []:
        wu_file = ref.get("file")
        if not wu_file:
            continue
        wu_path = feature_dir / wu_file
        if not wu_path.exists():
            continue
        fm, _ = read_frontmatter(wu_path)
        if fm.get("status") != "done":
            continue
        cost = fm.get("cost_usd")
        if isinstance(cost, bool):
            continue
        if isinstance(cost, (int, float)):
            total += float(cost)
    return total


def _should_halt_for_budget(plan: dict, gate: dict, feature_dir: Path) -> bool:
    """Run-loop predicate: should the per-gate budget brake fire before the
    next WU dispatch? True when a budget is declared and the gate's spent
    total has reached or exceeded it. False otherwise (including no budget)."""
    gate_file = feature_dir / gate["file"]
    budget = gate_budget_usd(gate_file)
    if budget is None:
        return False
    return gate_spent_usd(plan, gate, feature_dir) >= budget


def commit_bookkeeping(paths: list, message: str) -> str | None:
    """Stage specific paths and create a chore(loop) bookkeeping commit.

    Used for state we want durable that is NOT part of a WU's squash commit:
    the WU's `blocked_human` status flip, the events.jsonl append for that
    block, the gate's `awaiting_review` status flip, and (on spinning) the
    per-attempt failure notes flushed out of memory.

    The bug this exists to prevent: writes to the working tree don't survive
    a subsequent `git reset --hard`. Status flips written but not committed
    silently revert. Anything that should persist must be committed.

    No-op if nothing to commit (path missing or no diff).
    """
    existing = [str(p) for p in paths if Path(p).exists()]
    if not existing:
        return None
    git("add", *existing)
    if not git("status", "--porcelain"):
        return None  # all paths were already in their committed state
    subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
    return git("rev-parse", "HEAD")


def squash_commit(wu: WorkUnit, head_before: str) -> str | None:
    if git("rev-parse", "HEAD") != head_before:
        git("reset", "--soft", head_before)  # fold away any commits the agent made
    if not git("status", "--porcelain"):
        return None
    git("add", "-A")
    msg = f"feat: {wu.title}\n\nFeature: {wu.wu_id}"
    subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
    return git("rev-parse", "HEAD")


# --------------------------------------------------------------------------- #
# Dispatch + verification                                                     #
# --------------------------------------------------------------------------- #

PROMPT_PREAMBLE = """\
You are executing a single Specfuse work unit. Read .specfuse/rules/ in full before \
acting; they are binding. Do NOT run any git command — the driver owns all commits \
and bookkeeping. Edit files only. End your turn with the RESULT block defined in \
.specfuse/rules/result-contract.md. Verification is run by the driver, not by you; \
report honestly.
"""

CAVEMAN_DIRECTIVE = """\
## Output terseness directive
Drop articles (a/an/the), filler words (just/really/basically/actually/simply), \
pleasantries (sure/certainly/of course/happy to), and hedging. \
Avoid prose narration between tool calls. \
Omit any end-of-turn summary. \
Write code blocks and the fenced RESULT block normally — do not abbreviate them. \
Quote error strings exactly as they appear.
"""

_CAVEMAN_EFFORT = frozenset({"low", "medium"})


def truncate_failure_note(note: str, max_lines: int = 200,
                          max_chars: int = 8000) -> str:
    """Return note unchanged when within limits; otherwise head+marker+tail.

    Splits budget 50/50 by line count, clamped by char budget too. Marker is
    plain ASCII with no triple-backtick so RESULT-block parsing is unaffected.
    """
    if len(note) <= max_chars and note.count("\n") < max_lines:
        return note
    lines = note.splitlines()
    n = len(lines)
    line_budget = min(max_lines, n - 1)
    head_count = line_budget // 2
    tail_count = line_budget - head_count
    half_char_budget = max_chars // 2
    while head_count > 0 and sum(len(ln) + 1 for ln in lines[:head_count]) > half_char_budget:
        head_count -= 1
    while tail_count > 0 and sum(len(ln) + 1 for ln in lines[n - tail_count:]) > half_char_budget:
        tail_count -= 1
    head_lines = lines[:head_count]
    tail_lines = lines[n - tail_count:] if tail_count > 0 else []
    elided_lines = n - head_count - tail_count
    elided_chars = len(note) - sum(len(ln) + 1 for ln in head_lines) \
                             - sum(len(ln) + 1 for ln in tail_lines)
    marker = f"\n... [{elided_lines} lines / {elided_chars} chars elided] ...\n"
    return "\n".join(head_lines) + marker + "\n".join(tail_lines)


def dispatch(wu: WorkUnit, failure_note: str | None,
             cost_tracking: bool = True) -> tuple[str, dict | None]:
    """Run a fresh agent session for this WU.

    When `cost_tracking` is True (default), requests JSON output from
    `claude -p` so the cost / token-usage block can be extracted. Returns
    (result_text, usage_dict_or_None). On any JSON parse failure or
    unexpected shape, usage is None — the result_text is still returned so
    the RESULT-block parser and verify() can do their normal work.
    """
    preamble = (PROMPT_PREAMBLE + "\n\n" + CAVEMAN_DIRECTIVE
                if wu.effort in _CAVEMAN_EFFORT else PROMPT_PREAMBLE)
    prompt = preamble + "\n\n" + wu.body
    if failure_note:
        prompt += ("\n\n## Previous attempt failed verification\n"
                   "A prior fresh attempt failed the gates below. Diagnose and fix; "
                   "do not repeat the same approach.\n\n"
                   + truncate_failure_note(failure_note))
    cmd = [p.replace("{model}", wu.model).replace("{effort}", wu.effort)
           for p in CLAUDE_CMD]
    if cost_tracking:
        cmd += ["--output-format", "json"]
    proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True)
    raw = proc.stdout or ""
    if not cost_tracking:
        return raw, None
    return parse_claude_json_output(raw)


def parse_claude_json_output(raw: str) -> tuple[str, dict | None]:
    """Parse Claude CLI's `--output-format=json` envelope.

    Tolerant: any shape drift returns (raw, None) so the caller falls back
    to text-mode RESULT-block parsing. Extracts `total_cost_usd`,
    `input_tokens`, `output_tokens`, and cache-token counts when present.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw, None
    if not isinstance(data, dict):
        return raw, None
    result_text = data.get("result", "")
    if not isinstance(result_text, str):
        result_text = raw
    usage: dict = {}
    cost = data.get("total_cost_usd")
    if isinstance(cost, (int, float)):
        usage["cost_usd"] = float(cost)
    u = data.get("usage")
    if isinstance(u, dict):
        for key in ("input_tokens", "output_tokens",
                    "cache_read_input_tokens", "cache_creation_input_tokens"):
            if isinstance(u.get(key), int):
                usage[key] = u[key]
    return result_text, (usage if usage else None)


RESULT_BLOCK_RE = re.compile(r"```result\s*\n(.*?)\n```", re.DOTALL)


def parse_result_block(stdout: str) -> dict | None:
    """Return the parsed final ```result``` block from stdout, or None.

    The result-contract rule (`.specfuse/rules/result-contract.md`) requires the
    agent to end its turn with a single fenced `result` block. Be forgiving:
    agents may discuss before it, may emit other fenced blocks elsewhere, may
    produce malformed YAML. Any of those returns None and the caller falls back
    to verify() as the exit oracle. Crashing the loop on a garbled agent output
    would defeat the purpose of having a separate oracle in the first place.
    """
    if not stdout:
        return None
    matches = list(RESULT_BLOCK_RE.finditer(stdout))
    if not matches:
        return None
    body = matches[-1].group(1)  # LAST result block — agents may discuss before it
    try:
        parsed = _miniyaml.parse(body)
    except Exception:  # noqa: BLE001 - intentional: see comment below
        # Broad catch is deliberate AND scoped to this site only. The agent's
        # stdout is the least-trusted input in the system (free-form LLM text
        # supposedly ending in a fenced result block); the forgiving contract
        # here is "anything malformed degrades to verify() decides, never
        # crashes the driver." A MiniYAMLError covers documented-subset
        # violations, but the parser is hand-rolled and could in principle
        # raise IndexError/ValueError/etc. on a sufficiently weird input —
        # those must also degrade, not crash a real driver run.
        # Every OTHER _miniyaml.parse site (read_frontmatter, load_graph,
        # load_verification, and the linter) reads operator-authored config
        # and intentionally keeps the strict MiniYAMLError-only handling so
        # malformed config files fail loudly, per verify()'s fail-closed
        # philosophy. Do not broaden those.
        return None
    return parsed if isinstance(parsed, dict) else None


def agent_reported_blocked(stdout: str) -> tuple[bool, str | None]:
    """Did the agent explicitly emit `status: blocked` in its RESULT block?

    Returns (True, blocked_reason) only when a well-formed block names
    `status: blocked`. Missing block, malformed block, or any other status
    falls through to (False, None) — the driver then runs verify() as usual.
    """
    parsed = parse_result_block(stdout)
    if not parsed or parsed.get("status") != "blocked":
        return False, None
    reason = parsed.get("blocked_reason")
    return True, (str(reason) if reason is not None else None)


def load_verification() -> dict:
    if not VERIFICATION_PATH.exists():
        return {}
    return _miniyaml.parse(VERIFICATION_PATH.read_text()) or {}


def verify(wu: WorkUnit, feature_dir: Path,
           cfg: dict | None = None) -> tuple[bool, str]:
    """Driver runs the gates itself — the exit oracle. Agent self-report is advisory.

    Empty or missing gate set for the WU's type is a CONFIGURATION failure (not a
    pass): a misconfigured verification.yml must not silently let work through.
    The failure message names the configuration cause so a human reading the log
    knows to fix verification.yml, not the work unit. `cfg` is injectable for
    testing; in production it is read from VERIFICATION_PATH.
    """
    if cfg is None:
        cfg = load_verification()
    set_name = GATES_FOR_TYPE.get(wu.type, "code")
    gate_set = cfg.get(set_name) or []
    if not gate_set:
        return False, (
            f"CONFIGURATION ERROR: no '{set_name}' gates configured in "
            f".specfuse/verification.yml for work-unit type '{wu.type}'. "
            f"This is not a work-unit failure — fix verification.yml and re-run."
        )
    results, ok_all = [], True
    for gate in gate_set:
        command = gate["command"].replace("{feature_dir}", str(feature_dir))
        # shell=True is intentional: gate commands are authored by the user in
        # verification.yml and routinely use shell features (pipes, &&, glob,
        # redirects — e.g. `dotnet build && dotnet test --no-build`). The input
        # is the project's own config, not untrusted external data.
        proc = subprocess.run(  # nosec B602
            command, shell=True, capture_output=True, text=True,
        )
        ok = proc.returncode == 0
        ok_all = ok_all and ok
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-15:]
        results.append(f"### {gate['name']}: {'PASS' if ok else 'FAIL'}\n"
                       f"```\n$ {command}\n" + "\n".join(tail) + "\n```")
    return ok_all, "\n\n".join(results)


def execute_unit_attempt(
    wu: WorkUnit,
    feature_dir: Path,
    failure_note: str | None,
    *,
    dispatch_fn=None,
    verify_fn=None,
    cost_tracking: bool = True,
) -> tuple[str, object, dict | None]:
    """One dispatch + parse + (if not blocked) verify cycle.

    Factored out of run() so the parse-and-decision logic is unit-testable
    without spawning a real agent — pass stub callables for dispatch_fn and
    verify_fn from a test.

    Returns (outcome, payload, usage) where outcome is one of:
      "blocked" — agent explicitly emitted status: blocked
      "passed"  — verify() passed
      "failed"  — verify() failed

    `usage` is the per-attempt cost/token dict from the agent dispatch when
    `cost_tracking` is True and the agent returned a parseable usage block;
    None otherwise (or when the dispatch_fn stub returns a plain string).

    Backward-compatible dispatch_fn contract: stubs may return either a
    plain `str` (treated as text-only, usage=None) or `(str, dict|None)`.
    """
    if verify_fn is None:
        verify_fn = verify
    if dispatch_fn is None:
        result = dispatch(wu, failure_note, cost_tracking)
    else:
        result = dispatch_fn(wu, failure_note)
    if isinstance(result, tuple):
        stdout, usage = result
    else:
        stdout, usage = result, None
    is_blocked, reason = agent_reported_blocked(stdout or "")
    if is_blocked:
        return "blocked", reason, usage
    passed, evidence = verify_fn(wu, feature_dir)
    return ("passed" if passed else "failed"), evidence, usage


# --------------------------------------------------------------------------- #
# The loop                                                                    #
# --------------------------------------------------------------------------- #


def ready(units: list[WorkUnit], done_ids: set[str]) -> list[WorkUnit]:
    return [u for u in units
            if u.status in DISPATCHABLE and all(d in done_ids for d in u.depends_on)]


def run(feature_arg: str | None, dry_run: bool) -> int:
    feature_dir = find_feature(feature_arg)
    feat_fm, gates = load_graph(feature_dir)
    feature_id = feat_fm.get("feature_id", feature_dir.name)
    events_path = feature_dir / "events.jsonl"
    work_dir = feature_dir / "work"
    backend = make_backend(feat_fm)
    backend.on_feature_start(feature_id, feat_fm)

    gate = next((g for g in gates if g.status != "passed"), None)
    if gate is None:
        print(f"{feature_id}: all gates passed — feature complete.")
        backend.on_feature_complete(feature_id)
        write_frontmatter_field(feature_dir / "PLAN.md", "status", "complete")
        return 0

    if not dry_run:
        # dry-run performs no mutation; inspecting while a real run is active must stay allowed.
        try:
            _lock_fd = acquire_tree_lock(SPECFUSE_DIR)  # held for run() lifetime
        except BlockingIOError:
            print(
                "another loop driver is already running in this working tree "
                "(.specfuse/.loop.lock held)",
                file=sys.stderr,
            )
            return 1
        require_git_ready()
        ensure_feature_branch(feat_fm)

    # Per-project cost-tracking toggle (top-level key in verification.yml,
    # default True). When True, the driver records cumulative cost / tokens
    # on each WU's frontmatter at outcome time and a per-attempt breakdown
    # in events.jsonl; when False the driver passes plain text mode to
    # `claude -p` and writes no cost fields.
    cfg = load_verification()
    cost_tracking = cfg.get("cost_tracking", True) is not False

    units = [load_wu(feature_dir, ref) for ref in gate.refs]
    print(f"== {feature_id} — Gate {gate.number} [{gate.status}] "
          f"({len(units)} work units) ==")

    # Arm check: a gate plan-next drafted starts with draft WUs. Don't execute drafts.
    drafts = [u for u in units if u.status == "draft"]
    if drafts and not dry_run:
        review = feature_dir / f"GATE-{gate.number:02d}-REVIEW.md"
        print(f"\nGate {gate.number} is drafted but not armed. {len(drafts)} work "
              f"unit(s) are in `draft`.")
        if review.exists():
            print(f"Read {review} for the planner's findings, review the draft WU "
                  f"files, then flip the ones you accept to `status: pending` and "
                  f"re-run.")
        return 2

    done_ids = {u.wu_id for u in units if u.status == DONE}
    blocked = False

    while True:
        pending = ready(units, done_ids)
        if not pending:
            break
        for wu in pending:  # sequential v1; the frontier is independent -> fan-out later
            # Per-gate cost budget brake — halt-between-WUs.
            # Mirrors MAX_ATTEMPTS' shape (a brake, not an estimator). Fires
            # before the next WU's set_wu(in_progress) so an in-progress WU
            # always runs to a terminal outcome (squash contract intact).
            # Skipped when the gate is already awaiting_review: the closing
            # sequence already flipped the gate; the reviewer will observe the
            # overshoot via the spent vs budget numbers in the next review.
            if not dry_run and gate.status != "awaiting_review":
                gate_dict = {"file": gate.file.name, "work_units": gate.refs}
                if _should_halt_for_budget(feat_fm, gate_dict, feature_dir):
                    budget = gate_budget_usd(gate.file)
                    spent = gate_spent_usd(feat_fm, gate_dict, feature_dir)
                    backend.set_gate(gate, "awaiting_review")
                    flush_events(events_path, [build_event(
                        "human_escalation", feature_id, {
                            "reason": "gate_budget_exceeded",
                            "budget_usd": budget,
                            "spent_usd": round(spent, 6),
                            "next_wu_id": wu.wu_id,
                        })])
                    commit_bookkeeping(
                        [gate.file, events_path],
                        f"chore(loop): gate {gate.number} budget exceeded "
                        f"— awaiting_review\n\nFeature: {feature_id}",
                    )
                    print(f"\nGate {gate.number} budget exceeded: spent "
                          f"${spent:.4f} >= budget ${budget:.4f}. "
                          f"Halted before {wu.wu_id}.")
                    return 1

            print(f"\n-- {wu.wu_id} [{wu.type}] model={wu.model}")
            if dry_run:
                print("   (dry run — would dispatch)")
                wu.status = DONE
                done_ids.add(wu.wu_id)
                continue

            head_before = git("rev-parse", "HEAD")
            backend.set_wu(wu, "status", "in_progress")
            # Events and per-attempt notes are buffered in memory during the
            # WU's lifecycle and flushed at outcome time. This prevents the
            # `git reset --hard` between failed attempts from silently
            # wiping appended events / status flips — anything that should
            # be durable is either committed in the squash (PASS) or in a
            # bookkeeping commit (BLOCKED/SPINNING).
            wu_events = [build_event("task_started", wu.wu_id,
                                     {"type": wu.type, "model": wu.model})]
            attempt_notes: list[tuple[int, str]] = []
            # Cost accumulators: per-attempt list goes to events.jsonl,
            # cumulative sum to WU frontmatter at outcome time.
            attempts_usage: list[dict] = []
            cum_usage = {"cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0,
                         "duration_seconds": 0.0}

            failure_note = None
            for attempt in range(1, MAX_ATTEMPTS + 1):
                backend.set_wu(wu, "attempts", attempt)
                print(f"   attempt {attempt}/{MAX_ATTEMPTS} — fresh session")
                t0 = time.monotonic()
                outcome, payload, usage = execute_unit_attempt(
                    wu, feature_dir, failure_note, cost_tracking=cost_tracking,
                )
                duration = round(time.monotonic() - t0, 3)
                attempt_record: dict = {"attempt": attempt,
                                        "duration_seconds": duration}
                if usage:
                    attempt_record.update(usage)
                    cum_usage["cost_usd"] += float(usage.get("cost_usd", 0.0))
                    cum_usage["input_tokens"] += int(usage.get("input_tokens", 0))
                    cum_usage["output_tokens"] += int(usage.get("output_tokens", 0))
                attempts_usage.append(attempt_record)
                cum_usage["duration_seconds"] = round(
                    cum_usage["duration_seconds"] + duration, 3)

                if outcome == "blocked":
                    # Reset agent work first; THEN write our bookkeeping; THEN
                    # commit it. Doing the flip before the reset would let the
                    # reset wipe the flip — the silent-state-loss bug.
                    git("reset", "--hard", head_before)
                    backend.set_wu(wu, "status", "blocked_human")
                    write_cost_to_wu(backend, wu, cum_usage)
                    wu_events.append(build_event("human_escalation", wu.wu_id, {
                        "reason": "agent_reported_blocked",
                        "blocked_reason": payload,
                        "attempts": attempt,
                        "attempts_usage": attempts_usage,
                    }))
                    flush_events(events_path, wu_events)
                    commit_bookkeeping(
                        [wu.file, events_path],
                        f"chore(loop): {wu.wu_id} blocked_human "
                        f"(agent-reported)\n\nFeature: {wu.wu_id}",
                    )
                    print(f"   BLOCKED by agent — "
                          f"{payload or '(no reason given)'}")
                    blocked = True
                    break

                if outcome == "passed":
                    # Flip status to DONE BEFORE the squash so the flip is
                    # included in the commit content — survives the next WU's
                    # reset. Then flush events so they ride in the same commit.
                    backend.set_wu(wu, "status", DONE)
                    write_cost_to_wu(backend, wu, cum_usage)
                    wu_events.append(build_event("task_completed", wu.wu_id, {
                        "attempts": attempt,
                        "attempts_usage": attempts_usage,
                    }))
                    flush_events(events_path, wu_events)
                    sha = squash_commit(wu, head_before)
                    done_ids.add(wu.wu_id)
                    print(f"   PASS — committed {sha}")
                    break

                # outcome == "failed": evidence in payload, retry within budget.
                # Per-attempt notes are buffered (not written to disk) so they
                # ride with the spinning-escalation commit if we exhaust
                # attempts; on eventual PASS they're discarded as scratch.
                attempt_notes.append((attempt, payload))
                failure_note = payload
                git("reset", "--hard", head_before)
                print(f"   FAIL attempt {attempt}/{MAX_ATTEMPTS}")
            else:
                # for-else: ran out of attempts without break = spinning.
                # The reset has already happened in the failed branch above.
                # Flush attempt notes to disk for human inspection, mark the
                # WU blocked_human, then commit all of it.
                wu_key = wu.wu_id.replace("/", "_")
                note_paths = []
                for atmpt, evidence in attempt_notes:
                    p = work_dir / wu_key / f"attempt-{atmpt}.md"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(evidence)
                    note_paths.append(p)
                backend.set_wu(wu, "status", "blocked_human")
                write_cost_to_wu(backend, wu, cum_usage)
                wu_events.append(build_event("human_escalation", wu.wu_id, {
                    "reason": "spinning_detected",
                    "attempts": MAX_ATTEMPTS,
                    "attempts_usage": attempts_usage,
                }))
                flush_events(events_path, wu_events)
                commit_bookkeeping(
                    [wu.file, events_path, *note_paths],
                    f"chore(loop): {wu.wu_id} blocked_human "
                    f"(spinning, {MAX_ATTEMPTS} attempts)\n\nFeature: {wu.wu_id}",
                )
                print(f"   BLOCKED after {MAX_ATTEMPTS} attempts — escalated")
                blocked = True

    if blocked:
        print("\nGate halted: work unit(s) need human attention.")
        return 1
    if dry_run:
        print(f"\n(dry run) Gate {gate.number} would complete and await review.")
        return 0

    backend.set_gate(gate, "awaiting_review")
    # on_gate_passed fires here: WUs all done, gate now awaiting human review
    backend.on_gate_passed(feature_id, gate.number)
    flush_events(events_path,
                 [build_event("gate_reached", feature_id, {"gate": gate.number})])
    commit_bookkeeping(
        [gate.file, events_path],
        f"chore(loop): gate {gate.number} awaiting_review\n\nFeature: {feature_id}",
    )
    review = feature_dir / f"GATE-{gate.number:02d}-REVIEW.md"
    print(f"\nGate {gate.number} complete (retro, lessons, docs, plan-next).")
    print(f"The next gate has been drafted. Read {review.name} for the planner's "
          f"findings and where to look, review the draft WU files, arm the ones you "
          f"accept (status -> pending), set this gate's status to `passed`, re-run.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Specfuse loop driver (single-repo).")
    ap.add_argument("--feature", help="Feature dir name under .specfuse/features/ "
                    "(optional if exactly one feature is active).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Walk the current gate without dispatching or writing.")
    args = ap.parse_args()
    if not FEATURES_DIR.exists():
        sys.exit(f"No {FEATURES_DIR}. Run from your repo root.")
    return run(args.feature, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
