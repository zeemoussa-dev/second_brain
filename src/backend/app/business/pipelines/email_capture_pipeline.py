"""The Email Capture & Threading Pipeline (REQ-SB-55-US-01-T07, ADR-043
points 1-3) -- this codebase's first Pipeline-DAG-assembly module, under
`app/business/pipelines/` (ADR-043 point 1's own new subpackage, kept
separate from each capture type's own business-logic module).

This module now holds TWO genuinely separate things (`BUGFIX-05-US-01`,
`ADR-051`, supersedes `ADR-043` points 1/3's own live-execution/topology
halves only):

1. **The real, LIVE `run_email_capture_pipeline` entry point** -- what
   `process_staged_email`'s own real, scheduled call site actually
   invokes. It NO LONGER builds or invokes the `StateGraph` below; it is a
   plain, sequential composing function over Stage 1
   (`raw_message_capture.capture_raw_thread_messages`) + Stage 2
   (`email_classification.synthesize_thread`), with the old graph's three
   side effects that have no equivalent elsewhere (`detect_recurring_
   pattern`, `consult_librarian`, `project_customer_synthesizer.resync_
   project_from_thread`) explicitly, directly re-composed as plain calls.
   See its own docstring below for the full composition.
2. **The `StateGraph` construction/compile below (`EmailCapturePipelineState`,
   every `_..._node` function, `_build_graph`, `_GRAPH`) -- DEPRECATED, not
   deleted.** No longer on any live execution path for real capture --
   kept byte-for-byte unchanged only because `get_job_tree()`
   (`REQ-SB-65-US-01`, the Agents Map's Pipeline Job Tree visualization) is
   a real, separate, currently-shipped read-only capability that
   introspects this SAME compiled `_GRAPH` singleton. Its own topology is
   now known, disclosed stale (no longer what `process_staged_email`
   actually executes) -- see `architecture.md`'s "`email_capture_
   pipeline.py`'s `StateGraph` -- deprecated, not deleted" section and
   `ADR-051` Consequences.

Every graph node below is still a thin wrapper around a PLAIN,
LangGraph-ignorant function already living in `email_classification.py`
(T02-T06) -- this module never re-implements any Job's own real logic, and
no node ever imports `outlook_com`/`compass_client` directly (ADR-043
point 1).

Topology (ADR-043 point 3, unchanged, deprecated): `classify` is the fork
point, unconditionally routed to `summarize_attachment` (a mandatory
pass-through node -- when the email has zero real attachments this node is
a structural no-op, returning an empty `attachment_entries` list; when it
has one or more, it loops the plain `summarize_attachment` Job once per
attachment, collecting every real `dated_entry` produced), and
conditionally, in parallel, to `detect_recurring_pattern` when
`classification["recurring_candidate"]` is true -- that branch never feeds
back into `thread_match_merge`; it terminates on its own once it creates
its own Pending Approval. `summarize_attachment` always leads straight to
`thread_match_merge` next (a fixed, non-conditional edge) -- this is the
concrete mechanism satisfying the fan-in ordering constraint ("`thread_
match_merge` runs only once `summarize_attachment`'s branch, if
triggered, has completed"): `thread_match_merge` is never reachable in
the same superstep as `summarize_attachment`, so it always sees the fully
resolved `attachment_entries` list. `thread_match_merge` is the SECOND
fork point (REQ-SB-63-US-01-T02, extended by REQ-SB-57-US-01-T01):
`consult_librarian` and `trigger_project_synthesis` are BOTH
UNCONDITIONAL destinations, fired for every Thread update alike (created
and updated), never gating anything downstream or each other --
`trigger_project_synthesis` only calls THROUGH into
`project_customer_synthesizer.resync_project_from_thread`, it never reads
or writes a Project's own `## Glimpse`/`log.md` itself (REQ-SB-54 point 7's
ownership rule); `route_to_project` is an ADDITIONAL, parallel destination
only when this pass's own returned `created` is `True` (a brand-new
Thread) -- an update to an already-existing Thread still reaches
`consult_librarian`/`trigger_project_synthesis` but never re-routes/
re-approves via `route_to_project`, the concrete mechanism satisfying
Scenario 4/AC-04. None of the three feeds back into `thread_match_merge`
or into each other -- each terminates on its own via its own edge to the
graph's own end.

Mid-pipeline human approval is never a LangGraph `interrupt()`/
checkpointer suspension (ADR-043 point 4) -- `route_to_project` and
`detect_recurring_pattern` each run their own branch to a clean, ordinary
completion on every invocation (each creates its own Pending Approval
internally and returns; the graph run for that item simply ends).
`consult_librarian` mirrors that same clean-completion shape -- it
always returns an honest result dict (never raises), so it too runs to
a clean, ordinary end on every invocation. No `MemorySaver`/
`SqliteSaver` or any checkpointer is used anywhere in this module."""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.business import project_customer_synthesizer
from app.business.email_classification import (
    classify_captured_email_with_fallback,
    consult_librarian,
    detect_recurring_pattern,
    route_to_project,
    summarize_attachment,
    synthesize_thread,
    thread_match_merge,
)
from app.business.pipelines.raw_message_capture import capture_raw_thread_messages
from app.data_access import email_staging, vault_writer


