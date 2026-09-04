---
id: REQ-SB-49-US-02-T06
title: Cockpit chat thread — pending person-note-edit proposal confirm/discard UI
parent_story: REQ-SB-49-US-02
requirement_id: REQ-SB-49
type: frontend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-038 created) — carried from the parent story; the human reviews ADR-038 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-49-US-02-T01, REQ-SB-49-US-02-T05]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-02-T06 — Cockpit Pending Person-Note-Edit Proposal Confirm/Discard UI

## Parent Story

- Story: [[REQ-SB-49-US-02]] — `../UserStories/REQ-SB-49-US-02-cockpit-person-mention-proposed-note-edit.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-49 *Cockpit @Mentions*

---

## Objective

Render `data.person_note_proposals` (`T01`'s new `GET /cockpit/{subject_kind}/{stem}` response key) as a `.chat-proposal`-shaped "Awaiting your decision" region in `Cockpit.tsx`'s chat thread — the same structural pattern the thread already uses for `pendingResearch` — with a Confirm and a Discard control wired to `T01`'s two new endpoints.

---

## Starting State → End State

**Before / Inputs:**
- `Cockpit.tsx`'s existing `pendingResearch` state renders a `.chat-proposal` card with `badge-warning`/"Awaiting your decision", a `<p>` summary, and two buttons (`btn-primary` Save, `btn-danger` Discard) — the real, current, approved-prototype-derived pattern (verbatim, already read for this pass).
- `cockpitApiClient.ts`'s `CockpitData` interface has `{subject, people, thread, research_results}` — no `person_note_proposals` field yet.

**After / Outputs:**
- `CockpitData` gains a `person_note_proposals: CockpitPersonNoteProposal[]` field.
- `cockpitApiClient.ts` gains `confirmPersonNoteProposal`/`discardPersonNoteProposal` functions calling `T01`'s two new endpoints.
- `Cockpit.tsx` renders one `.chat-proposal` region per pending proposal (from `data.person_note_proposals`, server-derived — NOT client-only local state, unlike `pendingResearch`, since this proposal kind is created server-side and must survive a page reload), each naming the person/instruction, with Confirm/Discard buttons that call the two new API functions then `reload()`.

---

## Files to Modify

- `src/frontend/src/features/cockpit/cockpitApiClient.ts`:
  - Add to `CockpitData`'s interface:
    ```ts
    export interface CockpitPersonNoteProposal {
      id: string;
      note_path: string;
      person_name: string;
      instruction: string;
      status: 'pending' | 'confirmed' | 'discarded';
      timestamp: string;
    }

    export interface CockpitData {
      subject: Record<string, unknown>;
      people: CockpitPersonChip[];
      thread: CockpitThread;
      research_results: CockpitResearchResult[];
      person_note_proposals: CockpitPersonNoteProposal[];
    }
    ```
  - Add two new functions, placed after `saveCockpitResearch`:
    ```ts
    export function confirmPersonNoteProposal(
      subjectKind: string, stem: string, proposalId: string,
    ): Promise<CockpitPersonNoteProposal> {
      return apiFetch<CockpitPersonNoteProposal>(
        `/cockpit/${subjectKind}/${stem}/person-note-proposals/${proposalId}/confirm`,
        { method: 'POST' },
      );
    }

    export function discardPersonNoteProposal(
      subjectKind: string, stem: string, proposalId: string,
    ): Promise<CockpitPersonNoteProposal> {
      return apiFetch<CockpitPersonNoteProposal>(
        `/cockpit/${subjectKind}/${stem}/person-note-proposals/${proposalId}/discard`,
        { method: 'POST' },
      );
    }
    ```
- `src/frontend/src/features/cockpit/Cockpit.tsx`:
  - Add import: merge `confirmPersonNoteProposal, discardPersonNoteProposal` into the existing `import { fetchCockpit, bringInAgent, sendCockpitMessage, triggerCockpitResearch, saveCockpitResearch, type CockpitData } from './cockpitApiClient';` line.
  - Render, immediately after the existing `{pendingResearch && (...)}` block, one region per pending proposal:
    ```tsx
    {data?.person_note_proposals.map((proposal) => (
      <div className="chat-proposal" key={proposal.id}>
        <span className="badge badge-warning">Awaiting your decision</span>
        <p>Propose an update to <strong>{proposal.person_name}</strong>'s note: {proposal.instruction}</p>
        <div className="chat-proposal-actions">
          <button type="button" className="btn btn-primary" onClick={() =>
            confirmPersonNoteProposal(subjectKind, subjectNoteStem, proposal.id).then(reload)
          }>Confirm</button>
          <button type="button" className="btn btn-danger" onClick={() =>
            discardPersonNoteProposal(subjectKind, subjectNoteStem, proposal.id).then(reload)
          }>Discard</button>
        </div>
      </div>
    ))}
    ```
    (No new component-level state is introduced for this — `data.person_note_proposals` is already re-fetched by the existing `reload()`/`fetchCockpit` call, mirroring how `data.research_results`/`data.thread` are already rendered directly from `data`, unlike `pendingResearch`'s own client-only local-state shape, which does not apply here since this proposal kind is server-created.)

---

## Constraints

- Inherits from parent story.
- Reuses the EXACT existing `.chat-proposal`/`badge-warning`/`chat-proposal-actions`/`btn-primary`/`btn-danger` classes — no new CSS, no new visual pattern invented for this proposal kind (per the story's own Notes: "the existing `.chat-proposal` component already establishes the... visual language this new proposal kind can directly reuse").
- Confirm/Discard call `T01`'s two new endpoints directly — never a client-side-only state change (unlike `pendingResearch`'s own Discard, which is purely local since a research result is never server-persisted until Save; THIS proposal kind is already server-persisted the moment it exists, so both Confirm and Discard must be real backend calls).
- Render `data.person_note_proposals` directly from the fetched `CockpitData` (server-derived, survives reload) — do not introduce a parallel client-only proposal list.
- Do not alter the existing `pendingResearch`/research-proposal rendering block, the chat message list, the Available Agents panel, or the people-chips panel — this task's scope is additive (one new rendered region) only.

---

## Tests

<!-- AC-06 is a DOM-structure assertion (region + two interactive
controls), never pixel/visual polish, per this project's own structural-AC
mandate for screen-changing stories. -->

**Manual verification steps:**

1. **[REQ-SB-49-US-02-AC-06]** Using `T05`'s own live technique (a real Manual/Autonomous `run_agent_conversation` call through the real Cockpit thread — send a real message via the actual running frontend's chat input, e.g. `@people-producer Ahmed Moussa is leaving for Core42, update his note`, against a Cockpit with `people-producer` already brought in), confirm a `.chat-proposal` region renders in the chat thread once the page reloads/re-fetches, showing the person's name and the instruction text, with two distinct buttons present (Confirm / Discard) — inspect via CDP `Runtime.evaluate` for a `.chat-proposal` element containing both a `btn-primary` and a `btn-danger` button, sourced from `data.person_note_proposals`.
2. **[REQ-SB-49-US-02-AC-06]** Click Confirm. Confirm a real `POST .../person-note-proposals/{id}/confirm` network call fires (network-call check), the page reloads, and the `.chat-proposal` region for that proposal no longer renders (it is no longer `"pending"`). Confirm (backend-layer read, or via the note's own vault-browse page) the real Person note now reflects the proposed instruction.
3. **[REQ-SB-49-US-02-AC-06]** Repeat step 1 to produce a fresh pending proposal, then click Discard. Confirm a real `POST .../person-note-proposals/{id}/discard` network call fires, the region no longer renders after reload, and the real Person note is confirmed unchanged (no new line added).
4. Regression check: confirm the existing `pendingResearch` "Awaiting your decision" quick-research proposal card (unrelated to this task) still renders and behaves exactly as before — this task's own new region is additive, never a replacement of the existing one.

**Automated tests:** `n/a — no frontend test runner scaffolded yet (no *.test.* files exist under src/frontend as of this task)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-06** (Scenario 6, structural) — a `.chat-proposal`-shaped region renders per pending person-note proposal, naming the person/instruction, with a Confirm and a Discard control; Confirm writes the real edit and clears the region; Discard leaves the note unchanged and clears the region
- [ ] `CockpitData`/`cockpitApiClient.ts` extended with `person_note_proposals`/`confirmPersonNoteProposal`/`discardPersonNoteProposal`
- [ ] No new CSS class introduced — reuses `.chat-proposal` verbatim
- [ ] Existing `pendingResearch` rendering/behaviour unaffected
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to how a proposal is CREATED (that is `T02`'s/`T05`'s backend-only scope) — this task only renders/resolves an already-existing pending proposal.
- The Supervised-mode Pending-Approval flow (`my-day-approvals.html`, `AC-02`) — reused unmodified, no Cockpit-side UI change needed for it (per the story's own Notes).
- Exact visual/positioning polish (spacing, animation) — no DOM signal, not a locked AC; reusing `.chat-proposal` verbatim already satisfies the structural requirement.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-038` created at `/plan-tasks` step 1, carried) — the human reviews `ADR-038` and the task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Read the REAL current `Cockpit.tsx`/`cockpitApiClient.ts` first** (both already read in full for this decomposer pass; re-confirm at build time per this project's own repeated Learnings finding on shared-file drift, especially given `REQ-SB-49-US-01`'s own sibling task may also be landing changes to `Cockpit.tsx`'s chat-input area around the same time — reconcile against whatever the real file contains, this task's own region is additive and should not conflict with that sibling task's own input-row-only changes).

---

## Implementation Log

Built exactly as specced: `CockpitPersonNoteProposal` interface +
`person_note_proposals` field on `CockpitData`; `confirmPersonNoteProposal`/
`discardPersonNoteProposal` API functions; one `.chat-proposal` region per
`data.person_note_proposals` entry, rendered immediately after the
existing `pendingResearch` block, reusing `badge-warning`/
`chat-proposal-actions`/`btn-primary`/`btn-danger` verbatim — no new CSS
class. Read the REAL current `Cockpit.tsx` immediately before editing
(after `REQ-SB-49-US-01-T01`'s own chat-input-row changes had already
landed in the same session) — this task's own region is additive, below
the input row's own JSX, no conflict.

**Verification — real running frontend (port 5173) + real running
backend (port 8001), real vault, real `people-producer` agent (Manual
mode), driven via the same CDP client, against a second, independent
Cockpit thread (`/inbox-cockpit/2026-07-29--F0FA0000`):**
- **AC-06** — PASS, full round trip through the ACTUAL running Cockpit
  chat input (not a direct backend call): sent
  `@people-producer Mahmoud Moussa is leaving the company and going to
  Core42, please update his note` via the real chat input/Send button.
  A `.chat-proposal` region rendered, containing "Awaiting your decision",
  naming the person and the instruction, with exactly two buttons present
  (`btn btn-primary` "Confirm", `btn btn-danger` "Discard") — confirmed
  via `Runtime.evaluate` DOM inspection.
  - **Confirm path:** clicking Confirm fired the real `POST
    .../person-note-proposals/{id}/confirm` call; the region cleared after
    reload; the real target Person note (`Work/People/
    <operator-email>.md`) was independently confirmed (direct
    file read) to now contain the real proposed line.
  - **Discard path:** a fresh proposal was produced the same way; clicking
    Discard fired the real `POST .../person-note-proposals/{id}/discard`
    call; the region cleared after reload; the real Person note was
    independently confirmed byte-for-byte unchanged (no line added).
- Regression check — PASS: the pre-existing `pendingResearch`
  "Awaiting your decision" quick-research card is untouched by this
  task's own additive region (same component, same classes, unmodified
  code path).
- Clean-up: both real test edits to `Work/People/<operator-email>.md`
  were reverted (confirm-path write stripped; discard-path never wrote
  anything), confirmed byte-for-byte back to the pre-test body; working
  mode restored to autonomous afterward.

**One real, live-discovered infrastructure issue found and worked around
during this task's own verification, not a code defect:** `uvicorn
--reload`'s `WatchFiles`-triggered restart got stuck mid-reload for
several minutes while the worker process was continuously busy with the
background scheduler's own real Compass calls (never reaching an idle
point to gracefully restart) — reconfirms this project's own documented
`WatchFiles`-can-silently-serve-stale-code precedent (`SPRINT-035`). Fixed
by killing the specific stuck reloader-parent/worker PIDs (verified via
`Get-CimInstance Win32_Process`, never by process name) and starting one
fresh, explicitly-controlled `uvicorn --reload` instance for the rest of
verification.

gate: flagged (carried, trigger-3 — `ADR-038`) 2026-08-14 — no NEW
coder-owned trigger fired (additive-only UI region, exact class reuse, no
new visual pattern; no `ESCALATIONS.md` entry; AC-06 verified live
end-to-end through the real running UI, both Confirm and Discard paths).
