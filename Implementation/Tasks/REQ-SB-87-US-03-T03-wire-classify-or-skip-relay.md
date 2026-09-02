---
id: REQ-SB-87-US-03-T03
title: Wire the classify-or-skip relay call into ingest_email.py
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "trigger-scope-internal-judgement-calls (Pipeline.md: scope-internal judgement calls are logged as assumptions in the Implementation Log and flag the task for human spot-check) — see Implementation Log below and REVIEW-QUEUE.md"
phase: P1
depends_on: [REQ-SB-87-US-03-T02, REQ-SB-87-US-02-T01, REQ-SB-87-US-02-T06]
created: 2026-09-01
updated: 2026-09-02
---

# REQ-SB-87-US-03-T03 — Wire the Classify-or-Skip Relay Call into ingest_email.py

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Insert ONE bounded, one-shot classify-or-skip relay call into
`ingest_email.py`'s own `if existing_directory is None:` branch, BEFORE any
Thread/RawMessage note is written — per `ADR-018`'s Decision — and stamp
the resulting classification onto every genuinely-created Thread. A
first-seen message whose real `direction` is `"sent"` must never be
classified as Noise (added 2026-09-02, operator-locked business rule).

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-87-US-02-T01`'s migrated `ingest_email.py`:
  `existing_directory = vault_lib.resolve_thread_directory(...)` /
  `vault_manager.find_by_id(...)`; `if existing_directory is None:` creates
  the Thread unconditionally.
- `T02`'s classifier profile answers one bounded relay question.
- `T01`'s noise-definition artifact is readable via `--vault-path`.
- `REQ-SB-87-US-02-T06`'s real `direction` field (`"sent"` | `"received"`)
  is present on the email payload `ingest_email.py` receives (added
  2026-09-02 — this task now also `depends_on` that sibling-story task).

**After / Outputs:**
- Inside the SAME `if existing_directory is None:` branch, BEFORE the
  Thread-creation call:
  1. Read the current noise-definition artifact
     (`.second-brain/data/EmailCapture/noise_definition.json`).
  2. Issue ONE `hermes -p <classifier-profile> chat -q "..."` subprocess
     call (the SAME `subprocess.run()`-style dispatch technique
     `run_delta_capture.py` already uses for every other per-email step),
     passing the definition's own content + this email's own sender/
     subject/body.
  3. Parse the structured JSON verdict.
  4. If `is_noise` is `true`: return early — no Thread, no RawMessage, no
     Person-note side effect, nothing written anywhere for this email — and
     the function's own returned dict gains a new `"skipped_as_noise":
     true` field (alongside `thread_created: false, message_created:
     false`) so the caller (`T04`, aggregating in
     `run_full_capture.py`/`run_delta_capture.py`'s own real per-email loop
     — confirmed directly, both read `ingest_email.py`'s own returned JSON
     via `result.get(...)`) can count it. Every OTHER (non-skip) return
     path keeps `"skipped_as_noise": false`.
  5. If `is_noise` is `false`: proceed to create the Thread exactly as
     today, additionally stamping the returned `classification` value into
     the Thread's own new frontmatter field (`REQ-SB-87-US-01-T05`'s own
     declared field).
- **Classification happens exactly once, at first sight of a
  conversation_id** — this branch only ever runs when `existing_directory
  is None`; an already-existing Thread's classification is never
  re-evaluated by a later message on the same conversation (a structural
  guarantee, not a runtime check — the branch itself is the guard).
- **Disclosed relay-failure degrade default (decomposer-level decision,
  per `ADR-018`'s own Consequences):** if the relay call fails or times
  out, treat this conversation as NOT YET classified — do not create a
  Thread, do not skip permanently. Let the SAME per-email
  `try/except ... continue` pattern already present in the orchestrators
  catch it, so this conversation is naturally retried on the NEXT capture
  tick (since `existing_directory` stays `None` until a Thread is actually
  written). Never silently default to "not noise" (fabricates a positive
  create) nor "is noise" (silently, permanently discards real content the
  operator never decided to skip).
- Sent Mail items are never excluded merely because they originated from
  the user's own mailbox — the classify-or-skip judgment only evaluates
  content, never the sender-is-self flag `outlook_lib.py`'s own 2026-08-24
  design already uses for combining Sent+Inbox into one Thread.
- **Sent items are never Noise (added 2026-09-02, operator-locked, Scenario
  8):** when the first-seen message's own real `direction`
  (`REQ-SB-87-US-02-T06`) is `"sent"`, it must never be classified as
  Noise, regardless of its own subject/body content. Either mechanism
  satisfies this (coder's own disclosed choice, per the architect's own
  2026-09-02 note): (a) a deterministic guard BEFORE the relay call — skip
  the judgment entirely for a `direction: "sent"` first message and
  classify it directly (still exactly one of Internal-only/
  Partner-related/Customer-related), or (b) an explicit instruction inside
  the relay's own prompt/question text that the classifier must never
  return `is_noise: true` for a message it is told is `direction: "sent"`.
  Whichever is chosen, the resulting Thread must still be created and
  stamped with a real classification value exactly as any other non-noise
  email would be.
- **Noise judgment fires only once, on a genuinely new `conversation_id`
  (added 2026-09-02, now an explicit business rule, Scenario 9):** restates
  this task's own already-designed mechanism (the relay call only ever
  fires from the `if existing_directory is None:` branch) as an explicit,
  operator-confirmed rule — a further message on an already-classified
  conversation is captured unconditionally, never re-judged, even when that
  later message's own content, taken in isolation, would look noise-shaped
  (e.g. an automated reply-all notification landing inside an otherwise-real
  thread). This changes no code-shape versus what this task already builds
  for `AC-03`/the pre-existing "no second relay call" check — only the test
  coverage is extended (see Tests below).

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/ingest_email.py`

