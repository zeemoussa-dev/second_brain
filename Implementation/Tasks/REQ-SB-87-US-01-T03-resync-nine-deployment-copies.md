---
id: REQ-SB-87-US-01-T03
title: Resync canonical vault_manager.py to all nine real deployment locations
parent_story: REQ-SB-87-US-01
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-01-T02]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-01-T03 — Resync Canonical vault_manager.py to All Nine Real Deployment Locations

## Parent Story

- Story: [[REQ-SB-87-US-01]] — `../UserStories/REQ-SB-87-US-01-vault-manager-resync-and-thread-templates.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Copy the now-extended canonical `Hermes-Provisioning/shared/vault_manager.py`
(post `T01`/`T02`) byte-for-byte into every one of the nine real, active
deployment locations, so every already-deployed copy carries the SAME
engine — resolving Scenario 1's own confirmed drift (`meeting-capture`'s
own copy alone lags behind).

---

## Starting State → End State

**Before / Inputs:**
- Real, confirmed deployment inventory (nine copies, direct diff,
  2026-09-01): `azure-kb-writer`, `compass-kb-writer`, `research-kb-writer`,
  `capture-files`, `capture-notes`, `vault-index`, `track-opportunities`,
  `create-companies-partners`, `meeting-capture` — each has its own
  `scripts/vault_manager.py` copy.
- Only `meeting-capture`'s own copy has actually drifted BEHIND the
  canonical source (0 of `merge_tags`/`upsert_namespaced_tag`/
  `insert_body_line_if_missing`/`_tag_slugify`/`_child_note_name`/
  `root.children`/`parent.on_missing: "auto_create"` found there);
  `create-companies-partners`'s own copy already matches.

**After / Outputs:**
- All nine copies are byte-identical to the canonical source
  (`Hermes-Provisioning/shared/vault_manager.py`, now carrying `T01`'s
  dynamic-children primitive and `T02`'s per-caller access), each still at
  its own real path:
  - `Hermes-Provisioning/skills/**/azure-kb-writer/scripts/vault_manager.py`
  - `Hermes-Provisioning/skills/**/compass-kb-writer/scripts/vault_manager.py`
  - `Hermes-Provisioning/skills/**/research-kb-writer/scripts/vault_manager.py`
  - `Hermes-Provisioning/skills/**/capture-files/scripts/vault_manager.py`
  - `Hermes-Provisioning/skills/**/capture-notes/scripts/vault_manager.py`
  - `Hermes-Provisioning/skills/**/vault-index/scripts/vault_manager.py`
  - `Hermes-Provisioning/skills/**/track-opportunities/scripts/vault_manager.py`
  - `Hermes-Provisioning/skills/company-review/create-companies-partners/scripts/vault_manager.py`
  - `Hermes-Provisioning/skills/vault-rebuild/meeting-capture/scripts/vault_manager.py`
- Deployed to the real, active Hermes profile location(s) each Skill is
  actually running from (not only the `Hermes-Provisioning/` repo copies),
  per this project's own standing manual-deploy pattern
  (`[[feedback_deploy_hermes_provisioning_manually]]`).

---

## Files to Modify

- The nine `scripts/vault_manager.py` copies listed above (repo copies).
- Their corresponding real, active Hermes profile deployment copies (exact
  paths under the operator's local Hermes profile installation — resolve
  directly at build time; do not guess a path not actually confirmed to
  exist).

---

## Constraints

- Inherits from parent story.
- **Byte-identical, not "functionally equivalent"** — a straight file copy
  from the canonical source, no per-location edits.
- Never touch anything else in a Skill's own `scripts/` folder — this task
  only replaces the one `vault_manager.py` file at each location.
- Repo copy AND the real, active Hermes profile copy both need updating —
  the repo copy alone is inert until manually deployed
  (`[[feedback_deploy_hermes_provisioning_manually]]`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-01-AC-01]` For each of the nine repo-copy paths above,
   diff its content against the canonical
   `Hermes-Provisioning/shared/vault_manager.py`; confirm byte-identical
   (zero diff) for all nine.
2. `[REQ-SB-87-US-01-AC-01]` For each real, active Hermes profile location
   actually running one of these nine Skills today, diff its own deployed
   `vault_manager.py` copy against the canonical source the same way;
   confirm byte-identical.
