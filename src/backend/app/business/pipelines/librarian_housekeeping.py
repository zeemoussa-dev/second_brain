"""The Librarian's first housekeeping pipeline (`REQ-SB-72-US-01`, see
`ADR-049` in `Implementation/Architecture/ADR.md`) -- ongoing, self-running
vault hygiene over the real Thread corpus `REQ-SB-71-US-02` captured, the
deliberate opposite of that story's own explicitly manual/API-only capture
pipelines: Thread rename (this task, `T03`), Files/OKF backfill (`T04`),
company-mention detection (`T05`), `## Related` ownership transfer (`T06`),
company folder backfill (`T07`), and the orchestrating Agent/Section/
schedule identity (`T08`/`T09`) all live in this one module, composed
additively as each task lands -- never a second, divergent module per Job.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.business import agent_registry, customer_hub_linking, email_classification, partner_hub_linking, people_extraction, section_registry
from app.config import settings
from app.data_access import compass_client, vault_writer

_LEADING_RE_PREFIX = re.compile(r"^(?:re:\s*)+", re.IGNORECASE)


def _strip_leading_re_prefix(subject: str) -> str:
    """Strips a leading `"Re: "` (case-insensitive, possibly repeated --
    e.g. `"Re: Re: Ewec Discussion"`) from a Thread's own `thread_name`,
    so the renamed stem reads as the real subject, not a reply marker
    (`REQ-SB-72-US-01-T03`, `ADR-049` Decision 2)."""
    return _LEADING_RE_PREFIX.sub("", subject).strip()


def _latest_message_received_date(thread_directory) -> str | None:
    """Honest fallback date source when a Thread's own `last_message_at`
    frontmatter is not yet populated (real, disclosed gap found live
    against the real vault: `last_message_at` is written only once Stage 2
    (`synthesize_thread`) has run for a Thread at least once, and most of
    the real Thread corpus has only been through Stage 1 raw capture so
    far) -- reads every raw message note under the Thread's own current
    `messages/` directory (sorted by filename, which sorts by
    `received[:10]` first, mirroring `synthesize_thread`'s own identical
    ordering contract) and returns the LATEST one's own real `received`
    frontmatter field, never a guessed or placeholder date. Returns `None`
    only for the structurally-impossible case of a Thread directory with
    no raw messages under it at all."""
    messages_dir = thread_directory / "messages"
    message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []
    if not message_paths:
        return None
    frontmatter, _ = vault_writer.read_note(message_paths[-1])
    return frontmatter.get("received")


def rename_threads() -> dict:
    """The Rename Job (`REQ-SB-72-US-01-T03`, `ADR-049` Decision 2) -- for
    every real Thread whose directory still matches its own raw
    `conversation_id` slug (i.e. not already renamed), computes its
    human-readable `<date> <subject-without-Re->` stem from the Thread's
    own real frontmatter and renames the whole directory via `vault_
    writer.rename_thread_directory`. `date` prefers the Thread's own
    `last_message_at` frontmatter (populated once Stage 2 has run); when
    absent, falls back to the latest real raw message's own `received`
    date (see `_latest_message_received_date`) -- both are real, honest
    derivations from the Thread's own actual data, never a guess.

    Idempotent by construction: an already-renamed Thread's directory name
    no longer matches its raw `conversation_id` slug, so it is skipped, not
    re-renamed. A genuine `<date> <subject>` stem collision (`FileExistsError`
    from `rename_thread_directory`) is caught per-Thread -- skip-and-report,
    never aborting the whole run.

    On every successful rename, in the SAME loop iteration (`REQ-SB-73-
    US-01-T02`, `ADR-054` Decision 2), also fans out the new stem to every
    one of that Thread's own current `messages/*.md` via `vault_writer.
    upsert_frontmatter_key(message_path, "thread", f"[[{new_stem}]]")` --
    a zero-staleness-window guarantee: no message is ever left pointing at
    the Thread's own stale, pre-rename slug, even momentarily. Runs only
    after `rename_thread_directory` has already succeeded for that Thread,
    so a genuine collision (caught below) never leaves any message
    mid-way through a fan-out.

    Returns `{"renamed": [{"conversation_id", "old_path", "new_path"}],
    "skipped_already_renamed": [conversation_id, ...], "collisions":
    [{"conversation_id", "attempted_stem", "error"}]}`."""
    renamed: list[dict] = []
    skipped_already_renamed: list[str] = []
    collisions: list[dict] = []

    for concept_path in vault_writer.list_thread_notes():
        directory = concept_path.parent
        frontmatter, _ = vault_writer.read_note(concept_path)
        conversation_id = frontmatter.get("conversation_id", "")

        if directory.name != vault_writer._slugify(conversation_id):
            skipped_already_renamed.append(conversation_id)
            continue

        subject = _strip_leading_re_prefix(frontmatter.get("thread_name", ""))
        last_message_at = frontmatter.get("last_message_at") or _latest_message_received_date(
            directory
        )
        date = (last_message_at or "")[:10]
        new_stem = f"{date} {subject}".strip()
        new_directory = directory.parent / vault_writer._slugify(new_stem)

        try:
            new_concept_path = vault_writer.rename_thread_directory(directory, new_directory)
        except FileExistsError as exc:
            collisions.append({
                "conversation_id": conversation_id,
                "attempted_stem": new_stem,
                "error": str(exc),
            })
            continue

        new_messages_dir = new_concept_path.parent / "messages"
        new_message_paths = sorted(new_messages_dir.glob("*.md")) if new_messages_dir.exists() else []
        for message_path in new_message_paths:
            vault_writer.upsert_frontmatter_key(
                message_path, "thread", f"[[{new_concept_path.stem}]]"
            )

        renamed.append({
            "conversation_id": conversation_id,
            "old_path": str(directory),
            "new_path": str(new_concept_path.parent),
        })

    return {
        "renamed": renamed,
        "skipped_already_renamed": skipped_already_renamed,
        "collisions": collisions,
    }


def link_thread_messages() -> dict:
    """The Bidirectional Thread <-> Message Linking Job (`REQ-SB-73-US-01-T01`,
    `ADR-054` Decision 1) -- for every real Thread (`list_thread_notes()`),
    regenerates `## Messages` wholesale from the Thread's own CURRENT
    `messages/*.md` glob (sorted by filename, mirroring every sibling Job's
    own chronological-by-filename ordering) as one `"- [[<message-stem>]]"`
    bullet per message, via `vault_writer.insert_body_section_if_missing`
    then `vault_writer.replace_body_section(..., caller="librarian_
    housekeeping.link_thread_messages")` -- mirrors `backfill_files()`'s own
    exact two-call sequence for `## Files`, never incrementally patched. A
    Thread with zero messages under `messages/` is left with no `## Messages`
    section at all, mirroring `## Files`'s own "nothing to list, no empty
    header" contract.

    For every message under that same glob, calls `vault_writer.upsert_
    frontmatter_key(message_path, "thread", f"[[{concept_path.stem}]]")` --
    the Thread's own CURRENT stem (already-final if this Job runs after the
    Rename Job in the same pass). `upsert_frontmatter_key` alone satisfies
    write-new (a message with no `thread:` field yet gets one), self-heal (a
    stale pre-rename slug gets corrected), and true-no-op-on-rerun (an
    already-correct value triggers no write at all).

    Returns `{"threads_processed": [conversation_id, ...], "messages_linked":
    [{"conversation_id", "message_stem", "linked": bool}, ...]}` --
    `"linked"` mirrors `upsert_frontmatter_key`'s own return value (`True`
    only when the file was actually written -- inserted or corrected), so a
    true no-op rerun is honestly distinguishable from a real write."""
    threads_processed: list[str] = []
    messages_linked: list[dict] = []

    for concept_path in vault_writer.list_thread_notes():
        thread_directory = concept_path.parent
        frontmatter, _ = vault_writer.read_note(concept_path)
        conversation_id = frontmatter.get("conversation_id", "")
        messages_dir = thread_directory / "messages"
        message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []

        if not message_paths:
            continue

        threads_processed.append(conversation_id)

        content = "\n".join(f"- [[{message_path.stem}]]" for message_path in message_paths)
        vault_writer.insert_body_section_if_missing(concept_path, "## Messages")
        vault_writer.replace_body_section(
            concept_path, "## Messages", content,
            caller="librarian_housekeeping.link_thread_messages",
        )

        for message_path in message_paths:
            linked = vault_writer.upsert_frontmatter_key(
                message_path, "thread", f"[[{concept_path.stem}]]"
            )
            messages_linked.append({
                "conversation_id": conversation_id,
                "message_stem": message_path.stem,
                "linked": linked,
            })

    return {
        "threads_processed": threads_processed,
        "messages_linked": messages_linked,
    }


def _companion_file_slug(message_id: str, filename: str) -> str:
    """Mirrors `email_classification.write_file_companion`'s own
    `file_slug = f"{hash8(message_id)}-{filename}"` convention verbatim
    (`REQ-SB-71-US-02-T07`) -- reused here, not re-derived, so this Job's
    own pre-existence check agrees exactly with where `write_file_companion`
    itself would create (or already has created) a companion."""
    message_hash8 = hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:8]
    return f"{message_hash8}-{filename}"


def _condensed_summary_blurb(summary: str, max_len: int = 200) -> str:
    """Collapses a companion note's own (potentially multi-line, full)
    `## Summary` into one short, single-line blurb for a `## Files` list
    entry -- whitespace-collapsed, truncated with a trailing `...` beyond
    `max_len` characters. Never touches the companion note's own real
    `## Summary` content itself, which stays exactly as `write_file_
    companion` wrote it -- this is a display-only condensation."""
    collapsed = " ".join(summary.split())
    if len(collapsed) <= max_len:
        return collapsed
    return collapsed[:max_len].rstrip() + "..."


def backfill_files() -> dict:
    """The Files Backfill Job (`REQ-SB-72-US-01-T04`, `ADR-049` Decision 3)
    -- for every real attachment Stage 1 already durably persisted under
    `Work/Threads/attachments/...` with no `files/<slug>/` companion yet,
    creates one via the existing, unchanged `email_classification.write_
    file_companion` -- never a second, divergent companion primitive. Then
    writes a new, structured `## Files` section onto the owning Thread's
    own concept file, wholesale-regenerated (never appended) from the
    Thread's own CURRENT, complete companion set -- idempotent by
    construction: re-running never creates a duplicate companion (checked
    via the SAME `file_slug` convention `write_file_companion` itself uses,
    before ever calling it) and never duplicates a `## Files` entry.

    Operates on each Thread's own CURRENT `messages/` directory (via `list_
    thread_notes()`'s own already-current path) -- correct for both renamed
    and not-yet-renamed Threads, no extra resolution step needed.

    A Thread with zero companioned attachments (the common case) is left
    with no `## Files` section at all -- nothing to list, never an empty
    header cluttering every Thread in the vault.

    Returns `{"companioned": [{"conversation_id", "filename"}, ...],
    "already_companioned": [{"conversation_id", "filename"}, ...],
    "failed": [{"conversation_id", "filename", "summary_error"}, ...],
    "threads_updated": [conversation_id, ...]}` -- `"failed"` is an
    additive key (real, disclosed gap found live: `write_file_companion`
    honestly returns `{"saved": False, "summary_error": ...}` WITHOUT
    creating any companion at all for a genuinely non-extractable
    attachment, e.g. a scanned/image-only PDF with no embedded text layer
    -- this Job never crashes on that honest failure, and that attachment
    is simply left out of the Thread's own `## Files` list until it can be
    extracted, mirroring `summarize_attachment`'s own established
    "summary_error, never blocks" posture one layer over)."""
    companioned: list[dict] = []
    already_companioned: list[dict] = []
    failed: list[dict] = []
    threads_updated: list[str] = []

    for concept_path in vault_writer.list_thread_notes():
        thread_directory = concept_path.parent
        frontmatter, _ = vault_writer.read_note(concept_path)
        conversation_id = frontmatter.get("conversation_id", "")
        messages_dir = thread_directory / "messages"
        message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []

        thread_files_entries: list[dict] = []
        for message_path in message_paths:
            message_frontmatter, _ = vault_writer.read_note(message_path)
            message_id = message_frontmatter.get("message_id", "")
            received_date = (message_frontmatter.get("received") or "")[:10]

            for attachment_path in vault_writer.staged_attachment_files(conversation_id, message_id):
                filename = attachment_path.name
                file_slug = _companion_file_slug(message_id, filename)
                companion_dir = thread_directory / "files" / vault_writer._slugify(file_slug)
                companion_path = companion_dir / f"{vault_writer._slugify(file_slug)}.md"

                if companion_path.exists():
                    already_companioned.append({
                        "conversation_id": conversation_id, "filename": filename,
                    })
                else:
                    write_result = email_classification.write_file_companion(
                        attachment_path, message_id, thread_directory
                    )
                    if not companion_path.exists():
                        failed.append({
                            "conversation_id": conversation_id,
                            "filename": filename,
                            "summary_error": write_result.get("summary_error", "unknown failure"),
                        })
                        continue
                    companioned.append({
                        "conversation_id": conversation_id, "filename": filename,
                    })

                summary = vault_writer.read_body_section(companion_path, "## Summary")
                thread_files_entries.append({
                    "filename": filename,
                    "date": received_date,
                    "summary": _condensed_summary_blurb(summary),
                    "companion_stem": companion_path.stem,
                })

        if thread_files_entries:
            content = "\n".join(
                f"- **{entry['filename']}** ({entry['date']}) — "
                f"{entry['summary']} — [[{entry['companion_stem']}]]"
                for entry in thread_files_entries
            )
            vault_writer.insert_body_section_if_missing(concept_path, "## Files")
            vault_writer.replace_body_section(
                concept_path, "## Files", content,
                caller="librarian_housekeeping.backfill_files",
            )
            threads_updated.append(conversation_id)

    return {
        "companioned": companioned,
        "already_companioned": already_companioned,
        "failed": failed,
        "threads_updated": threads_updated,
    }


_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def _normalize_company_name(name: str) -> str:
    """Lowercased, punctuation-collapsed normalization for comparing a
    model-proposed company name against a known entity's own name --
    `"Ewec"`/`"EWEC"`/`"E.W.E.C."` all normalize identically. Used both for
    exact-match classification and as the basis for the fuzzy/partial
    check below."""
    return _NON_ALPHANUMERIC.sub(" ", name.lower()).strip()


def _fuzzy_match_known_entity(name: str, known_names: list[str]) -> str | None:
    """A real, disclosed, honest heuristic for "plausibly matches an
    existing entry under a different spelling" (`REQ-SB-72-US-01-T05`,
    `ADR-049` Decision 5) -- NOT a fuzzy-matching library (none is a
    dependency of this codebase); a normalized substring check either
    direction (the proposed name contains, or is contained in, a known
    name's own normalized form). Returns the matched known name, or
    `None` if no known name plausibly overlaps. Never used to auto-accept
    an entity -- only ever routes a mention to `"ambiguous"` classification
    for a human to resolve via Pending Approval (`T07`)."""
    normalized = _normalize_company_name(name)
    if not normalized:
        return None
    for known in known_names:
        known_normalized = _normalize_company_name(known)
        if not known_normalized:
            continue
        if normalized in known_normalized or known_normalized in normalized:
            return known
    return None


def detect_mentioned_companies_for_thread(thread_content: str, primary_customer: str) -> dict:
    """The business-layer wrapper (`REQ-SB-72-US-01-T05`, `ADR-049`
    Decision 5) both `T06` (`## Related` company wikilinks) and `T07`
    (Customer folder backfill) consume -- calls `compass_client.detect_
    mentioned_companies`, then RE-CHECKS every returned mention in Python
    against `vault_writer.list_known_customers()`/`list_known_partners()`
    (the SAME pre-fetched lists, never a second, divergent lookup) --
    mirrors `_maybe_create_cross_cutting_proposal`'s own exact discipline
    (`ADR-021` point 2). `primary_customer` itself is excluded from the
    result entirely -- it is the Thread's own Customer, not something
    "mentioned."

    Classifies each mention into exactly one of:
    - `"known"` -- an exact (normalized) match against an existing known
      customer/partner name -- a real, already-known company to link, no
      action beyond a wikilink. The classified entry's own `"name"` is the
      KNOWN list's own exact spelling (never the model's own variant), so a
      downstream wikilink resolves to the SAME existing hub note.
    - `"new_unambiguous"` -- no fuzzy/partial match against either known
      list, and the model's own confidence is `"high"` -- Tier-1-shaped,
      safe to auto-create (`T07`).
    - `"ambiguous"` -- plausibly matches an existing entry under a
      different spelling (`_fuzzy_match_known_entity`), OR the model itself
      flagged `"low"` confidence -- Tier-2-shaped, routes to Pending
      Approval (`T07`).

    On a `compass_client.CompassError`, returns `{"error": str, "mentions":
    []}` -- never raises, never fabricates a result, mirrors this
    codebase's own honest-degradation posture (`synthesize_thread`'s
    `summary_error` pattern)."""
    try:
        response = compass_client.detect_mentioned_companies(
            thread_content, "Thread company-mention detection"
        )
    except compass_client.CompassError as exc:
        return {"error": f"Company-mention detection failed: {exc}", "mentions": []}

    known_customers = vault_writer.list_known_customers()
    known_partners = vault_writer.list_known_partners()
    known_entities = known_customers + known_partners

    classified: list[dict] = []
    for mention in response["mentions"]:
        name = mention["name"]
        confidence = mention.get("confidence", "low")

        if _normalize_company_name(name) == _normalize_company_name(primary_customer):
            continue  # not "mentioned" -- it's the Thread's own Customer

        exact_match = next(
            (
                known for known in known_entities
                if _normalize_company_name(known) == _normalize_company_name(name)
            ),
            None,
        )
        if exact_match is not None:
            classified.append({"name": exact_match, "classification": "known"})
            continue

        if _fuzzy_match_known_entity(name, known_entities) is not None or confidence == "low":
            classified.append({"name": name, "classification": "ambiguous"})
        else:
            classified.append({"name": name, "classification": "new_unambiguous"})

    return {"mentions": classified}


def _thread_full_content(messages_dir) -> str:
    """Assembles a Thread's full concatenated raw-message content, the SAME
    shape `synthesize_thread` already composes as `full_content` (mirrored
    here, not imported, since `synthesize_thread` builds it from an
    already-in-memory `messages` list local to that function) -- reused by
    `populate_thread_related_links` as the grounding text for `T05`'s own
    company-mention detection call."""
    message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []
    parts: list[str] = []
    for message_path in message_paths:
        frontmatter, body = vault_writer.read_note(message_path)
        parts.append(
            f"From: {frontmatter.get('sender', '')} <{frontmatter.get('sender_email', '')}>\n"
            f"Received: {frontmatter.get('received', '')}\n"
            f"Subject: {frontmatter.get('subject', '')}\n\n{body.strip()}"
        )
    return "\n\n---\n\n".join(parts)


def populate_thread_related_links() -> dict:
    """The `## Related` ownership-transfer Job (`REQ-SB-72-US-01-T06`,
    `ADR-049` Decision 4) -- the Librarian's OWN sole caller for `##
    Related` going forward, replacing `synthesize_thread`'s own retired
    write. For every real Thread, reads its current `customer`/
    `participants`/`project` frontmatter and its full `messages/` content,
    calls `T05`'s `detect_mentioned_companies_for_thread`, and fully
    regenerates `## Related` via `email_classification.build_thread_
    related_wikilinks` -- extended with every `"known"`/`"new_unambiguous"`
    company mention. An `"ambiguous"` mention is NEVER wikilinked here --
    genuinely unresolved, honest-omission-style, exactly like an unmatched
    Person/Project (linking it would contradict the very Pending-Approval
    gate `T07` puts it behind).

    Returns `{"updated": [conversation_id, ...]}`."""
    updated: list[str] = []

    for concept_path in vault_writer.list_thread_notes():
        thread_directory = concept_path.parent
        frontmatter, _ = vault_writer.read_note(concept_path)
        conversation_id = frontmatter.get("conversation_id", "")
        customer = frontmatter.get("customer") or "Unsorted"
        participants = frontmatter.get("participants") or []
        project = frontmatter.get("project")

        full_content = _thread_full_content(thread_directory / "messages")
        detection = detect_mentioned_companies_for_thread(full_content, primary_customer=customer)
        mentioned_companies = [
            mention["name"] for mention in detection["mentions"]
            if mention["classification"] in ("known", "new_unambiguous")
        ]

        related_content = email_classification.build_thread_related_wikilinks(
            customer, participants, project, mentioned_companies=mentioned_companies,
        )
        vault_writer.replace_body_section(
            concept_path, "## Related", related_content,
            caller="librarian_housekeeping.populate_thread_related_links",
        )
        updated.append(conversation_id)

    return {"updated": updated}


def _create_librarian_company_link_proposal(
    entity_name: str, reason: str, thread_path: str, requesting_agent_id: str = "company-and-partner-building",
) -> dict:
    """Mirrors `vault_filing_expert._create_cross_cutting_proposal`'s own
    exact shape (`REQ-SB-72-US-01-T07`, `ADR-049` Decision 5) -- a LOCAL
    (not module-level) `pending_approval_registry` import, `trigger=
    "direct"` (never `"background"`: a single housekeeping pass can
    legitimately produce multiple distinct ambiguous findings across
    different Threads, and `"background"`'s own idempotency guard would
    silently collapse them). Never a second, divergent placement/proposal
    mechanism -- `ADR-021` point 2's own precedent, reused by analogy."""
    from app.business import pending_approval_registry  # local import -- see _create_cross_cutting_proposal's own precedent for why

    payload = {
        "entity_name": entity_name,
        "reason": reason,
        "thread_path": thread_path,
        "requesting_agent_id": requesting_agent_id,
    }
    description = (
        f"The Librarian's housekeeping pass flags a possibly-ambiguous "
        f"company mention: \"{entity_name}\" -- {reason}"
    )
    record = pending_approval_registry.create_pending_approval(
        agent_id=requesting_agent_id,
        trigger="direct",
        action_id="propose_librarian_company_link",
        description=description,
        payload=payload,
    )
    return {"status": "pending_approval", "approval_id": record["id"]}


def finalize_librarian_company_link(payload: dict) -> dict:
    """Called only once the operator approves a `propose_librarian_
    company_link` Pending Approval (`app/api/pending_approvals_router.py`'s
    `_APPROVAL_HANDLERS["propose_librarian_company_link"]`) -- performs the
    deferred `ensure_customer_hub_note` call, never called for a declined
    record (mirrors `vault_filing_expert.finalize_cross_cutting_update`'s
    own "payload-driven deferred write" shape exactly)."""
    entity_name = payload["entity_name"]
    result = customer_hub_linking.ensure_customer_hub_note(entity_name)
    return {
        "path": result["hub_note_path"],
        "message": f"Approved — created/confirmed Customer folder for \"{entity_name}\".",
    }


def backfill_company_folders() -> dict:
    """The Company Folder Backfill Job (`REQ-SB-72-US-01-T07`, `ADR-049`
    Decision 5) -- for every real Thread, calls `T05`'s `detect_mentioned_
    companies_for_thread`; a `"new_unambiguous"` mention auto-creates its
    Customer folder via the existing, unmodified `customer_hub_linking.
    ensure_customer_hub_note` (Tier-1-shaped, no approval); an `"ambiguous"`
    mention NEVER autonomously links or creates anything -- only a real
    Pending Approval (`action_id="propose_librarian_company_link"`),
    mirroring `vault_filing_expert`'s own propose/finalize shape. A
    `"known"` mention needs no action here (already linked by `T06`).

    Returns `{"created_folders": [{"conversation_id", "entity_name",
    "hub_note_path"}, ...], "pending_approvals": [approval_id, ...]}`."""
    created_folders: list[dict] = []
    pending_approvals: list[str] = []

    for concept_path in vault_writer.list_thread_notes():
        thread_directory = concept_path.parent
        frontmatter, _ = vault_writer.read_note(concept_path)
        conversation_id = frontmatter.get("conversation_id", "")
        customer = frontmatter.get("customer") or "Unsorted"

        full_content = _thread_full_content(thread_directory / "messages")
        detection = detect_mentioned_companies_for_thread(full_content, primary_customer=customer)

        for mention in detection["mentions"]:
            entity_name = mention["name"]
            classification = mention["classification"]

            if classification == "new_unambiguous":
                result = customer_hub_linking.ensure_customer_hub_note(entity_name)
                created_folders.append({
                    "conversation_id": conversation_id,
                    "entity_name": entity_name,
                    "hub_note_path": result["hub_note_path"],
                })
            elif classification == "ambiguous":
                reason = (
                    f"\"{entity_name}\" is mentioned in this Thread's content, but its "
                    "match against the live known Customers/Partners list is genuinely "
                    "ambiguous (a possible near-spelling match of an existing entity, or "
                    "low model confidence) -- routed for human confirmation rather than "
                    "guessed."
                )
                proposal = _create_librarian_company_link_proposal(
                    entity_name=entity_name,
                    reason=reason,
                    thread_path=str(concept_path),
                    requesting_agent_id="company-and-partner-building",
                )
                pending_approvals.append(proposal["approval_id"])

    return {"created_folders": created_folders, "pending_approvals": pending_approvals}


def propose_customer_backfill() -> dict:
    """The Customer backfill propose Job (`REQ-SB-74-US-01-T01`, `ADR-055`
    Decisions 1-2) -- for every real Thread still `customer: "Unsorted"`
    (`vault_writer.list_thread_notes()`, filtering on each concept file's
    own current `customer` frontmatter -- this filtering alone gives
    Scenario 9's own idempotency for free: an already-routed Thread's
    `customer` is no longer `"Unsorted"`, so it is never even considered
    again), calls `compass_client.detect_customer_for_thread` grounded in
    the Thread's own full concatenated message content (`_thread_full_
    content`, unchanged) against the real, live `vault_writer.list_
    customer_folders()` names (deliberately NOT `list_known_customers()`,
    per `ADR-055` Decision 3).

    Groups every non-`"Unsorted"` result into ONE batched Pending Approval
    per distinct proposed Customer name -- `trigger="direct"` (never
    `"background"`: one backfill pass can legitimately produce multiple
    distinct per-Customer batches, which `"background"`'s own idempotency
    guard would silently collapse, mirroring `_create_librarian_company_
    link_proposal`'s own established reasoning). A Thread whose detection
    result is `"Unsorted"` is left out of every batch entirely -- no forced
    guess (Scenario 8). No Thread's `customer` frontmatter or `tags` are
    written here -- proposal only, never a silent write (Scenario 1).

    Returns `{"proposed_batches": [{"customer", "is_new_customer",
    "thread_paths", "approval_id"}, ...], "matched_existing_customer_
    names": [str, ...], "left_unsorted": [str, ...], "failed": [{"thread_
    path", "error"}, ...]}` -- `matched_existing_customer_names` (every
    real existing Customer folder name that received at least one real
    Thread match this pass) feeds directly into `propose_customer_
    archival_candidates` (`T03`), one evidence pass, never a second,
    independent Compass sweep. `"failed"` is an additive key (real,
    disclosed gap found live at full-corpus scale, `REQ-SB-74-US-01-T06`)
    -- a single transient `compass_client.CompassError` for one Thread is
    recorded and skipped, never crashing the whole pass or silently
    treated as `"Unsorted"`; every OTHER Thread's own real classification
    this same run still lands in a real batch."""
    from app.business import pending_approval_registry  # local import -- see _create_librarian_company_link_proposal's own precedent for why

    existing_folder_names = [
        entry["customer"] for entry in vault_writer.list_customer_folders() if entry.get("customer")
    ]

    batches: dict[str, dict] = {}
    left_unsorted: list[str] = []
    failed: list[dict] = []
    matched_existing_customer_names: set[str] = set()

    for concept_path in vault_writer.list_thread_notes():
        frontmatter, _ = vault_writer.read_note(concept_path)
        if frontmatter.get("customer") != "Unsorted":
            continue  # already routed -- Scenario 9's own idempotency, for free

        thread_directory = concept_path.parent
        full_content = _thread_full_content(thread_directory / "messages")
        try:
            detection = compass_client.detect_customer_for_thread(
                full_content, known_customers=existing_folder_names,
            )
        except compass_client.CompassError as exc:
            # A real, live-found gap (REQ-SB-74-US-01-T06) -- a single
            # transient Compass failure among 100+ real sequential calls
            # must never waste every OTHER Thread's already-good
            # classification in the same pass. detect_customer_for_thread
            # itself deliberately carries no retry loop (ADR-055 Decision
            # 2, mirroring classify_task), so this Job-level honest-failure
            # handling is the orthogonal fix: mirrors backfill_files's own
            # "failed" key / detect_mentioned_companies_for_thread's own
            # non-raising {"error", ...} contract -- record and continue,
            # never silently drop into "Unsorted" (a false negative) or
            # crash the whole Job.
            failed.append({"thread_path": str(concept_path), "error": str(exc)})
            continue
        customer = detection["customer"]

        if customer == "Unsorted":
            left_unsorted.append(str(concept_path))
            continue

        is_new_customer = customer not in existing_folder_names
        if not is_new_customer:
            matched_existing_customer_names.add(customer)

        batch = batches.setdefault(
            customer, {"customer": customer, "is_new_customer": is_new_customer, "thread_paths": []},
        )
        batch["thread_paths"].append(str(concept_path))

    proposed_batches: list[dict] = []
    for customer, batch in batches.items():
        thread_count = len(batch["thread_paths"])
        new_or_existing = "a NEW" if batch["is_new_customer"] else "the existing"
        description = (
            f"The Librarian's Customer backfill pass proposes routing "
            f"{thread_count} Thread(s) to {new_or_existing} Customer "
            f"\"{customer}\"."
        )
        record = pending_approval_registry.create_pending_approval(
            agent_id="company-and-partner-building",
            trigger="direct",
            action_id="propose_customer_backfill_routing",
            description=description,
            payload=batch,
            # ADR-056 (BUGFIX-08-US-01) -- closes BUG-030's own gap: a
            # repeat Job run before this batch's first proposal resolves
            # re-scans the same still-Unsorted Threads without piling up a
            # brand-new duplicate batch for the same customer.
            dedupe_key=f"propose_customer_backfill_routing:{customer}",
        )
        proposed_batches.append({**batch, "approval_id": record["id"]})

    return {
        "proposed_batches": proposed_batches,
        "matched_existing_customer_names": sorted(matched_existing_customer_names),
        "left_unsorted": left_unsorted,
        "failed": failed,
    }


def finalize_customer_backfill_routing(payload: dict) -> dict:
    """Called only once the operator approves a `propose_customer_backfill_
    routing` Pending Approval (`REQ-SB-74-US-01-T02`, `ADR-055` Decision 1)
    -- the deferred-write half of `propose_customer_backfill`'s own
    proposal, mechanical and never a second Compass call (mirrors `finalize_
    background_amendment_proposal`'s own precedent). If `payload["is_new_
    customer"]`, creates the new Customer's folder first via the existing,
    UNCHANGED `customer_hub_linking.ensure_customer_hub_note` -- the exact
    mechanism `backfill_company_folders` already uses for a `new_
    unambiguous` mention. For every Thread named in `payload["thread_
    paths"]`: writes `customer` frontmatter to the approved Customer name,
    and REPLACES any existing `customer/...` tags-list element with the
    real `customer/<slug>` for the approved Customer (leaving every other
    tag, e.g. `kind/...`, untouched) -- a real, deliberate divergence from
    `synthesize_thread`'s own union-append tags logic, which never removes
    a stale element; this handler's own job is specifically to correct it.
    Both writes happen in the SAME pass for each Thread, per Scenario 2's
    own "in the same write" wording. No Thread outside `payload["thread_
    paths"]` is ever touched. `synthesize_customer`/`resync_project_from_
    thread` are NOT called as a side effect -- a routed Thread's Customer
    `## Glimpse` stays exactly as empty as it is today."""
    customer = payload["customer"]
    is_new_customer = payload["is_new_customer"]
    thread_paths = payload["thread_paths"]

    hub_note_path: str | None = None
    if is_new_customer:
        hub_result = customer_hub_linking.ensure_customer_hub_note(customer)
        hub_note_path = hub_result["hub_note_path"]

    corrected_customer_tag = f"customer/{vault_writer.tag_slug(customer)}"
    threads_routed: list[str] = []
    for thread_path_str in thread_paths:
        thread_path = Path(thread_path_str)
        frontmatter, _ = vault_writer.read_note(thread_path)
        existing_tags = list(frontmatter.get("tags") or [])
        replaced = False
        corrected_tags: list[str] = []
        for tag in existing_tags:
            if tag.startswith("customer/"):
                corrected_tags.append(corrected_customer_tag)
                replaced = True
            else:
                corrected_tags.append(tag)
        if not replaced:
            corrected_tags.append(corrected_customer_tag)

        vault_writer.upsert_frontmatter_key(thread_path, "customer", customer)
        vault_writer.upsert_frontmatter_key(thread_path, "tags", corrected_tags)
        threads_routed.append(str(thread_path))

    return {
        "customer": customer,
        "threads_routed": threads_routed,
        "hub_note_path": hub_note_path,
        "message": f"Approved — routed {len(threads_routed)} Thread(s) to \"{customer}\".",
    }


def propose_company_review() -> dict:
    """The Company Review propose Job (`REQ-SB-76-US-01-T04`, `ADR-057`
    Decisions 1-2) -- iterates EVERY real Thread (`vault_writer.list_
    thread_notes()`, NOT filtered to `"Unsorted"` only -- Scenario 9 needs
    an already-routed Thread considered too), calls `compass_client.
    extract_thread_companies_for_review` once per Thread against that
    Thread's full concatenated message content and the live UNION of
    `vault_writer.list_customer_folders()` + `vault_writer.list_known_
    partners()` names -- never hardcoded.

    For each returned company mention: skipped if that Thread's own
    CURRENT `tags` already carries the exact `customer/<slug>`/`partner/
    <slug>` for that company (the per-mention idempotency floor,
    generalizing `propose_customer_backfill`'s own per-Thread "already
    routed" skip to per-mention granularity -- Scenario 9 needs a Thread
    reconsidered for a genuinely NEW company even once it already has a
    primary). Every remaining mention groups into ONE batched Pending
    Approval per distinct company name: `action_id="propose_company_
    review"`, `trigger="direct"`, `payload = {"company", "thread_paths"}`,
    `dedupe_key=f"propose_company_review:{company}"` (`ADR-056`'s own
    target-aware convention, applied from day one).

    A single transient `compass_client.CompassError` for one Thread is
    recorded in a `"failed"` list and skipped, mirroring `propose_
    customer_backfill`'s own `T06`-found honest-failure handling -- never
    crashes the whole pass. This Job performs zero frontmatter/tag writes
    anywhere -- proposal only, never a silent write (Scenario 1).

    Added ALONGSIDE, never replacing, `propose_customer_backfill`/
    `finalize_customer_backfill_routing` -- both stay live, callable,
    byte-for-byte unedited (frozen, `Done`, superseded in PRACTICE only).
    Manually-triggered only -- never wired into `run_company_partner_building_pass()`.

    Returns `{"proposed_batches": [{"company", "thread_paths",
    "approval_id"}, ...], "failed": [{"thread_path", "error"}, ...]}`."""
    from app.business import pending_approval_registry  # local import -- see _create_librarian_company_link_proposal's own precedent for why

    known_companies = [
        entry["customer"] for entry in vault_writer.list_customer_folders() if entry.get("customer")
    ] + vault_writer.list_known_partners()

    batches: dict[str, list[str]] = {}
    failed: list[dict] = []

    for concept_path in vault_writer.list_thread_notes():
        thread_directory = concept_path.parent
        frontmatter, _ = vault_writer.read_note(concept_path)
        existing_tags = set(frontmatter.get("tags") or [])

        full_content = _thread_full_content(thread_directory / "messages")
        try:
            extraction = compass_client.extract_thread_companies_for_review(
                full_content, known_companies=known_companies,
            )
        except compass_client.CompassError as exc:
            failed.append({"thread_path": str(concept_path), "error": str(exc)})
            continue

        for company_mention in extraction["companies"]:
            company = company_mention["name"]
            customer_tag = f"customer/{vault_writer.tag_slug(company)}"
            partner_tag = f"partner/{vault_writer.tag_slug(company)}"
            if customer_tag in existing_tags or partner_tag in existing_tags:
                continue  # per-mention idempotency floor -- already routed for THIS company

            batches.setdefault(company, []).append(str(concept_path))

    proposed_batches: list[dict] = []
    for company, thread_paths in batches.items():
        description = (
            f"The Librarian's Company Review pass proposes classifying "
            f"\"{company}\" -- mentioned by {len(thread_paths)} real "
            f"Thread(s) -- as a Customer, Partner, Affiliate, Merge, or "
            f"Decline."
        )
        record = pending_approval_registry.create_pending_approval(
            agent_id="company-and-partner-building",
            trigger="direct",
            action_id="propose_company_review",
            description=description,
            payload={"company": company, "thread_paths": thread_paths},
            dedupe_key=f"propose_company_review:{company}",
        )
        proposed_batches.append({
            "company": company, "thread_paths": thread_paths, "approval_id": record["id"],
        })

    return {"proposed_batches": proposed_batches, "failed": failed}


def _apply_company_to_threads(thread_paths: list[str], target_name: str, target_kind: str) -> list[str]:
    """The Company Review outcomes' own shared per-Thread apply helper
    (`REQ-SB-76-US-01-T05`, `ADR-057` Decision 8) -- used by ALL FOUR
    Customer/Partner/Affiliate/Merge `finalize_company_review` branches
    (`T06`), so Scenario 9's already-set-vs-unset primary-`customer`/
    `partner` branch logic lives exactly once. `target_kind` in
    `{"customer", "partner"}`.

    For each Thread, freshly reads its CURRENT `customer`/`partner`
    frontmatter AT CALL TIME (never a payload snapshot taken at propose
    time -- a different Company Review batch could resolve first and
    change that state in between): if the Thread's own primary is still
    unset/`"Unsorted"` (no real `customer` AND no real `partner` value
    yet), writes `target_name` to the primary `target_kind` field, REPLACING
    any existing `customer/...`/`partner/...` tags-list element (e.g. a
    stale `customer/unsorted` placeholder tag) with the real `target_kind/
    <slug>` tag -- the "primary write" path (Scenarios 3-6/10), mirroring
    `finalize_customer_backfill_routing`'s own tag-correction shape. If the
    Thread's own primary is ALREADY set to a DIFFERENT real company, the
    primary field is left byte-for-byte untouched; instead an ADDITIVE
    `target_kind/<slug>` tag is added (alongside every pre-existing tag,
    never replacing one) and `## Related` is regenerated via
    `email_classification.build_thread_related_wikilinks` DIRECTLY
    (never `populate_thread_related_links()` itself, which has no
    per-Thread entry point), written under the SAME already-registered
    `librarian_housekeeping.populate_thread_related_links` caller id
    (Scenario 9) -- no new `section_ownership.py` entry.

    `customer:`/`partner:` frontmatter stays single-value by
    construction -- the primary-write branch only ever fires when BOTH
    fields are genuinely unset. No Thread outside `thread_paths` is ever
    touched. Returns the list of Thread paths actually processed."""
    target_tag = f"{target_kind}/{vault_writer.tag_slug(target_name)}"
    processed: list[str] = []

    for thread_path_str in thread_paths:
        thread_path = Path(thread_path_str)
        frontmatter, _ = vault_writer.read_note(thread_path)
        current_customer = frontmatter.get("customer") or ""
        current_partner = frontmatter.get("partner") or ""
        primary_unset = (not current_customer or current_customer == "Unsorted") and not current_partner

        existing_tags = list(frontmatter.get("tags") or [])

        if primary_unset:
            corrected_tags: list[str] = []
            replaced = False
            for tag in existing_tags:
                if tag.startswith("customer/") or tag.startswith("partner/"):
                    corrected_tags.append(target_tag)
                    replaced = True
                else:
                    corrected_tags.append(tag)
            if not replaced:
                corrected_tags.append(target_tag)
            vault_writer.upsert_frontmatter_key(thread_path, "tags", corrected_tags)
            vault_writer.upsert_frontmatter_key(thread_path, target_kind, target_name)
        else:
            if target_tag not in existing_tags:
                existing_tags = existing_tags + [target_tag]
                vault_writer.upsert_frontmatter_key(thread_path, "tags", existing_tags)
            participants = frontmatter.get("participants") or []
            project = frontmatter.get("project")
            related_content = email_classification.build_thread_related_wikilinks(
                current_customer, participants, project, mentioned_companies=[target_name],
            )
            vault_writer.replace_body_section(
                thread_path, "## Related", related_content,
                caller="librarian_housekeeping.populate_thread_related_links",
            )

        processed.append(str(thread_path))

    return processed


def _known_entity_exists(name: str, kind: str) -> bool:
    """Confirms `name` is a real, already-existing Customer or Partner
    entity in the vault -- `customer_concept_file_exists`/`hub_note_exists`
    for `"customer"` (either directory or legacy-flat shape),
    `partner_hub_note_exists` for `"partner"` (legacy-flat-shape only, the
    exact check `ADR-057` Decision 3 names -- a migrated/directory-shaped
    Partner is a disclosed, accepted narrower-check limitation, not fixed
    by this pass, mirroring `ensure_partner_hub_note`'s own unmodified
    reuse elsewhere in this function)."""
    if kind == "customer":
        return vault_writer.customer_concept_file_exists(name) or vault_writer.hub_note_exists(name)
    if kind == "partner":
        return vault_writer.partner_hub_note_exists(name)
    return False


def _existing_duplicate_shape(company: str) -> str | None:
    """Which real prior entity (if any) `company` already has of its own,
    for the Merge outcome's own "does the duplicate name already have
    real content of its own" check (`REQ-SB-76-US-01-T06`, `ADR-057`
    Decision 7) -- `"okf_customer"`/`"legacy_customer"`/`"partner"`, or
    `None` if `company` has no entity of its own yet (the common Merge
    case -- no new entity is ever created for a duplicate name)."""
    if vault_writer.customer_concept_file_exists(company):
        return "okf_customer"
    if vault_writer.hub_note_exists(company):
        return "legacy_customer"
    if vault_writer.partner_hub_note_exists(company):
        return "partner"
    return None


def finalize_company_review(payload: dict) -> dict:
    """Thin public wrapper (`REQ-SB-77-US-01-T02`, Scenario 6a's instant
    trigger) around `_finalize_company_review_outcome` -- runs the real
    outcome write first (unchanged, all 4 branches), then, only once that
    succeeds, relinks every Person note reachable from this company's own
    `payload["thread_paths"]` via `people_extraction.relink_people_for_
    thread_paths` -- ONE relink call, not four, since `thread_paths` is
    identical across every outcome. `_finalize_company_review_outcome`'s
    own raise (the unconfirmable-`parent_name` honest-failure path)
    propagates straight through this wrapper before the relink call ever
    runs, by construction -- a relink failure can never mask, and never
    runs before, the real outcome write."""
    result = _finalize_company_review_outcome(payload)
    people_extraction.relink_people_for_thread_paths(payload["thread_paths"])
    return result


def _finalize_company_review_outcome(payload: dict) -> dict:
    """Called only once the operator approves a `propose_company_review`
    Pending Approval, with the operator's own decision (`outcome`/
    `parent_name`/`parent_kind`) already merged into `payload` by the
    router (`REQ-SB-76-US-01-T07`, `ADR-057` Decisions 3/7/8). Branches on
    `payload["outcome"]` (`"customer" | "partner" | "affiliate" |
    "merge"`) -- ONE registered handler, not four, since exactly one
    Pending Approval record ever exists per company (Scenario 1's own
    "exactly ONE Pending Approval offering five real outcomes"). A
    `parent_name` the server cannot independently confirm is a real,
    existing Customer/Partner of the claimed `parent_kind` raises BEFORE
    any write happens -- the existing call order (`_APPROVAL_HANDLERS
    [...]` runs BEFORE `resolve_pending_approval`) already leaves the
    record `"pending"`, never silently half-applied. Renamed in place
    (`REQ-SB-77-US-01-T02`) from the former public `finalize_company_
    review` -- this function's own body is unchanged, a pure rename."""
    company = payload["company"]
    thread_paths = payload["thread_paths"]
    outcome = payload["outcome"]

    if outcome == "customer":
        hub_result = customer_hub_linking.ensure_customer_hub_note(company)
        applied = _apply_company_to_threads(thread_paths, company, "customer")
        return {
            "outcome": outcome, "company": company,
            "hub_note_path": hub_result["hub_note_path"], "threads_applied": applied,
            "message": f"Approved — classified \"{company}\" as a Customer, applied to {len(applied)} Thread(s).",
        }

    if outcome == "partner":
        hub_result = partner_hub_linking.ensure_partner_hub_note(company)
        applied = _apply_company_to_threads(thread_paths, company, "partner")
        return {
            "outcome": outcome, "company": company,
            "hub_note_path": hub_result["hub_note_path"], "threads_applied": applied,
            "message": f"Approved — classified \"{company}\" as a Partner, applied to {len(applied)} Thread(s).",
        }

    if outcome == "affiliate":
        parent_name = payload["parent_name"]
        parent_kind = payload["parent_kind"]
        if not _known_entity_exists(parent_name, parent_kind):
            raise ValueError(
                f"Company Review Affiliate decision names an unconfirmable "
                f"parent entity: {parent_name!r} is not a real, existing "
                f"{parent_kind} in the vault."
            )
        if parent_kind == "customer":
            hub_result = customer_hub_linking.ensure_customer_hub_note(company)
            entity_path = vault_writer.customer_directory_paths(company)["concept"]
        else:
            hub_result = partner_hub_linking.ensure_partner_hub_note(company)
            entity_path = Path(hub_result["hub_note_path"])
        vault_writer.upsert_frontmatter_key(entity_path, "affiliate_of", parent_name)
        applied = _apply_company_to_threads(thread_paths, company, parent_kind)
        return {
            "outcome": outcome, "company": company,
            "parent_name": parent_name, "parent_kind": parent_kind,
            "hub_note_path": hub_result["hub_note_path"], "threads_applied": applied,
            "message": (
                f"Approved — classified \"{company}\" as an Affiliate of "
                f"\"{parent_name}\", applied to {len(applied)} Thread(s)."
            ),
        }

    if outcome == "merge":
        parent_name = payload["parent_name"]
        parent_kind = payload["parent_kind"]
        if not _known_entity_exists(parent_name, parent_kind):
            raise ValueError(
                f"Company Review Merge decision names an unconfirmable "
                f"parent entity: {parent_name!r} is not a real, existing "
                f"{parent_kind} in the vault."
            )
        applied = _apply_company_to_threads(thread_paths, parent_name, parent_kind)

        retargeted: list[dict] = []
        archived_directory: str | None = None
        duplicate_shape = _existing_duplicate_shape(company)
        if duplicate_shape in ("okf_customer", "legacy_customer"):
            retargeted = partner_hub_linking.retarget_company_references(
                company, "customer", parent_name, parent_kind,
            )
            if duplicate_shape == "okf_customer":
                source_directory = vault_writer.customer_directory_paths(company)["directory"]
                archived_directory = str(vault_writer.move_okf_directory(
                    source_directory, settings.vault_path / "Work/Archive/Customers",
                ))
            else:
                archived_directory = vault_writer.move_note_and_attachments(
                    vault_writer.hub_note_path(company), settings.vault_path / "Work/Archive/Customers",
                )
        elif duplicate_shape == "partner":
            retargeted = partner_hub_linking.retarget_company_references(
                company, "partner", parent_name, parent_kind,
            )
            # Disclosed, not fixed by this pass (ADR-057 Consequences): no
            # Work/Archive/Partners/ root exists yet -- the now-unreferenced
            # duplicate Partner entity is correctly retargeted (every OTHER
            # note's own reference redirected) but left in place, not
            # archived.

        return {
            "outcome": outcome, "company": company,
            "parent_name": parent_name, "parent_kind": parent_kind,
            "threads_applied": applied, "retargeted_notes": retargeted,
            "archived_directory": archived_directory,
            "message": (
                f"Approved — merged \"{company}\" into \"{parent_name}\", "
                f"applied to {len(applied)} Thread(s)."
            ),
        }

    raise ValueError(f"unknown Company Review outcome: {outcome!r}")


