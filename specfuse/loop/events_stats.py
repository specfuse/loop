#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Read-only cost aggregator over ``events.jsonl`` (issue #271).

The loop writes a rich per-attempt record and, until this module, nothing read
it for cost. An afternoon of ad-hoc Python over that corpus produced four merged
fixes — the planning-floor correction (#266), the guard-contract ranking (#268),
the arm-time refusal prediction (#269), and the outcome-contract correction
(#272) — and none of it was reproducible by anyone else.

The most consequential of those *reversed a rule that had already merged*: the
floors were raised on the evidence of one feature whose ``plan-next`` cost
$16.44, against a population median of $3.57 across 62 observations. The data to
catch that was already on disk.

Answers the questions a failure-clustering tool structurally cannot:

- what a **passing** attempt of each WU type costs — the number a floor is
  calibrated from, and not a failure at all;
- how much spend goes to refused attempts, attributed to the guard that refused;
- whether a given feature is an outlier, before a rule is generalised from it.

Deliberately **read-only, and deliberately not wired to any gate.** Every fix
above needed a human reading the numbers and deciding what they meant; the one
time a number was acted on without that reading, it produced the wrong rule.

Usage:  events_stats.py [--roots DIR ...] [--json] [--min-fires N]
"""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

__all__ = ("collect", "render", "main")

# `passed` is the success path; `zero_token_skip` means no attempt ran, so it
# has nothing to describe and is not a missing diagnostic. Every other outcome
# carries its reason in one of the fields below — see docs/methodology.md,
# "Per-attempt outcome events". Reading only `failure_class` reports complete
# records as empty, an error made three times before that contract was written.
_DIAGNOSTIC_FIELDS = (
    "failure_class", "failure_excerpt", "failure_signature",
    "summary", "agent_blocked_reason", "unchanged_paths",
)
_NO_DIAGNOSTIC_EXPECTED = frozenset({"zero_token_skip"})

_CLOSING_SUFFIXES = {
    "PLAN": "plan-next",
    "CLOSE": "close",
    "CLOSE-INTERMEDIATE": "close-intermediate",
    "RETRO": "legacy-retro",
    "LESSONS": "legacy-lessons",
    "DOCS": "legacy-docs",
}
_CLOSING_RE = re.compile(r"/G\d+-([A-Z-]+)$")
_GUARD_RE = re.compile(r"\b(assert_[a-z_]+)")


def _wu_type(correlation_id: str) -> str:
    """Bucket a WU by its correlation-ID suffix.

    The ID is the only type signal available in the event stream — WU
    frontmatter is not reachable from a bare corpus scan, and the whole point of
    this tool is to read many repositories without checking them out.
    """
    m = _CLOSING_RE.search(correlation_id or "")
    if m:
        return _CLOSING_SUFFIXES.get(m.group(1), "other-closing")
    return "implementation"


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(int(len(ordered) * q), len(ordered) - 1)
    return ordered[idx]


def collect(roots: list[Path] | list[str]) -> dict:
    """Walk every ``events.jsonl`` under *roots* and aggregate.

    Deduplicates on ``(correlation_id, timestamp, event_type)``. This is not
    defensive tidiness: the same repository routinely appears at several paths —
    worktrees, parallel checkouts — and a naive glob double-counts. In the
    workspace this tool was written against, 13 paths collapsed to 9 distinct
    repositories, so without the dedupe every figure is inflated by an arbitrary
    factor.
    """
    seen: set[tuple] = set()
    attempts: list[dict] = []
    gate_runs: list[dict] = []
    repos: set[str] = set()

    for root in roots:
        root_path = Path(root)
        # Three layouts: the repository itself (the default `--roots .` run
        # from inside one), a workspace directory holding repos, and a
        # directory holding several such workspaces. Pointing at the wrong
        # depth otherwise returns zero, which an analysis tool must never
        # report as "no waste" — see `main` for the empty-corpus message.
        found = sorted(
            set(root_path.glob(".specfuse/features/*/events.jsonl"))
            | set(root_path.glob("*/.specfuse/features/*/events.jsonl"))
            | set(root_path.glob("*/*/.specfuse/features/*/events.jsonl"))
        )
        for path in found:
            rel = path.relative_to(root_path).parts
            repo = "/".join(rel[:rel.index(".specfuse")]) if ".specfuse" in rel else str(path)
            if not repo:
                repo = root_path.resolve().name
            for raw in path.read_text(errors="ignore").splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    event = json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    continue  # a torn line is not a reason to abandon the corpus
                if not isinstance(event, dict):
                    continue
                if event.get("event_type") not in ("attempt_outcome", "gate_result"):
                    continue
                # `gate_result` shares the timestamp of its sibling gates within
                # one flush, so the gate name and phase join the key; for
                # `attempt_outcome` the three-part key is unchanged.
                payload = event.get("payload") or {}
                key = (event.get("correlation_id"), event.get("timestamp"),
                       event.get("event_type"))
                if event["event_type"] == "gate_result":
                    key += (payload.get("gate"), payload.get("phase"),
                            payload.get("attempt"))
                if key in seen:
                    continue
                seen.add(key)
                if event["event_type"] == "gate_result":
                    if payload.get("gate") is None:
                        continue
                    gate_runs.append({
                        "gate": str(payload["gate"]),
                        "phase": payload.get("phase") or "attempt",
                        "seconds": float(payload.get("duration_seconds") or 0.0),
                        "feature": path.parent.name,
                    })
                    repos.add(repo)
                    continue
                attempts.append({
                    "cid": event.get("correlation_id") or "",
                    "outcome": payload.get("outcome"),
                    "cost": float(payload.get("cost_usd") or 0.0),
                    "attempt": payload.get("attempt") or 0,
                    "summary": payload.get("summary") or "",
                    "diagnosed": any(payload.get(f) for f in _DIAGNOSTIC_FIELDS),
                    "repo": repo,
                    "feature": path.parent.name,
                    "agent_s": (float(payload["agent_seconds"])
                                if "agent_seconds" in payload else None),
                    "verify_s": (float(payload["verify_seconds"])
                                 if "verify_seconds" in payload else None),
                })
                repos.add(repo)

    by_type: dict[str, dict] = {}
    per_wu: dict[str, list[dict]] = {}
    for a in attempts:
        per_wu.setdefault(a["cid"], []).append(a)

    for cid, atts in per_wu.items():
        bucket = by_type.setdefault(_wu_type(cid), {
            "wus": 0, "attempts": 0, "first_try": 0,
            "passing_costs": [], "waste": 0.0,
        })
        bucket["wus"] += 1
        bucket["attempts"] += len(atts)
        ordered = sorted(atts, key=lambda x: x["attempt"])
        if ordered and ordered[0]["outcome"] == "passed":
            bucket["first_try"] += 1
        for a in atts:
            if a["outcome"] == "passed":
                bucket["passing_costs"].append(a["cost"])
            else:
                bucket["waste"] += a["cost"]

    for bucket in by_type.values():
        costs = bucket["passing_costs"]
        bucket["median"] = round(statistics.median(costs), 2) if costs else 0.0
        bucket["mean"] = round(statistics.mean(costs), 2) if costs else 0.0
        bucket["p90"] = round(_percentile(costs, 0.9), 2)
        bucket["max"] = round(max(costs), 2) if costs else 0.0
        bucket["waste"] = round(bucket["waste"], 2)
        bucket["first_try_rate"] = (
            round(bucket["first_try"] / bucket["wus"], 4) if bucket["wus"] else 0.0
        )

    by_outcome: dict[str, dict] = {}
    by_guard: dict[str, dict] = {}
    undiagnosed = 0
    for a in attempts:
        if a["outcome"] == "passed":
            continue
        entry = by_outcome.setdefault(a["outcome"] or "(none)", {"n": 0, "waste": 0.0})
        entry["n"] += 1
        entry["waste"] = round(entry["waste"] + a["cost"], 2)
        if not a["diagnosed"] and a["outcome"] not in _NO_DIAGNOSTIC_EXPECTED:
            undiagnosed += 1
        guard = _GUARD_RE.search(a["summary"])
        if guard:
            g = by_guard.setdefault(guard.group(1), {"fires": 0, "waste": 0.0})
            g["fires"] += 1
            g["waste"] = round(g["waste"] + a["cost"], 2)

    # Agent/verify split per feature. Only attempts that carry both fields
    # count; an old corpus has neither, and must read "not recorded", never 0.
    split: dict[str, dict] = {}
    for a in attempts:
        if a["agent_s"] is None or a["verify_s"] is None:
            continue
        f = split.setdefault(f"{a['repo']}:{a['feature']}", {
            "attempts": 0, "agent_seconds": 0.0, "verify_seconds": 0.0})
        f["attempts"] += 1
        f["agent_seconds"] += a["agent_s"]
        f["verify_seconds"] += a["verify_s"]
    for f in split.values():
        total = f["agent_seconds"] + f["verify_seconds"]
        f["agent_seconds"] = round(f["agent_seconds"], 2)
        f["verify_seconds"] = round(f["verify_seconds"], 2)
        f["agent_share"] = round(f["agent_seconds"] / total, 4) if total else 0.0
        f["verify_share"] = round(f["verify_seconds"] / total, 4) if total else 0.0

    # Slowest gates, split by phase, ordered by total seconds.
    by_gate: dict[tuple, list[float]] = {}
    for g in gate_runs:
        by_gate.setdefault((g["phase"], g["gate"]), []).append(g["seconds"])
    gate_timings = [
        {"phase": phase, "gate": gate, "runs": len(secs),
         "total_seconds": round(sum(secs), 2),
         "median_seconds": round(statistics.median(secs), 2),
         "max_seconds": round(max(secs), 2)}
        for (phase, gate), secs in by_gate.items()
    ]
    gate_timings.sort(key=lambda r: (-r["total_seconds"], r["phase"], r["gate"]))

    spend = round(sum(a["cost"] for a in attempts), 2)
    waste = round(sum(a["cost"] for a in attempts if a["outcome"] != "passed"), 2)
    return {
        "totals": {
            "repos": len(repos),
            "work_units": len(per_wu),
            "attempts": len(attempts),
            "spend": spend,
            "waste": waste,
            "waste_share": round(waste / spend, 4) if spend else 0.0,
        },
        "by_type": by_type,
        "by_outcome": by_outcome,
        "by_guard": by_guard,
        "undiagnosed": undiagnosed,
        "time_split": split,
        "gate_timings": gate_timings,
    }


def render(stats: dict, min_fires: int = 1) -> str:
    """Human-readable report. Figures only — no verdicts, no thresholds."""
    t = stats["totals"]
    out = [
        f"events.jsonl — {t['attempts']} attempts across {t['work_units']} work "
        f"units in {t['repos']} repositories",
        "  deduplicated on (correlation_id, timestamp, event_type)",
        "",
        f"  total spend  ${t['spend']:.2f}",
        f"  waste        ${t['waste']:.2f}  ({t['waste_share'] * 100:.0f}% of spend, "
        f"on attempts that did not pass)",
        "",
        "cost of PASSING attempts, by WU type",
        f"  {'type':22s} {'WUs':>4s} {'1st-try':>8s} {'median':>8s} {'p90':>8s} "
        f"{'max':>8s} {'waste':>9s}",
    ]
    for name, b in sorted(stats["by_type"].items(), key=lambda kv: -kv[1]["wus"]):
        out.append(
            f"  {name:22s} {b['wus']:>4d} {b['first_try_rate'] * 100:>7.0f}% "
            f"{b['median']:>8.2f} {b['p90']:>8.2f} {b['max']:>8.2f} {b['waste']:>9.2f}"
        )

    if stats["by_guard"]:
        out += ["", "waste by guard (from the summary field)",
                f"  {'guard':54s} {'fires':>6s} {'waste':>9s}"]
        for g, v in sorted(stats["by_guard"].items(), key=lambda kv: -kv[1]["waste"]):
            if v["fires"] >= min_fires:
                out.append(f"  {g:54s} {v['fires']:>6d} {v['waste']:>9.2f}")

    if stats["by_outcome"]:
        out += ["", "waste by outcome", f"  {'outcome':32s} {'n':>5s} {'waste':>9s}"]
        for o, v in sorted(stats["by_outcome"].items(), key=lambda kv: -kv[1]["waste"]):
            out.append(f"  {o:32s} {v['n']:>5d} {v['waste']:>9.2f}")

    out += ["", "agent / verify time per feature"]
    split = stats.get("time_split") or {}
    if not split:
        out.append("  not recorded")
    else:
        out.append(f"  {'feature':54s} {'agent s':>9s} {'verify s':>9s} "
                   f"{'agent%':>7s} {'verify%':>8s}")
        for name, v in sorted(split.items(), key=lambda kv: -(
                kv[1]["agent_seconds"] + kv[1]["verify_seconds"])):
            out.append(f"  {name:54s} {v['agent_seconds']:>9.2f} "
                       f"{v['verify_seconds']:>9.2f} {v['agent_share'] * 100:>6.0f}% "
                       f"{v['verify_share'] * 100:>7.0f}%")

    out += ["", "slowest gates (gate_result events)"]
    timings = stats.get("gate_timings") or []
    if not timings:
        out.append("  not recorded")
    else:
        out.append(f"  {'phase':9s} {'gate':32s} {'runs':>5s} {'total s':>9s} "
                   f"{'median s':>9s} {'max s':>8s}")
        for r in timings:
            out.append(f"  {r['phase']:9s} {r['gate']:32s} {r['runs']:>5d} "
                       f"{r['total_seconds']:>9.2f} {r['median_seconds']:>9.2f} "
                       f"{r['max_seconds']:>8.2f}")

    if stats["undiagnosed"]:
        out += ["", f"  {stats['undiagnosed']} non-passing attempts carry no "
                    f"diagnostic in any documented field — see docs/methodology.md, "
                    f"'Per-attempt outcome events'"]
    return "\n".join(out)


def main() -> int:
    import argparse

    from specfuse.loop.build_provenance import warn_if_out_of_tree
    warn_if_out_of_tree()

    parser = argparse.ArgumentParser(
        description="Aggregate cost and outcomes from events.jsonl. Read-only.",
        usage="events_stats.py [--roots DIR ...] [--json] [--min-fires N]",
    )
    parser.add_argument(
        "--roots", nargs="+", default=["."],
        help="Repositories, or directories containing them (default: '.'). "
             "Pass a workspace root to compare across projects — the "
             "cross-repo view is what tells you whether one feature is an "
             "outlier.",
    )
    parser.add_argument("--json", action="store_true", help="Emit raw JSON.")
    parser.add_argument("--min-fires", type=int, default=1,
                        help="Hide guards below this fire count (default 1).")
    args = parser.parse_args()

    stats = collect([Path(r) for r in args.roots])
    if stats["totals"]["attempts"] == 0:
        # Never render an empty report as a clean one. A zero here almost always
        # means the roots point at the wrong depth, and "no waste" is a far more
        # damaging misreading than an error.
        print(
            "no events.jsonl found under: " + ", ".join(args.roots) + "\n"
            "Pass a repository, or a directory containing repositories, "
            "e.g. --roots ~/work."
        )
        return 1
    if args.json:
        print(json.dumps(stats, indent=2, sort_keys=True))
    else:
        print(render(stats, min_fires=args.min_fires))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
