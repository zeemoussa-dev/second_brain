# Shared

Canonical source for reusable, standalone (stdlib-only) Python modules that
get **physically copied** into individual Skills' own `scripts/` folders —
not imported/installed as a shared library, since a vault-writing Skill must
keep working even when Second Brain's own backend isn't running. Editing the
engine happens in exactly one place (here), then the file is re-copied to
each Skill that carries it; extending what it can write happens by adding a
`Template.json` under `.second-brain/data/Templates/`, never by writing a
new script. See `Implementation/Plans/2026-08-25-vault-writer-
standardization.md` for the full design and the real duplicated-primitive
evidence that motivated it.

- `vault_manager.py` — the template-driven vault read/write engine
  (`find`/`create`/`update`/`get_section`/`modify_section`). Not yet copied
  into any real Skill — see that plan doc's own "Applied so far" once it is.
- `tests/test_vault_manager.py` — regression coverage, run via the
  backend's own venv: `src\backend\.venv\Scripts\python.exe -m pytest
  Hermes-Provisioning\shared\tests`.
