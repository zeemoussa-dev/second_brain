---
id: REQ-SB-97-US-01
title: Can the agent I am asking actually perform this Action? — per-agent performability and deploy state
requirement_ids: [REQ-SB-97]
requirement_section: "REQ-SB-97: Edit an Action, and Have the Agent Actually Able to Perform It"
phase: P2
status: Draft
gate: flagged
gate_reason: "trigger-8 (two equally-valid scopings of REQ-SB-97: extend the in-flight REQ-SB-95-US-02 — whose T03 CRUD API and T06 catalogue/editor screen are still outstanding in SPRINT-087 and already cover the 'finish the Action surfaces' bullet — or add this story for only what is genuinely beyond it; this story takes the second, and the human should confirm before SPRINT-087 is planned around it) + trigger-7/trigger-4 (REQ-SB-97's mail-sending bullet asks the operator to reverse a hard constraint recorded in MEMORY.md and is therefore deliberately NOT specced here — ESC-067)"
sprint: ""
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-97-US-01 — Can the agent I am asking actually perform this Action? — per-agent performability and deploy state

## Story

**As a** Second Brain operator
**I want** an Action's screen to tell me which of the agents allowed to call it can
actually perform it right now, and why each one that cannot, cannot
**So that** a saved Action stops being a promise that resolved against a catalogue
and starts being a capability I can trust the agent I am asking to have

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-97* — Finding 2 ("a saved Action is not a
  capability": an Action whose implementation is a Skill means something to a
  Hermes agent only when that Skill is deployed into **that agent's own profile**;
  nothing checks that — "which is `REQ-SB-96` seen from the other end"), plus the
  second and third **What is wanted** bullets (say on save whether the agents that
  may call it can actually perform it; a deploy state per Action).
- **Overlap with `REQ-SB-95-US-02`, and what this story deliberately does not
  re-spec.** The PRD's first bullet — "finish the Action surfaces: list, create,
  edit, delete, and see why a broken Action is broken" — is **already specced and
  already decomposed** in `REQ-SB-95-US-02`:
  - `AC-01`/`AC-02`/`AC-03` (save, refuse an unresolvable implementation, exactly
    one implementation) and `AC-07` (a broken Action is visible without calling it)
    are locked ACs there.
  - `T03` (Actions CRUD API) and `T06` (catalogue + editor screen) are the two
    outstanding tasks in `SPRINT-087`; `T01`, `T02`, `T04` and `T07` are `Done`
    (2026-10-16).
  So REQ-SB-97's first bullet needs **no new story — it needs `SPRINT-087` to
  finish.** This story covers only what `REQ-SB-95-US-02` genuinely does not do.
- **Why that gap is real, measured in the code.** `ActionManager`'s resolution
  (`business/core/actions/action_manager.py`) asks `deployed_skill_ids()`, which is
  `{skill.id for skill in SkillManager().get_all() if skill.deployed_to}` — i.e.
  **"is this Skill deployed to *anybody*, according to the framework's own
  unverified claim"**. Two consequences, both exactly REQ-SB-97's Finding 2:
  - An Action resolves install-wide while the specific agent in `allowed_callers`
    does not carry that Skill at all.
  - It resolves off `deployed_to`, the very claim `REQ-SB-96`'s Finding 1 measured
    to be wrong (41 profiles claimed, every deployed copy a month stale).
  `ActionManager.resolution_report()` is therefore per-Action, never per-agent.
- **`allowed_callers` is already the right key.** `ADR-033` settled it as a list of
  agent ids or `["*"]`, "because an agent's id IS the Hermes profile id everywhere
  in this codebase" — which is precisely what makes per-profile performability
  computable at all.
- **The mail-sending bullet is deliberately absent from this story.** REQ-SB-97's
  own Finding 3 calls it "a policy question, not only plumbing", and `MEMORY.md`
  (2026-09-07) records the constraint as a hard framework rule: *"capture reads
  mail and writes only to the vault, never back to the mailbox… no `sendMail`…
  an agent that can send mail as the operator is a different risk class from one
  that files notes, and nothing in this product needs it."* The analyst may not
  edit `MEMORY.md` and will not spec around it. Logged as `ESC-067`, with a
  decision request in `REVIEW-QUEUE.md`. See **Non-Goals**.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The Action's screen says who can perform it, and who cannot and why

