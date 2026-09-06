# AGENT-MEMORY

Instance memory for ONE machine. Copy this file to
`<SECOND_BRAIN_DATA_PATH>/AGENT-MEMORY.md` on a new install and leave it empty
until there is something real to put in it.

**Never commit this file to the framework repo. Never read another operator's
copy.**

---

## The test

Would this still be true on a fresh install with a different vault and mailbox?

- **No** → here.
- **Yes** → the repo's `MEMORY.md`, as one atomic rule.

## What belongs here

- This machine's paths, vault, mailbox, model and keys
- This install's agent roster, profile names and cron jobs
- The customers, partners and entities that exist in this vault
- Local quirks and workarounds specific to this host
- Bugs that are this install's until proven to be the framework's

## What does not

- Anything true of the product itself — that is framework memory or the
  Framework documentation
- Another operator's paths, agents or data, in any form

## Promotion — the only way something leaves this file

A discovery starts here. It moves to the framework's `MEMORY.md` only when it has
been reproduced on another install, or is provably about the engine rather than
this data. Promotion **rewrites** it as one atomic rule with every instance detail
removed and replaced by `<OPERATOR_VAULT>` / `<operator>` placeholders.

Nothing ever moves sideways, instance to instance.

## Writing rules

Same as framework memory:

1. One entry is one fact, under 400 characters.
2. Never write while investigating — write once the thing is understood.
3. Keep it under 40 KB. Over budget, replace rather than append.

---

## This machine

<!-- Vault path, data path, mailbox, model, gateway profile. Fill in on setup. -->

## This install's agents

<!-- Profile names and what each owns. -->

## Local quirks

<!-- Host-specific behaviour that is not the framework's fault. -->
