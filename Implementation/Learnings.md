# Learnings

Append-only cross-sprint index of patterns and antipatterns harvested from sprint
retrospectives. Populated by the **human** from the coder's drafted retro. Read
this at the start of every new sprint.

<!-- Entry format:
## YYYY-MM-DD — SPRINT-NNN
### Patterns (do more of this)
- Pattern name — context and why it worked

### Antipatterns (avoid this)
- Antipattern name — context and why it hurt

### Sizing calibration
- Estimated vs. actual — takeaway for future sprint sizing
-->

## 2026-08-10 — Book reference, not a sprint retro

No sprint has run yet — this entry deviates from the file's own protocol
(harvested from retros, human-propagated) at the operator's explicit
request, since *Beyond the Second Brain* (Mo Elkholy) produced real
heuristics worth having on hand before the first retro exists. Source:
`Documentation/References/beyond-the-second-brain-methodology.md`. Treat
this entry as provisional against real sprint experience, not as
equivalent-weight to a harvested retro.

### Patterns (do more of this)

- **Tags for multidimensional attributes, folders only for single-home
  ones** — confirmed live via `ADR-004`: `Customer` (multi-valued, can
  change) became a tag; `Kind` (stable, single-valued) stayed a folder.
  Apply the same test to any future categorization axis before adding a
  folder level for it.
- **Self-explanatory notes ("context is the currency")** — a note destined
  to feed an AI synthesis session should be understandable without the
  conversation that produced it. Worth applying explicitly once synthesis
  features exist, not just capture ones.
- **Forward-only linking** — Obsidian computes backlinks automatically from
  `[[wikilinks]]`; the conversation-thread linking only writes a link on
  the *newer* note, never edits older ones. Prefer this shape (write once,
  let the graph compute the reverse) over any pattern that requires
  updating multiple existing notes when a new one arrives.
- **Design for the extensibility point, not the enum** — `kind`/`customer`
  are Compass-proposed and vault-derived, never a hardcoded list. When a
  future classification axis appears, prefer "read what's already there,
  let the model propose new values" over enumerating options in code.

### Antipatterns (avoid this)

- **Raw capture treated as a finished note** — every note so far is a full
  raw email body, not a distilled one-idea note (the book's "atomic notes"
  principle). Not yet fixed; flagged so it isn't mistaken for done.
- **Entity-first structure with no output orientation** — the vault
  organizes around *who* (Customer) with nothing yet organized around
  *what gets produced* (a decision, an account plan, a proposal). The book
  calls a topic/entity taxonomy that maps to no output "the design trap."
- **Assuming a natural key is unique** — date+subject collided in
  production (two same-day duplicate notifications overwrote each other).
  Always include a genuinely unique identifier (e.g. source system ID) in
  any generated filename/key, even when a collision seems unlikely.
