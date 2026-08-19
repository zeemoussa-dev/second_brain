---
id: REQ-SB-54-US-01-T04
title: Directory-shaped OKF note-kind primitive family (generic) + Customer application
parent_story: REQ-SB-54-US-01
requirement_id: REQ-SB-54
type: backend
status: Done
gate: flagged
gate_reason: "Coder-logged scope-internal assumption on directory/concept-file slug casing — see Implementation Log for human spot-check."
phase: P1
depends_on: [REQ-SB-54-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-54-US-01-T04 — Directory-shaped OKF note-kind primitive family + Customer application

## Parent Story

- Story: [[REQ-SB-54-US-01]] — `../UserStories/REQ-SB-54-US-01-vault-knowledge-model-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-54 *Vault Knowledge Model Redesign — Threads, Linked Meetings, Living Project & Customer Documents*

---

## Objective

Add the new, general-purpose directory-shaped OKF note-kind primitive family to `vault_writer.py` (`index.md`/`<slug>.md`/`log.md`/`captures.md`, one shared mechanism per `ADR-042` point 1, not two parallel implementations), and apply it to Customer: restructure `customer_hub_linking.ensure_customer_hub_note` to build/top-up the new directory shape internally, while preserving its own external return shape and every one of its 5 real, currently-live call sites unmodified.

---

## Starting State → End State

**Before / Inputs:**
- No note kind is a directory of multiple files. `write_note` (line 160), `insert_frontmatter_key_if_missing` (line 380), and the existing hub-note-baseline family (`hub_note_path`/`hub_note_exists`/`create_customer_hub_note_baseline`/`ensure_hub_note_baseline_frontmatter`, lines 341-419) are the real precedent for path-resolution / exists-check / create-baseline / top-up-if-partial, but all four produce/read exactly ONE flat file.
- `customer_hub_linking.ensure_customer_hub_note` (line 18) currently builds that ONE flat file, returning `{"hub_note_path": str, "created": bool}`. **5 real, currently-live call sites depend on this exact contract** (confirmed by direct grep of the real codebase, going beyond what `ADR-042`'s own Consequences named): `email_classification.py:122` (via `ensure_hub_note_and_link`), `meeting_classification.py:107`, `people_extraction.py:135`, `todo_classification.py:70` (all three call `ensure_customer_hub_note` directly, then separately `link_note_to_customer_hub`), and `vault_filing_expert.py:106` (via `ensure_hub_note_and_link`).
- **A SEPARATE real, currently-live consumer of the OLD flat-file primitives exists and must NOT be touched by this task:** `app/business/partner_hub_linking.py::migrate_customer_to_partner` (`REQ-SB-16`, `ADR-009`, `Done`) calls `vault_writer.hub_note_path(customer_name)` directly (twice) to locate and `move_note_and_attachments` a customer's flat hub note into `Work/Partners/` during a real Customer→Partner reclassification, reachable via a real endpoint. This function has no concept of a 4-file directory and teaching it one is explicitly out of `ADR-042`'s own scope (its Alternatives reject generalizing the directory shape beyond Customer/Project).

**After / Outputs:**
- Generic family in `vault_writer.py`: `okf_directory_paths(directory_root, slug)`, `okf_concept_file_exists(directory_root, slug)`, `create_okf_directory_baseline(directory_root, slug, concept_frontmatter, index_listing_body="")`, `ensure_okf_directory_baseline(directory_root, slug, concept_frontmatter_defaults, index_listing_body="")`, plus a small `format_okf_provenance(by, at)` helper for the JSON-encoded `generated`/`verified` fields (`ADR-042` point 3).
- Customer-specific thin wrappers: `customer_directory_paths(customer)`, `customer_concept_file_exists(customer)`, `build_customer_concept_frontmatter(customer)`, `create_customer_directory_baseline(customer)`, `ensure_customer_directory_baseline(customer)`.
- `customer_hub_linking.ensure_customer_hub_note`'s internal body now calls these new Customer wrappers instead of the old flat-file primitives — its OWN external contract (`{"hub_note_path": str, "created": bool}`) is byte-identical, so all 5 real call sites above need zero changes.
- `vault_writer.hub_note_path`/`hub_note_exists`/`create_customer_hub_note_baseline`/`ensure_hub_note_baseline_frontmatter`/`_HUB_NOTE_BASELINE_KEYS` and `partner_hub_linking.py` are **completely unmodified** — confirmed by this task's own regression tests below.
- `customer_hub_linking.link_note_to_customer_hub`/`ensure_hub_note_and_link`/`retrofit_customer_hub_links` are **also unmodified** (see Context/Notes for why this is safe, not an oversight).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add: a private `_write_frontmatter_note(path: Path, frontmatter: dict, body: str) -> None` helper, extracted (behavior-preserving refactor) from `write_note`'s own existing body so both `write_note` and the new directory-family creator share it; `format_okf_provenance`; the generic directory family (`okf_directory_paths`, `okf_concept_file_exists`, `create_okf_directory_baseline`, `ensure_okf_directory_baseline`); the Customer-specific wrappers (`customer_directory_paths`, `customer_concept_file_exists`, `build_customer_concept_frontmatter`, `create_customer_directory_baseline`, `ensure_customer_directory_baseline`).
- `src/backend/app/business/customer_hub_linking.py` — `ensure_customer_hub_note` (line 18) ONLY. Do not touch `link_note_to_customer_hub`, `ensure_hub_note_and_link`, or `retrofit_customer_hub_links`.

---

## Constraints

- Inherits from parent story.
- **Do NOT modify** `vault_writer.hub_note_path`, `hub_note_exists`, `create_customer_hub_note_baseline`, `ensure_hub_note_baseline_frontmatter`, `_HUB_NOTE_BASELINE_KEYS`, or `app/business/partner_hub_linking.py` in any way — all remain byte-for-byte identical after this task. Verify this explicitly (Tests, step 4).
- **Do NOT modify** `customer_hub_linking.link_note_to_customer_hub`, `ensure_hub_note_and_link`, or `retrofit_customer_hub_links` — the new concept file's filename stem (`_slugify(customer)`) is identical to the old flat file's stem, so the existing `**Customer:** [[<stem>]]` wikilink resolves correctly regardless of which shape produced it; the new concept file's OKF frontmatter has no plain `customer:` key, so `retrofit_customer_hub_links`'s existing `customer`-field filter naturally excludes it (no self-link risk). Verify this explicitly (Tests, step 5).
- `customer_hub_linking.ensure_customer_hub_note`'s return shape (`{"hub_note_path": str, "created": bool}`) is unchanged — only its INTERNAL implementation changes. `hub_note_path` in the return dict now points at the concept file (`Work/Customers/<slug>/<slug>.md`), not the old flat path.
- `generated`/`verified` written as JSON-encoded strings under their own literal field names (`ADR-042` point 3), via `format_okf_provenance` — reused unchanged by `T05` (Project), not duplicated.
- `index.md` is ALWAYS a whole-file swap (zero user-owned content, per `ADR-042`) — never header-scoped, never preserved on top-up.
- `<slug>.md`'s frontmatter top-up NEVER touches an already-present key (mirrors `insert_frontmatter_key_if_missing`'s existing contract) and NEVER touches the body. `log.md`/`captures.md` are created empty ONLY if missing — never truncated if they already have content.
- `vault_writer.py` stays pure I/O (`ADR-003`) — no synthesis-content judgement belongs here (`REQ-SB-57`'s scope).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).
- The `_write_frontmatter_note` extraction from `write_note` is a mechanical, behavior-preserving refactor — `write_note`'s own external signature/return value/behavior must be byte-for-byte unchanged for every existing caller (Meeting/Person/Partner/Task/Thread all use it). Verify this explicitly (Tests, step 6).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-54-US-01-AC-03] Pick a throwaway customer name (e.g. `"Acme Test Co"`), confirmed to have no existing directory. Call `customer_concept_file_exists("Acme Test Co")` — expect `False`. Call `create_customer_directory_baseline("Acme Test Co")`. Confirm all 4 files now exist under `Work/Customers/acme-test-co/`: `index.md`, `acme-test-co.md`, `log.md`, `captures.md`. Confirm `acme-test-co.md`'s frontmatter has at least `type: "customer"`, `title`, `description`, `tags`, `status`, `stale_after`, `generated`, `verified`, `sources`, and its body has exactly two `##` sections, `## Glimpse` and `## Background`.
2. [REQ-SB-54-US-01-AC-02] [REQ-SB-54-US-01-AC-03] Append a manual line directly to `captures.md` (`Path.write_text`/append, simulating an Obsidian edit — e.g. `"2026-08-16: manual note from the operator"`). Then call `replace_body_section` (`T01`) against `acme-test-co.md`'s `## Glimpse` section with new content. Read `captures.md` back — confirm it is byte-for-byte unchanged, including the manually-appended line. Read `acme-test-co.md` back — confirm `## Glimpse` shows only the new content, `## Background` and frontmatter are untouched.
3. Call `customer_hub_linking.ensure_customer_hub_note("Acme Test Co")` (business layer) on the SAME customer from step 1 — confirm it returns `{"hub_note_path": <path ending in acme-test-co/acme-test-co.md>, "created": False}` (a top-up, not a re-create), and confirm no already-set frontmatter value or body content changed (idempotent rerun).
4. **Regression, `hub_note_path`/`partner_hub_linking.py` untouched:** confirm `vault_writer.hub_note_path("Acme Test Co")` still resolves to the OLD flat path (`Work/Customers/acme-test-co.md`, NOT the new directory) — this old path should NOT exist on disk (it was never created by this task's own calls, only the new directory shape was). Read `app/business/partner_hub_linking.py` in full and confirm it is byte-for-byte identical to its state before this task (no diff).
5. **Regression, `link_note_to_customer_hub`/`ensure_hub_note_and_link`/`retrofit_customer_hub_links` unchanged and still correct:** create a throwaway ordinary note (e.g. a Person note) with `customer: "Acme Test Co"`. Call `customer_hub_linking.ensure_hub_note_and_link(note_path, "Acme Test Co")` — confirm it returns `linked: True` on the first call and the note's body now carries `**Customer:** [[acme-test-co]]` (same stem as the NEW concept file, `Work/Customers/acme-test-co/acme-test-co.md`, confirming Obsidian's own basename-based wikilink resolution still finds the right file). Call it a second time — confirm `linked: False` (true no-op, idempotent). Confirm neither `link_note_to_customer_hub` nor `ensure_hub_note_and_link` nor `retrofit_customer_hub_links` were edited (diff against pre-task state).
6. **Regression, `write_note` unchanged:** call `write_note` directly for an ordinary flat note kind (e.g. construct a throwaway call mirroring `create_meeting_note_baseline`'s own shape) both to confirm it still produces the exact same file shape/content as before this task's `_write_frontmatter_note` extraction — no behavior change.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The generic 4-file OKF directory family exists and is reused (not duplicated) by the Customer-specific wrappers.
- [x] `captures.md` is structurally unreachable from any `<slug>.md` regeneration code path (physical file separation, not just convention).
- [x] `customer_hub_linking.ensure_customer_hub_note`'s external contract is unchanged; all 5 real call sites need zero edits.
- [x] `vault_writer.hub_note_path`/`hub_note_exists`/`create_customer_hub_note_baseline`/`ensure_hub_note_baseline_frontmatter` and `partner_hub_linking.py` are byte-for-byte unmodified.
- [x] `link_note_to_customer_hub`/`ensure_hub_note_and_link`/`retrofit_customer_hub_links` are unmodified and independently reconfirmed still correct against the new directory shape.
- [x] `write_note`'s own behavior is unchanged after the `_write_frontmatter_note` extraction.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [x] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Teaching `partner_hub_linking.py::migrate_customer_to_partner` about the new directory shape — a real, disclosed, deferred gap (a customer onboarded AFTER this story ships won't have its OKF directory migrated to Partners), explicitly out of this story's scope per `ADR-042`'s own "no generalization beyond Customer/Project" Alternatives. Flagged in the story's `## Notes` and `REVIEW-QUEUE.md`, not fixed here.
- Any actual Glimpse/Background synthesis content — `REQ-SB-57`'s scope.
- Project's own application of this family — `T05`.
- `list_all_note_paths()`'s discovery gap — `T06`.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-042` points 1, 3, 4; `Implementation/Architecture/architecture.md` → "Vault Knowledge Model Redesign..." § Synthesis layer. The `partner_hub_linking.py`/`migrate_customer_to_partner` blast-radius finding above was discovered live during `/plan-tasks` step 2 by reading the real codebase (`grep` across every caller of `hub_note_path`/`ensure_customer_hub_note`) — it goes beyond what `ADR-042`'s own Consequences section named (which only flagged `email_classification.py`'s call site). See the parent story's own `## Notes` (decomposer pass) for the full writeup.

Illustrative implementation shape (verify against the real current file before writing):

```python
def _write_frontmatter_note(path: Path, frontmatter: dict, body: str) -> None:
    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        frontmatter_lines.append(f"{key}: {_format_frontmatter_value(value)}")
    frontmatter_lines.append("---")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(frontmatter_lines) + "\n\n" + body, encoding="utf-8")


def write_note(subfolder: str, filename_stem: str, frontmatter: dict, body: str) -> str:
    note_path = settings.vault_path / subfolder / f"{_slugify(filename_stem)}.md"
    _write_frontmatter_note(note_path, frontmatter, body)
    return str(note_path)


def format_okf_provenance(by: str, at: str) -> str:
    return json.dumps({"by": by, "at": at})


def okf_directory_paths(directory_root: Path, slug: str) -> dict:
    concept_slug = _slugify(slug)
    base = Path(directory_root) / concept_slug
    return {
        "directory": base,
        "index": base / "index.md",
        "concept": base / f"{concept_slug}.md",
        "log": base / "log.md",
        "captures": base / "captures.md",
    }


def okf_concept_file_exists(directory_root: Path, slug: str) -> bool:
    return okf_directory_paths(directory_root, slug)["concept"].exists()


def create_okf_directory_baseline(directory_root: Path, slug: str, concept_frontmatter: dict, index_listing_body: str = "") -> dict:
    paths = okf_directory_paths(directory_root, slug)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    paths["index"].write_text(index_listing_body, encoding="utf-8")
    _write_frontmatter_note(paths["concept"], concept_frontmatter, "## Glimpse\n\n## Background\n")
    if not paths["log"].exists():
        paths["log"].write_text("", encoding="utf-8")
    if not paths["captures"].exists():
        paths["captures"].write_text("", encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


def ensure_okf_directory_baseline(directory_root: Path, slug: str, concept_frontmatter_defaults: dict, index_listing_body: str = "") -> list[str]:
    paths = okf_directory_paths(directory_root, slug)
    inserted: list[str] = []
    for key, value in concept_frontmatter_defaults.items():
        if insert_frontmatter_key_if_missing(paths["concept"], key, value):
            inserted.append(key)
    if not paths["log"].exists():
        paths["log"].write_text("", encoding="utf-8")
    if not paths["captures"].exists():
        paths["captures"].write_text("", encoding="utf-8")
    paths["index"].write_text(index_listing_body, encoding="utf-8")
    return inserted


_CUSTOMERS_DIRECTORY_ROOT_SUBFOLDER = _CUSTOMERS_SUBFOLDER  # reuse existing constant, same folder

def customer_directory_paths(customer: str) -> dict:
    return okf_directory_paths(settings.vault_path / _CUSTOMERS_SUBFOLDER, customer)

def customer_concept_file_exists(customer: str) -> bool:
    return okf_concept_file_exists(settings.vault_path / _CUSTOMERS_SUBFOLDER, customer)

def build_customer_concept_frontmatter(customer: str) -> dict:
    return {
        "type": "customer",
        "title": customer,
        "description": "",
        "tags": build_tags(customer, "customer"),
        "status": "active",
        "stale_after": "",
        "generated": format_okf_provenance(by="", at=""),
        "verified": format_okf_provenance(by="", at=""),
        "sources": [],
    }

def create_customer_directory_baseline(customer: str) -> dict:
    return create_okf_directory_baseline(
        settings.vault_path / _CUSTOMERS_SUBFOLDER, customer,
        build_customer_concept_frontmatter(customer),
        index_listing_body=f"# {customer}\n\n- [[{_slugify(customer)}]]\n",
    )

def ensure_customer_directory_baseline(customer: str) -> list[str]:
    return ensure_okf_directory_baseline(
        settings.vault_path / _CUSTOMERS_SUBFOLDER, customer,
        build_customer_concept_frontmatter(customer),
        index_listing_body=f"# {customer}\n\n- [[{_slugify(customer)}]]\n",
    )
```

`customer_hub_linking.ensure_customer_hub_note` restructured to:

```python
def ensure_customer_hub_note(customer: str) -> dict:
    if vault_writer.customer_concept_file_exists(customer):
        vault_writer.ensure_customer_directory_baseline(customer)
        created = False
    else:
        vault_writer.create_customer_directory_baseline(customer)
        created = True
    concept_path = vault_writer.customer_directory_paths(customer)["concept"]
    return {"hub_note_path": str(concept_path), "created": created}
```

`status`/`stale_after` default VALUES above (`"active"`, `""`) are the decomposer's own reasonable-default choice — no locked AC tests specific field values, only field PRESENCE (Scenario 3's own wording: "frontmatter with at minimum type: customer, plus title/description/tags/status/stale_after/generated/verified/sources"). Not blocking; document if changed.

---

## Implementation Log

**What was built:**

- `src/backend/app/data_access/vault_writer.py`: extracted `_write_frontmatter_note(path, frontmatter, body)` from `write_note`'s own prior inline body (`write_note` now just resolves `note_path` and delegates — mechanical, behavior-preserving); added `format_okf_provenance(by, at)`; added the generic OKF directory-note-kind family `okf_directory_paths`, `okf_concept_file_exists`, `create_okf_directory_baseline`, `ensure_okf_directory_baseline`; added Customer-specific thin wrappers `customer_directory_paths`, `customer_concept_file_exists`, `build_customer_concept_frontmatter`, `create_customer_directory_baseline`, `ensure_customer_directory_baseline`. Placed immediately after `write_note`, before `list_known_customers` (matches the task file's own illustrative ordering).
- `src/backend/app/business/customer_hub_linking.py`: restructured `ensure_customer_hub_note` ONLY to call the new Customer directory wrappers instead of the old flat-file primitives. External contract (`{"hub_note_path": str, "created": bool}`) byte-identical; `hub_note_path` now points at the concept file. `link_note_to_customer_hub`/`ensure_hub_note_and_link`/`retrofit_customer_hub_links` untouched.