def propose_customer_archival_candidates(matched_existing_customer_names: list[str]) -> dict:
    """The archival-candidate propose Job (`REQ-SB-74-US-01-T03`, `ADR-055`
    Decisions 1, 3) -- surfaces every real Customer OKF directory (`vault_
    writer.list_customer_folders()`) whose own name is NOT present in
    `matched_existing_customer_names` (the real, evidence-based set
    `propose_customer_backfill` already computed THIS SAME pass) as its own
    explicit archival-candidate Pending Approval. Evidence-based only --
    the function's own ONLY input signal is the real `matched_existing_
    customer_names` set passed in; it never re-runs any detection call
    itself (one evidence pass, never a second, independently-run Compass
    sweep, `ADR-055` Decision 5), and never classifies a folder by its own
    name alone.

    Returns `{"archival_candidates": [{"customer", "source_directory",
    "approval_id"}, ...]}`."""
    from app.business import pending_approval_registry  # local import -- see _create_librarian_company_link_proposal's own precedent for why

    matched_set = set(matched_existing_customer_names)
    archival_candidates: list[dict] = []

    for entry in vault_writer.list_customer_folders():
        customer = entry.get("customer")
        if not customer or customer in matched_set:
            continue

        source_directory = str(entry["directory"])
        description = (
            f"The Librarian's Customer backfill pass found zero real Thread "
            f"matches for the existing Customer folder \"{customer}\" this "
            f"pass -- surfaced as an archival candidate, never classified "
            f"from its name alone."
        )
        record = pending_approval_registry.create_pending_approval(
            agent_id="company-and-partner-building",
            trigger="direct",
            action_id="propose_customer_archival_candidate",
            description=description,
            payload={"customer": customer, "source_directory": source_directory},
            # ADR-056 (BUGFIX-08-US-01) -- closes BUG-030's own gap for a
            # repeat Job run re-proposing the same archival candidate.
            dedupe_key=f"propose_customer_archival_candidate:{customer}",
        )
        archival_candidates.append({
            "customer": customer,
            "source_directory": source_directory,
            "approval_id": record["id"],
        })

    return {"archival_candidates": archival_candidates}


