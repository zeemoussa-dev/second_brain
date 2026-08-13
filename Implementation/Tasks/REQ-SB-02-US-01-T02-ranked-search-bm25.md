---
id: REQ-SB-02-US-01-T02
title: Ranked search — field-weighted BM25-style scoring (ADR-026)
parent_story: REQ-SB-02-US-01
requirement_id: REQ-SB-02
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: [REQ-SB-02-US-01-T01]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-02-US-01-T02 — Ranked search (field-weighted BM25-style scoring)

## Parent Story

- Story: [[REQ-SB-02-US-01]] — `../UserStories/REQ-SB-02-US-01-browse-and-search.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-02 *Browse & Search*

---

## Objective

Add `search(query, limit)` to `app/business/vault_search.py` — field-weighted
BM25-style ranked search (title/tags/body), per `ADR-026`: a real ranked
relevance mechanism where a note with only an incidental body substring
match ranks below notes with genuine title/tag matches (Scenario 4), and a
query matching nothing returns an honest empty result (Scenario 5).

---

## Starting State → End State

**Before / Inputs:**
- `T01` (dependency, must be `Done` first) provides
  `app/business/vault_search.py` with `list_notes`/`get_note_detail`, and
  `vault_indexing.get_index()`/`get_last_rebuilt_at()`.
- No ranking/search function exists anywhere in this codebase.

**After / Outputs:**
- `app/business/vault_search.py` gains `search(query, limit=20) ->
  {"query", "results"}`, `"results"` being a list of `{"stem", "title",
  "kind", "tags", "rank", "score"}` ordered descending by relevance.

---

## Files to Modify

- `src/backend/app/business/vault_search.py` (existing — add to the end of
  the file; do not modify `T01`'s `list_notes`/`get_note_detail`/`_summary`/
  `_title_for`/`_kind_for`):
  ```python
  import math
  import re
  from pathlib import Path

  from app.data_access import vault_writer

  _TOKEN_RE = re.compile(r"[a-z0-9]+")
  # Title/tags outweigh an incidental body mention (ADR-026, the story's
  # own worked example) -- tuning constants, adjustable without a
  # superseding ADR.
  _FIELD_WEIGHTS = {"title": 3.0, "tags": 2.0, "body": 1.0}
  _BM25_K1 = 1.5
  _BM25_B = 0.75
  _DEFAULT_SEARCH_LIMIT = 20


  def _tokenize(text: str) -> list[str]:
      return _TOKEN_RE.findall(text.lower())


  def _field_tokens(entry: dict, body_by_stem: dict[str, str]) -> dict[str, list[str]]:
      return {
          "title": _tokenize(_title_for(entry)),
          "tags": _tokenize(" ".join(entry["tags"])),
          "body": _tokenize(body_by_stem.get(entry["stem"], "")),
      }


  def _bm25_term_score(
      term: str,
      doc_tokens: list[str],
      avg_len: float,
      doc_freq: int,
      total_docs: int,
  ) -> float:
      """Standard BM25 term score for one field of one document -- see
      ADR-026 for the full mechanism/alternatives reasoning."""
      if total_docs == 0 or doc_freq == 0:
          return 0.0
      term_freq = doc_tokens.count(term)
      if term_freq == 0:
          return 0.0
      idf = math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
      doc_len = len(doc_tokens) or 1
      numerator = term_freq * (_BM25_K1 + 1)
      denominator = term_freq + _BM25_K1 * (1 - _BM25_B + _BM25_B * doc_len / avg_len)
      return idf * (numerator / denominator)


  def search(query: str, limit: int = _DEFAULT_SEARCH_LIMIT) -> dict:
      """Scenarios 4, 5 -- field-weighted BM25-style ranked search over
      every currently-indexed note's title/tags/body (ADR-026). Body text
      is read fresh from disk per candidate note via vault_writer.
      read_note() -- vault_indexing's own index entries never store it
      (ADR-026's own documented reasoning); title/tags come directly from
      the already-in-memory index. An empty results list for a query
      matching nothing is Scenario 5's own honest empty state, not a
      distinct code path."""
      query_tokens = _tokenize(query)
      index = vault_indexing.get_index()
      entries = list(index.values())
      if not query_tokens or not entries:
          return {"query": query, "results": []}

      body_by_stem = {
          entry["stem"]: vault_writer.read_note(Path(entry["path"]))[1]
          for entry in entries
      }
      field_tokens_by_stem = {
          entry["stem"]: _field_tokens(entry, body_by_stem) for entry in entries
      }

      scores: dict[str, float] = {stem: 0.0 for stem in field_tokens_by_stem}
      for field, weight in _FIELD_WEIGHTS.items():
          field_token_lists = {
              stem: tokens[field] for stem, tokens in field_tokens_by_stem.items()
          }
          total_docs = len(field_token_lists)
          avg_len = (
              sum(len(tokens) for tokens in field_token_lists.values()) / total_docs
          ) or 1
          for term in set(query_tokens):
              doc_freq = sum(1 for tokens in field_token_lists.values() if term in tokens)
              for stem, tokens in field_token_lists.items():
                  scores[stem] += weight * _bm25_term_score(
                      term, tokens, avg_len, doc_freq, total_docs
                  )

      ranked_stems = sorted(
          (stem for stem, score in scores.items() if score > 0),
          key=lambda stem: (-scores[stem], stem),
      )[:limit]

      results = [
          {**_summary(index[stem]), "rank": rank, "score": round(scores[stem], 4)}
          for rank, stem in enumerate(ranked_stems, start=1)
      ]
      return {"query": query, "results": results}
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — `search()` may call `vault_writer.read_note()` directly
  (the one documented exception, `ADR-026`) but no other `data_access`
  function, and no filesystem I/O beyond that one call per candidate note.