```gherkin
Given a catalogued Action whose allowed_callers name several real agents
When the operator opens that Action
Then each allowed caller is listed with whether it can perform this Action right
    now
  And every agent that cannot is given a reason naming the specific thing that is
    missing for that agent
  And an Action every allowed caller can perform says so, rather than leaving the
    operator to infer it from an absence of warnings
```

### Scenario 2: Performability is measured per profile, not claimed install-wide

```gherkin
Given an Action whose implementation is a Skill that is deployed into some
    profiles but not into the profile of an agent in allowed_callers
When that Action's performability is read
Then the agent whose profile lacks the Skill is reported as unable to perform it,
    naming the Skill and the profile
  And the verdict is computed from what that profile actually carries, never from
    the Skill's deployed_to list
  And an Action that resolves at save time against the install as a whole is still
    reported as unperformable for that agent
```

### Scenario 3: Saving tells the operator the truth without blocking the save

```gherkin
Given the operator saves an Action whose implementation resolves on this install
When one or more of its allowed callers cannot perform it
Then the save succeeds and the response states, per agent, which cannot and why
  And nothing about that warning weakens the existing refusal of an implementation
    that does not resolve at all
  And saving an Action every allowed caller can perform reports no such warning
```

### Scenario 4: A wildcard caller is answered honestly

```gherkin
Given an Action whose allowed_callers is ["*"]
When its performability is read
Then every real agent on the install is evaluated, and the result says how many
    can perform it and names those that cannot
  And an Action no agent at all can perform is reported as such rather than as
    allowed-for-everyone
```

### Scenario 5: What "performable" means differs by implementation kind, and is stated

```gherkin
Given Actions implemented as a Skill, as an HTTP route and as a UI feature
When their performability is read
Then a skill-implemented Action is performable by an agent only when that agent's
    own profile carries the Skill
  And an http-implemented Action's performability is a property of the running app
    rather than of any one profile, and is reported that way rather than as a
    per-agent gap
  And a ui-implemented Action is reported as operator-performed rather than as
    something an agent can execute
```

### Scenario 6: Deploy state is current, because it is never stored

```gherkin
Given an Action reported as performable by a named agent
When the Skill behind it is undeployed from that agent's profile
Then the next read reports that agent as unable to perform it, with the new reason
  And no stale verdict is served from anything written into Action.json
  And deploying the Skill back into that profile restores the performable verdict
    with no edit to the Action
```

### Scenario 7: An install that cannot be read does not become a verdict

```gherkin
Given the Hermes install is unreachable, or a profile's skills cannot be listed
When an Action's performability is read
Then the result says the install could not be read, and for which agents the
    answer is therefore unknown
  And no agent is reported as able to perform an Action on the strength of an
    unread install
```

## Affected Screens

- `src/frontend/src/pages/SettingsActionsPage.tsx` (name indicative — **created by
  `REQ-SB-95-US-02-T06`, not by this story**) — the single-Action view gains a
  per-allowed-caller performability list with a reason per agent (Scenarios 1–5)
  and the unreadable-install state (Scenario 7). Reuses the live approved
  `.item-list`/`.item-row` and badge families.
- The Actions catalogue list — a per-Action deploy-state badge, distinct from the
  existing broken/resolves badge that `REQ-SB-95-US-02-AC-07` already covers.
- `html-prototype/settings.html` — **not** the design authority (see Notes →
  Prototype parity).

## Dependencies

- **Blocked by:**
  - `REQ-SB-95-US-02` — specifically its outstanding `T03` (Actions CRUD API) and
    `T06` (catalogue + editor screen) in `SPRINT-087`. There is no Action screen to
    add a performability panel to until they land.
  - `REQ-SB-96-US-01` — per-profile deployment truth is what Scenario 2 is
    computed from. Building a second, Action-only way to ask "what does this
    profile really carry" is the duplicated-drift-logic failure `REQ-SB-96` exists
    to stop.
