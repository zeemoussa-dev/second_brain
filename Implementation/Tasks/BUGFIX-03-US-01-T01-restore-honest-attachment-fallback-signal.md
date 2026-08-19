---
id: BUGFIX-03-US-01-T01
title: Restore the honest-signal fallback for a Thread attachment that fails to save or summarize
parent_story: BUGFIX-03-US-01
requirement_id: BUG-014
type: backend
status: Done
gate: clear
gate_reason: ""
depends_on: []
created: 2026-08-17
updated: 2026-08-17
---

# BUGFIX-03-US-01-T01 — Restore the honest-signal fallback for a Thread attachment that fails to save or summarize

## Parent Story

- Story: [[BUGFIX-03-US-01]] — `../UserStories/BUGFIX-03-US-01-thread-attachment-capture-and-collision-safety.md`
- Requirement: `BUGS.md` → `BUG-014` (bugfix story; no PRD requirement anchor)

---

## Objective

Close gap 1 (the real, confirmed silent-loss defect — see the story's own
`## Notes` and `architecture.md`'s "Thread Attachment Capture" subsection,
resolving `ESC-041`): `_summarize_attachment_node` must never silently
discard a real attachment's own outcome just because `summarize_attachment`
returned a `summary_error` instead of a `dated_entry` — it must synthesize
an honest, visibly-distinct fallback line instead, mirroring the convention
`classify_recent_emails` already established.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/pipelines/email_capture_pipeline.py::_summarize_attachment_node`
  (lines ~93-114) loops `email.get("attachments") or []`, calls
  `email_classification.summarize_attachment(...)` for each, and appends to
  `entries` ONLY when `result.get("dated_entry")` is truthy. Every other
  outcome (`saved: False` + `summary_error` on an oversized attachment;
  `saved: True` + `summary_error` on a saved-but-unsummarizable file) is
  silently dropped — no line ever reaches `attachment_entries`, so
  `thread_match_merge` never writes anything to the Thread note's own
  `## Attachments` section for that attachment.
- `email_classification.py::summarize_attachment` (lines ~287-370) already
  returns an honest `{"filename", "saved", "summary_error", ...}` dict on
  every non-`dated_entry` path — its own already-AC-tested contract (never
  fabricate a `dated_entry` implying a real summary that never happened)
  is correct and must NOT change.
- The sibling, still-live `classify_recent_emails` (same file, lines
  ~664-670) already has the honest convention this task restores at the
  Thread-pipeline layer: `f"- {att['filename']} (not saved — {att['size']}
  bytes exceeds the size cap)\n"`.

**After / Outputs:**
- `_summarize_attachment_node` appends a synthesized fallback entry into
  `entries` whenever `dated_entry` is absent, so every real, non-inline
  attachment leaves SOME durable, visible trace on the Thread note — saved
  successfully or not, summarized or not.
- `summarize_attachment`'s own signature, return contract, and body are
  UNCHANGED.

---

## Files to Modify

