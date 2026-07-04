#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Parse .specfuse/LEARNINGS.md entries and rank them by BM25 relevance.

`parse_entries` splits the file's `- [<tag>] <text>` bullets (which may wrap
across several lines) into individual entries, skipping the file's header,
`## Format` example, and section headings. `rank` scores those entries against
a query string with a stdlib-only BM25 implementation so a planning consumer
can load only the relevant slice instead of the whole file.
"""

from __future__ import annotations

import math
import re

_ANCHOR = "<!-- lessons work units append below this line -->"
_BULLET_RE = re.compile(r"^-\s*\[([^\]]+)\]\s*(.*)$")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

_BM25_K1 = 1.5
_BM25_B = 0.75


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def parse_entries(text: str) -> list[dict]:
    """Parse LEARNINGS.md-style bullets into entry dicts.

    Only lines after the `_ANCHOR` marker (the line the append-only section
    starts below) are considered, which excludes the header prose and the
    `## Format` example bullet. A blank line or a `##`/`#` heading ends the
    current entry; a following non-bullet line is joined onto the current
    entry as a wrapped continuation.
    """
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if _ANCHOR in line:
            start = i + 1
            break

    entries: list[dict] = []
    current: dict | None = None

    def flush() -> None:
        if current is None:
            return
        entry_text = " ".join(part for part in current["parts"] if part).strip()
        if entry_text:
            entries.append(
                {
                    "tag": current["tag"],
                    "text": entry_text,
                    "raw": "\n".join(current["raw_lines"]),
                }
            )

    for line in lines[start:]:
        stripped = line.strip()
        match = _BULLET_RE.match(stripped)
        if match:
            flush()
            current = {
                "tag": match.group(1).strip(),
                "parts": [match.group(2).strip()],
                "raw_lines": [line],
            }
        elif stripped == "" or stripped.startswith("#"):
            flush()
            current = None
        elif current is not None:
            current["parts"].append(stripped)
            current["raw_lines"].append(line)

    flush()
    return entries


def rank(query: str, entries: list[dict], top_n: int | None = None) -> list[dict]:
    """Rank entries by BM25 relevance to query, descending; ties keep original order."""
    n = len(entries)
    if n == 0:
        return []

    docs = [_tokenize(entry["text"]) for entry in entries]
    doc_lens = [len(doc) for doc in docs]
    avgdl = sum(doc_lens) / n if n else 0.0

    doc_freq: dict[str, int] = {}
    for doc in docs:
        for term in set(doc):
            doc_freq[term] = doc_freq.get(term, 0) + 1

    idf = {
        term: math.log(1 + (n - freq + 0.5) / (freq + 0.5))
        for term, freq in doc_freq.items()
    }

    query_terms = _tokenize(query)

    scores = []
    for i, doc in enumerate(docs):
        term_freq: dict[str, int] = {}
        for term in doc:
            term_freq[term] = term_freq.get(term, 0) + 1

        dl = doc_lens[i]
        length_norm = _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl) if avgdl else _BM25_K1
        score = 0.0
        for term in query_terms:
            freq = term_freq.get(term)
            if not freq:
                continue
            score += idf.get(term, 0.0) * (freq * (_BM25_K1 + 1)) / (freq + length_norm)
        scores.append(score)

    order = sorted(range(n), key=lambda i: (-scores[i], i))
    ranked = [entries[i] for i in order]
    return ranked[:top_n] if top_n is not None else ranked