---

## Constraints

- Inherits from parent story.
- One relay call per newly-first-seen `conversation_id` ONLY — never per
  message, never for an already-existing Thread.
- Never regress the Sent+Inbox combined-capture design.
- The relay call must run BEFORE any Thread/RawMessage note is written —
  a genuine skip must leave zero trace in the vault.
- Verify against the SAME scratch vault/100-email sample `REQ-SB-87-US-02`'s
  own tasks used — never the live vault for this task.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
~100-email sample):**
1. `[REQ-SB-87-US-03-AC-01]` Find (or engineer, within the scratch sample)
   a genuinely first-seen conversation whose content matches the current
   noise definition; run the migrated `ingest_email.py` against it.
   Confirm NO Thread note and NO RawMessage note are written anywhere for
   it.
2. `[REQ-SB-87-US-03-AC-02]` Run against a genuinely first-seen,
   non-noise conversation; confirm the created Thread's own frontmatter
   carries a real classification value of exactly one of Internal-only/
   Partner-related/Customer-related.
3. `[REQ-SB-87-US-03-AC-03]` Run `ingest_email.py` a SECOND time for a
   FURTHER message on the SAME already-classified conversation_id; confirm
   the existing RawMessage-creation/capture flow proceeds exactly as
   before, and the Thread's own classification value is unchanged — no
   second relay call is made for it (confirm via a log/print statement or
   subprocess-call count, not just the end-state value).
4. `[REQ-SB-87-US-03-AC-06]` Confirm a real Sent Mail item combining into
   an existing Thread (or forming a new one) is still combined with its
   Inbox counterpart exactly as `outlook_lib.py`'s own 2026-08-24 design
   already does — the new judgment step never excludes it.
5. `[REQ-SB-87-US-03-AC-08]` (added 2026-09-02) Find or engineer a
   genuinely first-seen conversation whose first message has real
   `direction: "sent"` AND whose own subject/body content would otherwise
   read as noise-shaped (e.g. reuse one of `T02`'s own engineered noise
   examples but relabel/re-source it as Sent). Run the migrated
   `ingest_email.py` against it. Confirm it is NEVER classified as Noise —
   the resulting Thread IS created and stamped with a real classification
   value of exactly one of Internal-only/Partner-related/Customer-related.
6. `[REQ-SB-87-US-03-AC-09]` (added 2026-09-02) Extend step 3 above: for
   the FURTHER message run on the same already-classified conversation_id,
   deliberately use a real message whose OWN content, taken in isolation,
   would match the current noise definition (e.g. an automated reply-all
   notification subject). Confirm it is still captured into the existing
   Thread exactly as any other subsequent message would be — never
   silently dropped — and confirm (via the same log/print statement or
   subprocess-call count technique as step 3) that no relay call was made
   for it at all, not even one that happened to return `is_noise: false`.
7. (Unlabeled, supporting) Engineer a relay failure/timeout (e.g. a
   scoped, disclosed in-process monkeypatch of the relay call, reverted
   after); confirm the conversation is NOT classified as noise, no Thread
   is created, and it is naturally retried on the next call — matching
   the disclosed degrade default above.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Classify-or-skip relay call fires exactly once per newly-first-seen
      conversation_id, before any note is written
