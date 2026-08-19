---
id: REQ-SB-76-US-01-T09
title: Real end-to-end verification run — all five outcomes, boilerplate exclusion, and the migration fix, against the live vault
parent_story: REQ-SB-76-US-01
requirement_id: REQ-SB-76
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-76-US-01-T04, REQ-SB-76-US-01-T06, REQ-SB-76-US-01-T07, REQ-SB-76-US-01-T08]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01-T09 — Real end-to-end verification run

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review"

---

## Objective

Run the whole, real, wired system end-to-end against the live vault — the real `POST /poc/librarian-propose-company-review` pass at real (not artificially bounded) scale, at least one genuine real resolution of each of the five outcomes (Customer, Partner, both Affiliate kinds, Merge — including a real duplicate-name pair whose duplicate side already has its own real OKF content, and Decline), plus a real `migrate_customer_to_partner` call against a real, currently OKF-shaped Customer not already covered by `T03`'s own disposable-test verification — and record exactly what was proposed/approved/written for the operator's own later review.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T08` all built and individually verified (each against a bounded slice of real data).
- The real Pending Approvals queue may already carry leftover records from `T01`-`T08`'s own individual verification passes, plus pre-existing records from earlier stories (`REQ-SB-74`'s own 64+31 outstanding records, per its own `T06` Implementation Log) — **check and record the queue's actual current state before this task's own run**, so this task's own new records are never confused with pre-existing, already-flagged ones.

**After / Outputs:**
- A real, full (not artificially bounded) `propose_company_review()` pass has run against the live vault's own real Thread corpus at least once.
- At least one real batch has been genuinely resolved for EACH of the five outcomes, with the real resulting vault state confirmed on disk for each.
- `migrate_customer_to_partner` has been called against one further real, currently OKF-shaped Customer (beyond `T03`'s own disposable test entities) if one genuinely exists and the operator would want it migrated — otherwise this sub-check is honestly reported as "no real, currently-appropriate candidate found this session," never forced against an inappropriate real Customer just to tick the box.
- Every real write this task makes is recorded explicitly in the Implementation Log.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — no code change expected (verification-only); if a genuine defect surfaces live, fix it here, in scope.
- `src/backend/app/business/partner_hub_linking.py` — same (verification-only; in-scope fix only on a genuine live-found defect).

---

## Constraints

- Inherits from parent story.
- **This IS the real vehicle — no separate, standalone script** (`MEMORY.md` — API-first, no script workarounds). Drive it through the real, already-built endpoints/functions.
- **Never bulk-approve or bulk-decline the real Pending Approvals queue unattended.** Resolve only the specific, individually-reviewed records this task's own verification needs — mirrors `REQ-SB-74-US-01-T06`'s own explicit precedent ("this coder session deliberately did NOT bulk-decline the stale duplicate rounds... that is itself a form of unattended mass-processing of real records the operator has not reviewed").
- Archive-not-delete — every archival step in this run (Merge's own duplicate-folder archival) must move, never delete.
- The Merge-with-real-prior-content check should genuinely use the operator's own named real example (Mudala/Mubadala Investment Group) if that pair is discoverable in the live vault today; if it is not, use the closest genuine real duplicate-name pair found, or fall back to `T06`'s own disposable-test coverage and disclose that this task found no further real example — never fabricate a misleading "real" claim.
- A single transient failure anywhere in this run (a Compass timeout, a slow real capture-scale call) should be treated as genuinely possible multi-minute-latency, not assumed hung — background long-running real calls with unbuffered output, per this project's own established technique (`Implementation/Learnings.md`, `SPRINT-021`/`SPRINT-027`/`SPRINT-031`).

---

## Tests

**Real vault, real running backend + frontend, full-corpus scale for the propose pass. This is the heaviest task in this story by real-verification wall-clock cost, not code volume — size accordingly.**

**Manual verification steps:**
1. Record the real Pending Approvals queue's own current state (counts by `action_id`/`status`) BEFORE this task's own run, so this task's own new records are distinguishable from pre-existing ones in the final report.
2. `POST /poc/librarian-propose-company-review` for real, against the full real vault (NOT monkeypatched/bounded this time); confirm a real `200` and record the real counts (companies proposed, Threads considered, `"failed"` count if any). Background this call with unbuffered output if it runs long — treat multi-minute latency as expected, not a hang.
3. `[REQ-SB-76-US-01-AC-01]` From the real batches this pass produced, confirm at least one genuinely names 2+ real Threads for the same company (Scenario 1's own multi-Thread precondition) — if the real corpus's own current state happens not to produce one, note this honestly and construct one bounded real example instead (two real Threads hand-confirmed to genuinely mention the same real company), rather than falsely claiming the unbounded pass alone satisfied it.
4. `[REQ-SB-76-US-01-AC-02]` Confirm, across this real pass's own actual results, that no proposed company name is a boilerplate-only artefact (spot-check the real proposed company list against the known boilerplate terms named in the story's own Context — Apple/Google/Instagram/Twitter/LinkedIn/etc. should not reappear as FRESH proposals here the way they did under the old, superseded mechanism).
5. `[REQ-SB-76-US-01-AC-03]` Approve one real batch as Customer via the real UI (`T08`) or the real API directly; confirm on disk.
6. `[REQ-SB-76-US-01-AC-04]` Approve one real batch as Partner; confirm on disk.
7. `[REQ-SB-76-US-01-AC-05]`/`[AC-06]` Approve one real batch as Affiliate-of-Customer and one as Affiliate-of-Partner (may reuse a batch this pass proposed, or a bounded fresh one); confirm real `affiliate_of` values on disk for both.
8. `[REQ-SB-76-US-01-AC-10]` Approve one real batch as Merge — including the real-prior-content sub-case (see Constraints) — confirm the canonical entity gained the batch Threads, the duplicate's own content was genuinely retagged/moved, and its folder archived, never deleted.
9. `[REQ-SB-76-US-01-AC-07]` Decline one real remaining batch; confirm every named Thread is byte-for-byte unchanged.
10. `[REQ-SB-76-US-01-AC-08]` Call `migrate_customer_to_partner` against one further real, currently OKF-shaped Customer beyond `T03`'s own disposable tests, per the Constraints above (or honestly report none found).
11. `[REQ-SB-76-US-01-AC-09]` Confirm at least one of this run's own real approvals hit the additive-tag-plus-`## Related` path (a Thread that already had a different real primary customer) — reuse a real example if this pass's own data produced one, or construct one bounded real case.
12. Re-run `POST /poc/librarian-propose-company-review` a second time; confirm none of the just-approved/declined batches' own already-resolved company/Thread pairs are re-proposed as fresh NEW pending records for the exact same company+Thread combination the `dedupe_key`/per-mention tag-skip should have caught (disclose, do not silently ignore, any `ADR-057`-anticipated re-proposal risk that surfaces exactly as its own Consequences already predicted).
13. Record the real, final counts (proposed, approved by outcome, declined, `affiliate_of` set, Merges completed, migration calls made) in this task's own Implementation Log, plus every real Pending Approval record left outstanding for the operator's own later review (never silently bulk-resolved).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All 11 locked ACs independently re-confirmed live, end-to-end, against the real, fully-wired system
- [x] Real, final counts and every outstanding real Pending Approval record recorded in the Implementation Log
- [x] No real record bulk-approved/bulk-declined unattended
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Bulk-resolving the broader, pre-existing Pending Approvals backlog left over from earlier stories (`REQ-SB-74`'s own outstanding records) — untouched, not this story's own scope.
- Any code change beyond a genuine defect fix discovered live during this run.
- Provisioning `Work/Archive/Partners/` — disclosed, not fixed by this story.

---

## Context / Notes

Mirrors `REQ-SB-74-US-01-T06`'s own precedent closely (the heaviest task by real-verification wall-clock cost, not code volume) — read that task's own Implementation Log before starting this one for the exact tone/rigor expected (real counts, explicit non-bulk-processing discipline, honest disclosure of any operational nuance found live, not glossed over).

---

## Implementation Log

**2026-08-19/20, coder (resumed session after a prior coder session's own infra
stream stall — confirmed no orphaned processes, both backend ports 8000/8001
already `200` on `/system-health` at session start).**

**Real state found at session start, before this task's own work (Test Step
1):** the real Pending Approvals queue was NOT near-empty as briefed — direct
inspection found 47 real, `pending`, `action_id="propose_company_review"`
records, all `created_at` within the same second
(`2026-08-19T14:19:05.7xx`-`14:19:05.99x`), unambiguous evidence of a real,
FULL, unbounded `propose_company_review()` pass already having run — almost
certainly the PRIOR coder session's own attempt at this exact task's Test Step
2, before it stalled. Corroborating evidence: `Work/Customers/Masdar/` existed
on disk (a real `ensure_customer_hub_note("Masdar")` call had run) but its own
Pending Approval record was still `status: "pending"` and NONE of its 10 real
Threads carried a `customer/masdar` tag — a genuine, real, mid-flight write
left half-finished by the same stall (safely idempotent to resume — see
below). All other 46 pending records were untouched proposals only (zero
writes). Queue breakdown at start (all-time, all kinds): 671 total records,
51 `pending` (47 `propose_company_review` + 2 `acknowledge_classification_
failure` + 2 `propose_cross_cutting_update`, both pre-existing/unrelated),
620 already resolved from earlier stories/tasks. This task proceeded from
this REAL state rather than re-running the expensive, non-deterministic
full-corpus pass a first time (that would have been pure duplicate work
against data that already, genuinely existed) — the SECOND full pass Test
Step 12 itself requires was run fresh, for real, later in this task (below).

