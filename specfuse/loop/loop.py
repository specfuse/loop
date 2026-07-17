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
import hashlib
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import _filelock
from . import _miniyaml
from . import scaffold as _scaffold
from .gate_eval import evaluate_auto_close, AutoCloseDecision

SPECFUSE_DIR = Path(".specfuse")
REPO_ROOT = SPECFUSE_DIR.parent
FEATURES_DIR = SPECFUSE_DIR / "features"
VERIFICATION_PATH = SPECFUSE_DIR / "verification.yml"
DRIVER_VERSION = "0.3.14"
# Oldest scaffold layout this driver can drive. init.sh stamps the scaffold's own
# version into `.specfuse/VERSION`; check_scaffold_version() fails loud at startup if
# the consumer's scaffold is older than this, pointing at `specfuse upgrade`. Bump
# this only when a scaffold-format change makes an older `.specfuse/` undriveable.
MIN_SCAFFOLD_VERSION = "0.2.0"
SCAFFOLD_VERSION_PATH = SPECFUSE_DIR / "VERSION"
MAX_ATTEMPTS = 3  # spinning threshold: 3 failed verification cycles -> escalate
# Per-gate-command wall-clock ceiling. A gate that exceeds it is killed and the gate
# FAILS (not hangs) — so a deadlocked command (e.g. a test blocked on input()) can't
# stall the whole driver indefinitely. Generous vs real suites (this repo's is ~20s).
GATE_TIMEOUT_SECONDS = 900

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
    "implementation":    "sonnet",
    "retrospective":     "sonnet",
    "lessons":           "sonnet",
    "docs":              "sonnet",
    "plan-next":         "opus",
    "close":             "opus",
    "close-intermediate": "opus",
}
EFFORT_BY_TYPE = {
    "implementation":    "medium",
    "retrospective":     "low",
    "lessons":           "low",
    "docs":              "low",
    "plan-next":         "high",
    "close":             "high",
    "close-intermediate": "high",
}

# Which verification gate set (a key in verification.yml) applies to each WU type.
GATES_FOR_TYPE = {
    "implementation": "code",
    "retrospective": "doc",
    "lessons": "doc",
    "docs": "doc",
    "plan-next": "plannext",
    # `close` collapses the four closing ceremonies into one session for any terminal gate
    # (single- or multi-gate); `close-intermediate` is the equivalent for non-terminal gates,
    # leaving `plan-next` as a separate dispatch.
    # Both reuse the `plannext` gate set: lint_plan.py verifies structural integrity post-close.
    "close": "plannext",
    "close-intermediate": "plannext",
}

VERDICT_VALUES = frozenset({"met", "met_locally", "partially_met", "not_met"})

# Statuses the driver will dispatch. `draft` is excluded on purpose: plan-next
# writes the next gate's WUs as drafts, and a human must arm them first.
DISPATCHABLE = {"pending", "ready"}
DONE = "done"


def verdict_permits_terminal_flips(verdict: str | None) -> bool:
    """Return True iff verdict == 'met'; False for every other value including None."""
    return verdict == "met"


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
    # OPTIONAL sandbox-escape. When `unsandboxed: true` in WU frontmatter,
    # driver appends `--dangerously-skip-permissions` to the claude -p
    # invocation. Requires `unsandboxed_rationale` string in same frontmatter
    # (one-line justification, written to events.jsonl as the audit signal).
    # load_wu refuses to load a WU with unsandboxed=True and no rationale.
    unsandboxed: bool = False
    unsandboxed_rationale: str = ""
    verdict: str | None = None
    produces_driver_helper: list[str] = field(default_factory=list)
    # OPTIONAL author-declared deliverable contract. Names the file path(s) this
    # WU is contracted to yield. Distinct from `files_changed` (RESULT-block
    # runtime claim) and `produces_driver_helper` (driver symbols, lint-only):
    # `produces` names files and IS machine-enforced by FEAT-2026-0022/T02's
    # presence gate (each path must exist and be non-empty at completion).
    produces: list[str] = field(default_factory=list)
    # OPTIONAL extra verification gate sets, unioned onto the WU-type-selected set
    # by verify(). Names index into verification.yml the same way the type sets do
    # (e.g. `extra_gates: [live-verify]`). A name absent from verification.yml is a
    # CONFIGURATION ERROR, never a silent pass. See issue #62.
    extra_gates: list[str] = field(default_factory=list)


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


class WorkUnitFileMissingError(RuntimeError):
    """Raised when a frontmatter write targets a file that has vanished.

    Crash-hardening for #71: a per-attempt `git reset --hard` can delete an
    untracked-then-swept feature folder mid-run, after which the driver's next
    `set_wu(...)` → `write_frontmatter_field(...)` hit a bare FileNotFoundError
    (unhandled traceback, no diagnosis). This carries an actionable message —
    the likely cause (reset removed an uncommitted folder) and the reflog
    recovery — instead. The pre-flight untracked-folder guard normally prevents
    reaching this state; this is the defense-in-depth diagnostic.
    """


def write_frontmatter_field(path: Path, key: str, value) -> None:
    """Replace (or insert) a single key in a file's YAML frontmatter, leaving the
    body untouched. This is the whole reason the exploded layout is nicer than one
    shared file: status writes are clean single-file edits, not regex surgery."""
    if not path.exists():
        raise WorkUnitFileMissingError(
            f"frontmatter file {path} is gone — the feature folder may have been "
            f"removed by `git reset` mid-run (was it committed before the run?). "
            f"Recover the folder from the reflog "
            f"(`git checkout <squash-sha> -- {path.parent}`), reset the in-flight "
            f"WU's status, and commit it before re-running the loop."
        )
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
    done_pending_wrap = []
    for d in sorted(FEATURES_DIR.glob("*/")):
        plan = d / "PLAN.md"
        if plan.exists():
            fm, _ = read_frontmatter(plan)
            if fm.get("status") == "active":
                actives.append(d)
            elif fm.get("status") == "done":
                # Surface done features that may not have been wrapped yet.
                # Conservative heuristic: a RETROSPECTIVE.md exists (close
                # ceremony ran). Operator decides via /wrap-feature whether
                # push + PR are pending.
                if (d / "RETROSPECTIVE.md").is_file():
                    done_pending_wrap.append(d)
    if len(actives) == 1:
        return actives[0]
    if not actives:
        msg = "No active feature. Set a feature's PLAN.md status to 'active'.\n"
        if done_pending_wrap:
            names = ", ".join(d.name for d in done_pending_wrap[-3:])
            msg += (
                f"  - /wrap-feature   finalize a recently-closed feature "
                f"(push branch + open PR + merge advisory).\n"
                f"                    Candidates: {names}\n"
            )
        msg += (
            "  - /pick-feature   choose a 'planned' feature from the roadmap and activate it\n"
            "  - /draft-feature  scaffold a new feature (gates + gate-1 work units)\n"
            "  - /arm-gate       if a feature halted at a gate boundary awaiting review"
        )
        sys.exit(msg)
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
    unsandboxed = bool(fm.get("unsandboxed", False))
    unsandboxed_rationale = str(fm.get("unsandboxed_rationale", "") or "").strip()
    if unsandboxed and not unsandboxed_rationale:
        raise ValueError(
            f"{path}: `unsandboxed: true` requires a non-empty "
            f"`unsandboxed_rationale` in the same frontmatter. Sandbox-escape "
            f"is auditable; the rationale is the audit signal."
        )
    verdict: str | None = None
    if wu_type in {"close", "close-intermediate"}:
        verdict = fm.get("verdict") or None
    raw_pdh = fm.get("produces_driver_helper")
    if raw_pdh is None:
        produces_driver_helper: list[str] = []
    elif isinstance(raw_pdh, str):
        produces_driver_helper = [raw_pdh]
    elif isinstance(raw_pdh, list):
        produces_driver_helper = raw_pdh
    else:
        raise ValueError(
            f"{path}: `produces_driver_helper` must be a string or list of strings, "
            f"got {type(raw_pdh).__name__!r}"
        )
    raw_produces = fm.get("produces")
    if raw_produces is None:
        produces: list[str] = []
    elif isinstance(raw_produces, str):
        produces = [raw_produces]
    elif isinstance(raw_produces, list):
        produces = raw_produces
    else:
        raise ValueError(
            f"{path}: `produces` must be a string or list of strings, "
            f"got {type(raw_produces).__name__!r}"
        )
    raw_extra_gates = fm.get("extra_gates")
    if raw_extra_gates is None:
        extra_gates: list[str] = []
    elif isinstance(raw_extra_gates, str):
        extra_gates = [raw_extra_gates]
    elif isinstance(raw_extra_gates, list):
        extra_gates = [str(g) for g in raw_extra_gates]
    else:
        raise ValueError(
            f"{path}: `extra_gates` must be a string or list of strings, "
            f"got {type(raw_extra_gates).__name__!r}"
        )
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
        unsandboxed=unsandboxed,
        unsandboxed_rationale=unsandboxed_rationale,
        verdict=verdict,
        produces_driver_helper=produces_driver_helper,
        produces=produces,
        extra_gates=extra_gates,
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
        # Materialize the gate file if missing — PLAN.md may reference a gate
        # whose markdown was never authored (e.g. plan-next drafted an empty
        # follow-up gate that the human never filled in). Without this, the
        # first set_gate on a missing file crashes write_frontmatter_field
        # with FileNotFoundError and the whole feature halts unrecoverably.
        if not gate.file.is_file():
            gate.file.parent.mkdir(parents=True, exist_ok=True)
            gate.file.write_text(
                f"---\ngate: {gate.number}\nstatus: {status}\n---\n\n"
                f"# Gate {gate.number}\n\n"
                f"_Stub created by loop.set_gate because PLAN.md referenced "
                f"this gate but no markdown file existed. Body intentionally "
                f"minimal; edit if you want a real Definition of Done._\n"
            )
            gate.status = status
            return
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
        from .gh_backend import GitHubBackend
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


# Matches macOS ("/Users/" + "<name>/") and Linux ("/home/" + "<name>/") home
# prefixes, plus the Windows shape ("C:" + "\Users\" + "<name>" + "\" or "/",
# any drive letter, case-insensitive), at runtime without containing a literal
# "/Users/" substring in source, so this file's own staged diff never re-trips
# the structural leak-scan.
_HOME_PATH_RE = re.compile(r"/(?:Users|home)/[^/\s]+/")
_WIN_HOME_PATH_RE = re.compile(r"[A-Za-z]:\\Users\\[^\\/\s]+[\\/]", re.IGNORECASE)
_HOME_PATH_PLACEHOLDER = "<redacted-home>/"


def _redact_home_paths(value):
    """Recursively redact absolute home-directory prefixes from a JSON-ish value.

    Walks dict/list/str/scalar and replaces every "/Users/" + "<name>/",
    "/home/" + "<name>/", or Windows "<drive>:\\Users\\" + "<name>" + "\\"/"/"
    match in string leaves with a stable placeholder. Other text is preserved
    verbatim; idempotent (a second pass is a no-op).
    """
    if isinstance(value, str):
        value = _HOME_PATH_RE.sub(_HOME_PATH_PLACEHOLDER, value)
        return _WIN_HOME_PATH_RE.sub(_HOME_PATH_PLACEHOLDER, value)
    if isinstance(value, dict):
        return {k: _redact_home_paths(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_home_paths(v) for v in value]
    return value


def flush_events(events_path: Path, events: list) -> None:
    """Append a batch of buffered events to the JSONL log."""
    if not events:
        return
    with events_path.open("a") as fh:
        for evt in events:
            fh.write(json.dumps(_redact_home_paths(evt)) + "\n")


# --------------------------------------------------------------------------- #
# Attempt-outcome event helpers (FEAT-2026-0016/T01)                         #
# --------------------------------------------------------------------------- #


# Known signatures of a gate whose oracle SILENTLY DEGRADED — the command
# exits 0 while its analyzer measured a strict subset of the real check, so a
# green gate is a hollow pass (issue #134). Each entry is (compiled pattern,
# human reason). A gate whose output matches while exiting 0 is forced to FAIL
# so the driver blocks honestly instead of certifying `met` on a subset oracle.
# These are language/tool-specific data, not detection logic — extend the list
# as new silent-degradation modes surface; the matching in verify() is generic.
DEGRADED_ORACLE_MARKERS: list[tuple["re.Pattern[str]", str]] = [
    # Flutter/Dart custom_lint: the analyzer plugin can't resolve/build (e.g.
    # network to pub.dev blocked in the sandbox), so `flutter analyze` drops to
    # core lints only and still exits 0 — every custom_lint/riverpod_lint rule
    # is invisible. Observed on FEAT-2026-0005 (28 warnings CI caught, loop 0).
    (re.compile(r"error occurred while setting up the analyzer plugin",
                re.IGNORECASE),
     "custom_lint analyzer plugin did not load — 'flutter analyze' degraded to "
     "core lints only; the warnings oracle measured a subset of the real check "
     "and cannot certify zero warnings in this environment"),
]


def detect_degraded_oracle(stdout: str) -> str | None:
    """Return an honest reason string if gate output shows a silently degraded
    oracle, else None. Matches against DEGRADED_ORACLE_MARKERS (issue #134)."""
    for pattern, reason in DEGRADED_ORACLE_MARKERS:
        if pattern.search(stdout):
            return reason
    return None


def parse_gate_failure_signature(stdout: str) -> tuple[str, str]:
    """Extract (failure_class, failure_signature) from gate runner stdout.

    Scans for '### <gate>: FAIL' markers and maps them to a failure class.
    Returns ('other', 'no_gate_marker') when no marker is found.
    Both returned values are non-empty strings.
    """
    _GATE_CLASS_MAP = {
        "tests": "tests",
        "lint": "lint",
        "security": "security",
        "coverage": "coverage",
    }
    marker_re = re.compile(r"^### (\w+): FAIL", re.MULTILINE)
    m = marker_re.search(stdout)
    if not m:
        return "other", "no_gate_marker"
    gate_name = m.group(1)
    failure_class = _GATE_CLASS_MAP.get(gate_name, "other")
    after_lines = stdout[m.end():].splitlines()[:50]
    after_text = "\n".join(after_lines)
    _SIG_PATTERNS: dict[str, re.Pattern[str]] = {
        "tests": re.compile(r"^FAIL: (test_\S+)", re.MULTILINE),
        "lint": re.compile(r"\b([A-Z]\d{3,4})\b"),
        "security": re.compile(r"Issue: \[(B\d+)"),
        "coverage": re.compile(r"^([^\s]+\.py)\s+\d+\s+\d+", re.MULTILINE),
    }
    pattern = _SIG_PATTERNS.get(failure_class)
    if pattern:
        sm = pattern.search(after_text)
        if sm:
            sig = sm.group(1)
            return failure_class, sig if sig else "unknown"
    for line in after_lines:
        stripped = line.strip()
        if stripped:
            return failure_class, stripped[:100]
    return failure_class, "unknown"


def detect_spinning_signature_repeat(
    current: tuple[str | None, str | None],
    prior: tuple[str | None, str | None] | None,
) -> bool:
    """Return True iff the same (failure_class, failure_signature) repeats.

    Returns False when prior is None (first failure — nothing to compare).
    Returns False when either element of current is None.
    Returns False when current or prior is the no_gate_marker sentinel to
    avoid false-positive halts on parser-opaque failures (AC4).
    """
    _SENTINEL = ("other", "no_gate_marker")
    if prior is None:
        return False
    if current[0] is None or current[1] is None:
        return False
    if current == _SENTINEL or prior == _SENTINEL:
        return False
    return current == prior


def extract_failure_excerpt(stdout: str, max_chars: int = 500) -> str:
    """Return the last max_chars of failure-relevant lines from gate stdout.

    Relevant lines contain FAIL, Error, Exception, or Traceback.
    Falls back to the last max_chars of all stdout when no such lines exist.
    Trims to a UTF-8 safe boundary.
    """
    _KW = re.compile(r"FAIL|Error|Exception|Traceback", re.IGNORECASE)
    relevant = [ln for ln in stdout.splitlines() if _KW.search(ln)]
    text = "\n".join(relevant) if relevant else stdout
    encoded = text.encode("utf-8")
    if len(encoded) <= max_chars:
        return text
    return encoded[-max_chars:].decode("utf-8", errors="ignore")


def emit_attempt_outcome(
    wu: WorkUnit,
    attempt: int,
    outcome: str,
    usage: dict,
    *,
    failure_class: str | None = None,
    failure_signature: str | None = None,
    failure_excerpt: str | None = None,
    files_touched: list[str] | None = None,
    agent_status: str | None = None,
    agent_blocked_reason: str | None = None,
    extras: dict | None = None,
) -> dict:
    """Build a standardized attempt_outcome event dict (v1 payload shape).

    # T01's own events lack standardized payload; bootstrap gap

    Caller appends the returned dict to wu_events; flush_events runs at
    the existing flush point.  This helper does NOT call flush_events
    itself — preserves the 'one flush per outcome-cycle' invariant.

    extras: optional additional fields merged into the payload last.
    Used to preserve outcome-specific fields (e.g. assertion, summary)
    that are not part of the standard schema.
    """
    payload: dict = {
        "attempt": attempt,
        "outcome": outcome,
        "duration_seconds": usage.get("duration_seconds", 0.0),
        "cost_usd": usage.get("cost_usd", 0.0),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
        "model": wu.model,
        "effort": wu.effort,
        "failure_class": failure_class,
        "failure_signature": failure_signature,
        "failure_excerpt": failure_excerpt,
        "files_touched": files_touched if files_touched is not None else [],
        "agent_status": agent_status,
        "agent_blocked_reason": agent_blocked_reason,
        "re_arm_count": getattr(wu, "re_arm_count", 0),
    }
    if extras:
        payload.update(extras)
    return build_event("attempt_outcome", wu.wu_id, payload)


# --------------------------------------------------------------------------- #
# Git                                                                          #
# --------------------------------------------------------------------------- #


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def git_diff_names(head_before: str, head_after: str) -> list[str]:
    """Return file paths changed between two refs via git diff --name-only.

    When head_after is 'HEAD', also appends untracked files from
    git ls-files --others --exclude-standard (per [driver/files_changed-guard]
    LEARNINGS). Returns an empty list on any git error.
    """
    try:
        names = subprocess.run(
            ["git", "diff", "--name-only", head_before, head_after],
            capture_output=True, text=True, check=True,
        ).stdout.strip().splitlines()
        if head_after == "HEAD":
            untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, check=True,
            ).stdout.strip().splitlines()
            names = names + [f for f in untracked if f]
        return [f for f in names if f]
    except subprocess.CalledProcessError:
        return []


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


class FeatureBranchError(RuntimeError):
    """Raised when the feature branch cannot be entered safely.

    Carries an actionable, human-readable message — including git's own
    captured stderr when a checkout fails — instead of letting a bare
    subprocess.CalledProcessError (which swallows stderr) escape main().
    """


