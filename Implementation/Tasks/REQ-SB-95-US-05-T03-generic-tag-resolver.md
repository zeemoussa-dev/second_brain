---
id: REQ-SB-95-US-05-T03
title: The generic tag resolver — name/alias/domain to (kind, tag, hub), ambiguity and non-resolution reported
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "coder, 2026-10-18 — scope-internal judgement calls for human spot-check, nothing blocked: (1) the manual step was performed against a SYNTHETIC vault over a real running backend rather than the operator's real vault, because this session's standing conditions forbid reading it even from a throwaway probe — AC-05 is independently verified by its four automated steps; (2) the unknown-tag report carries three lists plus a registered-with-no-notes list rather than the one list the task names, so a failed namespace read can never be counted as a finding; (3) a new framework constraint could NOT be appended to `MEMORY.md`, which stands at 86 KB against the 40 KB budget its own rule 1 sets — written out in `REVIEW-QUEUE.md` instead"
phase: P2
depends_on: [REQ-SB-95-US-05-T01, REQ-SB-95-US-05-T02]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-05-T03 — The Generic Tag Resolver

## Parent Story

- Story: [[REQ-SB-95-US-05]] — `../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Turn a name, an alias or an email domain into `(kind, tag, hub)` by asking the
registered namespaces at that moment — reporting ambiguity and non-resolution
honestly, and never guessing from note titles.

---

## Starting State → End State

**Before / Inputs:**

- `T01`'s tag-keyed projection (which tags exist, and which notes carry them).
- `T02`'s registered namespaces, each with its `entries()` callable and its
  owning plugin id.
- Nothing resolves a name to anything today; the only verb is search.

**After / Outputs:**

- `app/business/logic/tag_resolution.py` (name indicative) — generic over any
  `<namespace>/<slug>` tag, knowing nothing of Customers, Partners or Entities
  and naming **no** plugin.
- `resolve(name)` asks every registered namespace's `entries()` **at call
  time** and matches case-insensitively against each entry's `name`, its
  `aliases`, and its `domains` (a bare domain, and the domain part of an email
  address). On exactly one match it returns that entry's `kind` (opaque,
  pass-through), its `<namespace>/<slug>` tag and its `hub`.
- **Zero matches** → an explicit "did not resolve" result repeating the name as
  it was given. Not an exception, not an empty entity, not a fallback search.
- **Two or more matches** → an explicit "ambiguous" result naming every
  candidate. Never silently picked.
- **A callable that raises** → that namespace is skipped and logged; the
  remaining namespaces still answer, and if nothing else matches the result is
  "did not resolve", never a wrong answer.
- **Zero registered namespaces** → nothing resolves, honestly.
- An "unknown tags" report over `T01`'s projection: every tag key in the vault
  with no registered entry behind it, named rather than dropped.

---

## Files to Modify

- `src/backend/app/business/logic/tag_resolution.py` (new)
- `src/backend/tests/test_tag_resolution.py` (new)

---

## Constraints

- Inherits from parent story.
- **A registry lookup, never a fuzzy search over note titles.** If this module
  reaches into vault search, it is wrong.
- **Core names no plugin** and never enumerates `kind` (`ADR-022`, `ADR-035`,
  `ADR-037`).
- **Ask the callable at resolution time**, every time. Do not memoise entries
  across calls — the plugin's registry is edited while the app runs.
- Ambiguity is a first-class result, not a logged warning plus a guess.
- Degrade to nothing, never to a wrong answer (`ADR-035`).

---

## Tests

**Automated tests** — `src/backend/tests/test_tag_resolution.py`, run with
`pytest tests/test_tag_resolution.py` from `src/backend`. Register fake
namespaces the way `tests/test_plugin_host.py` builds fake plugins, over a tmp
vault built like `tests/test_vault_index_collisions.py`.

1. `[REQ-SB-95-US-05-AC-01]` Register a namespace whose `entries()` knows one
   entity; resolve its primary name and assert the result carries that
   entity's `kind`, its `<namespace>/<slug>` tag and its `hub`.
2. `[REQ-SB-95-US-05-AC-01]` Assert the `entries()` callable was invoked during
   the resolve call and that changing what it returns changes the next
   resolve's answer with no re-registration — i.e. it is asked at that moment,
   never read from a list captured earlier.
3. `[REQ-SB-95-US-05-AC-01]` Assert resolution never consults note titles:
   spy the vault search entry point and assert zero calls, and assert a name
   that matches a note title but no registered entry does **not** resolve.
4. `[REQ-SB-95-US-05-AC-01]` Supply a `kind` string the framework has never
   seen (e.g. `"Counterparty"`) and assert it is returned byte-identically,
   with no validation against any list.
5. `[REQ-SB-95-US-05-AC-03]` Resolve by an alias, and by an email domain, and
   by an address at that domain, each in mixed letter case; assert all three
   return the same kind, tag and hub as the primary name.
6. `[REQ-SB-95-US-05-AC-03]` Register two entries matching the same name (and,
   separately, the same domain); assert each resolve reports **ambiguous** and
   names both candidates, and never returns one of them.
7. `[REQ-SB-95-US-05-AC-05]` Resolve a name no namespace knows; assert the
   result says plainly that it did not resolve and repeats the name exactly as
   given, and that no scoped read and no search was performed.
8. `[REQ-SB-95-US-05-AC-05]` Resolve with **zero** namespaces registered;
   assert the same honest "did not resolve".
9. `[REQ-SB-95-US-05-AC-05]` Register two namespaces where one `entries()`
   raises; assert the raising one is skipped and logged (assert on the log
   record), the other still resolves its own names, and a name only the broken
   one knew returns "did not resolve" rather than anything else.
10. `[REQ-SB-95-US-05-AC-07]` With a tmp vault carrying tags from an
    unregistered namespace, assert the unknown-tag report names every such tag
    key and that none was dropped from the index.

**Manual verification steps:**

1. `[REQ-SB-95-US-05-AC-05]` With the backend running and no entities plugin
   installed, ask the resolver for a real entity name from the vault and
   confirm it answers "did not resolve" rather than returning search results —
   the CFO test, observed live.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `(kind, tag, hub)` from a name, an alias or a domain, case-insensitively
- [x] `entries()` asked at resolution time, never captured
- [x] Ambiguity reported naming both candidates, never silently resolved
- [x] Non-resolution honest; raising callable skipped and logged
- [x] Unknown tag keys reported, never dropped
- [x] No plugin named; `kind` opaque; no title search anywhere
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **not done, and deliberately so:** `MEMORY.md` is 86 KB against the 40 KB
      budget its own rule 1 sets, which forbids appending while over. The one
      constraint this task produced is written out verbatim in `REVIEW-QUEUE.md`
      for the human to place once the file is under budget.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Reading the entity's notes — `T04`.
- Exposing this as an Action — `T05`.
- Populating or curating any registry — that is the plugin's own work.

---

## Context / Notes

`architecture.md` → **§Entity Resolution — a Generic Tag Resolver, No Plugin
Named** and `ADR-037`'s "framework behaviour at the seam" bullet are
authoritative; each behaviour there is borrowed from an existing precedent
(`provide_service` for duplicate ownership, `register_agent_matcher` for a
raising callable), so read those before inventing a new shape.

---

## Implementation Log

**Coder, 2026-10-18. `Ready → Done`. All four locked ACs verified.**

### What was built

Two files, exactly the two in `## Files to Modify`, both new.

