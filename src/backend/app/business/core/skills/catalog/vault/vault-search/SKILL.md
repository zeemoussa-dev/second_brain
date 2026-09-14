---
name: vault-search
description: Find notes in the vault by keyword AND by meaning (hybrid search), for when you know what you are looking for but not which note holds it. Use before answering any question about what the vault already knows -- never guess a filename.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, vault, search, retrieval]
---

# Vault Search

Answers "which notes are about X?" -- ranked, across the whole vault, in
one call.

Two rankings are fused (Reciprocal Rank Fusion):

- **Keyword (BM25)** -- unbeatable for an exact account name, a tag, a
  person's surname, a project code.
- **Meaning (embeddings)** -- finds the note that describes a concept
  without using the words the question used.

A note both rankings like outranks one only a single ranking loves. Each
result says which ranker found it (`keyword`, `semantic`, or both): a
keyword-only hit is an exact-name match, a semantic-only hit is a
conceptual one worth reading before it is trusted.

## When to use this

Use it **before answering any question about what the vault already
knows**, and before creating a note that may already exist. It replaces
guessing a filename and replaces walking folders by hand.

Do **not** use it when you already hold a note's real id or filename --
`find_by_id`/`find_by_filename` in `vault_manager.py` are a direct lookup
and cost nothing.

## Prerequisites

**Second Brain's backend must be running** (default
`http://127.0.0.1:8001`, override with `SECOND_BRAIN_API_URL`). Unlike
`vault-index`, this Skill deliberately depends on it: the embedding model
and the vector store live in the backend, and a Hermes-side script cannot
carry an embedding client without taking on real dependencies.

If the backend is down the script says so on stderr and exits non-zero.
That is an expected state, not a failure to report as broken -- fall back
to a direct `vault_manager` lookup.

## How to run

Call it through the `terminal` tool as a PLAIN command starting with
`python`, never wrapped in `bash -c`/`-lc` (Hermes requires human approval
for any `-c` shell-string invocation, which stalls a cron-triggered run
with nobody there to approve it):

```
terminal(command="python search_vault.py \"discount schedule we agreed with the refinery\"")
```

Run it from this Skill's own `scripts/` folder. Options:

- `--limit N` -- how many results (default 10).
- `--mode hybrid|semantic|search` -- `hybrid` (default) is almost always
  right; `search` is keyword-only; `semantic` is meaning-only.
- `--base-url URL` -- a backend somewhere other than the default port.

Output is a ranked list, one entry per note, each carrying the note's
`stem` -- feed that straight into `find_by_filename` to read the note
itself.

## What it will not do

Never writes, moves or edits a note. Never invents a result: an empty
corpus prints `No matching notes.` rather than a plausible guess. If the
semantic half is unavailable (index not built, or the embedding model is
not enabled on the subscription), it returns keyword-only results and
says so on the last line -- read that line before concluding the vault
does not contain something.
