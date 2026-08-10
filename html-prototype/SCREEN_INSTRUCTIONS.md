# Building a prototype screen

Canonical how-to for adding or changing a screen in this directory. Read this
before touching any screen — the `designer` agent reads it every time.

## Ground rules

- **No build step.** Plain HTML/CSS/JS, opened directly in a browser via
  `index.html` or any screen file.
- **`styles.css` is the single source of truth** for colour, typography, spacing,
  and shared components (`.card`, `.badge`, `.btn`, `.input`, the `.app-shell`
  layout). Reuse these tokens and classes before inventing anything new. If a
  genuinely new pattern is needed, add it to `styles.css` first so it's reusable,
  not just to the one screen that needed it.
- **One file per screen**, named for what it shows (e.g. `notes-browser.html`,
  `search.html`, `note-detail.html`), linked from `index.html`.
- **Every screen uses the shared shell**: a `.app-shell` div containing `.sidebar`
  (nav) and `.main` (content) — see `index.html` for the reference structure.

## Design-rationale breadcrumb

At the top of every screen file you create or change, add an HTML comment noting:
what changed, which existing patterns you reused, and any net-new pattern
introduced. Example:

```html
<!--
  Screen: Notes Browser (REQ-SB-03)
  Reused: .app-shell, .card, .badge-success
  New: .note-graph-mini (small inline graph preview) — added to styles.css
-->
```

## Buildable states

Draw states the real data model can actually produce — empty/first-run (no vault
configured yet), a vault with notes but none indexed yet, normal populated state,
and any error state (vault path invalid, parse failure on a malformed note). Don't
mock up a state the architecture can't produce.

## When you're done

Every design pass gets flagged to `REVIEW-QUEUE.md` for human browser sign-off —
this is mandatory, not optional (see `.claude/agents/designer.md`). Never mark a
prototype pass "clear."