def finalize_customer_archival(payload: dict) -> dict:
    """Called only once the operator approves a `propose_customer_
    archival_candidate` Pending Approval (`REQ-SB-74-US-01-T04`, `ADR-055`
    Decision 4) -- the deferred-write half of `propose_customer_archival_
    candidates`'s own proposal: moves the approved Customer folder to
    `Work/Archive/Customers/` via the new, generic `vault_writer.move_okf_
    directory`, content byte-for-byte unchanged by construction (a
    directory rename, never a per-file copy). Archive, never delete."""
    customer = payload["customer"]
    source_directory = Path(payload["source_directory"])
    target_parent_directory = settings.vault_path / "Work/Archive/Customers"
    new_directory = vault_writer.move_okf_directory(source_directory, target_parent_directory)
    return {
        "customer": customer,
        "new_directory": str(new_directory),
        "message": f"Approved — archived \"{customer}\" to {new_directory}.",
    }


def ensure_librarian_agents_and_section() -> dict:
    """Idempotent startup bootstrap for the "Librarian" Section + its two
    real, independently-schedulable Agent identities, `threads-cleaning`
    and `company-and-partner-building` (`REQ-SB-79-US-01`, `ADR-058`
    Decision 1) -- replaces the former single `librarian-housekeeping`
    identity's own bootstrap (`REQ-SB-72-US-01-T08`, `ADR-049` Decisions
    6/7). Existence-checked FIRST, per agent, via `agent_registry.
    get_agent`, so a repeat call (e.g. every app restart, `--reload`
    included) is a real no-op for each already-existing agent, never
    creating a second, disambiguated agent (`agent_registry.create_agent`
    is NOT idempotent by itself, so this existence check is what makes the
    bootstrap AS A WHOLE idempotent). `section_registry.create_section` is
    separately already idempotent-collapse-on-collision, so it is always
    safe to call again even though the agent-existence check alone would
    already prevent a repeat run from reaching it in practice. Retiring
    the old `librarian-housekeeping` identity is NOT this function's own
    job -- that is `T05`'s own bootstrap-wiring scope."""
    section = section_registry.create_section("Librarian")
    results: dict[str, dict] = {}
    for agent_id, name, settings_entries in [
        (
            "threads-cleaning",
            "Threads Cleaning",
            [
                {"key": "Schedule", "value": "Every 6 hours (default, operator-adjustable)"},
                {"key": "Vault target", "value": "Work/Threads/"},
                {"key": "Job chain", "value": "Rename -> Thread<->Message linking -> Files/OKF backfill -> ## Related"},
                {"key": "Purpose", "value": "Ongoing Thread hygiene over the real Thread corpus: renames Thread files to human-readable names, keeps Thread<->Message links current, backfills missing Files/OKF companions, and regenerates ## Related with real Person/Company wikilinks -- the fixed rename-first ordering guarantee is preserved."},
            ],
        ),
        (
            "company-and-partner-building",
            "Company and Partner Building",
            [
                {"key": "Schedule", "value": "Every 6 hours (default, operator-adjustable)"},
                {"key": "Vault target", "value": "Work/Customers/, Work/Partners/, Work/People/"},
                {"key": "Job chain", "value": "Company-folder backfill -> People retrofit (scheduled); Customer backfill, archival candidates, Company Review (manually triggered)"},
                {"key": "Purpose", "value": "Builds and maintains Customer/Partner/Affiliate entities from real Thread evidence -- creates a Customer folder for a newly-mentioned company on schedule, retrofits Person notes from captured Email senders, and offers manually-triggered Customer backfill/archival-candidate/Company Review passes; ambiguous findings route through a Pending Approval instead of being guessed."},
            ],
        ),
    ]:
        existing_agent = agent_registry.get_agent(agent_id)
        if existing_agent is not None:
            results[agent_id] = {"id": agent_id, **existing_agent}
            continue
        created_agent = agent_registry.create_agent(name, type="worker", settings=settings_entries)
        section_registry.set_agent_section(created_agent["id"], section["id"])
        results[agent_id] = created_agent
    return results