def untracked_paths() -> set[str]:
    """Repo-relative paths git reports as untracked, honoring .gitignore.

    Snapshotted per-WU immediately before dispatch so `squash_commit` can tell
    "the operator already had this file" from "this run created it" — only the
    latter belongs in the WU's commit. See issue #150 and `squash_commit`.
    """
    out = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True,
    ).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def _tracked_dirty_paths() -> set[str]:
    """Paths with TRACKED, uncommitted changes (staged or unstaged), repo-relative.

    Untracked files (porcelain `??`) are excluded: they never block a create
    (`checkout -B`), so counting them would spuriously flag a leftover
    events.jsonl as an "unexpected" change. The dirty-tree failure in #48 is
    tracked local modifications ("your local changes would be overwritten by
    checkout"), which is exactly what this set captures.

    This exclusion means untracked files DO carry onto a freshly created feature
    branch. That is safe only because `squash_commit` refuses to stage untracked
    paths that pre-date the WU's dispatch (#150) — before that fix, its
    `git add -A` committed them, so this guard was strictly narrower than the
    commit that followed it.
    """
    out = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout
    paths: set[str] = set()
    for line in out.splitlines():
        if not line.strip():
            continue
        if line[:2] == "??":
            continue  # untracked — carries harmlessly, never blocks checkout
        path = line[3:]
        if " -> " in path:  # rename: "old -> new"
            path = path.split(" -> ", 1)[1]
        paths.add(path.strip().strip('"'))
    return paths


def untracked_feature_files(feature_dir: "Path") -> list[str]:
    """Untracked, non-ignored files under *feature_dir* (repo-relative paths).

    `git ls-files --others --exclude-standard` lists files git knows nothing
    about, honoring .gitignore — so the driver-managed gitignored paths
    (`work/`, etc.) are excluded while genuinely uncommitted feature content
    (a freshly drafted PLAN/GATE/WU set) is surfaced. Empty list = the folder
    is fully tracked/committed. See `require_feature_folder_committed`.
    """
    out = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", str(feature_dir)],
        capture_output=True, text=True, check=True,
    ).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _current_branch() -> str:
    """The checked-out branch name ('' when detached)."""
    return git("branch", "--show-current")


def _default_branch() -> "str | None":
    """The repo's default branch, or None if undeterminable.

    Prefers origin's HEAD symref (`origin/main` -> `main`); falls back to a
    local `main`/`master` when there is no remote. None when neither resolves —
    callers then treat the current branch as non-default (auto_sync commits its
    scaffold sync rather than leaving it dangling).
    """
    ref = subprocess.run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        capture_output=True, text=True,
    )
    if ref.returncode == 0 and ref.stdout.strip():
        name = ref.stdout.strip()
        return name[len("origin/"):] if name.startswith("origin/") else name
    for cand in ("main", "master"):
        if subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", cand],
            capture_output=True, text=True,
        ).returncode == 0:
            return cand
    return None


def resolve_base(feat_fm: dict) -> "str | None":
    """The ref a feature's branch/PR should sit on top of.

    Frontmatter `base` wins when set and non-empty (after stripping
    whitespace). Absent, empty, or whitespace-only falls back to
    `_default_branch()`; if that too is undeterminable, falls back to the
    current branch. Callers (T02, T03) are responsible for wiring this in —
    this function only resolves the name, it does not touch git state.
    """
    base = feat_fm.get("base")
    if isinstance(base, str) and base.strip():
        return base.strip()
    default = _default_branch()
    if default:
        return default
    return _current_branch()


class BaseBranchError(RuntimeError):
    """Raised when a feature's declared `base` ref cannot be made available.

    Carries an actionable, human-readable message distinguishing a probable
    typo (remote confirms the ref does not exist) from an unreachable remote
    (network/auth failure — the ref's existence is simply unknown), so the two
    cases are never mistaken for each other.
    """


def ensure_base_ref(base: str) -> None:
    """Make sure git ref *base* is resolvable locally, fetching it if needed.

    No-ops (no network call) when `git rev-parse --verify base` already
    succeeds locally. Otherwise asks origin via `git ls-remote --exit-code`:
    if origin has it, fetches it and prints one line naming what and why; if
    origin explicitly does not have it, raises BaseBranchError naming likely
    local-branch candidates (probable typo); if ls-remote itself fails
    (offline/auth), raises a distinctly-worded BaseBranchError instead of
    conflating "does not exist" with "could not check".
    """
    local = subprocess.run(
        ["git", "rev-parse", "--verify", base],
        capture_output=True, text=True,
    )
    if local.returncode == 0:
        return
    remote = subprocess.run(
        ["git", "ls-remote", "--exit-code", "origin", base],
        capture_output=True, text=True,
    )
    if remote.returncode == 0:
        subprocess.run(["git", "fetch", "origin", base], capture_output=True, text=True, check=True)
        print(f"ensure_base_ref: fetched '{base}' from origin (declared feature base, not present locally).")
        return
    if remote.returncode == 2:
        # ls-remote's documented exit code for "ref not found on that remote".
        branches = subprocess.run(
            ["git", "branch", "--list", "--format=%(refname:short)"],
            capture_output=True, text=True,
        ).stdout.splitlines()
        candidates = [b.strip() for b in branches if b.strip()]
        listed = ", ".join(sorted(candidates)) if candidates else "(no local branches)"
        raise BaseBranchError(
            f"base '{base}' does not exist locally or on origin — probable typo. "
            f"Local branches: {listed}"
        )
    stderr = remote.stderr.strip() or remote.stdout.strip() or "(no git output)"
    raise BaseBranchError(
        f"base '{base}' could not be verified against origin — remote unreachable "
        f"(offline or auth failure), not confirmed missing: {stderr}"
    )


# Paths the scaffold overlay owns — auto_sync writes these on upgrade. They are
# the driver's, not the user's edits: they may carry onto a feature branch and
# are folded into the --prepare scaffold commit. Mirrors scaffold.py's versioned
# overlay set (templates/, rules/, docs/, schemas/) plus the meta files.
_SCAFFOLD_MANAGED_PREFIXES: tuple[str, ...] = (
    ".specfuse/templates/", ".specfuse/rules/",
    ".specfuse/docs/", ".specfuse/schemas/",
)
_SCAFFOLD_MANAGED_EXACT: frozenset[str] = frozenset({
    ".specfuse/VERSION", ".specfuse/.scaffold-manifest",
    ".specfuse/verification.yml.example",
})


def _is_scaffold_managed(path: str) -> bool:
    return (path in _SCAFFOLD_MANAGED_EXACT
            or any(path.startswith(p) for p in _SCAFFOLD_MANAGED_PREFIXES))


def _scaffold_managed_dirty() -> set[str]:
    """Tracked-dirty paths the scaffold overlay owns (subset of the dirty set)."""
    return {p for p in _tracked_dirty_paths() if _is_scaffold_managed(p)}


def _persist_scaffold_sync(installed: str) -> None:
    """After auto_sync overlays a newer scaffold, keep the tree clean for the
    rest of the run. On a non-default branch, commit the scaffold-managed
    changes (`chore(loop): sync scaffold to X.Y.Z`). On the DEFAULT branch, leave
    them and print guidance — committing scaffold churn onto the default branch
    is undesirable; --prepare (or the next ensure_feature_branch) carries them
    onto the feature branch and folds them into its scaffold commit instead.
    """
    dirty = _scaffold_managed_dirty()
    if not dirty:
        return
    branch = _current_branch()
    on_default = (not branch) or branch == _default_branch()
    if on_default:
        print(
            f"auto_sync: scaffold upgraded to {installed}; leaving "
            f"{len(dirty)} scaffold file(s) uncommitted on default branch "
            f"'{branch or '(detached)'}'. --prepare will carry them onto the "
            f"feature branch, or commit them yourself.",
            file=sys.stderr,
        )
        return
    commit_bookkeeping(sorted(dirty), f"chore(loop): sync scaffold to {installed}")
    print(
        f"auto_sync: scaffold upgraded to {installed}; committed "
        f"{len(dirty)} scaffold file(s) on '{branch}'.",
        file=sys.stderr,
    )


def _branch_prep_hint(feature_dir: "Path", feat_fm: dict, feature_id: str) -> str:
    """Actionable next-step block for the two pre-flight guards.

    `draft-feature` writes the feature folder but neither creates the feature's
    branch nor commits — so the loop refuses to start. The fix is two steps when
    you're not yet on the feature's branch (create it, then commit), and the
    `--prepare` flag does both for you. Build a hint that names the real branch
    and only includes the checkout line when it's actually needed.
    """
    branch = feat_fm.get("branch") or f"feat/{feature_id}"
    on_branch = _current_branch() == branch
    lines = [
        "",
        "Easiest — let the loop create the branch and commit for you:",
        "    specfuse-loop --prepare        # …then run",
        "    specfuse-loop --prepare-only   # …then stop, so you can review first",
        "",
        "Or do it manually:",
    ]
    if not on_branch:
        lines.append(f"    git checkout -b {branch}")
    lines.append(f"    git add {feature_dir}")
    lines.append(f"    git commit -m 'chore: scaffold feature {feature_id}'")
    return "\n".join(lines)


def require_feature_folder_committed(
    feature_dir: "Path", feat_fm: dict, feature_id: str,
) -> None:
    """Hard-stop if the dispatched feature folder has untracked files (#71).

    The per-attempt `git reset --hard head_before` rolls tracked files back to
    the pre-attempt base. A brand-new feature folder (all files untracked —
    `draft-feature` does not commit) passes the tracked-only dirty check, gets
    swept into the first WU's squash (becoming tracked), and is then DELETED by
    the next failed attempt's `reset --hard` (the folder is absent from
    head_before) — taking the WU markdown the driver is mid-read of with it, and
    crashing on the next frontmatter write. Refuse to start instead: a committed
    folder is part of head_before and survives every reset.
    """
    untracked = untracked_feature_files(feature_dir)
    if untracked:
        listed = "\n  ".join(sorted(untracked))
        sys.exit(
            f"loop.py: feature folder '{feature_dir}' has untracked files — "
            f"create the feature branch and commit them before running, or the "
            f"per-attempt `git reset --hard` will delete the folder mid-run (and "
            f"the driver will crash reading a WU file that no longer exists). "
            f"Untracked:\n  {listed}\n"
            + _branch_prep_hint(feature_dir, feat_fm, feature_id)
        )


def _expected_flip_paths(feature_dir: "Path | None") -> set[str]:
    """The paths /pick-feature legitimately leaves dirty before the loop runs:
    `.specfuse/roadmap.md` and the active feature's `PLAN.md`.
    """
    expected = {".specfuse/roadmap.md"}
    if feature_dir is not None:
        try:
            top = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            rel = (Path(feature_dir) / "PLAN.md").resolve().relative_to(
                Path(top).resolve()
            )
            expected.add(str(rel))
        except (subprocess.CalledProcessError, ValueError):
            pass  # can't resolve PLAN path — fall back to roadmap-only
    return expected


def feature_folder_tracked_modifications(feature_dir: "Path") -> list[str]:
    """Tracked, uncommitted modifications under *feature_dir* (repo-relative).

    Excludes untracked files (`??` — a separate concern) and the paths the
    driver itself manages or that /pick-feature legitimately leaves dirty:
    `PLAN.md` (pick-feature's status flip), `events.jsonl` (driver-managed,
    explicitly preserved across the per-attempt reset), and anything under a
    gitignored `work/` dir. What remains is human/skill edits to WU and GATE
    files — exactly arm-gate's status flips and acceptance-criteria revisions.
    """
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", str(feature_dir)],
        capture_output=True, text=True, check=True,
    ).stdout
    mods: list[str] = []
    for line in out.splitlines():
        if not line.strip() or line[:2] == "??":
            continue  # untracked carries separately; not this guard's concern
        path = line[3:]
        if " -> " in path:  # rename: "old -> new"
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        name = Path(path).name
        if name in ("PLAN.md", "events.jsonl"):
            continue
        if "/work/" in f"/{path}":
            continue
        mods.append(path)
    return mods


def require_feature_folder_unmodified(
    feature_dir: "Path", feat_fm: dict, feature_id: str,
) -> None:
    """Hard-stop on uncommitted arm-gate / WU-revision edits before dispatch (#74).

    arm-gate (and any manual WU-body revision at a gate boundary) writes
    UNCOMMITTED working-tree changes: WU status flips (draft → pending), the
    completed gate's status flip (awaiting_review → passed), and edited
    acceptance criteria. If the operator then runs the loop and the first
    dispatched WU's attempt fails, the per-attempt `git reset --hard
    head_before` DISCARDS those edits — the gate silently reverts to drafts and
    any AC revision is lost. Refuse to start until they are committed (mirrors
    #71's pre-flight): a committed arm is part of head_before and survives every
    reset, making the human checkpoint durable.
    """
    mods = feature_folder_tracked_modifications(feature_dir)
    if mods:
        listed = "\n  ".join(sorted(mods))
        sys.exit(
            f"loop.py: feature folder '{feature_dir}' has uncommitted changes — "
            f"commit them before running the loop, or the per-attempt "
            f"`git reset --hard` will discard them (your armed WU statuses and "
            f"any acceptance-criteria revisions would silently revert). "
            f"Modified:\n  {listed}\n"
            + _branch_prep_hint(feature_dir, feat_fm, feature_id)
        )


def prepare_feature(feat_fm: dict, feature_dir: "Path", feature_id: str) -> None:
    """`--prepare`: put the feature folder on its declared branch and commit it.

    `draft-feature` leaves the folder uncommitted on whatever branch you were on
    (usually the default). This creates/checks out the feature's branch (from
    PLAN.md `branch:`, carrying the untracked folder along) and commits the
    folder, so the pre-flight guards pass and the run can start. Idempotent: a
    no-op commit when there is nothing to commit.
    """
    branch = feat_fm.get("branch")
    ensure_feature_branch(feat_fm, feature_dir)
    # Stage the feature folder AND the roadmap surfaces draft-feature wrote but
    # left uncommitted (#127). The roadmap row is part of the feature's initial
    # state; if it isn't folded into this scaffold commit, the first WU's
    # per-attempt `git reset --hard head_before` discards it and terminal close
    # fails with roadmap_row_not_done ~20 minutes later. ensure_feature_branch
    # has already vetted the dirty set down to the expected /pick-feature flips.
    repo_root = Path(git("rev-parse", "--show-toplevel"))
    add_paths = [str(feature_dir)]
    for rel in (".specfuse/roadmap.md", ".specfuse/roadmap-archive.md"):
        if (repo_root / rel).exists():
            add_paths.append(str(repo_root / rel))
    # Fold auto_sync's scaffold overlay into this commit too. On the default
    # branch auto_sync leaves those uncommitted (see _persist_scaffold_sync);
    # committing them here lands the upgrade on the feature branch, clean.
    for rel in sorted(_scaffold_managed_dirty()):
        add_paths.append(str(repo_root / rel))
    git("add", "--", *add_paths)
    staged = git("status", "--porcelain", "--", *add_paths)
    if staged:
        git("commit", "-m", f"chore: scaffold feature {feature_id}")
        print(f"Prepared: committed feature folder on branch '{branch}'.")
    else:
        print(f"Prepare: feature folder already committed on branch '{branch}'.")


