"""The skill repository's code-level catalog (ADR-015 points 3/7/9) --
a new sibling module to app/business/vault_query_tools.py, both siblings
of app/business/agent_orchestration/. A skill's actual specialized-task
logic is necessarily code: an @mcp.tool()-decorated Python function
registered on Second Brain's shared MCP server, never a runtime
user-created entry (REQ-SB-27-US-01's own Constraints). SKILLS is the
single source of truth app/business/skill_registry.py reads directly,
never derived by introspecting the MCP server's full live tool list
(which would also surface vault_query_tools.py's non-skill tools).

REQ-SB-39-US-02 (ADR-029 point 5) adds the 4 formerly-hardcoded mutating
Action ids (run_capture_now, pause_schedule, rebuild_person_note,
build_knowledge) as Skills, preserving today's real/honest-unavailable
split exactly -- no new real behavior is built by this pass."""
import asyncio
import concurrent.futures

from app.api.mcp_server import mcp_server
from app.business import agent_registry, email_classification, provider_registry, thread_summary_backfill
from app.business.pipelines import email_pull
from app.business.pipelines import librarian_housekeeping
from app.data_access import anthropic_client, compass_client, vault_writer

SKILLS: dict[str, dict] = {
    "diagram-understanding": {
        "id": "diagram-understanding",
        "name": "Diagram Understanding",
        "description": (
            "Given an uploaded image, identify and describe the "
            "components in an architecture/engineering diagram."
        ),
        "mutates": False,
        "tool": "Compass",
    },
    "web-research": {
        "id": "web-research",
        "name": "Web Research",
        "description": (
            "Given a research subject or query, gather real, current "
            "information from the web -- using the invoking agent's own "
            "linked Provider's real web-search capability (Anthropic "
            "Claude's own server-side web-search tool, today)."
        ),
        "mutates": False,
        "tool": "Web",
    },
    # ADR-028 point 4 -- the 3 migrated read-only Actions. Each reuses its
    # exact former agent_registry.py Action id string (not a new kebab-case
    # id), which is what makes agents_router.py's later "id in SKILLS"
    # membership check correct with zero duplicated migrated-id bookkeeping.
    "view_last_run": {
        "id": "view_last_run",
        "name": "View Last Run",
        "description": "View this agent's most recent capture run result.",
        "mutates": False,
        "tool": "Outlook",
    },
    "ask_question": {
        "id": "ask_question",
        "name": "Ask a Question",
        "description": "Ask this agent a question grounded in the indexed vault.",
        "mutates": False,
        "tool": "Vault",
    },
    "view_channel_status": {
        "id": "view_channel_status",
        "name": "View Channel Status",
        "description": "View this agent's current channel status.",
        "mutates": False,
        "tool": "Vault",
    },
    # REQ-SB-39-US-02 (ADR-029 points 5/8) -- the 4 formerly-hardcoded
    # mutating Action ids, migrated onto the same "reuse the exact former
    # id string" precedent as the 3 read-only ids above. Every one of
    # these carries "mutates": True -- this is what makes T01's gate defer
    # them under Supervised mode.
    "run_capture_now": {
        "id": "run_capture_now",
        "name": "Run Capture Now",
        "description": "Run this agent's capture pipeline immediately.",
        "mutates": True,
        "tool": "Outlook",
    },
    "pause_schedule": {
        "id": "pause_schedule",
        "name": "Pause Schedule",
        "description": "Pause this agent's scheduled capture runs.",
        "mutates": True,
        "tool": "Outlook",
    },
    # REQ-SB-69-US-01-T04 (ADR-046 Decision 4) -- pull_email/
    # process_staged_email are two independently-dispatched capabilities
    # of the SAME email-capture-pipeline Agent-tier identity, deliberately
    # never sharing a lock (agent_schedule_registry.py's
    # dispatch_with_shared_lock for pull_email, a new dedicated
    # dispatch_with_dedicated_processing_lock for process_staged_email) --
    # this is the mechanism that makes a stalled Pull unable to block
    # already-staged mail, and a stalled Process unable to block the next
    # Pull, true by construction.
    "pull_email": {
        "id": "pull_email",
        "name": "Pull Email",
        "description": (
            "Fetch newly arrived mail from Outlook and durably stage it "
            "into .second-brain/email_staging/, without processing it yet."
        ),
        "mutates": True,
        "tool": "Outlook",
    },
    "process_staged_email": {
        "id": "process_staged_email",
        "name": "Process Staged Email",
        "description": (
            "Classify, thread, and file every already-staged email into "
            "the vault -- never touches Outlook."
        ),
        "mutates": True,
        "tool": "Vault",
    },
    "rebuild_person_note": {
        "id": "rebuild_person_note",
        "name": "Rebuild a Person Note",
        "description": "Rebuild a Person note from its own source content.",
        "mutates": True,
        "tool": "Vault",
    },
    "build_knowledge": {
        "id": "build_knowledge",
        "name": "Build My Knowledge",
        "description": "Bootstrap this agent's own knowledge via delegated research and filing.",
        "mutates": True,
        "tool": "Compass",
    },
    "write-to-vault-draft": {
        "id": "write-to-vault-draft",
        "name": "Write to Vault (Draft)",
        "description": (
            "Given a Producer agent's own generated output, write it into "
            "the vault as a new draft note. Not yet available — no real "
            "write handler has been built for it (REQ-SB-37-US-03's own "
            "Non-Goals)."
        ),
        "mutates": True,
        "tool": "Vault",
    },
    "summarize-file": {
        "id": "summarize-file",
        "name": "Summarize File",
        "description": (
            "Given a text-bearing uploaded file's extracted content, "
            "produce a Compass-generated summary of its actual content."
        ),
        "mutates": False,
        "tool": "Compass",
    },
    "propose_person_note_update": {
        "id": "propose_person_note_update",
        "name": "Propose a Person-Note Update",
        "description": (
            "Given a real, existing Person note and a described change, "
            "propose an edit reflecting it -- subject to the invoking "
            "agent's own working-mode gate; never silently applied."
        ),
        "mutates": True,
        "tool": "Vault",
    },
    # 2026-08-20 (operator-directed): retires the single monolithic
    # run_threads_cleaning_pass Skill (was one opaque call wrapping 4
    # real Jobs) in favor of one real, independently-grantable/
    # schedulable Skill per Job -- this is what lets each Job become its
    # own real Sub-Agent with a real depends_on chain, instead of one
    # collapsed Agents Map/Job Tree node (BUG-033). backfill_files/
    # populate_thread_related_links are NOT converted this pass (no
    # Sub-Agent requested for them yet) -- still reachable only via
    # librarian_housekeeping.run_threads_cleaning_pass() directly (the
    # orchestrating function itself is untouched, still callable) or the
    # existing /poc/librarian-backfill-files, /poc/librarian-populate-
    # related endpoints.
    "rename_threads": {
        "id": "rename_threads",
        "name": "Rename Threads",
        "description": (
            "Rename every real Thread directory still on its raw "
            "conversation_id slug to its own human-readable <date> "
            "<subject> stem."
        ),
        "mutates": True,
        "tool": "Vault",
    },
    "link_thread_messages": {
        "id": "link_thread_messages",
        "name": "Link Thread Messages",
        "description": (
            "Regenerate every real Thread's ## Messages section from its "
            "current messages/ folder, and link each message back to its "
            "Thread via a thread: frontmatter reference."
        ),
        "mutates": True,
        "tool": "Vault",
    },
    "backfill_thread_summaries": {
        "id": "backfill_thread_summaries",
        "name": "Summarize Threads",
        "description": (
            "Regenerate ## Summary and the opening-line sentence for "
            "every already-captured Thread note, in place."
        ),
        "mutates": True,
        "tool": "Vault",
    },
    "run_company_partner_building_pass": {
        "id": "run_company_partner_building_pass",
        "name": "Run Company and Partner Building Pass",
        "description": (
            "Run Company and Partner Building's scheduled pipeline "
            "(company-folder backfill, People retrofit) immediately."
        ),
        "mutates": True,
        "tool": "Vault",
    },
}


