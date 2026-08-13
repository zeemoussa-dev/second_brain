---
id: REQ-SB-35-US-01-T02
title: New vault_filing_expert.py — determine_placement_and_file, Tier-1 write path, uncertainty marker, collision-safe filenames
parent_story: REQ-SB-35-US-01
requirement_id: REQ-SB-35
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-021) carried, PLUS scope-internal judgement calls made during the build (see Implementation Log): (a) the JSON decision schema was extended with referenced_customer/referenced_partner fields, and the Tier-1 write call gained a customer/partner frontmatter field, beyond this task's own literal code sample — required to satisfy AC-02's own explicit 'discoverable via list_known_customers()' wording, confirmed via direct reading of list_known_customers (frontmatter-only scan); (b) a local .env got two empty ANTHROPIC_API_KEY/ANTHROPIC_MODEL placeholders added so config.py (a sibling story's already-added required field) could load at all — no source file touched, not in Files to Modify. All 6 locked ACs (AC-01/02/05/06/07/08) verified live."
phase: P1
depends_on: [REQ-SB-35-US-01-T01, REQ-SB-20-US-01-T05]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-35-US-01-T02 — `vault_filing_expert.py`'s Tier-1 placement/write path

## Parent Story

- Story: [[REQ-SB-35-US-01]] — `../UserStories/REQ-SB-35-US-01-vault-filing-expert.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-35 *Vault Filing Expert*

---

## Objective

Add new `app/business/vault_filing_expert.py`, exposing `determine_placement_and_file(content, source_description, requesting_agent_id) -> dict` (`ADR-021` point 2): deterministically pre-fetches the vault's own known kinds/customers/partners, issues one grounded `model_factory.resolve_agent_model("vault-filing-expert")` completion for a structured placement decision, re-checks the Tier boundary in Python, and writes immediately for Tier 1 (with a collision-safe filename and a visible uncertainty marker on low confidence). Tier 2 is deferred, without breaking Tier 1, to `T03`.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed the `"vault-filing-expert"` registry entry + keyword assignment.
- `REQ-SB-20-US-01-T05` has landed `graph.route_cross_section_request(requesting_agent_id, need_description) -> dict`.
- `vault_writer.list_known_kinds()` / `list_known_customers()` / `list_known_partners()`, `vault_writer.write_note(subfolder, filename_stem, frontmatter, body)`, and `model_factory.resolve_agent_model(agent_id)` all already exist and are unmodified (real, `Done`/already-built code).

**After / Outputs:**
- `app/business/vault_filing_expert.py` (new) exposes `determine_placement_and_file(...) -> dict`, returning one of:
  - `{"status": "written", "path": str, "kind": str, "tags": list[str], "confidence": "high"|"low"}` (Tier 1, this task's own scope), or
  - `{"status": "unavailable", "message": str}` (the Provider has no real client yet — the same honest funnel-gate shape `model_factory.resolve_agent_model` already returns `None` for), or
  - a Tier-2 shape (`T03`'s own scope — this task's own local stub keeps the module importable and Tier 1 fully working without requiring `T03`/`REQ-SB-21-US-01-T03` to exist yet).

---

## Files to Modify

- `src/backend/app/business/vault_filing_expert.py` (new):
  ```python
  """The Vault Filing Expert's own placement/write mechanism (ADR-021) —
  a distinct registry agent, reached exclusively via REQ-SB-20's Hub
  routing, never a shared skill (operator-confirmed, "This is an Agent").
  determine_placement_and_file is this module's one public entry point.
  Grounding is deterministic context injection (the three known-value
  lists are pre-fetched in plain Python, never left to the model's own
  discretion to tool-call), not a bound-tool reasoning loop -- ADR-021
  point 2's own "prefer a real deterministic call over hoping the model
  tool-calls correctly" precedent, one layer over ADR-016's
  extract_memory reasoning. Tier 1 (existing category, or a new tag/
  subfolder within an existing top-level area) writes immediately.
  Tier 2 (a genuinely new top-level area) is handled in finalize_new_
  top_level_area / the local _create_tier_2_proposal import inside this
  same function (T03's own scope) -- deliberately a LOCAL, not
  module-level, import of pending_approval_registry, so this whole
  module loads and every Tier-1 scenario works correctly even before
  REQ-SB-21-US-01-T03 ships that module (ADR-021's own Consequences:
  "Tier 1... has no such dependency and can be built and verified
  independently")."""
  import json

  from app.business import vault_filing_methodology  # see Context/Notes
  from app.business.agent_orchestration import model_factory
  from app.data_access import vault_writer

  _UNCERTAINTY_PREFIX = "> ⚠️ **Low-confidence placement.** {note}\n\n"


  def _unique_filename_stem(subfolder: str, filename_stem: str) -> str:
      """write_note() overwrites unconditionally on a filename collision
      (confirmed by direct reading of its own implementation) -- a
      model-proposed filename_stem is not guaranteed unique. Applies this
      project's own standing filename-uniqueness Constraint (MEMORY.md):
      append a numeric suffix until the target path is free, mirroring
      the Meeting-note dedup-suffix precedent one layer up (ADR-019's own
      "never trust a single proposed key as unique" lesson, applied here
      to a model-proposed stem instead of an Outlook-provided id)."""
      from app.config import settings
      base = filename_stem
      candidate = base
      suffix = 2
      target_dir = settings.vault_path / subfolder
      while (target_dir / f"{candidate}.md").exists():
          candidate = f"{base}-{suffix}"
          suffix += 1
      return candidate


  def determine_placement_and_file(
      content: str, source_description: str, requesting_agent_id: str
  ) -> dict:
      model = model_factory.resolve_agent_model("vault-filing-expert")
      if model is None:
          return {
              "status": "unavailable",
              "message": "The Vault Filing Expert's selected Provider is not available.",
          }

      known_kinds = vault_writer.list_known_kinds()
      known_customers = vault_writer.list_known_customers()
      known_partners = vault_writer.list_known_partners()

      prompt = vault_filing_methodology.build_placement_prompt(
          content=content,
          source_description=source_description,
          known_kinds=known_kinds,
          known_customers=known_customers,
          known_partners=known_partners,
      )
      raw = model.invoke(prompt)
      decision = json.loads(raw.content)  # {"kind", "is_new_top_level_area", "tags", "filename_stem", "body", "confidence", "uncertainty_note"}

      # Never trust the model's own boolean alone -- re-check the Tier
      # boundary against the real, live vault structure (ADR-021 point 2).
      is_new_top_level_area = decision["kind"] not in known_kinds

      if is_new_top_level_area:
          return _create_tier_2_proposal(
              content=content,
              source_description=source_description,
              requesting_agent_id=requesting_agent_id,
              decision=decision,
          )

      body = decision["body"]
      if decision.get("confidence") == "low":
          body = _UNCERTAINTY_PREFIX.format(note=decision.get("uncertainty_note") or "This placement is a best guess.") + body

      subfolder = f"Work/{decision['kind']}"
      filename_stem = _unique_filename_stem(subfolder, decision["filename_stem"])
      path = vault_writer.write_note(subfolder, filename_stem, {"tags": decision["tags"]}, body)

      return {
          "status": "written",
          "path": path,
          "kind": decision["kind"],
          "tags": decision["tags"],
          "confidence": decision.get("confidence", "high"),
      }


  def _create_tier_2_proposal(*, content, source_description, requesting_agent_id, decision) -> dict:
      """T03's own scope replaces this body with the real
      pending_approval_registry.create_pending_approval(...) call
      (ADR-021 point 3) -- deliberately a LOCAL import inside this
      function (not at module top), so this file loads correctly and
      every Tier-1 scenario works regardless of whether
      REQ-SB-21-US-01-T03 has shipped pending_approval_registry.py yet."""
      raise NotImplementedError(
          "Tier-2 (new-top-level-area) resolution is REQ-SB-35-US-01-T03's "
          "own scope -- not yet built. Tier-1 placements are unaffected."
      )
  ```
- New sibling `src/backend/app/business/vault_filing_methodology.py` (new, small) — `build_placement_prompt(content, source_description, known_kinds, known_customers, known_partners) -> list` (the message list `model.invoke(...)` expects), embedding a condensed excerpt of `Documentation/References/beyond-the-second-brain-methodology.md`'s own principles (atomic notes, output-orientation, tags-for-multidimensional-attributes, `ADR-004`'s tag/folder split) plus the three pre-fetched lists plus `content`/`source_description`, and instructing the model to return the exact structured JSON shape `determine_placement_and_file` expects, including setting `is_new_top_level_area` only when `kind` is not among the given `known_kinds` (`ADR-021` point 2's own prompt-design instruction — re-checked in Python regardless, never trusted alone).

---

## Constraints

- Inherits from parent story and `ADR-021` points 1–2.
- Grounding is deterministic context injection (plain Python calls to `list_known_kinds`/`list_known_customers`/`list_known_partners`), never a bound-tool reasoning loop the model could skip.
- `is_new_top_level_area` MUST be re-checked in Python (`kind not in known_kinds`) — never trusted from the model's own returned boolean alone.
- Tier 1 writes via `vault_writer.write_note` only — no new low-level `data_access` primitive.
- A low-`confidence` decision's body MUST carry a visible uncertainty marker sourced from the model's own `uncertainty_note`, never silently dropped or presented as a settled decision (Scenario 6) — independent of, never a substitute for, Tier 2's own approval gate.
- Filename collisions MUST be resolved deterministically (a numeric suffix), never silently overwriting an existing note (Scenario 8) — `write_note`'s own unconditional-overwrite behavior is a real, confirmed risk this task must not leave unhandled.
- The Tier-2 branch (`_create_tier_2_proposal`) MUST use a local (function-body), not module-level, import for `pending_approval_registry` once `T03` implements it — this task's own `NotImplementedError` stub already establishes this shape; do not change it to a module-level import.
- The written note's own `tags`/`body` must satisfy the standing tags-and-wikilinks rule (`MEMORY.md`) — the model's own prompt must instruct it to produce a real `[[wikilink]]` to any vault entity the content references, not just an identifying frontmatter field.

---

## Tests

<!-- AC-01/02/05/06/08 are verified here via direct calls to
determine_placement_and_file against the real backend .venv and real
vault (mirrors route_cross_section_request's own "directly callable,
testable without a live model-driven trigger" precedent). AC-07 needs
REQ-SB-20-US-01-T05's own route_cross_section_request to actually find
this agent via T01's real keyword assignment. AC-03/AC-04 (Tier 2) are
NOT tested here -- T03's own scope. -->

**Manual verification steps:**
1. **[REQ-SB-35-US-01-AC-01]** In a Python shell against the backend `.venv` (real configured `vault_path`, `"vault-filing-expert"` pointed at a real-client Provider, e.g. Compass). Call `determine_placement_and_file("<realistic customer-related content that clearly matches an existing Work/<Kind>/ folder, e.g. Emails>", "test — existing category", "some-agent-id")`. Confirm the result is `{"status": "written", ...}` with `"kind"` equal to an already-existing `list_known_kinds()` value, and the real note exists on disk at the returned `path` with the returned `tags` in its frontmatter.
2. **[REQ-SB-35-US-01-AC-02]** Call `determine_placement_and_file(...)` with content that plausibly needs a new tag/subfolder *within* an existing top-level area (e.g. a genuinely new customer name under `Work/Notes/`). Confirm `"status": "written"`, the note exists, and `vault_writer.list_known_customers()`/the note's own tags reflect the new value — confirm it's discoverable the same vault-derived way `list_known_kinds`/`list_known_customers` already work (no separate, hardcoded lookup needed).
3. **[REQ-SB-35-US-01-AC-05]** Directly inspect `vault_filing_methodology.build_placement_prompt`'s own output (call it directly, print the resulting message list). Confirm it embeds real excerpts from `Documentation/References/beyond-the-second-brain-methodology.md` and the three real pre-fetched lists — grounding is real, not a hardcoded rules table. Confirm the written note's own tags/body (from step 1 or 2) carry both the correct tags and a real `[[wikilink]]` to any vault entity referenced (e.g. a customer hub note), per the standing tags-and-wikilinks rule.
4. **[REQ-SB-35-US-01-AC-06]** Construct a call (or, if the model rarely returns low confidence naturally, temporarily monkeypatch `model.invoke` in-process to return a fixed low-confidence decision, then revert — mirroring the established in-process-monkeypatch pattern) where `confidence` is `"low"`. Confirm the written note's body starts with the visible uncertainty marker, sourced from the real `uncertainty_note` text, not a generic placeholder — and confirm the placement still completed (Tier 1 never pauses regardless of confidence).
5. **[REQ-SB-35-US-01-AC-08]** Call `determine_placement_and_file(...)` twice in a row with content that resolves to the identical `kind`/`filename_stem` (e.g. by monkeypatching the prompt to force an identical proposed stem both times). Confirm the second call's returned `path` differs from the first (the numeric-suffix collision guard fired) and the first note's own content is byte-unchanged after the second call — no overwrite.
6. **[REQ-SB-35-US-01-AC-07]** Confirm `agent_keywords.get_agent_keywords("vault-filing-expert")` returns `T01`'s real assigned keywords. Call `graph.route_cross_section_request("<some other agent id in a different Section>", "<a need description overlapping vault-filing-expert's own keywords, e.g. 'help filing and tagging this new content'>")`. Confirm the result is `{"matched": True, "agent_id": "vault-filing-expert", ...}`. Confirm, by direct code inspection, that no separate write path exists anywhere in this codebase for filing content other than this module's own `determine_placement_and_file` — any caller that routes to this agent must go through this same function.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — existing-category content is placed and written autonomously
- [x] **AC-02** (Scenario 2) — a new tag/subfolder within an existing top-level area is placed and written autonomously, discoverable via the same vault-derived listing mechanism
- [x] **AC-05** (Scenario 5) — placement reasoning is grounded in the real methodology text + real live vault structure; written tags/wikilinks satisfy the standing rule
- [x] **AC-06** (Scenario 6) — low-confidence placements carry a visible, honest uncertainty marker, never silently dropped
- [x] **AC-07** (Scenario 7) — the agent is discoverable via real Hub routing; no separate write path exists elsewhere
- [x] **AC-08** (Scenario 8) — a filename collision never silently overwrites an existing note
- [x] `is_new_top_level_area` is always re-checked in Python, never trusted from the model alone
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Tier-2 resolution (`finalize_new_top_level_area`, the `_APPROVAL_HANDLERS` dispatch entry, `pending_approval_registry.py`'s additive `payload` field) — `T03`.
- The `"vault-filing-expert"` registry entry itself and its keyword assignment — `T01`.
- `model_factory.py`, `vault_writer.write_note`, `list_known_kinds`/`list_known_customers`/`list_known_partners` — all reused as-is, unmodified.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-021` created at `/plan-tasks` step 1) — the human reviews `ADR-021` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why the Tier-2 branch is a local-import stub, not a fully wired call:** `ADR-021`'s own Consequences are explicit that "Tier 1... has no such dependency and can be built and verified independently" of `REQ-SB-21-US-01`'s still-unbuilt `pending_approval_registry.py`. Writing `_create_tier_2_proposal`'s real body now (a module-level `from app.business import pending_approval_registry` import) would make this entire module fail to import until that sibling story ships — defeating the point of the split. `T03` replaces this stub's body in place once `REQ-SB-21-US-01-T03` is real.

