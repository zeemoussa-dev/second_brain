# Authoring a Template

**A new note type is a new `Template.json`, never new code.** That is the whole
point of the vault engine — if you find yourself writing a script to produce a
new kind of note, stop and write a Template instead.

Verified against the code, 2026-09-06.

---

## Masters ship; each install seeds its own copy

Templates are **Entity Templates** (also "Master Templates"). The product ships
them; every install gets its own copy.

| | Where |
|---|---|
| **Shipped master** | `src/backend/app/business/core/templates/masters/<id>/Template.json` |
| **This install's copy** | `<SECOND_BRAIN_DATA_PATH>/data/Templates/<id>/Template.json` |

`TemplateManager.seed_shipped_masters()` runs **on every boot** and installs any
master this install does not already have.

> **It never overwrites.** An id already present is kept exactly as it is —
> because it runs every boot, and overwriting would silently revert an operator's
> edit on every restart. Upgrading an existing template is a separate, deliberate
> act.
>
> **The trap that follows from that:** a hand-authored template **outranks the
> shipped master forever**. If you write your own `thread` before the master
> seeds, yours wins, silently, and every Skill that declares a write against a
> section yours happens to lack fails at deploy. If a master exists for the id you
> want, delete your local copy and let it seed rather than hand-authoring one.

The folder name **is** the template id, and there is no caching — a change takes
effect on the next read.

---

## Two schemas, and how the engine decides

Both are supported. `schema_version` says which:

| | **v2** — two-layer | **v1** — flat |
|---|---|---|
| Shape | `identity` / `on_missing` at top, the rest nested under **`root`** | every key at the top level |
| Child notes | **yes** — `root.children` | no |
| Key names | `own_folder`, `plain_filename` | `note_own_folder`, `note_filename_plain` |

**Write v2.** v1 is still parsed so older files keep working.

A file that does not declare `schema_version` is inferred from its shape — the
presence of `root` means v2. That inference is resolved **once**, deliberately,
and the reason is worth knowing:

> Reading v1 key names out of a v2 file **never raises**. Every `.get()` just
> returns its default. That is how the bug this replaced stayed invisible: all 11
> real templates parsed to **zero sections with `error: None`** — no failure, no
> warning, just silently empty. If a template's sections come back empty, suspect
> a schema mismatch before anything else.

---

## v2 reference

### Top level

| Key | Default | Effect |
|---|---|---|
| `id` | — | Must match the folder name |
| `schema_version` | inferred | `2`. Say it explicitly rather than relying on inference |
| `version` | — | The **content** contract — see below |
| `identity` | `{"strategy": "id"}` | How an existing record is found. **An object, not a string** |
| `on_missing` | `"create"` | `"error"` refuses to create — right when a note *must* already exist |
| `allow_create_folder` | `true` | May the containing folder be auto-created |
| `parent` | — | For a child template; supplies `child_subpath` so `create()` derives `note_name` itself |

### `root`

| Key | Default | Effect |
|---|---|---|
| `type` | `"md"` | Node type. **Not** a domain label — leave it `"md"` |
| `sections` | `[]` | `[{ "name", "access" }]` |
| `frontmatter_defaults` | `{}` | Merged into every note |
| `on_existing_title` | `"update_section"` | Or `"always_new"` — every call makes a new file |
| `own_folder` | `false` | Each note gets its own folder, so attachments sit beside it |
| `plain_filename` / `plain_folder` | `false` | Drop the `YYYY-MM-DD-` prefix |
| `children` | `[]` | See below |
| `children_index_section` | — | The section children get wikilinked into |

**`note_name` is not a v2 key.** It is passed to `create()`.

### `root.children` — real per-item notes

| Key | Effect |
|---|---|
| `name` | The child name passed to `create_dynamic_child` |
| `growth` | Must be `"dynamic"` |
| `folder` | Subfolder under the parent's own folder |
| `identity_fields` | **The natural key** — same values return the same note, never a duplicate |
| `frontmatter_defaults` | Merged into each child |
| `sections` | Optional; omit it and write a flat `body` instead |

```python
create_dynamic_child(vault_path, template, root_id=conversation_id,
                     child_name="messages",
                     identity={"conversation_id": ..., "message_id": ...},
                     frontmatter={"title": "2026-09-04 09:12 alice@example.com"},
                     body=message_text)
```

