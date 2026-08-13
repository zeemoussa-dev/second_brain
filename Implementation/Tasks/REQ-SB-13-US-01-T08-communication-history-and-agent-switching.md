---
id: REQ-SB-13-US-01-T08
title: Communication history — unified chronological log, empty state, and full agent-switching refresh
parent_story: REQ-SB-13-US-01
requirement_id: REQ-SB-13
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-13-US-01-T06, REQ-SB-13-US-01-T07]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01-T08 — Communication history + agent switching

## Parent Story

- Story: [[REQ-SB-13-US-01]] — `../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-13 *Embedded Agent Chat & Communication History*

---

## Objective

Add the panel's Communication History section — a chronological `.log-list`
sourced from `T05`'s `GET /agents/{agent_id}/history` (unified chat + run
events, per `ADR-011`), or an `.empty-state` when there are none — and
verify, now that every panel section (settings, actions, chat, history)
exists, that switching agents fully swaps the panel's content with no
leftover from the previously selected agent.

---

## Starting State → End State

**Before / Inputs:**
- `T06` has landed the panel shell (settings + actions, open/close).
- `T07` has landed the chat thread (send/receive, action-triggering).
- `T05` has landed `GET /agents/{agent_id}/history` → the unified
  chronological list.

**After / Outputs:**
- `AgentDetailPanel.tsx` gains a Communication History section: `.log-list`
  of `.log-item`s (kind-agnostic — chat and run events render in the same
  list, in the order the backend returns) when populated, or `.empty-state`
  when empty.
- `features/agents-map/agentsApiClient.ts` gains `fetchAgentHistory`.
- `src/frontend/src/styles/agent-panel.css` gains the `.log-*` selector
  group.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — add:
  ```ts
  export interface AgentHistoryEntry {
    kind: 'chat_user' | 'chat_agent' | 'run_event';
    text: string;
    timestamp: string;
  }

  export function fetchAgentHistory(agentId: string): Promise<AgentHistoryEntry[]> {
    return apiFetch<AgentHistoryEntry[]>(`/agents/${agentId}/history`);
  }
  ```

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — add history
  state, re-fetched on every agent switch and after every chat send (so a
  just-sent message/triggered action shows up without a manual reload):
  ```tsx
  const [history, setHistory] = useState<AgentHistoryEntry[] | null>(null);

  useEffect(() => {
    setAgent(null);
    setMessages([]);
    setDraft('');
    setHistory(null); // clear the previous agent's history on switch
    fetchAgent(agentId).then(setAgent);
    fetchAgentHistory(agentId).then(setHistory);
  }, [agentId]);

  // inside handleSend, after appending the agent's reply to `messages`:
  fetchAgentHistory(agentId).then(setHistory);
  ```
  Render, inside `side-panel-agent`, after the Chat section:
  ```tsx
  <div className="side-panel-section">
    <h3>Communication history</h3>
    {history && history.length > 0 ? (
      <div className="log-list">
        {history.map((entry, index) => (
          <div className="log-item" key={index}>
            <span>{entry.text}</span>
            <span className="log-item-meta">{entry.timestamp}</span>
          </div>
        ))}
      </div>
    ) : (
      history && (
        <div className="empty-state">
          <p className="text-muted">Nothing recorded yet.</p>
        </div>
      )
    )}
  </div>
  ```
  (History entries render in the order the backend returns them — `T05`'s
  `load_agent_history` already returns append order, which is chronological
  order since every writer appends at the moment its event happens; this
  component does not re-sort. `kind` is not rendered as a separate visual
  distinction — Scenario 3b's "not as two separate lists" is satisfied by
  rendering every entry through the same `.log-item` markup regardless of
  `kind`, not by a kind-conditional style.)

- `src/frontend/src/styles/agent-panel.css` — add: `.log-list`/`.log-item`/
  `.log-item-meta`, ported verbatim from `html-prototype/styles.css`.

---

## Constraints

- Inherits from parent story: history is rendered as **one** list, not split
  by `kind` into separate "chat" vs. "run events" sections — the unified-
  timeline shape `ADR-011`/the parent story's own Constraints resolved.
- History re-fetches on agent switch and after every chat send — do not
  require a manual page reload to see a just-triggered action reflected.
- Must not modify `T06`'s Settings/Actions rendering or `T07`'s chat-send
  logic beyond adding the post-send history re-fetch call.
- No new dependency.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `uvicorn app.main:app --reload --port 8001`; browser preview
tool):

1. **[REQ-SB-13-US-01-AC-03]** Open the Email Capture agent's panel (its
   real history already has entries from prior dev-server starts/`T05`/`T07`
   verification, per `MEMORY.md`'s standing every-start-fires-a-capture-run
   constraint). Confirm the Communication History section renders a
   `.log-list` with one `.log-item` per entry, in chronological order
   (earliest timestamp first if the backend returns oldest-first, or confirm
   whichever order `T05`'s `load_agent_history` actually returns is a
   genuinely chronological — not shuffled — order; append order is
   chronological by construction, per `T01`'s own design).
2. **[REQ-SB-13-US-01-AC-04]** Still viewing Email Capture's history (which
   now has both `chat_user`/`chat_agent` entries from `T07`'s verification
   and `run_event` entries from repeated app-start capture runs), confirm
   both kinds of entries appear together in the same `.log-list`, interleaved
   by their real order — not as two separate lists/sections.
3. **[REQ-SB-13-US-01-AC-05]** Close the panel and open the Meeting Capture
   agent's panel instead (its backing pipeline, REQ-SB-08, has never run —
   its real history is empty). Confirm the Communication History section
   renders `.empty-state` with a message explaining nothing has been
   recorded yet.
4. **[REQ-SB-13-US-01-AC-07]** With Email Capture's panel open (showing its
   real settings, actions, a chat message or two from `T07`'s verification,
   and its non-empty history), click a different agent on the Agents Map
   (e.g. Meeting Capture) without closing the panel first. Confirm the panel
   updates in place to Meeting Capture's own settings/actions
   (`T06`)/chat thread (now empty, `T07`'s reset)/history (now the
   `.empty-state` from step 3) — and confirm none of Email Capture's prior
   chat messages or settings values remain visible anywhere in the panel.
5. Non-AC smoke check: confirm no console errors/warnings across steps 1-4.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Populated history renders one `.log-item` per entry in chronological
      order
- [ ] Chat and run-event entries render together in the same `.log-list`,
      not as two separate lists
- [ ] Empty history renders `.empty-state` with a "nothing recorded yet"
      message
- [ ] Switching the selected agent while the panel is open fully replaces
      every section's content (settings, actions, chat, history) with no
      leftover from the previously selected agent
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to how history entries are written (`T01`/`T04`/`T05` own
  that) — this task only reads and renders.
- Wiring the Available Actions buttons (direct-trigger path) — remains Out
  of Scope, unchanged from `T06`/`T07`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-011` created at
