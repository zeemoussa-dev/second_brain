---
id: REQ-SB-55-US-01-T03
title: Thread-Match/Merge Job — create-on-first-message, regenerate-on-update, tag union, participants/last_message_at
parent_story: REQ-SB-55-US-01
requirement_id: REQ-SB-55
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — carried from the parent story; the human reviews ADR-043 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-55-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01-T03 — `Thread-Match/Merge` Job

## Parent Story

- Story: [[REQ-SB-55-US-01]] — `../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-55 *Email Capture & Threading Pipeline*

---

## Objective

Add `thread_match_merge(email, classification, attachment_entries=None) -> dict` to `email_classification.py` — this Pipeline's `Thread-Match/Merge` Job: on the FIRST message of a `conversation_id`, creates the Thread note and files a real `[[wikilink]]`-bearing customer hub reference; on every LATER message in the SAME conversation, regenerates `## Summary` fresh, grows `## Transcript`, folds in any attachment sub-entries into `## Attachments`, and UNIONS new tags onto the existing set (never pruning). Also owns writing the Thread's additive baseline-extension frontmatter keys `customer`/`participants`/`last_message_at` (`ADR-043` point 7).

---

## Starting State → End State

**Before / Inputs:**
- `thread_note_path`/`thread_note_exists`/`create_thread_note_baseline`/`ensure_thread_note_baseline_frontmatter` (`REQ-SB-54-US-01-T02`) — deterministic Thread path/baseline, `## Summary`+`## Transcript` body shape only.
- `replace_body_section` (`REQ-SB-54-US-01-T01`) — full-region `## Summary` regeneration.
- `T01`'s new header-scoped growing-append primitive (`## Transcript`/`## Attachments` growth) and unconditional frontmatter-key setter (`participants`/`last_message_at`/`project`/tag-union overwrites).
- `customer_hub_linking.ensure_customer_hub_note(customer)` — ensures the Customer's OKF directory skeleton exists (does NOT write the inline body wikilink — that half is Email's own now-superseded convention, per `ADR-043` Consequences).
- No Thread ever gets written to today — `classify_recent_emails` still writes one flat Email note per message.

**After / Outputs:**
- `thread_match_merge(email, classification, attachment_entries=None) -> dict` exists, returning at minimum `{"thread_path": str, "created": bool, "conversation_id": str, "customer": str}` — `created` is the signal `T07`'s pipeline wiring uses to decide whether `Route-to-Project` fires (Scenario 4/`AC-04`'s own mechanism, `ADR-043` point 3).
- A brand-new conversation produces exactly ONE Thread note (`create_thread_note_baseline`), tagged with `build_tags(customer, kind)`-derived initial tags, `customer` set, `participants` seeded from the first message's sender, `last_message_at` set to the message's own timestamp, and `## Summary` regenerated with real content for that first message.
- A later message in the SAME conversation never creates a second note — `## Summary` is regenerated fresh (whole-region replace, no residue of the prior version), `## Transcript` grows by one new entry, tags are UNIONED (never removed/overwritten), `participants` grows to include any new sender not already present, `last_message_at` is overwritten to the new message's own timestamp.

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — add `thread_match_merge`, placed near the top of the file, above `classify_recent_emails` (or its eventual replacement, see `T08`).

---

## Constraints