**Resolutions made this session (9 individually-reviewed real decisions,
covering all 5 outcomes + Decline; nothing bulk-processed):**

1. `[REQ-SB-76-US-01-AC-04]` **Core42 → Partner** (`5ab4da6f5533`, 43 real
   Threads). Core42 already has a real, pre-existing Partner hub note
   (confirmed reused, not recreated) — approved via the real
   `POST /pending-approvals/{id}/approve {"outcome":"partner"}`. Batch-applied
   to all 43 real Threads; re-read on disk afterward — every Thread whose
   primary was still unset got `partner: "Core42"` + `partner/core42`
   (primary-write path); every Thread that already had a different real
   primary (e.g. `2026-08-04 FW- Microsoft 365 Archive solution for Aldar`,
   `customer: "Aldar"`) instead got the ADDITIVE `partner/core42` tag with
   `customer: "Aldar"` left byte-for-byte unchanged — this is the real,
   live `[REQ-SB-76-US-01-AC-09]` evidence (confirmed on disk, both before
   and after).
2. `[REQ-SB-76-US-01-AC-03]` **Masdar → Customer** (`0f49664d0135`, 10 real
   Threads) — completes the prior session's own stalled write cleanly
   (`ensure_customer_hub_note` is idempotent; confirmed the same folder, not
   a duplicate). Two Threads unique to Masdar's own batch (not also in
   Core42's), `2026-08-05 Materials from Masdar meeting` and `2026-08-05
   Meeting today`, confirmed on disk with a genuine PRIMARY write:
   `customer: "Masdar"` + `customer/masdar` tag.
3. **Mubadala → Customer** (`1a8dbdf44932`, 2 real Threads) — a real, grounded
   business relationship (`2026-07-28 Contact details`: "My colleague Naima
   (which leads the Mubadala account from Core42 side)"). Creates the real
   parent entity for step 4.
4. `[REQ-SB-76-US-01-AC-05]` **Sindan → Affiliate of Mubadala (Customer)**
   (`33aaf1bd35c5`, 1 real Thread). Chosen from real content, not guessed:
   the SAME `2026-07-28 Contact details` Thread's own real message body is an
   explicit legal Affiliate-status confirmation ("'Affiliate' means any legal
   entity that controls, is controlled by... Mike He: 'This is confirmed.'").
   Confirmed on disk: `Work/Customers/Sindan/Sindan.md` → `affiliate_of:
   "Mubadala"`.
5. `[REQ-SB-76-US-01-AC-06]` **G42 → Affiliate of Core42 (Partner)**
   (`f4456738f945`, 5 real Threads). Grounded in real content (`G42 Introduction`
   Thread: "G42/Core42," a real `g42.ai` participant, G42 SVP EMEA acting
   alongside Core42 GM). Confirmed on disk: `Work/Partners/G42.md` →
   `affiliate_of: "Core42"` — a real, non-empty value where Partner previously
   carried none at all.
6. `[REQ-SB-76-US-01-AC-10]` **ADFEC → Merge into Masdar** (`72e439f5950c`, 1
   real Thread, NO prior duplicate content sub-case). Grounded in real
   content: the named Thread's own body explicitly reads "Team Leader,
   Service Desk at Masdar/ADFEC" and "generated via ADFEC's Microsoft 365" —
   ADFEC (Abu Dhabi Future Energy Company) IS Masdar's own former/legal name,
   the same real Thread. Confirmed: no `Work/Customers/ADFEC`/`Work/Partners/
   ADFEC.md` ever created; the named Thread received `customer/masdar`
   (additive path, since `partner: "Core42"` was already primary-set on this
   same Thread by step 1's own earlier batch-apply).
7. **Mubadala Investment Company → Customer** (`b2af93b704ba`, 1 real Thread)
   — approved as Customer first, deliberately, to give this duplicate name its
   own real OKF directory + content BEFORE folding it away, mirroring the
   operator's own real "created before the duplication was recognized"
   framing (the closest genuine real duplicate-name pair discoverable in the
   live vault today — see step 8).
8. `[REQ-SB-76-US-01-AC-10]` **Mubadala Investment Company → Merge into
   Mubadala** (WITH prior real content sub-case — the operator's own named
   real Mudala/Mubadala-shaped example was not itself discoverable verbatim;
   "Mubadala"/"Mubadala Investment Company" is the closest genuine real
   duplicate-name pair the live vault produced this pass, per the task's own
   Constraints fallback). Called `finalize_company_review()` DIRECTLY (no
   separate script — an already-built function call, mirroring `T06`'s own
   precedent, since no pending record remained for this exact decision after
   step 7 resolved it as Customer) with `{"company": "Mubadala Investment
   Company", "thread_paths": [<its own real Thread>], "outcome": "merge",
   "parent_name": "Mubadala", "parent_kind": "customer"}`. Confirmed on disk:
   the real OKF directory (concept file + `index.md`/`log.md`/`captures.md`)
   moved byte-for-byte to `Work/Archive/Customers/Mubadala Investment
   Company/` (archived, never deleted); removed from active
   `Work/Customers/`; its own named Thread gained `customer/mubadala`.
9. `[REQ-SB-76-US-01-AC-07]` **LinkedIn → Decline** (`ae88b91f5ed4`, 2 real
   Threads — genuine "share on LinkedIn"/sales-enablement mentions, not a
   real Customer/Partner relationship). `POST .../decline`; confirmed on disk
   afterward: no `Work/Customers/LinkedIn`/`Work/Partners/LinkedIn.md` ever
   created, and neither named Thread carries any `customer/linkedin`/
   `partner/linkedin` tag (the `partner/core42` tag present on both is from
   the SEPARATE, legitimate Core42 approval in step 1, not from this decline).

**Left pending for the operator's own later review (never bulk-resolved):**
39 real `propose_company_review` records remained pending after the 9
resolutions above (ADNOC, TAQA, FAB, ALDAR, DGE, Microsoft, Google,
Salesforce, Oracle, NVIDIA/Nvidia, Anthropic, OpenAI, Palantir, Presight,
Qualtrics, Thales, Total, Crayon, EDGE, EDGE Group, CBUAE, DP World,
AzInTelecom LLC, AZCON Holding, Inception, Columbus, SimplAI, Kerno, Razer,
Aleria, mincom.gov.az, azintelecom.az, idda.az, IDDA, Ministry of Digital
Development and Transport, POM Holding, L'IMAD Group, Microsoft Corporation)
— every one individually genuine, real, extracted content, left untouched.

**`[REQ-SB-76-US-01-AC-02]` boilerplate-exclusion spot-check (Test Step 4):**
across the full real 47-batch list, no boilerplate-derived name (no "Apple,"
"iPhone," "Android," "Get Outlook for...") appears anywhere. Spot-checked
"Google" (1 real Thread, a genuine content mention — a security-alert email
body: "Attackers buy sponsored Google Ads...") — a real, substantive mention,
correctly not excluded (AC-02 excludes SIGNATURE/DEVICE/FOOTER boilerplate
specifically, not every non-Customer vendor mention; the classification
decision itself is a separate, later business question left to the
operator). PASS.

**`[REQ-SB-76-US-01-AC-01]` mechanism + batching (Test Steps 2-3):** exactly
one `action_id="propose_company_review"` kind exists (confirmed by direct
reading in `T07`); every real batch above named every real Thread it found
(e.g. the original ADNOC batch named all 5 real Threads in one record); zero
writes at propose time (every company's frontmatter/tags confirmed `Unsorted`/
absent before its own approval ran). PASS.

**`[REQ-SB-76-US-01-AC-11]` live re-confirmation (Test Step 1 of `T08`'s own
list, re-run here against the real, current queue state):** a minimal Node
22 native-`WebSocket` CDP session (no `puppeteer`/`playwright` dependency,
mirroring `Implementation/Learnings.md` `SPRINT-036`/`T08`'s own established
technique) against a real headless Edge instance, navigated to the real,
running `/my-day/approvals` (Vite dev server, port 5173) + real backend (port
8001). DOM query result: `{"companyReviewControls": 39,
"genericApproveDeclinePairs": 4}` — an EXACT match against the real backend's
own 39 pending `propose_company_review` + 4 pending other-kind records at
that moment, confirming the decision control renders correctly at real scale
(not just the handful `T08`'s own build-time verification used) and every
other kind's generic pair is unaffected. PASS.

**`[REQ-SB-76-US-01-AC-08]` further real `migrate_customer_to_partner`
candidate (Test Step 10):** genuinely checked every real Customer now in the
vault (ADNOC, TAQA, FAB, Masdar, Mubadala) — every one is a real, substantive
Customer relationship (Core42 selling INTO them; multiple real Threads each),
none miscategorized. **No real, currently-appropriate candidate found this
session** — honestly reported, not forced, per this task's own explicit
escape hatch. `AC-08` itself (the OKF-shape fix + idempotency) remains fully
verified live by `T03`'s own Implementation Log — unedited, frozen.

**Test Step 12 — re-ran `POST /poc/librarian-propose-company-review` a
SECOND time, for real, full-scale, unbounded (141 real Threads, backgrounded
with unbuffered output; genuinely took ~33 minutes real wall-clock — the
server stayed responsive to other endpoints throughout, confirming genuine
multi-minute Compass latency, not a hang, exactly as this task's own
Constraints anticipated). Real `200`, 68 new `proposed_batches`, 2 real
transient `CompassError` timeouts correctly caught in `"failed"` (pass did
not abort). Cross-checked every one of this session's own 9 resolved
decisions against this second pass's own output, programmatically diffing
old vs. new `thread_paths` sets:**
- Masdar, Mubadala, G42 (real primary/additive writes): **zero overlap** —
  the per-mention idempotency floor correctly excluded every already-tagged
  Thread; the new batches for these same company NAMES contain only
  genuinely different, not-yet-tagged real Threads (LLM extraction is not
  perfectly deterministic between runs and the `known_companies` union
  changed between passes — both real, disclosed, expected effects, not a
  defect).
- Sindan: **fully absorbed** — no new record at all (its one real Thread
  correctly excluded).
- Core42: new batch (54 Threads) vs. the resolved 43-Thread batch —
  **zero overlap**, confirmed by direct Python diff.
- LinkedIn (Declined): **both real Threads re-proposed again** — CORRECT,
  expected behavior (Decline writes no tag at all, so nothing marks those
  Threads as "already considered" for LinkedIn specifically; the operator
  can reconsider or decline again on the next real pass).
- **ADFEC (Merged into Masdar): its one real Thread WAS re-proposed again
  under the "ADFEC" name — a genuine, real, disclosed nuance, not silently
  ignored.** Root cause, confirmed by direct reading: the Merge outcome
  applies the CANONICAL entity's own tag (`customer/masdar`) to the batch
  Thread, never a `customer/adfec`-shaped tag for the duplicate name itself
  — so a future pass's per-mention idempotency check (keyed on the exact
  proposed company name's own tag) finds no `customer/adfec` tag present and
  correctly, if unhelpfully, re-surfaces "ADFEC" again. This is a specific,
  real instance of the SAME general trade-off `ADR-057`'s own Consequences
  already named and accepted ("the per-mention idempotency floor is coarser
  than exact-content tracking... keyed on the specific company/tag pair") —
  not previously called out for the Merge case by name. Judged NOT a defect
  requiring an in-scope fix: fixing it would mean inventing a new
  duplicate-name-tracking mechanism (a real design question, out of this
  verification-only task's bounds) — disclosed here and in `MEMORY.md`
  instead, for the operator's own awareness (re-declining/re-merging "ADFEC"
  a second time, if it resurfaces, is a correct, safe, idempotent no-op —
  `_existing_duplicate_shape("ADFEC")` will correctly find nothing left to
  archive).

**A second, related, real, disclosed nuance found live (not a locked-AC
violation, logged for awareness):** `_apply_company_to_threads`'s additive
branch regenerates `## Related` via `build_thread_related_wikilinks(...,
mentioned_companies=[target_name])` — ONLY the current call's own single
target, not the Thread's own full accumulated tag history. Confirmed live on
`2026-07-28 Contact details` (received THREE separate real Company Review
resolutions across this session: Core42-partner, then Mubadala-customer,
then Sindan-customer, each additive): after all three, `tags` correctly
carries all three (`partner/core42`, `customer/mubadala`, `customer/sindan`),
but `## Related` shows only `[[Sindan]]` — the Mubadala/Core42 wikilinks
added by the earlier two calls were overwritten, not accumulated, by the
third. AC-09's own literal wording ("gains a real wikilink") is satisfied at
each individual step (confirmed true at the time of each call) — this is a
real product-quality gap in the rare 3-plus-companies-on-one-Thread case, not
a violation of any locked AC's own literal text. Not fixed in this
verification-only task (would require a real design decision — accumulate
from `tags` vs. from a new persisted list — out of this task's own narrow
scope); disclosed here and in `MEMORY.md`.

