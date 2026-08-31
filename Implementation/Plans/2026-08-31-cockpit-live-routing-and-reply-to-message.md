# Cockpit live-question routing + reply-to-message (2026-08-31)

## Origin

Operator, reporting a real, reproducible symptom: "When an Agent Respond to
something and I say Yes a different Agent Picked the thread." Root-caused live
against the actual code (not guessed): `chat_turn.py::send_user_message` +
`moderator.py::route_question` re-route **every** message from scratch, purely
via deterministic keyword/token overlap between the message text and each
brought-in agent's `name`/`description` (`moderator.py:1-3`, "no LLM call, no
Hermes profile involvement"). There is no "who answered last" concept
anywhere in `chat_store.py`'s thread schema. A low-signal reply like "Yes"
has no domain keywords, so it can't match back to whoever just spoke and
falls through to a coincidental match or the Research Agent fallback
(`chat_turn.py:181`).

This is the exact open question `REQ-SB-82-US-04` already flags as
unresolved ("the routing-decision mechanism... genuinely unresolved by the
PRD's own text, including the tie-break case" — see that story's own
Context/Notes). **This plan resolves that specific sub-question** (live,
per-message routing among already-brought-in Experts) and adds a genuinely
new capability (reply-to-message) the operator asked for while designing the
fix. It does **not** touch `REQ-SB-82-US-04`'s remaining, separately-flagged
scope — the async Research Agent fallback + threaded-reply UI (Scenarios
2–4 of that story) and the disclosed Hermes live-back-channel risk are
untouched, still open, still that story's own problem to solve later.

## Design, as worked out with the operator (a genuine back-and-forth, not a
unilateral choice — options were presented, tradeoffs discussed, decisions
made explicitly)

### 1. Short-reply shortcut (cheap, deterministic, first-checked)