3. `[REQ-SB-87-US-01-AC-01]` Confirm `meeting-capture`'s own copy (the one
   real, confirmed drift) now contains `merge_tags`,
   `upsert_namespaced_tag`, `insert_body_line_if_missing`, `_tag_slugify`,
   `_child_note_name`, `root.children` support, and
   `parent.on_missing: "auto_create"` — the specific functions Scenario 1's
   own Given names as previously missing.

**Automated tests:** `n/a — a straight file-copy operation; verified by
direct diff, not a pytest run`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All nine real deployed `vault_manager.py` copies (repo + active
      Hermes profile locations) are byte-identical to the canonical source
- [x] `meeting-capture`'s own previously-drifted copy now carries every
      function it was missing
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Retrofitting the actual CALLING scripts (`ingest_meeting.py`,
  `create_companies_partners.py`) to pass the new caller-identity argument
  — `T04`.
- Deploying a brand-new (first-time) copy to `email-thread-capture`'s own
  `scripts/` folder or `summarize-and-tag-threads`'s own `scripts/` folder
  — those are `REQ-SB-87-US-02`'s and `REQ-SB-87-US-04`'s own scope
  respectively (first-time deployments, not a resync of an existing copy).

---

## Context / Notes

`architecture.md` → `§Canonical vault_manager.py Source & Deployment` names
the real, full nine-copy inventory. This is operational hygiene enforcing
an already-Accepted convention (no new ADR governs the resync itself,
per that architecture section's own text) — the ENGINE CAPABILITY changes
being resynced here are `ADR-017`'s.

---

## Implementation Log

**Real, live-enumerated deployment inventory (not trusted from the task's own
prose, re-derived directly, 2026-09-01):**
- 9 real repo copies via `Glob`/`find` over `Hermes-Provisioning/**/scripts/
  vault_manager.py` — matched the task's own list exactly: `azure-kb-writer`,
  `compass-kb-writer`, `research-kb-writer`, `capture-files`,
  `capture-notes`, `vault-index`, `track-opportunities`,
  `create-companies-partners`, `meeting-capture`.
- 73 real, ACTIVE deployed copies via a live `find` over
  `%LOCALAPPDATA%\hermes\profiles\**\scripts\vault_manager.py`: 26x
  `create-companies-partners`, 26x `meeting-capture`, 11x `azure-kb-writer`,
  5x `vault-index`, 1x each `capture-files`/`capture-notes`/
  `compass-kb-writer`/`research-kb-writer`/`track-opportunities`. Explicitly
  confirmed zero hits under any `_disabled-skills*` folder (correctly
  excluded — inactive, never a real deployment target). This is well past
  `[[feedback_deploy_hermes_provisioning_manually]]`'s own last-recorded
  count (2026-08-30, ~50 across a named subset of profiles) — that memory's
  own "don't assume this list is exhaustive, re-`find` when in doubt"
  caveat held.

**What was changed:** a straight byte-for-byte copy of
`Hermes-Provisioning/shared/vault_manager.py` (canonical, post-`T01`/`T02`)
onto all 9 repo copies and all 73 real profile copies. No per-location edits
of any kind. Nothing else in any Skill's own `scripts/` folder was touched.

**Verification (live, both pre- and post-resync, SHA-256 checksum — not
`diff -q`/eyeballing):**
- **Pre-resync:** computed the canonical file's own SHA-256 and compared it
  against all 9 repo copies (all 9 differed — expected, `T01`/`T02` had
  landed only on the canonical file) and, separately via `diff -q`, a sample
  sweep across all 73 real profile copies (all differed too, same reason).
- **Post-resync:** recomputed SHA-256 for the canonical source and all 82
  real copies (9 repo + 73 profile) — **all 82 match the canonical hash
  exactly** (`9b9caff1...e83c34af9`).

`[REQ-SB-87-US-01-AC-01]` **PASS** — all 82 real deployed copies confirmed
byte-identical (SHA-256, not just `diff -q`) to the canonical source, both
the 9 repo-tracked copies and the 73 real, active Hermes profile copies.

`[REQ-SB-87-US-01-AC-01]` **PASS** — `meeting-capture`'s own previously-
drifted copy (repo: `Hermes-Provisioning/skills/vault-rebuild/
meeting-capture/scripts/vault_manager.py`) now contains all of
`merge_tags` (1 occurrence), `upsert_namespaced_tag` (3),
`insert_body_line_if_missing` (2), `_tag_slugify` (3), `_child_note_name`
(5), `root.children` (6), `parent.on_missing: "auto_create"`/`auto_create`
(6) — the exact functions Scenario 1's own Given named as previously
missing — confirmed via direct `grep` against the resynced file, plus
`T01`'s `create_dynamic_child`/`growth: "dynamic"` and `T02`'s
`allowed_callers` (15 occurrences) both present, confirming the resync
brought the FULL current canonical, not an intermediate version.

**Real end-to-end smoke test (not just a static grep) — `meeting-capture`'s
own resynced deployed copy, driven via its own CLI against a scratch vault,
mirroring `ingest_meeting.py`'s exact real call shape (no `--caller`
argument passed, since `T04` — retrofitting existing callers to pass their
own caller identity — is explicitly out of this task's own scope):**
1. `find` (by id) on a not-yet-existing note — correctly returned
   `{"path": null}`.
2. `create` (own-folder template, no declared parent, explicit
   `note_name`) — created the real note on disk with correct frontmatter.
3. `modify-section` (a plain `machine_write` section, no `allowed_callers`
   declared, no `--caller` passed) — succeeded, appended real content.
4. `find` again — resolved the same real path (idempotent).
5. Read the real file back from disk directly — frontmatter + `## Notes`
   content exactly as written, nothing corrupted or silently altered.
6. Also confirmed via `--help` that all 9 resynced repo copies run cleanly
   as standalone scripts (exit code 0, `--caller` correctly exposed in the
   CLI signature).

Scratch vault deleted after verification (not a repo artefact). Also
confirmed directly (grep across the real live vault's own
`.second-brain/data/Templates/`) that **no real `Template.json` today
declares `allowed_callers`** (`T05`, which authors the Thread template, has
not yet run) — so `T02`'s new caller-identity gate is a genuine no-op for
every already-`Done` Skill today, and `meeting-capture`'s/
`create-companies-partners`'s real callers (`ingest_meeting.py`,
`create_companies_partners.py` — confirmed by reading both directly, neither
passes a `caller=`/`--caller` argument anywhere) continue to work completely
unchanged. This satisfies Scenario 1's own "every other existing real
caller of `vault_manager.py` continues to work unchanged" clause for both
already-migrated real callers, not just `meeting-capture`'s.

