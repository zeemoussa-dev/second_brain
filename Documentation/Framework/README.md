# Framework Documentation

**How to build with this framework.** Read these before extending anything — they
exist so a session does not have to read the engine source to learn what it can
do.

| Guide | Read it when |
|---|---|
| **[Templates.md](Templates.md)** | You need a new *kind of note*. Full key reference, the section-access model, a worked example, and how to test one. |
| **[Artifacts.md](Artifacts.md)** | You are authoring or moving an Agent, Skill, Pipeline or Template — their shapes, where they live on disk, and how `.sbf` / `.sbb` / `.sbd` differ. |
| **[Hermes-Provisioning.md](Hermes-Provisioning.md)** | Skills come back empty, you are taking a backup, or you need the canonical engine. Lists exactly what depends on the folder held outside the tree. |

## Documentation vs memory

They are different things and should not duplicate each other:

- **This documentation** — how the framework works and how to use it. Written to
  be read *before* doing something.
- **[`MEMORY.md`](../../MEMORY.md)** — the framework's hard-won rules and
  constraints. Written *after* something went wrong, so it does not go wrong
  twice.
- **`<SECOND_BRAIN_DATA_PATH>/AGENT-MEMORY.md`** — one machine's own paths,
  vault, mailbox, model and state. Never in this repo.

**The test for where something goes:** would it still be true on a fresh install
with a different vault and mailbox? Yes → here or `MEMORY.md`. No → that
machine's instance memory.

## The one thing to internalise

**A new note type is a new `Template.json`, never new code.** If you are about to
write a script to produce a new kind of note, write a Template instead.
