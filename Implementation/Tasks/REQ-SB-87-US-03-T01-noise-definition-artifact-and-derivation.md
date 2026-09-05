---
id: REQ-SB-87-US-03-T01
title: Noise-definition artifact + out-of-band derivation mechanism
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "trigger-scope-internal-judgement-calls (Pipeline.md: scope-internal judgement calls are logged as assumptions in the Implementation Log and flag the task for human spot-check) — see Implementation Log below and REVIEW-QUEUE.md"
phase: P1
depends_on: []
created: 2026-09-01
updated: 2026-09-02
---

# REQ-SB-87-US-03-T01 — Noise-Definition Artifact + Out-of-Band Derivation Mechanism

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Create the real, structured, persisted noise-definition artifact under the
vault's own `.second-brain/data/` tree, plus a genuinely separate,
out-of-band derivation mechanism to (re)generate it — per `ADR-018`'s
Decision.

---

## Starting State → End State

**Before / Inputs:**
- No noise-definition artifact exists anywhere.
- `ADR-018`: the artifact is a real, structured, persisted file under
  `.second-brain/data/` (a new sibling to `Templates/`), never a
  Skill-`scripts/`-folder file, never baked into a profile's static system
  prompt — every Capture script already receives `--vault-path`, so it
  reads with zero deploy step.

**After / Outputs:**
- `.second-brain/data/EmailCapture/noise_definition.json` (exact path —
  this task's own naming call, matching `ADR-018`'s illustrative example):
  a real, structured JSON document describing what content counts as
  "noise" — e.g. a list of natural-language rules/criteria (not a
  hand-written keyword list — the definition's own CONTENT is LLM-derived
  prose/criteria, per PRD point 7's prompt-driven-not-hardcoded-heuristic
  principle; only the FILE FORMAT/persistence mechanism is this task's own
  mechanical code).
