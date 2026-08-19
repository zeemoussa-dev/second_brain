---
id: REQ-SB-28-US-01
title: File upload on agent chat — Compass summarization, handoff to the Vault Filing Expert, and vault filing with tags/wikilinks
requirement_ids: [REQ-SB-28]
requirement_section: "REQ-SB-28: File Upload for Agents"
phase: P1
status: Done
gate: flagged
gate_reason: "carried forward from the decomposer pass (trigger-3, ADR-034) plus T05's own trigger-8 scope-internal judgement calls — all resolved/verified, human spot-check only, not blocking. All 10 locked ACs verified live end-to-end (T01-T05, all Done)."
sprint: SPRINT-038
created: 2026-08-11
updated: 2026-08-14
---

# REQ-SB-28-US-01 — File upload on agent chat — Compass summarization, handoff to the Vault Filing Expert, and vault filing with tags/wikilinks

## Story

**As a** Second Brain user
**I want** to attach a file to a chat message I send an agent and have the
agent summarize it via Compass and hand that summary to the Vault Filing
Expert, which decides where it belongs and files it with the right tags
**So that** I can upload source material (a document, a book, a pricing
sheet) once and later find and link to a properly-placed, properly-tagged
vault note built from it, without doing the filing myself

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-28: File Upload for Agents* — "The
  user can upload a file to an agent; the agent summarizes it via Compass
  and hands the summary to the Vault Filing Expert (REQ-SB-35), which
  decides where it belongs and files it with the right tags — the same
  mechanism regardless of which agent received the upload." Acceptance:
  "The user can attach a file to a chat message sent to an agent; the
  agent summarizes the file's contents via Compass; the summary is handed
  to the Vault Filing Expert, which files it into the vault with
  appropriate tags, matching existing schema conventions, so the user can
  link to and find it later."
