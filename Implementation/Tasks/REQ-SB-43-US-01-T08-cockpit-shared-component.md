---
id: REQ-SB-43-US-01-T08
title: New src/frontend/src/features/cockpit/Cockpit.tsx — shared 3-panel component (chat thread + agents-to-bring-in/research list + subject info/people chips), optional attachments slot and draft-reply affordance
parent_story: REQ-SB-43-US-01
requirement_id: REQ-SB-43
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal reconciliation against the REAL approved prototype (per this task's own Context/Notes directive) — see Implementation Log."
phase: P1
depends_on: [REQ-SB-43-US-01-T07]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-43-US-01-T08 — Shared `Cockpit.tsx` component

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

One shared `Cockpit` component (3-column grid: chat thread + agents-to-bring-in/research list + subject info/people chips) — mirrors `BUGFIX-02-US-01`'s already-established "one component, optional props, two call sites" precedent (`AgentNode.tsx`'s `compact`/`radiusOverride`). Accepts an optional attachments slot and an optional draft-reply affordance (both unused/undefined this pass — wired by `REQ-SB-44-US-01`'s own additive props, never a fork). Structural ACs only — visual polish beyond the ported CSS is a non-blocking, out-of-band spot-check against the approved prototype.

---

## Starting State → End State

**Before / Inputs:** `T07` has landed `cockpitApiClient.ts`. `src/frontend/src/styles/agent-panel.css` already has `.chat-thread`/`.chat-message`/`.chat-message--user`/`.chat-message--agent`/`.chat-input-row`. `src/frontend/src/styles/vault-browser.css` has `.tag-chip`. `src/frontend/src/styles/settings.css` has `.kv-list`/`.kv-row`/`.badge`. `src/frontend/src/styles/my-day.css` has `.item-list`/`.item-row`.

**After / Outputs:**
- New `src/frontend/src/styles/cockpit.css` — the two genuinely new rules `html-prototype/styles.css`'s own "Agent activity pulses"/people-chip section defines (`.tag-chip--static`, `.chat-message-author`), ported verbatim, plus a `.cockpit-grid` 3-column layout rule (`grid-template-columns`, matching the approved prototype's own left/middle/right panel order).
- New `src/frontend/src/features/cockpit/Cockpit.tsx`:
  ```typescript
  import { useEffect, useState } from 'react';
  import { fetchAgentList, type AgentSummary } from '../agents-map/agentsApiClient';
  import {
    fetchCockpit, bringInAgent, sendCockpitMessage, triggerCockpitResearch, saveCockpitResearch,
    type CockpitData,
  } from './cockpitApiClient';

  interface CockpitProps {
    subjectKind: 'meeting' | 'email';
    subjectNoteStem: string;
    subjectTitleFields: { label: string; key: string }[]; // e.g. [{label:'Time',key:'start'}]
    attachmentsSlot?: React.ReactNode;    // REQ-SB-44-US-01 only, undefined here
    enableDraftCopyAffordance?: boolean;  // REQ-SB-44-US-01 only, undefined/false here -- see Context/Notes
  }

  export function Cockpit({
    subjectKind, subjectNoteStem, subjectTitleFields, attachmentsSlot, enableDraftCopyAffordance,
  }: CockpitProps) {
    const [data, setData] = useState<CockpitData | null>(null);
    const [availableAgents, setAvailableAgents] = useState<AgentSummary[] | null>(null);
    const [messageInput, setMessageInput] = useState('');
    const [pendingResearch, setPendingResearch] = useState<{ query: string; summary: string } | null>(null);

    const reload = () => fetchCockpit(subjectKind, subjectNoteStem).then(setData);
    useEffect(() => { reload(); fetchAgentList().then(setAvailableAgents); }, [subjectKind, subjectNoteStem]);

    const hasExperts = (data?.thread.brought_in_agent_ids.length ?? 0) > 0;

    return (
      <div className="cockpit-grid">
        <div className="card">
          <h3>Available Agents</h3>
          <div className="item-list">
            {availableAgents?.map((agent) => (
              <div className="item-row" key={agent.id}>
                <div className="item-row-main"><span className="item-row-title">{agent.name}</span></div>
                <div className="item-row-actions">
                  <button type="button" className="btn" onClick={() => bringInAgent(subjectKind, subjectNoteStem, agent.id).then(reload)}>
                    + Bring in
                  </button>
                </div>
              </div>
            ))}
          </div>
          <h3 style={{ marginTop: 'var(--space-6)' }}>Quick research ({subjectKind === 'meeting' ? 'this meeting' : 'this email'})</h3>
          <div className="item-list">
            {data?.research_results.map((result) => (
              <div className="item-row" key={result.stem}><span className="item-row-title">{result.title}</span></div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3>Chat</h3>
          <div className="chat-thread">
            {data?.thread.messages.map((message, index) => (
              <div className={`chat-message chat-message--${message.speaker === 'user' ? 'user' : 'agent'}`} key={index}>
                {message.speaker === 'agent' && <span className="chat-message-author">{message.agent_name}</span>}
                {message.text}
                {enableDraftCopyAffordance && message.speaker === 'agent' && (
                  <button type="button" className="btn" style={{ marginLeft: 'var(--space-3)' }}
                    onClick={() => navigator.clipboard.writeText(message.text)}>
                    Copy
                  </button>
                )}
              </div>
            ))}
          </div>
          {pendingResearch && (
            <div className="card" data-role="research-pending-card">
              <p>{pendingResearch.summary}</p>
              <button type="button" className="btn btn-primary" onClick={() =>
                saveCockpitResearch(subjectKind, subjectNoteStem, pendingResearch.query, pendingResearch.summary)
                  .then(() => { setPendingResearch(null); reload(); })
              }>Save to vault</button>
              <button type="button" className="btn btn-danger" onClick={() => setPendingResearch(null)}>Discard</button>
            </div>
          )}
          <div className="chat-input-row">
            <input
              type="text" className="input" disabled={!hasExperts}
              placeholder={hasExperts ? 'Message the chat…' : 'Bring in an Expert to start chatting…'}
              value={messageInput} onChange={(e) => setMessageInput(e.target.value)}
            />
            <button type="button" className="btn btn-primary" disabled={!hasExperts}
              onClick={() => sendCockpitMessage(subjectKind, subjectNoteStem, messageInput).then(() => { setMessageInput(''); reload(); })}>
              Send
            </button>
          </div>
          {hasExperts && (
            <button type="button" className="btn" disabled={!messageInput}
              onClick={() => {
                const requestingAgentId = data!.thread.brought_in_agent_ids[0];
                triggerCockpitResearch(subjectKind, subjectNoteStem, requestingAgentId, messageInput).then((result) => {
                  if (result.status === 'found') setPendingResearch({ query: result.query!, summary: result.summary! });
                  setMessageInput('');
                  reload();
                });
              }}>
              Quick research
            </button>
          )}
        </div>

        <div className="card">
          <h3>{String(data?.subject.subject ?? '')}</h3>
          <div className="kv-list">
            {subjectTitleFields.map(({ label, key }) => (
              <div className="kv-row" key={key}><span className="kv-key">{label}</span><span>{String(data?.subject[key] ?? '')}</span></div>
            ))}
          </div>
          <h3 style={{ marginTop: 'var(--space-6)' }}>{subjectKind === 'meeting' ? 'Attendees' : 'People on this email'}</h3>
          <div className="action-list">
            {data?.people.map((person) => person.has_note ? (
              <a className="btn tag-chip" href={`/browse/${person.note_path?.split('/').pop()?.replace('.md', '')}`} key={person.email}>{person.name}</a>
            ) : (
              <span className="tag-chip--static" key={person.email}>{person.name} <span className="text-muted">(no note yet)</span></span>
            ))}
          </div>
          {attachmentsSlot}
        </div>
      </div>
    );
  }
  ```

