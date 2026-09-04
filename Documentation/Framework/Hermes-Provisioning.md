# `Hermes-Provisioning/` — what needs it, and when to bring it back

`Hermes-Provisioning/` is the canonical source for the Hermes side of the system:
the Skills, the shared engine, and the provisioning config. It **exists** — it is
just deliberately **held outside the working tree** (operator, 2026-09-04) so it
is not read as a standing part of the project on every task.

**This page is the contract for that arrangement:** it lists exactly what depends
on the folder, so it can be brought back for a specific job and taken away again
afterwards, instead of living in the checkout permanently.

Verified against the code, 2026-09-04.

---

## Real code dependencies — exactly three

These resolve a filesystem path at runtime. Everything else that mentions
`Hermes-Provisioning` is a comment or docstring with no runtime effect.

| # | Where | What it resolves | What happens while the folder is absent |
|---|---|---|---|
| 1 | `src/backend/app/data_access/skills.py:17` | `Hermes-Provisioning/skills` — **all Skill content** | `GET /skills` returns `[]` **silently**. No error, no warning. |
| 2 | `src/backend/app/data_access/indexes.py:26` | `.../vault-rebuild/vault-index/scripts` — the index-builder source copied into a profile on deploy | Reading Indexes is unaffected (that reads `<data>/data/Indexes/`). Only **deploying** the builder into a Hermes profile breaks. |
| 3 | `tools/hermes_backup.py:274` | `Hermes-Provisioning/skills` — the canonical Skill-id list | ⚠️ **Returns an empty set, so a `.sbb` backup bundles ZERO Skills — silently.** |

### The one that can actually hurt you

**#3.** `hermes_backup.py` only bundles a profile's Skill folder if its id appears
in the canonical list derived from `Hermes-Provisioning/skills/`. With the folder
absent that list is empty, so the backup completes normally, reports success, and
contains **no Skills at all**.

> **Bring the folder back before taking any `.sbb` backup you intend to restore
> from.** A backup taken without it looks fine and is not.

---

## Non-code dependencies — the work that needs it

| Task | Why |
|---|---|
| **Deploying a Skill to a Hermes profile** | The Skill content is the thing being copied. A Skill is inert until copied into a real profile — editing anywhere else does nothing to a live install. |
| **Child-note vault shapes** | `create_dynamic_child()` and per-caller section access live only in the canonical `Hermes-Provisioning/shared/vault_manager.py`. The backend's copy is an older engine without them — see [Templates.md](Templates.md). |
| **Re-provisioning Hermes from scratch** | `config/custom_providers.yaml` carries the verified Compass provider entry, including the `base_url` form that avoids the double-append 404. Not needed once a machine's `config.yaml` is already set up. |
| **Re-syncing the shared engine** | When `vault_manager.py` changes canonically, every deployed copy needs re-copying. That is a fan-out across profiles, and the canonical file is the source. |
| **Taking a `.sbb` backup** | See #3 above. |

---

## When you do *not* need it

Most work. Specifically:

- Anything in `src/backend` or `src/frontend` — the app runs fine without it.
- Authoring or testing a **Template** — Templates live in
  `<SECOND_BRAIN_DATA_PATH>/data/Templates/`, not here.
- Reading or writing notes through the vault engine.
- Sections, Agents, Pipelines, Providers, Indexes — all read from the app
  database folder.

---

## The tell

If Skills unexpectedly come back **empty** — in the UI, from `GET /skills`, or
inside a backup — that is almost always this, not a bug and not an empty system.
Check whether the folder is present before investigating anything else.