class EmailCapturePipelineState(TypedDict):
    email: dict
    known_customers: list[str]
    known_kinds: list[str]
    classification: dict
    attachment_entries: list[str]
    thread_result: dict
    route_to_project_result: dict | None
    recurring_pattern_result: dict | None
    consult_librarian_result: dict | None
    project_synthesis_result: dict | None


def _classify_node(state: EmailCapturePipelineState) -> dict:
    # BUG-015 follow-up (2026-08-17): classify_captured_email_with_fallback
    # never raises CompassError -- a persistent classification failure now
    # falls back to an honest "Unsorted" classification and raises a real
    # Pending Approval instead of leaving the email stuck retrying silently
    # forever (see that function's own docstring). The rest of this graph
    # runs exactly as it would for a real Compass success, so the email's
    # own content still lands in a real, visible Thread note this pass.
    classification = classify_captured_email_with_fallback(
        state["email"], state["known_customers"], state["known_kinds"]
    )
    return {"classification": classification}


def _summarize_attachment_node(state: EmailCapturePipelineState) -> dict:
    """A mandatory pass-through node -- runs for EVERY email, not just
    ones with attachments (ADR-043's own "in parallel, once per real
    attachment, when the email has any" framing is realized here as a
    loop over 0-or-more attachments rather than a real per-attachment
    graph fan-out; this is what guarantees `thread_match_merge`, reached
    only via this node's own fixed outgoing edge, is never reachable
    before this loop has fully completed). Every real, non-inline
    attachment leaves a durable entry in `attachment_entries` --
    `summarize_attachment`'s own real `dated_entry` when a genuine
    summary was produced, or a synthesized, visibly-distinct fallback
    line (BUGFIX-03-US-01, closes BUG-014's gap 1) whenever it wasn't
    -- never a silent drop, never a fabricated summary."""
    email = state["email"]
    conversation_id = email["conversation_id"]
    received = email["received"]
    entries: list[str] = []
    for attachment in email.get("attachments") or []:
        result = summarize_attachment(attachment, conversation_id, received)
        dated_entry = result.get("dated_entry")
        if dated_entry:
            entries.append(dated_entry)
        else:
            entries.append(_fallback_attachment_entry(result, received))
    return {"attachment_entries": entries}


def _fallback_attachment_entry(result: dict, received: str) -> str:
    """Restores the honest-signal convention classify_recent_emails
    already established (MEMORY.md, 2026-08-16) for the one case the
    Thread pipeline lost: a real, non-inline attachment that failed to
    save or summarize for ANY reason still leaves a durable, visibly-
    distinct trace on the Thread note -- never disguised as a genuine
    summary. `summarize_attachment`'s own contract (never fabricate a
    `dated_entry`) is what makes this branch reachable at all; this
    function only decides the fallback's own wording."""
    filename = result["filename"]
    summary_error = result.get("summary_error", "unknown error")
    if result.get("saved") and result.get("relative_link"):
        return (
            f"{received[:10]} — [{filename}]({result['relative_link']}) "
            f"(saved but could not be summarized — {summary_error})"
        )
    return f"{received[:10]} — {filename} (not saved — {summary_error})"


