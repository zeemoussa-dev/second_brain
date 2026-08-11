# REVIEW QUEUE

Live human inbox. Items here are awaiting a human decision before the pipeline can
proceed. Remove an item when it is resolved; add an `ESCALATIONS.md` entry if the
resolution involved a backward step.

<!-- Entry format:
- [ ] YYYY-MM-DD · **STORY-ID or SPRINT-ID** · one-line summary of what's needed
  Plain English: what's blocked, why, what the impact is if left unresolved.
  **What to do:** the concrete next step — command to run or decision to make.
  → `Implementation/UserStories/<file>.md` or `Implementation/Sprints/<file>.md`
-->

- [ ] 2026-08-10 · **SPRINT-001** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-001 (REQ-SB-07, scheduled recurring email capture) is
  Done — all 4 tasks built and verified live. The coder drafted a
  Retrospective (sizing accuracy, what worked/didn't, patterns/antipatterns,
  open follow-ups) in the sprint file, but does not write
  `Implementation/Learnings.md` directly — that's a human step.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" and "Antipatterns
  to avoid" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-001-scheduled-recurring-capture.md`

- [ ] 2026-08-11 · **SPRINT-002** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-002 (REQ-SB-14, vault graph connectivity) is Done —
  all 4 tasks built and verified live (customer hub notes now exist,
  existing and new notes carry wikilinks to them, manual hub-note content
  survives reruns). The coder drafted a Retrospective, but does not write
  `Implementation/Learnings.md` directly — that's a human step.
  **What to do:** read `## Retrospective` in the sprint file, then copy
  (verbatim or expanded) the "Patterns to carry forward" entries into
  `Implementation/Learnings.md` (no new antipatterns this sprint).
  → `Implementation/Sprints/SPRINT-002-vault-graph-connectivity.md`

- [ ] 2026-08-11 · **SPRINT-003** · skim the sprint retrospective and harvest learnings
  Plain English: SPRINT-003 (REQ-SB-15, Obsidian manual-entry templates +
  in-vault guide) is Done — both tasks built and verified (four templates,
  one guide note, all matching the resolved schema). The coder drafted a
  Retrospective, but does not write `Implementation/Learnings.md` directly.
  The Obsidian Settings → Templates → "Template folder location" step is
  now done (operator confirmed 2026-08-11) — only the Learnings harvest
  remains open.
  **What to do:** read `## Retrospective` in the sprint file and copy the
  "Patterns to carry forward" entries into `Implementation/Learnings.md`.
  → `Implementation/Sprints/SPRINT-003-manual-entry-templates-and-guide.md`


- [ ] 2026-08-11 · **Prototype update (round 6): Agents Map KB grown + entire radial scale rebalanced for real spacing** · needs browser sign-off
  Plain English: this is the same not-yet-approved REQ-SB-12/REQ-SB-13 prototype
  pass. Round 3 rebuilt `agents-map.html` as a true polar/radial grid — angular
  axis = sections (Capture/People/Q&A, virtual boundary only, no filled wedge),
  radial axis = 3 concentric rings global across every section, one per agent
  type (Worker outermost, Expert middle, Producer innermost); agents connect to
  each other and their section's Hub, only the Hub connects to the KB. Round 4
  fixed a confirmed container-sizing bug (independently re-verified by the
  operator, 226px measured) — untouched since. Round 5 moved Hubs from the outer
  rim to the inner ring, close to the KB, per the operator's explicit direction.
  Round 6 (this update) is a **scale/spacing rebalance, not another direction
  change** — round 5's inner-ring Hub placement is preserved, it just now has
  real breathing room. The operator measured directly (`getBoundingClientRect()`)
  and confirmed the KB itself was correctly centered and exactly 22% wide as
  coded (no centering bug) — the real problem was spacing: round 5's Hubs at
  r=19 sat only ~2.5%-of-canvas-radius from the KB's edge (~5.6px measured on a
  226px canvas), three 11%-wide Hub nodes crowding a KB too small (22%) to read
  as dominant. Fixed as one coordinated rebalance: (1) grew the KB from 22% to
  34% of canvas width (edge radius ~11 → ~17) and rebuilt the brain substantially
  denser — 23 neurons (16 outer + 6 mid + 1 center), up from 14, ~42 crossing
  synapse lines (up from ~26), varied neuron size/opacity across 3 depth layers,
  a stronger glow (drop-shadow blur 16px→26px, `kbPulse`'s peak spread
  28px→42px); (2) recomputed the entire radial scale outward, by the same
  angle×radius trigonometry every prior round used (not eyeballed), so nothing
  collides now the KB is bigger — Hub band r=19→32 (edge-to-edge KB-Hub gap is
  now ~9.5 units, ~19% of the canvas radius — the explicit "comfortable
  double-digit percentage" target), Producer ring r=18→30, Expert ring r=30→45,
  Worker ring r=42→50, boundary r=54→58; every dependent coordinate — all 3 Hub
  positions, all 5 agent positions, every `.spoke-line`, every `.cluster-line`,
  the ring/section-title label positions — recomputed from the new radii, none
  left pointing at stale round-5 coordinates. Hand-verified: KB-edge-to-Hub-edge
  ~9.5 units (19%, comfortable double-digit); KB-edge-to-Producer-ring-agent-edge
  ~8 units (16%); both same-angle Hub-vs-that-section's-own-agent pairs
  (Capture/Q&A) re-checked with positive clearance beyond the 10.5-unit
  combined-radii minimum (7.5 and 2.5 units respectively). The round-4
  canvas-sizing fix (`.agents-map-stage` padding / `.agents-map-canvas`
  min-width) is **untouched** — independently re-verified working by the
  operator before this round started, and nothing this round touches that CSS.
  REQ-SB-13's per-agent click → side-panel behavior is unchanged; the round 2
  light/green theme is unchanged.
  **What to do:** open `html-prototype/agents-map.html` in a browser and confirm
  the Knowledge Base now reads as the dominant visual anchor (substantially
  bigger, denser brain), with real visible breathing room between it and the
  Hub band, and Hubs still close to the KB per round 5's direction — not
  crowding it. `my-day.html`/its four drill-downs/`settings.html` are unchanged
  since round 2 (still worth a pass if not yet reviewed). Use each page's
  state-switcher buttons to review every buildable state. Once approved, run
  `/spec` on REQ-SB-12 and REQ-SB-13.
  → html-prototype/agents-map.html
  → html-prototype/my-day.html
  → html-prototype/my-day-emails.html
  → html-prototype/my-day-calendar.html
  → html-prototype/my-day-todo.html
  → html-prototype/my-day-reads.html
  → html-prototype/settings.html
