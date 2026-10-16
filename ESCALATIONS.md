# ESCALATIONS

Append-only log of every backward pipeline step (re-spec, re-architect, re-plan)
and out-of-scope event. Never edit a resolved entry. Every resolved entry names a
concrete resolving artefact (story ID, ADR number, or commit hash).

Categories: `unclear-requirement | out-of-scope | new-dependency |
shared-interface-change | adr-deviation | unanticipated-file | oversized-story |
other`

<!-- Entry format:
## ESC-NNN: [Short description] — YYYY-MM-DD
**Category:** [category from list above]
**Trigger:** What caused the escalation
**Resolution:** What was decided
**Resolving artefact:** story-id / ADR-NNN / commit abc123
**Status:** Resolved | Open
-->

> **Emptied 2026-09-06 (operator-directed), starting a clean cross-device build.**
> This file carried 63 entries / 5,035 lines, 36 still `Open`, the oldest from
> 2026-08-11.
>
> **This one is a deliberate exception to the file's own rule.** It is designed
> append-only precisely so the record of backward steps survives; emptying it is
> the operator's call for a fresh build phase, not a change to that rule. The
> rule still stands for everything logged from here on.
>
> **Nothing is lost** — the full log is in git at `d64dcb4`:
>
> ```bash
> git show d64dcb4:ESCALATIONS.md
> ```
>
> **The next id is `ESC-063`.** Ids are never reused; the historical ones are
> still referenced from stories, tasks and ADRs.

---

## ESC-063: `ADR-032`'s entity resolver and `ADR-022`'s Entities-plugin boundary disagree — 2026-10-16

**Category:** adr-deviation
**Trigger:** Specing `REQ-SB-95` (analyst, `/spec`) produced
`REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`, which cannot say which
repository it builds in. `ADR-032` (Accepted 2026-10-16) specifies entity
resolution as "ONE tag-keyed index, not one index per entity. A single artifact
groups every `customer/*` and `partner/*` tag" — written as framework work, and
spelt out nowhere as anything else. `ADR-022` (Accepted 2026-09-14) decides the
opposite boundary for exactly those concepts: "the Customer, Partner and
Opportunity code moves into a Entities plugin (`sb-plugins-entities`) together
with `Entities.md`, its Settings page, the company Skills and `company_index`",
and "Core never imports, names or knows a plugin", under the operator's own test
that *a second brain built for a CFO cares nothing about Partners and Customers*.
The contradiction is not theoretical: `Settings/Entities.md` is already reached
through `app/plugin_api.py`'s `register_seed_data_file()`, i.e. it is already
being handled as plugin-owned seed data, while `ADR-032` assumes a resolver that
reads it. The two readings land the work in different repositories, under
different `CLAUDE.md`/`MEMORY.md` contexts (`ADR-023`), with different answers to
whether a non-Customer/Partner install gets the feature at all.
**Resolution:** Operator, 2026-10-16: "Resolver is framework, Customer stays the
plugin." The framework ships a tag-keyed resolver generic over any `<namespace>/<slug>`
tag, naming no plugin and knowing nothing of Customers; a plugin registers its namespace
through the Plugin API, and the entities plugin registers `customer/` and `partner/`.
`REQ-SB-95-US-05` therefore builds in this repository as mechanism, with the namespace
registration belonging to `sb-plugins-entities`. `ADR-022` stands unamended -- core offers
a seam, the plugin fills it.
**Resolving artefact:** `ADR-035`
**Status:** Resolved