def run_threads_cleaning_pass() -> dict:
    """Threads Cleaning's own orchestrating capability (`REQ-SB-79-US-01`,
    `ADR-058` Decision 3) -- renamed from `run_housekeeping_pass`, now
    chaining ONLY the 4 Threads Cleaning jobs, on Threads Cleaning's own
    independent schedule; `backfill_company_folders` moves to its own
    sibling below. Runs the Rename Job FIRST (so the other Jobs operate on
    each Thread's own final, current directory, never a stale pre-rename
    path), then `link_thread_messages()` SECOND (`REQ-SB-73-US-01-T03`,
    `ADR-054` Decision 4), then the remaining Jobs in this same fixed
    order for determinism -- behaviourally identical to `run_housekeeping_
    pass`'s own first 4 entries (Scenario 2/7). Returns a combined result
    dict keyed by Job name, never swallowing any individual Job's own
    return shape."""
    return {
        "rename_threads": rename_threads(),
        "link_thread_messages": link_thread_messages(),
        "backfill_files": backfill_files(),
        "populate_thread_related_links": populate_thread_related_links(),
    }


def run_company_partner_building_pass() -> dict:
    """Company and Partner Building's own new, independently-scheduled
    orchestrating capability (`REQ-SB-79-US-01`, `ADR-058` Decision 3) --
    wraps `backfill_company_folders()` (the ONE Job of this pipeline
    previously on `run_housekeeping_pass`'s own shared schedule, Scenario
    3) plus `people_extraction.retrofit_people_from_emails()` (`REQ-SB-77-
    US-01` Scenario 6b's own scheduled, self-healing catch-all -- already-
    existing, already-`Done`, zero new mechanism, pure wiring).
    `propose_customer_backfill`/`propose_customer_archival_candidates`/
    `propose_company_review` stay individually, manually triggered via
    their own already-existing `/poc/*` endpoints -- never folded into
    this scheduled wrapper (`ADR-055`/`ADR-057`'s own explicit
    "manually-triggered only" precedent, untouched)."""
    return {
        "backfill_company_folders": backfill_company_folders(),
        "retrofit_people_from_emails": people_extraction.retrofit_people_from_emails(),
    }