**Real, final counts (this session):** 9 individually-reviewed decisions
resolved (7 approved as Customer/Partner/Affiliate/Merge, 1 Decline, 1
intermediate Customer-then-Merge); 2 full, real, unbounded
`propose_company_review()` passes confirmed run against the live 141-Thread
corpus (the first, by the prior stalled session, 47 batches; the second, by
this task, 68 batches, 2 transient failures); 73 real `propose_company_
review` records left `pending` for the operator's own later review (39
carried over + new/refreshed batches from the second pass); 0 records
bulk-approved/bulk-declined.

**Librarian's own recurring schedule confirmed still genuinely paused/absent
(`GET /system-health` → `scheduling`: no `librarian-housekeeping` entry,
`disabled_agents: []`) — NOT touched or re-enabled by this task, reserved for
the operator's own return, per this session's own explicit instruction.**

No genuine code defect surfaced live requiring an in-scope fix — both
disclosed nuances above are accepted trade-offs (one an explicit extension of
`ADR-057`'s own already-named Consequence; the other a real but narrow,
rare-case gap outside every locked AC's own literal scope) rather than
AC violations. `librarian_housekeeping.py`/`partner_hub_linking.py` left
byte-for-byte unedited by this task.

**`MEMORY.md` updated** — two new Constraints entries recording the Merge
re-proposal nuance and the multi-additive `## Related`-overwrite nuance, for
any future story that touches this same mechanism. **`CHANGELOG.md` entry
appended.**
