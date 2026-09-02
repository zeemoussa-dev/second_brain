---
id: REQ-SB-87-US-03-T02
title: Provision the dedicated Capture-classifier Hermes profile
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "trigger-scope-internal-judgement-calls (Pipeline.md: scope-internal judgement calls are logged as assumptions in the Implementation Log and flag the task for human spot-check) — see Implementation Log below and REVIEW-QUEUE.md"
phase: P1
depends_on: [REQ-SB-87-US-03-T01]
created: 2026-09-01
updated: 2026-09-02
---

# REQ-SB-87-US-03-T02 — Provision the Dedicated Capture-Classifier Hermes Profile

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Provision a new, dedicated, lightweight Hermes profile that answers ONE
bounded `chat -q` relay question per genuinely-new conversation — "is this
noise, and if not, what's its coarse classification?" — per `ADR-018`'s
Decision.

---

## Starting State → End State

**Before / Inputs:**
- No dedicated classifier profile exists.
- `T01`'s noise-definition artifact exists at
  `.second-brain/data/EmailCapture/noise_definition.json`.
- Real precedent for a lightweight, non-agentic-loop relay-target profile:
  `research-agent` (`REQ-SB-82-US-02`), provisioned via `hermes profile
  create <name> --clone` at `%LOCALAPPDATA%\hermes\profiles\<name>\`.

**After / Outputs:**
- A new, real, live Hermes profile (a disclosed name, e.g.
  `email-capture-classifier`) provisioned at
  `%LOCALAPPDATA%\hermes\profiles\<name>\`.
- Its own `SOUL.md` instructs it to: read the noise-definition artifact's
  own current content (passed in the relay call's own question text, or
  read directly if the profile has vault access — this task's own disclosed
  choice) plus the new email's own sender/subject/body (also passed in the
  question text); reason about whether it matches the noise definition;
  return ONE structured JSON verdict — conceptually `{"is_noise": bool,
  "classification": "internal" | "partner" | "customer" | null, "reasoning":
  str}` (exact field names this task's own call, matching `ADR-018`'s own
  illustrative shape) — and NOTHING ELSE (no tool-calling loop, no
  multi-turn follow-up expected; a single bounded `chat -q` reply).
- No cron job for this profile — it is invoked ONLY as a one-shot relay
  target from `ingest_email.py` (`T03`), never on its own schedule.
- No vault-write capability granted — this profile only ever answers a
  question; it never writes a note itself (the calling script does that).

---

## Files to Modify

- None new in the repo's own version control (mirrors
  `REQ-SB-82-US-05-T02`'s own established precedent — real, live Hermes-side
  profile provisioning has no further checked-in-repo file to diff, beyond
  whatever the coder discloses in this task's own Implementation Log).

---

## Constraints

- Inherits from parent story.
- **The agent decides, the script only applies** — this profile's own
  SOUL.md must instruct it to return a real, honest verdict based on actual
  reasoning over the definition + email content, never a rubber-stamp
  "not noise" default.
- The verdict's own `classification` value must be exactly one of
  Internal-only / Partner-related / Customer-related when `is_noise` is
  `false` — never fabricated, never `Noise` (a noise Thread is never
  created at all, so `classification` is meaningless/`null` when
  `is_noise` is `true`).
- No tool-calling loop — this is a bounded, single-reply relay target, not
  an agentic session with `search_files`/`terminal` access to the vault.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-03-AC-02]` Issue a real, direct relay call (`hermes -p
   <classifier-profile> chat -q "..."`) with a genuine non-noise email's
   content (sender/subject/body) plus the current noise definition;
   confirm the returned verdict has `is_noise: false` and a real
   `classification` value of exactly one of Internal-only/Partner-related/
   Customer-related.
2. `[REQ-SB-87-US-03-AC-01]` Issue the same relay call with content that
   genuinely matches the current noise definition (e.g. an obvious
   automated notification/newsletter pattern the definition names);
   confirm `is_noise: true`.
