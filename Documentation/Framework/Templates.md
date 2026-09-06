# Authoring a Template

**A new note type is a new `Template.json`, never new code.** That is the whole
point of the vault engine — if you find yourself writing a script to produce a
new kind of note, stop and write a Template instead.

---

## Read this first: there are TWO schemas, and two engines

This is the thing that bites. A Template written for one engine **will not load**
in the other — it is a schema-version mismatch, not a content mismatch.

| | **v2** — two-layer | **v1** — flat |
|---|---|---|
| Read by | `Hermes-Provisioning/shared/vault_manager.py` — **every Skill** | `src/backend/app/vault/vault_manager.py` — **the backend** |
| Shape | `identity` / `on_missing` / `allow_create_folder` at top, everything else nested under **`root`** | every key at the top level |
| Child notes | **yes** — `root.children` with `growth: "dynamic"` | no |
| `note_name` | a **`create()` parameter** | a **template key** |
| Per-caller access | yes (`allowed_callers`) | no |

**Write v2 unless you are specifically targeting the backend.** Capture pipelines
run as Skills, so they use v2. The backend's engine is older and has not been
brought forward yet — see [Hermes-Provisioning.md](Hermes-Provisioning.md).

The v2 engine's own docstring puts it plainly: *"a template is TWO layers, not one
flat object"*, where `root` is "today's entire old flat schema, unchanged in
substance, just nested".

Verified against both engines, 2026-09-05.

## Where Templates live

| Consumer | Path |
|---|---|
| The backend | `<SECOND_BRAIN_DATA_PATH>/data/Templates/<id>/Template.json` |
| A Skill (v2 engine) | `data_root()/data/Templates/<id>/Template.json` — `SECOND_BRAIN_DATA_PATH` if set, else `<vault>/.second-brain` |

The folder name **is** the template id. Nothing registers a Template — dropping
the file in is enough, and it takes effect on the next read (no caching).

---

## v2 — the current schema

### Top level

| Key | Default | Effect |
|---|---|---|
| `id` | — | Must match the folder name |
| `identity` | `{"strategy": "id"}` | How an existing record is found. **An object, not a string** |
| `on_missing` | `"create"` | `"error"` refuses to create — use it when a note *must* already exist |
| `allow_create_folder` | `true` | May the containing folder be auto-created, or is a missing one an error |
| `parent` | — | For a child *template*; supplies `child_subpath` so `create()` derives `note_name` itself |

### `root` — the note itself

| Key | Default | Effect |
|---|---|---|
| `type` | `"md"` | Node type. **Not** a domain label — leave it `"md"` |
| `sections` | `[]` | `[{ "name", "access", "allowed_callers"? }]` |
| `frontmatter_defaults` | `{}` | Merged into every note's frontmatter |
| `on_existing_title` | `"update_section"` | Same title updates in place; anything else always makes a new file |
| `own_folder` | `false` | Give each note its own folder so attachments sit beside it |
| `plain_filename` | `false` | Drop the `YYYY-MM-DD-` prefix |
| `plain_folder` | `false` | Same, for the folder name |
| `children` | `[]` | See below |
| `children_index_section` | — | The section children get wikilinked into |

**`note_name` is not a v2 template key.** It is passed to `create()`:

```python
create(vault_path, template, title, note_name="Threads", note_id=conversation_id, ...)
```

### Child notes — `root.children`

This is what v2 adds and v1 cannot do: real per-item notes inside the parent's
folder, rather than everything appended into one section.

| Key | Effect |
|---|---|
| `name` | The child name you pass to `create_dynamic_child` |
| `growth` | Must be `"dynamic"` — the engine looks it up by this |
| `folder` | Subfolder under the parent's own folder, e.g. `messages` |
| `identity_fields` | **The natural key.** Same values → same existing note, never a duplicate |
| `frontmatter_defaults` | Merged into each child |
| `sections` | Optional. If absent, write a flat `body` instead |

```python
create_dynamic_child(vault_path, template, root_id=conversation_id,
                     child_name="messages",
                     identity={"conversation_id": ..., "message_id": ...},
                     frontmatter={"title": "2026-09-04 09:12 alice@example.com"},
                     body=message_text)
```

`body` and `sections` are **mutually exclusive** — pass `body` for a child whose
template declares no sections (a plain email body has no `## Headers`), and
`sections` for one that does.

**Filenames come from frontmatter `title`**, falling back to the joined identity
values. Put the real timestamp *and* sender in the title: date alone collides,
and a folder of same-day messages becomes indistinguishable. Note the engine also
prefixes the **capture** date, so a backfill shows capture date + received time.

