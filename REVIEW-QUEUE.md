# REVIEW QUEUE

Live human inbox. Items here are awaiting a human decision before the pipeline can
proceed. Remove an item when it is resolved; add an `ESCALATIONS.md` entry if the
resolution involved a backward step.

<!-- Entry format:
- [ ] YYYY-MM-DD · **STORY-ID or SPRINT-ID** · one-line summary of what's needed
  Plain English: what's blocked, why, what the impact is if left unresolved.
  **What to do:** the concrete next step — command to run or decision to make.
  → `Implementation/UserStories/<file>.md` or `Implementation/Sprints/<file>.md`
-->

> **Emptied 2026-09-06 (operator-directed).** This file had grown to 9,101 lines
> / 612 KB carrying **134 unresolved items**, the oldest from 2026-08-10, and was
> not being read. An inbox nobody opens is worse than no inbox: agents kept
> flagging into it, and each flag read as "a human will decide this" when nobody
> would.
>
> **Nothing is lost.** The full contents are in git at `7db3968`:
>
> ```bash
> git show 7db3968:REVIEW-QUEUE.md
> ```
>
> The discarded items were mostly retro-harvest reminders, scope-internal
> judgement-call spot-checks, ADR reviews, and three design sign-offs — all
> against work that has since shipped.
>
> **The real issue is upstream, and is not fixed by emptying this.** Six agents
> and four commands write here (`analyst`, `architect`, `coder`, `decomposer`,
> `designer`, `product-owner`; `/design`, `/flow`, `/implement-sprint`,
> `/load-context`). They will refill it at the same rate unless either the
> MUST-FLAG triggers are narrowed, or this file is actually reviewed. If it fills
> up unread again, the flagging rules are what need changing — not this file.

- [x] 2026-10-16 · **REQ-SB-95-US-01** · Decide where the operator's own email address really lives before the Operator Profile absorbs it — resolved 2026-10-16: both env and Profile, written through by sync_settings_to_hermes (ADR-035)
  Plain English: the new Operator Profile is meant to be the one place that holds who you are, your mail addresses and your team. The architecture note for this work says it should take over "your email address" rather than sit beside it — but that setting is not a new field. It is required for the backend to start at all, it has its own step in the setup wizard, it is edited today on Settings → System, and copies of the code that reads it are already deployed inside live Hermes worker profiles doing email and meeting capture. There are two defensible ways to do the takeover: keep the existing startup setting as the real store and have the Profile screen edit it, or move the value into the Profile file and retire the setting. Pick the wrong one and the agent keeps telling your own messages apart correctly in testing while a deployed capture job silently stops doing so — the same shape as the 2026-09-04 outage where a skill read the wrong data root and 54 emails quietly vanished. The story is written so it does not guess: its acceptance criteria say "exactly one editable place, and every existing consumer still resolves the same value", without naming which store wins.
  **What to do:** decide which store is the single source of truth for the operator's own email, and whether the deployed Hermes capture scripts need redeploying as part of it. Then either record it on the story and re-run `/plan-tasks REQ-SB-95-US-01`, or hand it to the architect to settle in that stage. If you would rather not decide now, the rest of REQ-SB-95 (`US-02` through `US-04`) is `gate: clear` and can proceed without this story.
  → `Implementation/UserStories/REQ-SB-95-US-01-operator-profile.md`

- [x] 2026-10-16 · **REQ-SB-95-US-05** · Two accepted architecture decisions disagree about who owns Customer/Partner entity knowledge — resolved 2026-10-16: resolver is framework, Customer stays the plugin (ADR-035, ESC-063 Resolved)
  Plain English: this story makes "give me the updates about Adobe" read Adobe's own hub note and its tagged threads and meetings, instead of searching the whole vault. The mechanism is settled — one tag-keyed index covering every `customer/*` and `partner/*` tag, so a new entity needs no setup. What is not settled is which repository builds it. `ADR-032` writes it as framework work. `ADR-022` decided the opposite for exactly these concepts: Customer, Partner, `Entities.md`, its Settings page and `company_index` all move out of the framework into an Entities plugin, and framework core must never know a plugin exists — the test being that a CFO's second brain cares nothing about Partners and Customers. This is already half-true in the code: `Settings/Entities.md` is registered today as plugin seed data. So building this in the framework would knowingly cut across `ADR-022`, and building it in the plugin repository means this story is not framework work at all. Left unresolved, whoever picks it up at `/plan-tasks` will quietly choose for you.
  **What to do:** state which side of the `ADR-022` boundary the Entities registry, the resolver and the tag-keyed index live on — and whether that means amending `ADR-032` or scoping `ADR-022`'s Entities extraction around it. Logged as `ESC-063` in `ESCALATIONS.md`. Note the related, smaller point: `ADR-032` itself is Accepted but has never had a human review entry here.
  → `Implementation/UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`

