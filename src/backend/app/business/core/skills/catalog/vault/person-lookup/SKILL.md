---
name: person-lookup
description: The one-time attendee web-lookup mechanism for the Meeting Preparation Agent -- check whether an attendee's existing Person note is still empty beyond frontmatter, and if it is, append real, actually-found web-lookup findings into it. Never re-runs once real content exists.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, meeting-prep, librarian, knowledge-base, vault-write]
---

# Person Lookup

Your real, mechanical eligibility-check-then-append pair for one specific
need: "if we have nothing about the person, do a small search" (the
operator's own PRD wording). Two scripts, each doing exactly one
mechanical job -- neither performs the actual web lookup itself.

## Prerequisites

- Vault path (pass as `--note-path`'s own directory context on every call
  -- the real vault root is `$SECOND_BRAIN_VAULT_PATH`):
  `--note-path` always takes the ALREADY-RESOLVED absolute path to the
  specific attendee's own existing Person note (e.g.
  `$SECOND_BRAIN_VAULT_PATH\Work\People\<slug>.md`), not the
  vault root itself.

## What these scripts do

```
scripts/check_person_note_empty.py    <- read-only: is the body empty?
scripts/append_person_findings.py     <- write: append real findings
```

Neither script ever creates a new Person note -- Person notes already
exist (`REQ-SB-10`), created elsewhere, whenever an attendee is first seen
on a meeting. `append_person_findings.py` errors honestly if the given
path doesn't exist rather than creating one.

## The one-time gate IS the body-emptiness check

There is no separate "already looked up" tracking field or file anywhere
in this vault for this. A Person note's own body (everything after its
closing `---` frontmatter fence) being empty or whitespace-only IS "not
yet looked up." The moment real content exists there -- whether YOU wrote
it on a prior run, or the user wrote it themselves -- every future check
honestly reports `empty: false` and the lookup is never repeated. Never
try to work around this by tracking eligibility yourself elsewhere.

## When to use this

**Always check FIRST, before doing anything else, for every attendee on a
meeting you're preparing:**

```
terminal(command="python \"<...>\\person-lookup\\scripts\\check_person_note_empty.py\" --note-path \"<attendee's real Person note path>\"")
```

- `{"empty": false}` -> **stop here.** Do not perform a web lookup for
  this attendee at all -- real content already exists, whether from a
  prior run of yours or the user's own writing. Move on to the next
  attendee.
- `{"empty": true}` -> **only now** perform a real web lookup for this
  attendee (Hermes' own bundled `web_search` tool -- the same real
  mechanism Research Agent's own `research-agent` profile uses; this
  Skill has no lookup tool of its own).
- `{"error": ...}` -> the given path is wrong or the note genuinely
  doesn't exist; do not guess a path -- report the error honestly rather
  than fabricating a result.

## If the web lookup finds something real

`write_file` a scratch JSON payload:
```json
{
  "findings": "The real, actual findings you found -- what they do, where they work, anything genuinely relevant. Never a plausible-sounding guess."
}
```

Then call the script as a PLAIN, direct `terminal` call using its own full
absolute path:
```
terminal(command="python \"<...>\\person-lookup\\scripts\\append_person_findings.py\" --note-path \"<attendee's real Person note path>\" --input-file <scratch path>")
```

## If the web lookup finds nothing real

**Do NOT call `append_person_findings.py`.** No content gets appended for
that request -- never fabricate a plausible-sounding finding to fill the
gap. This matches `research-kb-writer`'s own identical honesty posture:
a missing update is always the correct outcome of an inconclusive lookup,
never a reason to write something anyway. Simply move on to the next
attendee (or continue the rest of your own meeting-prep flow).

## Never overwrites existing content

`append_person_findings.py` is append-only -- whatever real content
already exists in the note's body (agent- or user-written) is preserved
byte-for-byte; your findings are added after it. It cannot overwrite,
truncate, or remove anything already there.

## Pitfalls

- **Never wrap either script in `bash -lc "..."`** -- same categorical
  Hermes `terminal`-tool approval-block documented throughout this
  vault's Skills; a bare `python ...` command with the script's own full
  absolute path runs without a prompt.
- **Never call `check_person_note_empty.py` once and assume the result
  stays valid across a later run** -- always re-check on every scheduled
  scan; a user may have filled in the note themselves since the last run.
- **Never fabricate a finding, and never call `append_person_findings.py`
  for an inconclusive result.** See "If the web lookup finds nothing
  real" above.
- **`--note-path` is the specific note file, not the vault root or the
  `Work/People/` folder** -- resolve the exact attendee note path first.

## Verification

- After an append, `check_person_note_empty.py` on the SAME note now
  reports `{"empty": false}` -- confirms the gate will correctly skip this
  attendee on every future run.