@mcp_server.tool()
def diagram_understanding() -> dict:
    """Given an uploaded image, identify and describe the components in
    an architecture/engineering diagram. Not yet available -- no
    multimodal-capable Provider exists yet (REQ-SB-27-US-01's own
    Non-Goals); this stub always returns an honest "not available"
    response, never a fabricated or guessed result."""
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def view_last_run() -> dict:
    """View this agent's most recent capture run result. Not yet available
    -- no real handler has been built for it (ADR-028 point 4, migrated
    verbatim from the former view_last_run Action, which also had no real
    handler); always returns an honest "not available" response, never a
    fabricated or guessed result."""
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def ask_question() -> dict:
    """Ask this agent a question grounded in the indexed vault. Not yet
    available -- no real handler has been built for it (ADR-028 point 4,
    migrated verbatim from the former ask_question Action, which also had
    no real handler); always returns an honest "not available" response,
    never a fabricated or guessed result."""
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def view_channel_status() -> dict:
    """View this agent's current channel status. Not yet available -- no
    real handler has been built for it (ADR-028 point 4, migrated verbatim
    from the former view_channel_status Action, which also had no real
    handler); always returns an honest "not available" response, never a
    fabricated or guessed result."""
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


_ANTHROPIC_PROVIDER_ID = "anthropic-claude"


