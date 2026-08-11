# agentic-map → Second Brain: requirement port classification

**Date:** 2026-08-10
**Source:** `C:\myWorx\Projects\agentic-map\REQUIREMENTS.md` (76 pre-existing
entries, REQ-001…REQ-091 with gaps at REQ-085/REQ-088) as it stood on this date.
**Purpose:** Second Brain is described as an "upgrade" of agentic-map, reusing
its requirements/stories but swapping tooling (Hermes for messaging, Obsidian
for the KB) and dropping the staging→canonical promotion model entirely (see
[MEMORY.md](../../MEMORY.md)). agentic-map is a much broader multi-domain
personal assistant (sales pipeline, Outlook triage, a map-visualization
console, cron digests, meeting assistance); most of its 76 requirements don't
describe a personal knowledge-base tool at all. This file walks every entry
and records a verdict, mirroring the judgment-call precedent agentic-map's own
`REQ-095` set for reclassifying `GAPS.md`.

**Verdicts:**
- **Port** — maps directly onto a Second Brain requirement, tools swapped.
- **Adapt** — same underlying need, but reshaped enough that the Second Brain
  version will read differently from the source.
- **Drop** — describes a capability outside Second Brain's scope (sales,
  Outlook, the agent-routing console, multi-agent orchestration Hermes itself
  owns).
- **Already covered** — the scaffold already ships this (versioning, delivery
  methodology, typed logs).
- **Open question** — plausibly in scope but a real product call, not a
  mechanical port; needs the operator's decision before it becomes a `REQ-SB-NN`.
- **Note only** — not a candidate for porting, but evidence worth keeping (e.g.
  agentic-map itself moving *away* from staging for one channel).

---

## Verdict summary

| Verdict | Count | IDs |
|---|---|---|
| Port | 2 | REQ-008, REQ-015 |
| Adapt | 6 | REQ-007, REQ-009, REQ-016, REQ-042, REQ-047, REQ-078 |
| Open question | 2 | REQ-019, REQ-035 |
| Already covered | 3 | REQ-012, REQ-013, REQ-014 |
| Note only | 2 | REQ-055, REQ-058 |
| Drop | ~63 | everything else |

The overwhelming majority drops out because agentic-map is a multi-domain
assistant (sales, customers, productivity/mail, a map-style console, agent
orchestration) and Second Brain is, per `CLAUDE.md`, specifically "index and
serve the user's Obsidian vault" plus a Hermes channel — not a rebuild of
agentic-map's whole surface.

---

## Port (direct, tools swapped)

| ID | Title | Second Brain target |
|---|---|---|
| REQ-008 | Hybrid KB search — make retrieval relevant to real queries | Strengthens `REQ-SB-02` (Browse & Search) — search quality technique, not scope |
| REQ-015 | OpenClaw-based needs (multi-channel messaging integration) | Directly = `REQ-SB-03` (Conversational Agent Access via Hermes) — this *is* the OpenClaw-era version of the same idea |

## Adapt (same need, reshaped)

| ID | Title | Why adapted, not ported as-is |
|---|---|---|
| REQ-009 | Chunk KB content before embedding, ahead of 10GB scale | Second Brain's MVP indexes frontmatter/wikilinks/tags, not embeddings yet — this becomes a P1/P2 concern once semantic search is wanted, not an MVP one |
| REQ-016 | `kb_read` tool implementation | Becomes the P1 agent's read access into the vault via Hermes — same concept, no Postgres/Qdrant backing |
| REQ-042 | KB reranking stage | Search-quality refinement, likely P2, once basic search (REQ-SB-02) exists to refine |
| REQ-047 | Provision-from-scratch: one flow to stand up an empty, valid system | Low-priority dev-tooling nicety given this session's manual `.venv`/portable-Node setup — a single setup script, not a requirement on the level of the others |
| REQ-007 | One-click local dev launcher | Same bucket as REQ-047 — convenience tooling, not product scope |
| REQ-078 | Global search across mail, meetings, KB, and people | Narrows hard — Second Brain has no mail/meetings/people domains, so this collapses into "search across vault notes," which `REQ-SB-02` already covers. Listed here only so the narrowing is explicit, not silently dropped |

## Open questions (real product decisions) — RESOLVED 2026-08-10

