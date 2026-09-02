---
id: REQ-SB-87-US-03-T05
title: Scratch-vault proving-phase verification, noise-definition retune pass, and cutover
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-03-T04]
created: 2026-09-01
updated: 2026-09-02
---

# REQ-SB-87-US-03-T05 — Scratch-Vault Proving-Phase Verification, Noise-Definition Retune Pass, and Cutover

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

The final closing task: prove the full classify-or-skip + classification
mechanism end-to-end against the real ~100-email scratch-sample proving
phase, demonstrate the noise definition can be retuned without any
Capture-stage code change, confirm Sent+Inbox regression-free, then
participate in the same `--vault-path` cutover `REQ-SB-87-US-02-T05`
performs (this story's own new judgment step rides along with that same
cutover — it is layered onto the SAME `ingest_email.py`, not a separate
deploy).

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T04` complete: noise-definition artifact + derivation, classifier
  profile, the wired relay call, and skip-count reporting all exist and
  individually verify against the scratch sample.

**After / Outputs:**
- A real, disclosed confirmation that the WHOLE mechanism (definition →
  relay call → skip-or-classify → skip-count reporting) works correctly
  end-to-end against the real 100-email sample, including a real retune
  cycle and Sent+Inbox regression check.
- This story's own code changes are included in whatever real, active
  Hermes profile / `--vault-path` cutover `REQ-SB-87-US-02-T05` performs
  (same script, same deploy — no separate cutover action of this story's
  own).

---

## Files to Modify

- None — verification-only, plus (as needed) re-running `T01`'s derivation
  mechanism against real feedback from this pass.

---

## Constraints

- Inherits from parent story.
- Same rollout/verification posture as `REQ-SB-87-US-02`: prove against the
  scratch sample first; the real-vault cutover happens together with that
  sibling story's own `T05`, not independently.
- Never run more than one capture job concurrently against the same vault.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
~100-email sample):**
1. `[REQ-SB-87-US-03-AC-04]` Read the currently-persisted noise-definition
   artifact directly (independent of any capture run); confirm it is real,
   structured, and was genuinely derived (not invented fresh mid-run) —
   cross-check against a capture run's own classify-or-skip decisions to
   confirm they trace back to this SAME persisted content.
2. `[REQ-SB-87-US-03-AC-05]` Deliberately broaden or narrow the noise
   definition (e.g. re-run `T01`'s derivation mechanism with adjusted
   sample/guidance, or a direct, disclosed manual edit for a quick,
   observable test); confirm the VERY NEXT capture run classifies against
   the updated definition, with zero change to any Capture-stage script's
   own code required.
3. `[REQ-SB-87-US-03-AC-06]` Run a full capture pass across the scratch
   sample; confirm real Sent Mail items are still combined with their
   Inbox counterparts into the same Thread exactly as before this story's
   own changes — a real, side-by-side regression check against a
   pre-classification-step baseline capture of the SAME sample (captured
   before `T03`'s edits, kept for comparison).
4. (Unlabeled, closing) Run the full scratch-sample capture one final
   time, end-to-end, confirming all 7 of this story's own locked ACs hold
   together in one real, combined run — not just individually.

**Automated tests:** `n/a — real-vault/scratch-vault verification`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Full end-to-end mechanism confirmed against the real scratch sample
- [x] Noise-definition retune cycle confirmed with zero code change
- [x] Sent+Inbox regression-free
- [x] All 10 of this story's own currently-locked ACs (`AC-01`..`AC-10` —
      the decomposer's own 2026-09-02 pass added `AC-08`/`AC-09`/`AC-10`
      after this task's own "7" wording above was written; verified
      against the CURRENT, real story state, a superset of the stale "7",
      see Implementation Log) hold together in one combined real run
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The actual `--vault-path` cutover action itself — performed once,
  jointly, by `REQ-SB-87-US-02-T05` (this story's own code rides along in
  the same `ingest_email.py` file that task cuts over).

---

## Context / Notes

This task exists to give the FULL, combined classify-or-skip mechanism its
own final, honest end-to-end pass, distinct from `T01`-`T04`'s own
individual-capability verifications.

---

## Implementation Log

**2026-09-02 (coder pass — verification-only, `Done`).** Read `Pipeline.md`,
`Implementation/Learnings.md`, this story's own full text (all 10 currently-
locked ACs, `AC-01`..`AC-10`), `ADR-018` in full, `architecture.md`'s own
`§Capture-Time Classification & Noise-Skip` section, and `T01`-`T04`'s own
Implementation Logs before starting.

**Scope boundary explicitly confirmed before starting (per the launching
agent's own instruction):** this task's own real, locked scope is
scratch-vault-only. Its own `## Files to Modify` is `None` (verification-
only); its own `## Out of Scope` explicitly names "The actual `--vault-path`
cutover action itself — performed once, jointly, by `REQ-SB-87-US-02-T05`."
**Nothing in this task's own real scope touched the REAL vault
(`C:\myWorx\Moussa MD\Moussa Brain`) or the REAL Hermes profile/cron
deployment for `job4`/`email-delta-capture`** — confirmed at the end of this
pass via `git status` (zero diff on any Hermes-Provisioning file — this
task's own `## Files to Modify` is `None`, and none was touched) and via
direct inspection (the real vault's own `.second-brain/data/EmailCapture/
noise_definition.json`, written by `T01`, was read-only copied from, never
written to, by this task). `REQ-SB-87-US-02-T05` (the real-vault
retrofit + live cron cutover) remains untouched, `status: Ready`, exactly as
found — not built, not started.

**Verification infrastructure (all under `C:\scratch-sb87t05\`, deleted
after this pass — never under the repo, never under the real vault):**
- `current/` + `baseline/` — two independent scratch vaults, each seeded
  with a real copy of the live vault's own `thread/Template.json` and
  (T01's real, already-derived) `noise_definition.json`.
- A real ~100-email sample (`sample_page1.json`) pulled ONCE via the real,
  unmodified `list_recent_emails.py` against live Outlook (`--limit 100`):
  100 real emails, 88 received / 12 sent, 55 unique `conversation_id`s
  (first-seen conversations), spanning 2026-08-21 → 2026-09-02 (~12 days) —
  a genuinely representative real sample, matching this story's own
  "~100-email scratch-sample proving phase" posture.
- **Baseline reconstruction technique (disclosed):** no literal pre-`T03`
  git commit exists for `ingest_email.py` (this repo's own `Hermes-
  Provisioning/` tree carries every `US-02`/`US-03` task's changes as
  uncommitted working-tree edits against one single earlier commit,
  confirmed via `git log --oneline` — there is no intermediate commit to
  diff against). Reconstructed the "captured before `T03`'s edits" baseline
  via an in-process monkeypatch of the REAL, unmodified
  `ingest_email.ingest_email()`'s own `_classify_or_skip` dependency
  (`unittest.mock.patch.object`, same established technique as `T03`'s own
  AC-03/AC-09 call-count wrap, `Implementation/Learnings.md` `SPRINT-018`
  precedent) — a deterministic stub always returning
  `{"is_noise": false, "classification": "internal"}` with ZERO real relay
  call, which reproduces the exact EFFECT of pre-`T03` code on Thread/
  RawMessage creation and Sent+Inbox combining (unconditional create, no
  skip capability) while still exercising the real, unmodified `create()`/
  `create_dynamic_child()`/person-note logic. (A PATH-based `hermes.cmd`
  stub was tried FIRST and abandoned — real, disclosed finding: Python's
  `subprocess.run([...], shell=False)` on Windows resolves a bare command
  name via `CreateProcess`, which only auto-appends `.exe`, never the full
  `PATHEXT` list `cmd.exe` itself uses — a `.cmd`/`.bat` shim earlier in
  `PATH` is silently skipped in favor of a later `.exe` match. New
  `MEMORY.md` Constraint entry.)
- The SAME byte-identical 100-email sample was fed, in order, through both
  the baseline harness (monkeypatched) and a "current" harness (the REAL,
  unmodified `_classify_or_skip` — real subprocess relay calls to the real,
  installed `email-capture-classifier` profile) into the two separate
  scratch vaults.
- **A real bug in this task's OWN throwaway harness (not production code)
  found and fixed live:** the harness's own `print()` of a real email
  subject containing an emoji (`"CRM Enhancements | Weekly Release Summary
  🚀"`, a REAL, live, currently-recurring email subject in the real
  mailbox — a near-exact recurrence of one of `T01`'s own 5 seed examples,
  9 days later) crashed with `UnicodeEncodeError` against the sandboxed
  shell's cp1252 console — the SAME class of finding `MEMORY.md` already
  documents for `list_recent_emails.py`/`derive_noise_definition.py`. Fixed
  by wrapping `sys.stdout` in a UTF-8 `TextIOWrapper` and resumed from
  email #29 (the crash happened in `print`, AFTER the real vault write for
  that email had already succeeded and been flushed to the progress log —
  confirmed directly, zero data lost, zero re-run of already-completed real
  relay calls needed).