- `src/backend/app/business/pipelines/email_capture_pipeline.py`:
  1. Replace `_summarize_attachment_node`'s body (keep its existing
     docstring's first sentence; the "Collects only entries where..."
     sentence describing the OLD silent-drop behaviour must be rewritten to
     describe the new fallback behaviour) with:

     ```python
     def _summarize_attachment_node(state: EmailCapturePipelineState) -> dict:
         """A mandatory pass-through node -- runs for EVERY email, not just
         ones with attachments (ADR-043's own "in parallel, once per real
         attachment, when the email has any" framing is realized here as a
         loop over 0-or-more attachments rather than a real per-attachment
         graph fan-out; this is what guarantees `thread_match_merge`, reached
         only via this node's own fixed outgoing edge, is never reachable
         before this loop has fully completed). Every real, non-inline
         attachment leaves a durable entry in `attachment_entries` --
         `summarize_attachment`'s own real `dated_entry` when a genuine
         summary was produced, or a synthesized, visibly-distinct fallback
         line (BUGFIX-03-US-01, closes BUG-014's gap 1) whenever it wasn't
         -- never a silent drop, never a fabricated summary."""
         email = state["email"]
         conversation_id = email["conversation_id"]
         received = email["received"]
         entries: list[str] = []
         for attachment in email.get("attachments") or []:
             result = summarize_attachment(attachment, conversation_id, received)
             dated_entry = result.get("dated_entry")
             if dated_entry:
                 entries.append(dated_entry)
             else:
                 entries.append(_fallback_attachment_entry(result, received))
         return {"attachment_entries": entries}


     def _fallback_attachment_entry(result: dict, received: str) -> str:
         """Restores the honest-signal convention classify_recent_emails
         already established (MEMORY.md, 2026-08-16) for the one case the
         Thread pipeline lost: a real, non-inline attachment that failed to
         save or summarize for ANY reason still leaves a durable, visibly-
         distinct trace on the Thread note -- never disguised as a genuine
         summary. `summarize_attachment`'s own contract (never fabricate a
         `dated_entry`) is what makes this branch reachable at all; this
         function only decides the fallback's own wording."""
         filename = result["filename"]
         summary_error = result.get("summary_error", "unknown error")
         if result.get("saved") and result.get("relative_link"):
             return (
                 f"{received[:10]} — [{filename}]({result['relative_link']}) "
                 f"(saved but could not be summarized — {summary_error})"
             )
         return f"{received[:10]} — {filename} (not saved — {summary_error})"
     ```

     `_fallback_attachment_entry` is a new, plain, module-level function
     placed directly after `_summarize_attachment_node` — no new import
     needed (uses only stdlib string formatting already available in this
     file).

---

## Constraints

- Inherits from parent story (`ADR-043` unchanged; no new mechanism family;
  never fabricate a summary that never happened).
- Must NOT change `email_classification.py::summarize_attachment`'s
  signature, return contract, or body in any way — this task is scoped to
  the pipeline-node layer only.
- Must NOT change `thread_match_merge`, `append_body_section_line`, or any
  other function that consumes `attachment_entries` — the fix is entirely
  in what `_summarize_attachment_node` puts INTO that list.
- The fallback wording must be visibly distinct from a real `dated_entry`
  (which reads `"{date} — {filename}: {summary}"`) so a human reading the
  Thread note can never mistake a fallback line for a genuine summary —
  the `(not saved — ...)` / `(saved but could not be summarized — ...)`
  suffixes are load-bearing, not cosmetic.
- Must not regress the existing, correct fully-successful-summary case — a
  `dated_entry` produced by `summarize_attachment` is appended unchanged,
  exactly as today.

---

## Tests

<!-- The story's two locked ACs (AC-01, AC-02) both require the FULL fix
(this task's gap-1 restore AND T02's gap-2 per-message nesting) to be live
end-to-end verified together, since AC-02's own scenario is a continuation
of AC-01's within the same live capture session -- both are tagged and
verified in T02, per that task's own Tests section. This task carries its
own real, non-AC-tagged verification (the fallback mechanism itself, which
the story's given Gherkin doesn't exercise directly since it specs the
successful-attachment path) plus the mandatory live-diagnostic sub-step
architecture.md assigned to T01. -->

**Manual verification steps:**

1. (Not a locked AC — the given Gherkin scenario specs the successful-
   attachment path only, verified in T02. This is regression coverage for
   the actual root-cause fix.) In a Python shell against the real `.venv`
   (`.venv\Scripts\python.exe`, cwd `src/backend`), import
   `app.business.pipelines.email_capture_pipeline` and
   `app.business.email_classification`, then monkeypatch
   `email_capture_pipeline.summarize_attachment` in-process (mirroring this
   project's own established "monkeypatch a real, already-loaded dependency
   to induce a failure condition" technique, `Implementation/Learnings.md`
   `SPRINT-018`) to return a fixed `{"filename": "test.pdf", "saved": False,
   "summary_error": "Attachment not saved -- exceeds the size cap."}` (no
   `dated_entry` key), then call the real, unmodified
   `_summarize_attachment_node` against a minimal state dict with one fake
   attachment. Confirm the returned `attachment_entries` list contains
   exactly one entry reading
   `"{received[:10]} — test.pdf (not saved — Attachment not saved -- exceeds the size cap.)"`
   — not empty, not a fabricated summary. Repeat with
   `{"filename": "test.docx", "saved": True, "relative_link":
   "attachments/x/y/test.docx", "summary_error": "Not summarizable: ..."}`
   and confirm the entry reads the "saved but could not be summarized"
   wording with the link embedded. Revert the monkeypatch (or let the
   throwaway shell exit — no permanent code change).
