---
id: REQ-SB-30-US-01
title: My Day's Emails list filtered to Compass-judged important email
requirement_ids: [REQ-SB-30]
requirement_section: "REQ-SB-30: Email Importance Filtering via Compass Reasoning"
phase: P1
status: Draft
gate: clear
gate_reason: "Resolved 2026-08-12 — operator (via orchestrator) decided the retrofit scope: backfill only the ~22 already-captured emails currently inside the 7-day window (not all 181 real Email notes — no reason to classify importance for emails already outside the window's relevance), and fail-open (show, never silently hide) for any note where the Compass importance call errors — consistent with this project's standing honest-not-silent posture (ADR-011 point 3 / ADR-014 point 7's same pattern one layer over). Ready for /plan-tasks."
sprint: ""
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-30-US-01 — My Day's Emails list filtered to Compass-judged important email

## Story

**As a** Second Brain user
**I want** My Day's Emails list to show only the email Compass judges
important, not every email that was filed
**So that** I can scan My Day for what actually matters instead of wading
through every captured email, including routine/FYI/notification mail I
don't need to act on

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-30: Email Importance Filtering via
  Compass Reasoning* — "My Day's Emails list shows only the important
  captured email, not every email that was filed — determined by a real
  Compass (LLM) judgment call, not a keyword/sender heuristic." Acceptance:
  "My Day's Emails list shows only email Compass judges important, not the
  full captured set; the judgment is a real reasoning call (not a
  keyword/sender allowlist), and the user is not shown a
  misleadingly-empty 'Nothing captured yet' state when unimportant email
  was in fact captured and simply filtered out."
- **PRD breadcrumb (2026-08-12, operator-directed, "Don't show me All
  Emails Show me Important Email in the list use some Compass Reasoning"):**
  four questions explicitly left to `/spec`. Three are resolved below by
  direct code inspection and the breadcrumb's own stated reasoning; one
  (the retrofit question) is genuinely open and flagged for a human
  decision — see `## Notes`.
- **Depends on `REQ-SB-07` (`Done`)** — extends
  `app/business/email_classification.py::classify_recent_emails`'s
  existing per-email Compass call — and **`REQ-SB-22` (`Done`)** — filters
  the already-windowed `my_day.list_email_items()`/`GET /my-day/emails`
  read path, including the day-navigator (`day` query param) `REQ-SB-22`
  added directly outside this pipeline (`app/business/
  my_day.py::_resolve_day_bounds`, `app/api/my_day_router.py::_validate_day`
  — read directly, confirmed live in the real code, not assumed).
- **"Extend the existing call, don't add a second one" — resolved, not
  guessed, by reading the real prompt/response shape
  (`app/data_access/compass_client.py::classify_email`):** today's single
  Compass call already returns one JSON object —
  `{"customer": ..., "kind": ..., "confidence": ...}` — from one prompt
  that classifies the same email along two axes at once (customer, kind).
  Adding a third key (e.g. `"important": true|false`) to that same JSON
  object and prompt is a same-shape, same-call extension — no new HTTP
  round-trip, no new Compass endpoint, no new parsing path beyond one more
  dict key. This matches the PRD breadcrumb's own framing of a second,
  per-view call as "slower, costlier, and inconsistent between loads unless
  cached" against extending the existing capture-time call as "cheap going
  forward" — the real code confirms the cheap option is trivially
  buildable, not just theoretically preferable. **Resolved: extend
  `classify_email`'s existing prompt/response; no second Compass call.**
- **WHEN the judgment happens — resolved: capture time, not on-demand.**
  The PRD breadcrumb itself lays out the tradeoff (capture-time extends an
  already-working call cheaply vs. on-demand re-reasons about the same
  ~22-in-window emails on every My Day page load, which is slower,
  costlier, and would need its own caching layer to avoid inconsistent
  results between loads). Combined with the "extend the existing call"
  resolution directly above (there is no clean way to extend a
  capture-time-only call except by running it at capture time), and this
  project's own established preference (per this story's own brief) for
  extending an already-working Compass call rather than adding a second,
  parallel one, capture-time is the only option that doesn't introduce
  new architecture (a per-view Compass call + a caching layer neither of
  which exists anywhere in this codebase today). **Resolved: importance is
  judged once, at capture time, alongside customer/kind classification,
  and stored in the email note's own frontmatter — never re-reasoned on
  each My Day page view.**