---

## Files to Modify

- `src/frontend/src/styles/cockpit.css` (new) — `.tag-chip--static`, `.chat-message-author` (ported verbatim from `html-prototype/styles.css`), `.cockpit-grid`.
- `src/frontend/src/features/cockpit/Cockpit.tsx` (new) — per the code block above.
- `src/frontend/src/App.css` (or wherever global stylesheet imports are declared) — import `cockpit.css`, mirroring how `agents-map.css`/`agent-panel.css`/`my-day.css` are already imported.

---

## Constraints

- One component, optional `attachmentsSlot`/`enableDraftCopyAffordance` props — no `subjectKind === 'email' ? ... : ...` fork of the whole render tree; `REQ-SB-44-US-01` supplies its two extra pieces via these two props, additively.
- Reuses EVERY existing CSS class this task's own code block names (`.chat-thread`, `.chat-message`, `.item-list`, `.item-row`, `.tag-chip`, `.kv-list`, `.badge`, `.btn`, `.card`) — only `.tag-chip--static`/`.chat-message-author`/`.cockpit-grid` are genuinely new, ported verbatim from the approved prototype.
- Discard is a pure client-side state clear (`setPendingResearch(null)`) — no backend call (`T04`/`T05`'s own Constraint).
- The chat input row and the "Quick research" trigger are BOTH disabled/hidden until at least one Expert is brought in (`hasExperts`) — mirrors the approved prototype's own empty-state gating exactly (`meeting-cockpit.html`'s `data-state="empty"` panel).
- `subjectTitleFields` is caller-supplied (not hardcoded inside `Cockpit.tsx`) so `MeetingCockpitPage.tsx` (Time/Customer) and `InboxCockpitPage.tsx` (Received/Customer) can each show their own real subject fields without forking this component.
- Person-chip href construction (`/browse/:stem`) reuses `REQ-SB-01-US-01`'s already-`Accepted` `NoteDetailPage.tsx` route — do not invent a second note-detail view.