2. (Live diagnostic, non-blocking — folded into this task's own scope per
   `architecture.md`'s explicit instruction, mirrors
   `REQ-SB-56-US-01-T00`'s precedent.) If the historical "Presight Agent
   Academy Demo" Thread's own source email is still reachable in the real,
   live Outlook mailbox, inspect it directly (e.g. a short throwaway COM
   script reading `item.Attachments.Count` and each attachment's own
   `.Size`, or add temporary `print()`/logging at each hand-off point —
   fetch → `_summarize_attachment_node` → `summarize_attachment` →
   `write_attachments` — for one real re-processed capture of that
   message) to determine which of `architecture.md`'s four candidate
   causes (a: genuinely >20MB; b: a OneDrive/SharePoint link, not a real
   COM attachment; c: a pre-`T07`-wiring dev-verification artifact; d: a
   silently-swallowed `_extract_attachments` exception) actually applied.
   Record the finding in this task's own Implementation Log. If the
   message is no longer reachable (deleted/archived), record that
   explicitly instead — this does not block or change the fix above.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `_summarize_attachment_node` appends a synthesized, visibly-distinct
      fallback entry into `attachment_entries` whenever `summarize_attachment`
      returns no `dated_entry`, for every reason (unsaved/oversized,
      saved-but-unsummarizable) — never a silent drop
- [x] `summarize_attachment`'s own signature, return contract, and body are
      byte-for-byte unchanged
- [x] The live-diagnostic sub-step above ran and its finding (or
      "message no longer reachable") is recorded in the Implementation Log
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Per-message attachment-folder nesting / filename-collision safety
  (gap 2) — that is `T02`.
- Any change to `outlook_com.py` — gap 1's real mechanism is confirmed to
  be at the pipeline-node layer, not the Outlook fetch layer (`ESC-041`,
  resolved); `outlook_com.py` already correctly extracts attachments.
- Any change to `write_attachments`, `thread_match_merge`, or
  `append_body_section_line`.

---

## Context / Notes

Full root-cause investigation, corroborating evidence, and the four
unconfirmed historical-Thread candidate causes are in
`Implementation/Architecture/architecture.md` → "Thread Attachment Capture
— Silent-Loss Fix + Per-Message Collision Safety" and this story's own
`## Notes`. `ESC-041` (`ESCALATIONS.md`) is `Resolved` — do not re-litigate
`BUG-014`'s own originally-stated (and now-falsified) gap-1 mechanism
("`outlook_com.py` never reads Attachments").

---

## Implementation Log

**Change made, 2026-08-17:** `_summarize_attachment_node` in
`app/business/pipelines/email_capture_pipeline.py` now appends
`_fallback_attachment_entry(result, received)` into `entries` whenever
`summarize_attachment`'s returned `result` has no `dated_entry`, instead of
silently discarding the outcome. New module-level `_fallback_attachment_entry`
placed directly after the node, exactly as specified in this task's own
`## Files to Modify`. `_summarize_attachment_node`'s docstring rewritten
(kept the first sentence, replaced the "Collects only entries where..."
sentence describing the old silent-drop behaviour). No other function
touched; `summarize_attachment` in `email_classification.py` is
byte-for-byte unchanged (confirmed by `git diff` scoped to that file
showing no changes).

**Verification (non-AC-tagged, regression coverage for the root-cause fix)
— Tests step 1:** Ran a throwaway script against the real
`.venv\Scripts\python.exe` (cwd `src/backend`), monkeypatching
`email_capture_pipeline.summarize_attachment` in-process (no permanent code
change; monkeypatch reverted before the script exited) and calling the
real, unmodified `_summarize_attachment_node` against a minimal state dict
with one fake attachment:
- Oversized/unsaved case (`{"filename": "test.pdf", "saved": False,
  "summary_error": "Attachment not saved -- exceeds the size cap."}`, no
  `dated_entry`): returned `attachment_entries == ["2026-08-17 — test.pdf
  (not saved — Attachment not saved -- exceeds the size cap.)"]`. PASS —
  matches the task's own expected wording exactly.
- Saved-but-unsummarizable case (`{"filename": "test.docx", "saved": True,
  "relative_link": "attachments/x/y/test.docx", "summary_error": "Not
  summarizable: ..."}`): returned `attachment_entries == ["2026-08-17 —
  [test.docx](attachments/x/y/test.docx) (saved but could not be
  summarized — Not summarizable: ...)"]`. PASS — link embedded, wording
  matches.
- Regression check, genuine success case (`{"filename": "test.pdf",
  "saved": True, "relative_link": ..., "dated_entry": "2026-08-17 —
  test.pdf: a short presentation summary."}`): returned
  `attachment_entries == ["2026-08-17 — test.pdf: a short presentation
  summary."]` — the real `dated_entry` passed through completely
  unchanged, no fallback wrapping applied. PASS — no regression to the
  happy path.

No `VAULT_PATH`-scratch test vault was actually created or written to —
`summarize_attachment` itself (which is what performs the vault write) was
monkeypatched out entirely for this test, so `_summarize_attachment_node`
under test never reaches `vault_writer`. Confirmed no `_scratch_vault_*`
directory exists on disk after the run.

**AC-01/AC-02 (locked):** not verified here — both require the FULL fix
(this task's gap-1 restore AND T02's gap-2 per-message nesting) and are
tagged/verified together in T02's own Tests section, per the story's own
decomposer pass. Not claimed Done by this task.

**Live-diagnostic sub-step (Tests step 2, non-blocking, informational) —
finding recorded:** The historical "Presight Agent Academy Demo" message IS
still reachable in the real, live Outlook mailbox (found directly in the
default Inbox folder — the exact folder `list_recent_mail` reads —
matching `ConversationID = 01D26A7530444A23803A002210620160`, `Subject =
"Re: Presight Agent Academy Demo"`, received 2026-08-16 13:02:57 UTC).
Direct live COM inspection (`item.Attachments`, read-only, no code path
changed) found 14 raw attachments: 13 are genuine inline
signature/logo/social-icon images (`logo_*.png`, `twitter_*.png`,
`linkedin_*.png`, `instagram_*.png`, `youtube_*.png`, `leaf_*.png`,
`thumbnail_emailsignature_*.jpg`) plus exactly ONE real, non-inline
document: `260816 Agentic academy v06_shared.pdf`, `Size = 5,200,487`
bytes (~4.96 MB), `Type = 1` (`olByValue`, a genuine embedded/by-value
attachment, not a link).

Checked against `architecture.md`'s own four candidate causes directly:
- **(a) genuinely >20MB — FALSIFIED.** 4.96 MB is well under the 20 MB
  (`_MAX_ATTACHMENT_BYTES`) cap.
- **(b) a OneDrive/SharePoint link, not a real COM attachment —
  FALSIFIED.** `Type = 1` is a real by-value COM attachment (not
  `olLinked`); the message body (first 2000 chars) contains no
  `1drv.ms`/`sharepoint.com`/`onedrive` marker; calling the real
  `_extract_attachments`-internal `SaveAsFile` technique against it
  (via the diagnostic below) confirms it has real, readable byte content.
- **(c) pre-`T07`-wiring dev-verification artifact — cannot be fully
  ruled out from the message's current live state alone** (that is a
  question of processing history/timing), **but is moot**: a
  definitively confirmed, currently-live, deterministically-reproducible
  mechanism (below) independently and fully explains the loss on ANY
  future reprocessing too, regardless of whether (c) also applied
  historically.