@mcp_server.tool()
def web_research(query: str, agent_id: str) -> dict:
    """Given a research subject or query, gather real, current
    information from the web -- via whichever real Provider the
    INVOKING AGENT is itself linked to (operator correction, 2026-08-12,
    superseding ADR-022 point 3's original fixed-"anthropic-claude"-id
    design -- see ADR-022's own Correction addendum), not a single
    hardcoded Provider id. Only Anthropic Claude has a genuine, hosted
    server-side web-search tool (confirmed live against this codebase's
    own compass_client.py and the sibling agentic-map project's own
    gateway, which uses a dedicated Perplexity Sonar provider for real
    web search specifically because Compass/GPT-5 has none) -- an agent
    linked to any other Provider (Compass, or no Provider at all)
    honestly reports unavailability, exactly Scenario 4's existing
    shape, rather than fabricating a "researched" result from a plain,
    ungrounded completion (REQ-SB-33's own grounding guardrail).
    Honestly reports no results if a real Anthropic search genuinely
    finds nothing relevant -- never a fabricated result in any branch."""
    provider = provider_registry.get_agent_provider(agent_id)
    if (
        provider is not None
        and provider["id"] == _ANTHROPIC_PROVIDER_ID
        and provider_registry.has_real_client(_ANTHROPIC_PROVIDER_ID)
    ):
        return anthropic_client.web_search(provider["credential"], provider["model"], query)
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def summarize_file(content: str, source_description: str) -> dict:
    """Summarizes already-extracted text content via Compass
    (compass_client.summarize_content), for a file the user attached to
    an agent chat message. Never raises for ordinary control flow --
    catches CompassError and returns an honest {"status": "error", ...}
    result instead, mirroring invoke_skill's own "never raises" design
    intent (REQ-SB-27-US-01) so the router (T04) can branch on a result
    shape rather than a try/except around invoke_skill itself."""
    try:
        result = compass_client.summarize_content(content, source_description)
        return {"status": "ok", "summary": result["summary"]}
    except compass_client.CompassError as exc:
        return {"status": "error", "message": f"Summarization failed: {exc}"}