def _thread_match_merge_node(state: EmailCapturePipelineState) -> dict:
    thread_result = thread_match_merge(
        state["email"], state["classification"], state["attachment_entries"]
    )
    return {"thread_result": thread_result}


def _route_to_project_node(state: EmailCapturePipelineState) -> dict:
    result = route_to_project(
        state["thread_result"], state["classification"], state["email"]
    )
    return {"route_to_project_result": result}


def _detect_recurring_pattern_node(state: EmailCapturePipelineState) -> dict:
    result = detect_recurring_pattern(state["email"], state["classification"])
    return {"recurring_pattern_result": result}


def _consult_librarian_node(state: EmailCapturePipelineState) -> dict:
    result = consult_librarian(state["thread_result"])
    return {"consult_librarian_result": result}


def _trigger_project_synthesis_node(state: EmailCapturePipelineState) -> dict:
    """REQ-SB-57-US-01-T01's own trigger call site -- calls THROUGH
    project_customer_synthesizer.resync_project_from_thread, never reads or
    writes any Project's own `## Glimpse`/`log.md` itself (REQ-SB-54 point
    7's ownership rule). Fires on every Thread update alike (a brand-new
    Thread AND an update to an already-existing one), mirroring `consult_
    librarian`'s own unconditional-branch shape -- a not-yet-routed Thread
    (no `project` frontmatter key yet) resolves to a clean None no-op
    inside that helper, never raised here."""
    result = project_customer_synthesizer.resync_project_from_thread(
        state["thread_result"]["thread_path"]
    )
    return {"project_synthesis_result": result}


def _route_after_classify(state: EmailCapturePipelineState) -> list[str]:
    """The fork point (ADR-043 point 3). `summarize_attachment` is always
    a destination (it is the mandatory pass-through node leading to
    `thread_match_merge`); `detect_recurring_pattern` is an ADDITIONAL,
    parallel destination only when this email's own classification
    flagged it as a recurring-pattern candidate -- an independent branch
    that never feeds back into `thread_match_merge`."""
    destinations = ["summarize_attachment"]
    if state["classification"].get("recurring_candidate"):
        destinations.append("detect_recurring_pattern")
    return destinations


def _route_after_thread_match_merge(state: EmailCapturePipelineState) -> list[str]:
    """The second fork point (REQ-SB-63-US-01-T02, extended by
    REQ-SB-57-US-01-T01) -- mirrors `_route_after_classify`'s own "always
    this, additionally that" list shape. `consult_librarian` AND `trigger_
    project_synthesis` are BOTH ALWAYS destinations (fire on every Thread
    update, both `created=True` and `created=False` alike -- `consult_
    librarian` per ADR-041's own "consulting an Expert is additive"
    precedent, `trigger_project_synthesis` per REQ-SB-57's own Scenario
    1/AC-01, a routine update must resynthesize its linked Project's own
    Glimpse exactly as a brand-new Thread does); `route_to_project` is an
    ADDITIONAL, parallel destination only when this pass's own `created`
    is True (Scenario 4/AC-04's own mechanism -- an update to an
    already-existing Thread never re-routes/re-approves). No branch feeds
    into another or back into `thread_match_merge`; each terminates on its
    own via its own edge to END, so none of the three ever gates another."""
    destinations = ["consult_librarian", "trigger_project_synthesis"]
    if state["thread_result"]["created"]:
        destinations.append("route_to_project")
    return destinations