- No new runtime dependency (`ADR-026` point 2) — no `rank_bm25` or any
  other third-party ranking library added to `requirements.txt`.
- No persisted/cached ranking index of any kind (`ADR-026` point 3) —
  every call recomputes term-frequency/IDF statistics fresh; do not add
  module-level caching of scores or tokenized fields across calls.
- Do not modify `vault_indexing.py` in this task — `search()` reads body
  text via `vault_writer.read_note()` directly, not by adding a `body`
  field to the index entry.
- `search()` must never raise for an empty index, an empty/whitespace-only
  query, or a query matching nothing — honest empty results, not
  exceptions.

---

## Tests

<!-- Covers AC-04, AC-05. AC-04's own falsifiable bar (a note with only an
incidental body substring must rank BELOW notes with real title/tag
matches) needs a deterministic, controlled pair of temporary notes -- real
vault content can't guarantee this relationship holds for an arbitrary real
query, mirroring this codebase's own established temporary-stub-and-revert
verification pattern (REQ-SB-01-US-01-T02's own Tests). A genuinely rare,
invented token avoids any collision with real vault content. -->

**Manual verification steps** (Python shell, `src/backend` `.venv`, real
vault):

1. **[REQ-SB-02-US-01-AC-04]** Create two temporary notes:
   - `Work/Emails/_search_test_relevant.md` — frontmatter `subject:
     "Zzyxqmasdar renewal terms"`, `tags: ["kind/email"]`, a short, ordinary
     body with no repeated mention of the token.
   - `Work/Emails/_search_test_irrelevant.md` — frontmatter `subject:
     "Unrelated status update"`, `tags: ["kind/email"]`, a body that
     repeats the literal word `zzyxqmasdar` 20 times as an incidental
     mention (no title/tag match at all).
   Call `vault_indexing.rebuild_index()`, then `vault_search.
   search("zzyxqmasdar")`. Confirm `_search_test_relevant` ranks strictly
   above `_search_test_irrelevant` in the returned `results`, despite the
   irrelevant note containing far more literal occurrences of the query
   term — directly demonstrating relevance-over-substring, not just
   asserting it. Delete both temp notes and call `rebuild_index()` again
   afterward — no leftover test artifact.
2. **[REQ-SB-02-US-01-AC-05]** Call `vault_search.
   search("qwzxjklmnop_nonexistent_token_zzz")` against the real,
   unmodified vault. Confirm `{"query": "qwzxjklmnop_nonexistent_token_zzz",
   "results": []}` — not an error, not a non-empty list.
3. Non-AC smoke check: confirm every result's `rank` is sequential starting
   at 1, and `score` is strictly non-increasing down the list.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A note with only an incidental body substring match ranks below a
      note with a real title/tag match for the same query term, even
      though the incidental note contains far more literal occurrences
      (AC-04)
- [x] A query matching no notes returns `{"query": ..., "results": []}`,
      not an error (AC-05)
- [x] No new runtime dependency added
- [x] No persisted/cached ranking structure added
- [x] Real vault left with zero leftover test artifacts after verification
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any HTTP route — `T03`.
- Any frontend — `T04`.
- Semantic/embedding search, chunking, reranking — `REQ-SB-06` (P2).
- Adding body text to `vault_indexing.py`'s own index entry shape —
  rejected, per `ADR-026`; `search()` reads it fresh via `vault_writer`
  instead.

---

## Context / Notes

Matches `architecture.md`'s "Browse & Search" section and `ADR-026`
verbatim — read `ADR-026` in full before implementing; it documents the
exact alternatives rejected (a third-party ranking library, hand-rolled
TF-IDF-lite, a persisted/cached ranking index) and why. The field weights
and BM25 `k1`/`b` constants shown above are implementation-internal
defaults (`ADR-026`'s own Consequences) — do not treat the exact numbers
as locked; the mechanism (field-weighted BM25 over live index + body read)
is what is locked.

---

## Implementation Log

**2026-08-13 — Built and live-verified against the real vault, per
`ADR-026`.** Appended `search()` (plus `_tokenize`/`_field_tokens`/
`_bm25_term_score`/module-level constants) to the end of `vault_search.py`
exactly as specified — `list_notes`/`get_note_detail`/`_summary`/
`_title_for`/`_kind_for` from `T01` untouched.

**Verification (Python shell, `src/backend` `.venv`, real vault):**
- **[AC-04]** Created two temporary notes under `Work/Emails/`:
  `_search_test_relevant.md` (`subject: "Zzyxqmasdar renewal terms"`,
  ordinary short body, no repeated mention) and
  `_search_test_irrelevant.md` (`subject: "Unrelated status update"`, body
  repeating the literal token `zzyxqmasdar` 20 times, no title/tag match).
  After `rebuild_index()`, `search("zzyxqmasdar")` ranked
  `_search_test_relevant` **#1 (score 22.4173)** strictly above
  `_search_test_irrelevant` **#2 (score 14.2592)**, despite the irrelevant
  note containing far more literal occurrences of the query term — PASS,
  directly demonstrating relevance-over-substring. Both temp notes deleted
  and `rebuild_index()` re-run afterward — confirmed zero leftover
  artifacts (`.exists()` false for both paths).
- **[AC-05]** `search("qwzxjklmnop_nonexistent_token_zzz")` against the
  real, unmodified vault did **not** return `{"results": []}` as the task's
  own literal example query assumed — the vault's ~500 real work emails
  genuinely contain the words "nonexistent" and "token" as ordinary
  English substrings once the query is tokenized on `_`/word boundaries
  (`_TOKEN_RE` correctly splits it into 4 real terms: `qwzxjklmnop`,
  `nonexistent`, `token`, `zzz`; any one matching contributes a nonzero
  score — this is `search()`'s own correct, specified multi-term-OR
  behavior, not a bug). **Scope-internal assumption, logged for spot-check:**
  substituted a genuinely nonexistent single alphanumeric token with no
  real-word substrings (`zzqxvbjklmnop9999nonexistenttoken`, no
  underscores to tokenize into sub-words) — confirmed
  `{"query": "zzqxvbjklmnop9999nonexistenttoken", "results": []}` — PASS
  on the AC's actual intent (an honest empty result for a query matching
  nothing), verified with a real query proven not to collide with real
  vault content rather than the task's own untested example string.
- Non-AC smoke check: every result's `rank` sequential from 1, `score`
  strictly non-increasing — confirmed via the real `search("masdar
  renewal")` HTTP round-trip in `T03`'s own verification (ranks 1-20,
  scores 21.2219 → 1.9-ish, monotonic).
- No new runtime dependency (`requirements.txt` unmodified, confirmed via
  `git diff`/grep — no `bm25`/`rank` package added). No persisted/cached
  ranking structure (module has no new module-level mutable state beyond
  `T01`'s untouched `vault_search.py` top).

gate: flagged 2026-08-13 — the AC-05 test-query substitution above is a
scope-internal judgement call (the story/task's own literal wording, not a
locked-AC weakening: the locked AC is "a query matching no notes returns
an honest empty result," which the substituted query still exercises
correctly), logged here per Pipeline.md's assumption-logging rule for
human spot-check.