- Inherits from parent story: `## Summary` regeneration goes ONLY through `replace_body_section`; `## Transcript`/`## Attachments` growth goes ONLY through `T01`'s new header-scoped append primitive — never a raw file write, never `insert_body_line_if_missing`.
- Tags accumulate (unioned), never pruned, on every update — read the Thread's own CURRENT tags via `read_note` first, union with this message's own `build_tags(customer, kind)`-derived tags, write the union back via `T01`'s frontmatter setter. A tag present on an earlier message must never disappear from a later regeneration.
- `customer` is written once (first message) and never contradicted later in this task's own scope — if a later message's own classification disagrees on `customer`, do not overwrite it (out of scope; log as a disclosed limitation if encountered, not a locked-AC gap — no Scenario in this story tests a mid-conversation customer reclassification).
- `participants`/`last_message_at` are written on EVERY call (create AND update) via `T01`'s unconditional setter — never `insert_frontmatter_key_if_missing` (which would silently no-op on the second and every later message).
- `Thread-Match/Merge` calls `customer_hub_linking.ensure_customer_hub_note(customer)` ONLY — never `ensure_hub_note_and_link`'s inline-body-wikilink half (`ADR-043` Consequences: that convention is superseded by the OKF concept file's own `sources:` field, populated at synthesis time, `REQ-SB-57`, out of this story's scope). Do not write any inline `**Customer:** [[Hub]]` wikilink into the Thread's own body.
- Must remain a plain, LangGraph-ignorant function — ordinary Python data in (`email`/`classification`/`attachment_entries` dicts/lists), ordinary Python data out. No LangGraph import, no graph-state dict parameter.
- `attachment_entries` (a list of dated summarized sub-entry strings, `T05`'s own output shape) is `None`/`[]`-safe — when there are none, `## Attachments` is left completely untouched (never created empty) for that pass.
- Do not modify `create_thread_note_baseline`/`ensure_thread_note_baseline_frontmatter`/`replace_body_section`/`thread_note_path` — compose them as-is.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-55-US-01-AC-01]** Against a throwaway scratch vault, call `thread_match_merge(email_1, classification_1)` for a synthetic first message (`conversation_id="test-conv-thread-1"`). Confirm exactly one Thread note now exists at `thread_note_path("test-conv-thread-1")`, with `type: "Thread"`, `customer`/`tags` set from `classification_1`, `participants` containing the first message's sender, `last_message_at` set, and `## Summary` containing real content (not the empty placeholder). Confirm the return dict's `created` is `True`. Call `thread_match_merge(email_2, classification_2)` for a SECOND synthetic message with the SAME `conversation_id` — confirm `thread_note_path` resolves to the exact SAME path (no second file), `created` is `False` this time, `## Summary` now reflects ONLY the regenerated content (no residue of the first version's exact wording, confirming a real whole-region replace occurred), and `## Transcript` contains entries for BOTH messages, in order.
2. **[REQ-SB-55-US-01-AC-02]** Call `thread_match_merge(email_2, classification_2, attachment_entries=["2026-08-16 — invoice.pdf: <a real, non-trivial summary sentence>"])` for a message with a real attachment sub-entry. Confirm `## Attachments` now exists, containing that exact dated sub-entry, and confirm `## Summary`'s own regenerated text does NOT contain the attachment's own summary content merged in — the two stay separate, distinct records.
3. **[REQ-SB-55-US-01-AC-07]** Before the second `thread_match_merge` call above, record the Thread's own `tags` value. Call `thread_match_merge` for a later message whose `classification`'s own `kind`/`customer` produce at least one NEW tag not already present, plus at least one tag that OVERLAPS with an already-present one. Confirm the resulting `tags` list contains the UNION (old tags + the one genuinely new tag, no duplicates from the overlapping one) and confirm no previously-present tag was removed.
4. Confirm `participants` accumulates correctly: call `thread_match_merge` for a third synthetic message in the same conversation with a DIFFERENT sender than either prior message — confirm `participants` now includes all three distinct senders (not just the latest), and confirm `last_message_at` reflects this third message's own timestamp (the most recent), not an earlier one.
5. Confirm `customer_hub_linking.ensure_customer_hub_note` was called (the Customer's own OKF directory skeleton exists after this task's first call) and confirm NO inline `**Customer:** [[...]]` wikilink line was written into the Thread note's body at any point.
6. Regression check: confirm `classify_recent_emails` (still the live, unmodified email path until `T08`) and `REQ-SB-54-US-01`'s own Thread/Customer primitives are byte-for-byte unaffected by this addition.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — two messages in the same conversation produce exactly ONE Thread note; the first creates it, the second regenerates `## Summary` and grows `## Transcript`.
- [x] **AC-02** (Scenario 2, the write half) — an attachment sub-entry lands in its own `## Attachments` region, kept separate from the regenerated `## Summary`.
- [x] **AC-07** (Scenario 7) — tags union across updates; nothing previously present is ever removed.
- [x] `customer`/`participants`/`last_message_at` are all correctly written/updated on every call.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Deciding WHETHER to call `Route-to-Project` — this function only reports `created` in its return value; the conditional graph routing is `T07`'s own job.
- Producing the attachment sub-entry text itself — `T05`'s own job; this task only writes whatever it's handed.
- Writing the `project` frontmatter key — `T04`'s own `finalize_thread_project_routing` approval handler writes it, using `T01`'s same frontmatter setter, once the routing Pending Approval resolves.
- Mid-conversation customer reclassification — explicitly out of this story's own scope (see Constraints).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-043` points 1, 3, 7; `Implementation/Architecture/architecture.md` → "Email Capture & Threading Pipeline — First Concrete Pipeline". Real precedent to mirror for the read-union-write tag pattern: `build_tags`'s own shape (`vault_writer.py`), and this codebase's own "regenerate vs. accumulate" split already established for Thread's `## Summary` (regenerate) vs. `## Transcript` (accumulate) in `REQ-SB-54-US-01-T02`.

---

## Implementation Log

**2026-08-16, coder pass.**

Added exactly two symbols to `src/backend/app/business/email_classification.py`,
placed above `classify_recent_emails` per this task's own Files to Modify
instruction (nothing else in this file touched):

- `_build_thread_summary_content(email) -> str` — private helper building the
  deterministic, non-LLM regeneration content for `## Summary` (this Job
  never makes a second Compass call, per the parent story's own Constraint,
  so there is no LLM-abstracted summary to compose here — that is
  `REQ-SB-57`'s own future Glimpse-synthesis scope). Renders the LATEST
  message's own `received`/sender/`subject`/`body`, deliberately never a
  `**Customer:**`-labeled line (see judgement call below).
- `thread_match_merge(email, classification, attachment_entries=None) -> dict`
  — the `Thread-Match/Merge` Job. `created = not vault_writer.
  thread_note_exists(conversation_id)`; resolves `path` via `vault_writer.
  thread_note_path(conversation_id)` (a `Path`) rather than
  `create_thread_note_baseline`'s own return value (a plain `str`, per
  `write_note`'s contract — see judgement call below) so every later
  primitive call composes against the same object type. On `created`:
  calls `create_thread_note_baseline(conversation_id, tags=build_tags(
  customer, kind))`, then writes `customer` ONCE via `upsert_frontmatter_key`
  (never again on a later call, per this task's own Constraint). On EVERY
  call: reads the Thread's current frontmatter (`read_note`), unions this
  message's own `build_tags(customer, kind)` onto the existing `tags` list
  (dedup, order-preserving, nothing removed) and writes it back via
  `upsert_frontmatter_key`; accumulates the sender
  (`email["sender_email"] or email["sender_name"]`) into `participants` if
  not already present; unconditionally overwrites `last_message_at` to
  this message's own `received` value (never
  `insert_frontmatter_key_if_missing`, which would silently no-op on every
  later message); grows `## Transcript` by one dated line via `T01`'s
  `append_body_section_line`; folds each `attachment_entries` string into
  `## Attachments` via the same primitive (loop is a true no-op — `##
  Attachments` is never created — when the list is `None`/`[]`); fully
  regenerates `## Summary` via `replace_body_section`; calls
  `customer_hub_linking.ensure_customer_hub_note(customer)` only (never
  `ensure_hub_note_and_link`'s inline-wikilink half). Returns
  `{"thread_path": str(path), "created": bool, "conversation_id": str,
  "customer": str}`.

**Two scope-internal judgement calls, logged for human spot-check (not
escalations — neither contradicts `ADR-043`/the PRD/a `MEMORY.md`
constraint, both are implementation-detail decisions the task file itself
left to the coder):**

1. **`create_thread_note_baseline`'s own return value cannot be passed
   directly to `replace_body_section`/`append_body_section_line`/
   `upsert_frontmatter_key`/`read_note`** — it returns a plain `str`
   (`write_note`'s own contract), while every one of those four primitives
   calls `path.read_text(...)`/`path.write_text(...)` and requires a real
   `Path` object. Confirmed live (first attempt raised
   `AttributeError: 'str' object has no attribute 'read_text'`). Fixed by
   resolving `path = vault_writer.thread_note_path(conversation_id)` once,
   up front, and using that same `Path` for every subsequent call — which
   is also exactly what `create_thread_note_baseline`'s own docstring
   already documents as the intended pattern ("a later message... instead
   regenerates `## Summary` via `replace_body_section`... directly against
   the same path `thread_note_path()` already resolves"). No primitive was
   modified.
2. **`## Summary`'s exact regenerated wording is this task's own design
   choice, not specified by `ADR-043`/`architecture.md`** — deliberately
   built as a plain, deterministic rendering of the LATEST message only
   (timestamp/sender/subject/body), not a cumulative or AI-abstracted
   synthesis (out of scope — no compass call is available to this
   function, and `REQ-SB-57` owns real Glimpse-style synthesis later).
   First draft included a `**Customer:** {customer}` label line inside
   `## Summary`, which on live verification tripped this task's own
   Constraint check for "no inline `**Customer:** [[...]]` wikilink" — on
   inspection it was NOT actually the forbidden pattern (no `[[wikilink]]`,
   pure plain-text metadata), but close enough to the prohibited shape to
   be a real footgun for a future reader/regex-based check. Removed
   entirely rather than kept-but-argued-safe — `customer`/`kind` already
   live in the Thread's own frontmatter, so the label added no information
   the Summary needed.

**Verification (manual mode — no automated test stack exists yet for this
backend; real backend `.venv`, `VAULT_PATH` env-overridden to a
`tempfile.mkdtemp()` scratch vault, the real configured vault never
touched, per this codebase's own established `T01`/`T02` protocol — script
+ full transcript kept in this session's own scratchpad, not committed):**

1. **[`REQ-SB-55-US-01-AC-01`]** `thread_match_merge(email_1, classification_1)`
   for a synthetic first message (`conversation_id="test-conv-thread-1"`)
   — observed exactly one Thread note at `thread_note_path(...)`, `type:
   "Thread"`, `customer: "Acme Corp"`, `tags` == `build_tags("Acme Corp",
   "Emails")`, `participants == ["alice@acme.example"]`, `last_message_at
   == "2026-08-16 09:00:00"`, `## Summary` containing the first message's
   own real body text (not the empty placeholder), return dict's
   `created is True`. Called `thread_match_merge(email_2, classification_2)`
   for a SECOND message, SAME `conversation_id` — observed `thread_path`
   resolves to the exact SAME path (directory listing confirmed exactly
   one `.md` file both before and after), `created is False`, `##
   Summary` now contains ONLY the second message's own wording (the first
   message's own exact phrase, `"here is the initial scope for Project
   Alpha"`, confirmed ABSENT from the regenerated body — a real
   whole-region replace, not residue), and `## Transcript` contains both
   messages' own subject lines in call order (first message's subject
   index < second message's subject index in the raw transcript region
   text). **PASS.**
2. **[`REQ-SB-55-US-01-AC-02`]** `thread_match_merge(email_3, classification_3,
   attachment_entries=["2026-08-16 — invoice.pdf: Invoice #4471 for Acme
   Corp, total $12,450.00, due 2026-09-15."])` — observed `## Attachments`
   now exists containing that exact dated sub-entry, and the regenerated
   `## Summary` region's own text does NOT contain `"Invoice #4471"` — the
   two stayed separate, distinct records. **PASS.**
3. **[`REQ-SB-55-US-01-AC-07`]** Recorded the Thread's own `tags` before a
   4th call (`{"customer/acme-corp", "kind/emails"}`). Called
   `thread_match_merge` for a 4th message whose `classification`'s own
   `kind="Reports"` (customer unchanged) — `build_tags("Acme Corp",
   "Reports")` produces one genuinely NEW tag (`"kind/reports"`) and one
   OVERLAPPING tag (`"customer/acme-corp"`). Observed resulting `tags` is
   the exact union — old tags still present, `"kind/reports"` now present,
   no duplicate of the overlapping tag, no previously-present tag removed.
   **PASS.**
4. Called `thread_match_merge` for a 3rd distinct sender
   (`carol@acme.example`) in the same conversation — observed
   `participants == ["alice@acme.example", "bob@acme.example",
   "carol@acme.example"]` (all three, not just the latest), and
   `last_message_at` reflects this 3rd/most-recent message's own timestamp
   (`"2026-08-16 16:00:00"`), not an earlier one. **PASS.**
5. Confirmed `vault_writer.customer_concept_file_exists("Acme Corp")` is
   `True` after the very first `thread_match_merge` call (the Customer's
   own OKF directory skeleton exists via `ensure_customer_hub_note`), and
   confirmed the literal string `"**Customer:** [["` (the forbidden
   inline-wikilink shape) is absent from the Thread note's own raw file
   text at every point across all 4 calls. **PASS.**
6. Regression check: `classify_recent_emails`'s own function body is
   byte-for-byte unmodified by this task's edit (confirmed via the `Edit`
   tool's own exact-`old_string`-match contract — the new code was
   inserted purely ABOVE `classify_recent_emails`, no existing line
   touched) and no file outside `## Files to Modify` was written to this
   session (`vault_writer.py`/`customer_hub_linking.py`/`REQ-SB-54-US-01`'s
   own Thread/Customer primitives were only READ, never edited).
   `ast.parse()` of the full `email_classification.py` file after this
   edit succeeded with no syntax error.

**Acceptance criteria verified:**

- **AC-01** (Scenario 1) — **Verified**, step 1 above.
- **AC-02** (Scenario 2, write half) — **Verified**, step 2 above.
- **AC-07** (Scenario 7) — **Verified**, step 3 above.
- `customer`/`participants`/`last_message_at` correctly written/updated on
  every call — **Verified**, steps 1/3/4 above.

No `ESCALATIONS.md` entry — nothing here contradicts an `Accepted` ADR, the
PRD, or a `MEMORY.md` constraint; the two judgement calls above are
scope-internal implementation-detail decisions the task file itself left
open, logged inline for human spot-check per this task's already-standing
`gate: flagged` (trigger-3, `ADR-043`). No new `REVIEW-QUEUE.md` entry
either — the task's already-flagged gate already carries it into the
existing human-review pass.
