---
id: REQ-SB-99-US-01-T04
title: Raw reads for the debug view — the soul as one verbatim document, and config as two labelled layers
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement calls logged for human spot-check — the three-way file status as a machine-readable field, UnicodeDecodeError treated as unreadable, a non-mapping config.yaml treated as a read failure, and the `default` profile's single layer labelled `profile`. Nothing blocked; no AC weakened."
phase: P2
depends_on: []
created: 2026-10-17
updated: 2026-10-18
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

- [x] The full soul is readable verbatim, with its source path and a truthful failure
- [x] Both config layers readable as written, each naming its file, never merged
- [x] `install_is_readable()` separates "no install" from "no such file"
- [x] `_soul_excerpt` / `description` / `short_description` unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — not updated: nothing new. `ADR-043` already records both decisions (two
      labelled layers, three different failures) and `MEMORY.md`'s 260-character
      `is_file()` trap is the existing constraint this reader obeys rather than a
      new one.
- [x] `CHANGELOG.md` entry appended

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

**2026-10-18 — Done.** `src/backend/app/hermes/profiles.py` gained the three
readers and nothing else; `src/backend/tests/test_profile_raw_reads.py` is new
(17 tests). No file outside `## Files to Modify` was touched by the code change.

### What was built

- `read_soul_document(agent_id) -> SoulDocument(path, status, text, error)` —
  the file verbatim, or `None` text with the failure named.
- `read_config_layers(agent_id) -> list[ConfigLayer(scope, path, status, values, error)]`
  — profile layer first, install-root layer second for any non-`default`
  profile, never merged.
- `install_is_readable() -> bool` — `home_path.is_dir()`, one stat, no read.
- Module-level helpers `_read_file_as_written()` / `_read_config_layer()` and
  the status constants `FILE_WAS_READ` / `FILE_IS_ABSENT` / `FILE_IS_UNREADABLE`,
  plus `CONFIG_LAYER_PROFILE` / `CONFIG_LAYER_INSTALL_ROOT` so `T05` compares
  against names rather than retyping literals.
- `read_soul()`, `_soul_excerpt()`, `_first_sentence()`, `_read_agent()`,
  `_deep_merge()`, `_read_yaml_file()`, `get_all()`, `find_by_id()`, `update()`
  and `write_soul()` are **unchanged** — additive only, as the Constraints
  require.

### Verification — automated mode, every locked AC tagged in the test file