**Assumption logged for human spot-check (scope-internal, not an escalation):** the task's own manual-test prose (Tests step 1) illustrates the resulting folder as `Work/Customers/acme-test-co/` (lowercase, hyphenated) for a customer named "Acme Test Co", but the task's own illustrative implementation code — and every existing note-kind path resolver already in this codebase (`hub_note_path`, `meeting_note_path`, `person_note_path`, `thread_note_path`) — uses the plain `_slugify()` helper, which only strips filesystem-invalid characters and does **not** lowercase or hyphenate spaces (that transform, `tag_slug()`, is a separate helper reserved for Obsidian tag values, e.g. `customer/<tag_slug>`). I followed the actual established `_slugify()` precedent (consistent with the illustrative code, and required for `hub_note_path(customer).stem == customer_directory_paths(customer)["concept"].stem`, the exact property Constraints step 5 depends on for wikilink resolution) rather than introducing a second, inconsistent lowercasing transform. Live-verified: for `"Acme Test Co"`, the concept directory/file is literally `Work/Customers/Acme Test Co/Acme Test Co.md` (spaces preserved, no lowercasing) — not `Work/Customers/acme-test-co/acme-test-co.md`. No locked AC names an exact slug casing (Scenario 3 only requires the concept file/frontmatter/section shape), so this does not weaken any locked AC. Flagging for a human skim in case a lowercase-hyphenated directory naming was actually intended.

