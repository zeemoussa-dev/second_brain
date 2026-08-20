"""One-off migration: flattens Work/Customers/<Customer>/<Kind>/ into
Work/<Kind>/ — customer stops being a folder level (see
Documentation/References/beyond-the-second-brain-methodology.md and
email_classification.py's module docstring for why). Idempotent in the
sense that once Work/Customers/ is gone, a rerun finds nothing to move."""
from __future__ import annotations

from app.config import settings
from app.data_access import vault_writer


def flatten_customer_folders() -> list[dict]:
    results: list[dict] = []
    customers_root = settings.vault_path / "Work" / "Customers"
    if not customers_root.exists():
        return results

    for customer_dir in sorted(p for p in customers_root.iterdir() if p.is_dir()):
        for kind_dir in sorted(p for p in customer_dir.iterdir() if p.is_dir()):
            target_dir = settings.vault_path / "Work" / kind_dir.name
            for note_path in sorted(kind_dir.glob("*.md")):
                try:
                    new_path = vault_writer.move_note_and_attachments(note_path, target_dir)
                    results.append({"from": str(note_path), "to": new_path, "status": "moved"})
                except FileExistsError as exc:
                    results.append({"from": str(note_path), "status": "collision", "error": str(exc)})

    vault_writer.remove_empty_dirs(customers_root)
    return results