def _build_graph():
    builder = StateGraph(EmailCapturePipelineState)
    builder.add_node("classify", _classify_node)
    builder.add_node("summarize_attachment", _summarize_attachment_node)
    builder.add_node("thread_match_merge", _thread_match_merge_node)
    builder.add_node("route_to_project", _route_to_project_node)
    builder.add_node("detect_recurring_pattern", _detect_recurring_pattern_node)
    builder.add_node("consult_librarian", _consult_librarian_node)
    builder.add_node("trigger_project_synthesis", _trigger_project_synthesis_node)
    builder.set_entry_point("classify")
    builder.add_conditional_edges(
        "classify",
        _route_after_classify,
        ["summarize_attachment", "detect_recurring_pattern"],
    )
    builder.add_edge("summarize_attachment", "thread_match_merge")
    builder.add_edge("detect_recurring_pattern", END)
    builder.add_conditional_edges(
        "thread_match_merge",
        _route_after_thread_match_merge,
        ["consult_librarian", "route_to_project", "trigger_project_synthesis"],
    )
    builder.add_edge("consult_librarian", END)
    builder.add_edge("route_to_project", END)
    builder.add_edge("trigger_project_synthesis", END)
    return builder.compile()


# Compiled once at module load, mirroring app/business/agent_orchestration/
# graph.py's own existing _GRAPH module-level-singleton convention -- never
# recompiled per call.
_GRAPH = _build_graph()


def get_job_tree() -> list[dict]:
    """Read-only StateGraph introspection (REQ-SB-65-US-01-T01, `ADR-043`
    point 1 extended, not reopened) -- calls `.get_graph()` on the SAME
    already-compiled `_GRAPH` singleton `run_email_capture_pipeline`
    already invokes below (never recompiles a second graph instance),
    filters the graph's own synthetic `START`/`END` sentinel nodes (never
    real Jobs), and shapes every real remaining node into
    `{"id", "name", "depends_on"}` -- `depends_on` derived purely from the
    real `Graph.edges` (every edge whose `target` is this node
    contributes its `source`), never a hardcoded Job-name list. Reads
    `_GRAPH.get_graph()` fresh on every call, so a future Job added,
    removed, or rewired in `_build_graph` changes this function's own
    output with zero code change here."""
    graph = _GRAPH.get_graph()
    real_node_ids = [node_id for node_id in graph.nodes if node_id not in (START, END)]
    jobs: list[dict] = []
    for node_id in real_node_ids:
        depends_on = [
            edge.source
            for edge in graph.edges
            if edge.target == node_id and edge.source not in (START, END)
        ]
        jobs.append({
            "id": node_id,
            "name": graph.nodes[node_id].name,
            "depends_on": depends_on,
        })
    return jobs


