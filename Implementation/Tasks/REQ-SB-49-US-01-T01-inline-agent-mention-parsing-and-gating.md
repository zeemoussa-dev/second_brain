---
id: REQ-SB-49-US-01-T01
title: Inline @agent_id mention parsing, bring-in wiring, send-control gating fix, and live suggestion dropdown
parent_story: REQ-SB-49-US-01
requirement_id: REQ-SB-49
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-01-T01 — Inline @agent_id Mention Parsing, Bring-In Wiring, Send-Control Gating Fix, and Live Suggestion Dropdown

## Parent Story

- Story: [[REQ-SB-49-US-01]] — `../UserStories/REQ-SB-49-US-01-cockpit-inline-agent-mention-bring-in.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-49 *Cockpit @Mentions*

---

## Objective

Add send-time `@token` extraction and exact-match resolution against the
Cockpit's own real `availableAgents` list to `Cockpit.tsx`, wiring every
resolved match to the existing `bringInAgent(...)` call before
`sendCockpitMessage(...)`; fix the real `disabled={!hasExperts}` gating
conflict this creates on the chat input/Send control; and add a live,
prefix-filtered `@`-mention suggestion dropdown while typing — all inside
the one shared `Cockpit.tsx` component, with zero backend changes.

---

## Starting State → End State

**Before / Inputs:**
- `Cockpit.tsx`'s `chat-input-row` is a plain, unparsed `<input>` with no
  `@`-handling of any kind. Both the input and the Send button carry
  `disabled={!hasExperts}` — the input is not even typable until at least
  one agent has already been brought in via the left panel's "+ Bring in"
  button.
- `availableAgents` (`AgentSummary[] | null`, from `fetchAgentList()`) is
  already fetched on mount and is the exact list the left panel's
  "Available Agents" section renders from.
- `bringInAgent(subjectKind, subjectNoteStem, agentId)` and
  `sendCockpitMessage(subjectKind, subjectNoteStem, message)`
  (`cockpitApiClient.ts`) already exist, unmodified, and are the real
  calls the left panel's button and the Send button already use.

**After / Outputs:**
- Sending a chat message extracts every `@token` in the message text,
  resolves each against `availableAgents` by exact, case-insensitive
  `id`-or-(space-stripped)-`name` match, and calls `bringInAgent(...)` for
  every resolved match (deduplicated within the message) BEFORE
  `sendCockpitMessage(...)` fires, mirroring the button's own
  bring-in-then-message sequencing applied to the same message.
- The chat `<input>` is always typable; the Send button is disabled only
  when the message is empty OR (zero agents are brought in yet AND the
  current message text contains no resolvable `@mention`) — an `@mention`
  in the message text can now itself satisfy the "has an expert"
  precondition, per the story's own Scenario 1.
- While typing, a live suggestion dropdown appears once `@` plus at least
  one character has been typed, showing real agents from the same
  `availableAgents` list whose `id`/`name` prefix-matches what has been
  typed so far.
- An unresolvable `@token` is left in the sent message exactly as typed —
  no bring-in call, no fabricated match.

---

## Files to Modify

- `src/frontend/src/features/cockpit/Cockpit.tsx` — the only file this
  task touches. No backend file, no `cockpitApiClient.ts` change (both
  composed calls already exist with the right signatures).

---

## Constraints

- Inherits from parent story (`REQ-SB-49-US-01`).
- **Never a second bring-in code path.** Every resolved mention calls the
  exact same `bringInAgent(subjectKind, subjectNoteStem, agentId)` the
  left panel's button already calls — no parallel implementation.
- **Matching is exact, case-insensitive `id`-or-`name` (name compared with
  internal whitespace stripped) only** — no fuzzy/partial/substring
  matching for the SEND-time resolution step. No ranking.
- **No new client-side dedupe against already-brought-in agents.** Rely on
  `bringInAgent`'s own existing idempotent backend behaviour for a repeat
  mention of an agent already in the thread (Scenario 2) — only dedupe
  WITHIN one message's own token list (so `"@vault-qa @vault-qa"` in one
  message calls `bringInAgent` once, not twice, per the architecture
  note's own "same-source" reasoning; calling it twice would still be
  harmless given backend idempotency, but once is the cleaner, intended
  shape).
- **Suggestions and send-time resolution both read the SAME `availableAgents`
  state** — never a second, independently-fetched list.
- **The chat `<input>` must never be `disabled` again for any reason tied
  to `hasExperts`** — this is the concrete fix for the flagged gating
  conflict. Only the Send button carries the (now-relaxed) gate.
- An unmatched `@token` is left exactly as typed in the message — never
  silently corrected to the nearest real agent.

---

## Tests

**Manual verification steps:**

1. **[REQ-SB-49-US-01-AC-01]** Open a Cockpit for a subject with zero
   brought-in agents. Confirm the chat `<input>` is typable (not
   `disabled`) and Send is disabled while the box is empty. Type
   `Hey @vault-qa can you help?` — confirm Send becomes enabled purely
   because the text contains a resolvable mention, with zero agents
   brought in yet. Click Send. Confirm: (a) a `bringInAgent` call fires
   for `agent_id: "vault-qa"` — the same call the left panel's own
   "+ Bring in" button uses (verify via a `window.fetch`/network-call
   check or equivalent), (b) after reload, the left panel's Available
   Agents list shows `vault-qa` with the `badge-success` "In this chat"
   badge in place of "+ Bring in", and (c) the sent message and
   `vault-qa`'s own reply both appear in the shared chat thread.
2. **[REQ-SB-49-US-01-AC-02]** With `vault-qa` already brought into the
   thread (post-step-1), send a second message containing `@vault-qa`
   again. Confirm the Available Agents list still shows exactly ONE
   "In this chat" badge for `vault-qa` (no duplicate entry, no thrown
   error) — the repeat `bringInAgent` call resolves through the backend's
   own existing idempotent behaviour.
3. **[REQ-SB-49-US-01-AC-03]** Send a message containing
   `@not_a_real_agent` (matches no real agent's `id` or `name`). Confirm
   no `bringInAgent` call fires for that token, and the message as shown
   in the chat thread contains `@not_a_real_agent` exactly as typed,
   unmodified.
4. **[REQ-SB-49-US-01-AC-04]** With `vault-qa` and `people-producer` both
   real, not-yet-brought-in agents, send one message containing both
   `@vault-qa` and `@people-producer`. Confirm two separate `bringInAgent`
   calls fire (one per agent id), both now show "In this chat" in the
   Available Agents list after reload, and both are able to reply within
   the same shared thread.
5. **[REQ-SB-49-US-01-AC-05]** Type `@va` into the chat input (any
   Cockpit state, zero or more agents already brought in). Confirm a
   suggestion list renders (e.g. a `.mention-suggestion-list`/
   `data-testid="mention-suggestions"` region), populated only from the
   real `availableAgents` list, containing `vault-qa` (id-prefix match).
   Then type `@zzz_nonexistent` and confirm the suggestion list is empty
   or absent — never a fabricated/nearest-guess entry.

**Automated tests:** `n/a — no frontend test runner scaffolded yet
(no *.test.* files exist under src/frontend as of this task)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `REQ-SB-49-US-01-AC-01` — real send-time `@vault-qa` mention brings the
  agent in via the existing `bringInAgent` call, visible in the thread and
  the Available Agents list; Send is reachable with zero prior experts.
