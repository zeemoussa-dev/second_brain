# Authoring a Template

**A new note type is a new `Template.json`, never new code.** That is the whole
point of the vault engine — if you find yourself writing a script to produce a
new kind of note, stop and write a Template instead.

Verified against `src/backend/app/vault/vault_manager.py`, 2026-09-04.

---

## What a Template controls

A Template is a small JSON file that tells the engine how one *kind* of note
behaves: where it lands, what its filename looks like, whether a repeat call
updates or duplicates, which sections exist, who is allowed to write each one,
and what frontmatter every note of that kind carries.

## Where Templates live

| Consumer | Path |
|---|---|
| The backend | `<SECOND_BRAIN_DATA_PATH>/data/Templates/<id>/Template.json` |
| A Hermes Skill's own copy of the engine | `<vault>/.second-brain/data/Templates/<id>/Template.json` |

The folder name **is** the template id. Nothing registers a Template — dropping
the file in is enough, and it takes effect on the next read (no caching).

## The complete key list

These are the only keys the engine reads. Anything else you add is ignored.

| Key | Default | Effect |
|---|---|---|
| `id` | — | Template id; must match the folder name |
| `note_name` | — | Subfolder under `Work/`. `"Threads"` → `Work/Threads/…` |
| `on_missing` | `"create"` | `"create"` makes the note when absent. `"error"` refuses — use it when a note **must** already exist and silently creating one would be a bug |
| `on_existing_title` | `"update_section"` | `"update_section"` means a call with the same title updates that note in place. Any other value means every call makes a new file |
| `note_own_folder` | `false` | Give each note its own folder, so attachments and related files sit beside it |
| `note_filename_plain` | `false` | Drop the `YYYY-MM-DD-` prefix from the filename |
| `sections` | `[]` | `[{ "name": str, "access": str }]` — see below |
| `frontmatter_defaults` | `{}` | Merged into every note's frontmatter at creation |

## Where notes land

```
Work/<note_name>/<YYYY-MM-DD>-<Title>.md                        # default
Work/<note_name>/<YYYY-MM-DD>-<Title>/<YYYY-MM-DD>-<Title>.md   # note_own_folder: true
```

The root is **`Work/`**, not `Notes/`.

## Identity — the part that makes re-runs safe

Frontmatter **`id`** is the stable key: a caller-supplied external id (a
conversation id, a calendar event id) or an auto-generated uuid4. The engine also
stamps `title` and `created`.

**Key on a real external id and re-running a capture becomes idempotent** — the
engine finds the existing note and updates it rather than writing a second copy.
Key on nothing and every run duplicates. This is the single most important
decision when designing a Template.

Renaming is `update(id, title=...)` — nothing moves on disk and no backlink
breaks.

## Section access — a real guarantee, not a convention

Each section declares an `access`. The vocabulary is:

| Value | Meaning |
|---|---|
| `machine_write` | Automated callers may write it |
| `human_only` | **The engine refuses** an automated write — `_require_machine_write` raises |
| `public` | Open |

`human_only` is structural. An agent cannot write one no matter what its prompt
says, which is a stronger guarantee than any instruction.

> **Trap: an undeclared section defaults to `machine_write` (open).** A section
> you want protected must be declared explicitly. Omitting it does not protect
> it.

Vault convention: `## Actions` and `## Personal Notes` are the human-owned
sections.

## The two ways a note gets written

```python
create(vault_path, template, note_name, title,
       note_id=..., frontmatter=..., sections={...})
```

Makes a note. Use when you know it does not exist yet.

```python
modify_section(vault_path, template, note_id, section, content, mode,
               note_name=..., title=...)
```

**"Create if it does not exist, otherwise update this section"** — in one call.
`mode` is `"replace"` or `"append"`. Omit `note_name`/`title` to get
"must already exist" behaviour regardless of `on_missing`.

This single call is usually all a capture needs.

## Worked example — `email-thread`

A threaded source is **one note per thread**, keyed on the provider's own
conversation id, with messages appended:

```json
{
  "id": "email-thread",
  "note_name": "Threads",
  "on_missing": "create",
  "on_existing_title": "update_section",
  "note_own_folder": true,
  "note_filename_plain": false,
  "sections": [
    { "name": "Summary",        "access": "machine_write" },
    { "name": "Messages",       "access": "machine_write" },
    { "name": "Actions",        "access": "human_only" },
    { "name": "Personal Notes", "access": "human_only" }
  ],
  "frontmatter_defaults": {
    "kind": "thread",
    "source": "email",
    "participants": [],
    "last_message_at": ""
  }
}
```

Each incoming message is one call:

```python
modify_section(vault_path, template,
               note_id=conversation_id,        # the idempotency key
               section="Messages",
               content=rendered_message,
               mode="append",
               note_name="Threads", title=subject)
```

First call creates the thread; every later call on the same conversation id
appends to the same note. `Actions` and `Personal Notes` stay yours.

The same shape fits any threaded source — chat, tickets — not just email.

## How to test a Template before trusting it

Run it against a scratch vault, not the real one. Copy the Template into
`<scratch>/data/Templates/<id>/`, then check the three things that actually
matter:

1. **Does a second call on the same `id` append, or duplicate?**
   Expect `created: False, updated: True` and the same path.
2. **Is `human_only` enforced?** A write to one must raise `VaultManagerError`.
3. **Does the note look right?** Read the file, do not infer it from return
   values.

## Known limits of the current engine

- **No child notes in this copy.** `create_dynamic_child()` and per-caller access
  exist only in the canonical engine at `Hermes-Provisioning/shared/vault_manager.py`,
  which is held outside the working tree by default. So a "container note with one
  child note per item" shape is **not** available in
  `src/backend/app/vault/vault_manager.py` as it stands — use one note plus an
  appended section, or ask for the canonical engine to be brought back.
- **The backend copy resolves Templates without the `.second-brain` prefix**,
  because it is passed `second_brain_data_path` directly. A comment in the file
  says to re-apply that line if the engine is ever re-copied from a canonical
  source — do not silently overwrite it back.