@mcp_server.tool()
def run_capture_now(agent_id: str) -> dict:
    """Run this agent's capture pipeline immediately. Preserves EXACTLY
    the real/honest-unavailable split _ACTION_HANDLERS already had before
    this migration (REQ-SB-39-US-02, ADR-029 point 5, confirmed by direct
    code inspection) -- real only for email-capture-pipeline
    (email_classification.run_capture_and_record_completion, REQ-SB-55-US-01-T08);
    every other agent, including meeting-capture/todo-capture (whose own
    real classification logic exists but is wired to the BACKGROUND
    scheduler only, never this on-demand path), gets the honest "not yet
    available" response. Do NOT wire meeting-capture/todo-capture to their
    own classification functions here -- that would be new real on-demand
    behavior this task's own Constraint forbids (a gating/declaration
    refactor, not a rewrite)."""
    if agent_id == "email-capture-pipeline":
        results = email_classification.run_capture_and_record_completion()
        return {"available": True, "message": f"Done — {len(results)} email(s) filed."}
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def pull_email(agent_id: str) -> dict:
    """Fetch newly arrived mail from Outlook and durably stage it, without
    processing it yet (REQ-SB-69-US-01-T04, ADR-046 Decision 4). Preserves
    the same real/honest-unavailable split run_capture_now already has --
    real only for email-capture-pipeline (email_pull.pull_and_stage_emails,
    T02); every other agent gets the honest "not yet available" response.
    Dispatched either through agent_schedule_registry.dispatch_with_
    shared_lock (the shared Outlook-COM lock, same as every other real
    Outlook caller) or via the scheduled tick's own inline call inside
    email_classification.run_capture_and_record_completion -- never
    through the new dedicated processing lock, which is scoped to
    process_staged_email alone."""
    if agent_id == "email-capture-pipeline":
        summary = email_pull.pull_and_stage_emails()
        return {
            "available": True,
            "message": f"Pull completed — {summary['newly_staged']} new email(s) staged.",
        }
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def rename_threads() -> dict:
    """Renames every real Thread directory still on its raw
    conversation_id slug (2026-08-20) -- a thin wrapper delegating to
    librarian_housekeeping.rename_threads(), which is what makes this
    Skill genuinely dispatchable/schedulable (agent_schedule_registry.
    create_or_update_schedule refuses any capability id that is not both
    granted AND classified "mutates": True, dispatched via skill_registry.
    invoke_skill -> this handler)."""
    return librarian_housekeeping.rename_threads()


@mcp_server.tool()
def link_thread_messages() -> dict:
    """Regenerates every real Thread's ## Messages section and links each
    message back to its Thread (2026-08-20) -- a thin wrapper delegating
    to librarian_housekeeping.link_thread_messages()."""
    return librarian_housekeeping.link_thread_messages()


@mcp_server.tool()
def backfill_thread_summaries() -> dict:
    """Regenerates ## Summary for every already-captured Thread note
    (2026-08-20) -- a thin wrapper delegating to thread_summary_backfill.
    backfill_thread_summaries(). Returns a list, not a dict, unlike its
    two Job siblings above -- wrapped under a "results" key so every
    Skill handler in this module keeps returning a dict, matching
    invoke_skill's own return-shape contract."""
    return {"results": thread_summary_backfill.backfill_thread_summaries()}


@mcp_server.tool()
def run_company_partner_building_pass() -> dict:
    """Runs Company and Partner Building's scheduled pipeline immediately
    (REQ-SB-79-US-01, ADR-058 Decision 5) -- a thin wrapper delegating to
    librarian_housekeeping.run_company_partner_building_pass(). No
    agent_id gating -- this capability has exactly one real Agent identity
    that can ever be granted it (company-and-partner-building), so there
    is no honest-unavailable branch to preserve."""
    return librarian_housekeeping.run_company_partner_building_pass()