3. `[REQ-SB-87-US-03-AC-10]` (added 2026-09-02) Issue five separate real
   relay calls, one per real seed example subject already confirmed
   noise-shaped in the story's own Constraints: "Learning Assignment
   Changes Email Notification", "New Payslip available for
   viewing-download", "Core42 Information Security Awareness Training",
   "Compass Alert- Failed API Calls", "CRM Enhancements - Weekly Release
   Summary" (a plausible real sender/body for each, since the classifier
   reasons over full content, not just the subject line). Confirm all
   five return `is_noise: true`. Then read `T01`'s own persisted
   `noise_definition.json` directly and confirm its content explicitly
   frames the category as "anything automated/broadcast" (system/HR/
   security notifications, broadcast newsletters, event-announcement
   blasts) — broader than, and not limited to, literal meeting-invite
   `.ics` items (already filtered upstream via `MessageClass`, outside
   this classifier's own scope).
4. (Unlabeled, supporting) Confirm the profile has NO vault-write
   capability and no cron job of its own.

**Automated tests:** `n/a — real, live Hermes-side profile provisioning;
verified via real relay calls`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Real, live classifier profile provisioned
- [x] Returns a real, structured `{is_noise, classification, reasoning}`
      verdict for both a noise and a non-noise real input
- [x] All five real seed-example subjects (added 2026-09-02) return
      `is_noise: true`; the noise definition's own content frames the
      category as "anything automated/broadcast," not limited to `.ics`
      meeting invites
- [x] No vault-write capability, no cron job of its own
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring the actual relay CALL into `ingest_email.py` — `T03`.
- The noise-definition artifact itself — `T01`.

---

## Context / Notes

`ADR-018`'s own Decision + Alternatives Considered (the rejected
bespoke-direct-HTTP-client and static-system-prompt options) are
authoritative. `REQ-SB-82-US-05-T02`'s own Implementation Log is the
closest real precedent for how live Hermes profile provisioning is
disclosed in this pipeline's own task-file convention — read it before
starting.

**Added 2026-09-02 (decomposer pass):** `AC-10`'s own five real seed
example subjects (operator-confirmed noise-shaped) are added here as this
task's own positive-case test batch, not as new profile-provisioning
scope — `T01`'s own derivation mechanism is separately expected to
incorporate the same five subjects as guidance/sample content for whatever
(re)derivation actually produces `noise_definition.json`'s content (see
`T01`'s own updated Tests), so this task's own check and `T01`'s own
derivation are mutually reinforcing, not duplicative.

---

## Implementation Log

**2026-09-02 (coder pass — built and live-verified).** Read `ADR-018` in
full again, this story's own Scenario 8/9/10 text, `T01`'s own
Implementation Log (the closest real precedent for the derivation-side
relay), and `REQ-SB-82-US-05-T02`'s Implementation Log (the closest real
precedent for live Hermes profile provisioning — `hermes profile create
<name> --clone`).