- A derivation mechanism — a new, standalone script (e.g.
  `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/
  derive_noise_definition.py`, or an equivalent out-of-band process; this
  task's own naming/shape call) that:
  - Takes a real sample of email content (e.g. a batch pulled via the
    already-real `list_recent_emails.py`/`run_full_capture.py` paging, or a
    hand-curated set for the initial derivation).
  - Invokes real LLM reasoning (a one-shot `hermes -p <profile> chat -q
    "..."` relay call, or an interactive Hermes session — this task's own
    disclosed choice; either is legitimate per `ADR-018`'s own "a dedicated
    one-off script, a live interactive Hermes agent session" allowance) to
    derive/refine the noise definition's own real content from that
    sample.
  - Writes/overwrites the persisted artifact above.
  - Is invoked ON-DEMAND only (e.g. during the 100-email scratch-sample
    proving phase, and again whenever the operator wants to retune it) —
    NEVER auto-triggered from inside the recurring capture tick.

---

## Files to Modify

- `.second-brain/data/EmailCapture/noise_definition.json` (new, initial
  content — a real, first derivation, not a placeholder).
- A new derivation script (path per the coder's own disclosed choice,
  documented in the Implementation Log).

---

## Constraints

- Inherits from parent story.
- **Prompt-driven, minimal code (PRD point 7):** the definition's own
  CONTENT comes from real LLM reasoning over real sample content — never a
  hand-written keyword/sender heuristic invented directly in this task's
  own code.
- The artifact must be plainly readable/inspectable independently of any
  capture run (a plain JSON file, human- and script-readable).
- Derivation is decoupled from the recurring 30-minute capture tick — never
  triggered automatically from inside `ingest_email.py`/
  `run_delta_capture.py`.
- No change to any Capture-stage script's own code is required to re-tweak
  the definition's content — only the artifact file itself changes.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-03-AC-04]` Run the derivation mechanism once against a
   real sample of email content (or a representative curated set); confirm
   `.second-brain/data/EmailCapture/noise_definition.json` is written with
   real, structured, genuinely LLM-derived content (not a placeholder, not
   a hand-written keyword list). Read the file directly, independently of
   any capture run, and confirm it is inspectable/legible.
2. (Unlabeled, supporting) Re-run the derivation mechanism a second time
   with a genuinely different sample; confirm the artifact's content
   updates to reflect the new derivation (proves it isn't a one-time,
   frozen file).
3. (Unlabeled, supporting, added 2026-09-02, grounds `T02`'s own tagged
   `[REQ-SB-87-US-03-AC-10]` check) Include the five real seed example
   subjects the operator already confirmed noise-shaped ("Learning
   Assignment Changes Email Notification", "New Payslip available for
   viewing-download", "Core42 Information Security Awareness Training",
   "Compass Alert- Failed API Calls", "CRM Enhancements - Weekly Release
   Summary") as guidance/sample content for this task's own real
   derivation run — as seed examples grounding the definition, never as a
   hardcoded rule list substituting for the LLM's own reasoning. Confirm
   the resulting persisted `noise_definition.json` explicitly frames its
   own category as "anything automated/broadcast" (system/HR/security
   notifications, broadcast newsletters, event-announcement blasts) —
   broader than, and not limited to, literal meeting-invite `.ics` items.
   The actual "these five subjects verdict as Noise" observation is `T02`'s
   own `AC-10`-tagged check, once a real classifier exists to answer it.

**Automated tests:** `n/a — no existing pytest harness for this Skill; the
artifact's own content is LLM-derived, not deterministic code output`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Noise-definition artifact exists at a real, structured,
      `.second-brain/data/`-tree path
- [x] A genuinely separate, out-of-band derivation mechanism exists and
      produces real, LLM-derived content
- [x] Derivation never auto-triggers from the recurring capture tick
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Provisioning the classifier Hermes profile that CONSUMES this artifact
  at capture time — `T02`.
- Wiring the classify-or-skip relay call into `ingest_email.py` — `T03`.
- The real 100-email scratch-sample proving-phase RETUNE pass — `T05` (this
  task's own derivation run only needs to prove the mechanism works, not
  perform the final production-quality tune).

---

## Context / Notes

`ADR-018` (`Implementation/Architecture/ADR.md`) — read the full Decision
and "Alternatives Considered" (the rejected static-system-prompt option)
before implementing.

**Added 2026-09-02 (decomposer pass):** `REQ-SB-87-US-03-AC-10`'s own
locked, AC-tagged verification step lives in `T02` (the task that actually
has a classifier to observe "classified as Noise" with) — this task's own
role is grounding the derivation's real INPUT sample with the five
operator-confirmed seed subjects (see Tests step 3), so `T02`'s later
check has a real definition to verify against, not inventing new scope
here.

---

## Implementation Log

**2026-09-02 (coder pass — built and live-verified).** Read `ADR-018` in
full, `outlook_lib.py` directly (confirmed literal `.ics` meeting invites
are already filtered upstream via `MessageClass.startswith("IPM.Schedule.
Meeting")`, before any classification would ever run — `_MEETING_MESSAGE_
CLASS_PREFIX`, `_list_folder_mail`), and the 5 real seed Thread/RawMessage
notes directly from the live vault (`Work/Threads/...`, read-only).

**What was built:**
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/
  derive_noise_definition.py` (new) — a standalone, out-of-band script.
  Takes a real email sample (`--sample-file`, a JSON array of
  `{subject, sender_email, body}`; defaults to a built-in 5-item sample
  copied verbatim from the operator's own locked seed subjects), builds
  one prompt instructing the target Hermes profile to derive a
  structured JSON noise definition grounded in that sample (explicitly
  framed as "anything automated/broadcast," explicitly told literal
  meeting invites are already filtered upstream and must not be the
  definition), relays it via one bounded `hermes [-p PROFILE] chat -Q
  --query-file <scratch-file>` subprocess call, parses the JSON response
  (`json.JSONDecoder.raw_decode` from the first `{`, tolerant of
  incidental prose/fencing), and persists `{version, derived_at,
  derivation_profile, sample_size, sample_subjects, definition}` to
  `.second-brain/data/EmailCapture/noise_definition.json` UNDER THE REAL
  VAULT (`<OPERATOR_VAULT_OLD>`), never inside this repo —
  per `ADR-018`'s own explicit Decision text ("a real, structured,
  persisted file under the VAULT's own `.second-brain/data/` tree").
  A failed relay/parse leaves any previously-persisted artifact
  untouched (`derive()` only writes after a successful parse). Deployed
  to the real profile-facing copy under `AppData\Local\hermes\skills\
  vault-rebuild\email-thread-capture\scripts\` (this project's own
  established manual-deploy convention, `MEMORY.md`) so it could
  actually run.

**Scope-internal judgement calls (assumptions), logged for human
spot-check per Pipeline.md:**
1. **Derivation relay target profile:** used the default/root Hermes
   profile (no `-p` flag at all) rather than provisioning a new
   dedicated profile. `ADR-018`/this task's own text explicitly leave
   this as "this task's own disclosed choice" for the DERIVATION script
   specifically (distinct from `T02`'s own later, separate, dedicated
   CLASSIFIER profile) — the root profile is a real, already-provisioned
   general-reasoning agent, sufficient for a one-off structured-JSON
   derivation task. `--profile` is a real CLI flag on the script so a
   future re-derivation can target any other real profile instead.
2. **JSON schema for `definition`:** `{category, description, criteria,
   positive_signals, negative_signals}` — `ADR-018` explicitly leaves
   "exact field names" as decomposer/coder-level; chosen to keep the
   content genuinely structured/queryable while staying entirely
   LLM-authored (this script's own code never writes a criterion,
   signal, or category string itself).
3. **Built this task ahead of `SPRINT-084`'s own formal
   `depends_on_sprints: [SPRINT-083]` start gate** (`SPRINT-083` is
   currently `In Progress`, not yet `Done` — its own `US-02` half is
   `Blocked` on `ESC-061`) — done under the launching agent's own
   explicit instruction that this specific task (`depends_on: []`) is
   independently buildable in parallel with `REQ-SB-87-US-02-T06`, no
   file overlap. Confirmed directly: this task touches zero files any
   other in-flight `REQ-SB-87` task touches, and needs nothing
   `SPRINT-083` delivers (only `US-03-T03` reaches back into `SPRINT-083`,
   per the sprint's own Dependencies section). Disclosed here rather than
   silently built as if the sprint had formally started in order.

**Live verification (real, no mocks) — `AC-04`:**
- Ran the real derivation mechanism twice against the real, installed
  Hermes CLI (`hermes.exe`, confirmed on PATH) and the real vault.
  Real Python resolved via `py -0p` after the sandboxed shell's own
  `python`/`py` aliases turned out to be a non-functional Microsoft
  Store stub (see `MEMORY.md`, new Constraint entry) —
  `AppData\Local\Python\pythoncore-3.14-64\python.exe` used directly.
- **Run 1** (built-in default sample — the operator's exact 5 locked
  seed subjects: "Learning Assignment Changes Email Notification", "New
  Payslip available for viewing/download", "Core42 Information Security
  Awareness Training", "Compass Alert: Failed API Calls", "CRM
  Enhancements | Weekly Release Summary 🚀"): completed in ~40s CPU-alive
  (confirmed the real `hermes.exe` child process was alive and running
  the expected `chat -Q --query-file ...` command mid-call, not hung),
  wrote a real, structured `noise_definition.json`. Read directly,
  independently of any capture run — fully legible: `definition.
  category = "Automated/Broadcast Notifications"`, a 4-sentence
  `description`, 6 `criteria`, 10 `positive_signals`, 6 `negative_
  signals`, all genuine LLM prose (e.g. "Sender identity indicates
  automation or a broad alias...", "Primary call-to-action is to
  visit/login to a portal, dashboard, LMS, or app...") — never a
  hand-written keyword list, and the category explicitly frames "anything
  automated/broadcast" (HR/payroll, security-training, alerts,
  newsletters, release summaries) with **zero mention of meeting
  invites anywhere in the definition**, confirming it is not narrowed to
  literal `.ics` items. **This satisfies `[REQ-SB-87-US-03-AC-04]`'s
  primary Tests step, and the 2026-09-02-added unlabeled supporting step
  (seed-grounded, "anything automated/broadcast" framing).**
- **Run 2** (unlabeled, supporting Tests step — "re-run with a
  genuinely different sample"): a real, different 3-email sample (none
  of the 5 seed subjects — "Alert for Mahmoud Moussa, Data Change -
  Others", "[SECURITY ALERT]: Protect Yourself from Fake Insurance
  Search Results", "Requested Item RITM0108464 has been updated", all
  read directly from other real vault Threads). The persisted artifact's
  content visibly changed: different `sample_subjects`, different
  `derived_at`, and a materially different `definition` (new criteria
  wording, new signals the first sample never surfaced — `RITM`/`INC`
  ticket-ID patterns, `List-Unsubscribe` headers) — **confirms the
  artifact is a real, re-derivable file, never a one-time frozen
  output.** The artifact was then restored (file copy) back to Run 1's
  own content, since Run 1 — grounded in the operator's exact locked
  seed subjects — is this task's own required "real, first derivation,"
  and the one `T02`'s own later `AC-10` check depends on.
- **Inspectable/persisted, not regenerated on read:** confirmed directly
  — the artifact is a plain, static JSON file; reading it (`Read` tool,
  a fresh `hermes`-uninvolved process) returns the exact same persisted
  content with no side effect, satisfying Scenario 4's "read/inspected
  independently of any capture run."

**Live verification — derivation never auto-triggers from the recurring
tick:** confirmed by construction and by `git status` — `ingest_email.py`
and `run_delta_capture.py`/`run_full_capture.py` are entirely outside
this task's own `## Files to Modify` and were never touched (`git
status` shows zero diff on any of them from this task's own work; the
pre-existing `M` markers on those files belong to the parallel, already-
`Done` `REQ-SB-87-US-02-T06`, not this task).

**Files actually touched (matches `## Files to Modify` exactly):**
- `.second-brain/data/EmailCapture/noise_definition.json` — written
  under the real vault (not the repo), real, first-derivation content
  (Run 1 above), not a placeholder.
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/
  scripts/derive_noise_definition.py` — new derivation script.

No `ESCALATIONS.md`/new `REVIEW-QUEUE.md` entry required for this task's
own build (no out-of-scope event, no new dependency, no shared-interface
change, no ADR deviation) — the pre-existing `REQ-SB-87-US-03`/`ADR-018`
`REVIEW-QUEUE.md` entry already covers the story-level human-review flag
this task inherits; `gate: flagged` here is solely the standard
scope-internal-judgement-call spot-check flag (assumptions 1-3 above),
not a new escalation.
