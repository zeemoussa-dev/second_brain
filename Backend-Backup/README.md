# Backend Backup — 2026-08-20

A full, byte-for-byte copy of `src/backend` as it stood on 2026-08-20,
taken before a proper architecture redesign (`ADR-059` — Hermes/LangGraph
pivot; see `MEMORY.md` "Decisions" and `Implementation/Architecture/
ADR.md`).

**Purpose:** the live `src/backend` is about to go through a real
architecture + documentation pass and will change shape substantially.
This folder is the safety net — a complete, working snapshot to copy
individual pieces back from as needed, rather than digging through git
history mid-redesign. Archive-never-delete applies here the same as
anywhere else in this project (`MEMORY.md`).

**Excluded from the copy** (regenerable / not backend code / secrets —
never duplicate a secret into a second location): `.venv/` (170MB,
rebuild via `requirements.txt`/`pyproject.toml`), `.env` (real Compass/
Anthropic/Outlook credentials — still only in `src/backend/.env`,
untouched), `__pycache__/` directories.

**What's included:** everything else, as-is — the full `app/` package
(including tonight's `_archive/` and the new Hermes client scaffold),
config files, and the untracked scratch/log files that happened to be
present at copy time (harmless to keep, not cleaned up here).

**Status of the live `src/backend`:** untouched by this backup — still
the exact same code, still fully runnable, confirmed via a real `python -c
"import app.main"` immediately after this copy was taken. Nothing has
been removed from the live tree yet; that's a deliberate, separate step
for the architecture pass itself, done together, not unilaterally.