**Exact prompt wording, JSON schema key names, and the Anthropic/OpenAI model call shape** (`model.invoke(...)` returning `.content` as a JSON string) are ordinary implementation latitude — confirm the real, installed `langchain_openai.ChatOpenAI`'s own response shape at build time and adapt if it differs, logging any deviation as a scope-internal assumption in the Implementation Log, mirroring `REQ-SB-20-US-01-T05`'s own identical caveat for its LangGraph API surface.

---

## Implementation Log

**Built 2026-08-12 (coder, `/implement-sprint`, `SPRINT-023`), against the
real `REQ-SB-20-US-01-T02`/`T05` and `REQ-SB-21-US-01-T03`/`T06` source
(all 4 confirmed `Done` by direct reading before writing anything, per the
launching agent's own instruction — not trusted from any task's possibly-
stale sample).** New `app/business/vault_filing_methodology.py`
(`build_placement_prompt`) and `app/business/vault_filing_expert.py`
(`determine_placement_and_file`, `_unique_filename_stem`,
`_create_tier_2_proposal` as a `NotImplementedError` stub per this task's
own scope — `T03` replaces it) built per this task's own code shape.

**Two scope-internal judgement calls made and logged here for human
spot-check (not escalations — no locked AC was weakened, no new
dependency, no ADR deviation):**