def run_email_capture_pipeline(limit: int = 10) -> list[dict]:
    """The public entry point (ADR-043 point 1) -- what `email-
    capture-pipeline`'s `process_staged_email` capability calls.
    RETARGETED (`BUGFIX-05-US-01`, `ADR-051`) off the compiled
    `StateGraph` above entirely -- a plain, sequential composing
    function now:

    1. Calls `capture_raw_thread_messages(limit=limit)` once (Stage 1
       -- zero-Compass raw capture, unchanged). Its own additive
       `conversation_ids_touched` key names every conversation_id
       that received at least one genuinely NEW raw message this run.
    2. For each such `conversation_id`, calls `synthesize_thread
       (conversation_id)` (Stage 2) -- which, internally, already
       performs create-vs-update, customer/tags/participants,
       `## Summary` regeneration, the Files/OKF companion writes, and
       `route_to_project`'s own created-only Pending-Approval trigger.
    3. For each such Thread, three of the old graph's other real
       branch effects -- which have NO equivalent anywhere in the
       REQ-SB-71/REQ-SB-72 redesign -- are explicitly, directly
       re-composed as plain calls, never re-implemented (ADR-051
       Decision 3):
       - `detect_recurring_pattern`, for each raw message note under
         this Thread's own `messages/` directory whose `message_id`
         is in Stage 1's own `processed` list this run (a genuinely
         NEW message, not `skipped_already_noted`) -- reads that
         message's own just-written raw note back, reconstructs an
         `email`-shaped dict, classifies it again (`classify_
         captured_email_with_fallback`, a genuine, additional Compass
         call separate from `synthesize_thread`'s own Thread-
         lifetime-scoped classify), and calls `detect_recurring_
         pattern(email, classification)` when `recurring_candidate`
         is true. Wrapped in its own try/except -- never gates the
         enclosing Thread's own already-successful capture/
         synthesis.
       - `consult_librarian(thread_result)`, once per synthesized
         Thread (`synthesized: True`) -- unconditional for both a
         brand-new and an updated Thread alike. Already has its own
         internal broad try/except; no additional wrapping needed
         here.
       - `project_customer_synthesizer.resync_project_from_thread(
         thread_result["thread_path"])`, once per synthesized Thread
         -- unconditional. Wrapped in its own try/except, same
         non-gating reason as the recurring-pattern step.
    4. The whole per-`conversation_id` unit (Stage 2 plus its three
       composed side effects) is ALSO wrapped in one outer
       try/except at the loop level -- a genuinely unexpected
       exception anywhere in that unit is caught, reported as
       `{"conversation_id", "error"}`, and the loop continues to the
       next `conversation_id`; it never aborts the whole tick's
       remaining Threads.

    Returns one row per synthesized Thread this run, not one row per
    fetched email -- a real, disclosed behavior change (ADR-051
    Decision 5); `skill_tools.process_staged_email`'s own
    `"error"`-key-presence convention (`filed = [r for r in results
    if "error" not in r]`) stays compatible as-is.

    NOTE: this composition does NOT close BUGFIX-05-US-01's own
    `AC-01` alone (a new message for a pre-redesign, FLAT-shape
    Thread) -- that facet is closed by `T03`'s own `resolve_thread_
    directory()` migration primitive (`ADR-052`), composed
    transparently underneath `synthesize_thread`'s own create-vs-
    update check with zero call-site change here."""
    capture_summary = capture_raw_thread_messages(limit=limit)
    newly_processed_message_ids = set(capture_summary["processed"])
    known_customers = vault_writer.list_known_customers()
    known_kinds = vault_writer.list_known_kinds()
    results: list[dict] = []

    for conversation_id in capture_summary["conversation_ids_touched"]:
        try:
            thread_result = synthesize_thread(conversation_id)
            if not thread_result.get("synthesized"):
                results.append({
                    "conversation_id": conversation_id,
                    "error": thread_result.get("reason", "synthesis_skipped"),
                })
                continue

            messages_dir = Path(thread_result["thread_path"]).parent / "messages"
            for message_path in messages_dir.glob("*.md"):
                message_frontmatter, message_body = vault_writer.read_note(message_path)
                message_id = message_frontmatter.get("message_id", "")
                if message_id not in newly_processed_message_ids:
                    continue
                try:
                    email = {
                        "subject": message_frontmatter.get("subject", ""),
                        "sender_name": message_frontmatter.get("sender", ""),
                        "sender_email": message_frontmatter.get("sender_email", ""),
                        "body": message_body.strip(),
                        "conversation_id": conversation_id,
                    }
                    classification = classify_captured_email_with_fallback(
                        email, known_customers, known_kinds,
                    )
                    if classification.get("recurring_candidate"):
                        detect_recurring_pattern(email, classification)
                except Exception:  # noqa: BLE001 -- never gates this Thread's own already-successful capture/synthesis (ADR-051 Decision 3)
                    pass

            try:
                consult_librarian(thread_result)
            except Exception:  # noqa: BLE001 -- defensive only; consult_librarian already returns an honest {"status": "unavailable", ...} internally
                pass

            try:
                project_customer_synthesizer.resync_project_from_thread(
                    thread_result["thread_path"]
                )
            except Exception:  # noqa: BLE001 -- never gates this Thread's own already-successful capture/synthesis (ADR-051 Decision 3)
                pass

            results.append({
                "conversation_id": conversation_id,
                "customer": thread_result.get("customer"),
                "thread_path": thread_result.get("thread_path"),
                "created": thread_result.get("created"),
                "message_count": thread_result.get("message_count"),
            })
        except Exception as exc:  # noqa: BLE001 -- honest per-Thread failure funnel (ADR-051 Decision 4); never crashes the whole tick's own loop over the remaining conversation_ids
            results.append({"conversation_id": conversation_id, "error": str(exc)})

    return results
