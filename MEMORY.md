# MEMORY

Append-only log of decisions, patterns, and constraints discovered during delivery.
Updated by Claude when a task produces a new rule or constraint worth preserving
across sessions.

**Protocol (from CLAUDE.md):**
- Decisions → `## Decisions` — format: `[date] Decision – Reason`
- Patterns → `## Patterns` — format: `Pattern name – description`
- Constraints → `## Constraints` — format: `Constraint – reason`
- Do NOT add logs, chat transcripts, or debugging output.

---

## Decisions

- [2026-08-10] No staging/promotion gate on ingested vault data – Second Brain
  indexes the user's own trusted Obsidian vault, not agent-written scratch data;
  the two-tier staging→canonical model `agentic-map` uses (its invariant 4) does
  not apply here and is intentionally not replicated.
- [2026-08-10] Standalone project, no agentic-map integration built yet – future
  integration (agentic-map's agents querying this KB) is a deliberately separate,
  later decision, not part of this project's initial scope.

## Patterns

<!-- Pattern name – what it means and when to apply it -->

## Constraints

- Hermes (external MCP-based multi-channel communication tool) is an integration
  point, not something this project builds — treat it as a dependency with its own
  interface, not code to implement here.