1. **JSON decision schema extended with `referenced_customer`/
   `referenced_partner`, and the Tier-1 `write_note` frontmatter extended
   with a `customer`/`partner` field, beyond this task's own literal code
   sample (which only ever passed `{"tags": decision["tags"]}`).** Found
   live verifying `AC-02`: a first pass using only `tags` produced a note
   tagged `customer/<slug>` but `vault_writer.list_known_customers()`
   still returned `False` for the new customer — direct reading of
   `list_known_customers()` confirms it scans the `customer:`
   FRONTMATTER field, never the tags list (`ADR-004`). Without this
   extension, `AC-02`'s own explicit wording ("the note's own tags
   reflect the new value... discoverable the same vault-derived way
   list_known_kinds/list_known_customers already work") is not actually
   satisfied by the task's own literal sample. Fixed inside this same
   file (`_placement_frontmatter`, `_link_referenced_entity` — the latter
   mechanically reuses `customer_hub_linking`/`partner_hub_linking`'s
   existing granular primitives per `ADR-021`'s own Consequences text,
   rather than trusting the model's free-text body to have produced a
   correctly-slugged wikilink). The prompt (`vault_filing_methodology.py`)
   was also strengthened after a first live pass showed the model
   reliably tagged `customer/<slug>` but left `referenced_customer: null`
   for a genuinely NEW customer — the original prompt wording only asked
   for "the exact KNOWN customer name," inadvertently telling the model
   to skip this field for new ones; corrected to make it required
   whenever the corresponding tag is set, known or new alike. Re-verified
   live after the fix (see `AC-02` below) — passes cleanly.