`app/business/logic/tag_resolution.py` — `resolve(name) -> TagResolution` and
`report_unknown_tags() -> UnknownTagReport`, plus `TagCandidate` and
`NamespaceCouldNotAnswer`. It imports exactly two things from the app:
`PluginManager` (the registry read surface `T02` built) and `VaultManager` (the
projection `T01` built). No file I/O, no `data_access` import, no search, no
note read — `business/logic/` composing two Managers (`ADR-003`).

- `resolve()` asks `PluginManager().get_tag_namespaces()` and then every
  registration's `entries()` **inside the call**, keeping nothing between
  calls. Matching is exact after casefold+strip, over the entry's `name`, its
  `aliases`, and its `domains` — a domain given bare, with a leading `@`, or
  as an address at it, on either side of the comparison. Nothing is matched by
  prefix, substring or similarity.
- `resolved` is the single field a caller branches on, separate from `outcome`
  (`resolved` / `ambiguous` / `did_not_resolve`) for the reason
  `ActionCallVerdict.accepted` is separate from its own: a caller forced to
  enumerate outcomes would read any outcome added later as success.
- `kind` is `object`-typed and passed through untouched — never coerced,
  defaulted, normalised or checked against a list.

### Synthesis before evidence, carried in the shape rather than in a convention

