---
id: BUGFIX-03-US-01
title: Thread email attachments are actually captured, saved, and collision-safe (BUG-014 fix)
requirement_ids: [BUG-014]
requirement_section: "BUGS.md → BUG-014"
status: Done
gate: flagged
gate_reason: "ESC-043 opened by T02's own verification pass (shared-interface-change, non-blocking to this story's own DoD): the gap-2 fix T02 built is exactly the story's own adopted design, both locked ACs (AC-01, AC-02) verified live and passing, but the fix has a real, previously-unconsidered consequence for app/business/cockpit/attachments.py (an out-of-scope file) -- see ## Notes and ESCALATIONS.md -> ESC-043. Does not block this story's own Done status; recommends a separate /bug capture."
sprint: "SPRINT-055"
created: 2026-08-17
updated: 2026-08-17
---

# BUGFIX-03-US-01 — Thread email attachments are actually captured, saved, and collision-safe (BUG-014 fix)

## Story

**As a** Second Brain user reading a captured Thread note in Obsidian
**I want** a real email attachment sent into a Thread to actually be saved
to the vault, summarized, and linked from the Thread note's own
`## Attachments` section — and, when two different messages in the same
Thread happen to carry same-named attachments (e.g. recurring
`image001.png` signature images), for BOTH to survive intact rather than
one silently overwriting the other
**So that** the `Summarize-Attachment` Job (`REQ-SB-55-US-01`) actually
does what it was built to do, and a Thread's attachment history is never
silently lossy

## Context