- **A separate, third real-orchestrator pass** (`run_delta_capture.py`,
  completely unmodified, invoked for real via `subprocess`/`SECOND_BRAIN_
  VAULT_PATH` against a FRESH, separately-seeded scratch vault with a
  20-minute-old watermark, so the real, live Outlook pull it performs
  internally stays small and bounded rather than repeating the full
  ~100-email/55-relay-call cost a second time) proved the TRUE production
  entry point end-to-end — real `list_recent_emails.py` → real
  `ingest_email.py` (the real classify-or-skip code, invoked as a genuine
  `subprocess.run([PYTHON, "ingest_email.py", ...])` child process, never
  direct-imported) → real orchestrator aggregation, all in one real,
  unmocked chain nobody had exercised together before this pass (`T03`'s
  own verification used direct import; `T04`'s own verification mocked the
  `ingest_email.py` subprocess boundary itself).

**Live verification results, all real, against the artefacts above:**

- `[REQ-SB-87-US-03-AC-04]` **PASS.** The real, persisted `noise_
  definition.json` was read directly and independently (a fresh script,
  no capture run involved) — real, structured content (`category`,
  `description`, 6 `criteria`, `positive_signals`, `negative_signals`,
  `derived_at`), matching `T01`'s own already-derived artifact exactly (a
  read-only copy, never re-derived by this task). Cross-checked against 2
  real classify-or-skip verdicts (one noise, one non-noise) re-issued for
  already-processed sample emails: each verdict's own `reasoning` text
  explicitly cites concepts straight out of the persisted definition
  (e.g. "templated Service Portal update... automated/broadcast
  notification criteria" for a real skipped ServiceNow ticket-update
  email; "no external customer or partner" for a real non-noise internal
  email) — the decision traces to the SAME persisted content, not a
  fresh, un-recorded judgment.
