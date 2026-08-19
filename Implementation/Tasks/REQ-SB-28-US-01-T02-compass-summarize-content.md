---
id: REQ-SB-28-US-01-T02
title: compass_client.py — new summarize_content(content, source_description), same shape as classify_email/classify_task
parent_story: REQ-SB-28-US-01
requirement_id: REQ-SB-28
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-28-US-01-T02 — `compass_client.summarize_content`

## Parent Story

- Story: [[REQ-SB-28-US-01]] — `../UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-28 *File Upload for Agents*

---

## Objective

Add `summarize_content(content: str, source_description: str) -> dict` to
`app/data_access/compass_client.py` — a plain Compass chat-completion call
that summarizes real, already-extracted text content, following the exact
`classify_email`/`classify_task` payload/error-handling shape (`ADR-034`
point 3). No new dependency; `compass_client.py` already exists and is
already text-only.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/compass_client.py` has `CompassError`, `classify_email`,
  `classify_task` — confirmed text-only (`ADR-034`); no generic
  `summarize_*` function exists yet.

**After / Outputs:**
- `compass_client.py` additionally exposes:
  ```python
  def summarize_content(content: str, source_description: str) -> dict:
      """Summarizes already-extracted text content (never a raw binary --
      T01's upload_storage.extract_text_content has already produced plain
      text by the time this is called). Same payload construction and
      CompassError handling as classify_email/classify_task (ADR-034 point
      3) -- no new dependency, no new error-handling shape."""
      prompt = (
          "Summarize the following document's actual content, concisely "
          "and accurately, for filing into a personal knowledge base. "
          "Respond with a single JSON object: {\"summary\": <string>}. "
          "Base the summary strictly on the real content below -- never "
          "invent, generalize, or pad with placeholder content.\n\n"
          f"Source: {source_description}\n\n{content[:8000]}"
      )
      payload = {
          "model": settings.compass_model,
          "messages": [{"role": "user", "content": prompt}],
      }
      headers = {
          "Authorization": f"Bearer {settings.compass_api_key}",
          "Content-Type": "application/json",
      }
      try:
          response = httpx.post(
              settings.compass_base_url, headers=headers, json=payload, timeout=30.0
          )
          response.raise_for_status()
      except httpx.HTTPError as exc:
          raise CompassError(f"Compass call failed: {exc}") from exc

      data = response.json()
      try:
          raw_content = data["choices"][0]["message"]["content"]
          parsed = json.loads(raw_content)
          summary = parsed.get("summary")
          if not summary:
              raise CompassError("Compass returned an empty summary")
          return {"summary": summary}
      except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
          raise CompassError(f"couldn't parse Compass response: {exc}") from exc
  ```

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py` — add `summarize_content`
  per the code block above, appended after `classify_task`. Do not modify
  `CompassError`, `classify_email`, or `classify_task`.

---

## Constraints

- Inherits from parent story: never fabricate — an empty/missing summary
  from Compass raises `CompassError`, never returns a placeholder string.
- Same `CompassError` type and `httpx.HTTPError`/parse-error handling
  shape as the two existing functions — no new exception type.
- `content[:8000]` truncation mirrors `classify_email`'s own `body[:4000]`
  precedent (a longer allowance since a summarization prompt's own
  instruction text is shorter than a classification prompt's).
- Do not modify `classify_email`/`classify_task`.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, real Compass
Provider):

1. **[REQ-SB-28-US-01-AC-02]** Call `summarize_content("<real multi-
   paragraph text, e.g. an excerpt from a real document>", "test fixture")`.
   Confirm it returns `{"summary": <string>}` and that the summary text
   genuinely reflects the input content's real subject matter (not a
   generic/placeholder response) — read it and confirm by eye against the
   input.
2. **[REQ-SB-28-US-01-AC-09]** Induce a real Compass failure (in-process
   monkeypatch of `httpx.post` to raise `httpx.ConnectError`, or point
   `settings.compass_base_url` at an unreachable URL for this call only)
   and confirm `summarize_content` raises `CompassError`, not a silent
   empty/placeholder return.
3. Non-AC smoke check: call with an empty string content — confirm either
   a `CompassError` (empty-summary case) or a real, honest low-content
   summary is returned; in no case a fabricated-sounding generic filler.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `summarize_content(content, source_description) -> dict` exists,
      returns `{"summary": str}` on success
- [ ] Raises `CompassError` on HTTP failure, unparseable response, or an
      empty/missing summary — never returns a fabricated placeholder
- [ ] `classify_email`/`classify_task` unmodified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Text extraction from an uploaded file (`.pdf`/`.txt`/`.md` → plain
  text) — `T01`'s `extract_text_content`; this task only summarizes
  already-extracted text.
- Skill catalog/dispatch registration — `T03`.
- Any endpoint/orchestration calling this function — `T04`.

---

## Context / Notes

`content` here is always already-plain-text by the time this function is
called — `T01`'s `upload_storage.extract_text_content` is the caller's
own responsibility (`T04`), not this function's. `summarize_content`
itself has no knowledge of file types.

---

## Implementation Log

**2026-08-14 — built per the task's own code block.** One deviation
from the task's own literal instruction, self-corrected during build:
the Files-to-Modify text says "appended after `classify_task`" — an
initial pass mistakenly inserted the new function between
`classify_email` and `classify_task` instead; caught before
verification and moved to the real end of the file, after
`classify_task`, matching the task's own explicit placement instruction.
`classify_email`/`classify_task` are otherwise byte-for-byte unchanged.

**Verification (Python shell, backend `.venv`, real Compass Provider):**

- **AC-02** (step 1): `summarize_content(<real multi-paragraph "Atlas
  Migration" kickoff-notes text>, "test fixture")` → `{"summary":
  "Atlas Migration kickoff: migrate the legacy billing service from
  on-prem SQL Server to a managed cloud Postgres instance. Stakeholders:
  Priya Raman (Engineering Lead) and Devon Clarke (Finance Ops). Target
  cutover: October 3rd. Risks: data reconciliation drift and downtime
  during the final sync window."` — read by eye against the input:
  genuinely reflects the real subject matter (correct project name,
  both named stakeholders, the correct date, the correct risks), not a
  generic/placeholder response. **Pass.**
- **AC-09** (step 2): in-process monkeypatch of `httpx.post` to raise
  `httpx.ConnectError` for the duration of one call — confirmed
  `summarize_content` raised `CompassError("Compass call failed:
  simulated failure")`, not a silent empty/placeholder return; the
  monkeypatch was reverted immediately after (confirmed `httpx.post`
  restored to the real function). **Pass.**
- Non-AC smoke check (step 3): empty-string content → a real, honest
  low-content response, `{"summary": "No content provided; the document
  is empty."}` — not a fabricated-sounding generic filler.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (`classify_email`/
`classify_task` confirmed unmodified; no new dependency/interface/ADR
deviation; both locked ACs verified live against a real Compass call).