- Bug ledger: `BUGS.md` → `BUG-014` — "Thread email attachments are never
  captured, and the underlying save path has no filename-collision
  protection" (Logic, Major, `Open` at triage time).
  - **Repro:** send/receive a real email with a genuine attachment into an
    Outlook conversation the email-capture pipeline processes, let it
    capture (scheduled tick or manual `run_capture_now`), then check the
    resulting Thread note (`Work/Threads/<conversation-id>.md`) for a
    `## Attachments` section and `Work/Threads/attachments/` on disk.
  - **Expected (BUG-014's own text):** the attachment is saved under
    `Work/Threads/attachments/<thread-slug>/...`, summarized, and appears
    as a dated sub-entry under a `## Attachments` section on the Thread
    note, per `REQ-SB-55-US-01`'s own `Summarize-Attachment` Job design.
  - **Actual, confirmed live against real vault data, 2026-08-17:** a real
    captured Thread (`01D26A7530444A23803A002210620160.md`) whose own
    source email body literally reads "Please find attached a short
    presentation..." has NO `## Attachments` section at all, and
    `Work/Threads/attachments/` does not exist anywhere in the vault. This
    live observation is not in dispute — it is the bug's own regression
    condition this story's Scenario below must close.
  - **BUG-014's own stated root cause for this (gap 1):** "`outlook_com.py`
    never reads a `MailItem`'s `Attachments` COM collection at all — the
    word 'attachment' does not appear anywhere in that file,"
    making `email_capture_pipeline.py::_summarize_attachment_node`'s
    `for attachment in email.get("attachments") or []:` loop always empty.
  - **BUG-014's own second, independently-confirmed defect (gap 2, not in
    dispute):** `vault_writer.py::write_attachments` (line ~484) writes
    `attachments_dir / filename` and calls `file_path.write_bytes(...)`
    with **no existence check, no collision handling of any kind** —
    confirmed by this triage pass's own direct re-reading (lines 464-494):
    the function unconditionally overwrites on a same-filename collision.
    Real, likely-frequent risk for Threads specifically: corporate emails
    routinely carry generically-named inline signature/logo images
    (`image001.png`, etc.) that recur across nearly every message in a
    multi-message thread, and today's flat
    `attachments/<thread-slug>/<filename>` layout (confirmed live:
    `email_classification.py::summarize_attachment` calls
    `vault_writer.write_attachments(subfolder="Work/Threads",
    note_stem=conversation_id, ...)` — one flat folder per Thread, not one
    per message) would silently clobber one with the other. This directly
    contradicts the collision-handling convention `vault_writer.py`
    already establishes one function below
    (`move_note_and_attachments`: "Refuses to silently overwrite an
    existing file at the destination — a genuine collision should surface,
    not disappear one of the two notes").

- **Analyst re-verification, 2026-08-17 (this triage pass) — gap 1's
  stated root cause does NOT hold against the current live code; flagged,
  not silently trusted or silently rewritten.** Direct reading of
  `src/backend/app/data_access/outlook_com.py` (not guessed) found:
  - `_extract_attachments(item)` (lines ~160-194) is a full, real COM
    `Attachments`-collection reader — the exact "save-to-temp-file, read
    the bytes, delete the temp file" technique BUG-014's own recommended
    fix direction describes wanting built. It filters out inline
    signature/logo images via `_is_inline_attachment` and returns
    `{"filename", "content", "size"}` dicts, capped at
    `_MAX_ATTACHMENT_BYTES` (oversized → `content: None`, same "recorded,
    not silently dropped" precedent `write_attachments` already expects).
  - `list_recent_mail()` (lines 197-231) — the SAME fetch function both
    the legacy `email_classification.classify_recent_emails` and the new
    `pipelines.email_capture_pipeline.run_email_capture_pipeline` call —
    already includes `"attachments": _extract_attachments(item)` on every
    returned email dict (line 220).
  - The word "attachment" (case-insensitive) appears **15 times** in
    `outlook_com.py` today, not zero.
  - This is not new/uncommitted-just-now code: `CHANGELOG.md`'s own
    history places basic attachment extraction ("email/file-share
    attachments are saved into `attachments/<note>/`... 20MB cap,
    oversized files recorded but not written") among the very earliest
    features of this project, well before `REQ-SB-55`'s Thread pipeline
    (`SPRINT-049`) existed — `list_recent_mail`'s attachment population is
    old, foundational plumbing, not something this triage pass just
    happened to catch mid-edit.
  - The live production call chain was traced end-to-end, not assumed:
    `capture_scheduler.py::run_capture_if_idle` →
    `email_classification.run_capture_and_record_completion` (its own
    docstring confirms the email step "now dispatches... to
    `pipelines.email_capture_pipeline.run_email_capture_pipeline`") →
    `outlook_com.list_recent_mail`. The new Thread pipeline is genuinely
    the live path, and it genuinely receives a populated `"attachments"`
    key from `list_recent_mail` today.
  - **What this means, and what it does NOT mean:** it does NOT mean
    `BUG-014` is invalid — the live observed symptom (a real Thread note
    with a real "please find attached" email and zero `## Attachments`
    section / zero `attachments/` folder) is confirmed and unexplained by
    this finding alone. It DOES mean the specific mechanism BUG-014 names
    for gap 1 is wrong, so a fix built literally to that description (e.g.
    "add `Attachments` COM reading to `outlook_com.py`") would be
    redundant work that does not actually close the real symptom. The true
    cause is now genuinely open — candidates include (not decided here):
    (a) the specific Thread note used in the repro predates whatever
    fetch/pipeline wiring is live today and was never reprocessed; (b)
    `_extract_attachments`'s own broad `except Exception: return
    results`/`except Exception: continue` guards could be silently
    swallowing a real per-item or per-attachment COM failure with zero
    logging, on some real emails but not others; (c) `_is_inline_attachment`
    misclassifying a real (non-signature) attachment as inline for that
    specific email; (d) some other cause not yet found. None of these can
    be distinguished by static reading alone — see `## Notes` and
    `ESCALATIONS.md` → `ESC-041`.
  - Gap 2 (no collision protection) has NO such contradiction — this
    triage pass's own direct reading fully confirms it exactly as
    `BUG-014` describes.

- **Recommended fix direction (BUG-014's own text, adopted as this
  story's own direction for gap 2 — see Constraints):** nest attachment
  storage one level deeper per message —
  `attachments/<thread-slug>/<message-date-or-id>/<filename>` instead of
  today's flat `attachments/<thread-slug>/<filename>` — rather than a
  rename/hash-check scheme, matching the existing "dated sub-entry per
  attachment" convention `summarize_attachment` already uses in the
  Thread body. The exact per-message identifier and how
  `write_attachments`'/its caller's signature changes to carry it are
  architecture-level details left to `/plan-tasks`, not decided here.

- No `html-prototype/` screen applies — like `BUGFIX-01-US-01`, this is
  backend/vault-content work with no application UI surface.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then) by the analyst; the
decomposer locks and AC-IDs this at /plan-tasks. One scenario, two
sequential facets — mirrors BUGFIX-02-US-01's own "one scenario, two
When/Then facets for one bug" precedent — since both facets are aspects of
the same BUG-014 regression criterion (a Thread's attachments are actually
captured AND never silently clobber each other). Phrased around the
OBSERVABLE outcome BUG-014's own Expected text names, not around the
specific (contradicted, see Notes) gap-1 mechanism, so this scenario is a
valid regression criterion regardless of what the true gap-1 cause turns
out to be. -->

### Scenario 1: A Thread's real email attachment is captured, saved, and linked

```gherkin
Given a real Outlook email with at least one genuine (non-inline) file
    attachment arrives in a conversation the email-capture pipeline
    processes
When the pipeline captures that email (scheduled tick or a manual
    run_capture_now trigger)
Then the attachment's own bytes are saved to disk under
    Work/Threads/attachments/<thread-slug>/...
  And the resulting Thread note (Work/Threads/<conversation-id>.md) gains
    a ## Attachments section containing a dated sub-entry naming that
    attachment
```
<!-- AC-ID: BUGFIX-03-US-01-AC-01 -->

### Scenario 2: Two different messages in the same Thread never collide on a shared attachment filename

```gherkin
Given a Thread already has one message's own genuine attachment saved and
    linked, per Scenario 1
When a second, later message in that SAME Thread arrives carrying its own
    genuine attachment whose filename is identical to the first message's
    attachment (e.g. two distinct real image001.png files with genuinely
    different content, one per message — the realistic recurring-
    signature-image case)
Then both attachments' own distinct content survives on disk intact
  And neither attachment's saved file is silently overwritten by the
    other
  And the Thread note's ## Attachments section gains a second, separate
    dated sub-entry for the second message's own attachment
```
<!-- AC-ID: BUGFIX-03-US-01-AC-02 -->

<!-- Decomposer pass, /plan-tasks step 2, 2026-08-17: split the analyst's
one scenario into two locked ACs (tightened wording only — "per Scenario 1"
added to AC-02's Given, otherwise verbatim), since AC-01 and AC-02 are
verified together in ONE continuous live capture session (T02's Tests
section) but map to two structurally distinct owning fixes (AC-01 needs
T01's gap-1 honest-signal restore; AC-02 additionally needs T02's own gap-2
per-message nesting) — mirrors this story's own Notes explicitly inviting
either a single AC or a split, and BUGFIX-01-US-01's own precedent of
splitting one analyst scenario into multiple locked ACs. -->

## Affected Screens

None — backend/vault-content only. No `html-prototype/` screen exists or
is needed for this fix; Obsidian's own note body/file-explorer views are
the surface this change affects, not a Second Brain application screen.

## Dependencies

- **Blocked by:** none. `REQ-SB-55-US-01` (Email Capture & Threading
  Pipeline, `Done`, `SPRINT-049`) already built the `write_attachments`
  primitive, the `summarize_attachment` Job, and the Thread pipeline this
  fix extends — this story does not depend on any not-yet-built story.
- **Related to:** `REQ-SB-55-US-01` — this fix closes the gap in its own
  `Summarize-Attachment` Job design.
- **Related to (NOT the same defect):** `BUG-011` — a different,
  already-`Open` `_slugify`-truncation collision bug affecting
  `Work/Tasks/`'s flat note-filename stems. `BUG-014`'s gap 2 is a
  different collision (attachment filenames within one Thread's own
  attachments folder, via `write_attachments`, not `_slugify`) — mentioned
  here only so the two aren't conflated; not part of this story's own
  scope.
- **External:** none new. Verification of gap 1's true cause and the fix
  itself will need to run against the user's real, live Outlook/vault
  configuration (`VAULT_PATH`), not a fixture/test vault — same as every
  other capture-pipeline bugfix in this project.

## Constraints

- **Gap 1's true cause must be re-confirmed by direct investigation before
  it is "fixed"** — do not build a change to `outlook_com.py`'s
  `Attachments`-reading mechanism on the strength of `BUG-014`'s own
  stated root cause alone; this story's own Notes/Context above directly
  contradict it via live code reading. A live capture run against a real
  email with a known, non-inline attachment (with logging/inspection
  added at each hand-off point if needed — fetch → `_summarize_attachment_
  node` → `summarize_attachment` → `write_attachments`) is the concrete
  next step to find the real point of loss, not a guess.
- **Gap 2's fix direction is adopted, not open:** nest attachment storage
  one level deeper per message (`attachments/<thread-slug>/
  <message-date-or-id>/<filename>`), per `BUG-014`'s own recommended
  direction — not a rename/hash-check scheme. The exact per-message
  identifier and the resulting signature change to `write_attachments`/its
  caller are an architecture-level detail for `/plan-tasks`.
- Must not regress the existing, correct single-attachment / single-
  message Thread case — a Thread with only one message and one attachment
  (no collision to protect against) must still produce the same saved
  file + `## Attachments` dated sub-entry it does today once gap 1 is
  genuinely closed.
- Must not weaken `write_attachments`'s own existing oversized-attachment
  precedent (`content is None` → recorded with `"saved": False`, never
  written) — that path is unrelated to filename collision and must stay
  intact.
- This work runs against the user's real, live Obsidian vault and real
  Outlook mailbox, not a fixture/test vault — no-data-loss (never
  silently overwrite a real attachment) is load-bearing, not a
  convenience, per `BUG-014`'s own severity (Major).

## Implementation Tasks

<!-- Analyst's own starting-point table — expect the decomposer to
supersede/expand this at /plan-tasks, especially T01, once gap 1's real
cause is confirmed live. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| BUGFIX-03-US-01-T01 | backend | Restore the honest-signal fallback in `_summarize_attachment_node` (gap 1 — closes the real, confirmed silent-loss mechanism, `ESC-041` resolved); live-diagnostic sub-step on the historical Thread | `app/business/pipelines/email_capture_pipeline.py` | `../Tasks/BUGFIX-03-US-01-T01-restore-honest-attachment-fallback-signal.md` |
| BUGFIX-03-US-01-T02 | backend | Nest `write_attachments`' save path one level deeper per message (new required `message_segment` param); wire both call sites; live end-to-end verification of AC-01 + AC-02 | `app/data_access/vault_writer.py`, `app/business/email_classification.py` | `../Tasks/BUGFIX-03-US-01-T02-per-message-attachment-nesting.md` |

## Definition of Done

- [x] The acceptance-criteria scenario passes (verified live: a real
      captured attachment appears saved + linked; two same-named
      attachments from different messages in the same Thread both survive
      intact)
- [x] Every Implementation Task above is complete (or explicitly dropped
      with reason)
- [x] All Constraints respected — including gap 1's true cause being
      re-confirmed live, not assumed from `BUG-014`'s own text
- [x] Automated tests added/updated and passing (once test tooling
      exists) — n/a today; manual mode per Pipeline.md
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] `BUG-014` flipped `In Sprint → Closed` in both `BUGS.md` and
      `BACKLOG.md`'s `## Bugs` mirror once this story is `Done`

## Non-Goals / Out of Scope

- `BUG-011` (`_slugify` 80-char-truncation collision in `Work/Tasks/`'s
  flat folder) — a different, already-`Open` bug against a different
  subsystem; not addressed by this story.
- Any change to `summarize_attachment`'s own text-extraction/summarization
  behaviour, or to `compass_client.summarize_content` — this story only
  concerns whether/how an attachment's bytes reach disk and stay
  collision-safe, not how it is subsequently summarized.
- Retroactively backfilling attachments for already-captured Thread notes
  that were processed while gap 1 was live (e.g. re-scanning historical
  mailbox items for attachments already missed) — out of scope unless the
  human/architect explicitly asks for a retrofit pass once gap 1's real
  cause is confirmed; not assumed here.
- Operator-directed bundling of this story into `REQ-SB-68-US-01`'s own
  sprint — a `/plan-sprints` decision, not made by this story or this
  triage pass (per the operator's own explicit instruction this session).

## Notes

**Prototype parity:** not applicable — this story has no screen surface,
same as `BUGFIX-01-US-01`.

**Why one scenario, two facets:** per the triage-mode contract, one
untagged Gherkin scenario per bug in the batch — this batch is `BUG-014`
only. Its two `When` blocks (capture-and-save, then collision-safety
across two messages) are two facets of the same regression criterion
`BUG-014` itself names (a Thread's attachments are actually captured, and
never silently overwrite each other) — mirrors `BUGFIX-02-US-01`'s own
precedent of one scenario with sequential `When`/`Then` facets for one
bug. The decomposer may split this into two locked ACs at `/plan-tasks` if
that reads more verifiable, same as `BUGFIX-01-US-01`'s own precedent of
splitting one analyst scenario into multiple locked ACs.

**Why this story is `gate: flagged` (trigger 7 — contradictory inputs):**
`BUG-014`'s own stated root cause for gap 1 — "the word 'attachment' does
not appear anywhere in that file" (`outlook_com.py`) — is directly
falsified by this triage pass's own direct re-reading of the current live
code: the word appears 15 times, `_extract_attachments()` is a full,
real COM-Attachments reader, and `list_recent_mail()` already populates an
`"attachments"` key consumed by the exact live production call chain
`BUG-014` names as broken. This is not a case where "the fix's design is
already fully resolved, confirmed via direct code reading" (as this
story's own triage brief characterized it) — a genuinely material,
unresolved contradiction exists between the bug ledger's own investigation
and the real code, and per Pipeline.md trigger 7/8 this is flagged rather
than guessed past. Gap 2 (no collision protection) has no such
contradiction and is fully, independently confirmed — only gap 1's
mechanism is in question, not gap 2's, and not the bug's own live-observed
symptom (a real Thread genuinely missing its attachment), which stands
unexplained but real. See `ESCALATIONS.md` → `ESC-041` for the full
write-up and `REVIEW-QUEUE.md` for the pointer. This does NOT block
authoring this Draft story — the scenario above specs the observable
outcome `BUG-014` itself demands, which remains a valid target regardless
of which exact mechanism turns out to be the true gap-1 cause; it DOES
mean a human should look at `ESC-041` before `/plan-tasks` decides T01's
concrete fix, so the architect doesn't build a fix against a false
premise.

gate: flagged 2026-08-17 — trigger 7 fired (contradictory inputs: BUG-014's
own gap-1 root-cause claim vs. the current live code). No other trigger
fired independently: no ADR created/changed (analyst scope); `BUG-014` is
a finalised, non-`Draft` bug-ledger entry (trigger 2 doesn't apply); gap
2's fix direction has one clearly-adopted answer (BUG-014's own
recommendation, matching an existing in-file convention) — not itself a
multiple-equally-valid fork; the story is small and well-bounded (one
existing fetch/pipeline chain to re-diagnose, one existing save primitive
to extend) — not oversized.

---

**Architect pass, `/plan-tasks` step 1, 2026-08-17 — ESC-041 resolved,
architecture scope recorded.**

**Architecture scope:** `Implementation/Architecture/architecture.md` →
"Email Capture & Threading Pipeline — First Concrete Pipeline" (REQ-SB-55)
and the new "Thread Attachment Capture — Silent-Loss Fix + Per-Message
Collision Safety" subsection (`BUGFIX-03-US-01`, appended directly below
it). The coder's T01/T02 work is bounded to those two sections plus the
files they name: `app/business/pipelines/email_capture_pipeline.py`
(`_summarize_attachment_node`), `app/business/email_classification.py`
(`summarize_attachment`), and `app/data_access/vault_writer.py`
(`write_attachments`).

**Root-cause investigation — the real gap-1 mechanism (resolves
`ESC-041`), NOT `BUG-014`'s own originally-stated one:** Direct reading of
the live `Summarize-Attachment` Job chain end-to-end
(`_summarize_attachment_node` → `summarize_attachment` →
`write_attachments`) finds: `_summarize_attachment_node` only appends an
entry into `attachment_entries` (and therefore only ever gets a
`## Attachments` line written by `thread_match_merge`) when
`summarize_attachment` returns a real `dated_entry` string — produced
ONLY on a fully successful save-then-summarize path. Every other real
outcome for a genuinely-attached, non-inline file — an oversized
attachment (`outlook_com.py`'s own `_MAX_ATTACHMENT_BYTES = 20MB` cap
already sets `attachment["content"]` to `None` before `write_attachments`
ever sees it), a saved-but-non-text-extractable file type, or a real
`compass_client.CompassError` during summarization — collapses to a
`summary_error` key `_summarize_attachment_node` silently discards: no
exception, no log, no fallback entry. For the oversized case specifically,
`vault_writer.write_attachments`'s own `.mkdir()` call sits INSIDE the
per-attachment `if attachment["content"] is None` early-continue branch
(confirmed by direct reading, lines ~478-483) and is never reached — the
whole `attachments/<thread-slug>/` directory itself never comes into
existence. **This single, confirmed mechanism independently explains
BOTH of `BUG-014`'s own live-observed symptoms** (the real captured
Thread's missing `## Attachments` section AND its missing `attachments/`
folder anywhere in the vault) from one cause, with no unverifiable claim
about Outlook's own COM behavior needed.

**Corroborating evidence (not just structural code reading):** the
still-live sibling path, `classify_recent_emails` (dead code for the live
Thread pipeline, but real, unmodified, and still reachable via
`/poc/classify-emails`), already carries an honest fallback line for
exactly this case — `f"- {att['filename']} (not saved — {att['size']}
bytes exceeds the size cap)"`. This proves "record an unsaved
attachment's own existence anyway" was already an established convention
in this codebase BEFORE the new Thread pipeline shipped.
`REQ-SB-55-US-01-T05`'s own `summarize_attachment` Job deliberately chose
not to fabricate a `dated_entry` for a failed real summary (correct,
per `MEMORY.md`'s 2026-08-16 entry — "`summary_error` was chosen as the
equivalent honest signal") but no downstream node/function was ever built
to actually surface `summary_error` into a visible Thread-note artifact —
the "equivalent honest signal" was designed at the Job level but never
wired at the pipeline/node level. **This is the real, confirmed
regression: not "an attachment is never extracted," but "an attachment
that fails to save or summarize for ANY reason vanishes from the Thread
note without a trace" — an already-established convention the new
pipeline lost, not a never-built feature.**

**What remains genuinely unconfirmed — folded into `T01`'s own
live-verification scope, not blocking this design (per this story's own
Constraint and `REQ-SB-56-US-01-T00`'s precedent):** which real-world
variant explains the SPECIFIC "Presight Agent Academy Demo" Thread's own
historical repro:
  - (a) the real attachment's own byte size genuinely exceeded the 20MB
    cap — most probable given a presentation file with embedded
    media/images, but not provable from code alone;
  - (b) it was actually a OneDrive/SharePoint cloud-attachment link,
    which modern M365-signed-in Outlook's own "Attach File" flow can
    insert as a body hyperlink rather than a real `Attachments`-collection
    entry (Outlook's own behavior, not a defect in this codebase) —
    needs a live `item.Attachments.Count` read against the real message
    to confirm or rule out;
  - (c) the specific message was processed once via a direct,
    pre-`T07`-pipeline-wiring dev-verification call during `SPRINT-049`'s
    own same-day build-out (`thread_match_merge` shipped at `T03`,
    `summarize_attachment` at `T05`, the two only wired together by
    `T07`) — `vault_writer.mark_email_processed` is called ONLY by
    `run_email_capture_pipeline`'s own per-tick loop, never by any Job
    function directly, so a message captured once outside that loop
    during development, then later revisited by a real tick as a
    Thread-`update` (`created: False`), is structurally indistinguishable
    from (a)/(b) by static reading;
  - (d) a real, silently-swallowed per-attachment COM read failure inside
    `outlook_com.py::_extract_attachments`'s own broad
    `except Exception: continue`/`except Exception: return results`
    guards, which log nothing on failure.

  None of (a)-(d) changes the fix's own design below — each is already
  covered by the SAME honest-signal mechanism this fix restores — so this
  architecture pass proceeds on the strength of the confirmed,
  code-read mechanism above, without blocking on a live check I have no
  tool-set access to perform myself (no COM/live-Outlook capability
  available to this agent). `T01` should carry a live-diagnostic
  verification sub-step (log/inspect at each hand-off point per this
  story's own Constraint, and/or a direct live COM read of the real
  message's own `Attachments` collection if it's still in the mailbox) so
  the coder records which of (a)-(d) actually applied — informative for
  closing this specific historical gap and for judging whether the 20MB
  cap itself ever needs revisiting (a separate, NOT-in-scope product
  decision), but not a gate on shipping the fix itself.

**Fix scope, gap 1 (silent-loss):** restore the honest-signal convention
at the pipeline layer. `_summarize_attachment_node`'s loop (or
`summarize_attachment`'s own return contract — the exact layer is a
decomposer/coder-level implementation choice, not decided here, since
either preserves `ADR-043` unchanged) gains a fallback entry, synthesized
from `result["summary_error"]` + `result["filename"]` (+
`result.get("relative_link")` when the file WAS actually saved to disk
but only failed to summarize), appended into `attachment_entries`
whenever `dated_entry` is absent — mirroring `classify_recent_emails`'s
own already-established wording convention. `summarize_attachment`'s own
already-AC-tested contract (never fabricate a `dated_entry` implying a
real summary that never happened) stays intact — the fallback entry uses
visibly distinct wording, never disguised as a genuine summary.

**Fix scope, gap 2 (per-message collision safety):** `write_attachments`
gains one new required parameter, `message_segment: str`, threaded into
its own directory composition (`.../attachments/<note_slug>/
<slug-of-message_segment>/<filename>`) and its returned `relative_link`.
`summarize_attachment`'s one live call site passes
`message_segment=received` (`received` is already one of its own
existing parameters — zero new plumbing upstream of that one call site).
Full timestamp, not a day-only date truncation, per architecture.md's own
reasoning (a Thread routinely receives multiple same-day messages; a
day-only segment would just relocate the collision window). The OTHER
live caller of `write_attachments` (`classify_recent_emails`) needs a
mechanical, no-real-collision-risk update to keep compiling — it is
already collision-safe by construction (its own `note_stem` embeds a
per-email EntryID suffix) and is NOT part of this story's repro scope.

Full reasoning, alternatives considered, and exact code-location citations:
`Implementation/Architecture/architecture.md` → "Thread Attachment Capture
— Silent-Loss Fix + Per-Message Collision Safety". `ESCALATIONS.md` →
`ESC-041` marked `Resolved`, this Notes entry + the architecture.md
section named as the resolving artefact. `REVIEW-QUEUE.md`'s
`BUGFIX-03-US-01` entry checked off accordingly (residual live-check item
noted, not blocking).

---

**Decomposer pass, `/plan-tasks` step 2, 2026-08-17:**

Locked the analyst's single Gherkin scenario as two ACs — `AC-01`
(capture/save/link, the successful-attachment path) and `AC-02`
(same-filename collision safety across two messages) — tightened wording
only (added an explicit "per Scenario 1" clause to `AC-02`'s `Given` so it
reads as a standalone, verifiable continuation rather than an implicit
carry-over). Split rather than kept as one AC because the two facets have
different owning fixes (`AC-01` only needs `T01`'s gap-1 restore; `AC-02`
additionally needs `T02`'s gap-2 nesting) even though both are verified
together in one continuous live session — the story's own Notes explicitly
invited either choice.

Created 2 flat-root tasks: `BUGFIX-03-US-01-T01` (gap 1 — the honest-signal
fallback in `_summarize_attachment_node`, plus the residual live-diagnostic
sub-step architecture.md assigned it; `app/business/pipelines/
email_capture_pipeline.py` only) and `BUGFIX-03-US-01-T02` (gap 2 —
`write_attachments`' new required `message_segment` parameter and both its
call sites; `app/data_access/vault_writer.py` +
`app/business/email_classification.py`). `depends_on`: `T01: []`, `T02:
[BUGFIX-03-US-01-T01]` — a strict two-node chain, acyclic by inspection.
Sequenced (not left independent) because `T02`'s own Tests section carries
the full live end-to-end verification of BOTH locked ACs in one continuous
capture session (a second message arriving after the first), which reads
most naturally once `T01`'s fix is already in place; the two tasks touch
disjoint files, so this is a verification-sequencing choice, not a
code-level requirement.

**AC → verification mapping:** `AC-01` and `AC-02` are both tagged in
`T02`'s `## Tests` (steps 1-2, one continuous live capture session); `T01`
carries its own real, non-AC-tagged verification (an in-process
monkeypatch-induced regression check of the fallback mechanism itself,
since the given Gherkin only specs the successful-attachment path) plus
the mandatory live-diagnostic sub-step. Every locked AC has at least one
tagged step — confirmed.

**Gate checks:** every AC is locked (`AC-01`, `AC-02`); both have a
matching tagged verification step (`T02`); `depends_on` is acyclic
(`T01 → T02`, confirmed by inspection). Story `status:` advances
`Draft → Ready`; both tasks are written at `status: Ready`, per Pipeline.md's
"task status moves in lockstep with the story" rule.

`gate: clear 2026-08-17` — no MUST-FLAG trigger fired this pass: no
material assumption filled a real gap (the AC-split and task-sequencing
choices above each have one clearly-better answer given the story's own
Notes/architecture scope, not a genuine multiple-equally-valid fork); no
`Draft`/unfinalised requirement relied on (`BUG-014` is a finalised ledger
entry); no ADR created or changed by this pass (`architecture.md`'s own
"no new ADR" framing carries forward unchanged); no new `ESCALATIONS.md`
entry needed (`ESC-041` was already resolved by the architect pass, not
reopened here); both tasks are small, single-file-scoped, one-working-
session-sized (matching this project's own `BUGFIX-01-US-01` two-task
precedent) — not oversized; both locked ACs are directly, live-verifiably
observable (a real saved file + a real `## Attachments` line); no
contradictory inputs remain (`ESC-041` resolved this pass's own
predecessor). The one residual item (which exact real-world variant
explains the historical Thread) is explicitly non-blocking per
`architecture.md`'s own instruction and does not itself constitute a
MUST-FLAG trigger for this pass. No `REVIEW-QUEUE.md` entry written by
this pass. Per the operator's explicit instruction this session, `/plan-
sprints` is NOT run now — this story stays ungrouped (`sprint: ""`),
pending a later `/plan-sprints` pass that bundles it into the same sprint
as `REQ-SB-68-US-01`.

---

**Product-owner pass (`/plan-sprints`, 2026-08-17) — grouped into
`SPRINT-055`, bundled with `REQ-SB-68-US-01` per the explicit operator
instruction anticipated above.** No `depends_on` edge connects either
story's tasks to the other's — the bundling is a directive followed, not a
dependency this pass discovered. Task order within the sprint: this
story's own `T01→T02` chain runs after `REQ-SB-68-US-01`'s own
`T01→T02→T03→T04` chain (a placement choice, not a dependency claim — see
the sprint's own Grouping Rationale). `gate: clear` for this pass —
advances the sprint's own `Draft → Ready`; this story's own `gate: clear`
status is unchanged. `BUG-014`'s `Fixed by` note in `BUGS.md`/`BACKLOG.md`
updated to point at `SPRINT-055`. Full reasoning:
`Implementation/Sprints/SPRINT-055-non-blocking-capture-dispatch-and-thread-attachment-fix.md`.

---

**Coder pass, `T01`, 2026-08-17 — `T01` Done, story advances `Ready →
In Progress` (`T02` still outstanding).** Restored the honest-signal
fallback in `_summarize_attachment_node`
(`app/business/pipelines/email_capture_pipeline.py`) exactly as this
story's own architecture scope specified; `summarize_attachment`'s own
contract left byte-for-byte unchanged. Verified via a throwaway,
in-process monkeypatch against the real `.venv` (both the oversized/unsaved
and saved-but-unsummarizable fallback cases, plus a regression check that
a genuine `dated_entry` still passes through unwrapped) — not `AC-01`/
`AC-02` themselves, which remain tagged and verified together in `T02`'s
own Tests section per the decomposer's own mapping. Ran the mandatory
live-diagnostic sub-step against the real, live Outlook mailbox: the
historical "Presight Agent Academy Demo" message is still reachable, and
architecture.md's own four candidate causes (a-d) were each directly
checked and falsified for this message — the real, confirmed mechanism is
a fifth cause: `outlook_com.py::_is_inline_attachment`'s `PR_ATTACH_
CONTENT_ID` check false-positives on the message's one genuine PDF
attachment (a real MIME Content-ID was set by the sending mail system on
every attachment in that message, not just the truly-inline signature
images), so `_extract_attachments` never returns it to the pipeline at
all — closest to this story's own separate `## Notes` candidate list's
item (c), not literally any of architecture.md's a-d. This is a real,
live, currently-reproducible defect distinct from `BUG-014`'s gap 1/gap 2
and outside `outlook_com.py`'s Out-of-Scope boundary for this story — not
fixed here; recommended for a separate `/bug` capture. Full write-up:
`T01`'s own Implementation Log,
`Implementation/Tasks/BUGFIX-03-US-01-T01-restore-honest-attachment-fallback-signal.md`.
`gate: clear` — no MUST-FLAG trigger fired.

(Since T01's own pass: the `_is_inline_attachment` false-positive it found
was independently captured and directly fixed the same day —
`BUG-017`, `Closed`, "Direct fix, 2026-08-17" — outside this story's own
scope/tracking, noted here only for continuity.)

---

**Coder pass, `T02`, 2026-08-17 — `T02` Done, story advances `In Progress →
Done`.** `write_attachments` (`app/data_access/vault_writer.py`) now
requires `message_segment: str`, nesting its save path and returned
`relative_link` one level deeper via `_slugify(message_segment)`, exactly
per this story's own adopted gap-2 design and `T02`'s own `## Files to
Modify`. Both live call sites updated:
`email_classification.summarize_attachment` passes
`message_segment=received`; `email_classification.classify_recent_emails`
passes `message_segment=email["id"]` (mechanical, per architecture.md's
own framing). `grep`-confirmed no other real caller exists.

**Both locked ACs verified live, in one continuous session, against the
real configured `VAULT_PATH` vault** — no natural same-filename-collision
email arrived within the verification window, so used `T02`'s own Tests
step 3 disclosed substitute: called the real, unmodified
`summarize_attachment` directly, twice, against a real, already-existing
Thread's `conversation_id`, with two `image001.png` attachment dicts
(identical filename, genuinely different content) and two different
`received` timestamps on the same day. Both files saved to disk under
distinct nested `<slug-of-received>/` subfolders; read back and confirmed
byte-identical to their own source content and NOT identical to each
other (no collision). The Thread note's own `## Attachments` section
(exercised via the same real `append_body_section_line` primitive
`thread_match_merge` itself calls, disclosed as a scope-internal
assumption) gained two separate dated sub-entries, not merged/replaced. A
third, distinct-filename attachment confirmed no regression to the
single-attachment case. The real vault was fully restored to its
pre-task state afterward (note reverted byte-for-byte, throwaway
attachment files/folders deleted, confirmed via direct re-read/diff).
**`[BUGFIX-03-US-01-AC-01]`: PASS. `[BUGFIX-03-US-01-AC-02]`: PASS.**

**New finding during verification, `ESCALATIONS.md` → `ESC-043`
(shared-interface-change, non-blocking):** `T02`'s own required fix has a
real, previously-unconsidered consequence for `app/business/cockpit/
attachments.py` (Inbox Cockpit, live via `cockpit_router.py`) — it reads
`classify_recent_emails`-sourced attachments back via a hardcoded FLAT
path that the new per-message nesting now breaks for any FUTURE capture
through that (still-live, `/poc/classify-emails`-reachable) path.
Already-saved historical attachments are unaffected. Not fixed here
(outside `T02`'s own `## Files to Modify`) — recorded and escalated, a
`/bug` capture recommended, mirroring `T01`'s own established precedent
this story of recording rather than fixing an out-of-scope finding. Full
write-up: `T02`'s own Implementation Log,
`Implementation/Tasks/BUGFIX-03-US-01-T02-per-message-attachment-nesting.md`,
and `ESCALATIONS.md` → `ESC-043` (`Status: Open`).

**Story-level closure:** every locked AC verified, every Implementation
Task complete, all Constraints respected (gap 1's true cause was
re-confirmed live by `T01`, not assumed; gap 2's collision protection is
live-verified, not just designed). `BUG-014` flipped `In Sprint → Closed`
in both `BUGS.md` and `BACKLOG.md`'s `## Bugs` mirror. `MEMORY.md` and
`CHANGELOG.md` updated. Story `status: Done`, `gate: flagged` (`ESC-043`,
non-blocking) — see this story's own frontmatter `gate_reason`.