A message that is low-signal by construction (very short, or matches a small
fixed acknowledgment vocabulary — "yes", "ok", "sure", "go ahead", "please
continue", etc.) is **not** worth a model call to route. Detect it and route
directly to whichever agent most recently replied in this thread, no
inference needed. This needs a real "last-answering agent" concept added to
`chat_store.py`'s own thread schema (today: `{"brought_in_agent_ids": [...],
"messages": [...]}`, nothing recording who spoke last).

### 2. LLM-based moderator, always on (operator's explicit choice: "Always run
it," not fallback-only)

Replace `moderator.route_question`'s deterministic keyword-overlap with a
real model call that reasons over: the roster agents' own `name`/
`description`, recent conversation history (who said what, in order), the
new message's own text, and — when present — which specific earlier message
the new one is replying to (see §3). This runs on **every** message, per the
operator's explicit choice over a fallback-only design (accepted: consistent
behavior over minimizing latency/cost on the easy cases the short-reply
shortcut doesn't already catch).

**Model/infrastructure, investigated live, not assumed:**
`COMPASS_BASE_URL`/`COMPASS_API_KEY`/`COMPASS_MODEL` already exist as env
vars and a `Provider` metadata record (`src/backend/.env.example:1-3`,
`app/config.py:10-12`, `app/data_access/providers.py:52-58`) — but **nothing
in `src/backend` actually calls Compass today.** The `Provider` store is
read-only display data for the System Health page
(`system_health.py:33-43`); no HTTP client exists anywhere under
`app/business/core/provider/` or elsewhere. More broadly, Second Brain's
backend never calls an LLM directly today — every real model call goes
through Hermes (`app/business/hermes/client.py` / `app/hermes/client.py`),
which is a full agent-turn subprocess/session, not a lightweight structured
call.

Operator's own idea, evaluated and accepted: use the Compass-hosted
`gpt-oss-120b` (Core42) model for this, via a **new, dedicated, direct HTTP
client** built specifically for the moderator's routing decision — **not**
routed through Hermes. Reasoning, disclosed to and accepted by the operator:
the moderator now runs on every message, so it needs to be fast; a Hermes
call is a full agent-turn with real session/subprocess startup overhead,
which actively fights the "faster routing" goal the operator stated. This is
genuinely new backend infrastructure (auth, request/response shaping) — the
env vars were anticipated but never wired up. **Flag for `/plan-tasks`:**
this is very plausibly ADR-worthy (first-ever direct-to-LLM client in this
backend, a real structural boundary decision, matching MUST-FLAG trigger 3)
— the architect should decide whether this needs a new ADR or extends an
existing one (`ADR-022` already discusses `has_real_client`/provider
plumbing, per the investigation above).

### 3. Reply-to-message (new capability, both surfaces, different purpose in
each — operator's explicit answer: "Both surfaces")

- **Cockpit** (`Cockpit.tsx`, multi-agent): replying to a specific message is
  a **strong signal fed into the LLM moderator's reasoning — not a hard
  override** (operator's explicit choice over hard-override, after
  weighing both). The moderator still gets final say; e.g. if the reply
  text clearly asks a different agent's specialty question, it can route
  elsewhere anyway. This directly gives the moderator exactly the kind of
  context a human would use to disambiguate "Yes" — which is the real fix
  for the reported bug, with the short-reply shortcut (§1) as a cheaper
  first-pass for the most common case.
- **Chat panel** (`AgentChatPanel.tsx`, single-agent): only one agent exists
  here, so reply-to-message can't affect *who* answers (already
  unambiguous). Its purpose is **context-anchoring** — "I'm asking about
  THIS specific earlier answer" — a different value proposition from the
  Cockpit's use of the same mechanism.

**Real overlap with `REQ-SB-82-US-04`, disclosed, not ignored:** that story's
own Scenario 4 (async Research Agent result "lands as a reply threaded to
the SPECIFIC question that triggered it") already flagged `net-new-design-
needed` for threaded/parent-child reply rendering — confirmed then, still
true: "no real chat surface anywhere in this app... shows this pattern
anywhere" (`REQ-SB-82-US-04`'s own Notes, `ChatMessageText`/`.chat-thread`
is flat-list-only). **This plan's reply-to-message work is the natural,
shared building block for that** — "a message can reference a parent
message and render as a reply" is the same underlying data-model/UI need in
both cases. The story this plan produces should build that primitive for
real (not a narrow, Cockpit-only hack), so `REQ-SB-82-US-04` can build its
own threaded async-result rendering on top of it later, once that story's
own separate open questions (the Hermes live-back-channel risk) are
resolved — genuinely reducing that story's remaining scope, not just
sitting beside it. `/plan-tasks` should decide the exact reusable shape
(likely: a `reply_to_message_id` field on a stored message, surfaced through
the API, with `AgentChatPanel.tsx`/`Cockpit.tsx` each getting their own
rendering treatment for it).

## Scope for the new story (proposed `REQ-SB-82-US-06`)

**In scope:**
- `chat_store.py` thread schema: add a "last-answering agent" concept and a
  `reply_to_message_id` field on stored messages.
- Short-reply shortcut in `chat_turn.py`/`moderator.py` (or wherever
  `/plan-tasks` lands it) — routes a low-signal message straight to the
  thread's own last-answering agent.
- A new, dedicated Compass HTTP client (`gpt-oss-120b`) for the moderator's
  routing decision — real auth, request/response shaping, error handling
  (never silently fabricate a routing decision on a client failure — fall
  back to the existing deterministic keyword-overlap `route_question` as a
  degrade path, not a broken chat).
- LLM-based moderator replacing `moderator.route_question`'s keyword-overlap
  for every message (not just ambiguous ones) — given roster
  descriptions, recent history, the new message, and (if present) its
  `reply_to_message_id`'s context.
- Reply-to-message UI + wiring in both `Cockpit.tsx` (strong hint into the
  moderator, not a hard override) and `AgentChatPanel.tsx`
  (context-anchoring only, no routing effect).

**Out of scope (explicitly, not this story):**
- `REQ-SB-82-US-04`'s own async Research Agent fallback + threaded-reply
  rendering for THAT flow, and its disclosed Hermes live-back-channel
  risk — unaffected, still that story's own open problem. This plan's
  reply-to-message primitive is meant to be reusable there later, not a
  resolution of that story's remaining scope.
- Any change to `REQ-SB-20`'s own Hub-routing mechanism (agent-initiated,
  different mechanism, same precedent `REQ-SB-82-US-04` already
  established for coexistence).
- Provider CRUD API/UI (the `ProviderManager` already has `create`/
  `update`/`delete` methods with no router exposing them) — out of scope
  unless `/plan-tasks` finds it's genuinely needed to configure the new
  Compass client; likely a static config read (env vars already exist) is
  sufficient for a first pass.

## Open items for `/plan-tasks` to resolve (not decided in this plan)

- Exact short-reply detection rule (length threshold vs. fixed vocabulary vs.
  both).
- Exact Compass request/response contract for `gpt-oss-120b` (the model's
  own real API shape needs confirming, not assumed here).
- Whether the new Compass client needs its own ADR or extends `ADR-022`.
- Exact reply-to-message UI treatment (visual affordance for "replying to
  X" in both surfaces) — no `html-prototype/` screen covers this; likely
  `net-new-design-needed` same as `REQ-SB-82-US-04`'s own threaded-reply
  flag, so `/design` may need to run first for the two surfaces' own
  treatment before `/plan-tasks` cuts tasks, matching the established
  design-first-precursor discipline for genuinely new UI patterns.