- [x] Noise verdict → zero vault trace
- [x] Non-noise verdict → Thread created with a real classification value
- [x] Already-classified Thread never re-evaluated
- [x] Sent+Inbox combined-capture design unaffected
- [x] Relay failure degrades to "retry next tick," never a silent
      fabricated default
- [x] A first-seen `direction: "sent"` message is never classified as
      Noise; its Thread is created and classified exactly as any other
      non-noise email
- [x] A further message on an already-classified conversation is never
      re-judged even when its own content, in isolation, would look
      noise-shaped
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Reporting the skip count through the orchestrators' own JSON summary —
  `T04`.
- Deriving/tweaking the noise-definition artifact's own content — `T01`/`T05`.
- Real-vault cutover — `T05`.

---

## Context / Notes

`ADR-018`'s own Decision, Alternatives Considered, and Consequences are
authoritative — read in full before implementing, especially the
Consequences' own note on assuming multi-minute relay latency is possible
and never assuming a hang.

**Added 2026-09-02 (decomposer pass):** this task now also `depends_on`
`REQ-SB-87-US-02-T06` (a sibling story's own task) — the "Sent is never
Noise" guard (`AC-08`) needs the real `direction` field that task delivers
on the email payload. Confirm `T06` has actually landed in the real,
current `ingest_email.py` before starting this task's own build.

---

## Implementation Log

**2026-09-02 (coder pass — built and live-verified).** Read `Pipeline.md`,
`Implementation/Learnings.md`, this story's own full text (including the
2026-09-02 Scenario 8/9/10 additions), `ADR-018` in full, `T02`'s own
Implementation Log (the real classifier profile's exact provisioned
shape) and its deployed `SOUL.md` directly
(`%LOCALAPPDATA%\hermes\profiles\email-capture-classifier\SOUL.md`),
`T06`'s own Implementation Log (the real `direction`/`to_recipients`/
`cc_recipients` fields already on `ingest_email.py`'s input payload),
`T01`'s own `derive_noise_definition.py` (the established real
`hermes [-p PROFILE] chat -Q --query-file <tmp file>` subprocess-dispatch
convention, timeout, and JSON-extraction technique reused here), and the
REAL current `ingest_email.py` before editing.

