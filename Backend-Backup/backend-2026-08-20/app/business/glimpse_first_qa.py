"""Glimpse-first entity resolution + context read for `vault-qa`
(`REQ-SB-58-US-01-T01`) -- one public function,
resolve_glimpse_first_context(), composes vault_search (business) and
vault_writer.read_body_section (data_access) only, per ADR-003. Read-only:
never calls replace_body_section/append_person_note_update_line/any other
Glimpse/Background/History write primitive -- ownership of those stays
exclusively with project_customer_synthesizer.py (REQ-SB-54 point 7).

Never bound as a model tool and never registered on
app/api/mcp_server.py -- T02's own new graph.py node is its only caller.
See architecture.md -> "Glimpse-First vault-qa Answers" for the full
mechanism reasoning."""
from __future__ import annotations

from pathlib import Path

from app.business import vault_indexing, vault_search
from app.data_access import vault_writer

_RESOLVABLE_KINDS = {"customer", "project"}


def resolve_glimpse_first_context(question: str) -> dict | None:
    """Entity resolution reuses vault_search.search()'s own rank-1 result
    only -- no new matching/ranking logic (story Constraint). None when
    there are no results at all, or the rank-1 result is some other note
    kind than a Customer/Project OKF concept file (Scenario 6's own honest
    no-match case).

    The matched entity's own concept-file path is resolved directly from
    the search result's own vault_indexing.get_index() entry (never
    recomputed via customer_directory_paths/project_directory_paths from a
    name/slug round-trip) -- by construction, the exact same on-disk file
    project_customer_synthesizer.py already owns and keeps current.

    entity_name reads frontmatter["title"] directly, not vault_search's
    own _title_for/summary "title" field (which falls back to the note's
    filename stem when no "subject" key is present -- the convention
    vault_search.py designed for Email/Meeting notes, not concept files)
    -- decomposer-authored implementation-latitude choice, per this task's
    own Context/Notes.

    Reads BOTH ## Glimpse and ## Background -- deliberately not a
    durable-vs-current-status classifier; ADR-042 already structurally
    separates the two (architecture.md's own documented reasoning)."""
    results = vault_search.search(question)["results"]
    if not results:
        return None

    top_result = results[0]
    if top_result["kind"] not in _RESOLVABLE_KINDS:
        return None

    index = vault_indexing.get_index()
    entry = index[top_result["stem"]]
    concept_path = Path(entry["path"])

    return {
        "entity_type": top_result["kind"],
        "entity_name": entry["frontmatter"]["title"],
        "glimpse": vault_writer.read_body_section(concept_path, "## Glimpse"),
        "background": vault_writer.read_body_section(concept_path, "## Background"),
    }