---

## Tests

<!-- Structural rendering steps -- this project has no jsdom/automated
runner yet (manual mode); verify via a real dev server + browser against
T05's real backend, per this project's own established live-verification
convention. -->

**Manual verification steps** (real backend + frontend dev servers, a temporary throwaway page or direct navigation once `T09` exists — if `T09` has not landed yet, verify by temporarily mounting `<Cockpit subjectKind="meeting" subjectNoteStem="<real-stem>" subjectTitleFields={[{label:'Time',key:'start'}]} />` at any existing route for this task's own isolated verification, then remove the temporary mount):
1. **[REQ-SB-43-US-01-AC-02]** Confirm the right panel renders the subject's real `subject`/`start`/`customer` fields, and every attendee WITH an existing Person note renders as a clickable `<a className="tag-chip">`.
2. **[REQ-SB-43-US-01-AC-03]** Confirm an attendee with NO existing Person note renders `<span className="tag-chip--static">` — not a link, not clickable (no `href`).
3. **[REQ-SB-43-US-01-AC-04]** Confirm the left panel lists every real agent from `fetchAgentList()`, each with a "+ Bring in" button.
4. **[REQ-SB-43-US-01-AC-05]** Click "+ Bring in" on a real agent — confirm the chat input row becomes enabled (`hasExperts` flips true), and a second "+ Bring in" click on a DIFFERENT agent keeps the SAME chat thread rendering (both agents' future replies appear in the one `.chat-thread`, not two).
5. **[REQ-SB-43-US-01-AC-06]** Send a message with two Experts brought in — confirm both replies render with distinct `.chat-message-author` labels naming each real agent.
6. **[REQ-SB-43-US-01-AC-07]** Confirm the "Quick research (this meeting)" list only shows results for the CURRENT `subjectNoteStem` (cross-check against a second, different stem's own cockpit).
7. **[REQ-SB-43-US-01-AC-08]**/**[REQ-SB-43-US-01-AC-09]**/**[REQ-SB-43-US-01-AC-10]** Click "Quick research", confirm a pending card renders with Save/Discard; click Save — confirm the research list gains the new entry; repeat and click Discard — confirm nothing is added.
8. Non-AC smoke check: confirm `attachmentsSlot` renders nothing when not supplied and no Copy affordance renders on any message when `enableDraftCopyAffordance` is not supplied — no layout gap/placeholder implying a feature that isn't there yet.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `Cockpit.tsx` renders the 3-panel layout: left (Agents + research list), middle (chat + save/discard), right (subject info + people chips)
- [ ] A person chip with an existing Person note links to `/browse/:stem`; one with none renders `.tag-chip--static`
- [ ] The chat input/Quick-research trigger are disabled until an Expert is brought in
- [ ] Discard is client-side only, no backend call
- [ ] `attachmentsSlot`/`enableDraftCopyAffordance` props exist, unused this pass (`undefined`/`false`)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The route-level page wrapper and My Day clickable rows — `T09`.
- `REQ-SB-44-US-01`'s own attachments/draft-reply content — supplied via the two optional props, built by that story.

---

## Context / Notes

Visual reference: `html-prototype/meeting-cockpit.html` (approved). Read that file's REAL, current markup before finalizing this component — do not assume the code sample above is byte-for-byte identical to the approved prototype; reconcile class names/structure against it.

---

## Implementation Log

**Reconciled against the REAL, current `html-prototype/meeting-cockpit.html`
(approved), per this task's own Context/Notes directive — several deliberate
deviations from the task's own illustrative code sample, all in the direction of
matching the real approved design more closely, none weakening any locked AC:**
- `.cockpit-layout` (the real approved prototype's class, `260px 1fr 300px`
  grid) used instead of the sample's own `.cockpit-grid` (never defined
  anywhere, including in the sample's own CSS file list).
- The pending-research card uses the real `.chat-proposal`/`.chat-proposal-actions`/
  `badge-warning` classes (the approved prototype's own save/discard pattern,
  already ported into `agent-panel.css`) instead of the sample's generic nested
  `.card`.
- Real `.empty-state` blocks for "no Agents brought in yet" (chat) and "nothing
  saved yet" (research list), matching the prototype's own empty states — the
  sample rendered nothing in either case.
- An already-brought-in agent shows the prototype's own `badge-success "In this
  chat"` instead of a second, redundant "+ Bring in" button.
- Per-Expert `chat-message-author` color is wired to the real
  `--agent-color-{worker|producer|expert}` token via each message's real
  `agent_id` cross-referenced against `fetchAgentList()`'s own `type` field —
  the sample had no color mechanism at all, silently failing Scenario 6's own
  "distinguishable" requirement beyond plain text; this closes that gap using
  already-existing tokens, zero new CSS.
- Person-chip `note_path` splitting handles both `/` and `\` (a real Windows
  path from the backend) — the sample's `split('/')` alone would have produced
  a wrong stem on Windows.
- `main.tsx` (not `App.css`, which is empty/unused — confirmed by direct
  reading) is this project's REAL global-stylesheet import point; used the
  task's own explicit "(or wherever global stylesheet imports are declared)"
  permission.

**Manual verification (real backend `.venv` + real Vite dev server, driven via
the same from-scratch CDP WebSocket client as `T07`; `T09` landed in the same
session so verification used its real `/meeting-cockpit/:stem` route directly,
per the Tests block's own allowed alternative to a throwaway temporary mount;
temporary real state changes reverted, same protocol as prior tasks):**
1. **AC-02:** real Meeting note's real `subject`/`start`/`customer` rendered in the right panel; a real, hand-constructed test Meeting note (same `attendees`-as-JSON-string technique `T03` established, since no REAL pipeline-captured Meeting note in this vault carries the field yet) with a real existing Person note rendered a clickable `<a class="btn tag-chip" href="/browse/a.tuffaha@core42.ai">`. Confirmed live in the browser DOM.
2. **AC-03:** the same test note's fabricated non-existent attendee rendered `<span class="tag-chip--static">Ghost Person (no note yet)</span>` — no `href`, not clickable. Confirmed.
3. **AC-04:** left panel listed all 7 real Agents from `fetchAgentList()`, each with "+ Bring in". Confirmed.
4. **AC-05:** clicked "+ Bring in" on 2 real agents (Vault Q&A, People Notes) via real React Fiber `onClick` dispatch — chat input flipped enabled; both now show "In this chat"; a real message produced replies from BOTH inside the SAME `.chat-thread`. Confirmed.
5. **AC-06:** the two real replies rendered with distinct `.chat-message-author` labels ("Vault Q&A" pink/expert, "People Notes" purple/producer) — confirmed both the text labels and the real, distinct `--author-color` CSS custom property values applied.
6. **AC-07:** a saved research result for one test meeting did NOT appear in a second, different meeting's own cockpit (`research_results: []`, confirmed via direct `GET`).
7. **AC-08/AC-09/AC-10:** real "Quick research" click (after a temporary `vault-qa` grant + Provider swap, same reverted protocol as `T04`/`T05`/`T07`, with a genuinely cross-Section requesting agent — `compass-expert` — brought in FIRST, since the component's own "Quick research" trigger uses `brought_in_agent_ids[0]` as the requesting agent and Hub-routing excludes same-Section/self candidates) produced a real `.chat-proposal` pending card with real Anthropic web-search content; clicking "Save to vault" cleared the card and (after the SAME already-established index-rebuild step `T04`'s/`T05`'s own verification needed — saving a note does not itself trigger a rebuild, matching `ADR-024`'s established index lifecycle, not a defect) the research list gained the real entry; a second trigger + "Discard" click cleared the card client-side with a real `window.fetch` spy confirming ZERO calls to `/research/save`, and no note was written to disk for the discarded query.
8. Non-AC: `attachmentsSlot`/`enableDraftCopyAffordance` unsupplied — zero "Copy" buttons rendered anywhere, confirmed via DOM query.
9. **Visual harness (Layer-1):** a real headless-Edge screenshot of the live Cockpit (`--headless=new --window-size=1600,1200`) was captured and reviewed against `html-prototype/meeting-cockpit.html`'s own approved "in-progress" state — 3-panel layout, chip styles, per-Expert colored attribution labels all visually match.
10. Cleanup: all 3 test Meeting notes + the saved test Research note + `.second-brain/cockpit_threads.json` test entries deleted; `vault-qa`'s temporary grant/Provider reverted; the CDP-launched headless-Edge browser PID tree killed by its own specific root PID (`taskkill /PID <pid> /T /F`, never `/IM`); index rebuilt back to its pre-test count (593).

**Honest, disclosed finding, not a defect in this task's own code:** saving a
research result does not immediately update the left panel's own research list
on the SAME page load without an intervening index rebuild — `research.
list_research_results` (`T04`, already `Done`) reads via `vault_indexing`
backlinks, and no code anywhere calls `rebuild_index()` synchronously on save;
this matches the whole app's own already-established index-freshness precedent
(scheduler-tick/explicit-rebuild, `ADR-024`) rather than a defect unique to the
Cockpit, and AC-09's own wording ("appears in this meeting's own quick-research
results list") does not assert a specific latency. Worth a possible future
candidate follow-up (an explicit rebuild call after a Cockpit save), not
blocking this task.

gate: flagged 2026-08-14 — scope-internal reconciliation against the real
approved prototype (deviations listed above), logged for human spot-check; not
a MUST-FLAG escalation (stayed within this task's own 2 declared files, reused
only already-existing CSS/tokens, no new dependency/shared-interface change).