**What was built (`ingest_email.py` only, per `## Files to Modify`):**
- New module-level constants: `_CLASSIFIER_PROFILE =
  "email-capture-classifier"`, `_HERMES_EXE = "hermes"`,
  `_CLASSIFIER_TIMEOUT_SECONDS = 420`, `_NOISE_DEFINITION_RELATIVE_PATH
  = .second-brain/data/EmailCapture/noise_definition.json`,
  `_VALID_CLASSIFICATIONS = {"internal", "partner", "customer"}`
  (`T02`'s own locked lowercase values).
- `_read_noise_definition`, `_extract_json_object` (same
  find-first-`{`-then-`raw_decode` technique as
  `derive_noise_definition.py`, duplicated rather than imported — kept
  this task genuinely self-contained within its own `## Files to
  Modify`, no new cross-script import dependency on a sibling script
  built for an unrelated, out-of-band purpose), `_build_classification_
  question` (embeds the noise definition JSON verbatim + the new
  email's direction/sender/recipients-participants/subject/body), and
  `_classify_or_skip` (the one bounded relay subprocess call — same
  explicit-UTF-8-both-sides discipline as `run_delta_capture.py`'s own
  `run_script`).
- Inside `ingest_email()`'s own `if thread_path is None:` branch (the
  ONE place a first-seen-conversation decision is made, per `ADR-018`),
  BEFORE `vault_manager.create(...)`: call `_classify_or_skip(...)`;
  if `direction != "sent"` and `verdict["is_noise"]` is true, return
  early with `{"thread_created": false, "message_created": false,
  "thread_path": None, "message_path": None, "skipped_as_noise": true}`
  — no Thread, no RawMessage, no Person-note side effect (the whole
  `ensure_bare_person_note`/RawMessage-creation block sits AFTER this
  branch, entirely unreached on a genuine skip). Otherwise, validate
  `classification` is one of `_VALID_CLASSIFICATIONS` (raise, never
  fabricate, if not) and pass it through as the new Thread's own
  `classification` frontmatter value on the same `create()` call.
  Every other, already-existing return path now also carries
  `"skipped_as_noise": false` (additive field only).
- Module docstring extended to document the new relay-call mechanism,
  the return shape's new `skipped_as_noise` field, the Sent-guard, and
  the relay-failure degrade default — no change to any pre-existing
  documented behavior.

**Design choice, disclosed (Sent-guard mechanism — the task's own text
left this open as "coder's own disclosed choice" between (a) a
deterministic pre-relay guard or (b) an in-prompt instruction):** built
as a hybrid that is effectively (a) in practice — the relay IS still
called for a first-seen Sent message (a real `classification` value is
still needed, never fabricated), but `ingest_email.py`'s own code never
reads/branches on that verdict's `is_noise` field when `direction ==
"sent"` — the skip-return path is structurally unreachable for it,
regardless of what the classifier itself replies. This does not rely on
trusting `T02`'s own SOUL.md safety net (which its own text already
frames as secondary: "the calling script is expected to handle this rule
itself... honor it anyway if it reaches you") — the CALLER enforces the
rule by construction. New `MEMORY.md` Pattern entry added generalizing
this shape.

**Real, disclosed finding (non-blocking): `T02`'s deployed `SOUL.md` documents
`direction` as `"inbound"`/`"sent"`, but `T06`'s real field is
`"received"`/`"sent"`.** Non-blocking here because this task's own
Sent-guard (above) checks the real value literally for `"sent"` (which
matches) and never depends on the classifier itself recognizing
`"received"`/`"inbound"` for anything load-bearing — `direction` is
still passed through verbatim in the relay's own question text for the
classifier's own secondary safety net and general context. Logged as a
new `MEMORY.md` Constraint entry and a `REVIEW-QUEUE.md` pointer (a
`SOUL.md` wording correction, `T02`'s own file, out of this task's own
`## Files to Modify`).

**Relay-failure degrade default (per `ADR-018`'s own Consequences,
decomposer-level, this task's own implementation):** `_classify_or_skip`
raises (uncaught) on a non-zero relay exit code, an unparseable
response, a response missing `is_noise`, or a missing/unreadable
`noise_definition.json`; the Thread-creation branch also raises if a
non-noise verdict's own `classification` isn't one of the three valid
values. In every case, `ingest_email()` exits before `vault_manager.
create(...)` is ever reached — no Thread, no permanent skip recorded —
so `find_by_id` still returns `None` on the next call for the same
`conversation_id`, naturally retrying it (verified live below).

**Live verification (real, no mocks except where explicitly disclosed
below) — fresh scratch vault `C:\scratch-sb87t03\vault` (deleted after
verification), seeded with real copies of the live vault's own
`thread/Template.json` and `noise_definition.json`; the real, unmodified
`ingest_email.py` driven by directly importing the module (never
`subprocess`-spawning it) so a scoped, reverted `subprocess.run`
call-count wrap could be applied for the AC-03/AC-09 check only — every
other scenario made real, live `hermes -p email-capture-classifier chat
-Q ...` relay calls against the real, installed `hermes.exe`/Compass
Provider:**

- `[REQ-SB-87-US-03-AC-01]` **PASS.** A genuinely new conversation with
  real noise-definition-matching content (EY Payslip notification,
  `donotreply@ey.com`) returned `{"skipped_as_noise": true,
  "thread_created": false, "message_created": false, "thread_path":
  null, "message_path": null}`. Independently confirmed via
  `vault_manager.find_by_id` (returned `None`) AND a direct directory
  listing of the scratch vault's own `Work/Threads/` — no
  `conv-ac01-noise-*` directory exists anywhere. Zero vault trace.
- `[REQ-SB-87-US-03-AC-02]` **PASS.** A genuinely new, content-rich
  conversation (a Customer-specific renewal/go-live discussion naming a
  real external recipient domain) returned `thread_created: true`; the
  Thread's own real on-disk frontmatter (read via `vault_manager.
  read_note`, not stdout) carries `classification: "customer"`.
- `[REQ-SB-87-US-03-AC-03]` / `[REQ-SB-87-US-03-AC-09]` **PASS (both).**
  A SECOND message on the SAME already-classified `conversation_id`,
  deliberately using real noise-definition-matching content (a Compass
  Alert subject/body, taken from `T01`'s own seed examples) for the
  isolated-content check `AC-09`'s own wording names: `message_created:
  true`, a real second RawMessage file created under the Thread's own
  `messages/` folder (2 total), the Thread's own `classification` value
  unchanged (`"customer"`, confirmed by direct re-read), AND a scoped,
  reverted in-process wrap of `ingest_email.subprocess.run` (counts real
  calls, then calls straight through — never fakes a response) recorded
  **zero** relay calls made during this second `ingest_email()` call —
  a real subprocess-call-count proof, not just an end-state inference.
- `[REQ-SB-87-US-03-AC-06]` **PASS.** A real Inbox-received first
  message plus a real Sent-Mail second message on the SAME
  `conversation_id` (a live customer-renewal exchange) both landed in
  the SAME Thread — 2 real distinct message files under one `messages/`
  folder, the second call returning `thread_created: false,
  message_created: true` — the Sent item was never excluded merely for
  originating from the user's own mailbox, and the Thread's own
  classification (`"customer"`) was unaffected by the second message.
- `[REQ-SB-87-US-03-AC-08]` **PASS.** A genuinely new,
  `direction: "sent"` first message, deliberately given real
  noise-definition-matching content (reusing one of `T02`'s own seed
  examples, subject "Learning Assignment Changes Email Notification",
  relabeled as Sent) was NEVER skipped: `skipped_as_noise: false`,
  `thread_created: true`, the Thread's own real frontmatter carries a
  valid `classification: "internal"` (one of the three real allowed
  values, never `null`, never fabricated) — the classify-or-skip
  judgment's own `is_noise` value was never consulted for this message
  (per the Sent-guard's own structural design above), confirmed by the
  observed outcome (never skipped regardless of the noise-shaped
  content).
- (Unlabeled, supporting) **PASS.** An engineered relay failure (a
  scoped, disclosed in-process monkeypatch of `ingest_email.subprocess.
  run` returning a fake non-zero-exit result, reverted immediately
  after via `unittest.mock.patch.object`'s own context-manager exit) —
  `ingest_email()` raised the expected `RuntimeError`
  ("classify-or-skip relay failed (code 1): simulated relay timeout"),
  and `vault_manager.find_by_id` confirmed no Thread was created for
  that `conversation_id`. Immediately re-ran the SAME payload with the
  monkeypatch removed (a real, unpatched relay call): it succeeded
  normally, creating the Thread — confirming the conversation is
  naturally retried on the next call rather than permanently lost or
  silently defaulted either way.

**Compile check:** `python -m py_compile ingest_email.py` — clean (real
Python resolved via `py -0p`, same sandboxed-shell PATH-stub finding as
`T01`'s own Implementation Log).

**Scope-internal judgement calls (assumptions), logged for human
spot-check per Pipeline.md hard rule 5:**
1. The Sent-guard mechanism (a hybrid effectively-(a) design — see
   above) — the task's own text explicitly left the exact mechanism as
   "coder's own disclosed choice."
2. `T02`'s real deployed `SOUL.md` documents `direction` values that
   don't match `T06`'s real field (`"inbound"` vs. `"received"`) — see
   above; non-blocking, filed for a future `SOUL.md` wording fix.
3. Duplicated `_extract_json_object`'s JSON-extraction technique into
   `ingest_email.py` rather than importing it from
   `derive_noise_definition.py` — kept this task's own file scope
   genuinely self-contained per `## Files to Modify`, at the cost of
   ~15 duplicated lines.
4. The relay's own question-text format/wording (how the noise
   definition and email content are embedded) is this task's own
   disclosed construction — `ADR-018`/`T02` specify the CONTENT that
   must arrive (definition + sender/recipients/subject/body/direction)
   but not the literal prompt text shape.
5. An invalid/missing `classification` on a non-noise verdict is
   treated as a relay failure (raise, retry next tick) rather than
   fabricating a default value — a direct, disclosed reading of
   `ADR-018`'s own "never fabricate a positive create" principle,
   extended to this specific new failure mode.

No `ESCALATIONS.md` entry required — no out-of-scope event, no new
dependency beyond what `T02`/`T06` already deliver, no shared-interface
change, no ADR deviation; the pre-existing `REQ-SB-87-US-03`/`ADR-018`
`REVIEW-QUEUE.md` entry already covers the story-level human-review
flag this task inherits. `gate: flagged` here is the standard
scope-internal-judgement-call spot-check flag (assumptions 1-5 above),
not a new escalation — see the new `REVIEW-QUEUE.md` entry.

`MEMORY.md`: 2 new entries added (a Pattern — caller-side deterministic
override over trusting a model's own prompted safety net for a locked
business rule; a Constraint — the `direction` value doc/reality
mismatch). `CHANGELOG.md`: entry appended.

Task marked `Done` — all 8 locked/unlabeled Tests-block steps (`AC-01`,
`AC-02`, `AC-03`, `AC-06`, `AC-08`, `AC-09`, plus the relay-failure
degrade check) verified live with a real, positive result against a
real scratch vault and the real, installed classifier profile.