The resolution hands back the `hub` as a field of its own and the `tag` as the
scope for evidence, **and no notes at all** — there is no note list on the
result, so nothing downstream can serve thirty tagged Threads without having
first been told where the single hub note is. An entry registering no hub
resolves with `hub = None` and says so in its message
("it registers no hub note, so there is no synthesis to read before its
evidence"), rather than letting a reader quietly lead with evidence. Asserted
by `test_the_resolution_hands_over_synthesis_and_a_scope_but_never_notes`.

### Three kinds of non-answer, three shapes, none borrowing another's look

`SPRINT-091`'s retro rule — an empty-state look may never be borrowed by a
failed read — is applied in the data shape, not in wording:

| The real situation | What it looks like |
|---|---|
| nothing knows that name | `outcome=did_not_resolve`, `every_namespace_answered=True` |
| something could not be asked | same outcome, but `namespaces_that_could_not_answer` non-empty, `every_namespace_answered=False`, and the message ends "so this is incomplete rather than final" |
| two entries match | `outcome=ambiguous`, every candidate named, `tag`/`kind`/`hub` all `None` |
| the tag has no registered entry | `report.unknown_tags` names it |
| the namespace could not answer | `report.tags_whose_namespace_could_not_answer` — never counted as unknown |
| registered, but no note carries it | `report.registered_tags_with_no_notes` |
| the index itself could not be read | every list is `None`, not `[]`, with `index_was_read=False` and the verbatim failure |

### Locked ACs, step by step, with what was observed

18 tests, all AC-tagged, in `tests/test_tag_resolution.py`. Namespaces are
registered by **real plugins** written into a temporary App Database Folder
and loaded by the real `PluginManager` (the `test_plugin_host.py` /
`test_tag_namespace_registration.py` technique), so every resolution goes
through the same seam a shipped plugin would use. Two whole-file tripwires are
armed for **every** test here: `VaultManager.search`, `hybrid_search.search`
and `VaultManager.get_entries_for_tag` are all replaced with `pytest.fail`.

**`[REQ-SB-95-US-05-AC-01]` — verified** (task steps 1–4).

1. *Primary name → kind, tag, hub.* One namespace `glyph` registered by plugin
   `glyph-owner`, one entry. Observed: `resolved=True`, `kind` the opaque
   string, `tag` `glyph/lumen-cartography`, `hub`
   `Work/Hubs/Lumen Cartography.md`, `namespace` `glyph`, `plugin_id`
   `glyph-owner`. (`test_a_registered_name_resolves_to_its_kind_its_tag_and_its_hub`)
2. *Asked at that moment, never captured.* The fake plugin's `entries()`
   appends to a file every time it is called. Observed: call count **0** after
   load, **1** after the first `resolve`, **2** after the second; the registry
   file was rewritten between them with no re-registration and the answer
   followed it — `glyph/lumen-cartography` then `glyph/lumen-cartography-nw`,
   hub changing with it, same registration object owning it.
   (`test_the_callable_is_asked_during_the_resolve_and_the_next_answer_follows_the_registry`)
3. *Never consults note titles.* A tmp vault really holds `Tessellate Works.md`,
   indexed through the real walk (`"Tessellate Works" in get_index()` asserted
   as a precondition). Observed: `resolve("Tessellate Works")` →
   `did_not_resolve`, `tag None`. Zero search calls is **enforced**, not
   inspected: both search entry points fail the test if touched.
   (`test_a_name_that_is_a_real_note_title_but_no_registered_entry_does_not_resolve`)
4. *An unseen `kind`, byte-identical.* `"Counterparty"` and then
   `"Counterparty :: 42/x — née"` — a separator, punctuation and a non-ASCII
   letter, so anything splitting, trimming, casing or mapping it would change a
   byte. Observed: `.encode("utf-8")` equal both times.
   (`test_a_kind_the_framework_has_never_seen_comes_back_byte_identically`)
   Plus the structural half: the module's own source carries none of the words
   `customer`, `partner`, `entities`, `opportunity`, asserted over the real
   file rather than by intention.
   (`test_the_resolver_names_no_plugin_and_enumerates_no_kind`)

**`[REQ-SB-95-US-05-AC-03]` — verified** (task steps 5–6).

5. *Alias, domain, and an address at that domain, in mixed case.* Observed:
   `"lUmEn CaRtOgRaPhY"`, `"  Lc  "`, `"Lumen.Example.INVALID"` and
   `"Someone.Else@Lumen.Example.Invalid"` all return the identical
   `(kind, tag, hub)` triple.
   (`test_an_alias_a_bare_domain_and_an_address_at_it_all_resolve_the_same`)
6. *Two entries matching one name, and separately one domain.* Observed in
   both cases: `outcome=ambiguous`, `resolved=False`, `tag`/`kind`/`hub` all
   `None` — no candidate is returned as the answer — and **both** candidate
   tags appear in `candidates` and in the message. The domain case is proved
   twice over, asked as a bare domain and as an address at it, with the two
   entries registering the domain in different forms (`shared.example.invalid`
   and `info@shared.example.invalid`).
   (`test_two_entries_matching_one_name_are_reported_ambiguous_naming_both`,
   `test_two_entries_sharing_a_domain_are_reported_ambiguous_naming_both`)
   The inverse is pinned too: one entry matched by two of its own spellings is
   **one** candidate, not an ambiguity — otherwise an entry listing its own
   name among its aliases could never resolve.
   (`test_one_entry_matched_by_two_of_its_own_spellings_is_not_ambiguous`)

**`[REQ-SB-95-US-05-AC-05]` — verified** (task steps 7–9).

7. *A name nothing knows.* Asked as `"  A Name Nobody Registered  "`, leading
   and trailing spaces included. Observed: `did_not_resolve`,
   `name_as_asked` **byte-equal to what was asked**, the same string present
   verbatim in the message beside the words "did not resolve",
   `tag`/`kind`/`hub` `None`, `candidates` empty. No scoped read and no search
   was performed — both are armed to fail.
   (`test_a_name_no_namespace_knows_does_not_resolve_and_repeats_it_exactly`)
8. *Zero namespaces registered.* No plugin installed at all;
   `get_tag_namespaces() == []` asserted first. Observed: the same honest
   `did_not_resolve`, name repeated.
   (`test_with_zero_namespaces_registered_nothing_resolves_honestly`)
9. *A raising callable.* Two real plugins load, `quarl-owner` (whose
   `entries()` raises `RuntimeError`) and `glyph-owner`. Observed: the healthy
   namespace still resolves its own name to `glyph/lumen-cartography`; a name
   only the broken one could have known returns `did_not_resolve` and nothing
   else; and `caplog` holds a WARNING from the resolver naming `quarl` and the
   reason. (`test_a_raising_namespace_is_skipped_and_logged_while_the_rest_still_answer`)
   The honesty half is its own test: with only the broken namespace registered,
   `every_namespace_answered` is `False`, the failure record names the
   namespace, the plugin and the verbatim error, and the message ends
   "incomplete rather than final".
   (`test_an_answer_reached_without_every_namespace_is_not_dressed_as_a_final_one`)

**`[REQ-SB-95-US-05-AC-07]` — verified** (task step 10).

10. *Unknown tag keys named, none dropped.* A tmp vault carries five tag keys
    across four namespaces, one of them on a note whose path is **over 260
    characters** (the fixture asserts that precondition, so a key the
    `MAX_PATH` trap could have hidden is covered). One namespace is registered.
    Observed: `known_tags == ['glyph/lumen-cartography']`, `unknown_tags ==
    ['kind/hub', 'kind/thread', 'ward/tessellate-works', 'zz9/plural-z-alpha']`
    — including the deep note's `zz9/plural-z-alpha` — and
    `sorted(known + unknown)` equals `get_tag_index_keys()` exactly, which is
    the "none was dropped" assertion stated as an identity rather than a count.
    (`test_every_tag_key_with_no_registered_entry_is_named_and_none_is_dropped`)
    Three further tests keep "unknown" honest: a registered tag no note carries
    is its own list and is **not** an unknown tag (and still resolves); a tag
    whose namespace is registered but raised is in
    `tags_whose_namespace_could_not_answer`, absent from `unknown_tags`, with
    `is_complete=False`; and an unreadable index returns every list as `None`
    with `index_was_read=False` and the verbatim failure, so "we read it and
    found nothing unknown" cannot be mistaken for "we could not read it".

**Manual step — PASS, against a running backend on a synthetic install** (see
judgement call 1). A real uvicorn was started on `127.0.0.1:8097` (never the
operator's `:8001`) with `VAULT_PATH`/`SECOND_BRAIN_DATA_PATH` at scratch
paths. Observed, in order:

```
POST /vault-index/refresh -> 200 {'notes_indexed': 4, ...}
GET  /vault-search/search?q=Lumen%20Cartography -> 200 4 hit(s):
     ['Lumen Cartography', 'A quiet handover', 'A short standup', 'Tessellate Works']
GET  /system-health plugins -> 200 []
registered namespaces : []
tag index keys        : ['glyph/lumen-cartography', 'kind/hub', 'kind/meeting',
                         'kind/thread', 'ward/tessellate-works']
resolve('Lumen Cartography')
  outcome        : did_not_resolve
  name_as_asked  : 'Lumen Cartography'
  tag/kind/hub   : None / None / None
  message        : "Lumen Cartography" did not resolve: no registered tag
                   namespace knows that name, alias or domain
report_unknown_tags() -> 5 tag(s) in the vault: 0 registered, 5 with no
  registered entry behind them
```

That is the CFO test exactly: the same running backend **would** return four
search hits for the name, a note is literally titled it, and the tag is a key
in the index — and the resolver with no plugin installed still answers "did not
resolve" rather than handing back search results. Every tag key is named as
unknown; none is dropped.

### Test runs

Baseline measured **before the first edit**, and the final run, both from a
**scratch CWD** with `VAULT_PATH`, `SECOND_BRAIN_DATA_PATH` and
`HERMES_HOME_PATH` at scratch directories and the other startup-required
settings set to obvious fakes, so the repository `.env` was never read and the
operator's vault, data store and Hermes install were never reachable:

- **Baseline: 724 passed / 9 failed** (at `5d4a493`).
- **Final: 742 passed / 9 failed** — exactly +18, this file, no regression.

The 9 failures are the same test ids in both runs and are not this task's: the
pre-existing empty-install consequence of a scratch data store with no seeded
Templates (`test_blueprint_install.py`, `test_blueprints_api.py`,
`test_skill_writes_declaration.py` ×3, `test_vault_engine_is_single.py`,
`test_versioning.py` ×3).

### Judgement calls logged for human spot-check (none blocking)

1. **The manual step ran against a synthetic vault, not the operator's.** The
   step names "a real entity name from the vault"; this session's standing
   conditions forbid reading the real vault even from a throwaway probe, and
   pointing a backend at it would run startup side effects that can write. The
   same observation was made over a real running server against a synthetic
   vault, verbatim above. AC-05 does not depend on it — its four automated
   steps all pass. Same call `T01` made, same reason.
2. **The unknown-tag report carries four lists, not one.** The task names "every
   tag key in the vault with no registered entry behind it". Reporting only
   that would have made a namespace whose callable raised look like a finding
   about the vault, which is exactly what `SPRINT-091`'s retro forbids, so
   `tags_whose_namespace_could_not_answer`, `registered_tags_with_no_notes` and
   the `None`-when-unread rule were added beside it. Strictly more than asked
   for, and the superset the ACs' own honesty clause implies.
3. **Identical duplicate entries collapse; differing ones are ambiguous.** Two
   registered entries agreeing on tag, kind and hub are one candidate; any
   difference between them is a genuine ambiguity, because picking either would
   answer a question the data cannot. Stated at the code and tested both ways.
4. **No `MEMORY.md` entry was appended.** The constraint this task produced is
   worth keeping — *a resolver's "not found" and "could not ask" are different
   answers and must differ in shape, not only in wording; payload `None` for an
   unread region, `[]` only for one genuinely read and empty* — but `MEMORY.md`
   is 86 KB against the 40 KB budget its own rule 1 sets, which forbids
   appending while over. The text is written out in `REVIEW-QUEUE.md` for the
   human to place.

### Not done, deliberately

No scoped read and no note ordering (`T04`), no Action and no route (`T05`), no
namespace populated or curated (the plugin's own work), no screen. **No
`FRAMEWORK_API` bump and no edit to `app/plugin_api.py`** — `ESC-079` is the
operator's, and nothing here needed it: the version gate governs only whether a
*plugin* may declare the capability, and the resolver reads whatever is
registered without caring which version allowed it. Every test above registers
its namespaces at the current `FRAMEWORK_API`, so the resolver is proved
against the real seam as it stands today.

### Escalations

**None.** No file outside `## Files to Modify` was needed. Both files are new
and nothing imports them yet — `T04` is the first caller — which is the correct
shape for this task; no existing module had to change to make the resolver
reachable.
