"""One-shot maintenance operation (REQ-SB-67-US-01-T03): regenerates
`## Summary` + the opening-line sentence for every already-captured Thread
note in the vault, in place. Pure resynthesis of what's already persisted
(no new-message delta) — mirrors tag_backfill.py's own iterate-and-filter
shape and honest per-item try/except+continue posture exactly."""
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
        results.append({"note": str(path), "status": "regenerated"})

    return results