- **(d) a silently-swallowed `_extract_attachments` exception —
  FALSIFIED for this attachment.** No exception occurred; the real,
  unmodified `outlook_com._is_inline_attachment(att)` returned `True`
  cleanly and deterministically (not a caught/swallowed error).

**The actual confirmed mechanism is a FIFTH cause, not literally one of
architecture.md's four** (closest to the story's own separate `## Notes`
candidate list's item (c), "`_is_inline_attachment` misclassifying a real
(non-signature) attachment as inline for that specific email" — a
different, more specific list than architecture.md's later a-d list):
calling the real, unmodified `outlook_com._is_inline_attachment` and
`outlook_com._extract_attachments` directly against this live message
confirms `_extract_attachments` extracts **0 non-inline attachments** —
the PDF is filtered out because Outlook's own `PR_ATTACH_CONTENT_ID` MAPI
property (`_is_inline_attachment`'s first, highest-priority check) IS set
on this genuine PDF attachment, to a real MIME-style Content-ID
(`F78603F9BF6F5F44A8FB0E7067BD8D34@AREP273.PROD.OUTLOOK.COM`) — distinctly
different in shape from the 13 truly-inline images' own content-ids, which
literally echo their own filenames (e.g.
`logo_c2dc40ec-8072-4fec-82f4-57b4bc03cc29.png`). This indicates the
sending mail system assigned a Content-ID to every MIME part of this
message (a real, observed behavior of some senders/relays), not that the
PDF is actually referenced inline in the message body — `_is_inline_attachment`'s
content-id heuristic has a genuine false-positive on this specific,
real-world message shape. This is a live-confirmed, currently-reproducible
defect distinct from `BUG-014`'s gap 1/gap 2 (which this story fixes) and
outside this task's own `## Files to Modify` (`outlook_com.py` is
explicitly Out of Scope for this story). Not fixed here. Recommend a new
`/bug` capture against `outlook_com.py::_is_inline_attachment` (interactive
capture, not run by this task) so it is tracked and triaged separately —
flagged in this task's closing report for the human, per this task's own
instruction to record rather than fix.