@mcp_server.tool()
def process_staged_email(agent_id: str) -> dict:
    """Classify, thread, and file every already-staged email into the
    vault -- never touches Outlook (REQ-SB-69-US-01-T04, ADR-046 Decision
    4). Preserves the same real/honest-unavailable split run_capture_now
    already has -- real only for email-capture-pipeline
    (email_capture_pipeline.run_email_capture_pipeline, now reading
    exclusively from email_staging, T03); every other agent gets the
    honest "not yet available" response. Dispatched exclusively through
    agent_schedule_registry.dispatch_with_dedicated_processing_lock -- a
    NEW, separate asyncio.Lock scoped to email processing alone, never the
    shared Outlook-COM lock pull_email itself acquires -- this is what
    makes a stalled process_staged_email run structurally unable to block
    the next pull_email dispatch, and vice versa.

    The import of email_capture_pipeline is deliberately INSIDE this
    function body, not at module top level -- confirmed by direct testing
    (this task's own Implementation Log), NOT merely assumed: skill_tools
    -> email_classification -> vault_filing_expert -> agent_orchestration
    -> ... -> knowledge_bootstrap -> skill_registry -> skill_tools ->
    email_capture_pipeline is a REAL transitive cycle back into THIS
    module through email_classification's own other imports (not the
    direct one-hop edge run_capture_for_agent's own docstring describes),
    which surfaces as a genuine ImportError ("partially initialized
    module") whenever app.business.pipelines.email_capture_pipeline (or
    anything importing it) is the FIRST module imported in a process. By
    the time this handler actually runs, every module in that chain has
    already finished loading, so the deferred import is safe -- mirrors
    build_knowledge's/propose_person_note_update's own deferred-import
    precedent for the same reason, one layer deeper."""
    if agent_id == "email-capture-pipeline":
        from app.business.pipelines.email_capture_pipeline import run_email_capture_pipeline

        results = run_email_capture_pipeline()
        # BUG-FIX 2026-08-17: results includes per-item {"error": ...}
        # entries for staged emails that failed processing (T03's own
        # honest per-item failure funnel) -- len(results) alone silently
        # mislabels those as "filed", exactly the bug email_classification
        # .run_capture_and_record_completion's own history_text already
        # fixed for the Pull-bundled path (see that function's own
        # comment). Confirmed live: without this fix, 4 real BUG-015
        # Compass-classification failures were reported as "4 filed".
        filed = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]
        message = f"Done — {len(filed)} thread(s) updated."
        if failed:
            message += f" {len(failed)} failed (will retry next run)."
        return {"available": True, "message": message}
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def pause_schedule() -> dict:
    """Pause this agent's scheduled capture runs. Not yet available -- no
    real handler exists for this id on any agent today (REQ-SB-39-US-02,
    ADR-029 point 5, confirmed by direct code inspection); always returns
    an honest "not available" response, never a fabricated or guessed
    result."""
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def rebuild_person_note() -> dict:
    """Rebuild a Person note from its own source content. Not yet
    available -- no real handler exists for this id today (REQ-SB-39-US-02,
    ADR-029 point 5, confirmed by direct code inspection); always returns
    an honest "not available" response, never a fabricated or guessed
    result."""
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def build_knowledge(agent_id: str) -> dict:
    """Bootstrap this agent's own knowledge via delegated research and
    filing -- calls through to knowledge_bootstrap.bootstrap_agent_
    knowledge(agent_id, subject), reusing agents_router.py::
    _run_build_knowledge's own Subject-resolution and status-to-message
    translation, reshaped into this module's {"available", "message"}
    handler-return convention.

    The import of knowledge_bootstrap is deliberately INSIDE this
    function body, not at module top level -- skill_registry.py already
    imports skill_tools, and knowledge_bootstrap.py already imports
    skill_registry (its own existing Hub-routed invoke_skill call); a
    module-level import here would complete a real circular import
    (skill_tools -> knowledge_bootstrap -> skill_registry -> skill_tools).
    By the time this handler actually runs, both modules have already
    finished loading, so the deferred import is safe.

    bootstrap_agent_knowledge is genuinely async def (matching ITS OWN
    caller's async signature); invoke_skill/_dispatch_skill's own
    dispatch contract is synchronous end-to-end, and a real caller
    (agents_router.py's own async trigger_action/chat routes) may
    already be executing inside FastAPI's own active event loop when
    this handler runs -- a plain asyncio.run() call would raise
    "RuntimeError: cannot be called from a running event loop" in that
    real case. Driving the coroutine to completion from a dedicated,
    single-use thread is safe regardless of the calling thread's own
    event-loop state.

    Sets "history_recorded": True -- bootstrap_agent_knowledge already
    records exactly one real run_event/proposal entry itself, internally,
    in every branch (mirrors _run_build_knowledge's own identical flag,
    REQ-SB-36-US-02); T02's own Approve-branch skip_history guard reads
    this flag."""
    from app.business.agent_orchestration import knowledge_bootstrap

    agent = agent_registry.get_agent(agent_id)
    subject = next((s["value"] for s in agent["settings"] if s["key"] == "Subject"), agent["name"])
    coro = knowledge_bootstrap.bootstrap_agent_knowledge(agent_id, subject)
    result = concurrent.futures.ThreadPoolExecutor(max_workers=1).submit(asyncio.run, coro).result()
    message = {
        "written": f"Built knowledge — filed to {result.get('path')}.",
        "pending_approval": "Research gathered; filing paused pending approval of a new top-level vault area.",
        "no_match": f"Could not find a matching agent for the {result.get('hop')} step.",
        "no_results": "The web research step found nothing relevant.",
        "not_autonomous": f"{result.get('matched_agent_id')} is not in Autonomous mode.",
        "unavailable": result.get("message", "The Vault Filing Expert is not available."),
    }.get(result["status"], "The build-knowledge chain completed with an unexpected status.")
    return {"available": True, "message": message, "history_recorded": True}


