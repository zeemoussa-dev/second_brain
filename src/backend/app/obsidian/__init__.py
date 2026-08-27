"""Obsidian-vault-format primitives -- .md files, frontmatter/properties,
tags, `## ` headers, section write-permission rules. Zero knowledge of
Second Brain's own concepts (no "Customer", "Section", "Template"):
this package knows only the Obsidian file FORMAT, nothing about what any
particular app uses it for. Every function takes an explicit `path` or
`vault_path` -- nothing here imports app.config, matching app/hermes/'s
own "config injected, never imported" convention.
"""