def _checked_checkout(checkout_args: list[str], action: str) -> str:
    """Run a `git checkout ...` guarded: on non-zero exit raise FeatureBranchError
    carrying git's stderr, instead of a bare CalledProcessError that hides it.
    """
    proc = subprocess.run(
        ["git", *checkout_args], capture_output=True, text=True,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip() or "(no git output)"
        raise FeatureBranchError(f"{action} failed: {stderr}")
    return proc.stdout.strip()


def ensure_feature_branch(feat_fm: dict, feature_dir: "Path | None" = None) -> None:
    """Ensure HEAD is on the feature's declared branch, creating it if needed.

    The methodology assigns each feature its own branch (PLAN.md frontmatter's
    `branch` field). Without this, per-WU squash commits land on whatever
    branch the user happened to be on, violating per-feature isolation.

    Idempotent: no-op if already on the declared branch. If the branch
    doesn't exist locally, creates it from the current HEAD (`git checkout -B`),
    which carries the expected /pick-feature flips (roadmap.md + PLAN.md) onto
    the new branch.

    Robust to the two real-world states that used to crash with a bare
    CalledProcessError (#48):

    * **Dirty tree.** Tracked changes confined to the expected /pick-feature
      flips are carried onto a freshly created branch. Tracked changes to any
      OTHER path stop the driver with a message naming them (silently moving
      unrelated edits onto a feature branch is worse than failing loudly).
    * **Stale divergent branch.** A pre-existing branch that is not an ancestor
      of HEAD is surfaced rather than silently checked out; resolution policy
      (reuse / recreate / abort) is left to the human.

    Any checkout failure raises FeatureBranchError carrying git's stderr.
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
    # A declared `base` (T01's resolve_base/ensure_base_ref) is the branch's
    # true starting point, not wherever HEAD happens to be standing. Resolving
    # and fetching it here — before any checkout — lets both branch creation
    # and the staleness check below anchor on the base instead of HEAD.
    # BaseBranchError is intentionally left to propagate uncaught: the base
    # cause must reach the operator, not be reshaped into a FeatureBranchError.
    base = resolve_base(feat_fm)
    if base:
        ensure_base_ref(base)
    else:
        base = current
    exists = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        capture_output=True, text=True,
    ).returncode == 0
    if exists:
        # Surface a stale branch that diverged from the declared base instead
        # of silently reusing it. `merge-base --is-ancestor B <base>` exits 0
        # iff B is an ancestor of base (i.e. base already contains B — safe).
        is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", branch, base],
            capture_output=True, text=True,
        ).returncode == 0
        if not is_ancestor:
            raise FeatureBranchError(
                f"branch '{branch}' has diverged from '{base}' — it carries "
                f"commits '{base}' does not, likely because it was created "
                f"from a different starting point or '{base}' has since moved "
                f"on. The safe action is to bring it up to date with the base:\n"
                f"  git checkout {branch} && git rebase {base}"
            )
        _checked_checkout(["checkout", branch], f"checkout of existing branch '{branch}'")
        print(f"Switched to feature branch '{branch}' (was on '{current}').")
    else:
        # Create-from-base carries the working tree onto the new branch. Only
        # the expected /pick-feature flips may ride along; anything else stops.
        dirty = _tracked_dirty_paths()
        # Scaffold-overlay files (auto_sync's own upgrade writes) ride along too:
        # they are driver-owned, and prepare_feature folds them into the scaffold
        # commit. Only genuinely-unrelated edits remain "unexpected" (#prepare).
        allowed = _expected_flip_paths(feature_dir) | _scaffold_managed_dirty()
        unexpected = dirty - allowed
        if unexpected:
            raise FeatureBranchError(
                "working tree has uncommitted changes to unexpected paths: "
                + ", ".join(sorted(unexpected))
                + f". Refusing to carry them onto new branch '{branch}'. "
                "Commit or stash them first, then re-run."
            )
        _checked_checkout(["checkout", "-B", branch, base], f"create of branch '{branch}'")
        print(f"Created feature branch '{branch}' from '{base}'.")


def acquire_tree_lock(specfuse_dir: Path):
    """Open .specfuse/.loop.lock and acquire a non-blocking exclusive lock.

    Delegates to `_filelock`, which selects fcntl.flock (POSIX) or
    msvcrt.locking (Windows) by sys.platform. See `_filelock` for why the
    kernel-auto-release property this preserves rules out pidfiles.
    Raises BlockingIOError if another process already holds the lock.
    """
    return _filelock.acquire_tree_lock(specfuse_dir)


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


def detect_rearm_dispatch(wu: WorkUnit) -> bool:
    """Return True when wu is a re-arm dispatch whose prior cycle's cost has
    not yet been folded into the cumulative accumulators.

    Reads re_arm_count and cost_usd from the WU's on-disk frontmatter because
    load_wu does not load those fields into the WorkUnit object.
    Returns False for first-time dispatches (re_arm_count absent or 0) and for
    re-arms where cost was already folded (cost_usd == 0 after a prior fold).
    """
    fm, _ = read_frontmatter(wu.file)
    re_arm_count = fm.get("re_arm_count", 0)
    if not isinstance(re_arm_count, int) or re_arm_count <= 0:
        return False
    cost_usd = fm.get("cost_usd", 0)
    return isinstance(cost_usd, (int, float)) and float(cost_usd) > 0


def fold_cumulative_on_rearm(wu: WorkUnit, backend: Backend) -> None:
    """Fold the prior dispatch cycle's cost/token/duration into cumulative fields.

    Called once per re-arm before the new cycle's attempt loop begins.
    Reads per-cycle fields (cost_usd, duration_seconds, input_tokens,
    output_tokens) written by the prior write_cost_to_wu call, accumulates
    them into cumulative_* counterparts (initialising to 0 when absent), then
    resets the per-cycle fields so the new cycle's write_cost_to_wu starts
    from zero.

    Backward-compatible: existing WUs with no cumulative_* fields initialise
    from 0 — no KeyError on first re-arm of a WU that pre-dates this contract.
    """
    fm, _ = read_frontmatter(wu.file)
    prior_cost = float(fm.get("cost_usd") or 0)
    prior_duration = float(fm.get("duration_seconds") or 0)
    prior_input = int(fm.get("input_tokens") or 0)
    prior_output = int(fm.get("output_tokens") or 0)

    cum_cost = float(fm.get("cumulative_cost_usd") or 0) + prior_cost
    cum_duration = float(fm.get("cumulative_duration_seconds") or 0) + prior_duration
    cum_input = int(fm.get("cumulative_input_tokens") or 0) + prior_input
    cum_output = int(fm.get("cumulative_output_tokens") or 0) + prior_output

    backend.set_wu(wu, "cumulative_cost_usd", round(cum_cost, 6))
    backend.set_wu(wu, "cumulative_duration_seconds", round(cum_duration, 3))
    backend.set_wu(wu, "cumulative_input_tokens", cum_input)
    backend.set_wu(wu, "cumulative_output_tokens", cum_output)

    # Reset per-cycle fields so the new cycle's write_cost_to_wu starts clean.
    backend.set_wu(wu, "cost_usd", 0.0)
    backend.set_wu(wu, "duration_seconds", 0.0)
    backend.set_wu(wu, "input_tokens", 0)
    backend.set_wu(wu, "output_tokens", 0)


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


class BookkeepingCommitError(RuntimeError):
    """Raised when commit_bookkeeping's `git commit` is rejected (non-zero exit).

    Sibling of SquashCommitError (issue #51) for the driver's bookkeeping
    commits (gate status flips + events.jsonl audit). Before this, the
    bookkeeping commit used `check=True` and a pre-commit hook rejection escaped
    run()/main() as a bare CalledProcessError with git's stderr swallowed — an
    unhandled traceback. It now raises this readable error carrying git's
    stderr instead. Surfaced FEAT-2026-0024: a leak-scan FINDINGS line quoting
    `git@github.com` was captured into events.jsonl and re-tripped the hook on
    the awaiting_review bookkeeping commit (the address is now allowlisted; this
    guard remains so a genuine bookkeeping leak fails loud, not cryptic).
    """


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
    # -f: caller curates the path list (driver-managed bookkeeping state); some
    # paths intentionally live under `.specfuse/**/work/` which the scaffold
    # gitignores. Force-add bypasses the ignore for these known paths only.
    git("add", "-f", *existing)
    if not git("status", "--porcelain"):
        return None  # all paths were already in their committed state
    res = subprocess.run(
        ["git", "commit", "-m", message], capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise BookkeepingCommitError(
            f"bookkeeping commit was rejected (exit {res.returncode}) — "
            f"usually a pre-commit hook rejecting the staged bookkeeping state.\n"
            f"--- git stderr ---\n{res.stderr.strip()}\n"
            f"--- git stdout ---\n{res.stdout.strip()}"
        )
    return git("rev-parse", "HEAD")


def reset_preserving_events(head_before: str, events_path: Path) -> None:
    """`git reset --hard <head_before>` without losing events.jsonl content.

    The hard-reset is the methodology's "wipe agent's edits before we write our
    bookkeeping" move. But events.jsonl can carry flushed-but-not-yet-committed
    entries from a PRIOR WU whose flush happened after its squash commit (the
    passed path flushes events AFTER the squash). Those entries sit on disk
    waiting for the NEXT WU's `commit_bookkeeping` to capture them. A bare
    `git reset --hard` between WUs rolls events.jsonl back to its last-
    committed state, silently dropping the prior WU's lifecycle events.

    Surfaced FEAT-2026-0015/T02 (commits 52a176a / 74d1911): T02 ran clean,
    its task_started + task_completed events were flushed post-squash, then
    T03 blocked → bare hard-reset wiped them. Same loss recurred when T02H
    completed clean and T03 was re-armed.

    This helper:
      1. Reads events.jsonl content (if any) into memory.
      2. Performs the hard-reset (drops the agent's working-tree edits).
      3. Writes the preserved events.jsonl back to disk.

    Subsequent `flush_events` calls then append to the preserved content;
    `commit_bookkeeping` captures the full history.
    """
    saved = events_path.read_text() if events_path.is_file() else None
    git("reset", "--hard", head_before)
    if saved is not None:
        events_path.write_text(saved)


class SquashCommitError(RuntimeError):
    """Raised when squash_commit's `git commit` is rejected (non-zero exit).

    The usual cause is a pre-commit hook (e.g. the leak-scan hook) rejecting the
    squash. The message carries git's stderr/stdout — which `capture_output`
    would otherwise swallow — so the caller can record an actionable failure
    note instead of crashing on a bare CalledProcessError. See issue #51.
    """


def squash_commit(
    wu: WorkUnit,
    head_before: str,
    untracked_before: "set[str] | frozenset[str]" = frozenset(),
) -> str | None:
    """Squash the WU's work into one commit; return its sha, or None if nothing.

    `untracked_before` is the set of untracked paths captured immediately before
    this WU was dispatched (see `untracked_paths`). Those are the operator's —
    scratch notes, another harness's config, a local script — and are unstaged
    after `add -A` so they are not absorbed into the WU's commit (#150). Files
    the run itself created are still committed: the distinction is "did this
    dispatch create it", not "is it tracked".

    Callers that omit the snapshot keep the legacy stage-everything behavior.
    """
    if git("rev-parse", "HEAD") != head_before:
        git("reset", "--soft", head_before)  # fold away any commits the agent made
    if not git("status", "--porcelain"):
        return None
    git("add", "-A")
    if untracked_before:
        # Unstage the operator's pre-existing untracked files. Paths the agent
        # deleted during dispatch are skipped — `git reset -- <missing>` is fine,
        # but pathspec-matching nothing errors on some git versions.
        stale = sorted(p for p in untracked_before if Path(p).exists())
        if stale:
            git("reset", "-q", "--", *stale)
        # `add -A` may have had nothing else to stage: a WU whose only tree
        # change was the operator's WIP must not manufacture a commit from it.
        if not git("diff", "--cached", "--name-only"):
            return None
    msg = f"feat: {wu.title}\n\nFeature: {wu.wu_id}"
    res = subprocess.run(
        ["git", "commit", "-m", msg], capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise SquashCommitError(
            f"git commit for {wu.wu_id} was rejected (exit {res.returncode}) — "
            f"usually a pre-commit hook rejecting the squash.\n"
            f"--- git stderr ---\n{res.stderr.strip()}\n"
            f"--- git stdout ---\n{res.stdout.strip()}"
        )
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


# leak-scan FINDINGS lines quote the offending match via repr, e.g.
#   line 12: email: 'a@b.com'
#   src/x.py:4: denylist: 'acme-widget'
# The category label is plain prose; the quoted token is the secret that
# re-trips a re-scan. We redact only the quoted token, preserving the label.
_LEAK_FINDING_RE = re.compile(
    r"(?P<label>email|user-path|private-host|denylist):\s*"
    r"(?P<q>['\"])(?P<tok>.*?)(?P=q)"
)


def redact_leak_findings(text: str) -> str:
    """Redact the quoted match inside captured leak-scan FINDINGS text (#76).

    When a squash (or bookkeeping) commit is rejected by the leak-scan
    pre-commit hook, git's stderr — which embeds the hook's FINDINGS block and
    QUOTES the offending token — is captured as the attempt-failure note and
    flushed into events.jsonl. The next bookkeeping commit re-scans events.jsonl
    and re-trips on that quoted token, cascading into more failures (the
    systemic form of the per-token allowlist band-aids). Replacing each quoted
    match with ``<redacted:sha8>`` keeps the audit signal (which check failed,
    on which line, and a stable hash to correlate occurrences) while removing
    the live trigger, so the captured note can never self-poison the log.

    No-op when *text* contains no leak-scan FINDINGS marker, so ordinary
    failure notes (verify output, tracebacks) pass through untouched.
    """
    if "leak-scan" not in text:
        return text

    def _sub(m: re.Match) -> str:
        digest = hashlib.sha256(m.group("tok").encode("utf-8")).hexdigest()[:8]
        return f"{m.group('label')}: '<redacted:{digest}>'"

    return _LEAK_FINDING_RE.sub(_sub, text)


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
    cmd = resolve_claude_cmd(cmd)
    if wu.unsandboxed:
        # Per-WU sandbox-escape. Audited via the unsandboxed_dispatch event
        # emitted in run()'s attempt loop; rationale lives in WU frontmatter.
        # Inserted after `-p` so it composes with --model/--effort/--output-format.
        cmd.insert(2, "--dangerously-skip-permissions")
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


def verify_files_changed(result: dict, head_before: str) -> list[str]:
    """Return claimed `files_changed` paths that show no diff against head_before.

    The RESULT-block contract lets the agent declare which paths its work
    touched. This guard, run before squash_commit, checks each claimed path
    actually differs from HEAD's pre-attempt SHA. A path that does not exist
    on disk is reported as "unchanged" — it cannot have a diff to commit.

    Returns an empty list when all claimed paths show real diffs, OR when
    `files_changed` is absent / empty (the opt-out: pre-existing WUs and the
    worked example do not always declare it; absence MUST NOT fire the
    guard).

    See FEAT-2026-0008 / RETROSPECTIVE for the failure mode this exists to
    catch — T04 and T08 of FEAT-2026-0007 declared files_changed naming
    source paths their attempts never touched.
    """
    paths = result.get("files_changed") or []
    if not isinstance(paths, list) or not paths:
        return []
    unchanged: list[str] = []
    for raw in paths:
        path = str(raw)
        if not Path(path).exists():
            unchanged.append(path)
            continue
        rc = subprocess.run(
            ["git", "diff", "--quiet", head_before, "--", path],
            capture_output=True,
        ).returncode
        if rc == 0:
            # `git diff` only sees tracked content — a freshly created file
            # is invisible to it even though it's a real change vs
            # head_before. Probe ls-files --others to catch the
            # newly-created-untracked case; without this, agent-created new
            # files (.tf, .sh, .md the WU just added) get flagged as
            # "unchanged" and the WU spins to blocked_human even though the
            # deliverable is present and correct.
            ls = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard",
                 "--", path],
                capture_output=True, text=True,
            ).stdout.strip()
            if not ls:
                unchanged.append(path)
    return unchanged


# Smoke-import runner (FEAT-2026-0008/T03). The conservative pattern matches
# ONLY a `python3 -c "from X import Y"` line. The agent-authored WU body may
# declare an existence check naming new symbols this WU just minted; the
# driver runs each match after a successful verify() + squash and rolls back
# the squash if any smoke import raises. Free-form `python3 -c` lines are
# NOT executed — running arbitrary agent-authored Python in the driver
# process would be a security regression (see WU escalation trigger 2).
SMOKE_IMPORT_RE = re.compile(
    r'''^\s*python3?\s+-c\s+(["'])from\s+\S+\s+import\s+\S+\1\s*$'''
)


def extract_smoke_imports(wu_body: str) -> list[str]:
    """Return WU-body lines matching the conservative import-smoke pattern.

    Each returned element is the full command string ready for
    `subprocess.run(shell=True, ...)`. Order preserved. Lines that look
    similar but do not match — `python -c "import X"`, `python -c
    "print(...)"`, prose — are skipped.
    """
    out: list[str] = []
    for line in wu_body.splitlines():
        if SMOKE_IMPORT_RE.match(line):
            out.append(line.strip())
    return out


def run_smoke_imports(commands: list[str], cwd: Path) -> tuple[bool, str]:
    """Run each smoke-import command in `cwd` in declared order.

    Returns `(True, "")` if every command exits 0. On the first non-zero
    exit, returns `(False, summary)` where `summary` names the failing
    command and its stderr — short, suitable for an event payload and a
    retry failure_note. Subsequent commands are not run; one failure is
    enough to fail the attempt.

    Inherits the driver's PATH so the active venv's `python3` resolves
    (the methodology requires the driver to be invoked from within an
    active venv per `[loop-driver-operation]`).
    """
    for cmd in commands:
        proc = subprocess.run(  # nosec B602
            cmd, shell=True, capture_output=True, text=True, cwd=str(cwd),
        )
        if proc.returncode != 0:
            summary = (
                f"smoke import failed (exit {proc.returncode}):\n"
                f"  $ {cmd}\n"
                f"stderr:\n{proc.stderr.strip()}"
            )
            return False, summary
    return True, ""


def is_zero_token_attempt(usage: dict | None) -> bool:
    """Did the dispatched session bill zero input tokens?

    Returns True iff `usage` is a dict whose `input_tokens` key is exactly 0.
    A zero-token attempt means the agent never produced output (often due to a
    transient CLI / quota / connectivity failure that the SDK reports as a
    success with empty content); its RESULT block — if present — is
    hallucinated upstream and must not be trusted.

    Returns False for `usage is None` (cost tracking disabled — preserve prior
    behavior for users who opt out), for a dict missing `input_tokens`, and
    for any positive integer. The guard is opt-in via the cost-tracking flag:
    when the operator runs with cost tracking off, `dispatch()` always returns
    `usage=None` and this function always returns False.

    See FEAT-2026-0008 / RETROSPECTIVE for the failure mode this exists to
    catch — a zero-token attempt in FEAT-2026-0007/T08H landed `status: done`
    despite the agent never running.
    """
    if not isinstance(usage, dict):
        return False
    return usage.get("input_tokens") == 0


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


def resolve_claude_cmd(cmd: list[str]) -> list[str]:
    """Resolve a bare `claude` argv[0] to its executable path on Windows.

    `subprocess.run(..., shell=False)` calls `CreateProcess` on Windows, which
    does not consult `PATHEXT` — a bare `"claude"` argv[0] will not resolve to
    the `claude.cmd` shim the Windows install ships. `shutil.which` does honor
    `PATHEXT`, so use it to find the real executable and substitute it as
    argv[0]; the rest of `cmd` (flags, model/effort substitution) is untouched.
    On POSIX, `shell=False` with a bare `claude` already resolves via PATH, so
    `cmd` is returned unchanged.
    """
    if sys.platform != "win32":
        return cmd
    resolved = shutil.which(cmd[0])
    if not resolved:
        raise SystemExit(
            f"claude not found on PATH — install Claude Code or add its "
            f"install directory to PATH (resolve_claude_cmd: "
            f"shutil.which('{cmd[0]}') returned None)."
        )
    return [resolved] + cmd[1:]


def resolve_bash() -> str | None:
    """Resolve a Git-for-Windows `bash.exe` for routing gate commands.

    Prefers deriving it from `git --exec-path` (the git-core dir inside a
    Git-for-Windows install; `bash.exe` lives at the install's `bin/bash.exe`,
    i.e. two levels up from git-core then into `bin`) over a bare
    `shutil.which("bash")`, which on a Windows host can resolve to
    `C:\\Windows\\System32\\bash.exe` — the WSL launcher, which fails with no
    distro installed. Returns None if no Git-Bash can be found.
    """
    try:
        completed = subprocess.run(
            ["git", "--exec-path"], capture_output=True, text=True, check=True,
        )
        exec_path = str(completed.stdout).strip()
        if exec_path:
            candidate = Path(exec_path).parent.parent / "bin" / "bash.exe"
            if candidate.is_file():
                return str(candidate)
    except Exception:
        pass

    # Manual PATH scan rather than shutil.which(): shutil.which's win32 branch
    # touches _winapi, which is unavailable when running under a mocked
    # sys.platform on a non-Windows test host.
    for dirname in os.environ.get("PATH", "").split(os.pathsep):
        if not dirname:
            continue
        for name in ("bash.exe", "bash"):
            candidate = Path(dirname) / name
            if candidate.is_file() and "system32" not in str(candidate).lower():
                return str(candidate)

    return None


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
    # Union any author-declared extra_gates sets onto the type-selected set,
    # deduping by gate name so a set shared between the type default and an extra
    # entry is not run twice (issue #62). An extra_gates name absent from
    # verification.yml is a CONFIGURATION ERROR — same class as an empty type set,
    # never a silent pass.
    gate_set = list(gate_set)
    seen_names = {g["name"] for g in gate_set}
    for extra_name in wu.extra_gates:
        if extra_name == set_name:
            continue  # already the type-selected set
        extra_set = cfg.get(extra_name)
        if not extra_set:
            return False, (
                f"CONFIGURATION ERROR: work unit declares `extra_gates: "
                f"[{extra_name}]` but no '{extra_name}' gates are configured in "
                f".specfuse/verification.yml. This is not a work-unit failure — "
                f"fix verification.yml (or the WU's extra_gates) and re-run."
            )
        for gate in extra_set:
            if gate["name"] in seen_names:
                continue
            seen_names.add(gate["name"])
            gate_set.append(gate)
    results, ok_all = [], True
    for gate in gate_set:
        command = gate["command"].replace("{feature_dir}", str(feature_dir))
        # shell=True is intentional: gate commands are authored by the user in
        # verification.yml and routinely use shell features (pipes, &&, glob,
        # redirects — e.g. `dotnet build && dotnet test --no-build`). The input
        # is the project's own config, not untrusted external data.
        #
        # Two hang defenses (a bare subprocess.run(timeout=) is NOT enough — on
        # timeout it SIGKILLs only the shell, leaving a hung grandchild holding the
        # output pipe so communicate() stalls past the timeout):
        #  1. stdin=DEVNULL — a gate that reads stdin (e.g. a test calling input())
        #     gets EOF immediately and fails fast instead of blocking forever.
        #  2. start_new_session + killpg (POSIX) / CREATE_NEW_PROCESS_GROUP +
        #     taskkill (Windows) on timeout — the gate runs in its own process
        #     group; on timeout the WHOLE group (shell + grandchildren) is
        #     killed, so the timer actually returns.
        is_win32 = sys.platform == "win32"
        spawn_kwargs = (
            {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)}
            if is_win32
            else {"start_new_session": True}
        )
        if is_win32:
            # cmd.exe (the shell=True default on Windows) does not understand
            # the POSIX shell syntax (&&, ||, globs, pipes) that real
            # verification.yml gate commands routinely use. Route through
            # Git-Bash instead so gate commands run unmodified across
            # platforms.
            bash = resolve_bash()
            if not bash:
                ok_all = False
                results.append(
                    f"### {gate['name']}: FAIL\n```\n$ {command}\n"
                    f"No Git-Bash found — install Git for Windows "
                    f"(https://git-scm.com/download/win) so gate commands can "
                    f"run through bash.exe.\n```"
                )
                continue
            popen_argv = [bash, "-c", command]
            popen_kwargs = dict(shell=False)
        else:
            popen_argv = command
            popen_kwargs = dict(shell=True)  # nosec B604
        proc = subprocess.Popen(  # nosec B602
            popen_argv, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            **popen_kwargs, **spawn_kwargs,
        )
        try:
            out, _ = proc.communicate(timeout=GATE_TIMEOUT_SECONDS)
            ok = proc.returncode == 0
            tail = (out or "").strip().splitlines()[-15:]
            # A green gate whose oracle silently degraded is a hollow pass
            # (issue #134): force FAIL and name the degradation honestly so the
            # log reads as "oracle couldn't measure it," not "code is clean."
            if ok:
                degraded = detect_degraded_oracle(out or "")
                if degraded:
                    ok = False
                    tail = tail + [f"DEGRADED ORACLE: {degraded}"]
        except subprocess.TimeoutExpired:
            if is_win32:
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                    capture_output=True,
                )
            else:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    proc.kill()
            out, _ = proc.communicate()
            ok = False
            tail = (out or "").strip().splitlines()[-10:] + [
                f"GATE TIMEOUT: exceeded {GATE_TIMEOUT_SECONDS}s and was killed "
                f"(process group) — a hang (test reading stdin, infinite loop, "
                f"or a wedged subprocess)."
            ]
        ok_all = ok_all and ok
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
    head_before: str | None = None,
) -> tuple[str, object, dict | None]:
    """One dispatch + parse + (if not blocked) verify cycle.

    Factored out of run() so the parse-and-decision logic is unit-testable
    without spawning a real agent — pass stub callables for dispatch_fn and
    verify_fn from a test.

    Returns (outcome, payload, usage) where outcome is one of:
      "zero_token"              — usage reports input_tokens=0 (agent never
                                  ran); payload is None
      "blocked"                 — agent explicitly emitted status: blocked
      "passed"                  — verify() passed AND the files_changed
                                  guard found nothing to flag
      "failed"                  — verify() failed
      "files_changed_mismatch"  — verify() passed but the RESULT's
                                  files_changed list names paths that show
                                  no diff against head_before; payload is
                                  the list of unchanged paths

    `usage` is the per-attempt cost/token dict from the agent dispatch when
    `cost_tracking` is True and the agent returned a parseable usage block;
    None otherwise (or when the dispatch_fn stub returns a plain string).

    Backward-compatible dispatch_fn contract: stubs may return either a
    plain `str` (treated as text-only, usage=None) or `(str, dict|None)`.

    `head_before` is the pre-attempt HEAD SHA the files_changed guard
    diffs against. None disables the guard — preserved for unit tests that
    exercise this function in isolation without a git working tree.
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
    # Zero-token guard runs BEFORE RESULT-block parsing: the agent did not
    # produce output, so any block in stdout is hallucinated upstream and
    # must not be trusted (FEAT-2026-0008/T01). Opt-in via cost tracking —
    # when disabled, usage is None and is_zero_token_attempt returns False.
    if is_zero_token_attempt(usage):
        return "zero_token", None, usage
    is_blocked, reason = agent_reported_blocked(stdout or "")
    if is_blocked:
        return "blocked", reason, usage
    passed, evidence = verify_fn(wu, feature_dir)
    if not passed:
        return "failed", evidence, usage
    # files_changed guard (FEAT-2026-0008/T02): the agent's RESULT claim
    # gets diffed against head_before BEFORE squash_commit. A non-empty
    # mismatch flags the attempt as a verification failure even though
    # verify() reported PASS — gates can't see "the diff is empty" when
    # the gate commands operate on files unrelated to the WU's scope.
    if head_before is not None:
        parsed = parse_result_block(stdout or "")
        if parsed:
            unchanged = verify_files_changed(parsed, head_before)
            if unchanged:
                return "files_changed_mismatch", unchanged, usage
    return "passed", evidence, usage


# --------------------------------------------------------------------------- #
# Roadmap row parser (header-name based) — issue #15                          #
# --------------------------------------------------------------------------- #


def _parse_roadmap_row(roadmap_text: str, feature_id: str) -> dict | None:
    """Find feature_id's row in roadmap.md and return columns mapped by header name.

    Looks up the first markdown table header row containing a 'Status' cell,
    parses column names by name (not by positional index), then finds the
    feature_id data row after the header. Tolerates any column count and any
    ordering, including project-specific columns like 'Priority' or 'Budget'.

    Returns a dict on success:
        'columns':    {col_name: stripped_value, ...}
        'cell_spans': {col_name: (start, end), ...} absolute offsets into
                      roadmap_text spanning the BETWEEN-PIPES content (suitable
                      for whole-cell rewrites).
        'row_span':   (start, end) absolute offsets of the full row line.

    Returns None if no table header containing 'Status' is found, or if no
    feature_id row exists after that header.
    """
    # Locate the table header — a line `| col1 | col2 | ... |` whose cells
    # include the literal 'Status'. The header row appears immediately above
    # the markdown separator line; we use 'Status' in its cells as the marker.
    header_re = re.compile(r"^\|([^\n]*)\|\s*$", re.MULTILINE)
    header_m = None
    col_names: list[str] = []
    for m in header_re.finditer(roadmap_text):
        cells = [c.strip() for c in m.group(1).split("|")]
        if "Status" in cells:
            header_m = m
            col_names = cells
            break
    if header_m is None:
        return None

    # Locate the feature_id data row AFTER the header.
    row_re = re.compile(
        r"^\|\s*" + re.escape(feature_id) + r"\s*\|[^\n]*$",
        re.MULTILINE,
    )
    row_m = row_re.search(roadmap_text, pos=header_m.end())
    if not row_m:
        return None

    row_text = row_m.group(0)
    row_start_abs = row_m.start()

    # Pipe positions inside the row identify cell boundaries.
    pipes = [i for i, ch in enumerate(row_text) if ch == "|"]
    if len(pipes) < len(col_names) + 1:
        # Malformed row — fewer cells than the header declares.
        return None

    columns: dict[str, str] = {}
    cell_spans: dict[str, tuple[int, int]] = {}
    for col_idx, col_name in enumerate(col_names):
        cell_start_rel = pipes[col_idx] + 1
        cell_end_rel = pipes[col_idx + 1]
        raw = row_text[cell_start_rel:cell_end_rel]
        columns[col_name] = raw.strip()
        cell_spans[col_name] = (
            row_start_abs + cell_start_rel,
            row_start_abs + cell_end_rel,
        )

    return {
        "columns": columns,
        "cell_spans": cell_spans,
        "row_span": (row_start_abs, row_m.end()),
    }


# --------------------------------------------------------------------------- #
# Auto-archive helper                                                         #
# --------------------------------------------------------------------------- #


def auto_archive_feature(feature_id: str, repo_root: Path) -> str:
    """Re-implement roadmap-archive single-feature algorithm (Steps 1–6) in-driver.

    Returns "archived", "already archived", or "refused: <reason>".
    No git operations; touches only roadmap.md and roadmap-archive.md under repo_root.
    """
    roadmap_path = repo_root / ".specfuse" / "roadmap.md"
    archive_path = repo_root / ".specfuse" / "roadmap-archive.md"

    feat_id_lower = feature_id.lower()
    anchor = f'<a id="{feat_id_lower}"></a>'
    back_link = f'[→ archive](roadmap-archive.md#{feat_id_lower})'
    marker = "<!-- Archived sections appended below -->"

    # Step 1 — read and validate table row (header-name based; issue #15)
    if not roadmap_path.exists():
        return f"refused: {roadmap_path} not found"
    roadmap_text = roadmap_path.read_text()

    parsed = _parse_roadmap_row(roadmap_text, feature_id)
    if parsed is None:
        return f"refused: {feature_id} not found in roadmap"

    status = parsed["columns"].get("Status", "")
    detail = parsed["columns"].get("Detail", "")

    if "roadmap-archive.md#" in detail:
        return "already archived"
    if status not in ("done", "abandoned"):
        return f"refused: status={status}"

    # Step 2 — extract inline section
    section_re = re.compile(
        r'^(## ' + re.escape(feature_id) + r'[^\n]*(?:\n(?!## )[^\n]*)*\n?)',
        re.MULTILINE,
    )
    section_m = section_re.search(roadmap_text)
    had_inline_section = section_m is not None
    if had_inline_section:
        section_text = section_m.group(1).rstrip('\n') + '\n'
    else:
        # Row-only feature: a roadmap table row exists (status done/abandoned,
        # Detail still '—' — the back-link case already returned at Step 1) but
        # there is no inline `## FEAT-ID` detail section to move. /draft-feature
        # emits a table row without a detail section, so an auto-closed feature
        # drafted that way reaches here. Returning "already archived" without
        # writing the anchor leaves assert_terminal_flips_fired unsatisfiable
        # and halts the driver on archive_anchor_missing (FEAT-2026-0022
        # surfaced this live). Synthesize a minimal stub section so the anchor
        # and back-link still materialize.
        title = parsed["columns"].get("Title", "").strip()
        heading = f"## {feature_id}" + (f" — {title}" if title else "")
        section_text = (
            f"{heading}\n\n"
            "_No inline detail section was recorded for this feature; "
            "stub written at archive time._\n"
        )

    # Step 3 — append anchor + section to archive after marker.
    # Auto-create the archive file if a project never shipped it (the
    # roadmap-archive skill requires it to pre-exist; the unattended driver
    # must not crash on its absence — see FileNotFoundError on read_text).
    if not archive_path.exists():
        project = ""
        fm = re.match(r'^---\n(.*?)\n---', roadmap_text, re.DOTALL)
        if fm:
            pm = re.search(r'^project:\s*(.+)$', fm.group(1), re.MULTILINE)
            if pm:
                project = pm.group(1).strip()
        header = (
            (f"---\nproject: {project}\n---\n\n" if project else "")
            + "# Archived feature details\n\n"
            "This file holds the detail sections for features whose status has "
            "reached `done` or `abandoned`.\n\n"
            f"{marker}\n"
        )
        archive_path.write_text(header)
    archive_text = archive_path.read_text()
    if marker not in archive_text:
        return "refused: archive marker absent"
    marker_end = archive_text.index(marker) + len(marker)
    new_archive = archive_text[:marker_end] + f"\n{anchor}\n{section_text}" + archive_text[marker_end:]
    archive_path.write_text(new_archive)

    # Step 4 — update Detail cell with back-link (skip if column absent; issue #15)
    if "Detail" in parsed["cell_spans"]:
        detail_start, detail_end = parsed["cell_spans"]["Detail"]
        roadmap_text = (
            roadmap_text[:detail_start] + f" {back_link} " + roadmap_text[detail_end:]
        )

    # Step 5 — remove inline section (re-search since row update shifted
    # offsets). Only when one actually existed to move; a synthesized stub
    # was never in roadmap.md, so there is nothing to strip.
    if had_inline_section:
        section_m2 = section_re.search(roadmap_text)
        if section_m2:
            roadmap_text = roadmap_text[:section_m2.start()] + roadmap_text[section_m2.end():]
            roadmap_text = re.sub(r'\n{3,}', '\n\n', roadmap_text)
    roadmap_path.write_text(roadmap_text)

    return "archived"


def _legacy_4wu_terminal_close_complete(
    wu: "WorkUnit",
    units: "list[WorkUnit]",
    gate,
    gates: list,
) -> bool:
    """Detect legacy 4-WU close sequence completion on a terminal gate (issue #16).

    Pre-FEAT-2026-0015 feature scaffolds use the four-WU closing sequence
    (`retrospective` → `lessons` → `docs` → `plan-next`). FEAT-2026-0015 wired
    `fire_terminal_flips` to fire only on `close`-type WUs, leaving the legacy
    sequence with no terminating-equivalent trigger. This helper recognizes
    completion of the 4-WU sequence as terminating-equivalent so the driver
    can fire `fire_terminal_flips` on the gate.

    Returns True iff:
      - `wu.type == "plan-next"` (the last WU in the sequence)
      - `gate is gates[-1]` (terminal gate)
      - The gate's `units` include all four legacy types
        (`retrospective`, `lessons`, `docs`, `plan-next`) AND each is `done`.
    """
    if wu.type != "plan-next":
        return False
    if gate is not gates[-1]:
        return False
    required = {"retrospective", "lessons", "docs", "plan-next"}
    have_done = {u.type for u in units if u.type in required and u.status == DONE}
    return required.issubset(have_done)


def fire_terminal_flips(wu: WorkUnit, feature_dir: Path, repo_root: Path) -> list[Path]:
    """Flip terminal gate → passed, roadmap row → done, call auto_archive_feature.

    Called for close-type WUs after squash when verdict_permits_terminal_flips is True.
    Non-fatal: skips via logging, only raises on internal exceptions.
    Returns the Paths actually modified (for the bookkeeping commit add list).
    """
    modified: set[Path] = set()
    feature_id = wu.wu_id.rsplit("/", 1)[0]

    _, gates = load_graph(feature_dir)
    if not gates:
        logging.warning("fire_terminal_flips: no gates in PLAN.md for %s", wu.wu_id)
    else:
        terminal_gate = gates[-1]
        gate_path = terminal_gate.file
        if not gate_path.exists():
            logging.warning(
                "fire_terminal_flips: terminal gate file absent: %s — skipping gate flip",
                gate_path,
            )
        else:
            current_gate_status = terminal_gate.status
            if current_gate_status == "passed":
                logging.info(
                    "fire_terminal_flips: %s already passed — skipping gate flip",
                    gate_path.name,
                )
            elif current_gate_status == "awaiting_review":
                write_frontmatter_field(gate_path, "status", "passed")
                modified.add(gate_path)
            else:
                logging.warning(
                    "fire_terminal_flips: %s status is %r (not awaiting_review or passed)"
                    " — skipping gate flip",
                    gate_path.name,
                    current_gate_status,
                )

    roadmap_path = repo_root / ".specfuse" / "roadmap.md"
    if not roadmap_path.exists():
        logging.warning(
            "fire_terminal_flips: roadmap.md absent at %s — skipping row flip",
            roadmap_path,
        )
    else:
        # Header-name based parsing — tolerates projects with extra columns
        # (e.g. Priority). See issue #15.
        roadmap_text = roadmap_path.read_text()
        parsed = _parse_roadmap_row(roadmap_text, feature_id)
        if parsed is None:
            logging.warning(
                "fire_terminal_flips: %s not found in roadmap.md — skipping row flip",
                feature_id,
            )
        else:
            current_row_status = parsed["columns"].get("Status", "")
            status_start, status_end = parsed["cell_spans"]["Status"]
            if current_row_status == "done":
                logging.info(
                    "fire_terminal_flips: roadmap row for %s already done — skipping",
                    feature_id,
                )
            elif current_row_status == "active":
                status_cell = roadmap_text[status_start:status_end]
                new_roadmap = (
                    roadmap_text[:status_start]
                    + status_cell.replace("active", "done", 1)
                    + roadmap_text[status_end:]
                )
                roadmap_path.write_text(new_roadmap)
                modified.add(roadmap_path)
            else:
                logging.warning(
                    "fire_terminal_flips: roadmap row for %s has status %r"
                    " (not active or done) — skipping row flip",
                    feature_id,
                    current_row_status,
                )

    # PLAN.md status -> done (FEAT-2026-0023/T01, closes #49). Consolidate the
    # terminal PLAN flip into this one driver-side owner so BOTH the dispatched-
    # close path (loop.run's close branch) and the auto-close path
    # (_fire_and_verify_terminal_flips) get it for free — previously only the
    # dispatched path's *agent* flipped PLAN.md, so the agent-less auto-close
    # path left it `active`. Idempotent: a no-op when already `done`. Gated on
    # verdict_permits_terminal_flips so a hedged/non-met close does NOT flip PLAN
    # to done. Verdict is re-read from disk (not wu.verdict) to mirror
    # assert_terminal_flips_fired: the auto-close path writes verdict=met to the
    # WU file via mark_close_wu_auto_closed but leaves the in-memory wu.verdict
    # None, so disk is the authoritative source for both paths.
    # Re-read verdict from disk only when the WU file exists. The legacy 4-WU
    # close sequence reaches here with a plan-next WU that carries no verdict
    # field (and whose file may be a synthetic stub in tests); a missing file or
    # a non-met verdict simply skips the PLAN flip, leaving legacy behavior
    # unchanged (those features flip PLAN via the plan-next agent, as before).
    disk_verdict = None
    if wu.file.is_file():
        wu_fm, _ = read_frontmatter(wu.file)
        disk_verdict = wu_fm.get("verdict") or None
    if not verdict_permits_terminal_flips(disk_verdict):
        logging.info(
            "fire_terminal_flips: verdict %r does not permit terminal flips"
            " — skipping PLAN.md flip for %s",
            disk_verdict,
            wu.wu_id,
        )
    else:
        plan_path = feature_dir / "PLAN.md"
        if not plan_path.exists():
            logging.warning(
                "fire_terminal_flips: PLAN.md absent at %s — skipping PLAN flip",
                plan_path,
            )
        else:
            plan_fm, _ = read_frontmatter(plan_path)
            current_plan_status = plan_fm.get("status", "")
            if current_plan_status == "done":
                logging.info(
                    "fire_terminal_flips: PLAN.md for %s already done — skipping",
                    feature_id,
                )
            else:
                write_frontmatter_field(plan_path, "status", "done")
                modified.add(plan_path)

    archive_result = auto_archive_feature(feature_id, repo_root)
    if archive_result == "archived":
        modified.add(roadmap_path)
        modified.add(repo_root / ".specfuse" / "roadmap-archive.md")
    elif archive_result == "already archived":
        logging.info(
            "fire_terminal_flips: %s already archived — skipping auto-archive",
            feature_id,
        )
    else:
        logging.warning(
            "fire_terminal_flips: auto_archive_feature: %s — run /roadmap-archive manually",
            archive_result,
        )

    return list(modified)


# --------------------------------------------------------------------------- #
# Terminal auto-close helpers (FEAT-2026-0018/T04)                           #
# --------------------------------------------------------------------------- #


def _already_auto_closed(wu_file: Path) -> bool:
    """Return True iff the WU's on-disk frontmatter already shows it has been
    auto-closed (status=done AND auto_close truthy).

    Idempotency guard for both maybe_auto_close_intermediate and
    maybe_auto_close_terminal — prevents the duplicate `auto_close_decision`
    event and duplicate bookkeeping commit observed in issue #23 when the
    dispatch loop re-enters with a stale in-memory wu.status.
    """
    if not wu_file.is_file():
        return False
    fm, _ = read_frontmatter(wu_file)
    if fm.get("status") != DONE:
        return False
    auto = fm.get("auto_close")
    return auto in (True, "true", "True")


def write_stub_retrospective_terminal(
    feature_dir: Path,
    gate_number: int,
    decision: AutoCloseDecision,
) -> None:
    """Write (or append) the auto-close stub section to RETROSPECTIVE.md.

    Satisfies both assert_retrospective_exists (non-empty file) and
    assert_retrospective_gate_section (^#{1,3} Gate N heading).
    """
    retro = feature_dir / "RETROSPECTIVE.md"
    metrics = decision.metrics
    budget = metrics.get("gate_budget")
    budget_str = f"${budget:.2f}" if budget is not None else "<unset>"
    total_cost = metrics.get("gate_total_cost", 0.0)
    section = (
        f"## Gate {gate_number} — auto-closed (predicate=v1)\n\n"
        f"On-plan close; full retrospective ceremony skipped per\n"
        f"`evaluate_auto_close`.\n\n"
        f"- feature_id: {decision.feature_id}\n"
        f"- predicate_version: {decision.predicate_version}\n"
        f"- gate_total_cost: ${total_cost:.2f}\n"
        f"- gate_budget: {budget_str}\n"
        f"- reasons: [] (auto=True)\n"
    )
    if retro.exists():
        with retro.open("a") as fh:
            fh.write("\n" + section)
    else:
        retro.write_text(section)


def mark_close_wu_auto_closed(
    wu: "WorkUnit | None",
    decision: AutoCloseDecision,
) -> None:
    """Flip close-WU frontmatter fields for the auto-close path.

    Sets status=done, verdict=met (so assert_terminal_flips_fired fires),
    auto_close=true, auto_close_reasons=[] for downstream discoverability.
    No-op when wu is None (legacy gate without a close WU).
    """
    if wu is None:
        return
    write_frontmatter_field(wu.file, "status", "done")
    write_frontmatter_field(wu.file, "verdict", "met")
    write_frontmatter_field(wu.file, "auto_close", "true")
    write_frontmatter_field(wu.file, "auto_close_reasons", "[]")


def resolve_auto_close_override(
    args: "argparse.Namespace",
    feature_dir: Path,
) -> tuple[bool, str]:
    """Return (override_active, reason) for --force-full-close or PLAN.md field."""
    if getattr(args, "force_full_close", None):
        return (True, "force_full_close_cli_flag")
    plan_path = feature_dir / "PLAN.md"
    if plan_path.is_file():
        fm, _ = read_frontmatter(plan_path)
        if fm.get("auto_close_disabled") in (True, "true", "True"):
            return (True, "auto_close_disabled_per_plan")
    return (False, "")


def maybe_auto_close_terminal(
    feature_dir: Path,
    feature_id: str,
    gate: "GateNode",
    gates: "list[GateNode]",
    events_path: Path,
    close_wu_for_terminal: "WorkUnit | None",
    repo_root: Path = REPO_ROOT,
) -> tuple[bool, AutoCloseDecision]:
    """Evaluate the auto-close predicate for the terminal gate.

    Returns (True, decision) when predicate fires and the auto path was taken.
    Returns (False, decision) when predicate refuses; caller falls through to
    the existing close-WU dispatch path unchanged.

    Idempotent: a second call after the WU has already been auto-closed on
    disk short-circuits without re-emitting events (see
    `maybe_auto_close_intermediate` and issue #23 for the rationale).
    """
    if close_wu_for_terminal is not None and _already_auto_closed(close_wu_for_terminal.file):
        return False, AutoCloseDecision(
            auto=False,
            reasons=["already_auto_closed"],
            metrics={},
            gate_id=gate.number,
            feature_id=feature_id,
            predicate_version="v1",
        )
    decision = evaluate_auto_close(feature_dir, gate.number)
    if not decision.auto:
        return False, decision
    write_stub_retrospective_terminal(feature_dir, gate.number, decision)
    mark_close_wu_auto_closed(close_wu_for_terminal, decision)
    metrics = decision.metrics
    flush_events(events_path, [build_event(
        "auto_close_decision", feature_id, {
            "gate": gate.number,
            "auto": True,
            "reasons": decision.reasons,
            "predicate_version": decision.predicate_version,
            "metrics": {
                "gate_total_cost": metrics.get("gate_total_cost", 0.0),
                "gate_budget": metrics.get("gate_budget"),
                "blocked_human_events": metrics.get("blocked_human_events", []),
                "replan_events": metrics.get("replan_events", []),
            },
        },
    )])
    return True, decision


# --------------------------------------------------------------------------- #
# Intermediate auto-close helpers (FEAT-2026-0018/T05)                        #
# --------------------------------------------------------------------------- #


def append_stub_retrospective_intermediate(
    feature_dir: Path,
    gate_number: int,
    decision: AutoCloseDecision,
) -> None:
    """APPEND a Gate N auto-close stub to RETROSPECTIVE.md; create file if absent.

    Idempotent: skips if a '## Gate N ... auto-closed' heading already exists
    (re-arm guard, AC5). Satisfies assert_retrospective_gate_section.
    """
    retro = feature_dir / "RETROSPECTIVE.md"
    if retro.exists() and re.search(
        rf"^##\s+Gate\s+{gate_number}\b.*auto-closed",
        retro.read_text(),
        re.MULTILINE,
    ):
        return
    metrics = decision.metrics
    budget = metrics.get("gate_budget")
    budget_str = f"${budget:.2f}" if budget is not None else "<unset>"
    total_cost = metrics.get("gate_total_cost", 0.0)
    section = (
        f"## Gate {gate_number} — auto-closed (predicate=v1)\n\n"
        f"On-plan intermediate close; full close-intermediate ceremony\n"
        f"skipped per `evaluate_auto_close`. `plan-next` WU dispatched\n"
        f"to draft gate {gate_number + 1}.\n\n"
        f"- feature_id: {decision.feature_id}\n"
        f"- predicate_version: {decision.predicate_version}\n"
        f"- gate_total_cost: ${total_cost:.2f}\n"
        f"- gate_budget: {budget_str}\n"
        f"- reasons: [] (auto=True)\n"
    )
    if retro.exists():
        with retro.open("a") as fh:
            fh.write("\n" + section)
    else:
        retro.write_text(section)


def maybe_auto_close_intermediate(
    feature_dir: Path,
    feature_id: str,
    gate: "GateNode",
    gates: "list[GateNode]",
    events_path: Path,
    repo_root: Path,
    close_intermediate_wu: "WorkUnit | None",
    plan_next_wu: "WorkUnit | None",
) -> tuple[bool, AutoCloseDecision]:
    """Evaluate auto-close predicate for an intermediate (non-terminal) gate.

    Returns (True, decision) when predicate fires and the auto path was taken.
    Returns (False, decision) when predicate refuses; caller falls through to
    the existing close-intermediate dispatch unchanged.
    Caller is responsible for dispatching plan_next_wu afterward (AC4).
    Does NOT set verdict: met — close-intermediate has no terminal verdict.

    Idempotent: a second call after the WU has already been auto-closed on
    disk (status=done AND auto_close=true) short-circuits with
    (False, decision_with_auto=False) and emits NO `auto_close_decision`
    event. Prevents the double-fire observed in #23 where the dispatch
    loop re-entered with a stale in-memory wu.status and called this
    helper again, appending a duplicate event + producing a duplicate
    bookkeeping commit.
    """
    if close_intermediate_wu is not None and _already_auto_closed(close_intermediate_wu.file):
        return False, AutoCloseDecision(
            auto=False,
            reasons=["already_auto_closed"],
            metrics={},
            gate_id=gate.number,
            feature_id=feature_id,
            predicate_version="v1",
        )
    decision = evaluate_auto_close(feature_dir, gate.number)
    if not decision.auto:
        return False, decision
    append_stub_retrospective_intermediate(feature_dir, gate.number, decision)
    if close_intermediate_wu is not None:
        write_frontmatter_field(close_intermediate_wu.file, "status", "done")
        write_frontmatter_field(close_intermediate_wu.file, "auto_close", "true")
        write_frontmatter_field(close_intermediate_wu.file, "auto_close_reasons", "[]")
    flush_events(events_path, [build_event(
        "auto_close_decision", feature_id, {
            "gate": gate.number,
            "gate_type": "intermediate",
            "auto": True,
            "reasons": decision.reasons,
            "plan_next_dispatched": True,
            "predicate_version": decision.predicate_version,
        },
    )])
    return True, decision


def _fire_and_verify_terminal_flips(
    close_wu: "WorkUnit",
    feature_dir: Path,
    events_path: Path,
    feature_id: str,
) -> int:
    """Fire terminal state flips and run the post-pass invariant guard.

    Returns 0 on success, 1 when the guard fires. Called from both the
    auto-close path and the normal close-WU path; factored here to avoid
    duplicating the fire+verify block across both branches (FEAT-2026-0018/T04).
    """
    flip_paths = fire_terminal_flips(close_wu, feature_dir, REPO_ROOT)
    if flip_paths:
        commit_bookkeeping(
            flip_paths,
            f"chore(loop): {close_wu.wu_id} terminal flips"
            f"\n\nFeature: {feature_id}",
        )
    head_post = git("rev-parse", "HEAD")
    ok, reason = verify_post_pass_invariants(close_wu, feature_dir, REPO_ROOT, head_post)
    if not ok:
        flush_events(events_path, [build_event(
            "human_escalation", close_wu.wu_id, {
                "reason": "post_pass_invariant_failed",
                "assertion": reason.split(":", 1)[0].strip(),
                "summary": reason,
            })])
        commit_bookkeeping(
            [events_path],
            f"chore(loop): {close_wu.wu_id} "
            f"post_pass_invariant_failed\n\nFeature: {feature_id}",
        )
        print(f"\n   POST-PASS INVARIANT FAILED — {reason}")
        print(
            "Close WU passed with verdict=met but a terminal flip did "
            "not materialize. This is the FEAT-2026-0015/T06 "
            "wiring-race regression surface. Inspect events.jsonl "
            "and the fire_terminal_flips wiring."
        )
        return 1
    return 0


# --------------------------------------------------------------------------- #
# Closing-ceremony deliverable guards (FEAT-2026-0015/T07)                   #
# --------------------------------------------------------------------------- #


def _gate_number_from_wu_id(wu_id: str) -> int | None:
    """Parse gate number from a closing WU ID like FEAT-2026-0015/G1-PLAN."""
    segment = wu_id.rsplit("/", 1)[-1]
    m = re.match(r"G(\d+)-", segment)
    return int(m.group(1)) if m else None


def assert_retrospective_exists(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(close-a) RETROSPECTIVE.md exists and is non-empty in the feature dir."""
    retro = feature_dir / "RETROSPECTIVE.md"
    if not retro.exists() or not retro.read_text().strip():
        return (
            False,
            "assert_retrospective_exists: RETROSPECTIVE.md absent or empty in feature dir",
        )
    return True, ""


def assert_learnings_appended_or_noop(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(close-b) LEARNINGS.md has ≥1 added line in this squash, or RETRO says 'nothing generalizes'."""
    proc = subprocess.run(
        ["git", "diff", head_before, "HEAD", "--", ".specfuse/LEARNINGS.md"],
        capture_output=True, text=True,
    )
    added = any(
        ln.startswith("+") and not ln.startswith("+++")
        for ln in proc.stdout.splitlines()
    )
    if added:
        return True, ""
    retro = feature_dir / "RETROSPECTIVE.md"
    if retro.exists() and "nothing generalizes" in retro.read_text().lower():
        return True, ""
    return (
        False,
        "assert_learnings_appended_or_noop: no LEARNINGS.md additions in squash "
        "and no 'nothing generalizes' note in RETROSPECTIVE.md",
    )


def assert_doc_or_roadmap_diff(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(close-c) A documentation deliverable appears in the squash diff.

    Accepts: docs/*, .specfuse/roadmap.md, .specfuse/LEARNINGS.md, or any
    file named RETROSPECTIVE.md (under a feature dir). The roadmap.md case
    survives only for close-intermediate WUs that legitimately edit it;
    terminal close WUs do NOT touch roadmap.md (FEAT-2026-0015/T06
    consolidated that driver-side) — they deliver RETROSPECTIVE.md and
    LEARNINGS.md instead.
    """
    proc = subprocess.run(
        ["git", "diff", "--name-only", head_before, "HEAD"],
        capture_output=True, text=True,
    )
    for path in proc.stdout.splitlines():
        if path == ".specfuse/roadmap.md" or path.startswith("docs/"):
            return True, ""
        if path == ".specfuse/LEARNINGS.md":
            return True, ""
        if path.endswith("/RETROSPECTIVE.md") or path == "RETROSPECTIVE.md":
            return True, ""
    # For close-intermediate: skip when the WU spec declares no doc surface.
    if wu.type == "close-intermediate":
        if "docs/" not in wu.body and "roadmap.md" not in wu.body:
            return True, ""
    return (
        False,
        "assert_doc_or_roadmap_diff: no docs/, .specfuse/roadmap.md, "
        ".specfuse/LEARNINGS.md, or RETROSPECTIVE.md file in squash diff",
    )


def assert_verdict_well_formed(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(close-d) verdict frontmatter field is present and in VERDICT_VALUES.

    Re-reads frontmatter from disk: the agent writes `verdict:` DURING
    dispatch, but `wu.verdict` was populated by `load_wu` BEFORE dispatch.
    Without the re-read, the agent's verdict write is invisible and the
    assertion spins to MAX_ATTEMPTS, rolling back all artifacts on each
    attempt (issue #12). Mirrors the re-read at the terminal-flip path
    (FEAT-2026-0015/G2-CLOSE). Updates wu.verdict in-memory so downstream
    checks see the post-squash value.
    """
    fm, _ = read_frontmatter(wu.file)
    verdict = fm.get("verdict")
    if verdict is None or verdict not in VERDICT_VALUES:
        return (
            False,
            f"assert_verdict_well_formed: verdict {verdict!r} absent or not in "
            f"VERDICT_VALUES ({sorted(VERDICT_VALUES)})",
        )
    wu.verdict = verdict
    return True, ""


def assert_cost_analysis_section_when_met(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(close-e) When verdict=='met', RETROSPECTIVE.md must have a '## Cost analysis' header.

    Re-reads frontmatter (same reasoning as `assert_verdict_well_formed`):
    the agent writes `verdict:` during dispatch and `wu.verdict` from
    `load_wu` is stale. Independent re-read keeps this assertion robust
    even if invoked outside the canonical close-d → close-e ordering.
    """
    fm, _ = read_frontmatter(wu.file)
    verdict = fm.get("verdict")
    if verdict != "met":
        return True, ""
    retro = feature_dir / "RETROSPECTIVE.md"
    if retro.exists():
        if re.search(r"^##+ Cost analysis", retro.read_text(), re.MULTILINE | re.IGNORECASE):
            return True, ""
    return (
        False,
        "assert_cost_analysis_section_when_met: verdict=met but '## Cost analysis' "
        "section absent from RETROSPECTIVE.md",
    )


_NO_FAILURES_SENTINEL = "### Failure-class breakdown\n\n(no non-passing attempts in scope)\n"


def summarize_attempt_failure_classes(
    feature_dir: Path,
    gate_n: int | None = None,
    exclude_correlation_id: str | None = None,
) -> str:
    """Render a '### Failure-class breakdown' markdown table from events.jsonl.

    Reads attempt_outcome events whose outcome != 'passed'.  When gate_n is
    provided, restricts to events whose correlation_id belongs to that gate
    (resolved via _gate_number_from_wu_id).  When exclude_correlation_id is
    provided, drops events with that exact correlation_id — used to keep a
    close WU's OWN non-passing attempts out of the breakdown it authors, so the
    close's stumble does not arm the guard against itself (issue #145).  Returns
    _NO_FAILURES_SENTINEL when no non-passing attempts match the filter.

    Pure function — reads events.jsonl; no writes, no side effects.
    Malformed JSONL lines are skipped (legacy-event tolerance, AC5).
    """
    events_path = feature_dir / "events.jsonl"
    if not events_path.exists():
        return _NO_FAILURES_SENTINEL

    non_passing: list[dict] = []
    for raw in events_path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            evt = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if evt.get("event_type") != "attempt_outcome":
            continue
        payload = evt.get("payload") or {}
        if payload.get("outcome") == "passed":
            continue
        cid = evt.get("correlation_id", "")
        if exclude_correlation_id is not None and cid == exclude_correlation_id:
            continue
        if gate_n is not None:
            if _gate_number_from_wu_id(cid) != gate_n:
                continue
        non_passing.append(payload)

    if not non_passing:
        return _NO_FAILURES_SENTINEL

    # Group by failure_class; collect signatures for dominant-sig resolution.
    class_counts: dict[str, int] = {}
    class_signatures: dict[str, list[str]] = {}
    for p in non_passing:
        fc = str(p.get("failure_class") or "null")
        sig = str(p.get("failure_signature") or "")
        class_counts[fc] = class_counts.get(fc, 0) + 1
        class_signatures.setdefault(fc, []).append(sig)

    def _dominant(sigs: list[str]) -> str:
        freq: dict[str, int] = {}
        for s in sigs:
            freq[s] = freq.get(s, 0) + 1
        return max(freq, key=lambda k: (freq[k], -sigs.index(k)))

    # Sort: count descending, class ascending for ties.
    rows = sorted(
        class_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )

    lines = [
        "### Failure-class breakdown",
        "",
        "| failure_class | non-passed attempts | dominant signature |",
        "|---------------|---------------------|--------------------|",
    ]
    total = 0
    for fc, count in rows:
        dom = _dominant(class_signatures[fc])
        lines.append(f"| {fc} | {count} | {dom} |")
        total += count
    lines.append(f"| **total** | **{total}** | — |")
    lines.append("")
    return "\n".join(lines)


def assert_failure_class_breakdown_when_failures_present(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(close-f / close-intermediate-d) RETROSPECTIVE.md has '### Failure-class breakdown'
    when non-passing attempt_outcome events exist for the gate.

    Returns (True, "") when:
    - RETROSPECTIVE.md is absent (assert_retrospective_exists fires first for 'close';
      assert_retrospective_gate_section fires first for 'close-intermediate').
    - No non-passing attempts exist in events.jsonl for the gate.
    - The heading is present.

    Returns (False, reason) when non-passing attempts exist but the heading is absent.
    """
    retro = feature_dir / "RETROSPECTIVE.md"
    if not retro.exists():
        return True, ""

    gate_n = _gate_number_from_wu_id(wu.wu_id)
    # Exclude the close WU's OWN non-passing attempts: the breakdown documents
    # SUBSTANTIVE-WU failures, not the close's own stumble. Without this, a
    # failed first close attempt retroactively requires a new subsection in the
    # RETROSPECTIVE the close itself authors — and the between-attempt
    # `reset --hard` wipes the partial each retry → spin → blocked_human on
    # otherwise-done features (issue #145).
    summary = summarize_attempt_failure_classes(
        feature_dir, gate_n, exclude_correlation_id=wu.wu_id)

    if summary == _NO_FAILURES_SENTINEL:
        return True, ""

    if re.search(r"^#{3} Failure-class breakdown\b", retro.read_text(), re.MULTILINE):
        return True, ""

    # Count non-passing attempts (excluding the close's own) for the message.
    events_path = feature_dir / "events.jsonl"
    count = 0
    if events_path.exists():
        for raw in events_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                evt = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if evt.get("event_type") != "attempt_outcome":
                continue
            payload = evt.get("payload") or {}
            if payload.get("outcome") == "passed":
                continue
            cid = evt.get("correlation_id", "")
            if cid == wu.wu_id:
                continue
            if gate_n is not None:
                if _gate_number_from_wu_id(cid) != gate_n:
                    continue
            count += 1

    gate_label = f"gate {gate_n}" if gate_n is not None else "all gates"
    # Actionable, self-contained retry note (flows into the next attempt's prompt
    # via failure_note, issue #145 fix #2): name the moved bar AND embed the exact
    # table to paste, so the agent doesn't rediscover the requirement.
    return (
        False,
        f"assert_failure_class_breakdown_when_failures_present: {count} "
        f"substantive-WU attempt(s) in {gate_label} did not pass, so "
        f"RETROSPECTIVE.md MUST include a '### Failure-class breakdown' subsection "
        f"— it is absent. Add exactly this subsection to RETROSPECTIVE.md:\n\n"
        f"{summary}",
    )


def assert_retrospective_gate_section(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(close-intermediate-a) RETROSPECTIVE.md contains a '## Gate N' or '### Gate N' section."""
    gate_n = _gate_number_from_wu_id(wu.wu_id)
    if gate_n is None:
        return (
            False,
            "assert_retrospective_gate_section: cannot parse gate number from wu_id",
        )
    retro = feature_dir / "RETROSPECTIVE.md"
    if not retro.exists():
        return (
            False,
            "assert_retrospective_gate_section: RETROSPECTIVE.md absent in feature dir",
        )
    if re.search(rf"^#{{1,3}} Gate {gate_n}\b", retro.read_text(), re.MULTILINE):
        return True, ""
    return (
        False,
        f"assert_retrospective_gate_section: RETROSPECTIVE.md has no "
        f"'## Gate {gate_n}' or '### Gate {gate_n}' section",
    )


def assert_gate_review_exists(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(plan-next-a) GATE-(N+1)-REVIEW.md exists + non-empty, or no next gate (terminal)."""
    gate_n = _gate_number_from_wu_id(wu.wu_id)
    if gate_n is None:
        return (
            False,
            "assert_gate_review_exists: cannot parse gate number from wu_id",
        )
    # If no next gate is defined in PLAN.md the feature is terminal: no review expected.
    _, gates = load_graph(feature_dir)
    if not any(g.number == gate_n + 1 for g in gates):
        return True, ""
    next_gate = gate_n + 1
    review = feature_dir / f"GATE-{next_gate:02d}-REVIEW.md"
    if not review.exists() or not review.read_text().strip():
        return (
            False,
            f"assert_gate_review_exists: GATE-{next_gate:02d}-REVIEW.md absent or empty",
        )
    return True, ""


def assert_next_gate_drafted_or_terminal(
    wu: WorkUnit, feature_dir: Path, repo_root: Path, head_before: str,
) -> tuple[bool, str]:
    """(plan-next-b) Next gate has ≥1 drafted WU in PLAN.md, or PLAN.md/roadmap is terminal."""
    plan_path = feature_dir / "PLAN.md"
    plan_fm, _ = read_frontmatter(plan_path)
    if plan_fm.get("status") == "done":
        return True, ""
    feature_id = wu.wu_id.rsplit("/", 1)[0]
    roadmap_path = repo_root / ".specfuse" / "roadmap.md"
    if roadmap_path.exists():
        row_re = re.compile(
            r"^\|\s*" + re.escape(feature_id) + r"\s*\|([^|]*)\|([^|]*)\|",
            re.MULTILINE,
        )
        rm = row_re.search(roadmap_path.read_text())
        if rm and rm.group(2).strip() == "done":
            return True, ""
    gate_n = _gate_number_from_wu_id(wu.wu_id)
    if gate_n is None:
        return (
            False,
            "assert_next_gate_drafted_or_terminal: cannot parse gate number from wu_id",
        )
    _, gates = load_graph(feature_dir)
    next_gates = [g for g in gates if g.number == gate_n + 1]
    # No gate N+1 in PLAN.md → terminal (plan-next set PLAN.md done or feature is single-gate).
    if not next_gates:
        return True, ""
    if next_gates[0].refs:
        return True, ""
    return (
        False,
        f"assert_next_gate_drafted_or_terminal: gate {gate_n + 1} has no drafted "
        f"work_units in PLAN.md and neither PLAN.md nor roadmap marks done",
    )


CLOSING_ASSERTIONS_BY_TYPE: dict[str, list] = {
    "close": [
        assert_retrospective_exists,
        assert_learnings_appended_or_noop,
        assert_doc_or_roadmap_diff,
        assert_verdict_well_formed,
        assert_cost_analysis_section_when_met,
        assert_failure_class_breakdown_when_failures_present,
    ],
    "close-intermediate": [
        assert_retrospective_gate_section,
        assert_learnings_appended_or_noop,
        assert_doc_or_roadmap_diff,
        assert_failure_class_breakdown_when_failures_present,
    ],
    "plan-next": [
        assert_gate_review_exists,
        assert_next_gate_drafted_or_terminal,
    ],
}


def assert_closing_deliverables(
    wu: WorkUnit,
    feature_dir: Path,
    repo_root: Path,
    head_before: str,
) -> tuple[bool, str]:
    """Fire the type-keyed closing deliverable guard (FEAT-2026-0015/T07).

    Returns (True, "") if the WU type has no assertions (implementation type —
    other guards handle it) or all assertions pass.  On the first failure returns
    (False, reason) where reason names the failing assertion function.

    No "diff is empty" bypass: a close-type WU whose squash contains only the
    driver's own WU-file bookkeeping is a hollow pass and MUST fail one of the
    typed assertions (assert_retrospective_exists fires first for ``close``).
    The earlier bypass introduced for test-fixture convenience also silently
    passed real hollow-pass close ceremonies (FEAT-2026-0017/G1-CLOSE attempt-3
    surface).
    """
    assertions = CLOSING_ASSERTIONS_BY_TYPE.get(wu.type, [])
    if not assertions:
        return True, ""
    # Aggregate, don't short-circuit (#72). Each assertion fails independently;
    # returning only the first one forced the agent to discover the requirement
    # set one rejection at a time. With MAX_ATTEMPTS=3 a close missing >=2
    # sections spins to a block (and can oscillate — fix A, drop B, regress A).
    # Run every assertion each attempt and return the complete unmet list so a
    # single attempt can satisfy them all and a re-fix re-checks everything.
    failures = []
    for fn in assertions:
        ok, reason = fn(wu, feature_dir, repo_root, head_before)
        if not ok:
            failures.append(reason)
    if not failures:
        return True, ""
    if len(failures) == 1:
        return False, failures[0]
    bullets = "\n".join(f"  - {r}" for r in failures)
    return False, (
        f"{len(failures)} closing deliverables unmet (fix all in one attempt):"
        f"\n{bullets}"
    )


def assert_implementation_touched_files(
    wu: WorkUnit,
    touched: list[str],
) -> tuple[bool, str]:
    """Empty-files escalation for implementation WUs (FEAT-2026-0022/T03).

    A hard, ``produces:``-independent gate on the ``files_touched`` signal
    every WU already produces. Returns ``(True, "")`` when ``wu.type`` is not
    ``implementation`` (close/plan-next/etc. produce reflective artifacts
    gated by ``assert_closing_deliverables``), or when ``touched`` — after
    removing the WU's own file and any ``events.jsonl`` entry — still names a
    file. Otherwise returns ``(False, summary)``: an ``implementation`` WU that
    produced no deliverable file diff cannot be ``done``.

    This closes the zero-deliverable hollow pass from the other side of
    ``verify_files_changed`` (which opts out when the agent claims nothing):
    regardless of what the agent claimed, the squash diff must name a real
    deliverable. ``touched`` MUST be derived from the post-squash ``sha`` so the
    WU's own status flip is present — the filter strips it; without that strip
    the guard never fires and is a silent no-op (escalation trigger 2).
    """
    if wu.type != "implementation":
        return True, ""
    wu_name = wu.file.name
    deliverables = [
        t for t in touched
        if Path(t).name not in (wu_name, "events.jsonl")
    ]
    if deliverables:
        return True, ""
    return (
        False,
        f"implementation WU {wu.wu_id} produced no deliverable files: the "
        f"squash diff names only its own WU file and/or events.jsonl",
    )


def assert_declared_deliverables(wu: WorkUnit) -> tuple[bool, str]:
    """Deliverable-presence gate (FEAT-2026-0022/T02).

    Verify every path the WU declared in ``produces:`` exists on disk and is
    non-empty (``test -s`` semantics: ``Path(p).exists()`` and
    ``Path(p).stat().st_size > 0``). Returns ``(True, "")`` when ``wu.produces``
    is empty — the opt-out: an undeclared ``produces:`` means no gate, exactly
    as ``verify_files_changed``'s absence opt-out (loop.py:994) — or when every
    declared path exists and is non-empty. On the first offending path returns
    ``(False, summary)`` naming that path and whether it was absent or empty.

    A path that exists but is zero-length is treated as missing: an empty
    deliverable is a hollow deliverable. This catches the partial-bundle hollow
    pass (FEAT-2026-0020/T12: SECURITY.md present, bundled CODE_OF_CONDUCT.md
    absent). The check is file-level only; symbol-level checks are out of scope
    (PLAN Scope OUT).
    """
    if not wu.produces:
        return True, ""
    for raw in wu.produces:
        path = str(raw)
        p = Path(path)
        if not p.exists():
            return False, f"declared deliverable absent: {path}"
        if p.stat().st_size == 0:
            return False, f"declared deliverable empty: {path}"
    return True, ""


# --------------------------------------------------------------------------- #
# Post-pass driver-state invariants (FEAT-2026-0017/T01)                      #
# --------------------------------------------------------------------------- #


def assert_terminal_flips_fired(
    wu: WorkUnit,
    feature_dir: Path,
    repo_root: Path,
    head_before: str,
) -> tuple[bool, str]:
    """Post-pass invariant: when a close WU writes verdict=met, the terminal
    state-flips must have materialized.

    Checks (in order):
      - WU frontmatter verdict (re-read from disk); skip if not "met"
      - Terminal gate file's `status: passed`
      - Roadmap row Status column == `done`
      - Roadmap-archive anchor `<a id="<feat_lc>"></a>` present

    head_before is accepted to mirror the assertion-function signature shape;
    this check is pure file-state and does not need it.
    """
    fm, _ = read_frontmatter(wu.file)
    verdict = fm.get("verdict") or None
    if verdict != "met":
        return True, ""

    feature_id = wu.wu_id.rsplit("/", 1)[0]

    _, gates = load_graph(feature_dir)
    if not gates:
        return False, "terminal_gate_not_passed: PLAN.md has no gates"
    terminal_gate = gates[-1]
    gate_path = terminal_gate.file
    if not gate_path.exists():
        return (
            False,
            f"terminal_gate_not_passed: {gate_path.name} absent",
        )
    gate_fm, _ = read_frontmatter(gate_path)
    gate_status = gate_fm.get("status", "")
    if gate_status != "passed":
        return (
            False,
            f"terminal_gate_not_passed: {gate_path.name} status={gate_status!r}",
        )

    roadmap_path = repo_root / ".specfuse" / "roadmap.md"
    if not roadmap_path.exists():
        return (
            False,
            f"roadmap_row_not_done: roadmap.md absent at {roadmap_path}",
        )
    parsed = _parse_roadmap_row(roadmap_path.read_text(), feature_id)
    if not parsed:
        return (
            False,
            f"roadmap_row_not_done: row for {feature_id} not found in "
            f"{roadmap_path}. /draft-feature writes this row but leaves it "
            f"uncommitted; if it was dropped before dispatch, restore it and "
            f"re-commit. `specfuse-loop --prepare` folds the row into the "
            f"scaffold commit — dispatch through it so the row survives the "
            f"per-attempt reset.",
        )
    row_status = parsed["columns"].get("Status", "").strip()
    if row_status != "done":
        return False, f"roadmap_row_not_done: status={row_status!r}"

    archive_path = repo_root / ".specfuse" / "roadmap-archive.md"
    feat_id_lower = feature_id.lower()
    anchor = f'<a id="{feat_id_lower}"></a>'
    if not archive_path.exists():
        return (
            False,
            f"archive_anchor_missing: {feat_id_lower} (roadmap-archive.md absent)",
        )
    if anchor not in archive_path.read_text():
        return False, f"archive_anchor_missing: {feat_id_lower}"
    return True, ""


POST_PASS_INVARIANTS_BY_TYPE: dict[str, list] = {
    "close": [assert_terminal_flips_fired],
}


def verify_post_pass_invariants(
    wu: WorkUnit,
    feature_dir: Path,
    repo_root: Path,
    head_before: str,
) -> tuple[bool, str]:
    """Dispatch the type-keyed post-pass invariant guard (FEAT-2026-0017/T01).

    Returns (True, "") when the WU type has no invariants or all pass. On the
    first failure returns (False, reason).

    Distinct from `assert_closing_deliverables`: that guard fires immediately
    after squash and checks the WU's own ceremony deliverables (retrospective,
    learnings, etc.). This guard fires after the gate-boundary
    `fire_terminal_flips` invocation and checks that driver-side state
    transitions actually materialized — independent of the agent's RESULT.

    Defends against the FEAT-2026-0015/T06 wiring-race surface: a close WU
    passed cleanly with `verdict: met` but `fire_terminal_flips` was never
    invoked because the in-memory `wu.verdict` snapshot (loaded BEFORE
    dispatch by `load_wu`) shadowed the agent's just-written frontmatter
    value. The re-read fix landed in PR #11 (commit 7f403bf); this guard is
    the canary against re-introducing that or any equivalent close-path race.
    """
    invariants = POST_PASS_INVARIANTS_BY_TYPE.get(wu.type, [])
    if not invariants:
        return True, ""
    for fn in invariants:
        ok, reason = fn(wu, feature_dir, repo_root, head_before)
        if not ok:
            return False, reason
    return True, ""


# --------------------------------------------------------------------------- #
# The loop                                                                    #
# --------------------------------------------------------------------------- #


def ready(units: list[WorkUnit], done_ids: set[str]) -> list[WorkUnit]:
    return [u for u in units
            if u.status in DISPATCHABLE and all(d in done_ids for d in u.depends_on)]


def run(
    feature_arg: str | None,
    dry_run: bool,
    force_full_close: str | None = None,
    prepare: bool = False,
    prepare_only: bool = False,
) -> int:
    # Fail-fast on a malformed verification.yml BEFORE we touch any WU state.
    # The per-gate `verify()` call lazy-loads the same file; if it's malformed,
    # the crash lands mid-WU with `status: in_progress` already on disk,
    # corrupting the recovery surface (see specfuse/loop#35). Validating once
    # here collapses that into "bad config, no work started."
    try:
        load_verification()
    except _miniyaml.MiniYAMLError as exc:
        print(
            f"loop.py: .specfuse/verification.yml is malformed — {exc}",
            file=sys.stderr,
        )
        print(
            "Fix the file and re-run. No WUs were touched.",
            file=sys.stderr,
        )
        return 1
    feature_dir = find_feature(feature_arg)
    feat_fm, gates = load_graph(feature_dir)
    feature_id = feat_fm.get("feature_id", feature_dir.name)
    if force_full_close is not None and force_full_close != feature_id:
        sys.exit(
            f"loop.py: --force-full-close {force_full_close} does not match "
            f"feature being processed {feature_id}"
        )
    _override_ns = argparse.Namespace(force_full_close=force_full_close)
    _override_active, _override_reason = resolve_auto_close_override(_override_ns, feature_dir)
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

    lock_fd = None
    if not dry_run:
        # dry-run performs no mutation; inspecting while a real run is active must stay allowed.
        try:
            lock_fd = acquire_tree_lock(SPECFUSE_DIR)
        except BlockingIOError:
            print(
                "another loop driver is already running in this working tree "
                "(.specfuse/.loop.lock held)",
                file=sys.stderr,
            )
            return 1
        require_git_ready()
        # --prepare / --prepare-only: create the feature branch + commit the
        # folder up front so the guards below pass (the do-it-for-me path
        # draft-feature can't take). --prepare-only stops after, so you can
        # review the commit before the loop dispatches anything.
        if prepare or prepare_only:
            # Genuinely-unrelated dirty paths (not the /pick-feature flips, not
            # auto_sync's scaffold overlay) still stop --prepare — but with a
            # clean, actionable message and a non-zero exit, not a traceback.
            try:
                prepare_feature(feat_fm, feature_dir, feature_id)
            except FeatureBranchError as exc:
                print(f"--prepare cannot proceed:\n{exc}", file=sys.stderr)
                return 1
        if prepare_only:
            print("Prepared: feature is on its branch and committed. "
                  "Re-run `specfuse-loop` to start the gate.")
            return 0
        # Pre-flight guards — both run BEFORE ensure_feature_branch so the
        # refusal happens before any branch mutation, and both protect against
        # the per-attempt `git reset --hard` destroying uncommitted state:
        #   #71 — an untracked feature folder would be swept into a squash then
        #         deleted by the reset (and crash the next frontmatter write).
        #   #74 — uncommitted arm-gate / WU-revision edits (armed statuses, AC
        #         revisions) would be silently discarded by the reset.
        require_feature_folder_committed(feature_dir, feat_fm, feature_id)
        require_feature_folder_unmodified(feature_dir, feat_fm, feature_id)
        ensure_feature_branch(feat_fm, feature_dir)

    try:

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

        # Done-set must include WUs from every PREVIOUS gate that are already done —
        # cross-gate `depends_on` references are valid (e.g. gate 2's implementation
        # WU may depend on gate 1's). Without this, the ready() filter sees the
        # cross-gate dep as unmet and silently no-ops the gate (then set_gate
        # awaiting_review fires on an empty run, leaving real WUs un-dispatched).
        done_ids: set[str] = set()
        for g in gates:
            if g.number > gate.number:
                continue
            for ref in g.refs:
                wu_path = feature_dir / ref["file"]
                if not wu_path.is_file():
                    continue
                wfm, _ = read_frontmatter(wu_path)
                if wfm.get("status") == DONE:
                    done_ids.add(ref["id"])
        blocked = False
        close_wu_for_terminal: WorkUnit | None = None
        _terminal_auto_closed_wu: WorkUnit | None = None  # FEAT-2026-0018/T11H

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

                print(f"\n[{time.strftime('%H:%M:%S')}] -- {wu.wu_id} "
                      f"[{wu.type}] model={wu.model} effort={wu.effort}")
                # Summary line: the WU's title, so the log says WHAT is being
                # worked, not just its id. Skipped when title just echoes the id
                # (the parse default when a WU has no `# Title` heading).
                if wu.title and wu.title != wu.wu_id:
                    print(f"   ↳ {wu.title}")
                if dry_run:
                    print("   (dry run — would dispatch)")
                    wu.status = DONE
                    done_ids.add(wu.wu_id)
                    continue

                # FEAT-2026-0018/T05 — intermediate auto-close branch
                if wu.type == "close-intermediate" and not _override_active:
                    _plan_next_wu = next(
                        (w for w in units if w.type == "plan-next"),
                        None,
                    )
                    _auto_closed, _ = maybe_auto_close_intermediate(
                        feature_dir, feature_id, gate, gates,
                        events_path, REPO_ROOT, wu, _plan_next_wu,
                    )
                    if _auto_closed:
                        commit_bookkeeping(
                            [feature_dir / "RETROSPECTIVE.md",
                             wu.file, events_path],
                            f"chore(loop): {wu.wu_id} auto-closed "
                            f"(predicate=v1)\n\nFeature: {feature_id}",
                        )
                        # Mirror the on-disk status flip into the in-memory
                        # WorkUnit so ready()'s u.status in DISPATCHABLE filter
                        # excludes it on the next while-loop pass — without
                        # this, the same WU re-appears in pending, the helper
                        # is called a second time, and (absent its idempotency
                        # guard) a duplicate auto_close_decision event +
                        # duplicate bookkeeping commit are produced (issue #23).
                        wu.status = DONE
                        done_ids.add(wu.wu_id)
                        continue
                elif wu.type == "close-intermediate" and _override_active:
                    flush_events(events_path, [build_event(
                        "auto_close_decision", wu.wu_id, {
                            "gate": gate.number,
                            "gate_type": "intermediate",
                            "auto": False,
                            "reasons": [_override_reason],
                            "predicate_version": "v1",
                            "override": True,
                        }
                    )])

                # FEAT-2026-0018/T11H — terminal auto-close branch (relocated from post-loop)
                # Guard wu.verdict is None: only attempt auto-close for WUs that have
                # not yet been dispatched (no verdict written). WUs with a pre-existing
                # verdict (e.g. met_locally from a prior attempt) fall through to
                # normal dispatch so their verdict semantics are honoured.
                if (wu.type == "close" and gate is gates[-1]
                        and not _override_active and wu.verdict is None):
                    _auto_closed, _decision = maybe_auto_close_terminal(
                        feature_dir, feature_id, gate, gates,
                        events_path, wu, repo_root=REPO_ROOT,
                    )
                    if _auto_closed:
                        commit_bookkeeping(
                            [feature_dir / "RETROSPECTIVE.md",
                             wu.file, events_path],
                            f"chore(loop): {wu.wu_id} auto-closed "
                            f"(predicate=v1)\n\nFeature: {feature_id}",
                        )
                        # Terminal flips fire in post-loop after set_gate(awaiting_review)
                        _terminal_auto_closed_wu = wu
                        # See intermediate branch above: mirror disk → memory
                        # so ready() filters this WU on the next pass (issue #23).
                        wu.status = DONE
                        done_ids.add(wu.wu_id)
                        continue
                elif (wu.type == "close" and gate is gates[-1]
                        and _override_active and wu.verdict is None):
                    flush_events(events_path, [build_event(
                        "auto_close_decision", wu.wu_id, {
                            "gate": gate.number,
                            "auto": False,
                            "reasons": [_override_reason],
                            "predicate_version": "v1",
                            "override": True,
                        }
                    )])
                    # Fall through to existing close-WU dispatch path

                head_before = git("rev-parse", "HEAD")
                # Snapshot the operator's untracked files alongside head_before:
                # squash_commit must not absorb WIP that pre-dates this dispatch
                # (#150). Captured here, not inside squash_commit, because by
                # then the agent's own new files are indistinguishable from it.
                untracked_before = untracked_paths()
                _is_rearm = detect_rearm_dispatch(wu)
                if _is_rearm:
                    fold_cumulative_on_rearm(wu, backend)
                backend.set_wu(wu, "status", "in_progress")
                # Stamp the resolved execution metadata into the WU frontmatter so
                # it is visible when you read the .md (not only on the console /
                # in events.jsonl): the model + effort it runs with (override or
                # type default), which verification gate set is its exit oracle,
                # the driver version that executed it, and when it was dispatched.
                # Written after head_before so they ride the WU's squash commit;
                # idempotent on retries/re-arms (same values overwrite cleanly,
                # started_at refreshes to the latest dispatch).
                backend.set_wu(wu, "model", wu.model)
                backend.set_wu(wu, "effort", wu.effort)
                backend.set_wu(wu, "gate_set", GATES_FOR_TYPE.get(wu.type, "code"))
                backend.set_wu(wu, "driver_version", DRIVER_VERSION)
                backend.set_wu(wu, "started_at",
                               dt.datetime.now(dt.timezone.utc).isoformat())
                # Events and per-attempt notes are buffered in memory during the
                # WU's lifecycle and flushed at outcome time. This prevents the
                # `git reset --hard` between failed attempts from silently
                # wiping appended events / status flips — anything that should
                # be durable is either committed in the squash (PASS) or in a
                # bookkeeping commit (BLOCKED/SPINNING).
                _wu_fm_rearm, _ = read_frontmatter(wu.file)
                re_arm_count = int(_wu_fm_rearm.get("re_arm_count") or 0)
                wu_events = [build_event("task_started", wu.wu_id,
                                         {"type": wu.type, "model": wu.model,
                                          "re_arm_count": re_arm_count})]
                if _is_rearm:
                    _rearm_history = _wu_fm_rearm.get("re_arm_history") or []
                    _rearm_reason = ""
                    if isinstance(_rearm_history, list) and _rearm_history:
                        _last_entry = _rearm_history[-1]
                        if isinstance(_last_entry, dict):
                            _rearm_reason = str(_last_entry.get("reason", ""))
                    wu_events.append(build_event("re_arm_dispatched", wu.wu_id, {
                        "re_arm_count": re_arm_count,
                        "reason": _rearm_reason,
                    }))
                if wu.unsandboxed:
                    # Audit signal: WU opted out of the claude -p sandbox.
                    # Event logged before first attempt so the trail exists
                    # even if the attempt crashes. Rationale carried verbatim.
                    wu_events.append(build_event("unsandboxed_dispatch", wu.wu_id, {
                        "rationale": wu.unsandboxed_rationale,
                    }))
                    print(f"   ⚠ UNSANDBOXED dispatch — rationale: "
                          f"{wu.unsandboxed_rationale}")
                attempt_notes: list[tuple[int, str]] = []
                attempt_outcomes: list[str] = []
                # Cost accumulators: per-attempt list goes to events.jsonl,
                # cumulative sum to WU frontmatter at outcome time.
                attempts_usage: list[dict] = []
                cum_usage = {"cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0,
                             "duration_seconds": 0.0}

                failure_note = None
                prior_failure_signature: tuple[str | None, str | None] | None = None
                for attempt in range(1, MAX_ATTEMPTS + 1):
                    backend.set_wu(wu, "attempts", attempt)
                    print(f"   [{time.strftime('%H:%M:%S')}] attempt "
                          f"{attempt}/{MAX_ATTEMPTS} model={wu.model} "
                          f"effort={wu.effort} — fresh session")
                    if attempt > 1 and failure_note:
                        reason = failure_note.strip().splitlines()[0][:200]
                        print(f"   retry reason: {reason}")
                    t0 = time.monotonic()
                    outcome, payload, usage = execute_unit_attempt(
                        wu, feature_dir, failure_note, cost_tracking=cost_tracking,
                        head_before=head_before,
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
                    attempt_outcomes.append(outcome)

                    if outcome == "zero_token":
                        # Agent never produced output (input_tokens=0). Skip
                        # RESULT parsing, buffer an event, reset the tree, and
                        # treat as a failed attempt for the purposes of the
                        # attempt loop — counter already incremented at top.
                        wu_events.append(emit_attempt_outcome(
                            wu, attempt, "zero_token_skip",
                            attempts_usage[-1],
                        ))
                        reset_preserving_events(head_before, events_path)
                        print(f"   ZERO-TOKEN attempt {attempt}/{MAX_ATTEMPTS} "
                              f"— no agent output, skipping")
                        continue

                    if outcome == "blocked":
                        # Reset agent work first; THEN write our bookkeeping; THEN
                        # commit it. Doing the flip before the reset would let the
                        # reset wipe the flip — the silent-state-loss bug.
                        # Use reset_preserving_events to keep prior WU's
                        # flushed-but-uncommitted events.jsonl entries.
                        reset_preserving_events(head_before, events_path)
                        backend.set_wu(wu, "status", "blocked_human")
                        write_cost_to_wu(backend, wu, cum_usage)
                        wu_events.append(emit_attempt_outcome(
                            wu, attempt, "blocked",
                            attempts_usage[-1],
                            files_touched=git_diff_names(head_before, "HEAD"),
                            agent_status="blocked",
                            agent_blocked_reason=payload,
                        ))
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
                        # reset.
                        backend.set_wu(wu, "status", DONE)
                        write_cost_to_wu(backend, wu, cum_usage)
                        try:
                            sha = squash_commit(wu, head_before,
                                                untracked_before=untracked_before)
                        except SquashCommitError as exc:
                            # The squash commit was rejected (typically a
                            # pre-commit hook). Treat as a failed attempt rather
                            # than crashing the driver (issue #51): reset the
                            # tree — which also discards the premature DONE flip
                            # written just above — record the failure with git's
                            # stderr, and retry within budget (MAX_ATTEMPTS
                            # exhaustion escalates to blocked_human).
                            reset_preserving_events(head_before, events_path)
                            # Redact any quoted leak-scan match before it lands
                            # in events.jsonl / the attempt note, so the captured
                            # FINDINGS text can't re-trip the next bookkeeping
                            # commit (#76 — the systemic self-poison).
                            summary = redact_leak_findings(str(exc))
                            wu_events.append(emit_attempt_outcome(
                                wu, attempt, "squash_commit_failed",
                                attempts_usage[-1],
                                extras={"summary": summary},
                            ))
                            attempt_notes.append((attempt, summary))
                            failure_note = summary
                            print(f"   SQUASH COMMIT REJECTED attempt "
                                  f"{attempt}/{MAX_ATTEMPTS}")
                            continue
                        # Smoke-import runner (FEAT-2026-0008/T03): after a
                        # successful verify() AND squash, run each
                        # `python3 -c "from X import Y"` line declared in the WU
                        # body. A non-zero exit fails the attempt — the squash
                        # is rolled back via `git reset --hard head_before` so
                        # the verify-passing-but-smoke-failing tree does not
                        # remain in history. Rollback FIRST (before event log
                        # and before the next attempt iterates) per WU
                        # escalation trigger 3.
                        smoke_cmds = extract_smoke_imports(wu.body)
                        if smoke_cmds:
                            smoke_ok, smoke_summary = run_smoke_imports(
                                smoke_cmds, Path("."),
                            )
                            if not smoke_ok:
                                reset_preserving_events(head_before, events_path)
                                wu_events.append(emit_attempt_outcome(
                                    wu, attempt, "smoke_import_failed",
                                    attempts_usage[-1],
                                    extras={"summary": smoke_summary},
                                ))
                                attempt_notes.append((attempt, smoke_summary))
                                failure_note = smoke_summary
                                print(f"   SMOKE FAIL attempt "
                                      f"{attempt}/{MAX_ATTEMPTS}")
                                continue
                        # Closing deliverable guard (FEAT-2026-0015/T07):
                        # fires after smoke, before terminal-flip bookkeeping.
                        closing_ok, closing_summary = assert_closing_deliverables(
                            wu, feature_dir, REPO_ROOT, head_before,
                        )
                        if not closing_ok:
                            reset_preserving_events(head_before, events_path)
                            # `assertion` names the primary (first) failing
                            # assertion. With aggregation (#72) closing_summary
                            # may list several; the first `assert_*` token is the
                            # primary one and keeps the event field queryable.
                            _assert_m = re.search(r"assert_\w+", closing_summary)
                            wu_events.append(emit_attempt_outcome(
                                wu, attempt, "closing_deliverable_missing",
                                attempts_usage[-1],
                                extras={
                                    "assertion": (
                                        _assert_m.group(0) if _assert_m
                                        else closing_summary.split(":", 1)[0].strip()
                                    ),
                                    "summary": closing_summary,
                                },
                            ))
                            attempt_notes.append((attempt, closing_summary))
                            failure_note = closing_summary
                            print(
                                f"   CLOSING DELIVERABLE MISSING attempt "
                                f"{attempt}/{MAX_ATTEMPTS} — {closing_summary}"
                            )
                            continue
                        # Deliverable-presence gate (FEAT-2026-0022/T02):
                        # fires after smoke and closing-deliverable guards,
                        # before the empty-files catch-all so the named-path
                        # diagnostic wins. Every path the WU declared in
                        # `produces:` must exist on disk and be non-empty; an
                        # absent or zero-length declared deliverable refuses the
                        # pass (the partial-bundle hollow pass,
                        # FEAT-2026-0020/T12). Opt-out: a WU with empty
                        # `produces:` never fires this — existing behavior for
                        # every current WU is unchanged.
                        deliv_ok, deliv_summary = assert_declared_deliverables(wu)
                        if not deliv_ok:
                            reset_preserving_events(head_before, events_path)
                            missing = deliv_summary.split(": ", 1)[-1]
                            wu_events.append(emit_attempt_outcome(
                                wu, attempt, "deliverable_missing",
                                attempts_usage[-1],
                                extras={"summary": deliv_summary,
                                        "missing": missing},
                            ))
                            attempt_notes.append((attempt, deliv_summary))
                            failure_note = deliv_summary
                            print(
                                f"   DELIVERABLE MISSING attempt "
                                f"{attempt}/{MAX_ATTEMPTS} — {deliv_summary}"
                            )
                            continue
                        # Empty-files escalation (FEAT-2026-0022/T03): compute
                        # the post-squash touched-paths list ONCE here and reuse
                        # it for the passed event below. An implementation WU
                        # whose squash names only its own WU file + events.jsonl
                        # produced no deliverable — refuse the pass, MAX_ATTEMPTS
                        # exhaustion escalates via existing machinery.
                        touched = git_diff_names(head_before, sha) if sha else []
                        impl_ok, impl_summary = assert_implementation_touched_files(
                            wu, touched,
                        )
                        if not impl_ok:
                            reset_preserving_events(head_before, events_path)
                            wu_events.append(emit_attempt_outcome(
                                wu, attempt, "no_deliverable_files",
                                attempts_usage[-1],
                                extras={"summary": impl_summary},
                            ))
                            attempt_notes.append((attempt, impl_summary))
                            failure_note = impl_summary
                            print(
                                f"   NO DELIVERABLE FILES attempt "
                                f"{attempt}/{MAX_ATTEMPTS}"
                            )
                            continue
                        if wu.type == "close":
                            # Re-read frontmatter post-squash: the agent writes
                            # `verdict:` to the WU file DURING dispatch, but
                            # `wu.verdict` was populated by `load_wu` BEFORE
                            # dispatch. Without this re-read, the agent's
                            # verdict write is invisible to the close-path
                            # check and `fire_terminal_flips` never fires.
                            # Surfaced FEAT-2026-0015/G2-CLOSE: verdict: met
                            # written by agent; in-memory wu.verdict stayed
                            # None; terminal flips skipped silently.
                            wu_fm_post, _ = read_frontmatter(wu.file)
                            wu.verdict = wu_fm_post.get("verdict") or None
                            if verdict_permits_terminal_flips(wu.verdict):
                                close_wu_for_terminal = wu
                            else:
                                plan_path = feature_dir / "PLAN.md"
                                plan_fm_recheck, _ = read_frontmatter(plan_path)
                                if plan_fm_recheck.get("status") == "done":
                                    write_frontmatter_field(plan_path, "status", "active")
                                    commit_bookkeeping(
                                        [plan_path],
                                        f"chore(loop): {wu.wu_id} revert PLAN.md done"
                                        f" (hedged verdict)\n\nFeature: {wu.wu_id}",
                                    )
                        elif _legacy_4wu_terminal_close_complete(
                            wu, units, gate, gates,
                        ):
                            # Legacy 4-WU close sequence completed on terminal gate
                            # (issue #16). The pre-FEAT-2026-0015 shape
                            # (retrospective + lessons + docs + plan-next) has no
                            # close-type WU and no verdict field. Treat the
                            # plan-next pass as terminating-equivalent so the
                            # post-loop block fires fire_terminal_flips.
                            close_wu_for_terminal = wu
                        # FEAT-2026-0018/T07 — plan-next-draft lint hook (warn-only v1)
                        if wu.type == "plan-next":
                            try:
                                # Package-relative + function-local: lint_plan
                                # imports `from .loop import VERDICT_VALUES`, so a
                                # module-top import would be circular; the old
                                # flat (top-level) form broke once the driver
                                # ships as a pip package (#100).
                                from .lint_plan import lint_plan_next_draft
                                _warns = lint_plan_next_draft(feature_dir, gate.number)
                            except Exception as _exc:
                                _warns = [f"lint_plan_next_draft raised: {_exc}"]
                            for _w in _warns:
                                print(f"   WARN (plan-next-draft lint): {_w}")
                            if _warns:
                                wu_events.append(build_event(
                                    "plan_next_draft_lint", wu.wu_id,
                                    {"gate": gate.number, "warns": list(_warns),
                                     "blocking": False},
                                ))
                        wu_events.append(emit_attempt_outcome(
                            wu, attempt, "passed",
                            attempts_usage[-1],
                            files_touched=touched,
                            agent_status="complete",
                            agent_blocked_reason=None,
                        ))
                        wu_events.append(build_event("task_completed", wu.wu_id, {
                            "attempts": attempt,
                            "attempts_usage": attempts_usage,
                        }))
                        flush_events(events_path, wu_events)
                        done_ids.add(wu.wu_id)
                        print(f"   PASS — committed {sha}")
                        break

                    if outcome == "files_changed_mismatch":
                        # RESULT declared files_changed paths that show no diff
                        # against head_before. Treat as a failed attempt: skip
                        # squash, reset the tree, record evidence, retry within
                        # budget. payload is the list of unchanged paths.
                        note = (
                            "RESULT block declared `files_changed` paths that "
                            "show NO diff against HEAD before this attempt:\n"
                            + "\n".join(f"  - {p}" for p in payload)
                            + "\nEither actually modify them, or correct the "
                              "files_changed list to match what you really edited."
                        )
                        wu_events.append(emit_attempt_outcome(
                            wu, attempt, "files_changed_mismatch",
                            attempts_usage[-1],
                            extras={"unchanged_paths": list(payload)},
                        ))
                        attempt_notes.append((attempt, note))
                        failure_note = note
                        reset_preserving_events(head_before, events_path)
                        print(f"   FILES_CHANGED MISMATCH attempt "
                              f"{attempt}/{MAX_ATTEMPTS} — {len(payload)} path(s) "
                              f"unchanged")
                        continue

                    # outcome == "failed": evidence in payload, retry within budget.
                    # Per-attempt notes are buffered (not written to disk) so they
                    # ride with the spinning-escalation commit if we exhaust
                    # attempts; on eventual PASS they're discarded as scratch.
                    attempt_notes.append((attempt, payload))
                    failure_note = payload
                    _fc, _fs = parse_gate_failure_signature(payload)
                    _ex = extract_failure_excerpt(payload)
                    wu_events.append(emit_attempt_outcome(
                        wu, attempt, "failed",
                        attempts_usage[-1],
                        failure_class=_fc,
                        failure_signature=_fs,
                        failure_excerpt=_ex,
                        files_touched=git_diff_names(head_before, "HEAD"),
                        agent_status="complete",
                        agent_blocked_reason=None,
                    ))
                    # T04: halt early when same (class, signature) repeats.
                    if detect_spinning_signature_repeat((_fc, _fs), prior_failure_signature):
                        wu_events.append(build_event("human_escalation", wu.wu_id, {
                            "reason": "spinning_signature_repeat",
                            "failure_class": _fc,
                            "failure_signature": _fs,
                            "attempts": attempt,
                            "attempts_usage": attempts_usage,
                        }))
                        reset_preserving_events(head_before, events_path)
                        backend.set_wu(wu, "status", "blocked_human")
                        write_cost_to_wu(backend, wu, cum_usage)
                        flush_events(events_path, wu_events)
                        commit_bookkeeping(
                            [wu.file, events_path],
                            f"chore(loop): {wu.wu_id} blocked_human "
                            f"(spinning_signature_repeat, attempt {attempt})"
                            f"\n\nFeature: {wu.wu_id}",
                        )
                        print(f"   BLOCKED — spinning signature repeat at "
                              f"attempt {attempt}/{MAX_ATTEMPTS}")
                        blocked = True
                        break
                    if (_fc, _fs) != ("other", "no_gate_marker"):
                        prior_failure_signature = (_fc, _fs)
                    flush_events(events_path, wu_events)
                    wu_events.clear()
                    reset_preserving_events(head_before, events_path)
                    print(f"   FAIL attempt {attempt}/{MAX_ATTEMPTS}")
                else:
                    # for-else: ran out of attempts without break = spinning.
                    # The reset has already happened in the failed/zero_token
                    # branch above. Flush attempt notes to disk for human
                    # inspection, mark the WU blocked_human, then commit it.
                    #
                    # Distinguish two spinning shapes in the event payload:
                    #   all_attempts_zero_token — every attempt billed 0 input
                    #     tokens (CLI/quota/connectivity issue, not a real
                    #     verification failure); no per-attempt notes to write.
                    #   spinning_detected — at least one attempt produced
                    #     output that failed verify(); per-attempt evidence is
                    #     buffered in attempt_notes.
                    all_zero = bool(attempt_outcomes) and all(
                        o == "zero_token" for o in attempt_outcomes)
                    reason = ("all_attempts_zero_token" if all_zero
                              else "spinning_detected")
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
                        "reason": reason,
                        "attempts": MAX_ATTEMPTS,
                        "attempts_usage": attempts_usage,
                    }))
                    flush_events(events_path, wu_events)
                    commit_bookkeeping(
                        [wu.file, events_path, *note_paths],
                        f"chore(loop): {wu.wu_id} blocked_human "
                        f"({reason}, {MAX_ATTEMPTS} attempts)"
                        f"\n\nFeature: {wu.wu_id}",
                    )
                    print(f"   BLOCKED after {MAX_ATTEMPTS} attempts — "
                          f"escalated ({reason})")
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
        is_terminal_gate = gate is gates[-1]
        # FEAT-2026-0018/T11H: in-loop auto-close sets _terminal_auto_closed_wu;
        # fire terminal flips here after gate is at awaiting_review.
        if _terminal_auto_closed_wu is not None:
            rc = _fire_and_verify_terminal_flips(
                _terminal_auto_closed_wu, feature_dir, events_path, feature_id,
            )
            if rc:
                return rc
        elif close_wu_for_terminal is not None:
            # Post-pass driver-state invariant guard (FEAT-2026-0017/T01):
            # fires AFTER fire_terminal_flips so the side-effect checks (gate
            # `passed`, roadmap row `done`, archive anchor) observe the flips.
            rc = _fire_and_verify_terminal_flips(
                close_wu_for_terminal, feature_dir, events_path, feature_id,
            )
            if rc:
                return rc
        used_combined_close = any(
            (feature_dir / ref["file"]).is_file()
            and read_frontmatter(feature_dir / ref["file"])[0].get("type") == "close"
            for ref in gate.refs
        )
        # Re-read PLAN.md status after the close ceremony: a `close` or
        # `plan-next` WU may have flipped it to `done` (single-gate combined
        # close always does; multi-gate terminal plan-next does on the
        # terminal gate). The branching below honors what the close ceremony
        # actually decided rather than guessing from gate shape alone.
        plan_fm_after, _ = read_frontmatter(feature_dir / "PLAN.md")
        feature_done = plan_fm_after.get("status") == "done"
        review = feature_dir / f"GATE-{gate.number:02d}-REVIEW.md"
        if feature_done:
            ceremony = ("combined close ceremony"
                        if used_combined_close
                        else "retro, lessons, docs, plan-next")
            print(f"\nGate {gate.number} complete ({ceremony}); "
                  f"PLAN.md status: done.")
            print(
                "Terminal — feature ready to wrap. Next step:\n"
                "  - /wrap-feature        push branch + "
                "open PR + merge advisory (single-confirm per step).\n"
                "  - Or manually: read RETROSPECTIVE.md, "
                "git push, gh pr create."
            )
        elif is_terminal_gate:
            print(f"\nGate {gate.number} complete (retro, lessons, docs, "
                  f"plan-next); terminal gate but PLAN.md not yet `done`.")
            print(
                "Inconsistency: terminal gate closed without close ceremony "
                "flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / "
                "events.jsonl. Likely fix: manually flip PLAN.md `status: "
                "active -> done`, then `/wrap-feature`."
            )
        else:
            print(f"\nGate {gate.number} complete (retro, lessons, docs, "
                  f"plan-next).")
            print(
                f"Next gate drafted. Next step:\n"
                f"  - /arm-gate            walk drafts, accept/revise/reject, "
                f"flip accepted WUs to `pending`,\n"
                f"                          mark this gate `passed`. "
                f"Reads {review.name} for planner findings.\n"
                f"  - Resume               specfuse-loop"
            )
        return 0
    except BookkeepingCommitError as exc:
        # A bookkeeping commit (gate/WU status flip + events.jsonl audit) was
        # rejected — typically the pre-commit leak-scan hook tripping on staged
        # events content (#75; sibling of squash_commit's #51 rejection
        # handling). Halt the gate cleanly with an actionable message instead of
        # letting the error escape run()/main() as a raw traceback. The staged
        # bookkeeping stays in the working tree (staged-but-uncommitted) for the
        # operator to inspect; nothing is silently lost.
        print(
            "\nloop.py: a bookkeeping commit was rejected — halting the gate "
            "cleanly (no crash).",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        print(
            "\nThe gate/WU status flips and the events.jsonl audit are staged "
            "but uncommitted in the working tree. Inspect the rejecting hook "
            "above, resolve the cause (e.g. a leak-scan FINDINGS line quoted "
            "into events.jsonl — see #76), then commit the staged bookkeeping "
            "manually or re-run the loop.",
            file=sys.stderr,
        )
        return 1
    finally:
        if lock_fd is not None:
            lock_fd.close()


def _parse_version(s: str) -> tuple[int, ...]:
    """Lenient dotted-int parse for version compare. Non-numeric leading junk in a
    component (e.g. a `-rc1` suffix) is dropped; missing components count as 0. No
    third-party `packaging` dependency — the driver stays stdlib-only."""
    parts: list[int] = []
    for tok in str(s).strip().split("."):
        m = re.match(r"\d+", tok)
        parts.append(int(m.group()) if m else 0)
    return tuple(parts) or (0,)


def auto_sync(
    repo: Path | None = None,
    *,
    dry_run: bool = False,
    no_autosync: bool = False,
) -> None:
    """Version-sync .specfuse/ to the installed scaffold on every run.

    Decision tree:
      no_autosync=True / config autosync:false -> skip entirely
      missing .specfuse/           -> scaffold.init (create)
      older, no modified files     -> scaffold.upgrade_specfuse (overlay)
      older, with modified files + TTY  -> prompt per file (overwrite/keep)
      older, with modified files, no TTY -> partial overlay (skip modified, warn)
      equal                        -> no-op
      newer than installed         -> warn + refuse (never downgrade)

    The .specfuse/config file (optional) is parsed for an ``autosync: false``
    entry that disables auto-sync project-wide. Absent config means auto-sync
    is on (default). The ``no_autosync`` parameter takes precedence.
    """
    if no_autosync:
        return

    target = Path(repo) if repo is not None else REPO_ROOT
    specfuse_dir = target / ".specfuse"

    # Check .specfuse/config for project-level opt-out (absent → on).
    config_path = specfuse_dir / "config"
    if config_path.exists():
        try:
            cfg = _miniyaml.parse(config_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001 — malformed config → treat as absent
            cfg = {}
        if cfg.get("autosync") is False:
            return

    if not specfuse_dir.exists():
        if dry_run:
            print(f"auto_sync [dry-run]: .specfuse/ missing -> would scaffold.init({target})")
            return
        if sys.stdin.isatty():
            ans = input(
                f"auto_sync: no .specfuse/ found in {target}. "
                f"Scaffold will create it now. Proceed? [Y/n] "
            ).strip().lower()
            if ans in ("n", "no"):
                print(
                    "auto_sync: scaffold skipped. To suppress this prompt, "
                    "pass --no-autosync or set 'autosync: false' in .specfuse/config.",
                    file=sys.stderr,
                )
                return
        else:
            print(
                f"auto_sync: no TTY — self-provisioning .specfuse/ in {target}.",
                file=sys.stderr,
            )
        _scaffold.init(target)
        _scaffold.refresh_claude_plugin_config(target)  # wire_claude already ran; ensures AC3 call
        return

    installed = _scaffold.scaffold_version()
    version_path = specfuse_dir / "VERSION"

    raw = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else ""
    raw = raw.splitlines()[0].strip() if raw else ""

    if not raw:
        current_tuple: tuple[int, ...] = (0,)
        current_str = "(missing)"
    else:
        current_tuple = _parse_version(raw)
        current_str = raw

    installed_tuple = _parse_version(installed)

    if current_tuple > installed_tuple:
        print(
            f"WARNING: auto_sync: .specfuse/VERSION {current_str} is newer than "
            f"installed scaffold {installed}. Not downgrading. Update specfuse to continue.",
            file=sys.stderr,
        )
        return

    if current_tuple == installed_tuple:
        if dry_run:
            changes = _scaffold.refresh_claude_plugin_config(target, dry_run=True)
            if changes:
                print(
                    f"auto_sync [dry-run]: would correct plugin config drift: {', '.join(changes)}"
                )
            return
        changes = _scaffold.refresh_claude_plugin_config(target)
        if changes:
            print(
                f"WARNING: auto_sync: plugin config drift corrected: {', '.join(changes)}",
                file=sys.stderr,
            )
        return

    # Older — upgrade needed.
    modified = _scaffold.detect_modified(target)

    if not modified:
        if dry_run:
            print(
                f"auto_sync [dry-run]: scaffold {current_str} -> {installed} "
                f"(no modified files) -> would upgrade_specfuse"
            )
            changes = _scaffold.refresh_claude_plugin_config(target, dry_run=True)
            if changes:
                print(
                    f"auto_sync [dry-run]: would correct plugin config drift: {', '.join(changes)}"
                )
            return
        _scaffold.upgrade_specfuse(target)
        changes = _scaffold.refresh_claude_plugin_config(target)
        if changes:
            print(
                f"WARNING: auto_sync: plugin config drift corrected: {', '.join(changes)}",
                file=sys.stderr,
            )
        _persist_scaffold_sync(installed)
        return

    # Older with modified files.
    if sys.stdin.isatty():
        # Interactive: prompt the operator per file (or accept bulk answers).
        files_to_keep: list[str] = []
        overwrite_all = False
        keep_all = False
        for f in modified:
            if overwrite_all:
                continue
            if keep_all:
                files_to_keep.append(f)
                print(f"  auto_sync: (kept) {f}", file=sys.stderr)
                continue
            ans = input(
                f"auto_sync: '{f}' was locally modified. "
                f"Overwrite with scaffold {installed}? [y/N/all/keep-all] "
            ).strip().lower()
            if ans == "all":
                overwrite_all = True
            elif ans == "keep-all":
                keep_all = True
                files_to_keep.append(f)
                print(f"  auto_sync: (kept) {f}", file=sys.stderr)
            elif ans == "y":
                pass  # upgrade_specfuse will overwrite; do not save
            else:
                files_to_keep.append(f)
                print(f"  auto_sync: (kept) {f}", file=sys.stderr)

        if dry_run:
            kept = len(files_to_keep)
            print(
                f"auto_sync [dry-run]: would overlay {len(modified) - kept} file(s), "
                f"keep {kept} file(s)"
            )
            changes = _scaffold.refresh_claude_plugin_config(target, dry_run=True)
            if changes:
                print(
                    f"auto_sync [dry-run]: would correct plugin config drift: {', '.join(changes)}"
                )
            return

        saved: dict[str, bytes] = {
            rel: (specfuse_dir / rel).read_bytes()
            for rel in files_to_keep
            if (specfuse_dir / rel).exists()
        }
        _scaffold.upgrade_specfuse(target)
        for rel, content in saved.items():
            (specfuse_dir / rel).write_bytes(content)
        changes = _scaffold.refresh_claude_plugin_config(target)
        if changes:
            print(
                f"WARNING: auto_sync: plugin config drift corrected: {', '.join(changes)}",
                file=sys.stderr,
            )
        _persist_scaffold_sync(installed)
    else:
        # Non-interactive (CI / claude -p): skip modified files + warn; never block.
        print(
            f"WARNING: auto_sync: {len(modified)} modified versioned file(s) skipped during "
            f"scaffold upgrade ({current_str} -> {installed}). Review manually:",
            file=sys.stderr,
        )
        for f in modified:
            print(f"  (skipped) {f}", file=sys.stderr)

        if dry_run:
            print(
                f"auto_sync [dry-run]: would overlay unmodified versioned files "
                f"({len(modified)} file(s) skipped)"
            )
            changes = _scaffold.refresh_claude_plugin_config(target, dry_run=True)
            if changes:
                print(
                    f"auto_sync [dry-run]: would correct plugin config drift: {', '.join(changes)}"
                )
            return

        saved = {
            rel: (specfuse_dir / rel).read_bytes()
            for rel in modified
            if (specfuse_dir / rel).exists()
        }
        _scaffold.upgrade_specfuse(target)
        for rel, content in saved.items():
            (specfuse_dir / rel).write_bytes(content)
        changes = _scaffold.refresh_claude_plugin_config(target)
        if changes:
            print(
                f"WARNING: auto_sync: plugin config drift corrected: {', '.join(changes)}",
                file=sys.stderr,
            )
        _persist_scaffold_sync(installed)


def main() -> int:
    ap = argparse.ArgumentParser(description="Specfuse loop driver (single-repo).")
    ap.add_argument("--feature", help="Feature dir name under .specfuse/features/ "
                    "(optional if exactly one feature is active).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Walk the current gate without dispatching or writing.")
    ap.add_argument("--force-full-close", metavar="FEATURE_ID",
                    help="Bypass predicate consultation and run the existing close "
                    "path for the named feature. Must match the feature being processed.")
    ap.add_argument("--no-autosync", action="store_true",
                    help="Skip auto-sync entirely (no scaffold create or overlay).")
    ap.add_argument("--prepare", action="store_true",
                    help="Create the active feature's branch (from PLAN.md "
                    "'branch:') and commit its folder, then run — the do-it-for-me "
                    "path after /draft-feature, which leaves the folder "
                    "uncommitted on the current branch.")
    ap.add_argument("--prepare-only", action="store_true",
                    help="Like --prepare (create branch + commit the folder) but "
                    "STOP afterwards without dispatching — review the commit, then "
                    "re-run `specfuse-loop` to start.")
    args = ap.parse_args()
    if not FEATURES_DIR.exists():
        sys.exit(f"No {FEATURES_DIR}. Run from your repo root.")
    auto_sync(dry_run=args.dry_run, no_autosync=args.no_autosync)
    return run(args.feature, args.dry_run, force_full_close=args.force_full_close,
               prepare=args.prepare, prepare_only=args.prepare_only)


if __name__ == "__main__":
    raise SystemExit(main())
