---
id: REQ-SB-99-US-01-T04
title: Raw reads for the debug view — the soul as one verbatim document, and config as two labelled layers
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-99-US-01-T04 — The Soul As Written, and Two Config Layers

## Parent Story

- Story: [[REQ-SB-99-US-01]] — `../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-99 *See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs*

---

## Objective

Give `HermesProfiles` the three raw reads the debug view needs — the full
`SOUL.md` with a named-file failure, both config layers as written, and whether
the install root can be read at all — without changing anything it already
serves.

---

## Starting State → End State

**Before / Inputs:**

- `src/backend/app/hermes/profiles.py::read_soul(agent_id)` (line ~188) already
  returns the real full `SOUL.md`, or `None` on `OSError` — it does not say
  *which* file or *why*, and nothing distinguishes "absent" from "unreadable".
- `_read_yaml_file(path)` (line ~54) swallows both a missing file and a YAML
  error into `{}`.
- `_read_agent()` (line ~128) reads the profile's **own** `config.yaml` only.
  There is **no inheritance model anywhere in this codebase** — `_deep_merge`
  (line ~92) is `update()`'s write-patch merge, not a parent overlay. An unset
  key reads as `""`, indistinguishable from absent.
- `_profile_dir(agent_id)` resolves `<home>` for `"default"` and
  `<home>/profiles/<id>` otherwise; `self._config.home_path` is the install
  root.
- `_soul_excerpt()` / `description` / `short_description` are live on the
  Agents Map and must not change.

**After / Outputs:**

- `HermesProfiles.read_soul_document(agent_id)` — returns the real `SOUL.md`
  text **verbatim** together with the absolute path it came from and, when it
  could not be read, a truthful reason distinguishing "no such file" from
  "unreadable" (e.g. a small dataclass or dict: `path`, `text | None`,
  `error | None`). No excerpting, no section splitting, no reassembly.
- `HermesProfiles.read_config_layers(agent_id)` — the profile's own
  `config.yaml` as written, plus, for a non-`default` profile, the install
  root's `config.yaml` as written. Per layer: the file path, the parsed mapping
  (or `None` if the file is absent / does not parse), and a truthful error.
  Nothing is merged.
- `HermesProfiles.install_is_readable()` — `home_path.is_dir()`, so the
  business layer can tell "the install cannot be read at all" from "this
  profile has no such file" without reaching for a path itself.
- `read_soul()`, `_soul_excerpt()`, `_read_agent()`, `description` and
  `short_description` behave exactly as they do today.

---

## Files to Modify

- `src/backend/app/hermes/profiles.py` — the three new readers only.
- `src/backend/tests/test_profile_raw_reads.py` (new) — the tests below.

---

## Constraints

- Inherits from parent story.
- **Additive only.** Do not change `read_soul()`, `_soul_excerpt()`,
  `_first_sentence()`, `_read_agent()` or `_deep_merge()`. The existing short
  description is load-bearing on the Agents Map (story Constraints).
- **Never merge the two config layers** and never present an "effective" value.
  Hermes' own precedence is not readable from this repository, and guessing it
  is a fabrication (`ADR-043`).
- **Verbatim means verbatim** — the soul text is returned unaltered (no strip,
  no normalisation, no truncation); `## Scope`'s body and section order survive
  intact.
- `app/hermes/` stays portable: no `app.config`, no `app.obsidian` import, and
  **no third copy of `long_path()`** (`ADR-043` Consequences). This task adds no
  new tree walk; a path already over 260 characters must surface as the honest
  per-file error above, not as a crash.
- Read-only — nothing here creates a file or a directory.

---

## Tests

**Automated tests:** `cd src/backend; pytest tests/test_profile_raw_reads.py tests/test_soul_and_profile_hygiene.py`

Build a real temporary Hermes home with `tmp_path` (`<home>/SOUL.md`,
`<home>/config.yaml`, `<home>/profiles/adnoc-expert/{SOUL.md,config.yaml,profile.yaml}`)
and construct `HermesProfiles(HermesConfig(base_url="", home_path=tmp_path), HermesSkills(...))`
directly — real files, no mocks.

1. `[REQ-SB-99-US-01-AC-01]` Write a `SOUL.md` longer than 280 characters that
   contains a `## Guardrails` section, a `## Scope` section with a prose body,
   and a trailing section after both. Assert `read_soul_document("adnoc-expert")`
   returns the file's bytes **exactly** (`== path.read_text()`), including the
   `## Scope` body and the original section order, and that the returned path is
   that profile's own `SOUL.md`.
2. `[REQ-SB-99-US-01-AC-01]` Assert the returned text is not the 280-character
   excerpt: `len(text) > 280` and `text != _soul_excerpt(profile_dir)`. Then
   assert the existing surface is untouched — `find_by_id("default").description`
   and `.short_description` are byte-identical to what they are before this
   change for the same fixture, and `tests/test_soul_and_profile_hygiene.py`
   passes unchanged.
3. `[REQ-SB-99-US-01-AC-03]` With the root `config.yaml` holding
   `model: {provider: custom}` and the profile's own holding
   `model: {default: gpt-5}`, assert `read_config_layers("adnoc-expert")`
   returns two layers, each naming its own real file path, with the profile
   layer carrying only `default` and the root layer only `provider` — and that
   **no** merged mapping is returned anywhere in the result.
4. `[REQ-SB-99-US-01-AC-03]` Assert `read_config_layers("default")` returns a
   single layer (the install root *is* the `default` profile), naming
   `<home>/config.yaml`.
5. `[REQ-SB-99-US-01-AC-06]` Delete the profile's `SOUL.md` and assert
   `read_soul_document("adnoc-expert")` returns no text, the path it looked for,
   and an error that distinguishes absent from unreadable; make its
   `config.yaml` unparseable YAML and assert that layer reports an error naming
   the file while the root layer still returns its real mapping — i.e. one
   unreadable file never hides the others.
6. `[REQ-SB-99-US-01-AC-07]` Point `HermesConfig.home_path` at a path that does
   not exist and assert `install_is_readable()` is `False`; point it at an
   existing directory and assert it is `True`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] The full soul is readable verbatim, with its source path and a truthful failure
- [ ] Both config layers readable as written, each naming its file, never merged
- [ ] `install_is_readable()` separates "no install" from "no such file"
- [ ] `_soul_excerpt` / `description` / `short_description` unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Editing a soul or a config — editing already exists elsewhere and is not
  reached from this story.
- Any response shape, route or region assembly — `T05`.
- Resolving which layer Hermes itself would honour — explicitly rejected in
  `ADR-043`.

---

## Context / Notes

`architecture.md` → **§Config as Two Labelled Layers** and **§What Already
Answers This, and What Does Not** (the architect's correction: config
inheritance does not exist in this codebase, and the soul's genuine loss is
`## Scope`'s body plus the document's integrity — text outside the marker blocks
is already exposed through `Agent.prompt`, so a reassembled soul is not
evidence).

---

## Implementation Log

_(Filled in by the coder.)_