`body` and `sections` are **mutually exclusive**. Filenames come from frontmatter
`title`, falling back to the joined identity values — put the real timestamp *and*
sender in it, because date alone collides.

---

## `version` — the content contract, and what depends on it

Two version fields, deliberately distinct:

- **`schema_version`** — how to **parse** the file.
- **`version`** — what the **content** promises: which sections exist. Bump it
  when a section is removed or renamed.

A Skill's `writes:` entry may declare `requires: <n>`. `SkillManager` refuses the
deployment when that does not match the installed `template.version` — so a Skill
written against a section that has since been renamed fails at deploy time rather
than silently writing nowhere.

---

## Section access — declared by Skills, not by the Template

`allowed_callers` **no longer lives in a Template.** A Skill declares what it
writes, in its `SKILL.md` frontmatter:

```yaml
writes:
  - action: link_person_to_thread
    template: thread
    sections: [Related]
    requires: 1
```

`SkillManager.build_section_access_map()` derives `template → section → actions`
from those declarations. Two consequences worth internalising:

- **It counts only DEPLOYED Skills.** "A Skill sitting in the catalog undeployed
  grants nothing." On a machine with no deployments the map is legitimately empty
  — that is correct, not a fault.
- **It is derived, never authored**, so it cannot name an Action that is not
  actually deployed, and cannot go stale against a renamed script the way a
  hand-maintained list in the Template silently did.

The Template still declares each section's own `access`:

| Value | Meaning |
|---|---|
| `machine_write` | Automated callers may write it |
| `human_only` | **The engine refuses** an automated write |
| `public` | Open |

> **An undeclared section defaults to `machine_write` (open).** Protection is
> opt-in.

---

## Identity — what makes re-runs safe

Frontmatter **`id`** is the stable key: a caller-supplied external id (a
conversation id, an event id) or a uuid4. The engine also stamps `title` and
`created`.

**Key on a real external id and a re-run is idempotent** — the engine finds the
existing note and updates it instead of writing a second copy. Key on nothing and
every run duplicates. For child notes the equivalent is `identity_fields`.

---

## Worked example — the shipped `thread` master

```json
{
  "id": "thread",
  "schema_version": 2,
  "version": 1,
  "identity": { "strategy": "id" },
  "on_missing": "error",
  "allow_create_folder": true,
  "root": {
    "type": "md",
    "own_folder": true,
    "plain_filename": true,
    "plain_folder": true,
    "on_existing_title": "always_new",
    "frontmatter_defaults": {
      "type": "Thread", "last_message_at": "",
      "last_summarized_at": "", "classification": ""
    },
    "sections": [
      { "name": "Summary",        "access": "machine_write" },
      { "name": "Personal Notes", "access": "human_only" },
      { "name": "Actions",        "access": "machine_write" },
      { "name": "Related",        "access": "machine_write" },
      { "name": "Files",          "access": "machine_write" }
    ],
    "children": [
      {
        "growth": "dynamic",
        "name": "messages",
        "folder": "messages",
        "identity_fields": ["conversation_id", "message_id"],
        "frontmatter_defaults": { "type": "RawMessage" }
      }
    ]
  }
}
```

Note `on_missing: "error"` — a Thread must already exist before a message is
filed into it, so a typo cannot mint an empty Thread. That is a deliberate choice
this template makes, not a default.

## How to test a Template before trusting it

Against a scratch vault, never the real one. Point `SECOND_BRAIN_DATA_PATH` at a
scratch config folder, copy the Template in, then check what a mistake actually
breaks:

1. **Does it load, with the sections you expect?** Empty sections and
   `error: None` is the schema-mismatch signature above.
2. **Does a second call on the same id duplicate?** Re-ingest and count files.
3. **Is `human_only` enforced?** A write to one must raise.
4. **Read the note.** Do not infer it from return values.

## Errors that fail at load

- **`"identity": "id"`** as a string → `AttributeError: 'str' object has no
  attribute 'setdefault'`. It must be an object: `{"strategy": "id"}`.
- **`root.type` as a domain label** (`"thread"`) — it is a node type and defaults
  to `"md"`.