- [ ] 2026-10-16 · **REQ-SB-95-US-03** · `ADR-033` decides how an agent actually invokes an action — review the call path before the build starts
  Plain English: `ADR-032` said an action call must be checked by the framework, but not *where* that check happens, and the obvious place turned out not to exist — the direction where Hermes calls into this app was deleted in September, and the in-app chat screen only watches a Hermes conversation go by, so it cannot stop anything. `ADR-033` was written to settle it: the agent calls one new address on this app (`POST /actions/{id}/call`) through a single small skill, the same way the vault-search skill already phones this app on `127.0.0.1:8001` today. The app checks the action exists, that this agent is allowed to run it, and that every required input was supplied — then performs it if it owns it (an HTTP feature), points the operator at the screen if it is a UI feature, or hands back a one-time permission slip if the thing that does the work is a skill living inside Hermes. Two things you should know before approving: this is a deliberate re-opening of a Hermes→app direction, narrower than the MCP surface that was deleted, and the trust is loopback — the calling agent says which agent it is and the app believes it, exactly as the existing vault-search call does. Also decided here: confirmation ("ask me before you do that") is a new small record the app owns, because the old Pending Approvals screen's router is archived and no longer in the repo at all — so this story cannot reuse it the way the story assumed.
  **What to do:** review `ADR-033` in `Implementation/Architecture/ADR.md` — particularly the loopback call path and the honest trust boundary — approve or reject, then run `/plan-tasks REQ-SB-95-US-03` again if you change it.
  → `Implementation/UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`

- [ ] 2026-10-16 · **REQ-SB-95-US-04** · `ADR-034` decides the framework runs a workflow, rather than telling the agent to follow one
  Plain English: a Workflow is your written-down handling for a kind of request — the ordered steps, which need your confirmation, what gets reported. The cheap way to ship it is to paste those steps into the agent's instructions and hope it follows them; that would make "it did not skip a step" something nobody can check, which is the same silent-failure shape `ADR-032` rejected when it refused prompt-only grounding. `ADR-034` instead gives a run its own record on disk: the framework hands the agent one step at a time, will not move on until the step's result is recorded, pauses where you asked to confirm, and builds the final report out of what actually happened rather than what the agent remembers. The cost is more back-and-forth per request and one more small store; the gain is that an abandoned run stays visibly open instead of looking finished.
  **What to do:** review `ADR-034` in `Implementation/Architecture/ADR.md`, approve or reject, then run `/plan-tasks REQ-SB-95-US-04` again if you change it.
  → `Implementation/UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`

- [ ] 2026-10-16 · **REQ-SB-95-US-02** · `ADR-033` fixes two fields the Action catalogue stores — confirm them before the editor is built
  Plain English: this story builds the Actions catalogue itself, and `ADR-032` already settled most of it. Two fields were left open and `ADR-033` has now set them. "Who may run it" is a plain list of agent ids (or `*` for everyone), because an agent's id is also its Hermes profile id — the one name both sides already share; a Section was rejected because an agent that nobody has placed yet has no section at all. "Needs confirmation" stays a simple yes/no here, and the machinery that honours it belongs to `US-03`. Nothing else in this story changed, and it is only flagged because an ADR was written in the same pass.
  **What to do:** review the `allowed_callers` and confirmation-flag decisions in `ADR-033` (`Implementation/Architecture/ADR.md`), approve or reject, then run `/plan-tasks REQ-SB-95-US-02` again if you change them.
  → `Implementation/UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`