Baseline measured before any edit, at `02a37bd`: **548 passed, 0 failed,
36.21s**. The other session then landed `35f2c22`/`82dd66d`/`4eed39c` mid-task
(+2 tests), so the comparable baseline at `4eed39c` is **550**. After this task:
**567 passed, 0 failed, 42.13s** (+17, exactly this file's tests). Both named
flakes passed. `tests/test_soul_and_profile_hygiene.py` passed **unchanged**, as
the Tests block requires.

| AC-ID | Test (`tests/test_profile_raw_reads.py`) | Observed |
|---|---|---|
| `AC-01` | `test_the_soul_comes_back_byte_for_byte_with_the_file_it_came_from` | **Pass.** `document.text == soul_path.read_text()` for a 900-character soul; `## Scope`'s prose body present; `## Guardrails` < `## Scope` < `## Escalation` index order holds; `path` is that profile's own `SOUL.md`; `(status, error) == ("read", "")`. |
| `AC-01` | `test_the_full_soul_is_not_the_280_character_excerpt` | **Pass.** `len(text) > 280`, `text != _soul_excerpt(profile_dir)`, and the text does not end in the excerpt's `…`. |
| `AC-01` | `test_the_live_short_description_surface_is_untouched` | **Pass.** `find_by_id("default").description` is the pinned 276-character literal and `.short_description` the pinned `"You are the primary identity of this install."` — both literals, so a future change to `_soul_excerpt`/`_first_sentence` fails here. `read_soul("default")` still returns the same bytes. |
| `AC-03` | `test_a_named_profile_reads_as_two_labelled_layers_and_nothing_merged` | **Pass.** Two layers; profile layer path `<home>/profiles/adnoc-expert/config.yaml` carrying only `model.default`, root layer path `<home>/config.yaml` carrying only `model.provider`; neither key leaks into the other. |
| `AC-03` | `test_no_merged_effective_value_is_returned_anywhere` | **Pass.** `len(layers) == 2`, no layer's `model` holds both keys, `[["default"], ["provider"]]` by equality. |
| `AC-03` | `test_the_default_profile_has_one_layer_because_it_is_the_install_root` | **Pass.** One layer, `<home>/config.yaml`, with the root's real mapping. |
| `AC-06` | `test_a_missing_soul_names_the_file_it_looked_for_and_says_it_is_absent` | **Pass.** `text is None`, `status == "absent"`, error contains the full path, and the file is still absent afterwards. |
| `AC-06` | `test_an_unreadable_soul_is_a_different_answer_from_an_absent_one` | **Pass.** Real non-UTF-8 bytes on disk → `status == "unreadable"` (≠ `"absent"`), `text is None`, non-empty reason, path named. |
| `AC-06` | `test_an_empty_soul_is_read_successfully_and_is_not_absent` | **Pass.** `("read", "", "")` — the fourth answer the brief asks for. |
| `AC-06` | `test_one_unreadable_config_layer_never_hides_the_other` | **Pass.** Unparseable profile YAML → `status "unreadable"`, `values is None`, file named in the error; the root layer still returns `{"model": {"provider": "custom"}}`. |
| `AC-06` | `test_an_absent_config_layer_is_told_apart_from_an_empty_one` | **Pass.** Deleted profile config → `("absent", None)`; empty root config → `("read", {}, "")`. This is the distinction `_read_yaml_file()` structurally cannot make. |
| `AC-07` | `test_install_is_readable_separates_no_install_from_no_such_file` | **Pass.** `False` for a non-existent home, `True` for the real one, and asking created nothing. |
| `AC-07` | `test_a_file_on_an_absent_install_still_answers_honestly_rather_than_raising` | **Pass.** On an absent install both readers return `absent` rather than raising, so `T05` can render Scenario 7 from `install_is_readable()` without a second failure mode. |
| `AC-05` | `test_reading_a_profile_writes_nothing` | **Pass.** `rglob("*")` listing identical before/after five calls including two against a profile that does not exist; no directory created. |

### Cost, pinned by equality (`BUG-086`)

Measured by wrapping the real `Path.read_text` (the files stay real), asserting
the exact list of paths, not a count bound:

- `read_soul_document(profile)` → **exactly 1 read**: `[<profile>/SOUL.md]`.
- `read_config_layers(profile)` → **exactly 2 reads, in order**:
  `[<profile>/config.yaml, <home>/config.yaml]`.
- `read_config_layers("default")` → **exactly 1 read**: `[<home>/config.yaml]`
  — the same file is not read twice.
- `install_is_readable()` → **exactly 0 reads** (one stat).
- A failing read is **reported once and never retried**: with both profile
  files deleted, the three calls produce exactly
  `[SOUL.md, <profile>/config.yaml, <home>/config.yaml]`.
- **0 subprocesses** — `subprocess.run`/`Popen` are refused for the whole file
  by an autouse fixture, so a spawn would fail the test rather than be counted.

### No access to the operator's real install

- conftest's suite-wide sandbox is asserted, not assumed: the last test checks
  `settings.hermes_home_path` does not exist, then proves the stronger property
  these readers actually need — **every path any of them touched is under this
  test's own `tmp_path`**, and none is under the sandbox's parent. Nothing in
  the sandbox was weakened, bypassed or special-cased; these readers take their
  home from the `HermesConfig` they are handed, which is the seam the fixture
  builds.
- Measured independently with a session-wide tripwire (a throwaway pytest
  plugin in the scratchpad, not committed) that records every
  `Path.read_text/read_bytes/write_text/write_bytes/open/mkdir/unlink/touch/rename`,
  `builtins.open` and `os.open` whose target is under the **real**
  `<HERMES_HOME>` (which exists on this machine), plus every subprocess spawn:
  - this file alone → **0 touches under the real install, 0 subprocess spawns**;
  - the whole suite → **0 touches under the real install**; all 156 recorded
    spawn events (78 spawns, each seen twice because `run` delegates to `Popen`)
    belong to other files and target `git`/`python` under `tmp_path`.
  - Under the tripwire only, `test_marketplace_source.py::test_a_plugin_installs_from_a_git_repository…`
    failed — it is the named known flake, it passes in every plain run, and the
    tripwire wraps `builtins.open`/`subprocess` which that git-clone test is
    sensitive to. Not caused by this change.

### Judgement calls (scope-internal — logged, not escalated)

1. **The three failures are a machine-readable `status` field**, not only a
   prose `error`. The task's own wording ("a small dataclass or dict: `path`,
   `text | None`, `error | None`") would have forced `T05`/`T06` to sniff an OS
   error string to tell absent from unreadable, which is the dishonesty
   `AC-06` exists to prevent. The constants are exported for `T05`.
2. **A non-UTF-8 file is `unreadable`, not a crash.** `read_soul()` catches
   `OSError` only, so a binary `SOUL.md` would propagate a `UnicodeDecodeError`
   and take the whole composed response down. Caught here as the honest
   per-file failure `ADR-043` asks for.
3. **A `config.yaml` that parses to something other than a mapping is a read
   failure** naming the file (`"… does not hold a mapping of settings (it
   parsed as list)"`), rather than `_read_yaml_file()`'s silent `{}`. An empty
   file, by contrast, is a successful read of `{}` — it exists and sets nothing.
4. **The `default` profile's single layer is labelled `profile`**, not
   `install_root`: `<HERMES_HOME>/config.yaml` *is* that profile's own config,
   and emitting it twice (once per scope) would invent a second source for one
   file. Documented on the method.
5. **Absence is decided by the read, not by a preceding `is_file()`** — on this
   host a path over 260 characters makes `is_file()` answer `False`
   (`MEMORY.md`), which would report an unreachable file as a non-existent one.
   The OS's own error is reported instead. This also keeps the reader at one
   filesystem call per file.
6. **Paths are returned as derived from the configured home, not `resolve()`d** —
   `resolve()` does I/O, can itself fail on a long path, and would make the
   returned path differ from the one the operator configured.

### Not escalated, and why

No new dependency, no shared-interface change (every existing method keeps its
name, signature and value), no ADR deviation (`ADR-043`'s two-layers and
three-failures decisions are implemented as written), no unanticipated file —
`profiles.py` and the new test file are exactly the task's `## Files to Modify`.
Nothing was written to `ESCALATIONS.md` or `REVIEW-QUEUE.md`.