- **This is a RE-SPEC of an already-`Draft` story following an operator
  PRD rewrite (2026-08-13), not a fresh story.** The requirement's own
  mechanism was previously undecided ("how does 'summarize and file' map
  onto a skill invocation vs. a bespoke capability" — left open). The
  operator has now resolved it directly, quoted verbatim in the PRD's own
  breadcrumb: *"The Files we got from the Attachments we need to pass
  them to Compass to Generate a Summary and we Store the Summary in the
  Vault and tags so I can Link and use them later"* — then, asked whether
  this is the same mechanism as a dedicated file-intake agent handing off
  to the Vault Filing Expert: *"Same thing."* This story is rewritten in
  place (never a new same-numbered file) per this project's append-only
  spec rule — the story was still `Draft`, never `Ready`/`Done`, so an
  in-place rewrite is the correct move, not a new story.
- **The mechanism, concretely, per the PRD's own resolved framing:** (1)
  summarization is a Compass-backed capability (a plain chat-completion
  call, the same shape `compass_client.classify_email`/`classify_task`
  already use — confirmed by direct reading of
  `app/data_access/compass_client.py`; no generic `summarize_*` function
  exists there yet, so this story adds one, same client/error pattern,
  not a new dependency); (2) the summary is never filed directly by the
  receiving agent — it always routes through the Vault Filing Expert
  (`REQ-SB-35-US-01`, **Done**), the same placement/tagging authority
  `REQ-SB-36`'s own delegated-research chain already uses, so
  upload-derived and research-derived content are filed consistently.
- **Confirmed by direct code inspection: `REQ-SB-35-US-01`'s existing
  interface already accepts exactly what this handoff needs, with zero
  changes to that story.** `app/business/vault_filing_expert.py::
  determine_placement_and_file(content: str, source_description: str,
  requesting_agent_id: str)` takes a plain summary string plus a free-text
  source description and the calling agent's id — there is no
  upload-specific input shape it's missing. This story's handoff step is
  therefore a straightforward call into already-Done, already-verified
  code (`SPRINT-023`), not new architecture on the receiving end.
- **The REQ-SB-39 dependency judgment call (per this run's own
  instruction to judge, not assume):** the PRD's own dependency line
  names `REQ-SB-39` ("summarization should be built as a Skill from the
  start, not a bespoke capability this story would otherwise invent").
  Direct inspection of `app/business/skill_registry.py`/`skill_tools.py`
  (both `REQ-SB-27-US-01`, **Done**) shows the Skills mechanism itself —
  a static `SKILLS` catalog, a `_SKILL_HANDLERS` dispatch table, and
  `grant_skill_access`/`invoke_skill` — is a plain, additive registry:
  adding a new skill (e.g. `summarize-file`) means one new catalog entry,
  one new handler function, one new dispatch-table row, and a grant to
  the relevant agent(s) — exactly the same shape `web-research` and
  `diagram-understanding` already use. **`REQ-SB-39` is specifically
  about migrating already-existing hardcoded Actions into this model**
  (`REQ-SB-39-US-01`, `Draft`/`gate: flagged`, scoped to read-only Action
  migration only) — an unrelated backward-compatibility concern, not a
  prerequisite for registering a brand-new Skill through a mechanism that
  is already `Done`. **Judgment: this story does NOT block on
  `REQ-SB-39`.** It is recorded as "Related to, not blocking" in
  `## Dependencies`, with this reasoning, rather than silently accepted
  or silently dropped — the operator's own underlying intent ("built as a
  Skill from the start, not a bespoke capability") is fully satisfiable
  today via `REQ-SB-27`'s already-Done mechanism.
- **A genuine, load-bearing technical finding, not silently patched: a
  plain Compass completion cannot meaningfully "summarize" an image
  file.** Compass is confirmed (`compass_client.py`'s docstring, and both
  its existing functions) to be an OpenAI-chat-completions-shaped
  text-only HTTP endpoint — no evidence anywhere in this codebase of
  vision/multimodal input support. The PRD's own text asserts "a plain
  Compass completion is sufficient for summarization," which holds for
  text-bearing files (`.txt`, `.md`, extracted PDF text) but not for an
  image (`.png`/`.jpg`) — that would need either a vision-capable Compass
  call (unconfirmed anywhere in this codebase) or `REQ-SB-27`'s own
  `diagram-understanding` Skill (a genuinely separate mechanism, already
  scoped to "given an uploaded image, identify and describe its
  components" — not "summarize an arbitrary document"). This story does
  not silently invent a vision path. See Constraints/Non-Goals.
- **Still genuinely open per the PRD's own current text** (unchanged from
  the prior spec pass, explicitly not decided here): which agents accept
  uploads (any agent's chat, or a dedicated intake surface), accepted
  file types/size limits, and whether uploaded originals are retained
  alongside their summary or discarded after processing.
- **Carried forward, not re-litigated: this story's own prior operator
  resolution (2026-08-12) of two of those three items still stands** —
  accepted file types PDF/`.txt`/`.md`/PNG/JPG, 20 MB cap; storage
  retention is temporary-for-processing only, never vault-retained by
  default (a `.second-brain/uploads/` scratch directory, discarded after
  the summary is produced and handed off). Nothing in the 2026-08-13 PRD
  rewrite revisits or contradicts either decision — both are general
  product/privacy policy, not specific to the earlier "raw content
  handoff to the message-processing path" mechanism this rewrite
  supersedes. The image-format entry in that accepted-types list is kept
  as stated policy (not silently narrowed by this pass), but see the
  Compass-vision finding above: **the mechanism by which an image gets
  summarized is left open to `/plan-tasks`** — either a real Compass
  vision call (if the Provider genuinely supports it, unconfirmed) or
  routing an image upload through `REQ-SB-27`'s `diagram-understanding`
  Skill instead of a plain summarization call, with its own output still
  handed to the Vault Filing Expert the same way. This is not guessed at
  here.
- **Which agents accept uploads — same literal-Acceptance-text reading
  as the prior spec pass, not re-guessed:** the PRD's Acceptance text
  says "a chat message sent to an agent," agent-agnostic, unlike a
  narrower "the My Day Agent specifically" phrasing. This story extends
  `REQ-SB-25-US-01`'s existing embedded chat panel (any agent reachable
  through it) with an attach affordance — the same surface, not a new
  one restricted to one agent.
- No `html-prototype/` screen shows any file-attachment affordance —
  reconfirmed by direct inspection of `agents-map.html`'s Chat block
  (`.chat-thread` plus a plain text send form, no attach control,
  unchanged since the prior spec pass). A `/design` pass is needed before
  this story can proceed past `/plan-tasks`.
- No backend upload endpoint exists anywhere — reconfirmed by direct
  grep of `app/api/` for `upload`/`attach` (no match) and of
  `src/frontend/src` (no match). The earlier POC-era
  `email_poc_router.py` was also directly checked and contains no
  attachment handling at all (no `attach` match) — it is not reusable
  groundwork, contrary to what might be assumed; this is genuinely
  net-new backend surface.

## Acceptance Criteria

<!-- Decomposer pass, 2026-08-13 (/plan-tasks step 2). Locked per ADR-034:
scope narrowed to text-bearing files only (.pdf/.txt/.md); image types
(.png/.jpg) are explicitly deferred, not built. Scenario 1 (original) is
tightened for the narrowed accepted-type list and the attach control's
existence; Scenario 2 is tightened to name the real extraction/summarize
mechanism; Scenario 3 is tightened to name determine_placement_and_file's
real signature; Scenario 6 is tightened to name the real, unmodified
POST /agents/{agent_id}/chat contract. The original Scenario 7 ("fails
validation") is split into two distinct honest-rejection cases so each
has its own unambiguous verification: Scenario 7 (NEW) covers an
unsupported file type (e.g. an image) — an honest capability-scoping
decline, mirroring REQ-SB-33's honest-decline pattern; Scenario 8 (was
Scenario 7) covers exceeding the size cap. Happy path first (upload
through to a filed, tagged, linkable vault note), then the resulting
note's findability, then the no-attachment regression guard, then the two
honest-rejection cases, then honest failure handling at each handoff
point. -->

### Scenario 1: Attaching a supported file to a chat message stores it and shows it in the chat thread

```gherkin
Given the user has an agent's chat panel open, with an attach control
    available in the chat input row
When the user attaches a file with an accepted extension (.pdf, .txt, or
    .md) and size (20 MB or under) to a chat message and sends it
Then the message, with a clear indication of its attached file (at least
    the filename), appears in the chat thread
  And the file's bytes are stored temporarily outside the vault (under
    .second-brain/uploads/) so they can be read and summarized
```

<!-- AC-ID: REQ-SB-28-US-01-AC-01 -->

### Scenario 2: The agent summarizes the attached file's real content via Compass

```gherkin
Given the user has sent a chat message with an attached, accepted file to
    an agent
When the agent processes the message
Then the file's text content is extracted (directly for .txt/.md, or via
    PDF text extraction for .pdf) and passed to a Compass completion call
    that produces a summary of that content
  And the summary reflects the file's actual extracted content, not a
    fabricated or generic placeholder
```

<!-- AC-ID: REQ-SB-28-US-01-AC-02 -->

### Scenario 3: The summary is handed to the Vault Filing Expert, which files it with tags

```gherkin
Given a Compass-generated summary of an uploaded file exists (Scenario 2)
When the agent hands the summary off
Then it is passed to the Vault Filing Expert's existing
    determine_placement_and_file(content, source_description,
    requesting_agent_id), with source_description identifying the upload
    (at least the original filename) and requesting_agent_id set to the
    receiving agent's id
  And the Vault Filing Expert determines placement and tags per its own
    existing behavior and writes the resulting note — the receiving agent
    does not file the content itself through a separate write path
```

<!-- AC-ID: REQ-SB-28-US-01-AC-03 -->

### Scenario 4: The filed note is tagged, linkable, and findable later

```gherkin
Given the Vault Filing Expert has filed a summary derived from an uploaded
    file (Scenario 3)
When the user later looks for that content in the vault
Then the resulting note carries tags consistent with the vault's existing
    taxonomy conventions and any wikilinks the standing tags-and-wikilinks
    rule requires
  And the user can locate and link to the note the same way as any other
    Vault-Filing-Expert-filed content
```

<!-- AC-ID: REQ-SB-28-US-01-AC-04 -->

### Scenario 5: The uploaded original is not retained in the vault, and its temporary copy is cleaned up

```gherkin
Given a file has been attached, summarized, and its summary filed
    (Scenarios 1-4)
When the process completes
Then the original uploaded file is never written into the Obsidian vault —
    only the Vault Filing Expert's own filed note (the summary, tags, and
    wikilinks) persists
  And the temporary copy under .second-brain/uploads/ is deleted once it
    has been summarized, regardless of whether the later filing step
    succeeds
```

<!-- AC-ID: REQ-SB-28-US-01-AC-05 -->

### Scenario 6: Sending a chat message with no attachment is unaffected

```gherkin
Given the user sends an ordinary chat message with no file attached, via
    the existing POST /agents/{agent_id}/chat endpoint
When the agent's existing message-processing path runs
Then its behavior is identical to before this story shipped — no
    summarization or Vault-Filing-Expert handoff is triggered, and neither
    that endpoint's request/response contract nor the REQ-SB-25-US-01
    conversational chat mechanism changes for a plain message
```

<!-- AC-ID: REQ-SB-28-US-01-AC-06 -->

### Scenario 7: Attempting to attach a file of an unsupported type (e.g. an image) is honestly declined, never silently processed

```gherkin
Given the user attempts to attach a file whose type is not one of the
    accepted text-bearing types (.pdf, .txt, .md) — for example a .png or
    .jpg image
When the user sends the message
Then the user receives a clear, honest message naming the file type as
    not yet supported for summarization — never a fabricated or generic
    summary, and never a silent no-op
  And the file is not stored, and no summarization or filing is attempted
```

<!-- AC-ID: REQ-SB-28-US-01-AC-07 -->

### Scenario 8: Attempting to attach a file that exceeds the size limit is rejected clearly

```gherkin
Given the user attempts to attach a file that is an accepted type but
    exceeds the 20 MB size limit
When the user sends the message
Then the user receives a clear rejection message explaining the file was
    too large and was not accepted
  And no partial/corrupt attachment is stored, and no summarization or
    filing is attempted
```

<!-- AC-ID: REQ-SB-28-US-01-AC-08 -->

### Scenario 9: A Compass summarization failure is surfaced honestly, not silently dropped

```gherkin
Given the user has attached a valid, accepted file to a chat message
When the Compass summarization call fails (e.g. the Provider is
    unavailable or the call errors)
Then the user is told the summarization failed, honestly and specifically
    — never a fabricated summary and never a silent no-op
  And the Vault Filing Expert is never invoked with a fabricated or empty
    summary, and no partial vault note is written
```

<!-- AC-ID: REQ-SB-28-US-01-AC-09 -->

### Scenario 10: A Vault Filing Expert failure after a successful summary does not lose the summary

```gherkin
Given a Compass summary of an uploaded file was produced successfully
    (Scenario 2)
When the handoff to the Vault Filing Expert fails or it cannot
    immediately write the content (e.g. its own selected Provider is
    unavailable, mirroring its existing "unavailable" status)
Then the failure is surfaced to the user honestly, naming what succeeded
    (the summary) and what did not (the filing)
  And the summary is not silently discarded — it remains visible in the
    chat thread so the user is not left with nothing to show for the
    upload
```

<!-- AC-ID: REQ-SB-28-US-01-AC-10 -->

## Affected Screens

- No `html-prototype/` screen currently covers this. `agents-map.html`'s
  agent detail panel's Chat block (`.chat-thread` + send form) is the
  natural surface this story extends with an attach-file control — but no
  such control exists in the approved prototype (reconfirmed this pass,
  unchanged). Per the mandatory prototype-reconciliation rule, this
  triggers `net-new-design-needed`; recommend `/design REQ-SB-28` for the
  attach affordance itself and for however the chat thread surfaces a
  summarization-in-progress/filed-note-confirmation state (Scenarios 2-5,
  8-9 all need some visible acknowledgement in the thread, exact shape
  left to `/design`).

## Dependencies

- **Blocked by (all satisfied already):** `REQ-SB-25-US-01` (Real
  Conversational Agent Chat, **Done**) — the embedded chat panel this
  story attaches files to. `REQ-SB-35-US-01` (Vault Filing Expert,
  **Done**) — the filing/tagging authority this story hands summaries to;
  confirmed its real interface (`determine_placement_and_file`) already
  accepts what this story needs, with zero changes to that story. Both
  are real, satisfied blockers, not aspirational.
- **Related to, not blocking:** `REQ-SB-27-US-01` (Skills Repository,
  **Done**) — this story's Compass-summarization capability is intended
  to be registered as a new Skill through this already-Done mechanism
  (`skill_registry.py`/`skill_tools.py`'s catalog + dispatch + grant
  pattern), satisfying the operator's own "built as a Skill from the
  start" intent without needing any new architecture here.
- **Related to, not blocking (judgment call, see Context):**
  `REQ-SB-39-US-01`/`-US-02` (Unify Agent Capabilities Under Skills,
  `Draft`, `gate: flagged`) — the PRD's own dependency line names this,
  but direct code inspection shows `REQ-SB-39` is scoped to migrating
  already-existing hardcoded Actions into the Skills model, not to
  building brand-new Skills, which the already-Done `REQ-SB-27-US-01`
  mechanism already fully supports. This story does not wait on
  `REQ-SB-39`.
- **Related to:** `REQ-SB-20-US-01` (Hub cross-Section routing, **Done**)
  — the mechanism by which the receiving agent's summary reaches the
  Vault Filing Expert, mirroring how `REQ-SB-35-US-01`'s own Scenario 7
  already composes with it.
- **Related to:** `REQ-SB-36` (Agent Knowledge Bootstrapping) — that
  requirement's own PRD text names this story's mechanism ("more source
  material can be added later... via file upload (REQ-SB-28), following
  the same Vault Filing Expert step") as its own later ingestion path;
  not built here, but this story's Scenario 3 is the exact step that
  future composition depends on.
- **External:** none new. The image-summarization mechanism (Compass
  vision vs. `diagram-understanding` Skill routing, see Context) is left
  to `/plan-tasks` — not a blocker on planning, since the text-file path
  (PDF/txt/md) is independently buildable and verifiable regardless of
  how the image path is eventually resolved.

## Constraints

- **Never fabricate a summary or a filed note.** A Compass failure or a
  Vault Filing Expert failure must be surfaced honestly (Scenarios 9-10),
  mirroring this project's standing honesty posture
  (`REQ-SB-33-US-01`/`ADR-011`/`ADR-014`).
- **The receiving agent never files content itself** — every filing
  write goes through the Vault Filing Expert's own write path
  (Scenario 3), never a separate write path this story implements.
- **Accepted file types — narrowed by the decomposer per `ADR-034`,
  superseding this story's own prior 2026-08-12 operator resolution's
  image-type entry (the Constraints text above explicitly authorized this
  tuning "for a concrete implementation reason"):** PDF (`.pdf`), plain
  text/markdown (`.txt`, `.md`) only. Max size 20 MB per file. PNG/JPG
  image support is explicitly deferred, not built — see Non-Goals; an
  attempted image upload is honestly declined (Scenario 7), never
  silently processed or fabricated.
- **Storage retention (carried forward, not re-decided here): temporary-
  for-processing only, never vault-retained by default** — an uploaded
  file is stored outside the Obsidian vault (`.second-brain/uploads/`,
  the `.second-brain/` convention's first extension to raw bytes,
  `ADR-034`) only until it has been summarized and handed off
  (Scenario 5), or until validation rejects it (Scenarios 7-8).
- **The image-summarization mechanism is resolved, not left open:**
  `ADR-034` confirmed by direct code inspection that neither a Compass
  vision call nor `REQ-SB-27`'s `diagram-understanding` Skill produces a
  usable text output today — image support is deferred to a follow-up
  story (see Non-Goals), not guessed at or silently built here.
- No backend endpoint accepted a file alongside a chat message, and no
  frontend attach control existed, before this pass. `/design` was
  explicitly skipped for this batch (operator direction, per the
  architect's Notes) — the decomposer specifies a minimal, structurally
  locked attach affordance directly (Scenario 1/`AC-01`) rather than
  waiting on a prototype pass; the new endpoint's exact shape is `ADR-034`
  point 6 (`POST /agents/{agent_id}/chat/attachment`, additive,
  multipart/form-data).

## Implementation Tasks

| Task | Title | Depends on |
|---|---|---|
| [[REQ-SB-28-US-01-T01]] | `requirements.txt` (`pypdf`, `python-multipart`) + new `app/data_access/upload_storage.py` (validate/save/extract/delete) + `.second-brain/uploads/` boundary | — |
| [[REQ-SB-28-US-01-T02]] | `compass_client.py` — new `summarize_content(content, source_description)` | — |
| [[REQ-SB-28-US-01-T03]] | `skill_tools.py`/`skill_registry.py` — new `summarize-file` Skill (catalog entry + real handler + dispatch row) | T02 |
| [[REQ-SB-28-US-01-T04]] | `agents_router.py` — new `POST /agents/{agent_id}/chat/attachment` composing storage → skill (summarize) → Vault Filing Expert handoff | T01, T03 |
| [[REQ-SB-28-US-01-T05]] | `AgentDetailPanel.tsx` attach affordance + `agentsApiClient.ts` upload call, including client-side honest-rejection display | T04 |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **PNG/JPG image upload support** — explicitly deferred by `ADR-034`
  (direct code inspection confirmed neither a Compass vision call nor
  `REQ-SB-27`'s `diagram-understanding` Skill produces usable text today);
  an attempted image upload is honestly declined (Scenario 7/`AC-07`), not
  silently processed. A follow-up story builds real image summarization.
- **A confirmed Compass vision capability, or building it if it doesn't
  exist** — this story does not confirm or build multimodal Compass
  support.
- **`REQ-SB-27`'s `diagram-understanding` Skill's own implementation** —
  unchanged by this story; not composed with (see above — routing images
  through it was considered and rejected in `ADR-034`, it remains a stub).
- **Migrating any existing Action to a Skill, or the Skills grant/revoke
  UI** — `REQ-SB-39`'s own scope, not built here (see Dependencies); this
  story only registers one new Skill through the already-Done
  `REQ-SB-27-US-01` mechanism.
- **A dedicated `/design` prototype pass for the attach affordance** —
  `/design` was explicitly skipped for this batch (operator direction);
  `REQ-SB-28-US-01-T05` builds a minimal, structurally-locked attach
  control directly instead (Scenario 1/`AC-01`) — visual polish beyond
  that structural signature is out of scope pending a future design pass.
- **Retaining the original uploaded file in the vault** — explicitly
  discarded after processing by default (Scenario 5); a future "keep
  this file" action is not built here.

## Notes

**Prototype parity:** not applicable — no file-attachment region exists
in any `html-prototype/` screen today (`agents-map.html`'s Chat block
reconfirmed directly this pass: a `.chat-thread` plus a plain text send
form, no attach control anywhere, and no summarization/filing-progress
indication in the thread either). `net-new-design-needed` — recommend
`/design REQ-SB-28` for the attach-file affordance and the
summarization/filing acknowledgement shown in the chat thread.

**Why `gate: flagged` — re-checked against every MUST-FLAG trigger, not
carried forward blindly:**

1. No new material assumption of consequence — the two previously-open
   policy questions (file types, retention) are carried forward from
   this story's own prior, genuine operator resolution (2026-08-12), not
   re-guessed. The image-summarization mechanism is named as open and
   left to `/plan-tasks`, not silently assumed.
2. `REQ-SB-28` is not marked `<!-- Draft -->`/unfinalised in the PRD — it
   carries a "Scope resolved" / "mechanism resolved" breadcrumb.
3. N/A (architect/ADR trigger) — though `/plan-tasks` should expect a
   real, new Compass function (`summarize_content` or similar), a new
   Skill catalog entry, and new upload API/storage surface.
4. No new `ESCALATIONS.md` entry opened by this pass — `ESC-007` (this
   story's own prior escalation) remains `Resolved`, unaffected by this
   update; the REQ-SB-39 dependency-judgment finding and the Compass-
   vision finding are both recorded plainly in Context/Dependencies as
   defensible, single-reading resolutions, not escalated as unresolved
   ambiguity.
5. Not oversized. Unlike `REQ-SB-37`, this story composes two already-
   partially-proven mechanisms (a Compass completion call, following the
   exact `classify_email`/`classify_task` pattern; and the Vault Filing
   Expert's already-Done, already-verified write path) rather than three
   structurally distinct new flows. One story remains appropriate — the
   real net-new surface is bounded (one new Compass function, one new
   Skill entry, one new upload endpoint, one new frontend attach
   control), and every downstream consumer (`REQ-SB-35`) needs zero
   changes.
6. N/A (coder trigger).
7. No contradictory PRD inputs found. The PRD's own stated `REQ-SB-39`
   dependency and this story's own code-grounded finding that it isn't a
   real blocker are reconciled, not left as an unresolved contradiction
   (see Context/Dependencies) — this is a resolved judgment call, not a
   flagged ambiguity in itself.
8. **Genuinely unclear, and the sole live reason for `gate: flagged`:**
   the image-summarization mechanism (Compass vision vs.
   `diagram-understanding` Skill routing) is a real, undecided fork —
   named plainly, not guessed past, and does not block planning the
   text-file path. **The controlling flag, however, is
   `net-new-design-needed`** (mandatory per the prototype-reconciliation
   rule) — no file-attach affordance exists in any approved prototype
   screen.

**Net assessment vs. the prior spec pass:** this story is genuinely
*less* blocked than before. Both of the prior pass's real product
dependencies (`REQ-SB-25`, `REQ-SB-35`) are now `Done` and verified; the
receiving-end interface needs zero changes; the only remaining hard gate
is the design pass, plus one narrow, non-blocking mechanism question for
image files specifically. `REQ-SB-28-US-01`'s own `REVIEW-QUEUE.md` entry
is updated accordingly (recommend `/design REQ-SB-28`, then straight to
`/plan-tasks` — no other human decision required first).

---

## Architect pass (2026-08-13) — `/plan-tasks` step 1

**`/design` skipped for this batch (operator direction), superseding the
prior `net-new-design-needed` flag above.** The architect proceeded
directly to architecture/ADR work, following the identical precedent
`REQ-SB-40-US-01` already established ("`/design` explicitly skipped for
this batch... this pass's own architectural call, not a prototype port").

**Direct code inspection performed this pass (not re-trusted from the
story's own re-spec text):**
- `app/data_access/compass_client.py` — confirmed text-only. Both
  `classify_email`/`classify_task` build a plain OpenAI-chat-completions-
  shaped payload; no vision/image parameter anywhere.
- `app/business/vault_filing_expert.py::determine_placement_and_file(
  content: str, source_description: str, requesting_agent_id: str)` —
  confirmed its real, current signature accepts exactly this story's
  handoff shape; zero changes needed.
- `app/business/skill_registry.py`/`skill_tools.py` — confirmed the Skills
  mechanism (catalog, `_SKILL_HANDLERS` dispatch, grant/`invoke_skill`) is
  a plain, additive registry, unaffected by `REQ-SB-39`'s still-`Draft`
  Actions-migration scope. **`diagram-understanding` is confirmed to be an
  unconditional stub** — `skill_tools.diagram_understanding()` always
  returns `{"available": False, ...}`, its own docstring naming "no
  multimodal-capable Provider exists yet" as the reason. It does not
  produce a text description of an image today.
- `app/api/agents_router.py`, `app/api/email_poc_router.py` — confirmed no
  attachment/upload handling exists anywhere in the backend today.
- `requirements.txt` — confirmed no PDF-parsing library exists yet.

**Image-summarization gap, resolved:** neither of the story's own two
named options (a real Compass vision call, or routing through
`diagram-understanding`) produces a usable text output today — Compass has
no vision capability and `diagram-understanding` is a non-functional stub.
Per this run's own instruction, **this story is scoped to text-file types
only (`.pdf` via `pypdf` extraction, `.txt`, `.md`); PNG/JPG image support
is explicitly deferred to a follow-up story**, not silently built or
guessed at. The story's own Constraints text explicitly permits the
decomposer to tune the accepted-file-types default "for a concrete
implementation reason" — this is that reason; the decomposer should narrow
Scenario/AC scope to the text-file path accordingly.

**ADR written — `ADR-034`** (`Implementation/Architecture/ADR.md`): a new
temporary non-vault blob-storage boundary (`.second-brain/uploads/`, the
`.second-brain/` convention's first extension to raw bytes rather than
JSON); `pypdf` as a new dependency for PDF text extraction (with
`pdfplumber`/`PyMuPDF`/`unstructured` considered and rejected); a new
`compass_client.summarize_content` function (same shape as
`classify_email`/`classify_task`); the summarization capability registered
as a new `summarize-file` Skill through the already-`Accepted` `ADR-015`
Skills extensibility path (this project's first real, non-stub Skill); the
Vault Filing Expert handoff needs zero changes; the new upload endpoint is
an additive sub-resource on `agents_router.py`, never a modification of
the existing `POST /agents/{agent_id}/chat` JSON contract; and image
support is explicitly deferred (see above). This ADR composes several
already-`Accepted` mechanisms but introduces one genuinely new dependency
(`pypdf`) and one genuinely new storage boundary (binary blob storage) —
enough to warrant a dedicated ADR rather than folding into an existing
one, mirroring `ADR-027`'s own precedent of one ADR bundling several
related decisions for a single story.

**Architecture scope:** §"File upload, Compass summarization & Vault
Filing Expert handoff" (`architecture.md`, under "In-App Agent
Orchestration (LangGraph) & Shared MCP Server") — the coder is bounded to:
`app/data_access/compass_client.py` (new `summarize_content`), a new
`app/data_access` upload-storage module (name left to the decomposer/
coder), `app/business/skill_tools.py` (new `summarize-file` catalog entry
+ handler), `app/business/skill_registry.py` (`_SKILL_HANDLERS` gains one
row), `app/business/vault_filing_expert.py` (call site only — read, not
modify, its own interface), `app/api/agents_router.py` (new additive
multipart sub-resource route), `requirements.txt` (`pypdf`),
`src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (Chat tab:
attach control + summarization/filing status indication),
`src/frontend/src/features/agents-map/agentsApiClient.ts` (new multipart
call). Full mechanism detail and every alternative considered:
[ADR-034](../Architecture/ADR.md).

**Gate: flagged — trigger-3 (ADR-034 created).** A `REVIEW-QUEUE.md`
pointer is filed. The decomposer still runs (per the pipeline's "flag, do
not halt" rule) so the human reviews the ADR and the resulting tasks
together in one pass.

---

## Decomposer pass (2026-08-13) — `/plan-tasks` step 2

**Gherkin tightened and locked, 10 ACs (`AC-01`..`AC-10`).** The original
9 scenarios were re-read against `ADR-034`'s narrowed real scope:
Scenario 1 now names the accepted-extension list explicitly and the
attach control's existence (structural, `AC-01`); Scenario 2 names the
real extraction/summarize mechanism; Scenario 3 names
`determine_placement_and_file`'s real signature; Scenario 6 names the
real, unmodified `POST /agents/{agent_id}/chat` contract. The original
Scenario 7 ("fails validation") assumed a single generic type/size
failure mode that no longer reads accurately once image types are
deferred — **split into two distinct scenarios**: new Scenario 7/`AC-07`
(an unsupported file type, e.g. an image, is honestly declined — mirrors
`REQ-SB-33`'s honest-decline posture, distinct in kind from a size-limit
rejection) and Scenario 8/`AC-08` (was Scenario 7 — exceeds the 20 MB
cap). Scenarios 8-9 (Compass/Vault-Filing-Expert honest failures) are
renumbered 9-10, otherwise unchanged in substance.

**A genuine finding beyond `ADR-034`'s own text, corrected here, not
silently patched:** `requirements.txt` has no `python-multipart`.
FastAPI's `File`/`Form` parameters (needed for the new multipart
endpoint `ADR-034` point 6 already decided) require it installed or the
endpoint fails at request time with an unhelpful runtime error —
`ADR-034`'s own dependency list named only `pypdf`. This is a routine
implementation necessity of an already-decided architectural choice
(the multipart endpoint itself), not a new architectural decision, so no
new ADR is warranted — `python-multipart` is added to
`REQ-SB-28-US-01-T01` alongside `pypdf`.

**`summarize-file` grant resolved as a task-level judgement call, not
left ambiguous:** `skill_registry.py`'s own documented design is
"explicit-grant-only, deliberately no self-healing default assignment"
(`REQ-SB-27-US-01`) — but this story's own Acceptance text requires
upload-and-summarize to work for "any agent" reachable through the chat
panel, with no scenario describing a "this agent lacks skill access"
refusal path. Rather than leave every agent unable to summarize until a
human manually grants each one via the existing `skills_router.py`,
`REQ-SB-28-US-01-T04`'s endpoint calls `grant_skill_access(agent_id,
"summarize-file")` unconditionally before `invoke_skill` (idempotent,
mirrors `grant_skill_access`'s own no-op-if-already-granted shape) —
`summarize-file` is this mechanism's own mandatory default capability,
not an optional user-configurable skill like `web-research`. Recorded
here explicitly as a task-scoped judgement call, not a MUST-FLAG trigger
(single defensible reading, does not change task breakdown).

**Dependency composition, cited directly (Done work, no task
`depends_on` edge needed):** the `summarize-file` Skill is registered
through the identical catalog/dispatch/grant shape
`REQ-SB-27-US-01-T02`/`T03` already built (`skill_tools.SKILLS`,
`skill_registry._SKILL_HANDLERS`), both **Done** — no new mechanism.
`REQ-SB-39-US-01` (`Draft`) is unrelated (Actions-migration scope only,
per the story's own Context) and is not a dependency.
`REQ-SB-35-US-01` (Vault Filing Expert) is **Done**, its interface
confirmed to need zero changes (architect pass, above) — cited in
`REQ-SB-28-US-01-T04`'s own Context, no task dependency required.

**Structural AC for the frontend affordance:** since `/design` was
skipped for this batch, `AC-01`'s attach-control requirement is locked
at the DOM-structural level only (an attach/file-input control renders
in the chat input row) — no pixel/visual-polish AC is locked, per the
structural-ACs-for-screens rule; visual polish is a non-blocking
out-of-band spot-check once a real design pass covers this surface.

**Tasks created (flat root, all `status: Ready`):**
`REQ-SB-28-US-01-T01` (`requirements.txt` + `upload_storage.py` +
`.second-brain/uploads/`), `REQ-SB-28-US-01-T02`
(`compass_client.summarize_content`), `REQ-SB-28-US-01-T03`
(`summarize-file` Skill registration, `depends_on: [T02]`),
`REQ-SB-28-US-01-T04` (new multipart endpoint composing storage → skill
→ Vault Filing Expert, `depends_on: [T01, T03]`), `REQ-SB-28-US-01-T05`
(frontend attach affordance + honest-rejection UI,
`depends_on: [T04]`). Acyclic — a straight line, T01/T02 parallel-buildable
at the root.

**Status: `Draft → Ready`.** All 10 ACs locked; every locked AC has at
least one AC-tagged manual verification step across the 5 tasks;
`depends_on` is acyclic. Every task's `status:` set to `Ready` in
lockstep, per the mandatory rule.

---

## Coder pass (2026-08-14) — `/implement-sprint SPRINT-038`

All 5 tasks (`T01`-`T05`) built and verified live, in dependency order,
against real files/real Compass/real Vault Filing Expert calls — full
detail in each task's own Implementation Log. All 10 locked ACs
verified:

- `AC-01`/`AC-02` — a real `.txt` attach → real extraction → a real
  Compass summary genuinely reflecting the file's content, confirmed by
  eye, twice (backend-layer `curl` call and a real CDP-driven browser
  session).
- `AC-03`/`AC-04` — a real, hand-built `.pdf` about a genuinely new
  customer ("Northwind Logistics", confirmed absent from the real
  vault beforehand) → filed with real tags/frontmatter/a real
  `[[wikilink]]` to a freshly-created hub note — the same shape any
  other Vault-Filing-Expert-filed note carries.
- `AC-05` — the temporary upload confirmed deleted on every reachable
  path (success, extraction failure, summarization failure, filing
  failure), never orphaned; the vault note itself never carries raw
  binary content.
- `AC-06` — the existing `POST /agents/{agent_id}/chat` confirmed
  byte-for-byte unmodified (direct re-read) and behaviorally identical
  live (same message, same real historical response).
- `AC-07`/`AC-08` — the two honest-rejection paths (unsupported type,
  size limit) both confirmed with zero storage/Compass/Vault-Filing-
  Expert calls made, distinct wording, and (frontend) rendered as
  error-styled bubbles.
- `AC-09`/`AC-10` — a real induced Compass failure and a real induced
  Vault-Filing-Expert-unavailable outcome both confirmed honest,
  specific, and non-fabricating; `AC-10`'s real summary text confirmed
  preserved and shown, never silently discarded.

Two scope-internal judgement calls (`T05` only, frontend attach-state
reset on agent switch; a file-only send guard loosening) logged in
`T05`'s own Implementation Log and `REVIEW-QUEUE.md` for human
spot-check — non-blocking, single-reading, does not weaken any locked
AC.

**Story status: `Ready → Done`.** `gate: flagged` carried forward
(human spot-check of `T05`'s two judgement calls; the decomposer's own
`ADR-034` trigger-3 flag is resolved by this build having shipped
exactly per that ADR, with zero deviation).

**Gate: stays `flagged` — trigger-3 (`ADR-034`) is a carry-forward, not
re-triggered by this pass.** Per this role's own governing rule ("If the
architect flagged the story this run for an ADR change, leave it `gate:
flagged`"), the flag set by the architect's pass above is left exactly as
set — the human reviews `ADR-034` and this pass's resulting tasks
together in one sitting, per the existing `REVIEW-QUEUE.md` entry for
this story. No new MUST-FLAG trigger fired in this pass beyond that
carried-forward one: no new material assumption of consequence (the
`python-multipart`/grant judgement calls above are routine,
single-reading implementation necessities, not gaps filled by guessing);
no unfinalised requirement; no new `ESCALATIONS.md` entry; not oversized
(5 tasks, straight dependency chain, mirrors `SPRINT-023`'s "compose
already-proven mechanisms" precedent); every locked AC has an observable,
verifiable outcome; no contradictory inputs; no genuinely unclear
breakdown (the two judgement calls above each had one defensible
reading, recorded, not guessed past silently).