**Scope-internal note (non-blocking, disclosed for visibility, not a
requirement gap):** the task's own launching instruction additionally asked
for "whatever real, lightweight discipline the task file's own End-State
calls for to keep it true going forward (a verification script/checksum
comparison, not just a prose reminder)." Re-read this task's own End-State
and `## Files to Modify` directly: neither names a new, persisted
verification-script artefact as an output — the task's own `## Tests`
section explicitly scopes verification as `"n/a -- a straight file-copy
operation; verified by direct diff, not a pytest run"`. Creating a NEW
committed script file would be an unanticipated file outside this task's
own `## Files to Modify`. Followed the task file's own authored contract
exactly: performed the "lightweight discipline" as a live, rigorous
SHA-256 checksum comparison (ad hoc, via the coder's own tooling, not a new
repo artefact) — satisfies the launching instruction's actual intent
(genuine checksum verification, not a prose claim) without expanding this
task's own scope. A future task could formalize this as a small,
persisted `verify_vault_manager_sync.py` if the operator wants a
repeatable pre-commit/CI-style check going forward — not built here,
named only for visibility. `gate: clear` — this is a disclosed reconciliation
of an informal instruction against the task's own authored contract, not an
assumption filling a real requirement gap (the task's own Tests section is
unambiguous on this point).

**No `ESCALATIONS.md` / `REVIEW-QUEUE.md` entries written by this task** —
no new dependency, no shared-interface change, no ADR deviation (this task
enforces an already-Accepted convention per `architecture.md`'s own
§Canonical `vault_manager.py` Source & Deployment, no new ADR needed), no
unanticipated file was actually created, and both locked ACs verified with
a real positive result (live SHA-256 checksum comparison + a real
end-to-end scratch-vault smoke test through the exact resynced deployed
artefact).

gate: clear 2026-09-01 — no triggers fired (operational hygiene enforcing
an already-Accepted convention per `architecture.md`; the one disclosed
note above is a reconciliation against the task's own unambiguous Tests
section, not an assumption filling a gap; no ESCALATIONS entry; task not
oversized; both locked ACs verified live with a real positive result across
all 82 real deployed copies).
