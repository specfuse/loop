---
id: FEAT-2026-0025/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces: .specfuse/scripts/learnings_query.py
oracle_env: macos_local
---

# LEARNINGS entry parser + stdlib BM25 ranker

**Objective.** A pure-Python module that parses `.specfuse/LEARNINGS.md` into
individual tagged entries and ranks them by BM25 relevance to a query string, so a
planning consumer can later load only the relevant slice.

**Context.** This is `FEAT-2026-0025/T01`. `LEARNINGS.md` is loaded whole into every
planning session and is now ~1700 lines / ~100 entries. Entries are markdown
bullets of the form `- [<tag>] <rule text…>` where `<tag>` is `FEAT-YYYY-NNNN/G<n>`
or `meta/<slug>`; a bullet may span several wrapped lines until the next bullet or
blank line. The file also has non-entry prose (the header, `## Format`, `## Entries`
sections). This WU builds the retrieval primitive; T02 wraps it as a CLI with a
threshold fallback, and gate 2 wires the consumers.

Live under `.specfuse/scripts/learnings_query.py`, importable by file path in the
test (the pattern other `.specfuse/scripts` helpers use — not a package import).
Stdlib only — no external dependency (no `rank_bm25`, no `sklearn`). Reference the
binding rules under `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`); honor them rather than restating.

**Acceptance criteria.**

1. **Red test (fails on HEAD):** `tests/test_learnings_query.py::test_ranks_relevant_entry_first`
   builds a small entries list where one entry is clearly on-topic for a query and
   others are not, calls `rank(query, entries)`, and asserts the on-topic entry is
   ranked first. Fails on HEAD because the module does not exist.
2. `parse_entries(text: str) -> list[dict]` returns one dict per bullet entry
   (`{"tag": str, "text": str, "raw": str}`), correctly: joining multi-line wrapped
   bullets into one entry; capturing the `[tag]`; and excluding the file's non-entry
   prose (header, `## Format` example block, section headings). A round-trip test on
   the real `.specfuse/LEARNINGS.md` returns a plausible entry count (> 1, and every
   returned entry has a non-empty `text`).
3. `rank(query: str, entries: list[dict], top_n: int | None = None) -> list[dict]`
   scores each entry against the query with a **BM25** function implemented in this
   module (stdlib only — tokenise on word boundaries, lowercase, standard BM25 term
   weighting over the entry corpus), returns entries sorted by descending score, and
   truncates to `top_n` when given. Ties break deterministically (e.g. by original
   order) so output is stable.
4. The red test passes after this WU. Additional cases pass: an empty query returns
   entries in a deterministic order (no crash); a query matching nothing returns all
   entries with equal/zero score in stable order; `top_n` truncates.
5. **Symbol-existence check:**
   `python3 -c "import importlib.util,pathlib; s=importlib.util.spec_from_file_location('lq', pathlib.Path('.specfuse/scripts/learnings_query.py')); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert callable(m.parse_entries) and callable(m.rank)"`
   exits 0.

**Do not touch.** `.specfuse/LEARNINGS.md` (read-only input — do not edit or
compact it; that is `/learnings-curate`'s job), the driver and linter internals,
other WUs' files, `.git/`, secrets, generated dirs. The driver owns all git. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests`), `coverage` (≥ 90%), `lint`
(`ruff check`), `security` (`bandit`). Plus the AC5 symbol check.

**Escalation triggers.** If the LEARNINGS entry format is ambiguous enough that
`parse_entries` cannot reliably separate entries from prose (e.g. entries and
examples are indistinguishable), emit `status: blocked` naming the ambiguity
rather than guessing a fragile parser. If `parse_entries`/`rank` cannot be added
to `.specfuse/scripts/learnings_query.py`, emit `status: blocked` — do not claim
complete. Blocked is a respectable outcome (`result-contract.md` rule 4).