@mcp_server.tool()
def write_to_vault_draft() -> dict:
    """Given a Producer agent's own generated output, write it into the
    vault as a new draft note. Not yet available — no real write handler
    has been built for it (REQ-SB-37-US-03's own Non-Goals, ADR-031 point
    2). This stub always returns an honest "not available" response,
    never a fabricated or guessed result — mirrors
    diagram_understanding's exact honest-unavailable shape."""
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


@mcp_server.tool()
def propose_person_note_update(
    note_path: str,
    person_name: str,
    instruction: str,
    agent_id: str,
    subject_kind: str | None = None,
    subject_note_stem: str | None = None,
    already_approved: bool = False,
) -> dict:
    """Proposes (or, once already_approved, applies) one described edit
    to an already-resolved, real, existing Person note (ADR-038 points
    3/6/7). NEVER creates a Person note, NEVER guesses a match -- the
    caller (graph.py's own _propose_person_note_update node, T05) has
    already resolved note_path via a real, read-only name lookup
    before this handler is ever reached.

    already_approved=True (T04's own seam, reached only via a
    just-approved Supervised Pending Approval) -- the user's own
    "Approve" click already IS the human confirmation (Scenario 2);
    writes directly via vault_writer.append_person_note_update_line
    and returns {"status": "written", ...}.

    already_approved=False (default -- the gate's own Manual/
    Autonomous fallthrough, which has zero human click of any kind in
    its own dispatch path) -- never writes as a direct, unconfirmed
    side effect (this story's own unqualified Constraint). Records an
    explicitly confirmable/discardable in-thread proposal via
    person_note_proposals.create_proposal (T01) instead, and returns
    {"status": "proposed", "proposal_id": ..., ...}.

    The import of person_note_proposals is deliberately INSIDE this
    function body, not at module top level -- mirrors build_knowledge's
    own already-documented reason one layer over: a module-level
    import here would complete a real circular import (skill_tools ->
    person_note_proposals -> threads -> graph (T05) -> skill_registry
    -> skill_tools), confirmed by direct tracing of the real import
    graph. By the time this handler actually runs, every module in
    that chain has already finished loading, so the deferred import is
    safe.

    subject_kind/subject_note_stem are None when this handler is
    reached from a context with no owning Cockpit thread (e.g. a
    one-on-one agent chat outside any Cockpit, agents_router.py's own
    chat() -- the SAME run_agent_conversation function serves both
    call sites) -- this story's own 6 ACs are all Cockpit-scoped, so
    that case gets an honest, non-crashing refusal, never a silent
    write and never an unhandled error."""
    if already_approved:
        vault_writer.append_person_note_update_line(note_path, f"- {instruction}")
        return {
            "status": "written",
            "message": f"Updated {person_name}'s note.",
            "note_path": note_path,
        }
    if not subject_kind or not subject_note_stem:
        return {
            "status": "unavailable",
            "message": "Proposing a Person-note edit is only available inside a Cockpit chat today.",
        }
    from app.business.cockpit import person_note_proposals

    proposal = person_note_proposals.create_proposal(
        subject_kind, subject_note_stem, note_path, person_name, instruction
    )
    return {
        "status": "proposed",
        "proposal_id": proposal["id"],
        "message": f"Proposed an update to {person_name}'s note — awaiting confirmation.",
        "note_path": note_path,
    }