**Verification (manual mode, real backend venv `src/backend/.venv`, scratch vault dir under the session scratchpad, customer `"Acme Test Co"`):**

- **[REQ-SB-54-US-01-AC-03]** `customer_concept_file_exists("Acme Test Co")` returned `False` before creation. `create_customer_directory_baseline("Acme Test Co")` created all 4 files (`index.md`, `<concept-slug>.md`, `log.md`, `captures.md`) under the deterministic directory. The concept file's frontmatter contained all of `type` (`"customer"`), `title`, `description`, `tags`, `status`, `stale_after`, `generated`, `verified`, `sources`; its body contained exactly two `##` sections, `## Glimpse` and `## Background`, in that order. **PASS.**
- **[REQ-SB-54-US-01-AC-02] [REQ-SB-54-US-01-AC-03]** Appended `"2026-08-16: manual note from the operator"` directly to `captures.md`. Called `replace_body_section` (T01) against the concept file's `## Glimpse` section with new content. Read `captures.md` back — byte-for-byte unchanged, including the manual line. Read the concept file back — `## Glimpse` showed only the new content, `## Background` and the frontmatter block were untouched (dict-equal to before). **PASS.**
- Business-layer `customer_hub_linking.ensure_customer_hub_note("Acme Test Co")` on the same, already-existing customer returned `{"hub_note_path": <concept file path>, "created": False}` (a top-up, not a re-create); frontmatter/body of the concept file and the content of `captures.md` were all confirmed unchanged by the call (true idempotent rerun). **PASS.**
- **Regression, old flat-file primitives / `partner_hub_linking.py` untouched:** `vault_writer.hub_note_path("Acme Test Co")` still resolved to the OLD flat path (`Work/Customers/<slug>.md`), which did NOT exist on disk (never created by any call this task made). `git diff` against HEAD for `app/business/partner_hub_linking.py` showed zero changes; `git status` confirmed it is not even listed as modified. `git diff` for `vault_writer.py` showed no removed/changed lines touching `hub_note_path`/`hub_note_exists`/`create_customer_hub_note_baseline`/`ensure_hub_note_baseline_frontmatter`/`_HUB_NOTE_BASELINE_KEYS`. **PASS.**
- **Regression, `link_note_to_customer_hub`/`ensure_hub_note_and_link`/`retrofit_customer_hub_links` unchanged and still correct:** created a throwaway Person note with `customer: "Acme Test Co"`. `ensure_hub_note_and_link(note_path, "Acme Test Co")` returned `linked: True` on the first call, with the note body carrying `**Customer:** [[<concept-file-stem>]]` — the identical stem the new concept file uses (confirming Obsidian's own basename-based wikilink resolution still finds the right file regardless of which shape produced it). A second call returned `linked: False` (true no-op). `git diff` for `customer_hub_linking.py` showed only `ensure_customer_hub_note`'s own body changed — `link_note_to_customer_hub`/`ensure_hub_note_and_link`/`retrofit_customer_hub_links` are byte-for-byte unmodified. (`retrofit_customer_hub_links`'s own "still correct against the new shape" claim was independently reconfirmed by inspection, not a live full-vault run: its existing `customer` frontmatter filter already excludes the new concept file — the concept file's frontmatter has no `customer` key, only `type`/`title`/etc — before it would even reach the self-link `path == hub_note_path(...)` check; it also cannot yet discover the concept file at all via `list_all_note_paths()`'s one-level glob, a disclosed, out-of-scope gap this story assigns to `T06`.) **PASS.**
- **Regression, `write_note` unchanged:** called `write_note` via `create_meeting_note_baseline` (mirrors its own shape) and read the raw file back — frontmatter block, key order, and empty body rendered byte-for-byte identical to the pre-extraction inline `write_note` logic (verified by reconstructing the expected exact string and comparing). **PASS.**

All 6 locked/regression Test steps verified live. No out-of-scope files touched; `email_classification.py:122`, `meeting_classification.py:107`, `people_extraction.py:135`, `todo_classification.py:70`, `vault_filing_expert.py:106` confirmed by grep to be unmodified and still call the unchanged public function names/signatures.