2. **Local `.env` (untracked, not in `## Files to Modify`, no project
   source file) gained two empty placeholder lines,
   `ANTHROPIC_API_KEY=`/`ANTHROPIC_MODEL=`** — `app/config.py`'s
   `Settings` (extended by a sibling story, `ADR-022`/`SPRINT-022`, not
   this task's own scope) now requires both fields to be present at all,
   and the real local `.env` predates that change — the whole `app`
   package failed to import at all without this. Compass (this task's own
   real, configured, working Provider) is unaffected; no code changed.

**Live verification (real backend `.venv`, real vault, real Compass
Provider calls unless noted):**

- **[AC-01]** `determine_placement_and_file("Summary of an ongoing email
  thread with ADNOC's cloud infrastructure team about migrating their
  analytics workloads to Azure...", "TEST-AC01 — existing category",
  "some-other-agent")` → `{"status": "written", "kind": "Emails", "tags":
  ["kind/emails", "customer/adnoc"], "confidence": "high", ...}` — `Emails`
  is an already-existing `list_known_kinds()` value; the real note exists
  on disk at the returned path with the returned tags in frontmatter, plus
  a real `**Customer:** [[ADNOC]]` wikilink. Re-confirmed with a second,
  independent call (`Masdar`) after the prompt-wording fix below — same
  outcome shape. **PASS.**
- **[AC-02]** First pass (`Northwind Traders`, an Azure-MACC-flavoured
  prompt) — the model attributed the content primarily to the known
  partner `Microsoft` instead of the new customer, a legitimate LLM
  judgement call given that specific wording, not a defect; re-ran with
  unambiguous new-customer content (`Riverside Logistics`, no
  partner/Azure framing) → `{"status": "written", "kind": "Emails",
  "tags": ["kind/emails", "customer/riverside-logistics"], ...}`.
  `vault_writer.list_known_customers()` — `False` before, `True` after;
  a real `Work/Customers/Riverside Logistics.md` hub note was created and
  the Email note carries `customer: "Riverside Logistics"` frontmatter
  plus a real `**Customer:** [[Riverside Logistics]]` wikilink. Discoverable
  the same vault-derived way `list_known_kinds`/`list_known_customers`
  already work — no separate, hardcoded lookup. **PASS.**
- **[AC-05]** Direct call to `vault_filing_methodology.
  build_placement_prompt(...)`, printed output confirmed: real excerpts
  from the Five Core Principles + `ADR-004`'s tag/folder split embedded
  verbatim, plus the three real, live-fetched `known_kinds`/
  `known_customers`/`known_partners` lists — not a hardcoded rules table.
  The written notes from `AC-01`/`AC-02` both carry correct tags AND a
  real `[[wikilink]]` to the referenced entity (`ADNOC`, `Riverside
  Logistics`), satisfying the standing tags-and-wikilinks rule. **PASS.**
- **[AC-06]** `model_factory.resolve_agent_model` temporarily monkeypatched
  in-process (reverted immediately after, confirmed
  `resolve_agent_model is _original_resolve` → `True`) to return a fixed
  low-confidence decision — mirrors the task's own "monkeypatch
  model.invoke... mirroring the established in-process-monkeypatch
  pattern" instruction, applied one level up (the resolved model object
  itself, equivalent effect). Result: `{"status": "written", "confidence":
  "low", ...}` — placement completed (never paused for approval), and the
  written note's body starts with `> ⚠️ **Low-confidence placement.**
  Unsure whether this belongs under Notifications or Files.` — the real
  `uncertainty_note` text, not a generic placeholder. **PASS.**
- **[AC-07]** `agent_keywords.get_agent_keywords("vault-filing-expert")` →
  `T01`'s real assigned keywords. `graph.route_cross_section_request(
  "email-capture", "I need help with vault placement and categorize this
  new content, filing and tags")` → `{"matched": True, "agent_id":
  "vault-filing-expert", "from_section_id": "productivity",
  "matched_section_id": "technical"}` (real seed state: `vault-filing-
  expert` self-healed alone into `"technical"`, the other 5 agents in
  `"productivity"` — genuinely cross-Section, no reassignment needed).
  Grep across `src/backend/app` for `determine_placement_and_file`/
  `finalize_new_top_level_area` confirms both are referenced only inside
  `vault_filing_expert.py`/`vault_filing_methodology.py` (their own
  definitions) — no separate write path exists anywhere else in this
  codebase. **PASS.**
- **[AC-08]** Two consecutive calls forced (via a monkeypatched fake
  model, reverted after) to propose the identical `kind`/`filename_stem`
  (`Notifications`/`TEST-AC08-collision-stem`) with different body text
  each time. Second call's returned path carries a `-2` numeric suffix,
  distinct from the first; the first note's own file content is
  byte-identical before and after the second write (`True`) — no
  overwrite. **PASS.**
- Code inspection: `is_new_top_level_area = decision["kind"] not in
  known_kinds` — the Python re-check line is present and unconditional,
  the model's own `is_new_top_level_area` boolean is read from nowhere in
  this file. **PASS.**

No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry — no locked AC failed, no new
dependency, no shared-interface change beyond what `ADR-021` already
designed, no ADR deviation. `gate: flagged` (carried `ADR-021`, PLUS the
two scope-internal judgement calls above logged for human spot-check).
