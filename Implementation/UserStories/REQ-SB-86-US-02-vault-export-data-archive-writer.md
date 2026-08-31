---
id: REQ-SB-86-US-02
title: "Export — automatic embedded-attachment inclusion, flat/hierarchy extraction, single `.sbd` archive"
requirement_ids: [REQ-SB-86]
requirement_section: "REQ-SB-86: Vault Data Sharing — Export a Real Slice of the Vault (`.sbd`)"
phase: P2
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-016 created) — architect pass 2026-09-01, .sbd Vault Data Archive mechanism. Design-gate/flat-collision findings (was trigger-1 + trigger-8/net-new-design-needed) already resolved 2026-09-01 per REQ-SB-86-US-01's own reasoning; see below. Carried forward unresolved through T01/T02/T03's own build — human still owes ADR-016 its review pass; also see T02/T03's own additionally-flagged scope-internal findings, logged separately per REVIEW-QUEUE.md, not folded into this note."
sprint: "SPRINT-081"
created: 2026-09-01
updated: 2026-09-01
---

<!-- Coder pass (2026-09-01): REQ-SB-86-US-02-T03 (export-options screen)
built and verified Done — the last of this story's 3 tasks (T01/T02 were
already Done). All 6 locked ACs (AC-01..AC-06) now verified across the
three tasks' own Implementation Logs, real live positive results
throughout. status: Ready -> Done. gate stays flagged (ADR-016 human
review, carried forward as the architect set it) plus two additional,
separately-logged, non-blocking findings from T02/T03's own live
verification (see their Implementation Logs + REVIEW-QUEUE.md) -- none
weakening a locked AC. This closes REQ-SB-86 end-to-end (both US-01 and
US-02, all 5 tasks Done). -->

# REQ-SB-86-US-02 — Export — automatic embedded-attachment inclusion, flat/hierarchy extraction, single `.sbd` archive

## Story

