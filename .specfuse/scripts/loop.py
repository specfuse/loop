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
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("This driver needs PyYAML.  Install it with:  pip install pyyaml")

SPECFUSE_DIR = Path(".specfuse")
FEATURES_DIR = SPECFUSE_DIR / "features"
VERIFICATION_PATH = SPECFUSE_DIR / "verification.yml"
DRIVER_VERSION = "0.2.0"
MAX_ATTEMPTS = 3  # spinning threshold: 3 failed verification cycles -> escalate

# How to launch a fresh agent. {model} is filled per WU; the prompt is piped on stdin.
CLAUDE_CMD = ["claude", "-p", "--model", "{model}"]

# Which verification gate set (a key in verification.yml) applies to each WU type.
GATES_FOR_TYPE = {
    "implementation": "code",
    "retrospective": "doc",
    "lessons": "doc",
    "docs": "doc",
    "plan-next": "plannext",
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
    fm = yaml.safe_load("\n".join(lines[1:j])) or {}
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
    graph = yaml.safe_load(m.group(1)) or {}
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
    return WorkUnit(
        wu_id=ref["id"],
        file=path,
        depends_on=list(ref.get("depends_on", []) or []),
        type=fm.get("type", "implementation"),
        model=fm.get("model", "claude-sonnet-4-6"),
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


# --------------------------------------------------------------------------- #
# Event log (per feature)                                                      #
# --------------------------------------------------------------------------- #


def log_event(events_path: Path, event_type: str, correlation_id: str,
              payload: dict) -> None:
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "event_type": event_type,
        "source": "driver",
        "source_version": DRIVER_VERSION,
        "payload": payload,
    }
    with events_path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


# --------------------------------------------------------------------------- #
# Git                                                                          #
# --------------------------------------------------------------------------- #


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout.strip()


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


def dispatch(wu: WorkUnit, failure_note: str | None) -> None:
    prompt = PROMPT_PREAMBLE + "\n\n" + wu.body
    if failure_note:
        prompt += ("\n\n## Previous attempt failed verification\n"
                   "A prior fresh attempt failed the gates below. Diagnose and fix; "
                   "do not repeat the same approach.\n\n" + failure_note)
    cmd = [p.replace("{model}", wu.model) for p in CLAUDE_CMD]
    subprocess.run(cmd, input=prompt, capture_output=True, text=True)


def load_verification() -> dict:
    if not VERIFICATION_PATH.exists():
        return {}
    return yaml.safe_load(VERIFICATION_PATH.read_text()) or {}


def verify(wu: WorkUnit, feature_dir: Path) -> tuple[bool, str]:
    """Driver runs the gates itself — the exit oracle. Agent self-report is advisory."""
    cfg = load_verification()
    gate_set = cfg.get(GATES_FOR_TYPE.get(wu.type, "code"), [])
    if not gate_set:
        return True, "_No gates configured for this type; treated as pass._"
    results, ok_all = [], True
    for gate in gate_set:
        command = gate["command"].replace("{feature_dir}", str(feature_dir))
        proc = subprocess.run(command, shell=True, capture_output=True, text=True)
        ok = proc.returncode == 0
        ok_all = ok_all and ok
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-15:]
        results.append(f"### {gate['name']}: {'PASS' if ok else 'FAIL'}\n"
                       f"```\n$ {command}\n" + "\n".join(tail) + "\n```")
    return ok_all, "\n\n".join(results)


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
    backend = Backend()

    gate = next((g for g in gates if g.status != "passed"), None)
    if gate is None:
        print(f"{feature_id}: all gates passed — feature complete.")
        return 0

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
            print(f"\n-- {wu.wu_id} [{wu.type}] model={wu.model}")
            if dry_run:
                print("   (dry run — would dispatch)")
                wu.status = DONE
                done_ids.add(wu.wu_id)
                continue

            head_before = git("rev-parse", "HEAD")
            backend.set_wu(wu, "status", "in_progress")
            log_event(events_path, "task_started", wu.wu_id,
                      {"type": wu.type, "model": wu.model})

            failure_note = None
            for attempt in range(1, MAX_ATTEMPTS + 1):
                backend.set_wu(wu, "attempts", attempt)
                print(f"   attempt {attempt}/{MAX_ATTEMPTS} — fresh session")
                dispatch(wu, failure_note)
                passed, evidence = verify(wu, feature_dir)
                if passed:
                    sha = squash_commit(wu, head_before)
                    backend.set_wu(wu, "status", DONE)
                    log_event(events_path, "task_completed", wu.wu_id,
                              {"attempts": attempt, "commit": sha})
                    done_ids.add(wu.wu_id)
                    print(f"   PASS — committed {sha}")
                    break
                note = work_dir / wu.wu_id.replace("/", "_") / f"attempt-{attempt}.md"
                note.parent.mkdir(parents=True, exist_ok=True)
                note.write_text(evidence)
                failure_note = evidence
                git("reset", "--hard", head_before)
                print(f"   FAIL — evidence in {note}")
            else:
                backend.set_wu(wu, "status", "blocked_human")
                log_event(events_path, "human_escalation", wu.wu_id,
                          {"reason": "spinning detected", "attempts": MAX_ATTEMPTS})
                print(f"   BLOCKED after {MAX_ATTEMPTS} attempts — escalated")
                blocked = True

    if blocked:
        print("\nGate halted: work unit(s) need human attention.")
        return 1
    if dry_run:
        print(f"\n(dry run) Gate {gate.number} would complete and await review.")
        return 0

    backend.set_gate(gate, "awaiting_review")
    log_event(events_path, "gate_reached", feature_id, {"gate": gate.number})
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
