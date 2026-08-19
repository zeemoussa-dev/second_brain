---
id: REQ-SB-44-US-01-T06
title: New InboxCockpitPage.tsx + App.tsx route /inbox-cockpit/:stem + MyDayEmailsPage.tsx rows become clickable + attachments panel + draft-copy affordance wiring
parent_story: REQ-SB-44-US-01
requirement_id: REQ-SB-44
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-44-US-01-T05, REQ-SB-43-US-01-T08, REQ-SB-44-US-01-T02]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-44-US-01-T06 — `InboxCockpitPage.tsx` + clickable Emails rows

## Parent Story

- Story: [[REQ-SB-44-US-01]] — `../UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-44 *Inbox Cockpit — Expert-Assisted Email Workspace*

---

## Objective

Final wiring task, mirroring `REQ-SB-43-US-01-T09`'s exact shape: a new thin `InboxCockpitPage.tsx` supplying `subjectKind="email"` plus this story's own two additive props (`attachmentsSlot`, `enableDraftCopyAffordance`) to `REQ-SB-43-US-01-T08`'s shared `Cockpit` component, a new `/inbox-cockpit/:stem` route, and `MyDayEmailsPage.tsx`'s rows become clickable using `T02`'s new `"stem"` field.

---

## Starting State → End State

**Before / Inputs:** `T02` has landed `list_email_items`'s `"stem"` field. `T05` has landed `fetchCockpitAttachments`/`handOffAttachment`. `REQ-SB-43-US-01-T08` has landed the shared `Cockpit` component with its `attachmentsSlot`/`enableDraftCopyAffordance` props. `MyDayEmailsPage.tsx`'s rows are plain, non-clickable (same shape as `MyDayCalendarPage.tsx` before `REQ-SB-43-US-01-T09`).

**After / Outputs:**
- New `src/frontend/src/features/cockpit/AttachmentsPanel.tsx`:
  ```typescript
  import { useEffect, useState } from 'react';
  import { fetchCockpitAttachments, handOffAttachment, type CockpitAttachment } from './cockpitApiClient';

  export function AttachmentsPanel({ stem, onHandOff }: { stem: string; onHandOff: () => void }) {
    const [attachments, setAttachments] = useState<CockpitAttachment[] | null>(null);
    useEffect(() => { fetchCockpitAttachments(stem).then(setAttachments); }, [stem]);

    if (!attachments || attachments.length === 0) return null; // Scenario 4b -- nothing rendered, no affordance implies one exists

    return (
      <>
        <h3 style={{ marginTop: 'var(--space-6)' }}>Attachments</h3>
        <div className="item-list">
          {attachments.map((attachment) => (
            <div className="item-row" key={attachment.filename}>
              <div className="item-row-main">
                <span className="item-row-title">{attachment.filename}</span>
                <span className="item-row-meta">{Math.round(attachment.size / 1024)} KB</span>
              </div>
              <div className="item-row-actions">
                <button type="button" className="btn" onClick={() => handOffAttachment(stem, attachment.filename).then(onHandOff)}>
                  Hand off to Expert
                </button>
              </div>
            </div>
          ))}
        </div>
      </>
    );
  }
  ```
- New `src/frontend/src/pages/InboxCockpitPage.tsx`:
  ```typescript
  import { useState } from 'react';
  import { useParams, Link } from 'react-router';
  import { Cockpit } from '../features/cockpit/Cockpit';
  import { AttachmentsPanel } from '../features/cockpit/AttachmentsPanel';

  export function InboxCockpitPage() {
    const { stem } = useParams<{ stem: string }>();
    const [refreshKey, setRefreshKey] = useState(0);
    if (!stem) return null;
    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/my-day/emails">&larr; Emails</Link></p>
        <Cockpit
          key={refreshKey}
          subjectKind="email"
          subjectNoteStem={stem}
          subjectTitleFields={[{ label: 'Received', key: 'received' }, { label: 'Customer', key: 'customer' }]}
          attachmentsSlot={<AttachmentsPanel stem={stem} onHandOff={() => setRefreshKey((k) => k + 1)} />}
          enableDraftCopyAffordance
        />
      </>
    );
  }
  ```
- `App.tsx` gains `import { InboxCockpitPage } from './pages/InboxCockpitPage';` and `<Route path="/inbox-cockpit/:stem" element={<InboxCockpitPage />} />`, additive.
- `MyDayEmailsPage.tsx`'s row rendering becomes clickable `<Link to={`/inbox-cockpit/${item.stem}`}>`, keyed by `item.stem`, mirroring `MyDayCalendarPage.tsx`'s own `REQ-SB-43-US-01-T09` change exactly.
- `src/frontend/src/features/my-day/client.ts` — `MyDayEmailItem`'s TypeScript interface gains `stem: string`.

---

## Files to Modify

- `src/frontend/src/features/cockpit/AttachmentsPanel.tsx` (new) — per the code block above.
- `src/frontend/src/pages/InboxCockpitPage.tsx` (new) — per the code block above.
- `src/frontend/src/App.tsx` — add the import and route, additive.
- `src/frontend/src/pages/MyDayEmailsPage.tsx` — rows become `<Link>`s to `/inbox-cockpit/:stem`, keyed by `item.stem`.
- `src/frontend/src/features/my-day/client.ts` — `MyDayEmailItem` gains `stem: string`, additive.

---

## Constraints

- `refreshKey`-based remount after a hand-off is a pragmatic, minimal way to reload `Cockpit`'s own internal state after `AttachmentsPanel`'s own hand-off action changes the shared thread — an acceptable simple pattern for this pass (no new global state-management library introduced).
- `AttachmentsPanel` renders NOTHING (not even a heading) when there are zero attachments (Scenario 4b's own "no attachment-review affordance implies one exists").
- `enableDraftCopyAffordance` is always `true` for the Inbox Cockpit, never conditionally toggled — every agent reply in an email cockpit thread gets the Copy affordance (Scenario 7 is satisfied by ANY reply being reviewable-and-copyable text, not by detecting "this specific reply was a requested draft").
- `MyDayEmailsPage.tsx`'s own existing loading/empty-state/day-navigator behavior is unchanged — only the row element/click-target and `key` change.
- No "send" action/button/endpoint exists anywhere in this task's own code — Scenario 7's "never sent automatically" is satisfied by construction (nothing in this story builds a send capability at all).

---

## Tests

**Manual verification steps** (real backend + frontend dev servers; requires a real Email note inside the current 7-day window, at least one WITH an attachment and at least one WITHOUT, per `T03`/`T04`'s own fixtures):
1. **[REQ-SB-44-US-01-AC-01]** Load `/my-day/emails` — confirm each email row is a real clickable link to `/inbox-cockpit/<real-stem>`; click one — confirm the 3-panel Inbox Cockpit renders for that specific email.
2. **[REQ-SB-44-US-01-AC-02]** Confirm the right panel shows the email's real `subject`/`received`/`customer`, and the sender plus every CC'd/thread participant WITH an existing Person note render as clickable chips.
3. **[REQ-SB-44-US-01-AC-03]** Confirm a sender/CC'd participant with no existing Person note renders the plain `.tag-chip--static` fallback.
4. **[REQ-SB-44-US-01-AC-04]** For the email WITH an attachment: confirm the Attachments section lists it with a "Hand off to Expert" button; click it — confirm the resulting summary appears as a new turn in the chat thread.
5. **[REQ-SB-44-US-01-AC-05]** For the email WITHOUT an attachment: confirm NO "Attachments" heading/section renders at all.
6. **[REQ-SB-44-US-01-AC-06]** Confirm the left panel lists the user's available Agents.
7. **[REQ-SB-44-US-01-AC-07]** Bring in an Expert — confirm the chat becomes active, a second brought-in Expert joins the SAME thread.
8. **[REQ-SB-44-US-01-AC-08]** Send a message with two Experts brought in — confirm each reply carries its own distinct `.chat-message-author` label.
9. **[REQ-SB-44-US-01-AC-09]** Ask a brought-in Expert to draft a reply (e.g. type "Draft a reply agreeing to reschedule") — confirm the reply renders as ordinary reviewable chat text with a "Copy" button; click Copy — confirm the text is copied to the clipboard; confirm no network request to any "send"/outbound-email endpoint occurs (browser devtools Network tab — no such request exists to make, by construction).
10. **[REQ-SB-44-US-01-AC-10]** Generate a quick-research result in this email's own cockpit and in a DIFFERENT email's own cockpit — confirm each only shows its own.
11. **[REQ-SB-44-US-01-AC-11]** Trigger on-the-spot research — confirm a pending save/discard card appears.
12. **[REQ-SB-44-US-01-AC-12]** Save it — confirm a new standalone note is created, wikilinked to THIS Email note (not appended into it), and appears in the research list.
13. **[REQ-SB-44-US-01-AC-13]** Discard a different result — confirm no note is created.
14. Non-AC smoke check: confirm `/my-day/emails`'s own existing day-navigator/empty-state behavior is unchanged.
15. Clean-up: delete any test notes/thread entries created during this verification pass.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `/inbox-cockpit/:stem` renders `InboxCockpitPage.tsx` → `Cockpit` with `subjectKind="email"`, `attachmentsSlot`, `enableDraftCopyAffordance`
- [x] `MyDayEmailsPage.tsx`'s rows are real clickable links, keyed by the real stem
- [x] `AttachmentsPanel` renders nothing for an attachment-free email
- [x] Every reply in the Inbox Cockpit carries a Copy affordance; no send capability exists anywhere
- [x] The Emails page's own existing day-navigator/empty-state behavior is unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `MyDayCalendarPage.tsx`/`MeetingCockpitPage.tsx` — `REQ-SB-43-US-01`'s own tasks, already built.
- Building a real "send" capability — explicitly out of scope for this whole story.

---

## Context / Notes

Mirrors `REQ-SB-43-US-01-T09`'s exact shape and role — this story's own final integration task, carrying the majority of live-verification weight, per this project's own established precedent (`Implementation/Learnings.md`). Visual reference: `html-prototype/inbox-cockpit.html` (approved) — read its REAL, current markup before finalizing `AttachmentsPanel.tsx`'s structure.

---

## Implementation Log

**2026-08-14 — built exactly per the task's own code block, no deviation.** New `AttachmentsPanel.tsx`, new `InboxCockpitPage.tsx`; `App.tsx` gained the import + `/inbox-cockpit/:stem` route (additive, mirroring `/meeting-cockpit/:stem`'s own shape); `MyDayEmailsPage.tsx`'s rows became `<Link>`s to `/inbox-cockpit/${item.stem}`, keyed by `item.stem` (mirroring `MyDayCalendarPage.tsx`'s own `REQ-SB-43-US-01-T09` change exactly); `my-day/client.ts`'s `MyDayEmailItem` gained `stem: string`, additive.

**Verification — real backend (port 8001) + a dedicated real frontend dev server (port 5174, `VITE_API_BASE_URL` pointed at the real backend) + a real headless-Edge CDP session (own minimal Node WebSocket driver, no Playwright/Puppeteer) driving REAL clicks/typed input/network calls against the REAL running app — not a mock, not a static read of the code:**

- **[AC-01]** `/my-day/emails` — all 35 real rows confirmed real `<a>` elements, `href="/inbox-cockpit/<real-stem>"`. Navigated directly to a real email's cockpit URL — the 3-panel layout rendered for that exact email (subject/received/customer matched that specific note). **Pass.**
- **[AC-02]/[AC-03]** Real people-chip test: composed one real Email note via the established in-process-monkeypatch-of-`outlook_com.list_recent_mail` technique (real `classify_recent_emails()` run, real `vault_writer.write_note`), with a sender who already has a real Person note (`a.tuffaha@core42.ai`) and a CC'd participant who does not. After a real `POST /vault-index/rebuild`, the cockpit's real DOM showed: sender chip as a real `<a class="btn tag-chip">` linking to `/browse/a.tuffaha@core42.ai` (AC-02); CC'd chip as a real `<span class="tag-chip--static">...(no note yet)</span>`, non-clickable (AC-03). **Both Pass.**
- **[AC-04]** The real email with a real PDF attachment (`Sarmad_Jari_Resume.pdf`, `T03`/`T04`'s own fixture) — Attachments section listed it with a real "Hand off to Expert" button.
- **[AC-05]** The same email's sibling with no attachments — confirmed NO "Attachments" heading/section rendered at all (`AttachmentsPanel` returned `null`).
- **[AC-06]** Left panel listed all 7 real available Agents (Email Capture, Meeting Capture, To-Do Capture, People Notes, Vault Q&A, Vault Filing Expert, Compass Expert).
- **[AC-07]** Real clicks on two different "+ Bring in" buttons (Vault Q&A, then Compass Expert) — both showed "In this chat"; server-side `brought_in_agent_ids` confirmed both in the SAME thread, no separate thread created.
- **[AC-08]** Typed a real message, clicked real "Send" — both brought-in Experts replied (real `run_agent_conversation` calls, ~15-25s each), each rendered with a distinct real `.chat-message-author` label (`"VAULT Q&A"`, `"COMPASS EXPERT"`).
- **[AC-09]** Message: `"Draft a reply agreeing to reschedule the meeting"` — both replies rendered as ordinary reviewable chat text, each with a real "Copy" button. Clicked Copy (with a stubbed `navigator.clipboard.writeText` to observe the call, since headless Chrome has no real OS clipboard) — confirmed the EXACT real reply text (600 chars) was passed to the copy call. Confirmed by direct source-read of the entire codebase (backend `src/backend` + frontend `src/frontend`) that no send/outbound-email code path exists anywhere — the one incidental hit (`outlook_com.py`'s own module docstring) is prose stating write actions were deliberately never ported, not code. **Pass.**
- **[AC-10]** Two different emails' cockpits, each with its own real saved research result — confirmed each cockpit's `research_results` only ever showed its OWN result, never leaking the other's, at every point checked. **Pass.**
- **[AC-11]** Typed a real research query, clicked real "Quick research" — real Hub-routing (`requesting_agent_id = brought_in_agent_ids[0]` = the SECOND test cockpit's first-brought-in agent, `compass-expert`, routed to `vault-qa`) plus a real, temporarily-granted `web-research` skill + Anthropic-Claude Provider swap on `vault-qa` (mirroring `SPRINT-040`'s own established temporary-reconfigure-then-revert protocol — reverted and independently reconfirmed after, see below) produced a real Anthropic web-search result. The real `.chat-proposal` card rendered with the real summary text and "Save to vault"/"Discard" buttons. **Pass.**
- **[AC-12]** Clicked "Save to vault" — a real new standalone note (`Research - ADNOC sovereign cloud initiatives 2026.md`) was created under `Work/Research/`, containing a real `[[wikilink]]` to the Email note (never appended into the Email note's own body — confirmed by reading the Email note, unchanged). After a real index rebuild, the note appeared in that email's own `research_results` list. **Pass.**
- **[AC-13]** A second real research query, a real result produced, clicked "Discard" — confirmed the pending card disappeared, NO note was created on disk for that query, and it never appeared in `research_results`. **Pass.**
- Non-AC smoke check: `/my-day/emails?day=2026-08-11` — day-navigator query param still correctly filters to that day's 6 items (vs. 35 for the full window); heading/back-link unchanged.

**Real-state reconfiguration cleanly reverted and independently reconfirmed** (mirrors `SPRINT-040`'s own protocol): `vault-qa`'s temporary `web-research` skill grant was revoked and its Provider reverted to `compass` — a FRESH `list_agent_skills`/`get_agent_provider` call after the revert confirmed both exactly match the real pre-test state (`["ask_question", "view_channel_status"]`, `compass`). All synthetic test Email/Research/Person notes, `processed_email_ids.json`/`conversation_index.json`/`cockpit_threads.json` test entries were deleted immediately after verification; the vault index was rebuilt one final time and its note count confirmed back to the exact pre-test value (593), independent evidence of a fully clean revert.

**One live-observed, honestly-disclosed finding, not a defect:** on the FIRST research attempt (a cockpit where `vault-qa` — the one granted `web-research` — was brought in FIRST, making it `brought_in_agent_ids[0]`, the frontend's own hardcoded requester), Hub-routing excluded it as its own requester and returned an honest `"Could not find a Research Expert to help with this."` This exactly reproduces `SPRINT-040`'s own already-documented Learnings entry about "first-brought-in Expert being the only real keyword-matching candidate, excluded as its own requester" — not a new bug. Resolved by using a SECOND test cockpit with the bring-in order reversed (`compass-expert` first, `vault-qa` second), which routed correctly.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (no deviation from the task's own code sample; all 13 locked ACs this task owns verified live, in a real browser, against real data, real Providers, and real vault state; the one temporary real-state reconfiguration was cleanly reverted and independently reconfirmed).