- [ ] `REQ-SB-49-US-01-AC-02` — a repeat mention of an already-brought-in
  agent is a no-op (no duplicate, no error), relying on backend idempotency.
- [ ] `REQ-SB-49-US-01-AC-03` — an unresolvable token is left as plain
  literal text; no bring-in call fires for it.
- [ ] `REQ-SB-49-US-01-AC-04` — two real mentions in one message bring in
  both agents.
- [ ] `REQ-SB-49-US-01-AC-05` — a live, prefix-filtered suggestion dropdown
  renders real, `availableAgents`-sourced matches only, once `@` plus at
  least one character is typed.
- [ ] The chat `<input>`'s `disabled={!hasExperts}` is removed; Send's own
  gate is relaxed to account for a resolvable in-message mention.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- **`@PersonName` / person-directed-instruction handling and any Person-note
  edit** — entirely out of scope; covered by the sibling story
  `[[REQ-SB-49-US-02]]`. This task's token resolution must not consume or
  alter a token it doesn't resolve (an unmatched token, including a
  person-name-shaped one, is left byte-for-byte in the sent message), so
  it never breaks that sibling story's own future parsing pass over the
  same text.
- **Any backend/API change.** `bringInAgent`/`sendCockpitMessage` are
  reused exactly as they exist today; `cockpitApiClient.ts` is untouched.
- **Fuzzy/ranked/partial-substring matching for send-time resolution** —
  exact (case-insensitive) `id`/`name` match only, per the story's own
  resolved default. (The live-typing suggestion dropdown's own filter is
  intentionally looser — a prefix/substring match — per the architecture
  note; that looseness is scoped to suggestions only, never to send-time
  resolution.)