- `[REQ-SB-87-US-03-AC-05]` **PASS.** A real, disclosed manual edit to a
  SCRATCH copy of the definition (adding one `negative_signals` entry
  explicitly carving out "release/changelog summaries... are NEVER
  noise") flipped the SAME real email ("CRM Enhancements | Weekly Release
  Summary") from `is_noise: true` (before) to `is_noise: false` (after) —
  two real relay calls, zero change to `ingest_email.py` or any other
  Capture-stage script (imported completely unmodified both times; only
  the JSON artifact file changed).
- `[REQ-SB-87-US-03-AC-06]` **PASS.** Side-by-side comparison, baseline vs.
  current, across all 45 non-noise conversations in the current run: ZERO
  message-set mismatches (the exact same messages combine into the exact
  same Thread in both passes) — the classify-or-skip step changes WHICH
  conversations get a Thread at all (10 correctly excluded), never HOW
  Sent+Inbox items already destined for a Thread combine. 3 real
  conversations in the current run genuinely combine a Sent item with an
  Inbox item into one Thread (confirmed via real on-disk frontmatter
  `direction` values on the baseline vault's own messages, e.g. a real
  "Re: Masdar Cloud Strategy" Thread combining 2 received + 1 sent
  message).
- **(Unlabeled, closing) all 10 currently-locked ACs, one real, combined
  100-email run:** **PASS.** `current_results.json` — 100/100 emails
  processed, ZERO errors/exceptions, 55 unique conversations → 45 real
  Threads created + 10 correctly skipped as noise (`45 + 10 = 55`, exact).
  Confirmed directly on disk (not just the returned JSON): exactly 45
  real Thread directories exist under the scratch vault's own
  `Work/Threads/` — the 10 skips left literally zero directory trace
  (`[REQ-SB-87-US-03-AC-01]` **PASS**, disk-level proof). All 45 real
  Threads carry exactly one valid `classification` value, zero null/
  invalid (`customer: 23, internal: 18, partner: 4`) (`[REQ-SB-87-US-03-
  AC-02]` **PASS**). Every repeat message on an already-classified
  conversation (8 real cases across the run) shows `0.0s` elapsed with no
  relay call and an unchanged `classification` value on re-read
  (`[REQ-SB-87-US-03-AC-03]`/`[REQ-SB-87-US-03-AC-09]` **PASS**,
  reconfirming `T03`'s own call-count proof at combined-run scale). All
  12 real Sent messages in the sample: zero skipped as noise, 9 genuinely
  first-seen Sent conversations all correctly classified
  (`[REQ-SB-87-US-03-AC-08]` **PASS** at combined-run scale). The 10 real
  skips are all genuinely, unambiguously noise-shaped on manual content
  inspection — 2 real ServiceNow ticket auto-updates, a real Teams
  "X sent a message" notification (`no-reply@teams.mail.microsoft`), a
  real, LIVE recurrence of "CRM Enhancements | Weekly Release Summary"
  (one of `T01`'s own 5 locked seed subjects, 9 days later, same
  sender-alias shape), "Deal Governance... Phase 2 Now Live", a real,
  LIVE recurrence of "Learning Assignment Changes Email Notification",
  two real recurrences of "New Payslip available", "Welcome to EY
  Interact Payroll", and a real, LIVE recurrence of "Core42 Information
  Security Awareness Training" — **zero apparent false positives** (no
  real human signal wrongly skipped), the higher-risk failure mode per
  this task's own launching instruction, given more scrutiny than false
  negatives. Spot-checked 3 borderline non-noise cases by reading real
  body content directly (an empty-subject personal email from a personal
  address, a real "Automatic reply" OOF from a real colleague with
  specific personal business content, a real "RE:" reply inside an
  active partner conversation whose ORIGINAL message happened to be a
  workshop invite) — all 3 correctly judged non-noise, genuine signal,
  not broadcast content. `[REQ-SB-87-US-03-AC-10]` **reconfirmed** (`T02`
  already verified this live in full) via 4 real, LIVE, unplanned
  recurrences of near-identical seed-shaped content 9 days later, all
  correctly caught. Separately, the real, unmodified `run_delta_capture.py`
  orchestrator (never direct-imported, a genuine `subprocess`-dispatched
  child process) ran end-to-end against a bounded, freshly-seeded scratch
  vault: 9 real new emails, 5 Threads created, 7 messages, 3 attachments,
  **2 correctly skipped as noise**, zero per-email failures, a real,
  accurate `skipped_as_noise: 2` written to the real `SUMMARY_PATH` JSON
  file (`[REQ-SB-87-US-03-AC-07]` reconfirmed through the TRUE production
  entry point — `T04`'s own verification had scoped-monkeypatched the
  `ingest_email.py` subprocess boundary itself; this pass is the first
  real, fully-unmocked, subprocess-to-subprocess proof of the whole
  chain). The 5 real Threads this independent orchestrator-level run
  created exactly match 5 of the direct-call run's own 45 (byte-identical
  real-world decisions from two structurally independent invocation
  paths) — strong corroborating cross-validation.

