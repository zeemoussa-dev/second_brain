"""One-shot maintenance operation (REQ-SB-67-US-01-T03): regenerates
`## Summary` + the opening-line sentence for every already-captured Thread
note in the vault, in place. Mirrors tag_backfill.py's own iterate-and-
filter shape and honest per-item try/except+continue posture exactly.

Delta-aware (2026-08-20, operator-directed): a Thread whose `summary_
synced_at` frontmatter already equals its own current `last_message_at`
is skipped outright -- no new message has arrived since this Thread was
last summarized, so re-running Compass against unchanged content would
waste a real call and produce a real, but pointless, resynthesis.
`last_message_at` is already a real, reliable signal -- email_
classification.py's own Stage 2 (synthesize_thread) updates it every
time a Thread gains a message, unconditionally, regardless of whether
this Job has ever run. `summary_synced_at` is this module's own new
field, written as a copy of `last_message_at` at the moment a summary is
actually (re)generated -- never wall-clock time, so a re-run against
byte-for-byte the same Thread state is a true no-op by construction."""
from __future__ import annotations

from app.business.email_classification import (
    _THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS,
    _synthesize_thread_summary,
)
from app.business import agent_prompts
from app.data_access import vault_writer


def backfill_thread_summaries() -> list[dict]:
    results: list[dict] = []

    for path in vault_writer.list_all_note_paths():
        frontmatter, _ = vault_writer.read_note(path)
        if frontmatter.get("type") != "Thread":
            continue

        existing_summary = vault_writer.read_body_section(path, "## Summary")
        last_message_at = frontmatter.get("last_message_at") or ""
        summary_synced_at = frontmatter.get("summary_synced_at") or ""
        if existing_summary and summary_synced_at == last_message_at:
            # Already summarized, and no new message has arrived since --
            # skip, never touch the Thread. `existing_summary` being
            # non-empty is required too: a never-yet-summarized Thread
            # with no last_message_at (summary_synced_at also blank,
            # matching) must still get its first real synthesis, not be
            # mistaken for "already up to date."
            results.append({"note": str(path), "status": "skipped_up_to_date"})
            continue

        transcript = vault_writer.read_body_section(path, "## Transcript")
        prompt_override = (
            agent_prompts.get_prompt("thread_match_merge")
            or _THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS
        )
        synthesis = _synthesize_thread_summary(
            existing_summary, transcript, None, prompt_override
        )

        if "summary_error" in synthesis:
            # Honest, non-fabricating per-item failure posture (mirrors
            # tag_backfill.py's own per-item continue) -- neither the
            # opening line nor ## Summary is touched on this path, and
            # the loop moves on to the next Thread note rather than
            # aborting the whole backfill run.
            results.append({
                "note": str(path),
                "status": "summary_error",
                "summary_error": synthesis["summary_error"],
            })
            continue

        vault_writer.replace_body_opening_line(path, synthesis["opening_line"])
        vault_writer.replace_body_section(
            path, "## Summary", synthesis["summary"],
            caller="thread_summary_backfill.backfill_thread_summaries",
        )
        vault_writer.upsert_frontmatter_key(path, "summary_synced_at", last_message_at)
        results.append({"note": str(path), "status": "regenerated"})

    return results