**Assumption logged (scope-internal judgement call, per Pipeline.md hard
rule 5):** used a throwaway, read-only COM inspection script (not a
permanent code change, not committed) to perform the live-diagnostic
sub-step, mirroring the task's own suggested technique. Ran it twice
(once to locate/inspect the message broadly, once to call the real
`outlook_com` private functions directly) rather than one combined script,
purely for incremental clarity — no code-path difference in the finding.

**`MEMORY.md`:** added a Pattern entry for `_fallback_attachment_entry`'s
honest-signal convention and a Constraint entry flagging the newly-found
`_is_inline_attachment` content-id false-positive as a known, separate,
not-yet-filed defect.

**`CHANGELOG.md`:** entry appended under `[Unreleased]`.

**Story-level ACs:** `AC-01`/`AC-02` remain unverified by this task (by
design — see above); story `BUGFIX-03-US-01` stays `Ready`/`In Progress`
until `T02` completes and runs its own live end-to-end verification.

`gate: clear 2026-08-17` — no MUST-FLAG trigger fired: no material
assumption filled a real gap in this task's own scope (the fallback
wording/placement was fully specified verbatim by the task); no
`Draft`/unfinalised requirement relied on; no ADR created or changed; no
`ESCALATIONS.md` entry needed (the live-diagnostic finding is informational
per the task's own explicit non-blocking framing, not a contradiction
within this task's scope); both locked-AC-adjacent verifications performed
were directly, live-verifiably observable; the one new finding
(`_is_inline_attachment` false-positive) is out of this task's own Files to
Modify and does not block or change this task's own fix — recorded for the
human, not escalated as a blocker.