`/plan-tasks` step 1) — the human reviews `ADR-011` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story. This is the last task in the story's own
build order — once it lands, every locked AC (`AC-01` through `AC-08`) has
a tagged verification step across `T06`-`T08`.

---

## Implementation Log

**2026-08-11, coder pass.** Added `AgentHistoryEntry`/`fetchAgentHistory`
to `agentsApiClient.ts`, history state (fetched on agent switch and after
every chat send) + Communication History section to
`AgentDetailPanel.tsx`, `.log-*` selectors to `agent-panel.css` — verbatim
per this task's own code blocks.

Live verification (headless Chrome via CDP, same live backend as
T06/T07 — port 8003), continuing directly from T07's own chat session
(same open Email Capture panel, real history already populated by T05's
and T07's own live checks):

- **[REQ-SB-13-US-01-AC-03]** Email Capture's Communication History
  section rendered a `.log-list` with one `.log-item` per real entry,
  timestamps strictly increasing (append order = chronological order, by
  `T01`'s own design — confirmed, not just assumed, by reading the actual
  returned timestamps). **PASS.** Screenshot:
  `panel_scrolled_history_visible.png`.
- **[REQ-SB-13-US-01-AC-04]** The same `.log-list` interleaves
  `chat_user`/`chat_agent` entries (e.g. "hi there", "please run capture
  now") together with `run_event` entries (e.g. "Capture run completed —
  0 email(s) filed.", "Done — 0 email(s) filed.") in one list, in their
  real chronological order — not split into separate chat/run-event
  sections. **PASS.**
- **[REQ-SB-13-US-01-AC-05]** Without closing the panel, clicked
  `[data-agent-id=meeting-capture]` (kept deliberately untouched by every
  other task's live checks this pass — see T05's Log for why). The
  Communication History section rendered `.empty-state` with "Nothing
  recorded yet." **PASS.** Screenshot:
  `ac05_ac07_meeting_capture_switch.png`.
- **[REQ-SB-13-US-01-AC-07]** Same click as above, checked in the same
  pass: the panel updated in place to `"Meeting Capture" "worker"`, its
  own real settings (`Schedule`/`Vault target`/`Classification`/
  `Duplicate handling` — Meeting Capture's own 4 keys, not Email
  Capture's), an empty chat thread (0 `.chat-message` elements — T07's
  `setMessages([])` reset fired on the `agentId` change), and the empty
  history state above — no leftover Email Capture content anywhere in the
  panel. **PASS.**
- Non-AC smoke check: no console errors/warnings across the full sequence
  (open → chat ×2 → real trigger → history render → switch).

Note: this task's own `## Tests` anticipated needing a substitute agent
if `T08` had not yet landed when `T07`'s AC-08 check ran; in practice all
three frontend tasks (`T06`-`T08`) were built and verified in one
continuous coder pass, so `T07`'s AC-08 check and this task's AC-03/AC-04
checks both read from the same real, already-populated history — no
substitution was needed.

- [x] Populated history renders one `.log-item` per entry, chronological order — **AC-03 PASS**
- [x] Chat and run-event entries render together in one `.log-list` — **AC-04 PASS**
- [x] Empty history renders `.empty-state` with "nothing recorded yet" — **AC-05 PASS**
- [x] Switching agents fully replaces every section's content, no leftover — **AC-07 PASS**
- [x] `MEMORY.md` updated — yes, see Decisions/Patterns/Constraints entries for SPRINT-010
- [x] `CHANGELOG.md` entry appended — yes

This is the last task in the story's own build order — every locked AC
(`AC-01` through `AC-08`) now has a verified, PASS-recorded live outcome
across `T06`-`T08`.