| ID | Title | Decision |
|---|---|---|
| REQ-019 | `kb_write` tool implementation | **Allow writes.** A Hermes-connected agent may write back into the vault, not read-only. Ported as `REQ-SB-04` (P1) — needs its own AC around scope/confirmation, since this is a materially bigger trust surface than read access |
| REQ-035 | Upload data (docs/text/presentations) directly to an agent | **Add an ingest path.** Content can enter the vault through more than direct Obsidian editing. Ported as `REQ-SB-05` (P1) |

## Already covered by the scaffold

| ID | Title | Where |
|---|---|---|
| REQ-012 | Version number + changelog, visible in console and GitHub | `CHANGELOG.md` |
| REQ-013 | Adopt a delivery methodology (backlog + sprints + exception gating) | `Implementation/Pipeline.md` |
| REQ-014 | Split the backlog into typed Requirements/Bugs/Gaps logs | `BACKLOG.md` / `BUGS.md` |

## Note only (not ported, but relevant evidence)

| ID | Title | Why it matters here |
|---|---|---|
| REQ-055 | Mail sync writes straight to canonical (no staging/promote gate) | agentic-map itself later moved *away* from staging for at least one channel — independent precedent supporting Second Brain's own no-staging decision, not something to port as a requirement |
| REQ-058 | Compass Expert: initial + autonomously-refreshed KB from real Compass documentation | Naming collision worth flagging explicitly: this is agentic-map's own expert agent for *Core42 Compass's product docs* — a different thing from "Core42 Compass API as the LLM backing Second Brain's agents" (the P1 direction from this session's earlier discussion). Don't conflate the two when discussing "Compass" going forward |

## Drop (out of scope for a personal Obsidian second brain)

Sales/customers/pipeline domain: REQ-079, REQ-080, REQ-081, REQ-082, REQ-083,
REQ-084, REQ-086, REQ-089, REQ-090, REQ-091, REQ-074, REQ-077, REQ-056,
REQ-061, REQ-043.

Productivity/mail/meetings domain: REQ-005, REQ-031, REQ-038, REQ-052,
REQ-054, REQ-057, REQ-062, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068,
REQ-069, REQ-070, REQ-071, REQ-072, REQ-073, REQ-075.

Agent-routing / multi-agent orchestration (Hermes's job, not ours, per
`MEMORY.md`'s existing Hermes constraint): REQ-001, REQ-002, REQ-003, REQ-004,
REQ-017, REQ-018, REQ-020, REQ-021, REQ-022, REQ-026, REQ-033, REQ-034,
REQ-036, REQ-037, REQ-039, REQ-040, REQ-041, REQ-044, REQ-046, REQ-076,
REQ-087.

Console / map-visualization UI (a completely different UI concept from
Second Brain's notes browser, per `html-prototype/`): REQ-006, REQ-010,
REQ-011, REQ-023, REQ-024, REQ-025, REQ-027, REQ-028, REQ-029, REQ-030,
REQ-032, REQ-048, REQ-051, REQ-060, REQ-063.

Staging/promotion mechanics (explicitly the thing being removed):
REQ-024 (Discard button in Review queue), REQ-049, REQ-050, REQ-053, REQ-059,
REQ-045.

Infra scale concern not applicable at personal-vault scale: REQ-045.

---

## Resulting `REQ-SB-NN` mapping

| Second Brain ID | Phase | Title | Source |
|---|---|---|---|
| REQ-SB-01 | MVP | Vault Indexing | (native to Second Brain, not ported) |
| REQ-SB-02 | MVP | Browse & Search | native, strengthened by REQ-008 (hybrid search) |
| REQ-SB-03 | P1 | Conversational Agent Access via Hermes | REQ-015 (port) + REQ-016 (`kb_read`, adapt) |
| REQ-SB-04 | P1 | Agent Vault Write Access | REQ-019 (adapt, scope decision above) |
| REQ-SB-05 | P1 | Content Ingestion Path | REQ-035 (adapt, scope decision above) |

REQ-009 (chunking) and REQ-042 (reranking) are deferred to P2 as search-quality
refinements once basic search exists to refine. REQ-007/REQ-047 (dev-tooling
niceties) are not PRD material — track them as ad hoc infra work if/when
pursued, not a requirement.

Drafted directly into `Documentation/PRD.md` and indexed in `BACKLOG.md` — see
those files for the authoritative current text.