---

## v1 — the backend's older schema

Flat. Same ideas, fewer of them.

| Key | Default |
|---|---|
| `id`, `note_name` | — |
| `on_missing` | `"create"` |
| `on_existing_title` | `"update_section"` |
| `note_own_folder`, `note_filename_plain` | `false` |
| `sections` | `[]` — `[{ "name", "access" }]` |
| `frontmatter_defaults` | `{}` |

Notes land at `Work/<note_name>/<YYYY-MM-DD>-<Title>.md`. The root is **`Work/`**,
not `Notes/`.

---

## Identity — the part that makes re-runs safe

Frontmatter **`id`** is the stable key: a caller-supplied external id (a
conversation id, a calendar event id) or an auto-generated uuid4. The engine also
stamps `title` and `created`.

**Key on a real external id and re-running a capture is idempotent** — the engine
finds the existing note and updates it rather than writing a second copy. Key on
nothing and every run duplicates. This is the single most important decision when
designing a Template. For child notes the equivalent is `identity_fields`.

Renaming is `update(id, title=...)` — nothing moves and no backlink breaks.

## Section access — a real guarantee, not a convention

| Value | Meaning |
|---|---|
| `machine_write` | Automated callers may write it |
| `human_only` | **The engine refuses** an automated write — it raises |
| `public` | Open |

`human_only` is structural. An agent cannot write one no matter what its prompt
says. In v2 a section may also declare `allowed_callers` to narrow it to specific
callers.

> **Trap: an undeclared section defaults to `machine_write` (open).** Protection
> is opt-in. Omitting a section does not protect it.

Vault convention: `## Actions` and `## Personal Notes` are the human-owned ones.

## The two ways a note gets written

```python
create(vault_path, template, title, note_name=..., note_id=..., sections={...})
modify_section(vault_path, template, note_id, section, content, mode, ...)
```

`modify_section` is **"create if it does not exist, otherwise update this
section"** in one call. `mode` is `"replace"` or `"append"`. Omit `note_name`/
`title` to force "must already exist". That single call is usually all a capture
needs.

---

## Worked example — `thread` (v2, in production use)

One note per thread, keyed on the provider's conversation id, with **real
per-message child notes**:

```json
{
  "id": "thread",
  "identity": { "strategy": "id" },
  "on_missing": "create",
  "allow_create_folder": true,
  "root": {
    "type": "md",
    "own_folder": true,
    "on_existing_title": "update_section",
    "children_index_section": "Messages",
    "frontmatter_defaults": {
      "kind": "thread", "source": "email",
      "participants": [], "last_message_at": "", "last_summarized_at": ""
    },
    "sections": [
      { "name": "Summary",        "access": "machine_write" },
      { "name": "Messages",       "access": "machine_write" },
      { "name": "Related",        "access": "machine_write" },
      { "name": "Actions",        "access": "human_only" },
      { "name": "Personal Notes", "access": "human_only" }
    ],
    "children": [
      {
        "name": "messages",
        "growth": "dynamic",
        "folder": "messages",
        "identity_fields": ["conversation_id", "message_id"],
        "frontmatter_defaults": { "kind": "message", "source": "email" }
      }
    ]
  }
}
```

Produces:

```
Work/Threads/2026-09-05-Q3 renewal/
  2026-09-05-Q3 renewal.md
  messages/
    2026-09-05-2026-09-04 09-12 alice@example.com.md
    2026-09-05-2026-09-04 10-40 bob@example.com.md
```

The same shape fits any threaded source — chat, tickets — not just email.

## How to test a Template before trusting it

Run it against a scratch vault, never the real one. Point
`SECOND_BRAIN_DATA_PATH` at the scratch config folder, copy the Template in, then
check the things a mistake actually breaks:

1. **Does it load?** Both schema errors below fail here, loudly.
2. **Does a second call on the same id duplicate?** Re-ingest the same item and
   count the files. Expect no growth.
3. **Is `human_only` enforced?** A write to one must raise.
4. **Read the note.** Do not infer it from return values.

## Two schema errors worth knowing

Both were hit authoring the `thread` template, and both fail at load:

- **`"identity": "id"`** → `AttributeError: 'str' object has no attribute
  'setdefault'`. It must be an **object**: `{"strategy": "id"}`.
- **`root.type` as a domain label** (`"thread"`) — it is a *node type* and
  defaults to `"md"`. Leave it alone.