**As a** Second Brain operator who has selected folders/files in Settings
→ Vault → Export Data (`REQ-SB-86-US-01`)
**I want** the system to automatically include any attachment my selected
`.md` files actually embed, let me choose flat or hierarchy-preserving
extraction, and then produce one real `.sbd` file
**So that** I can hand a real, correctly-rendering slice of my own vault
data (a Customer's own notes, an Industry KB) to someone else in one
file, exactly as I chose to share it — nothing more, nothing silently
dropped

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-86* — "Any attachment a selected
  `.md` file actually embeds (an image, an SVG, a PDF) is **included
  automatically** — the export is meant to render correctly at the
  destination, the same way the vault's own `_assets` folders already
  work; this is not a markdown-only export by default. At export time,
  the operator chooses **flat** (every selected file lands in one folder,
  no nesting) or **hierarchy-preserving** (the original folder structure
  travels with it) extraction."
- **Second substory of `REQ-SB-86`'s own 2-way split** (picker/export —
  see `REQ-SB-86-US-01`'s own Context for the full split rationale). This
  story owns everything that happens once the operator requests an export
  of a selection made there.
- **PRD breadcrumb (2026-08-31, operator, verbatim):** "we can have an
  option of flat Extraction of maintain Heratichy." Attachment-handling
  resolved via a direct follow-up question, not assumed: referenced
  attachments are included automatically, not markdown-only and not a
  per-export toggle ("Yes, include automatically").
- **Deliberately does NOT reuse `REQ-SB-85`'s own dependency-closure/
  secret-scan machinery** — that machinery exists specifically because a
  capability bundle can implicitly depend on other capabilities and can
  carry secret-shaped credentials embedded in Skill/Agent code. Real
  vault data selected here has neither concept the same way: the operator
  is explicitly, deliberately choosing to share this exact content — the
  hard capability/data boundary `REQ-SB-85`'s own PRD text already draws
  ("this system moves *capability*, never *personal or business data*...
  Sharing actual vault *data*... is a deliberately separate, later
  capability (see REQ-SB-86)"). No secret-scan pass applies to this
  story.
- **Attachment mechanism, grounded directly against real code, not
  assumed:** real attachments (images, PDFs, etc.) already land under a
  note's own `<subfolder>/attachments/<note-slug>/<message-slug>/
  <filename>` or `<subfolder>/files/<slug>/<original-filename>`
  convention (`app/obsidian/attachments.py`, `write_attachments`/
  `write_file_companion`, both already real/`Done`) and/or under
  `_`-prefixed folders like `_assets` (the operator's own PRD text,
  confirmed against `list_all_note_paths()`'s own "hide `_`-prefixed
  folders from the ordinary note index" convention — read while speccing
  `REQ-SB-86-US-01`, this story's own sibling). **The exact detection
  mechanism for "which attachment(s) does THIS selected `.md` file's
  content actually embed" (a wikilink-embed scan `![[...]]`, a
  markdown-image-link scan `![...](...)`, or both) is left open,
  deliberately, to `/plan-tasks`** — same established precedent as
  `REQ-SB-85-US-02` leaving its own Skill→Template coupling-detection
  heuristic open. The Gherkin below asserts only the externally
  observable outcome (a genuinely embedded attachment is included
  automatically, with no prompt), not the detection algorithm.
- **Flat-extraction filename-collision risk — a real, disclosed finding,
  not addressed by the operator's own words:** surfaced by grounding
  against the real, already-`Done` OKF directory shape (`REQ-SB-54`):
  every Customer/Project directory shares the exact same 4 filenames
  (`index.md`/`log.md`/`captures.md`/`<slug>.md`) by convention.
  Selecting two or more such folders (a genuinely plausible real use case
  — "share my customer data" for more than one Customer at once) and
  choosing flat extraction will produce real filename collisions. Per
  this project's own standing "archive, never silently lose data"
  posture (`MEMORY.md`) and `Implementation/Learnings.md`'s own
  2026-08-10 entry ("assuming a natural key is unique... always include a
  genuinely unique identifier in any generated filename/key, even when a
  collision seems unlikely"), a disclosed, non-locked scope-internal
  default is proposed here for `/plan-tasks`: a flat-extraction naming
  collision is disambiguated by prefixing the file with its own original
  parent-folder name (e.g. `masdar_index.md`, `acme_index.md`), never a
  silent overwrite. Not locked — `/plan-tasks`/`/design` may choose a
  different disambiguation scheme without needing a re-spec, since
  Scenario 3 below asserts only that a flat-extraction collision is never
  silently dropped/overwritten, not this exact naming scheme.
- **Archive internal layout** (a manifest like `.sbf`'s own `ADR-013`, vs.
  a plain flat zip) is likewise left as an implementation detail for
  `/plan-tasks` — the PRD's own text only requires "you zip the folder,"
  not a specific internal shape, and no import round-trip needs a
  manifest to parse (import is out of scope, see Non-Goals).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns
them at /plan-tasks. -->

### Scenario 1: Hierarchy-preserving extraction keeps the original folder structure

```gherkin
Given the operator has a real selection from Settings → Vault → Export
    Data
When the operator exports choosing "hierarchy-preserving" extraction
Then the resulting .sbd file (a real zip archive) contains the selected
    files under the same relative folder structure they have in the real
    vault
```
<!-- AC-ID: REQ-SB-86-US-02-AC-01 -->

### Scenario 2: Flat extraction lands every selected file in one folder

```gherkin
Given the operator has a real selection from Settings → Vault → Export
    Data
When the operator exports choosing "flat" extraction
Then every selected file lands directly in the archive with no nested
    folder structure
```
<!-- AC-ID: REQ-SB-86-US-02-AC-02 -->

### Scenario 3: A flat-extraction filename collision is never silently overwritten

```gherkin
Given the operator's selection includes two or more files that would
    share the same filename once flattened (e.g. two different Customer
    folders each containing their own index.md)
When the operator exports choosing "flat" extraction
Then both files are included in the resulting archive, each disambiguated
    by prefixing its own original immediate parent-folder name onto its
    filename (e.g. index.md from the "masdar" folder becomes
    masdar_index.md, index.md from the "acme" folder becomes
    acme_index.md) — each still genuinely readable/distinguishable, never
    one silently overwriting or dropping the other
```
<!-- AC-ID: REQ-SB-86-US-02-AC-03 -->

### Scenario 4: A selected `.md` file's own embedded attachments are included automatically

```gherkin
Given a selected .md file's own content genuinely embeds an attachment
    (an image, an SVG, or a PDF) that physically exists in the vault
When the export is produced
Then that attachment is included in the resulting .sbd archive
    automatically
  And the operator is never prompted about whether to include it — this
    is not a per-export toggle
```
<!-- AC-ID: REQ-SB-86-US-02-AC-04 -->

### Scenario 5: A selection with no embedded attachments exports cleanly

```gherkin
Given none of the operator's selected .md files embed any attachment
When the export is produced
Then the resulting .sbd file contains exactly the selected files (per the
    chosen flat/hierarchy extraction) and nothing else
```
<!-- AC-ID: REQ-SB-86-US-02-AC-05 -->

### Scenario 6: The export contains exactly the operator's own real chosen content

```gherkin
Given the operator selects a real slice of the vault (e.g. a whole
    Customer folder, or an Industry KB folder)
When the export is produced
Then the resulting .sbd file is a single real zip archive
  And it contains exactly the selected files/folders (plus any
    automatically-resolved embedded attachments) — nothing outside the
    operator's own selection is ever included
```
<!-- AC-ID: REQ-SB-86-US-02-AC-06 -->

## Affected Screens

- New export-options screen (choose flat/hierarchy extraction, confirm,
  download), reached after the operator requests an export from Settings
  → Vault → Export Data (`REQ-SB-86-US-01`) — **`net-new-design-needed`**,
  no prototype coverage anywhere.
- `html-prototype/` — confirmed (via direct inspection of `index.html`'s
  own full screen catalog before writing this story) to have no
  equivalent flow anywhere.

## Dependencies

- **Blocked by:** `REQ-SB-86-US-01` (folder/file picker) — this story's
  own entry point is a selection made there.
- **Related to, not blocking:** `REQ-SB-85-US-02` (Export — `.sbf`) —
  sibling export mechanism over a structurally different kind of content
  (capability, not data); deliberately does not reuse `REQ-SB-85`'s own
  dependency-closure/secret-scan modules (see Context/Constraints).
- **External:** none new.

## Constraints

- **Never a capability/dependency-closure resolution and never a
  secret-scan pass** — this system moves real, already-trusted vault data
  the operator is deliberately choosing to share, the mirror-image
  boundary of `REQ-SB-85`'s own "capability, never data" rule (see
  Context).
- A flat-extraction filename collision is never resolved by silently
  overwriting or dropping a file (Scenario 3) — some disambiguation
  always happens; the exact naming scheme is left open to `/plan-tasks`
  (see Context).
- Any attachment a selected `.md` file's content genuinely embeds is
  always included automatically — never a per-export prompt or toggle
  (Scenario 4), per the operator's own explicit "Yes, include
  automatically" confirmation.
- The export never includes anything outside the operator's own selection
  except an embedded attachment's own resolved file (Scenario 6) — no
  silent scope creep.
- Import of a `.sbd` file is out of scope for this story and for
  `REQ-SB-86` entirely (see Non-Goals).

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-86-US-02-T01 | backend | Embedded-attachment resolver — scans a selected `.md` file's own content for a genuinely-embedded, on-disk attachment and adds it to the export set | `app/business/` (new module, exact location per `/plan-tasks`) | `../Tasks/REQ-SB-86-US-02-T01-attachment-resolver.md` |
| REQ-SB-86-US-02-T02 | backend | `.sbd` archive writer — flat/hierarchy-preserving extraction, flat-collision disambiguation, composes the resolved selection (including resolved attachments) into one real zip; `POST /vault/export-data/export` endpoint | `app/api/vault_router.py`, `app/business/` (new module) | `../Tasks/REQ-SB-86-US-02-T02-sbd-archive-writer.md` |
| REQ-SB-86-US-02-T03 | frontend | Export-options screen (flat/hierarchy choice, confirm, download), wired from the Export action on `SettingsVaultExportDataPage.tsx` | `src/frontend/src/pages/SettingsVaultExportDataPage.tsx`, `src/frontend/src/features/settings/vaultApiClient.ts` | `../Tasks/REQ-SB-86-US-02-T03-export-flow-ui.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Import of a `.sbd` file** — explicitly deferred by the operator ("we
  will get to it later"); confirmed against the PRD's own current
  `REQ-SB-86` entry, which is export-only. A future import requirement
  will need its own `/spec` pass.
- **Any dependency-closure resolution or secret-shaped-string scanning**
  — deliberately not reused from `REQ-SB-85` (see Constraints).
- **Editing a note's own content as part of exporting it** — export is
  read-only over each selected file's current real state.
- **Scheduling/automating an export** — always an explicit, one-off
  operator action.
- **Any artifact/capability kind** (Skill/Template/Agent/Pipeline) —
  that is `REQ-SB-85`'s own, separate, `.sbf` mechanism.

## Notes

**Prototype parity:**

- Export-options screen (flat/hierarchy choice, confirm, download) —
  **`net-new-design-needed`** (Scenarios 1, 2) — no prototype coverage
  anywhere.
- Flat-collision-safe naming and attachment auto-inclusion (Scenarios 3,
  4, 5, 6) — no distinct new visual region beyond the export-options
  screen above; expected to compose from already-approved primitives (a
  plain "Export complete, download `.sbd`" confirmation, matching
  `REQ-SB-85-US-02`'s own established shape for its equivalent step).

**Why `gate: flagged`:**

1. No material assumption fills a genuine PRD gap in the Gherkin itself.
   One disclosed, non-locked scope-internal judgement call was made (the
   flat-extraction collision disambiguation scheme) — a real, foreseeable
   gap the operator's own words never addressed, surfaced by grounding
   against the real OKF directory shape (`REQ-SB-54`), not guessed
   around; not treated as blocking since the PRD's own controlling intent
   (never silently lose/overwrite selected data) is fully honored
   regardless of the exact naming scheme chosen.
2. `REQ-SB-86` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A directly (architect/ADR trigger) — but `/plan-tasks` should expect
   the new attachment-resolver and `.sbd` archive-writer modules to be
   real, ADR-worthy additions (first-ever Second-Brain-side vault-data
   export mechanism, distinct from `REQ-SB-85`'s `.sbf`/`ADR-013`) —
   flagged as a likely trigger for the architect step, not resolved here.
4. No `ESCALATIONS.md` entry written by this pass.
5. Not oversized — 3 tasks (attachment resolver, archive writer +
   endpoint, frontend), meaningfully smaller than `REQ-SB-85-US-02`'s own
   5-task Export story since no dependency-closure resolution and no
   secret-scan pass apply here.
6. N/A (coder trigger).
7. No contradictory PRD inputs.
8. **The controlling flag: `net-new-design-needed`** — the export-options
   screen has no prototype coverage anywhere. As with `REQ-SB-86-US-01`,
   whether the operator's same-day "build functional-first, design after"
   override for `REQ-SB-85` also extends to this sibling requirement is
   NOT assumed here — it is flagged for a human decision (either run
   `/design REQ-SB-86`, or explicitly extend the same override).

gate: flagged 2026-09-01 — trigger-1 (disclosed, non-blocking
flat-collision judgement call) and trigger-8/net-new-design-needed
(export-options screen, zero prototype coverage). See `REVIEW-QUEUE.md`.

**Resolved 2026-09-01 (orchestrator, on the operator's standing
authorization):** design-gate extended from `REQ-SB-85`'s same-day
override, same reasoning as `REQ-SB-86-US-01`'s own resolution note.
The disclosed flat-collision disambiguation default (prefix the file
with its own original parent-folder name, e.g. `masdar_index.md`) is
accepted as proposed — it directly honors this project's own
`MEMORY.md` "archive, never silently lose data" posture and
`Implementation/Learnings.md`'s 2026-08-10 unique-key entry; the
decomposer may lock this scheme into Scenario 3's AC directly rather
than re-flagging it. `gate` set to `clear`; this analysis is preserved,
not deleted.

**Architect pass (2026-09-01) — ADR-016 created, verified not assumed:**
This story's own Notes point 3 flagged the attachment-resolver + `.sbd`
archive-writer as "likely ADR-worthy" but did not decide it — the architect
pass decided for real, against `architecture.md`/`ADR.md`/the real code
(`vault_manager.py`, `vault_router.py`, `app/obsidian/attachments.py`,
`app/obsidian/frontmatter.py::read_note`), not by accepting the story's own
flag at face value. **A new ADR was warranted and is now Accepted:**
`ADR-016` (`.sbd` Vault Data Archive). Grounds: this is the first-ever
Second-Brain-side vault-DATA export mechanism (`ADR-013` only ever covered
capability bundles); it introduces a new archive format with a real,
non-obvious internal-layout decision (no `manifest.json`, deliberately
diverging from `.sbf`'s own manifest-carrying shape, since no import reader
exists to design for); it introduces a new attachment-detection heuristic
(dual wikilink-embed/markdown-image-link scan) comparable in kind to
`ADR-013`'s own Skill→Template heuristic, which that ADR also formally
recorded; and it explicitly, formally establishes the posture divergence
from `ADR-013` (no dependency-closure resolution, no secret-scan gate) so a
future architect/coder can never accidentally assume `.sbf`'s machinery
applies here. Module placement itself (`app/business/logic/`, composing the
already-Accepted `VaultManager` gateway, never a new Manager) is NOT the
novel part — it's a direct reuse of `ADR-013`'s own already-established
composition-module convention — but is still recorded in `ADR-016` for
continuity, per this project's own precedent of recording placement
alongside format/heuristic decisions in the same ADR. See `ADR-016` in
`Implementation/Architecture/ADR.md` for the full Context/Decision/
Alternatives/Consequences. `architecture.md` gained a new §Embedded-
Attachment Resolution & `.sbd` Archive Writer section recording this.

**Architecture scope:** §Vault Data Export → §Embedded-Attachment
Resolution & `.sbd` Archive Writer (`architecture.md`, `ADR-016`) — bounds
the coder to: two new `business/logic/` modules
(`vault_attachment_resolver.py`, `sbd_archive.py`), one new `POST
/vault/export-data/export` route on the existing `app/api/vault_router.py`,
and the new export-options frontend screen wired from
`SettingsVaultExportDataPage.tsx`. No dependency-closure/secret-scan module
from `REQ-SB-85`/`ADR-013` is in scope — explicitly excluded by `ADR-016`.

gate: flagged 2026-09-01 — trigger-3 (`ADR-016` created/changed). Does not
halt `/plan-tasks` — the decomposer still runs; see `REVIEW-QUEUE.md`.

**Decomposer pass (2026-09-01):** Locked all 6 Gherkin scenarios as
`REQ-SB-86-US-02-AC-01`..`AC-06` (tags appended after each closing fence
above). Scenario 3's own Then-clause was tightened (not just tagged) to
lock the disclosed flat-collision disambiguation scheme directly — prefix
the archive member name with its own original immediate parent-folder
name (e.g. `masdar_index.md`, `acme_index.md`) — per this story's own
Notes, which explicitly authorized the decomposer to do this directly
rather than re-flagging it. Created `REQ-SB-86-US-02-T01` (attachment
resolver, `depends_on: []` — operates on a plain list of already-selected
`.md` file paths, no runtime call to `US-01`'s own endpoint), `T02`
(`.sbd` archive writer + `POST /vault/export-data/export`,
`depends_on: [T01]` — composes the resolver), `T03` (export-options
frontend screen, `depends_on: [T02, REQ-SB-86-US-01-T02]` — needs both the
real endpoint and `US-01`'s own page to wire the Export action onto, per
this story's own Affected Screens). **Cross-story dependency call:** `T01`
and `T02` are deliberately given NO `depends_on` edge onto `US-01-T01`
(the tree-listing endpoint) — the real data flow this story describes is
"the operator's selection, however it was built, is handed to the export
flow"; `T01`'s resolver and `T02`'s archive writer are both specified
against a plain `selection: list[str]` of real vault-relative paths as
their input contract, independently buildable and testable against any
real selection (hand-constructed for verification) without needing
`US-01`'s own tree endpoint to exist or run. Only `T03` (the frontend
screen) has a genuine file-level dependency on `US-01`'s own page, since
it wires the Export trigger directly onto `SettingsVaultExportDataPage.tsx`.
Every locked AC has at least one AC-tagged verification step across the
three tasks (`AC-01`/`AC-02` also get a UI-observable echo on `T03`,
mirroring `REQ-SB-85-US-02-T05`'s own established pattern of re-verifying
a backend-owned AC's outcome at the UI layer too). No cycles. `status`
advanced `Draft → Ready`; all three tasks written at `status: Ready` in
lockstep. **`gate` is left exactly as the architect set it —
`flagged`/`ADR-016` human review — not cleared here**; this is not the
decomposer's call to resolve. No new MUST-FLAG trigger fired at this
decomposer step itself beyond the already-recorded `ADR-016` one (no new
assumption beyond the story's own already-resolved flat-collision
default, no new `ESCALATIONS.md` entry, not oversized — 3 tasks matching
the pre-sketched table, every locked AC verifiable via a real observable
outcome, no contradictory inputs).
