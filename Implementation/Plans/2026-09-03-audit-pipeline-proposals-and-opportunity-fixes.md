# Audit pipeline proposals + real Opportunity-data fixes — draft

**Status:** draft, not yet spec'd. Written while the operator shapes the
Opportunity data model in a separate session — the two Opportunity-specific
pipelines below are deliberately sequenced to wait on that, everything else
isn't blocked by it.

**Inputs this draws on:** 8 pipeline proposals authored by a separate
Claude session's vault audit (`.second-brain/pipelines/proposed/*.json`),
this session's own feasibility check against the real vault (2026-09-02/03),
and a direct comparison of the 26 real Opportunity notes against
`track-opportunities/SKILL.md`'s own documented design.

---

## 1. Sequencing

**Build now, no dependency on the Opp-shaping work:**
Vault Integrity → Tag Taxonomy Enforcement → Topic Tagging → Commitment
Tracking → Contact Enrichment and Coverage.

**Wait for the Opp-shaping session to land first:**
Opportunity Discovery, Opportunity Health — both read/write the exact
`status`/`expected_consumption`/tag shape currently being redesigned.
Building against the current (partly-inconsistent) schema now means
rebuilding once the new shape lands. Revisit once that session settles.

**No strong dependency either way, but lowest priority:**
Fact Decay Watch — real and useful, but needs its own infra fix first
(below) and isn't blocking anything else.

---

## 2. The 8 proposed pipelines — feasibility recap

| Pipeline | Real blockers | Verdict |
|---|---|---|
| **Vault Integrity** | None found. Report-only, `vault-index` Skill already real and deployed. | Ready to spec now. |
| **Tag Taxonomy Enforcement** | `Tag Taxonomy.md` already exists, real and substantive (not a stub). | Ready to spec now. |
| **Topic Tagging** | Same `Tag Taxonomy.md` dependency, already satisfied. | Ready to spec now. |
| **Commitment Tracking** | None technical. Its own problem-scale framing ("866 Threads") doesn't match the real, current count (260) — re-verify the real baseline before writing the story, don't inherit the audit's stale number. | Ready to spec once re-baselined. |
| **Contact Enrichment and Coverage** | `person-lookup` really is deployed only to `meeting-prep-agent`, confirmed. Real Person-note counts also need re-baselining (audit claimed 538/490 empty; real count is 355/203 empty). | Ready to spec once re-baselined. |
| **Fact Decay Watch** | `cron_profile_id: research-agent`, but `research-agent` has no dedicated gateway Startup entry (only `default` and `meeting-prep-agent` do) — a job scoped there won't fire until that's set up. Real, fixable, same pattern as `meeting-prep-agent`'s own existing setup. | Spec-able now; infra fix needed before its cron job can actually run. |
| **Opportunity Discovery** | Same missing-gateway issue (`opp-manager`). Also: writes proposals shaped by the CURRENT Opportunity schema, which is mid-redesign. | Hold for Opp-shaping to land. |
| **Opportunity Health** | Same missing-gateway issue (`opp-manager`). Reads exactly the fields (`status`, `expected_consumption`) under active redesign. | Hold for Opp-shaping to land. |

---

## 3. Real fixes needed in `track-opportunities` (found via direct comparison, not proposed by the audit)

These are bugs in the CURRENT agent's own behavior, found by reading all 26
real Opportunity notes against `SKILL.md`'s own documented design — not
part of the 8 proposals, but should land alongside whatever the Opp-shaping
session produces, since they affect the same notes.

1. **`status` default isn't actually applying.** `SKILL.md` documents
   `status` as defaulting to `"Open"` when omitted from the create payload.
   19 of 26 real notes have `status: ""` instead — the likely cause is the
   creating call passing an explicit empty string rather than omitting the
   key (an explicit value always overrides a template default). Real,
   narrow fix: whatever calls `vault_manager.py create` for Job 1 should
   omit `status` from the payload entirely when the operator's answer is
   blank/skipped, not pass `""`.
2. **Missing `kind/opportunity` tag on the same batch.** The Aug 30–31
   notes (the same ones missing `status`) also lack the documented
   `kind/opportunity` tag — only carry `customer/<slug>`. The Sep 2 batch
   has both fields correct, so this self-corrected at some point; the
   older batch is still non-compliant with the agent's own spec.
   Mechanical, safe backfill — arguably the first real, concrete use case
   for `tag-taxonomy.json`'s own "repair mechanical failures" step once
   that pipeline exists (a missing mandatory tag "fully derivable from the
   note's own folder and type" is explicitly in its own scope).
3. **No declared `status` vocabulary.** One real note now carries
   `status: "Disengaged"` — a value `SKILL.md` never documents (only
   `"Open"` is mentioned). Nothing currently declares or enforces what
   values `status` can take, unlike the emerging `Tag Taxonomy.md` for
   tags. Real gap: author a `Settings/Opportunity Status.md` (or fold it
   into `Tag Taxonomy.md`) declaring the real, closed set of values once
   the Opp-shaping session settles on them.
4. **Two notes bypassed the pipeline entirely.** `Tadweer/.../Azure
   Services and DevSecOps Support` and `Masdar/.../Subscription
   Consolidation...` are rendered in raw YAML-block style, not
   `vault_manager.py`'s own JSON-inline style — direct file writes from
   outside the Skill. Not necessarily wrong content-wise, but any future
   pipeline that parses Opportunity frontmatter assuming one consistent
   shape (Tag Taxonomy Enforcement, Opportunity Health) needs to tolerate
   both renderings, or these two need re-writing through the real engine
   once their content is settled.

---

## 4. Infra fixes needed regardless of which pipelines get built

- **`research-agent` and `opp-manager` need their own dedicated gateway**
  (a `Hermes_Gateway_<profile>.vbs` Startup-folder entry, same pattern
  `meeting-prep-agent` already has) before any cron job scoped to
  `cron_profile_id` on either can actually fire. Currently only `default`
  and `meeting-prep-agent` have one.
- **Re-baseline, don't inherit, the audit's own cited counts** before
  writing any story around them — Thread and Person-note counts in
  particular don't match the current, real vault (see table above).

---

## 5. Recommended order

1. **Vault Integrity** — zero dependencies, catches regressions in
   everything built after it, cheapest to get right first.
2. **Tag Taxonomy Enforcement**, then **Topic Tagging** — same input file,
   natural pair; Tag Taxonomy Enforcement's own mechanical-repair step can
   immediately backfill the real `kind/opportunity` gap from §3.2 above.
3. **Commitment Tracking**, **Contact Enrichment and Coverage** — both
   ready once re-baselined, independent of each other and of Opportunities.
4. **Fact Decay Watch** — spec alongside the above; provision
   `research-agent`'s own gateway as part of its own build task.
5. **Opportunity Discovery** + **Opportunity Health** — once the other
   session's Opp-shaping work lands; fold the §3 fixes into whichever
   story touches `track-opportunities` next, rather than a separate pass.

Not yet run through `/spec` — this is the draft to react to before any of
it becomes a real requirement/story.
