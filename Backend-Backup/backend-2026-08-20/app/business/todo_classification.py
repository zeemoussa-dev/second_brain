"""Orchestrates the To-Do (Outlook Tasks) capture pipeline (REQ-SB-09):
fetch Outlook Tasks, classify each by customer via Compass
(classify_task, customer-only, ADR-027), write/top-up the Task note
through the EntryID-keyed dedup index (ADR-027 point 3 -- consulted
BEFORE any path is computed from current Outlook fields, a genuine
divergence from meeting_classification.py's own recompute-and-exists()
mechanism), link the matched customer hub after a confirmed match only.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.business import agent_prompts, customer_hub_linking
from app.data_access import compass_client, outlook_com, vault_writer


def classify_recent_todos(limit: int = 100) -> list[dict]:
    """The shared "ensure this Outlook Task's Task note exists and is
    up to date" operation -- called once per fetched task, every run.
    The task_note_index lookup (vault_writer.lookup_task_note_stem) is
    what prevents duplicate notes (Scenario 2, 6, 7), consulted BEFORE
    any filename is computed -- unlike meeting_classification.py, this
    module never recomputes a path from current field values and
    exists()-checks it."""
    tasks = outlook_com.list_outlook_tasks(limit=limit)
    known_customers = vault_writer.list_known_customers()
    results: list[dict] = []

    for task in tasks:
        try:
            classification = compass_client.classify_task(
                subject=task["subject"],
                body=task["body"],
                known_customers=known_customers,
                prompt_override=agent_prompts.get_prompt("todo-capture"),
            )
        except compass_client.CompassError as exc:
            results.append({"subject": task["subject"], "error": str(exc)})
            continue

        customer = classification["customer"]
        if not customer:
            # Task's own resolved schema requires an absent customer
            # field (None, not a written placeholder string) when no
            # confident match exists (Scenario 3) -- classify_task's own
            # honest-unclassified fallback is now an empty string too
            # (2026-08-20), so this is just a truthiness check.
            customer = None

        existing_stem = vault_writer.lookup_task_note_stem(task["id"])
        if existing_stem:
            note_path = Path(vault_writer.task_note_path_for_stem(existing_stem))
            vault_writer.ensure_task_note_baseline_frontmatter(
                note_path, task["subject"], customer, task["due"], task["status"], task["id"],
            )
            created = False
        else:
            capture_date = datetime.now().date().isoformat()
            stem = vault_writer.task_note_filename_stem(task["subject"], capture_date, task["id"])
            note_path = Path(vault_writer.create_task_note_baseline(
                task["subject"], customer, task["due"], task["status"], task["id"], capture_date,
            ))
            vault_writer.record_task_note(task["id"], stem)
            created = True

        linked = False
        if customer:
            customer_hub_linking.ensure_customer_hub_note(customer)
            linked = customer_hub_linking.link_note_to_customer_hub(note_path, customer)

        results.append({
            "subject": task["subject"],
            "note_path": str(note_path),
            "created": created,
            "customer": customer,
            "status": task["status"],
            "linked": linked,
        })

    return results