- **Related to:** `REQ-SB-96-US-02` (deploying the Skill is how an operator fixes
  an unperformable Action); `REQ-SB-95-US-03` (the call gate — this story predicts
  on screen what that gate would decide at call time); `REQ-SB-98-US-01` (a
  Workflow step's brokenness is this verdict, one level up).
- **External:** a real Hermes install with more than one profile, to measure
  per-profile difference against.

## Constraints

- **Never stored, always computed.** A performability verdict is a function of
  something *else* changing (a Skill undeployed, a profile removed, a route gone),
  so a stored one is wrong from the moment it is written — the discipline
  `ActionManager.resolution_report()` already states for broken Actions.
- **One source of deployment truth.** Per-profile facts come from
  `REQ-SB-96-US-01`'s comparison, not from a parallel reader and not from
  `deployed_to`.
- **Do not weaken `REQ-SB-95-US-02`'s locked ACs.** `AC-02` still refuses an
  implementation that does not resolve; this story adds a non-blocking per-agent
  warning beside it, and `AC-07`'s broken-Action status keeps its meaning.
- **`allowed_callers` keeps `ADR-033`'s shape** — agent ids or `["*"]`. This story
  reads it; it does not redefine it.
- **No new mailbox capability.** Nothing in this story grants, enables or prepares
  mail sending (see Non-Goals and `ESC-067`).
- **One Manager is the sole gateway**; raw I/O stays in `data_access/`.

## Implementation Tasks

<!-- Owned by the decomposer at /plan-tasks. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Action list / create / edit / delete, and the "why is this broken" display** —
  `REQ-SB-95-US-02`, tasks `T03` and `T06`, outstanding in `SPRINT-087`. Finishing
  that sprint *is* REQ-SB-97's first bullet; duplicating it here would mint a
  second editor for one entity.
- **A mail-sending capability for an Action, scoped to internal recipients** —
  REQ-SB-97's fourth bullet, **deliberately unspecced**. It reverses the hard
  constraint recorded in `MEMORY.md` (2026-09-07): the pipeline is read-only
  against the mailbox, "an explicit operator decision, not a feature to add
  quietly". The analyst may not edit `MEMORY.md`, and will not write acceptance
  criteria that assume a reversal the operator has not made. Logged as `ESC-067`
  with a decision request in `REVIEW-QUEUE.md`; once the operator decides, it is a
  new story (`REQ-SB-97-US-02`), not an edit to this one.
- **Fixing an unperformable Action automatically** — deploying the missing Skill is
  `REQ-SB-96-US-02`'s operation, invoked by the operator.
- **Enforcing performability at call time.** `REQ-SB-95-US-03`'s call gate owns the
  refusal; this story makes the same answer visible *before* anyone asks.
- **Rewriting `deployed_to`** to agree with reality — `REQ-SB-96` territory.
- **Retro-cataloguing existing in-app features as Actions** (already out of scope
  in `REQ-SB-95-US-02`).

## Notes

**Prototype parity (`html-prototype/settings.html` is the only prototype screen in
scope):**

- Settings landing navigation — **Superseded**: the real `SettingsPage.tsx`
  icon-card grid replaced the prototype's flat card stack on 2026-08-27.
- Actions list and Action editor regions — **Specced elsewhere**:
  `REQ-SB-95-US-02` owns them (its own parity note covers the same screen). This
  story adds one panel inside the editor and one badge in the list.
- The per-agent performability panel — **Specced functional-first** (Scenarios
  1–5), as a composition of the already-approved `.item-list`/`.item-row` and
  badge families, under the operator's 2026-08-31 functional-first precedent
  (recorded in `REQ-SB-85-US-01`'s `gate_reason`). If the human disagrees,
  `/design REQ-SB-97` before `/plan-tasks` is the cheap correction.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- `deployed_skill_ids()` in `action_manager.py` is the exact function Finding 2 is
  about; whether it becomes profile-aware or is joined against
  `REQ-SB-96-US-01`'s comparison is the architect's call. Note `_ResolutionSources`
  already exists to gather live sources **once per report** rather than per Action
  — the same O(n × sources) discipline applies here, now multiplied by profiles.
- "The tool enabled" (PRD, second bullet) has no measured meaning in this
  repository yet; a profile's toolsets are read for `REQ-SB-99-US-01`. Whether a
  disabled toolset counts as a performability gap is worth settling between the two
  stories rather than twice.
- Scenario 5's http case interacts with `ADR-033`'s loopback call path: an
  http-implemented Action is performed by this app on the agent's behalf, so
  "deployed into the profile" is the wrong question for it. The ACs state the
  behaviour; the wording of the on-screen explanation is the architect's.

**Audit breadcrumb:**

gate: flagged 2026-10-17 — trigger 8 (two equally-valid scopings against the
in-flight `REQ-SB-95-US-02`; this story took the narrower one and the human should
confirm before `SPRINT-087` is re-planned) and trigger 7 + trigger 4 (REQ-SB-97's
mail bullet contradicts a hard `MEMORY.md` constraint; `ESC-067` written, the
bullet left unspecced). `REQ-SB-97` is finalised in the PRD with no
`<!-- Draft -->` marker; no ADR created or changed by this pass; not oversized.
