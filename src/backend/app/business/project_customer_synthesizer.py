"""Project & Customer Status Synthesizer (`REQ-SB-57`) -- the sole owner of
a Project's own `## Glimpse`/`log.md` AND a Customer's own `## Glimpse`/
`log.md`/`## Background` (`REQ-SB-54` point 7's ownership rule, actually
enforced starting here). No other module in this codebase may call
`vault_writer.replace_body_section` against a Project's or Customer's own
concept file, or `vault_writer.append_person_note_update_line` against
either one's own `log.md`, directly -- every real evidence-change call
site (a Thread update, a Meeting link-in, a Route-to-Project approval, a
Project-level cascade under a Customer) only ever TRIGGERS resynthesis
through this module's own public functions; it never assembles or writes
`## Glimpse`/`log.md`/`## Background` content itself. `## Background` is
the one exception routed through a Pending Approval rather than written
directly by a Synthesizer pass (`T04`'s own `_propose_background_
amendment`/`finalize_background_amendment_proposal` pair, below) -- never
a silent rewrite, same "propose, human confirms" posture as `route_to_
project`.

One Agent-tier identity (`"project-customer-synthesizer"`, registered in
`agent_registry.py`'s own `_SEED_AGENTS`), triggered purely by real
evidence change -- NEVER on a fixed schedule (`REQ-SB-57`'s own Context)
-- with `synthesize_project`/`synthesize_customer` as its own tier-less
Jobs underneath it (decomposer's own implementation choice,
`REQ-SB-57-US-01`'s own `## Notes`). `synthesize_customer` is CASCADED
from `synthesize_project`'s own end only -- it never independently
re-derives a conclusion from its own separate `status` comparison
(`T02`'s own addition, `REQ-SB-57-US-01-T02`).

History-line "genuinely concludes" bar (`architecture.md` -> "Project &
Customer Synthesizer", operator-confirmed 2026-08-18): a Project's own
`status` enum is `active | on_hold | won | lost | renewed`; a dated
`log.md` line is appended iff `status` (read fresh, at the START of this
pass) differs from the PRIOR pass's own observed value
(`last_synthesized_status`) AND the new value is one of
`won`/`lost`/`renewed` -- never on `active`/`on_hold`, and never on a
repeated observation of an already-terminal value (idempotent)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.data_access import compass_client, vault_writer

_CONCLUDING_STATUSES = {"won", "lost", "renewed"}


def resync_project_from_thread(thread_path) -> dict | None:
    """The ONE shared trigger-call-site helper both this task's own
    Thread-pipeline node and `T03`'s Meeting-link wiring call -- neither
    real trigger call site ever reads/writes Glimpse content itself, they
    only call through here. Reads the Thread's own CURRENT frontmatter
    fresh on every call (`vault_writer.read_note`) -- never trusts a
    caller-passed customer/project -- and returns `None`, a genuine no-op
    touching no file, for a Thread with no `project` frontmatter key set
    yet (a not-yet-routed Thread; routing only happens later, at a
    separate operator Approve, via `finalize_thread_project_routing`)."""
    path = Path(thread_path)
    frontmatter, _ = vault_writer.read_note(path)
    project = frontmatter.get("project")
    if not project:
        return None
    customer = frontmatter.get("customer")
    evidence_text = vault_writer.read_body_section(path, "## Summary")
    return synthesize_project(customer, project, evidence_text=evidence_text)


def _build_project_glimpse(customer: str, project: str) -> str:
    """Mechanical rollup -- one bullet per currently-linked Thread, each
    carrying a real `[[wikilink]]` to it plus that Thread's own
    already-synthesized `## Summary` content. Never a second, divergent
    Compass call for Glimpse content (mirrors `consult_librarian`'s own
    documented "never a second Compass call" precedent) -- this function
    only reads and reassembles content `thread_match_merge` already
    produced."""
    thread_paths = vault_writer.list_threads_for_project(customer, project)
    if not thread_paths:
        return "_No linked Threads yet._"
    lines: list[str] = []
    for thread_path in thread_paths:
        thread_frontmatter, _ = vault_writer.read_note(thread_path)
        thread_name = thread_frontmatter.get("thread_name") or thread_path.stem
        summary_excerpt = vault_writer.read_body_section(thread_path, "## Summary")
        lines.append(f"- [[{thread_path.stem}]] {thread_name} — {summary_excerpt}")
    return "\n".join(lines)


def synthesize_project(customer: str, project: str, evidence_text: str = "") -> dict:
    """The Project Synthesizer's own real Job -- the ONLY function in this
    codebase, after this task, allowed to touch a Project's own `##
    Glimpse` or `log.md` (`REQ-SB-54` point 7). Fully regenerates `##
    Glimpse` via `replace_body_section` (never incrementally patched,
    `REQ-SB-54` point 8), then applies the History-line conclusion trigger
    (module docstring, above) against the Project's own concept-file
    `status`/`last_synthesized_status` frontmatter, unconditionally
    writing `last_synthesized_status = status` afterward regardless of
    whether a line was appended -- what makes a later, unchanged
    re-observation of an already-terminal `status` a true no-op.

    `evidence_text` is threaded through untouched into the returned dict
    and into the `synthesize_customer` cascade call below, for `T04`'s
    own later use -- this task's own code does nothing else with it.
    Ends by cascading into `synthesize_customer` (`REQ-SB-57-US-01-T02`)
    -- passing `concluded_project=project` only when THIS call itself
    just observed the conclusion, `None` otherwise; `synthesize_customer`
    never independently re-derives that decision (Ownership rule)."""
    paths = vault_writer.project_directory_paths(customer, project)
    concept_path = paths["concept"]

    glimpse_content = _build_project_glimpse(customer, project)
    vault_writer.replace_body_section(
        concept_path, "## Glimpse", glimpse_content,
        caller="project_customer_synthesizer.synthesize_project",
    )

    frontmatter, _ = vault_writer.read_note(concept_path)
    current_status = frontmatter.get("status") or "active"
    last_synthesized_status = frontmatter.get("last_synthesized_status") or "active"

    concluded = (
        current_status != last_synthesized_status
        and current_status in _CONCLUDING_STATUSES
    )
    if concluded:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        vault_writer.append_person_note_update_line(
            paths["log"],
            f"{today} — Project \"{project}\" status changed to {current_status}.",
        )
    vault_writer.upsert_frontmatter_key(concept_path, "last_synthesized_status", current_status)

    synthesize_customer(
        customer,
        concluded_project=project if concluded else None,
        evidence_text=evidence_text,
    )

    return {
        "customer": customer,
        "project": project,
        "concluded": concluded,
        "latest_evidence_text": evidence_text,
    }


def _build_customer_glimpse(customer: str) -> str:
    """Mechanical rollup -- one bullet per currently active/on_hold
    Project under `customer` (`architecture.md` -> "Project & Customer
    Synthesizer", Customer rollup rule), each carrying that Project's own
    current `status`. Never an LLM call -- reuses `list_customer_
    projects`'s own already-honest frontmatter read, mirroring `_build_
    project_glimpse`'s own "reuse already-synthesized content" precedent
    one level up."""
    active_projects = [
        project
        for project in vault_writer.list_customer_projects(customer)
        if project["status"] in {"active", "on_hold"}
    ]
    if not active_projects:
        return "_No active Projects yet._"
    return "\n".join(
        f"- **{project['project']}** — {project['status']}" for project in active_projects
    )


def _propose_background_amendment(customer: str, fact: str, source_description: str) -> dict:
    """Mirrors `vault_filing_expert._create_cross_cutting_proposal`'s own
    exact shape (`Implementation/Learnings.md`, `SPRINT-050`,
    3x-confirmed canonical "propose in the owning module, finalize via
    `_APPROVAL_HANDLERS`" shape) -- a LOCAL (not module-level)
    `pending_approval_registry` import, `trigger="direct"` (never
    `"background"`: a single synthesis pass can legitimately coexist with
    other distinct proposals across different Customers/passes, and
    `"background"`'s own idempotency guard would silently collapse them,
    same reasoning already established for `route_to_project`/`detect_
    recurring_pattern`/`_create_cross_cutting_proposal`)."""
    from app.business import pending_approval_registry  # local import -- mirrors vault_filing_expert's own precedent

    payload = {"customer": customer, "fact": fact}
    description = (
        f"Project & Customer Synthesizer proposes a Background amendment "
        f"for \"{customer}\": {fact} ({source_description})"
    )
    record = pending_approval_registry.create_pending_approval(
        agent_id="project-customer-synthesizer",
        trigger="direct",
        action_id="propose_background_amendment",
        description=description,
        payload=payload,
    )
    return {"status": "pending_approval", "approval_id": record["id"]}


def finalize_background_amendment_proposal(payload: dict) -> dict:
    """Called only once the operator approves `_propose_background_
    amendment`'s own record (`app/api/pending_approvals_router.py`'s
    `_APPROVAL_HANDLERS["propose_background_amendment"]`) -- performs the
    deferred write, never called for a declined record. Deliberately
    mechanical (read the Customer's own current `## Background`, append
    one new bullet), NOT a second Compass call (`REQ-SB-54` point 5's own
    "folded into prose" precedent) -- keeps this deferred write fully
    deterministic."""
    customer = payload["customer"]
    fact = payload["fact"]
    paths = vault_writer.customer_directory_paths(customer)
    concept_path = paths["concept"]

    existing_background = vault_writer.read_body_section(concept_path, "## Background")
    new_bullet = f"- {fact}"
    combined_content = f"{existing_background}\n{new_bullet}" if existing_background else new_bullet
    vault_writer.replace_body_section(
        concept_path, "## Background", combined_content,
        caller="project_customer_synthesizer.finalize_background_amendment_proposal",
    )

    return {
        "path": str(concept_path),
        "message": f"Approved — Background amended for {customer}.",
    }


def synthesize_customer(
    customer: str, concluded_project: str | None = None, evidence_text: str = "",
) -> dict:
    """The Customer Synthesizer's own real Job -- the ONLY function in
    this codebase, after this task, allowed to touch a Customer's own
    `## Glimpse` or `log.md` (`REQ-SB-54` point 7). Fully regenerates
    `## Glimpse` as a rollup of every currently active/on_hold Project
    under `customer` (`architecture.md` -> "Project & Customer
    Synthesizer", Customer rollup rule) via `replace_body_section` --
    never incrementally patched (`REQ-54` point 8).

    `concluded_project` drives the History-line append -- this function
    NEVER independently re-derives "did something conclude" from its own
    separate `status` comparison (Ownership rule, `REQ-SB-54` point 7:
    "a Project update TRIGGERS Customer resynthesis," never decides on
    its own). `synthesize_project`'s own end is the only caller that
    passes a non-`None` `concluded_project`, exactly once per genuine
    conclusion it itself observed.

    `evidence_text`, when non-empty, is this Customer's second, independent
    trigger (`T04`, `REQ-SB-57-US-01-AC-03`): reads the Customer's own
    CURRENT `## Background` prose first, then asks `compass_client.
    detect_customer_durable_fact` whether `evidence_text` names a
    genuinely new durable fact not already reflected there. On
    `has_durable_fact: True`, proposes a `propose_background_amendment`
    Pending Approval via `_propose_background_amendment` -- `## Background`
    itself is NEVER rewritten here, only on later operator approval
    (`finalize_background_amendment_proposal`). Any exception from the
    detection call (mirrors `consult_librarian`'s own honest, non-crashing
    posture, `Implementation/Learnings.md` `SPRINT-050`) is caught and
    never aborts the Glimpse/History work above, which is already durable
    by the time this runs. An empty `evidence_text` (e.g. `T02`'s own
    first-routing call site) makes no Compass call and proposes nothing."""
    paths = vault_writer.customer_directory_paths(customer)
    concept_path = paths["concept"]

    glimpse_content = _build_customer_glimpse(customer)
    vault_writer.replace_body_section(
        concept_path, "## Glimpse", glimpse_content,
        caller="project_customer_synthesizer.synthesize_customer",
    )

    if concluded_project is not None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        vault_writer.append_person_note_update_line(
            paths["log"],
            f"{today} — Project \"{concluded_project}\" concluded.",
        )

    amendment_proposed = False
    if evidence_text:
        try:
            existing_background = vault_writer.read_body_section(concept_path, "## Background")
            detection = compass_client.detect_customer_durable_fact(
                evidence_text=evidence_text,
                customer=customer,
                existing_background=existing_background,
            )
            if detection["has_durable_fact"]:
                _propose_background_amendment(
                    customer,
                    detection["fact"],
                    source_description=f"evidence observed while resynthesizing \"{customer}\"",
                )
                amendment_proposed = True
        except Exception:
            pass

    return {
        "customer": customer,
        "amendment_proposed": amendment_proposed,
    }
