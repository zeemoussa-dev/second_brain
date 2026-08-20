"""One-off migration: adds `tags:` (customer/kind) to notes written before
tags existed. Idempotent — a note that already has a `tags` field is left
untouched, so this is safe to rerun."""
from __future__ import annotations

from app.data_access import vault_writer


def backfill_tags() -> list[dict]:
    results: list[dict] = []

    for path in vault_writer.list_all_note_paths():
        frontmatter, _ = vault_writer.read_note(path)
        if "tags" in frontmatter:
            results.append({"note": str(path), "status": "already_tagged"})
            continue

        customer = frontmatter.get("customer")
        kind = frontmatter.get("type")
        if not customer or not kind:
            results.append({"note": str(path), "status": "skipped_no_customer_or_type"})
            continue

        tags = vault_writer.build_tags(customer, kind)
        vault_writer.insert_tags_line(path, tags)
        results.append({"note": str(path), "status": "tagged", "tags": tags})

    return results