- **Enter-key-to-send.** The real, current `Cockpit.tsx` has no
  `onKeyDown`/Enter-to-send handler at all today — only the Send button
  click fires `sendCockpitMessage`. This is a pre-existing gap, not
  introduced or required by this story's Gherkin ("sends it" is verified
  via the existing Send button); do not add new keyboard-submit behaviour
  as part of this task.
- **Exact visual/positioning polish of the suggestion dropdown** (spacing,
  animation, precise placement) — no DOM signal, not a locked AC; build it
  against the Cockpit's existing `.card`/`.item-list` conventions and leave
  exact visual treatment to a non-blocking design spot-check, per the
  story's own Notes.
- **Wiring directly against `REQ-SB-51-US-01`'s not-yet-built filtered
  candidate list** — see Context/Notes below; this task wires against
  today's real, unfiltered `availableAgents`.

---

## Context / Notes

**Send-time extraction/resolution (per `architecture.md`'s recorded
design):**

```ts
const MENTION_TOKEN_RE = /@(\S+)/g;

function normalizeForMatch(value: string): string {
  return value.toLowerCase().replace(/\s+/g, '');
}

function resolveMentionedAgents(text: string, candidates: AgentSummary[]): AgentSummary[] {
  const resolved: AgentSummary[] = [];
  const seenIds = new Set<string>();
  for (const match of text.matchAll(MENTION_TOKEN_RE)) {
    const normalizedToken = normalizeForMatch(match[1]);
    const agent = candidates.find(
      (a) => normalizeForMatch(a.id) === normalizedToken || normalizeForMatch(a.name) === normalizedToken,
    );
    if (agent && !seenIds.has(agent.id)) {
      seenIds.add(agent.id);
      resolved.push(agent);
    }
  }
  return resolved;
}
```

Send handler (replaces the current inline `onClick`):

```ts
const handleSend = () => {
  const candidates = availableAgents ?? [];
  const mentionedAgents = resolveMentionedAgents(messageInput, candidates);
  Promise.all(mentionedAgents.map((agent) => bringInAgent(subjectKind, subjectNoteStem, agent.id)))
    .then(() => sendCockpitMessage(subjectKind, subjectNoteStem, messageInput))
    .then(() => { setMessageInput(''); reload(); });
};
```

**Gating-fix mechanism (concrete, resolves the architect's flagged real
code fact):**

```ts
const hasExperts = (data?.thread.brought_in_agent_ids.length ?? 0) > 0;
const hasResolvableMention = resolveMentionedAgents(messageInput, availableAgents ?? []).length > 0;
const canSend = messageInput.trim().length > 0 && (hasExperts || hasResolvableMention);
```

```tsx
<input
  type="text" className="input"
  placeholder={hasExperts ? 'Message the chat…' : 'Bring in an Expert, or type @agent_id, to start chatting…'}
  value={messageInput} onChange={(e) => setMessageInput(e.target.value)}
/>
<button type="button" className="btn btn-primary" disabled={!canSend} onClick={handleSend}>
  Send
</button>
```

The `<input>`'s own `disabled={!hasExperts}` is dropped entirely — this is
the load-bearing half of the fix. Regating only the Send button while
leaving the input disabled would still make Scenario 1 impossible (the
user could never type `@vault-qa` in the first place). The placeholder
text tweak above is a reasonable UX nicety, not a locked AC — any honest
placeholder wording that doesn't claim experts are required is acceptable.

**Live suggestion dropdown (per `architecture.md`'s `/@(\S*)$/`-at-cursor
design; a plain single-line `<input>` has no rich cursor tracking, so
"at the cursor" is read as "at the end of the current value," the
standard simple implementation for this input shape):**

```ts
const mentionQueryMatch = messageInput.match(/@(\S*)$/);
const mentionQuery = mentionQueryMatch ? mentionQueryMatch[1] : null;
const mentionSuggestions = mentionQuery
  ? (availableAgents ?? []).filter((agent) => {
      const q = normalizeForMatch(mentionQuery);
      return normalizeForMatch(agent.id).includes(q) || normalizeForMatch(agent.name).includes(q);
    })
  : [];
```