**Real, disclosed finding, reconfirmed with fresh live evidence (already
known, already filed — NOT fixed here, out of this task's own `## Files to
Modify`):** the real orchestrator-level run above directly reconfirmed
`REQ-SB-87-US-02-T06`'s own already-disclosed `REVIEW-QUEUE.md` finding —
`run_full_capture.py`/`run_delta_capture.py`'s own `ingest_payload`
construction still does not forward the real `direction` field to
`ingest_email.py` (every RawMessage this orchestrator-level pass created
shows `direction: ""` on disk, even for a real, known-Sent message). This
means the `AC-08` "Sent items never Noise" CALLER-side guard is not yet
reliably reachable through the live cron path specifically (though it IS
fully, structurally correct and proven at the `ingest_email()` function
level, `T03`'s own scope and this task's own direct-call runs above, both
of which pass `direction` explicitly). No new email in this task's own
small bounded orchestrator sample happened to be BOTH first-seen AND
noise-shaped AND Sent, so no incorrect skip was actually observed live —
but the underlying gap is real and unfixed. Already tracked at
`REVIEW-QUEUE.md` → `REQ-SB-87-US-02-T06` entry, with its own "What to
do" pointing at `REQ-SB-87-US-02-T05`'s own future cutover pass (a
one-line fix to 2 files outside this task's own scope) — not duplicated
here, only reconfirmed with fresh evidence.

**Retune decision (per this task's own Objective — "RETUNE... if the real
results reveal it's mis-classifying anything"):** the REAL vault's own
already-persisted `noise_definition.json` (`T01`'s work) was NOT retuned.
Across a genuinely real, unseen, ~12-day/100-email sample, it produced
zero apparent false positives and correctly caught every real noise-shaped
email including several LIVE, unplanned recurrences of its own original
seed content — no misclassification was found that would justify a real
change to the REAL vault's own artifact, and per this task's own explicit
scratch-vault-only boundary, no such change was attempted regardless. The
`[REQ-SB-87-US-03-AC-05]` retune-CYCLE mechanism itself (the actual locked
AC) was proven separately, entirely inside the scratch `retune/` vault,
never touching the real one.

**Scope-internal judgement calls, disclosed (not `gate: flagged` — each is
an established, already-precedented VERIFICATION technique, matching
`T04`'s own identical "disclosed technique, not a fresh assumption"
`gate: clear` precedent, not a business/architecture decision):**
1. Baseline reconstruction via in-process monkeypatch of `_classify_or_
   skip` (above) rather than a literal git-history diff (none exists).
2. Sample size/window: the real, live 2-day `run_delta_capture.py`
   bootstrap lookback (unmodified, untouched) naturally produced the
   ~100-email sample via a single `list_recent_emails.py --limit 100`
   pull, matching this story's own "~100-email scratch-sample proving
   phase" language without needing to hand-curate a sample.
3. The bounded, 20-minute-watermark orchestrator-level pass (rather than
   a second full ~100-email/55-relay-call repeat through the real
   orchestrator) — a disclosed, deliberate scope-bounding of an otherwise
   redundant real-relay-call cost, matching `Implementation/Learnings.md`'s
   own "bound a live-data verification to a real, filtered subset" pattern
   (`SPRINT-028`).

No `ESCALATIONS.md` entry — no out-of-scope event, no new dependency, no
shared-interface change, no ADR deviation. No new `REVIEW-QUEUE.md` entry
either — the one real, disclosed finding above (the orchestrator
`direction`-forwarding gap) is a RECONFIRMATION of `REQ-SB-87-US-02-T06`'s
own already-open entry, not a new discovery; duplicating it would only
fragment the same open item (`Implementation/Learnings.md`'s own
`SPRINT-048` antipattern — give a genuinely separate risk its own line,
but don't re-file the SAME already-tracked one a second time).

`MEMORY.md`: 2 new entries — a Constraint (Windows `subprocess.run(...,
shell=False)` only auto-appends `.exe` when resolving a bare PATH command
name, never the full `PATHEXT` list; a `.cmd`/`.bat` PATH shim is silently
skipped) and a Pattern (reconstructing a "before this task's own code
change" regression baseline via a scoped, in-process monkeypatch of the
one specific dependency function the change added, when no literal
pre-change git commit exists). `CHANGELOG.md`: entry appended.

**Story-level closure:** all 5 tasks (`T01`-`T05`) of `REQ-SB-87-US-03`
are now `Done`; all 10 locked ACs verified live with real, positive
results (this task's own combined run re-verified all 10 together; `T01`-
`T04` each already verified their own subset individually). Per this
task's own launching instruction, `REQ-SB-87-US-03` is set `status: Done`
below — `SPRINT-084` stays `In Progress` (its sibling story
`REQ-SB-87-US-05` remains `Ready`, untouched by this task).

Task marked `Done` — every locked AC mapped to this task
(`AC-04`/`AC-05`/`AC-06`, plus the unlabeled closing combined-run step
covering all 10) verified live with a real, positive result against a
real scratch vault, a real ~100-email sample, and the real, installed
classifier profile. Nothing in this task's own real scope touched the
real vault or the real Hermes profile/cron deployment.