- **Binary vs. tiered — resolved: binary (show/hide), not a score/tier
  UI.** The PRD's own literal Acceptance text asks for filtering ("shows
  only email Compass judges important, not the full captured set") — it
  does not ask for a visible score or tier the UI surfaces; that is framed
  in the breadcrumb only as something the UI "could also" do, not
  something this requirement asks for. No `html-prototype/` screen shows
  an importance score/tier/badge on an Emails row (confirmed by direct
  inspection of `my-day-emails.html`, below) — inventing one now would be
  new UI with no design authority, triggering `net-new-design-needed`
  needlessly for scope the literal acceptance text doesn't request. A
  boolean filter satisfies the literal acceptance text with zero new
  screen surface. **Resolved: `important` is a boolean; a future story
  can add a visible tier/score if ever requested — not built here.**
- **Retrofit for the 181 already-captured emails (~22 currently inside the
  7-day My Day window as of 2026-08-12) — genuinely open, NOT resolved
  here, flagged below.** The PRD breadcrumb explicitly frames this as an
  open choice ("backfill now, or let the window naturally roll past them
  within a week") with real, materially different user-visible outcomes
  for up to 7 days — see `## Notes` for the full analysis and the
  `REVIEW-QUEUE.md` entry.
- **"Important Reads" (`my-day-reads.html`) is a DIFFERENT, still-unspecced
  concept — not this story.** The prototype already has a separate
  "Important Reads" My Day section with its own drill-down
  (`my-day-reads.html`), whose own in-file comment says its criteria are
  "still an open product question" left to a future `/spec` pass. REQ-SB-30
  is specifically about the **Emails** list (`my-day-emails.html`), not
  about "Important Reads." This story does not touch `my-day-reads.html`
  or resolve what makes something an "Important Read" — that remains a
  separate, later question.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Capture-time Compass call also judges importance, in the same call

```gherkin
Given a new email is captured during a scheduled or manual capture run
When Compass classifies the email (as it already does today for customer
    and kind)
Then the same Compass call also returns an importance judgment for that
    email — Compass reasons over the email's actual content (sender
    relationship, urgency, whether it's a direct ask vs. an FYI/
    notification, etc.), not a keyword or sender allowlist
  And no second, separate Compass call is made for importance
  And the email note's frontmatter is written with the resulting
    importance judgment
```

### Scenario 2: My Day's Emails list shows only important email

```gherkin
Given captured emails exist within the My Day 7-day window, some judged
    important by Compass and some not
When the user views the My Day Emails drill-down (the full window, or a
    single day via the day-navigator)
Then only the emails judged important are listed
  And emails judged not important are excluded from the list entirely —
    not shown de-emphasized, not hidden behind a toggle
```

### Scenario 3: My Day dashboard's Emails count reflects only important email

```gherkin
Given some captured emails within the window are judged important and
    others are not
When the user views the My Day dashboard
Then the Emails section's count reflects only the important emails, not
    the full within-window captured count
```

### Scenario 4: No misleading empty state when unimportant email was filtered out

```gherkin
Given captured emails exist within the window, but none of them are judged
    important — every one was filtered out, not because nothing was ever
    captured
When the user views the Emails drill-down
Then the empty state communicates that email was captured but none met
    the importance bar, distinct from the existing "no emails captured
    yet" message that would otherwise misleadingly suggest nothing
    arrived at all
```

### Scenario 5: Genuinely empty state — nothing captured at all

```gherkin
Given no captured emails exist within the window at all (the ordinary
    "nothing captured yet" case, unchanged from REQ-SB-22-US-01's own
    Scenario 6)
When the user views the Emails drill-down
Then the existing "no emails captured yet" empty state is shown, as it is
    today — not the "filtered out" message from Scenario 4
```

### Scenario 6: Compass importance classification fails for one email

```gherkin
Given an email is being captured and Compass's classification call fails
    or returns an unparseable response (the same existing failure mode
    `classify_email` already handles for customer/kind)
When the capture run processes that email
Then the failure is handled the same way the existing customer/kind
    classification failure already is — the email is not silently
    dropped from the capture results, and no importance judgment is
    fabricated for it
```

## Affected Screens

- `html-prototype/my-day-emails.html` — reuses the exact
  `.item-list`/`.item-row` pattern and `.empty-state` component already
  approved; no new region. The populated list is a data-only narrowing
  (fewer rows). The empty state gains a second copy variant (Scenario 4's
  "captured but filtered" message) alongside the existing "nothing
  captured yet" copy (Scenario 5) — both reuse the same
  `.empty-state`/`.empty-state-icon` markup, distinguished only by which
  message renders.
- `html-prototype/my-day.html` — no structural change; the Emails
  `day-section-count` now reflects the filtered (important-only) count
  instead of the full within-window capture count (data-only change, same
  as `REQ-SB-22-US-01`'s own dashboard-count precedent).

## Dependencies

- **Blocked by:** `REQ-SB-07` (`Done`) — extends
  `email_classification.py::classify_recent_emails`'s existing per-email
  Compass call.
- **Blocked by:** `REQ-SB-22` (`Done`) — filters the already-windowed
  `my_day.list_email_items()`/`GET /my-day/emails` read path (including
  the day-navigator `day` param added directly outside this pipeline).
- **Related to:** the still-unspecced "Important Reads" My Day section
  (`my-day-reads.html`) — a distinct, separately-open concept; not built
  or resolved by this story (see Context).
- **External:** none beyond the already-live Compass API integration.

## Constraints

- No second Compass call — importance must be added to the existing
  `classify_email` prompt/response, per the resolution in Context. Adding
  a second, parallel per-email Compass call for importance is out of
  scope for this story.
- Importance is judged once, at capture time, and persisted to the email
  note's frontmatter — My Day's read path (`my_day.py`) must never
  re-invoke Compass at request time; it only reads the already-stored
  field, same as it already does for `customer`.
- Importance is a boolean field (`important: true|false` or equivalent) —
  not a score/tier surfaced in the UI. See Context for why a tier/score UI
  is out of scope here (would trigger `net-new-design-needed` for scope
  the PRD's literal acceptance text doesn't request).
- The exact wording of the Compass prompt's importance-reasoning
  instructions (which specific signals it weighs) is an implementation
  detail left to `/plan-tasks`/the coder, the same way the existing
  customer/kind prompt's exact wording was never dictated by any prior
  story — the observable constraint is that it is real LLM reasoning over
  the email's content, not a keyword/sender allowlist (Scenario 1).
- Do not silently drop an email from capture results when its importance
  classification fails (Scenario 6) — mirror the existing `CompassError`
  handling `classify_recent_emails` already has for the customer/kind
  call.
- **Retrofit of the 181 already-captured emails (~22 currently
  in-window) is explicitly NOT decided by this story** — see `## Notes`.
  Do not silently pick a retrofit behavior at `/plan-tasks`/build time;
  the human decision recorded in `REVIEW-QUEUE.md` must be resolved first.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-30-US-01-T01 | backend | Extend the existing Compass classify-email prompt/response with an importance judgment; write it to email-note frontmatter | `app/data_access/compass_client.py`, `app/business/email_classification.py` | `../Tasks/REQ-SB-30-US-01-T01-compass-importance-judgment.md` |
| REQ-SB-30-US-01-T02 | backend | Filter `list_email_items()`/Emails count to important-only; distinguish "filtered" vs "nothing captured" | `app/business/my_day.py` | `../Tasks/REQ-SB-30-US-01-T02-my-day-importance-filtering.md` |
| REQ-SB-30-US-01-T03 | frontend | Emails drill-down + dashboard consume the filtered response; new "filtered out" empty-state copy | `features/my-day/client.ts`, `pages/MyDayEmailsPage.tsx` | `../Tasks/REQ-SB-30-US-01-T03-emails-drilldown-importance-empty-state.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A visible importance score/tier in the UI** — resolved to a binary
  show/hide filter only (see Context); a future story can add a
  surfaced score/tier if ever requested.
- **A second, parallel Compass call for importance** — resolved to extend
  the existing capture-time call (see Context).
- **On-demand/per-view importance re-reasoning** — resolved to capture-time
  only (see Context).
- **"Important Reads" (`my-day-reads.html`)** — a separate, still-unspecced
  My Day concept; not touched or resolved by this story (see Context).
- **Calendar/To-Do importance filtering** — REQ-SB-30's PRD text is scoped
  to the Emails list only; this story does not extend importance filtering
  to Calendar or To-Do.
- **Retrofitting the 181 already-captured emails** — explicitly left open
  for a human decision, not built here pending that decision (see Notes).
- **A user-facing control to override or disable importance filtering**
  (e.g. a "show all" toggle) — not requested by REQ-SB-30's acceptance
  text; out of scope.

## Notes

**Prototype parity (my-day-emails.html + my-day.html):**

- Emails drill-down populated list — **Specced** (Scenario 2) — reuses the
  approved `.item-list`/`.item-row` pattern unchanged; only the underlying
  query narrows (fewer rows), no new region.
- Emails drill-down empty state, "nothing captured at all" — **Specced**
  (Scenario 5) — reuses the existing `.empty-state` copy/markup as-is.
- Emails drill-down empty state, "captured but filtered out" — **Specced**
  (Scenario 4) — a second copy variant of the same existing
  `.empty-state`/`.empty-state-icon` component (not a new region or
  component); required by the PRD's own literal acceptance text, unlike
  `REQ-SB-22-US-01`'s optional nuance which was deliberately not added.
- Dashboard Emails section count — **Specced** (Scenario 3) — data-only
  change (filtered count instead of within-window total), no new screen
  region, same precedent as `REQ-SB-22-US-01`'s own dashboard-count
  resolution.
- "Important Reads" section/drill-down (`my-day-reads.html`) —
  **Deferred** — a distinct, still-unspecced concept (its own prototype
  comment says so); not this story's scope (see Context/Dependencies).

**Resolution record (2026-08-12, analyst):** three of the PRD breadcrumb's
four "left to /spec" questions are resolved directly in Context, each
grounded in direct code inspection (the real `classify_email`
prompt/response shape, the real `my_day.py`/day-navigator read path) or
the breadcrumb's own stated reasoning/tradeoffs — not guessed among
equally-valid options: (1) extend the existing Compass call, confirmed
buildable by reading the real single-JSON-object response shape; (2)
capture-time judgment, the only option that doesn't require inventing a
new per-view-call-plus-caching-layer architecture that exists nowhere in
this codebase today; (3) binary show/hide, matching the PRD's own literal
acceptance text and avoiding an unrequested `net-new-design-needed`
trigger for a score/tier UI.

**The fourth question — retrofit of the 181 already-captured emails (~22
currently inside the 7-day window as of 2026-08-12) — is genuinely open
and NOT resolved here.** The PRD breadcrumb itself frames this as a real
choice with materially different user-visible consequences, not a detail
with an obvious answer:

- **Option A — backfill now:** run a one-time retrofit (mirroring this
  codebase's existing retrofit precedent — e.g.
  `retrofit_email_sender_links`, `retrofit_customer_hub_links`) that
  classifies importance for the 181 already-captured emails (or at least
  the ~22 currently in-window) before this story's filtering goes live.
  Real Compass cost for 181 calls; the in-window emails behave correctly
  from day one.
- **Option B — let the window roll:** do nothing extra; the ~22
  currently-in-window emails have no `important` field yet. What happens
  to them in the meantime is itself a further, unresolved sub-question —
  whether a missing field is treated as "not important" (excluded,
  potentially making the Emails list look sparser than reality for up to
  a week) or "important" (shown, fail-open, until reclassified) changes
  what the user actually sees during that week, and either choice is a
  real product decision, not a technical default this story can silently
  pick.
- **Update, 2026-08-12 — Resolved.** Decided: **backfill only the ~22
  emails currently inside the 7-day window** (Option A, narrowed — not
  all 181; emails already outside the window's relevance have no reason
  to be classified before this story's own filtering ships), and
  **fail-open** for the missing-field/error case: any note where the
  Compass call errors or the field is genuinely absent is treated as
  important (shown), never silently hidden — matching `ADR-011` point 3/
  `ADR-014` point 7's existing "honest, not silent" posture one layer
  over. This closes both the Option A/B choice and Option B's own
  fail-open/fail-closed sub-question at once, since backfilling the
  in-window set makes the sub-question moot for everything the user will
  actually see this week; fail-open is recorded anyway as the
  general-case behavior for any future gap (a new capture whose Compass
  call fails, e.g.). `/plan-tasks` should size the backfill as a small
  additive task, following the existing retrofit-script precedent named
  above.
- Why this is flagged rather than resolved like the other three: unlike
  (1)-(3) above, there is no PRD text, code precedent, or breadcrumb
  framing that favors one of these options over the other — the
  breadcrumb explicitly presents both as live choices ("backfill now, or
  let the window naturally roll past them"), and Option B's own
  missing-field-handling sub-question has no stated preference either.
  Picking either without a human decision would be exactly the kind of
  guess among multiple equally-valid options the analyst is required to
  flag rather than make.

`gate: flagged` 2026-08-12 — MUST-FLAG trigger 8 fired (multiple
equally-valid ways to resolve the retrofit question for the 181
already-captured emails / ~22 currently-in-window emails; no PRD text,
code precedent, or breadcrumb framing favors one option over the other).
No other trigger fired: REQ-SB-30 is finalized PRD text (no `<!-- Draft
-->` marker on its Acceptance); the three other breadcrumb questions were
resolved by direct code inspection/precedent, not guessed among
equally-valid options; no new UI region is introduced (both empty-state
variants reuse the existing `.empty-state` component, no
`net-new-design-needed`); not oversized (one coherent extension of two
already-`Done` stories' existing read/write paths, 3 tasks); no
contradictory PRD inputs; no `ESCALATIONS.md` entry written — this is a
forward scoping decision the PRD itself explicitly deferred to `/spec`,
not a backward/out-of-scope event. See `REVIEW-QUEUE.md` for the pointer.
Once the human resolves the retrofit question and records it here, reset
`gate:` to `clear` and this story is ready for `/plan-tasks` — the rest of
the story (Scenarios 1-3, 5, 6 and their tasks) does not depend on that
decision and would not need to change; only Scenario 4's precise framing
and, if Option A is chosen, one additional retrofit task would be added.

---

**Architect pass (2026-08-12) — `/plan-tasks` step 1.** Full design recorded
in `Implementation/Architecture/architecture.md` → "My Day dashboard &
drill-downs" → "Amendment — Compass-judged email importance filtering
(REQ-SB-30-US-01)". Summary:

- `app/data_access/compass_client.py::classify_email` — one more IMPORTANT
  paragraph in the existing prompt, one more `"important": <true|false>`
  key in the same JSON response object; return dict gains
  `"important": bool(parsed.get("important", True))` (fail-open even on a
  parseable-but-key-omitting response).
- `app/business/email_classification.py::classify_recent_emails` — written
  frontmatter dict gains `"important": classification["important"]`; the
  existing per-email `CompassError` handling (whole note skipped, not
  partially written) already satisfies Scenario 6 with no new code.
- **Found in code, not assumed:** `important` is this codebase's first
  boolean frontmatter field, and `app/data_access/vault_writer.py`'s
  `_format_frontmatter_value`/`_parse_frontmatter_value` do not round-trip
  Python `bool` correctly today (would serialize as capitalized
  `"True"`/`"False"` strings and read back as truthy strings regardless of
  value, silently defeating the filter). In scope: add an
  `isinstance(value, bool)` branch to each, matching the same
  surgical-primitive-fix pattern already used elsewhere in that module —
  not a new serialization format, not a migration.
- `app/business/my_day.py::list_email_items` — one more condition after the
  existing window check: `frontmatter.get("important", True)` (fail-open —
  absent field or explicit `True` shown, only explicit `False` excluded).
  Response shape unchanged. `summary()`'s `emails` object gains one
  additive field, `captured_count` (window-scoped count *before* the
  importance filter, alongside the existing post-filter `count`) — the
  frontend's Scenario 4 vs. Scenario 5 empty-state distinction is a pure
  comparison of the two, no new endpoint.
- Retrofit — new function in `app/business/email_classification.py`,
  scoped only to `Work/Emails/` notes inside `my_day._compute_window()`/
  `_within_window()` (reused directly, not redefined), idempotent (skips
  notes already carrying `important`), calls `classify_email` per
  in-window note and writes only the returned `important` value (discards
  `customer`/`kind` — backfill, not re-classification), leaves a
  Compass-error note with no `important` field (fail-open, never
  fabricated). Exposed as `POST /poc/retrofit-email-importance` in
  `app/api/email_poc_router.py`, matching the existing retrofit-endpoint
  response shape (`{"notes_checked", "<verb>ed", "results"}`). Frontmatter
  write reuses `vault_writer.py::insert_tags_line`'s existing
  surgical-single-line-insert shape (a new small sibling primitive, or a
  narrow `important`-specific variant — decomposer/coder latitude, not an
  architectural fork).

**No new ADR.** Every piece above is a same-shape extension of already-
`Accepted` structure (one more key on the existing single Compass call;
a bugfix-shaped fix to an existing serialization primitive for its first
boolean field; an additive field + narrower filter on an already-
`Accepted` read path, same precedent as the REQ-SB-22-US-01 amendment; the
existing one-module-per-maintenance-operation retrofit shape). Does not
reopen or contradict ADR-015's "Model integration" note that
`compass_client.py` was untouched *by that pass* — `classify_email`
remains the one fixed-shape function called only by the linear
email-classification pipeline, extended in key-count only, not in kind.

**Architecture scope:** `app/data_access/compass_client.py`,
`app/business/email_classification.py`, `app/data_access/vault_writer.py`
(`_format_frontmatter_value`/`_parse_frontmatter_value` only — do not
touch unrelated primitives), `app/business/my_day.py`,
`app/api/my_day_router.py` (response-shape awareness only — no route
signature change), `app/api/email_poc_router.py` (new retrofit endpoint),
`src/frontend/src/features/my-day/client.ts`,
`src/frontend/src/pages/MyDayEmailsPage.tsx`, `src/frontend/src/pages/
MyDayPage.tsx` (dashboard count consumption only). Bounded by
`architecture.md` → "My Day dashboard & drill-downs" (base section) →
"Amendment — rolling 7-day window date-filtering (REQ-SB-22-US-01)" →
"Amendment — Compass-judged email importance filtering
(REQ-SB-30-US-01)".

`gate: clear` 2026-08-12 (architect) — no ADR created or changed; the one
real gap found (`vault_writer.py`'s bool round-trip) was resolved by
direct code inspection, not guessed among equally-valid options, and is a
primitive-level bugfix, not an architectural fork. No contradiction with
any `Accepted` ADR, the PRD, or a `MEMORY.md` constraint. Handing off to
the decomposer.