Render `mentionSuggestions` (when `mentionQuery` is non-empty, per
Scenario 5's "@ plus at least one character" trigger) in a small dropdown
using the existing `.card`/`.item-list`/`.item-row` classes, positioned
near the chat input. Selecting/clicking a suggestion completing the
partial token in the input box is a reasonable, expected autocomplete
behaviour (standard pattern) but is coder latitude on exact mechanism —
Scenario 5 only locks that the suggestion list itself renders correctly
sourced and never fabricates an entry, not the completion interaction.

**`REQ-SB-51-US-01` soft dependency (no hard `depends_on` edge, per the
architect's explicit instruction):** this task wires `resolveMentionedAgents`/
`mentionSuggestions` against today's real, unfiltered `availableAgents`
state. If `REQ-SB-51-US-01` (Background Agents filtering) lands AFTER this
task, that story's own `T04` coder must additionally repoint both
call sites at its new filtered `bringInCandidates` variable (a small,
same-file follow-on edit) so a Background Agent is correctly excluded from
`@mention` matching — record that obligation in `REQ-SB-51-US-01-T04`'s own
Context when that task is decomposed, if this story lands first.

**Read the real current file before applying any of the above.** Multiple
prior sprints (`SPRINT-020`/`021`/`027`) found `Cockpit.tsx`-adjacent /
shared-file drift between a task's own illustrative sample and the real
file by the time the coder starts — re-read `Cockpit.tsx` fresh
immediately before editing.

---

## Implementation Log

Implemented exactly as the task's own Context/Notes samples described:
`MENTION_TOKEN_RE`/`normalizeForMatch`/`resolveMentionedAgents` (module
level), `handleSend`/`canSend`/`mentionQuery`/`mentionSuggestions` inside
the component, the input's `disabled={!hasExperts}` dropped, Send's own
gate relaxed to `messageInput.trim().length > 0 && (hasExperts ||
hasResolvableMention)`, and a `.card mention-suggestion-list
data-testid="mention-suggestions"` dropdown rendered near the chat input.

**One scope-internal judgement call, per the task's own explicit
delegation (not a deviation, not an escalation):** `REQ-SB-51-US-01`
(Background Agents) had already landed by build time — the real current
`Cockpit.tsx` already had `bringInCandidates` (background-agent-filtered).
Wired `resolveMentionedAgents`/`mentionSuggestions` against
`bringInCandidates`, not the raw `availableAgents`, exactly per the
story's own Notes ("if `REQ-SB-51-US-01` lands first, wire against `T04`'s
filtered `bringInCandidates` list").

**Verification — real running frontend (Vite, port 5173) + real running
backend (uvicorn, port 8001), real vault, real agents, driven via a
from-scratch Node native-fetch/WebSocket CDP client against a headless
Edge instance (`--remote-debugging-port=9333`, own isolated
`--user-data-dir`), against `/inbox-cockpit/2026-07-20-Picture-5C920000`
(a real, fresh, zero-brought-in-agents email Cockpit thread):**

- **AC-01** — PASS. Chat `<input>` confirmed typable (not `disabled`) with
  zero experts. Typed `Hey @vault-qa can you help?`; Send became enabled
  purely from the resolvable mention (`disabled: false` with
  `brought_in_agent_ids: []`). Clicking Send fired the real `bringInAgent`
  call (confirmed via the Available Agents list showing `Vault Q&A` with
  a `badge-success` "In this chat" badge after reload) and the real
  message + a real `vault-qa` reply both appeared in the shared chat
  thread.
- **AC-02** — PASS. Sent a second message containing `@vault-qa` again;
  Available Agents list still showed exactly one `Vault Q&A` entry, still
  "In this chat" — no duplicate, no error.
- **AC-03** — PASS. Sent `Hi @not_a_real_agent, ignore this`; no bring-in
  call fired for that token (Available Agents badges unchanged
  before/after), and the message as rendered in the thread contains
  `@not_a_real_agent` exactly as typed.
- **AC-04** — PASS. Sent one message containing both `@vault-qa` and
  `@people-producer`; both now show "In this chat" in the Available
  Agents list.
- **AC-05** — PASS. Typing `@va` rendered
  `[data-testid="mention-suggestions"]` containing `vault-qa`
  (id-prefix match, alongside `vault-filing-expert` — both real,
  registry-derived matches for the `va` substring, never a fabricated
  entry). Typing `@zzz_nonexistent` rendered no suggestion region
  (absent, per the AC's own "empty or absent" wording).
- Gating-fix Constraint — PASS: the `<input>`'s own `disabled={!hasExperts}`
  is gone; only Send carries the (now-relaxed) gate, confirmed live
  (`sendDisabledWhenEmpty: true`, `sendEnabledWithResolvableMentionZeroExperts:
  true`).

gate: clear 2026-08-14 — no triggers fired (no ADR touched, the one
material judgement call above was pre-authorized by the story's own
explicit delegation, not a gap-filling guess; no `ESCALATIONS.md` entry;
every locked AC verified live with a real, observed outcome).