**What was built (real, live Hermes-side infrastructure, no repo file —
matches this task's own `## Files to Modify`):**

- `hermes profile create email-capture-classifier --clone --description
  "..."` — a new, real, live profile at `%LOCALAPPDATA%\hermes\profiles\
  email-capture-classifier\`, cloned from the currently-active `default`
  profile (confirmed via `hermes profile list`, the `◆` marker) so it
  inherits the real Compass/`gpt-5` model/provider config and the real
  `OBSIDIAN_VAULT_PATH` needed for an actual Provider round trip.
- **Structural "no tool-calling loop, no vault-write capability"
  enforcement (a disclosed scope-internal judgement call, beyond the
  task's own literal "clone" example):** a plain `--clone` inherits
  `default`'s full 78-skill set (`obsidian`, `email-thread-capture`,
  `hermes-obsidian-standalone`, `opp-manager`, etc. — all real vault-write
  capability) and its full `platform_toolsets.cli` list
  (`terminal`/`file`/`code_execution`/`browser`/`cronjob`/...). Rather than
  relying on SOUL.md prose alone to keep the classifier from ever touching
  a tool, two structural changes were made on the new profile so "no tool
  use" is true by construction, not just by instruction:
  1. Deleted the profile's entire cloned `skills/` directory (confirmed
     via `hermes -p email-capture-classifier skills list`: 78 → 0 skills;
     `hermes skills opt-out --remove --yes` alone only strips *bundled*
     skills, not the ~13 *local*, project-specific ones also copied by
     `--clone` — those needed a direct filesystem removal, since `hermes
     skills uninstall` only supports hub-installed skills).
  2. Edited the profile's own `config.yaml`: `platform_toolsets.cli: []`
     (was the full inherited list) — no toolset (`terminal`, `file`,
     `skills`, `code_execution`, `cronjob`, `browser`, etc.) is reachable
     from a CLI-sourced session on this profile at all, regardless of how
     the relay call is later invoked in `T03`.
  This satisfies "No vault-write capability granted" and "No tool-calling
  loop" as real, structural profile properties, not just prompt discipline
  — confirmed live below (session export shows `tool_call_count: 0`
  across every real relay call made during this task's own verification,
  and no new/modified file appeared anywhere under the real vault's
  `Work/` tree across the whole verification pass).
- **No cron job created** — `hermes -p email-capture-classifier cron
  list` confirms "No scheduled jobs" throughout; this profile is never
  invoked except as a one-shot relay target from `ingest_email.py`
  (`T03`).
- **`SOUL.md`** — fully replaced (the cloned `default` persona is
  irrelevant to this profile). Instructs: this profile is reached exactly
  once per genuinely-new conversation via a single bounded `chat -q`
  relay call; everything needed (the current noise-definition JSON,
  verbatim; the new email's sender/recipients-participants/subject/body;
  optionally `direction`) arrives embedded in the question text; judge
  noise against the GIVEN definition's own criteria/signals (never a
  fixed keyword list, never a fresh definition invented on the spot);
  when not noise, classify as exactly one of `"internal"` / `"partner"` /
  `"customer"` (never `null` in that case); reply with **exactly one JSON
  object and nothing else** —
  `{"is_noise": bool, "classification": "internal"|"partner"|"customer"|null,
  "reasoning": str}` — matching `ADR-018`'s own illustrative field names
  verbatim, per this task's own Objective text; never use any tool; never
  write to the vault; never rubber-stamp either verdict as a "safe"
  default. A narrow, explicitly-scoped safety net instructs it to never
  mark a `direction: "sent"` message Noise IF that field is given — the
  actual guard (never relaying a Sent-sourced first message for judgment
  at all) is correctly left to `T03`'s own caller-side logic, per this
  task's own Out of Scope / the operator's own "that's the CALLER's job"
  framing; this profile's own text makes that division of labor explicit
  rather than silently duplicating logic that belongs one layer up.
- **Live-discovered SOUL.md refinement (disclosed):** the first real
  non-noise verification call (below) returned a technically-valid but
  arguably-wrong `classification: "internal"` for a real, customer-related
  email, because only `sender`/`subject`/`body` were passed — the actual
  Customer/Partner participants were only present in the quoted reply
  chain, not the visible sender field. Widened `SOUL.md`'s "What you
  receive" section to explicitly include recipients/participants (when
  given) and added one paragraph instructing the classifier to decide
  `classification` from **everyone genuinely part of the conversation**,
  not just the one visible sender — re-verified live immediately after
  (below), correctly returning `"customer"` once given the same email's
  real recipients/Cc. Logged here as a real, live finding for `T03`'s own
  caller-side design: the relay call must pass real recipient/participant
  data, not sender-only, for the classification half to be accurate.

**Live verification (real, no mocks) — 7 real relay calls total, all via
the real, installed `hermes.exe` against the real Compass/`gpt-5`
Provider, real content read directly from the real vault's own Thread/
RawMessage notes under `Work/Threads/` (read-only):**

- **`[REQ-SB-87-US-03-AC-10]`** — all 5 real operator-confirmed seed
  subjects, using their own real RawMessage body content read directly
  from the vault (`2026-07-27 Compass Alert- Failed API Calls`,
  `2026-08-24 Core42 Information Security Awareness Training`,
  `2026-08-25 Learning Assignment Changes Email Notification`,
  `2026-08-25 New Payslip available for viewing-download`, `2026-08-31
  CRM Enhancements - Weekly Release Summary`), each relayed independently
  against the real, current `noise_definition.json` (`T01`'s own
  persisted artifact, read fresh from the real vault immediately before
  this run). **All 5 returned `is_noise: true`, `classification: null`**,
  with real, content-specific `reasoning` for each (e.g. "automated
  system alert... 'do not reply'"; "automated compliance/training
  notice... deadline... Orbit Learning Hub"; "automated payroll notice
  from donotreply@ey.com... 'Click here to login'"). **PASS.** Also
  re-confirmed the persisted `noise_definition.json`'s own
  `definition.category` is `"Automated/Broadcast Notifications"` with a
  description spanning system/HR/security notifications, broadcast
  newsletters, and release/event announcements, and zero mention of
  meeting invites anywhere in it (independently re-read directly from the
  real vault file, not just trusted from `T01`'s own prior write-up) —
  the second half of `AC-10`'s own wording. **PASS.**
- **`[REQ-SB-87-US-03-AC-02]`** — a real, content-rich, genuinely
  non-noise email (`2026-07-21 Action Required- Compass Activation
  Blocked for Dubai Future Foundation`, tags `partner/core42`,
  `customer/microsoft` in the real vault), real content read directly
  from its own RawMessage note. First pass (sender/subject/body only):
  `is_noise: false`, `classification: "internal"` (the live finding
  above — a real, valid value from the allowed set, just not the most
  accurate one given incomplete input). Second pass, same email, with its
  own real recipients/Cc added to the relay's question text (per the
  SOUL.md refinement above): `is_noise: false`, `classification:
  "customer"`, reasoning: "...the thread centers on a specific customer
  activation (DFF) with external coordination (Microsoft), so it's a
  customer-related conversation" — matching the real Thread's own
  existing `customer/microsoft` tag. **PASS, and confirms the classifier
  does NOT default everything to Noise** (the launching agent's own
  explicit requirement) — a real, substantive, correctly-reasoned
  non-noise verdict, not a rubber stamp.
- **`[REQ-SB-87-US-03-AC-01]`** — covered by the same 5 seed-example
  calls above (`AC-10`'s own cases are also real, live `AC-01` positive
  cases — genuinely-new-conversation content matching the current noise
  definition, correctly judged noise) plus the general mechanism proof
  the non-noise case above provides (the classifier distinguishes both
  directions on real content, not just one). **PASS.**
- **Re-verification after the SOUL.md refinement:** re-ran the
  `seed1-compass-alert` case a third time after widening `SOUL.md` (the
  edit only added participant-based classification guidance, never
  touched the noise-judgment section) — still `is_noise: true,
  classification: null`, confirming the refinement did not regress noise
  detection. **PASS.**
- **No tool-calling loop — structurally confirmed, not just asserted:**
  exported the first real session
  (`hermes -p email-capture-classifier sessions export ... --format
  jsonl`) and read it directly: `"tool_call_count": 0`, `"message_count":
  2` (one user turn, one assistant reply), `"api_call_count": 1` — a
  real, single, bounded relay turn with zero tool invocations, matching
  this task's own Objective ("no tool-calling loop, no multi-turn
  follow-up... a single bounded `chat -q` reply") by construction, not
  just by SOUL.md instruction. **PASS.**
- **No vault-write capability — confirmed by real absence of effect, not
  just by configuration:** across all 7 real relay calls made during this
  task's own verification pass, `find "Work/Threads" -newermt <before
  this pass started>` against the real vault returned zero files — no
  Thread, RawMessage, or any other note was created or modified anywhere
  in the vault by this profile, consistent with `tool_call_count: 0` and
  the emptied `platform_toolsets.cli`/deleted `skills/` above. **PASS.**
- **No cron job of its own:** `hermes -p email-capture-classifier cron
  list` → "No scheduled jobs" (checked both before and after the full
  verification pass — this task never ran `cron create`). **PASS.**

**Scope-internal judgement calls (assumptions), logged for human
spot-check per Pipeline.md hard rule 5:**
1. **Stripped ALL skills and emptied `platform_toolsets.cli` on the
   cloned profile**, beyond what a plain `--clone` (this task's own named
   precedent) provides on its own — needed because `--clone` inherits
   `default`'s full, vault-write-capable skill set and toolset list, which
   would otherwise leave "no vault-write capability, no tool-calling loop"
   resting on SOUL.md prose alone rather than being structurally true.
   Neither `ADR-018` nor this task's own text specifies this exact
   mechanism; a stronger, structural enforcement was chosen over a
   prompt-only one.
2. **`classification` field values are the exact lowercase strings
   `"internal"`/`"partner"`/`"customer"`**, matching this task's own
   Objective text verbatim (itself matching `ADR-018`'s own illustrative
   shape) — not the title-case PRD/story prose ("Internal-only",
   "Partner-related", "Customer-related"); `T03`/`T04`/`T05` and any
   frontmatter-writing code downstream should treat these three lowercase
   strings as the real, load-bearing values.
3. **Widened SOUL.md to request recipients/participants, not just
   sender/subject/body**, a real, live-discovered necessity for accurate
   `classification` (see the live-discovered-refinement write-up above) —
   `T03`'s own relay-call construction must pass real recipient/
   participant data (the Thread/RawMessage's own `participant_links`,
   already captured by `REQ-SB-87-US-02`) for classification accuracy to
   hold in production, not sender-only.
4. **`agent.reasoning_effort` left at the inherited `medium`** (not
   lowered for speed) — a real, disclosed judgement call favoring
   classification accuracy over per-call latency, given `ADR-018`'s own
   Consequences already accept variable relay latency as a real,
   disclosed trade-off; revisit if `T03`/`T05`'s own live capture-tick
   timing shows this mattering in practice.

No `ESCALATIONS.md` entry required — no out-of-scope event, no new
dependency, no shared-interface change, no ADR deviation; the
pre-existing `REQ-SB-87-US-03`/`ADR-018` `REVIEW-QUEUE.md` entry already
covers the story-level human-review flag this task inherits. `gate:
flagged` here is the standard scope-internal-judgement-call spot-check
flag (assumptions 1-4 above), not a new escalation — see the new
`REVIEW-QUEUE.md` entry.

`MEMORY.md`: new Pattern entry added (structural toolset/skill stripping
for a bounded, zero-tool relay-target profile). `CHANGELOG.md`: entry
appended.
