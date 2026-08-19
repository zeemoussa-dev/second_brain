"""Orchestrates the email-classification POC: fetch mail (meeting invites
already excluded at the Outlook layer), classify each by customer AND kind
via Compass, save any attachments, link it to other notes in the same
Outlook thread, file the result into the vault.

Per Documentation/References/beyond-the-second-brain-methodology.md
("folders are the enemy of thinking" — a note's customer relevance is
multidimensional, not a single fixed home), only `kind` is a folder level
(Work/<Kind>/); `customer` is frontmatter + a tag only, never a folder.
Reclassifying which customer a note belongs to is a tag edit, not a file
move — this is also how the earlier Unsorted-→-Affiliate reorg problem
gets solved without ever building a dedicated merge operation.

Both the customer list and the kind list are dynamic — read from the vault
itself (app.data_access.vault_writer.list_known_customers / list_known_kinds),
never hardcoded. Each starts empty and grows as Compass proposes new values;
this is the extensibility point for adding new filters/kinds later without a
code change. Already-processed emails (tracked by Outlook EntryID) are
skipped so a rerun — including a full-inbox pull — never reclassifies the
same email twice.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Literal

from app.business import (
    agent_prompts,
    customer_hub_linking,
    meeting_classification,
    pending_approval_registry,
    people_extraction,
    project_customer_synthesizer,
    todo_classification,
    vault_filing_expert,
    vault_indexing,
    working_mode_registry,
)
from app.data_access import compass_client, outlook_com, upload_storage, vault_writer


# REQ-SB-67-US-01-T02's own hardcoded default-instructions literal --
# thread_match_merge's own new Compass call site must ALWAYS pass a
# non-None prompt_override into compass_client.summarize_content (parent
# task's own Constraint): either an operator-set agent_prompts.get_prompt(
# "thread_match_merge") override, OR this literal as the fallback --
# summarize_content's own generic built-in default instructions do not
# know about the two-part opening-line+Summary split this literal
# explicitly requires.
_THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS = (
    "You are synthesizing the current state of an email Thread for a "
    "personal knowledge base, from the Thread's own prior synthesized "
    "Summary (if any), its full dated Transcript of messages exchanged so "
    "far, and -- when present -- the new message that just arrived. Fold "
    "the prior Summary and the new message together into ONE coherent, "
    "up-to-date picture of the Thread's current state -- never just "
    "append the new message onto the old Summary verbatim. Even when "
    "there is no prior Summary and only one message total, still produce "
    "a real, sensible synthesis grounded in that one message's own "
    "content -- never treat this as an error, insufficient input, or an "
    "empty result. Respond with a single JSON object: {\"summary\": "
    "<string>}, where the string's value is EXACTLY two parts separated "
    "by one blank line: first, a short, one-sentence 'current state at a "
    "glance' summary; then a fuller synthesized abstract of the Thread's "
    "current state. Base the synthesis strictly on the real content "
    "given below -- never invent, generalize, or pad with placeholder "
    "content.\n\n"
)


def _synthesize_thread_summary(
    existing_summary: str,
    transcript: str,
    new_message_body: str | None,
    prompt_override: str,
) -> dict:
    """The ONE new real Compass call this story adds (REQ-SB-67-US-01-T02,
    architecture.md's "Real Thread Summary Synthesis..." subsection) --
    grounded ROLLING/INCREMENTALLY, never via full-history reconstruction:
    `## Transcript` (append_body_section_line) only ever accumulates a
    terse one-line `date -- sender: subject` entry per message, never a
    message's own body text, so `existing_summary` (the Thread's own
    prior real synthesis -- the accumulated memory of everything before
    now; "" on a brand-new Thread's first message) IS the richest
    available grounding for everything that happened before this call.
    `new_message_body` is the new message's own real body text as the
    explicit delta on live capture (thread_match_merge); `None` on
    backfill (T03) -- a pure resynthesis of what's already persisted,
    with no new delta to fold in.

    Reused IDENTICALLY by thread_match_merge (live capture) and T03's own
    backfill -- one shared mechanism, not two divergent ones. Composes
    compass_client.summarize_content VERBATIM (no new Compass call shape)
    and splits its ONE returned "summary" string on the first blank line
    into {"opening_line": str, "summary": str} -- this split lives here,
    not inside compass_client.py, so summarize_content's own shared
    parsing (and every other real caller of it) is untouched.

    Honest, non-fabricating failure posture mirroring summarize_
    attachment's own "summary_error" pattern exactly: compass_client.
    CompassError is caught locally; on failure this returns
    {"summary_error": str} instead of {"opening_line": ..., "summary":
    ...} -- never raises, so the caller can leave the Thread's existing
    Summary/opening line completely untouched rather than writing a
    fabricated or partial result."""
    content_sections = [
        "Prior Summary (the Thread's own accumulated synthesis before "
        "now -- empty on a brand-new Thread's first message):\n"
        + (existing_summary or "(none yet -- this is the first message "
                                "in this Thread.)"),
        "Full Transcript so far (one dated line per message; message "
        "bodies are NOT included here -- they only ever live in the "
        "Prior Summary above and, when present, the new message "
        "below):\n" + (transcript or "(empty)"),
    ]
    if new_message_body is not None:
        content_sections.append(
            "New message just received -- the delta to fold in:\n"
            + new_message_body
        )
    content = "\n\n".join(content_sections)

    try:
        response = compass_client.summarize_content(
            content,
            "Thread summary synthesis",
            prompt_override=prompt_override,
        )
    except compass_client.CompassError as exc:
        return {"summary_error": f"Thread summary synthesis failed: {exc}"}

    return _split_thread_synthesis_response(response["summary"])


def _split_thread_synthesis_response(raw_summary: str) -> dict:
    """Splits `_synthesize_thread_summary`'s own ONE returned "summary"
    string on the first blank line into {"opening_line": str, "summary":
    str}. Graceful single-string fallback -- never an error -- when the
    model's response contains no blank line at all: the whole string
    becomes `summary`, and its own first line becomes `opening_line`."""
    blank_line_match = re.search(r"\n[ \t]*\n", raw_summary)
    if blank_line_match is not None:
        opening_line = raw_summary[: blank_line_match.start()].strip()
        summary = raw_summary[blank_line_match.end():].strip()
    else:
        opening_line = raw_summary.strip().split("\n", 1)[0].strip()
        summary = raw_summary.strip()
    return {"opening_line": opening_line, "summary": summary}


def build_thread_related_wikilinks(
    customer: str,
    participants: list[str],
    project: str | None,
    mentioned_companies: list[str] | None = None,
) -> str:
    """Assembles a Thread's `## Related` body section content (`ADR-046`
    Decision 9, `REQ-SB-69-US-01-T08`; PROMOTED from `_build_thread_
    related_wikilinks` to a public, cross-module function and extended
    with `mentioned_companies`, `REQ-SB-72-US-01-T06`, `ADR-049` Decision
    4 -- it now has a real caller outside this module, `librarian_
    housekeeping.populate_thread_related_links`) -- a Markdown bullet list
    of real, honest `[[wikilink]]`s, never a fabricated/placeholder one for
    an unresolved relationship (Scenario 11): a Customer hub link when
    `customer` is real (not "Unsorted"/blank), one Person link for each of
    `participants` that has a REAL, already-existing Person note (a
    participant with none is honestly omitted, never guessed), a Project
    link once `project` is populated (only true after route_to_project's
    own approval resolves, ADR-042 point 7 -- absent on every newly
    created/not-yet-routed Thread), and one Company link per name in
    `mentioned_companies` (default `None` -- every pre-existing caller's
    own behavior for the first three link kinds is completely unaffected).
    Every stem is resolved via the SAME conventions this codebase's own
    existing primitives already use -- `vault_writer.hub_note_path`
    (customer_hub_linking.link_note_to_customer_hub's own stem source,
    reused identically for each mentioned company's own hub note),
    `people_extraction.find_existing_person_note` (read-only, never
    creates), and `vault_writer.project_directory_paths` (route_to_
    project/finalize_thread_project_routing's own project-directory
    convention) -- never a second, divergent resolution scheme. Returns ""
    (an empty but present section, once passed through replace_body_
    section) when none of the four are currently resolvable -- an honest
    absence."""
    related_lines: list[str] = []
    if customer and customer != "Unsorted":
        customer_stem = vault_writer.hub_note_path(customer).stem
        related_lines.append(f"- [[{customer_stem}]]")
    for participant_email in participants:
        person = people_extraction.find_existing_person_note(participant_email)
        if person is not None:
            person_stem = Path(person["note_path"]).stem
            related_lines.append(f"- [[{person_stem}]]")
    if project:
        project_stem = vault_writer.project_directory_paths(customer, project)["concept"].stem
        related_lines.append(f"- [[{project_stem}]]")
    for company_name in mentioned_companies or []:
        company_stem = vault_writer.hub_note_path(company_name).stem
        related_lines.append(f"- [[{company_stem}]]")
    return "\n".join(related_lines)


def thread_match_merge(
    email: dict, classification: dict, attachment_entries: list[str] | None = None
) -> dict:
    """The `Thread-Match/Merge` Job (REQ-SB-55-US-01-T03, ADR-043 point 3)
    -- a thin, LangGraph-ignorant plain function, ordinary Python data
    in/out. On the FIRST message of a conversation_id, creates the Thread
    note (vault_writer.create_thread_note_baseline) and writes its
    `customer` frontmatter key once (upsert_frontmatter_key) -- never
    contradicted by a later message's own classification, per this task's
    own Constraint (mid-conversation customer reclassification is
    explicitly out of scope). On EVERY call (create AND update): unions
    this message's own build_tags(customer, kind)-derived tags onto the
    Thread's current tags (read-union-write via upsert_frontmatter_key,
    never pruning a previously-present tag); accumulates the sender into
    `participants` (never removing an existing one); overwrites
    `last_message_at` unconditionally to this message's own received
    timestamp, and writes an additive `last_message_at_display`
    human-readable sibling alongside it (ADR-046 Decision 10,
    REQ-SB-69-US-01-T07, vault_writer.format_human_readable_datetime --
    `last_message_at` itself stays byte-for-byte unchanged, still
    parseable by meeting_classification.py's own
    `_date_proximity_gap_days`); grows `## Transcript` by one
    human-readably-dated entry (append_body_section_line); folds any
    attachment_entries into `## Attachments` (left completely untouched
    when None/empty -- never
    created empty); and, via ONE new real Compass call
    (REQ-SB-67-US-01-T02, `_synthesize_thread_summary`), regenerates BOTH
    the body's opening "current state at a glance" line
    (vault_writer.replace_body_opening_line, T01's new primitive) AND `##
    Summary` (replace_body_section, REQ-SB-54's "regenerate, don't patch"
    invariant) from scratch -- a real whole-region replace for each, never
    a patch, so no residue of a prior message's own opening line/summary
    text survives. Grounded ROLLING/INCREMENTALLY: the Thread's own prior
    `## Summary` (read BEFORE this call overwrites it) + its full current
    `## Transcript` (read AFTER this message's own new dated entry has
    already been appended) + this message's own real body as the delta --
    never a full-history reconstruction (see `_synthesize_thread_summary`'s
    own docstring). On a `compass_client.CompassError`, neither the
    opening line nor `## Summary` is written (the Thread's existing
    content is left completely untouched) and the returned dict gains a
    `"summary_error"` key -- this function itself never raises.

    Only customer_hub_linking.ensure_customer_hub_note(customer) is
    called (never ensure_hub_note_and_link's inline-body-wikilink half --
    that convention is superseded by the OKF concept file's own
    `sources:` field, REQ-SB-57, out of this story's scope); no inline
    `**Customer:** [[Hub]]` wikilink is ever written into the Thread's
    own body. Instead, near the end of every call (after every other
    frontmatter/body write above, against the FINAL, post-rename path),
    `## Related` is fully regenerated from scratch via
    `build_thread_related_wikilinks`/`replace_body_section` (ADR-046
    Decision 9, REQ-SB-69-US-01-T08 -- this is `thread_match_merge`'s own
    STILL-LIVE call, unaffected by `REQ-SB-72-US-01-T06`'s ownership
    transfer, which narrows only `synthesize_thread`'s own allow-list) --
    a real, honest `[[wikilink]]` to
    the matched Customer hub, each participant with a REAL Person note,
    and the routed Project once `project` is populated; never a
    fabricated/placeholder link for an unresolved relationship.

    Returns {"thread_path": str, "created": bool, "conversation_id": str,
    "customer": str, "summary_error": str (present only when the one new
    Compass call above failed)} -- `created` is the signal T07's pipeline
    wiring uses to decide whether Route-to-Project fires (Scenario
    4/AC-04's own mechanism)."""
    conversation_id = email["conversation_id"]
    customer = classification["customer"]
    kind = classification["kind"]
    sender = email["sender_email"] or email["sender_name"]
    message_tags = vault_writer.build_tags(customer, kind)

    # resolve_thread_note_path() (REQ-SB-69-US-01-T06, ADR-046 Decision 7)
    # replaces thread_note_exists()/thread_note_path()'s own retired
    # "deterministic from conversation_id alone" contract -- a Thread's
    # filename can no longer be derived from conversation_id alone once it
    # also depends on thread_name/last_message_at, so create-vs-update is
    # now a real frontmatter-scan lookup, not a pure-function existence
    # check.
    existing_path = vault_writer.resolve_thread_note_path(conversation_id)
    created = existing_path is None
    if created:
        # thread_name is captured ONCE here, from this (the FIRST) message's
        # own subject, and never recomputed on a later message (ADR-046
        # Decision 6) -- a Thread's own descriptive name stays stable across
        # its life even though a later message's own subject may differ
        # ("Re: X").
        thread_name = email["subject"]
        path = vault_writer.thread_note_path_for(
            thread_name, email["received"][:10], conversation_id
        )
        vault_writer.create_thread_note_baseline(
            conversation_id, thread_name, email["received"][:10], tags=message_tags
        )
        # customer is written ONCE, on the first message only -- a later
        # message's own classification never contradicts it (this task's
        # own Constraint; no Scenario in this story tests mid-conversation
        # customer reclassification).
        vault_writer.upsert_frontmatter_key(path, "customer", customer)
    else:
        # Every existing read/write below continues to compose against this
        # real, CURRENT path, unchanged from today's shape -- the rename
        # check (if any) happens only AFTER every one of them has completed,
        # at the very end of this function (ADR-046 Decision 7 / this task's
        # own "rename never races an in-flight write" ordering).
        path = existing_path

    frontmatter, _ = vault_writer.read_note(path)
    if not created:
        thread_name = frontmatter.get("thread_name")
        if not thread_name:
            # BUG-021 (2026-08-17, found live): a Thread created BEFORE
            # ADR-046/T06 shipped never had a thread_name frontmatter key
            # at all (create_thread_note_baseline only gained that param
            # tonight) -- frontmatter.get returning None here used to flow
            # straight into thread_note_path_for below, producing a real,
            # literal "None-<date>-<hash>.md" filename. Backfill it now,
            # once, using this message's own subject (the same top-up-
            # only-if-missing convention this task's own baseline-key
            # helpers already use) so every later update reuses the real
            # persisted value instead of re-deriving it.
            thread_name = email["subject"]
            vault_writer.upsert_frontmatter_key(path, "thread_name", thread_name)
    # Read BEFORE the final replace_body_section call below overwrites it
    # -- the PRIOR real synthesis (empty string on the Thread's own first
    # message, per _synthesize_thread_summary's own rolling/incremental
    # grounding contract).
    existing_summary = vault_writer.read_body_section(path, "## Summary")

    existing_tags = frontmatter.get("tags") or []
    union_tags = existing_tags + [
        tag for tag in message_tags if tag not in existing_tags
    ]
    vault_writer.upsert_frontmatter_key(path, "tags", union_tags)

    existing_participants = frontmatter.get("participants") or []
    if sender and sender not in existing_participants:
        existing_participants = existing_participants + [sender]
    vault_writer.upsert_frontmatter_key(path, "participants", existing_participants)

    # Unconditional on every call (create AND update) -- never
    # insert_frontmatter_key_if_missing, which would silently no-op on
    # the second and every later message.
    vault_writer.upsert_frontmatter_key(path, "last_message_at", email["received"])
    # Additive human-readable sibling (ADR-046 Decision 10, REQ-SB-69-US-01-T07)
    # -- last_message_at itself above stays byte-for-byte unchanged, still
    # %Y-%m-%d-prefix-parseable for meeting_classification.py's own
    # _date_proximity_gap_days.
    vault_writer.upsert_frontmatter_key(
        path,
        "last_message_at_display",
        vault_writer.format_human_readable_datetime(email["received"]),
    )

    vault_writer.append_body_section_line(
        path,
        "## Transcript",
        f"- **{vault_writer.format_human_readable_datetime(email['received'])}** — {sender}: {email['subject']}",
    )

    for entry in attachment_entries or []:
        vault_writer.append_body_section_line(path, "## Attachments", entry)

    # Read AFTER the append above -- the transcript passed to Compass
    # includes this message's own just-arrived dated entry.
    transcript = vault_writer.read_body_section(path, "## Transcript")
    prompt_override = (
        agent_prompts.get_prompt("thread_match_merge")
        or _THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS
    )
    synthesis = _synthesize_thread_summary(
        existing_summary, transcript, email["body"], prompt_override
    )

    if "summary_error" in synthesis:
        # Honest, non-fabricating failure posture (mirrors
        # summarize_attachment's own "summary_error" pattern) -- neither
        # the opening line nor ## Summary is touched on this path.
        summary_error = synthesis["summary_error"]
    else:
        summary_error = None
        vault_writer.replace_body_opening_line(path, synthesis["opening_line"])
        vault_writer.replace_body_section(
            path, "## Summary", synthesis["summary"],
            caller="email_classification.thread_match_merge",
        )

    customer_hub_linking.ensure_customer_hub_note(customer)

    # Rename happens LAST, strictly after every other frontmatter/body
    # write for this call above has completed -- never before, never
    # interleaved (ADR-046 Decision 7) -- so a rename can never race an
    # in-flight write to the OLD path. Only ever computed on the update
    # path: a brand-new Thread is already created directly at its own
    # correct path above.
    if not created:
        new_path = vault_writer.thread_note_path_for(
            thread_name, email["received"][:10], conversation_id
        )
        if new_path != path:
            vault_writer.rename_thread_note(path, new_path)
            path = new_path

    # ## Related (ADR-046 Decision 9, REQ-SB-69-US-01-T08) -- a full,
    # deterministic regeneration via replace_body_section on EVERY call,
    # never a patch (never insert_body_line_if_missing, which Context
    # point 6 found would silently conflict with replace_body_opening_
    # line's own full ownership of the same pre-first-header region).
    # Computed against the Thread's own CURRENT frontmatter for this call
    # -- existing_participants (post-union, above) and frontmatter.get(
    # "project") (read at this call's own start, before any of this
    # function's writes -- project itself is never touched by this
    # function, only by finalize_thread_project_routing, so that earlier
    # read stays accurate) -- and against the FINAL, post-rename path, so
    # the write always lands on the right file.
    related_content = build_thread_related_wikilinks(
        customer, existing_participants, frontmatter.get("project")
    )
    vault_writer.replace_body_section(
        path, "## Related", related_content,
        caller="email_classification.thread_match_merge",
    )

    result = {
        "thread_path": str(path),
        "created": created,
        "conversation_id": conversation_id,
        "customer": customer,
    }
    if summary_error is not None:
        result["summary_error"] = summary_error

    return result


# REQ-SB-71-US-02-T05's own new Compass call site must ALWAYS pass a
# non-None prompt_override into compass_client.summarize_content (mirrors
# _THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS's own established
# contract for thread_match_merge) -- summarize_content's own generic
# built-in default instructions do not know about this Job's own FULL
# RECONSTRUCTION grounding (every raw message under messages/, on every
# call, never a rolling delta -- ADR-048 Alternatives Considered 6), a
# deliberately different grounding shape from thread_match_merge's own
# rolling/incremental one.
_THREAD_FULL_RECONSTRUCTION_DEFAULT_INSTRUCTIONS = (
    "You are synthesizing the current state of an email Thread for a "
    "personal knowledge base, from the FULL set of real, verbatim raw "
    "messages exchanged in this conversation so far (given below, in "
    "chronological order). Produce ONE coherent, up-to-date picture of "
    "the Thread's current state, grounded in the complete real content of "
    "every message -- never from just the latest one, and never a mere "
    "concatenation of per-message summaries. Respond with a single JSON "
    "object: {\"summary\": <string>}. Base the synthesis strictly on the "
    "real content given below -- never invent, generalize, or pad with "
    "placeholder content.\n\n"
)


def synthesize_thread(conversation_id: str) -> dict:
    """Stage 2 (`REQ-SB-71-US-02-T05`, `ADR-048` Decision 3) -- the real
    Compass-backed judgment REPLACING `thread_match_merge`'s prior role
    for all NEW capture going forward. Reads every raw message note
    currently under the Thread's own CURRENT `messages/` directory --
    derived from the already-resolved `existing_path`'s own parent on the
    update branch, or the deterministic `thread_directory_paths(
    conversation_id)["messages"]` path on the genuinely-new-Thread branch
    (retargeted `REQ-SB-72-US-01-T02`, `ADR-049` Decision 1, so an
    already-renamed Thread's own messages are found at their real, current
    location, never a stale pre-rename one) -- sorted by filename, which
    sorts by `received[:10]` first -- chronological order for same-day ties
    broken by hash, an accepted, disclosed limitation mirroring this
    codebase's own existing filename-based ordering conventions elsewhere.
    Returns an honest no-op (`{"conversation_id": ..., "synthesized": False,
    "reason": "no_raw_messages"}`) when no raw message note exists yet for
    this `conversation_id` -- never fabricates a synthesis from nothing.

    Classifies exactly ONCE, against the FIRST raw message's own
    reconstructed body (`classify_captured_email`) -- preserves the
    existing "customer decided once, on the first message, never
    contradicted later" Constraint. Determines create-vs-update via
    `vault_writer.resolve_thread_note_path` (the SAME primitive
    `thread_match_merge` already used, now backed by `T02`'s
    deterministic retargeting). Regenerates `## Summary` from the FULL
    concatenated content of every raw message currently under
    `messages/` (never a rolling/incremental delta -- `ADR-048`
    Alternatives Considered 6) via ONE real Compass call, written via the
    allow-list-checked `replace_body_section(..., caller="email_
    classification.synthesize_thread")`. `## Related` is NO LONGER written
    here (`REQ-SB-72-US-01-T06`, `ADR-049` Decision 4) -- ownership
    transferred wholesale to the Librarian's own `librarian_housekeeping.
    populate_thread_related_links` Job, the SOLE real caller of `build_
    thread_related_wikilinks` for a Thread going forward; this function's
    own `section_ownership.py` allow-list entry was narrowed to `{"##
    Summary"}` alone in the SAME change that registered that new caller,
    never a window where both could write it. Never targets `## Personal
    Notes`/`## Actions`/`## Related` -- writes exactly `## Summary`,
    nothing else in the body. Preserves `route_to_project`'s existing
    Pending-Approval trigger shape, now triggered from this function's own
    end instead of `thread_match_merge`'s.

    Content-preservation sidecar (`BUGFIX-05-US-01`, `ADR-053`): before
    composing `full_content`, checks for a `pre_migration_summary.md`
    sidecar next to this Thread's own concept file (written by
    `vault_writer.migrate_flat_thread_to_directory` for a freshly-migrated
    legacy flat Thread). If present, its text is prepended to
    `full_content` as an explicitly-labeled prior-history block, fed into
    this SAME existing Compass call -- never a second call. On a
    successful synthesis only, the sidecar is renamed in place to
    `pre_migration_summary.consumed.md` (archive-not-delete, fed exactly
    once); on a failed synthesis it is left completely untouched.

    Returns `{"conversation_id", "synthesized": True, "thread_path",
    "created", "customer", "kind", "message_count", "summary_error"
    (present only when the Compass synthesis call failed -- the Thread's
    existing `## Summary` is left untouched on that path)}`."""
    # Create-vs-update decision happens FIRST (REQ-SB-72-US-01-T02, ADR-049
    # Decision 1) -- the messages/ directory read below is reordered to
    # derive from THIS already-resolved existing_path's own parent on the
    # update branch (never directly composing thread_directory_paths(
    # conversation_id)["messages"], which silently resolves to the WRONG,
    # stale, since-renamed path once a Thread's own directory has been
    # renamed, T03's own Rename Job) -- only the genuinely-new-Thread
    # (created) branch falls back to the deterministic thread_directory_
    # paths(...)["messages"] path, the directory create_thread_note_
    # baseline is about to create it at.
    existing_path = vault_writer.resolve_thread_note_path(conversation_id)
    created = existing_path is None
    messages_dir = (
        vault_writer.thread_directory_paths(conversation_id)["messages"] if created
        else existing_path.parent / "messages"
    )
    message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []
    if not message_paths:
        return {
            "conversation_id": conversation_id,
            "synthesized": False,
            "reason": "no_raw_messages",
        }

    messages: list[dict] = []
    for message_path in message_paths:
        message_frontmatter, message_body = vault_writer.read_note(message_path)
        messages.append({
            "message_id": message_frontmatter.get("message_id", ""),
            "subject": message_frontmatter.get("subject", ""),
            "sender": message_frontmatter.get("sender", ""),
            "sender_email": message_frontmatter.get("sender_email", ""),
            "received": message_frontmatter.get("received", ""),
            "body": message_body.strip(),
        })

    first_message = messages[0]
    latest_message = messages[-1]

    if created:
        path = Path(vault_writer.create_thread_note_baseline(
            conversation_id, thread_name=first_message["subject"]
        ))
    else:
        path = existing_path

    frontmatter, _ = vault_writer.read_note(path)

    known_customers = vault_writer.list_known_customers()
    known_kinds = vault_writer.list_known_kinds()
    # classify_captured_email_with_fallback (BUG-015 follow-up), not the
    # raw classify_captured_email -- mirrors run_email_capture_pipeline's
    # own already-established, disclosed handling for exactly this
    # failure class (a persistent/transient real Compass classification
    # error), found live during this task's own real-endpoint
    # verification: an unhandled CompassError here would otherwise crash
    # this whole Stage 2 call with a 500, leaving the Thread's raw
    # messages captured but never synthesized.
    classification = classify_captured_email_with_fallback(
        {
            "subject": first_message["subject"],
            "sender_email": first_message["sender_email"],
            "sender_name": first_message["sender"],
            "body": first_message["body"],
            "conversation_id": conversation_id,
        },
        known_customers, known_kinds,
    )
    customer = classification["customer"]
    kind = classification["kind"]

    message_tags = vault_writer.build_tags(customer, kind)
    existing_tags = frontmatter.get("tags") or []
    union_tags = existing_tags + [tag for tag in message_tags if tag not in existing_tags]
    vault_writer.upsert_frontmatter_key(path, "tags", union_tags)
    vault_writer.upsert_frontmatter_key(path, "customer", customer)

    existing_participants = frontmatter.get("participants") or []
    for message in messages:
        sender = message["sender_email"] or message["sender"]
        if sender and sender not in existing_participants:
            existing_participants.append(sender)
    vault_writer.upsert_frontmatter_key(path, "participants", existing_participants)

    vault_writer.upsert_frontmatter_key(path, "last_message_at", latest_message["received"])
    vault_writer.upsert_frontmatter_key(
        path,
        "last_message_at_display",
        vault_writer.format_human_readable_datetime(latest_message["received"]),
    )

    pre_migration_summary_path = path.parent / "pre_migration_summary.md"
    pre_migration_summary_text = (
        pre_migration_summary_path.read_text(encoding="utf-8")
        if pre_migration_summary_path.exists() else ""
    )

    full_content = "\n\n---\n\n".join(
        f"From: {message['sender']} <{message['sender_email']}>\n"
        f"Received: {message['received']}\nSubject: {message['subject']}\n\n"
        f"{message['body']}"
        for message in messages
    )
    if pre_migration_summary_text:
        full_content = (
            "Prior history (pre-migration Summary, preserved verbatim "
            "from before this Thread was migrated to its current "
            "shape):\n" + pre_migration_summary_text
            + "\n\n---\n\n" + full_content
        )
    prompt_override = (
        agent_prompts.get_prompt("synthesize_thread")
        or _THREAD_FULL_RECONSTRUCTION_DEFAULT_INSTRUCTIONS
    )
    summary_error = None
    try:
        synthesis = compass_client.summarize_content(
            full_content, "Thread full-reconstruction synthesis",
            prompt_override=prompt_override,
        )
        vault_writer.replace_body_section(
            path, "## Summary", synthesis["summary"],
            caller="email_classification.synthesize_thread",
        )
        if pre_migration_summary_path.exists():
            pre_migration_summary_path.rename(
                path.parent / "pre_migration_summary.consumed.md"
            )
    except compass_client.CompassError as exc:
        summary_error = f"Thread synthesis failed: {exc}"

    customer_hub_linking.ensure_customer_hub_note(customer)

    # `## Related` is no longer written here (`REQ-SB-72-US-01-T06`,
    # `ADR-049` Decision 4) -- ownership transfers wholesale to the
    # Librarian's own `librarian_housekeeping.populate_thread_related_
    # links` Job, the sole real caller of `build_thread_related_
    # wikilinks` for a Thread going forward. This function now writes
    # exactly `## Summary`, nothing else in the body.

    thread_result = {
        "thread_path": str(path),
        "created": created,
        "conversation_id": conversation_id,
        "customer": customer,
    }
    route_to_project(thread_result, classification, {
        "subject": first_message["subject"],
        "sender_email": first_message["sender_email"],
        "sender_name": first_message["sender"],
        "body": first_message["body"],
    })

    # Files/OKF companions (REQ-SB-71-US-02-T07) -- called only now that
    # this Thread's own real identity/directory is determined, never from
    # Stage 1. Every real attachment Stage 1 durably persisted (see raw_
    # message_capture.py's own docstring) for any raw message under this
    # Thread gets its own files/<slug>/ OKF companion.
    file_companions: list[dict] = []
    for message in messages:
        for attachment_path in vault_writer.staged_attachment_files(
            conversation_id, message["message_id"]
        ):
            file_companions.append(
                write_file_companion(
                    attachment_path, message["message_id"], path.parent
                )
            )

    result = {
        "conversation_id": conversation_id,
        "synthesized": True,
        "thread_path": str(path),
        "created": created,
        "customer": customer,
        "kind": kind,
        "message_count": len(messages),
        "file_companions": file_companions,
    }
    if summary_error is not None:
        result["summary_error"] = summary_error
    return result


def write_file_companion(attachment_path: Path, message_id: str, thread_directory: Path) -> dict:
    """The Files/OKF companion composing Job (`REQ-SB-71-US-02-T07`,
    `ADR-048` Decision 4) -- named to match its own registered
    `section_ownership.py` caller id (`"email_classification.write_file_
    companion"`, `module.function` granularity, `ADR-048` Decision 2).
    Called from `synthesize_thread`'s own end, once a Thread's real
    directory is determined -- never from Stage 1. Reuses `upload_storage.
    save_upload/extract_text_content/delete_upload` + `compass_client.
    summarize_content` VERBATIM -- the identical technique `summarize_
    attachment` already established, no new extraction/summarization
    mechanism. Creates the companion note via `vault_writer.write_file_
    companion` with an empty `## Summary` placeholder, then writes the
    REAL summary separately via the allow-list-checked `replace_body_
    section` -- a real, observable pass through the guard, not merely a
    baseline literal.

    `file_slug` is `<hash8(message_id)>-<filename>` -- a SHORT
    disambiguator (mirrors `meeting_note_filename_stem`'s/`raw_message_
    note_path`'s own hash-suffix convention), not the owning message's
    own already-80-char-truncated slug (`staged_attachment_files`'s own
    directory name): concatenating that already-at-the-limit slug with a
    real filename would itself exceed `_slugify`'s own 80-char cap and
    silently drop the filename entirely, found live during this task's
    own real-endpoint verification (`REQ-SB-71-US-02-T07`) -- a real
    attachment's own PDF name was silently truncated away, and a SECOND
    attachment on the same message would have collided on the identical
    truncated slug, overwriting the first's own companion note. The
    short hash prefix leaves comfortable room for the real filename while
    still guaranteeing two different messages in the same Thread sharing
    one same-named attachment (e.g. a recurring signature image) never
    collide under one Thread's own `files/` namespace.

    Returns `{"filename": str, "saved": bool, "file_path"/"companion_
    path": str (present when saved), "summary_error": str (present when
    extraction/summarization failed -- an honest, non-fabricating result,
    never raises)}`."""
    filename = attachment_path.name
    content = attachment_path.read_bytes()

    upload_id = upload_storage.save_upload(filename, content)
    try:
        extracted_text = upload_storage.extract_text_content(upload_id, filename)
    except ValueError as exc:
        return {"filename": filename, "saved": False, "summary_error": f"Not summarizable: {exc}"}
    finally:
        upload_storage.delete_upload(upload_id, filename)

    try:
        summary = compass_client.summarize_content(
            extracted_text,
            f"Email attachment: {filename}",
            prompt_override=agent_prompts.get_prompt("write_file_companion"),
        )["summary"]
    except compass_client.CompassError as exc:
        return {"filename": filename, "saved": False, "summary_error": f"Summarization failed: {exc}"}

    message_hash8 = hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:8]
    file_slug = f"{message_hash8}-{filename}"
    write_result = vault_writer.write_file_companion(
        subfolder=str(thread_directory),
        note_stem=thread_directory.name,
        file_slug=file_slug,
        original_filename=filename,
        content=content,
        summary="",
    )
    companion_path = Path(write_result["companion_path"])
    vault_writer.replace_body_section(
        companion_path, "## Summary", summary,
        caller="email_classification.write_file_companion",
    )
    return {"filename": filename, "saved": True, **write_result}


def summarize_attachment(attachment: dict, conversation_id: str, received: str) -> dict:
    """The `Summarize-Attachment` branch Job (REQ-SB-55-US-01-T05, ADR-043
    point 3) -- a thin, LangGraph-ignorant plain function, ordinary Python
    data in/out, mirroring thread_match_merge's own shape. Runs for ONE
    real attachment, ahead of/alongside Thread-Match/Merge -- this
    function's own return value (a `dated_entry` string) is what T07's
    pipeline wiring collects and threads into thread_match_merge's own
    `attachment_entries` parameter; this function never calls
    thread_match_merge, replace_body_section, or any other `## Summary`-
    touching primitive itself, keeping an attachment's own content a
    SEPARATE, dated sub-entry rather than lossily compressed into the
    Thread's regenerated top-level summary (parent story's own
    Constraint).

    Saves the attachment under the Thread's own attachments subfolder via
    vault_writer.write_attachments (unchanged, composed directly --
    subfolder="Work/Threads", note_stem=conversation_id, so the saved
    location is Work/Threads/attachments/<slug-of-conversation_id>/<slug-of-received>/,
    reusing that primitive's own existing oversized-attachment
    `"saved": False` outcome rather than a second, divergent size check).
    Text extraction reuses REQ-SB-28-US-01's own upload_storage
    (save_upload/extract_text_content/delete_upload) DIRECTLY against the
    attachment's own real, already-in-memory bytes -- the identical
    temporary-save-then-extract-then-delete technique
    REQ-SB-44-US-01's own app/business/cockpit/attachments.py already
    established for a vault-saved email attachment (MEMORY.md,
    2026-08-14). Summarization reuses compass_client.summarize_content
    DIRECTLY -- the same primitive REQ-SB-28's own `summarize-file` Skill
    composes -- never skill_registry/invoke_skill dispatch, keeping this
    function graph-ignorant and independently callable/testable. No new
    attachment-saving or summarization mechanism is invented anywhere in
    this function (this task's own Constraint).

    Returns {"filename": str, "saved": bool, "relative_link": str
    (present only when saved), "dated_entry": str (present only when a
    real, genuine summary was produced), "summary_error": str (present
    when saved but no usable summary could be produced -- an
    oversized/unsaved attachment, a non-text-bearing type, or a real
    compass_client.CompassError)} -- an honest, non-fabricating result on
    every path; never raises, mirroring classify_recent_emails' own
    per-item try/except+continue posture applied at the attachment
    level."""
    filename = attachment["filename"]
    saved_results = vault_writer.write_attachments(
        subfolder="Work/Threads",
        note_stem=conversation_id,
        message_segment=received,
        attachments=[attachment],
    )
    saved = saved_results[0]

    if not saved["saved"]:
        return {
            "filename": filename,
            "saved": False,
            "summary_error": "Attachment not saved -- exceeds the size cap.",
        }

    result = {
        "filename": filename,
        "saved": True,
        "relative_link": saved["relative_link"],
    }

    upload_id = upload_storage.save_upload(filename, attachment["content"])
    try:
        extracted_text = upload_storage.extract_text_content(upload_id, filename)
    except ValueError as exc:
        result["summary_error"] = f"Not summarizable: {exc}"
        return result
    finally:
        upload_storage.delete_upload(upload_id, filename)

    try:
        summary = compass_client.summarize_content(
            extracted_text,
            f"Email attachment: {filename}",
            prompt_override=agent_prompts.get_prompt("summarize_attachment"),
        )["summary"]
    except compass_client.CompassError as exc:
        result["summary_error"] = f"Summarization failed: {exc}"
        return result

    result["dated_entry"] = f"{received[:10]} — {filename}: {summary}"
    return result


def route_to_project(thread_result: dict, classification: dict, email: dict) -> dict | None:
    """The `Route-to-Project` Job (REQ-SB-55-US-01-T04, ADR-043 point 4/5)
    -- a thin, LangGraph-ignorant plain function, ordinary Python data
    in/out, mirroring thread_match_merge's own shape. Returns None/no-op
    immediately when `thread_result["created"]` is False -- T07's own
    conditional graph edge is the PRIMARY mechanism deciding whether this
    Job runs at all (Scenario 4/AC-04), but this function's own contract
    also defends the same invariant defensively, so a future caller that
    mistakenly invokes it on an update can never create a second,
    spurious routing approval.

    For a brand-new Thread: reads the matched Customer's own
    currently-open (status == "active") Projects via
    vault_writer.list_customer_projects, asks Compass
    (guess_project_for_thread) to pick the best-fitting one or propose a
    new Project name if none genuinely fit, and ALWAYS creates a Pending
    Approval for that guess (trigger="direct", never "background" --
    create_pending_approval's own idempotency guard only dedupes
    "background" triggers, and a single pipeline tick can legitimately
    produce multiple distinct routing proposals across different new
    Threads) -- never auto-commits the Thread's own `project` frontmatter
    key. The actual write happens only once the operator approves, via
    finalize_thread_project_routing below (ADR-043 point 4's flat-JSON
    deferred-write shape, no LangGraph checkpointer).

    Grounds `guess_project_for_thread`'s own prompt in the Thread's own
    just-written, REAL Compass-synthesized `## Summary`
    (vault_writer.read_body_section, REQ-SB-67-US-01-T02) instead of
    recomputing a second, divergent summary of the same message --
    `email` is accepted only to match every other Job's own call shape
    (T07's pipeline wiring calls every Job uniformly); it is otherwise
    unused here now that `_build_thread_summary_content` is retired.
    `guess_project_for_thread`'s own call shape stays completely
    unchanged -- still exactly one Compass call.

    Returns the created pending-approval record (or None on the
    already-routed no-op path)."""
    if not thread_result["created"]:
        return None

    customer = classification["customer"]
    thread_path = thread_result["thread_path"]

    open_projects = [
        project["project"]
        for project in vault_writer.list_customer_projects(customer)
        if project["status"] == "active" and project["project"]
    ]
    thread_summary = vault_writer.read_body_section(Path(thread_path), "## Summary")
    guess = compass_client.guess_project_for_thread(
        thread_summary,
        open_projects,
        prompt_override=agent_prompts.get_prompt("route_to_project"),
    )
    guessed_project = guess["project"]
    is_new_project = guessed_project not in open_projects

    description = (
        f"Route-to-Project guesses the Thread \"{thread_path}\" belongs to "
        f"{'a NEW project' if is_new_project else 'the existing project'} "
        f"\"{guessed_project}\" for customer {customer}."
    )
    return pending_approval_registry.create_pending_approval(
        agent_id="email-capture-pipeline",
        trigger="direct",
        action_id="route_thread_to_project",
        description=description,
        payload={
            "thread_path": thread_path,
            "customer": customer,
            "guessed_project": guessed_project,
            "is_new_project": is_new_project,
            # REQ-SB-69-US-01-T06 / ADR-046 Decision 8 -- lets
            # finalize_thread_project_routing re-resolve this Thread's
            # CURRENT real path at Approve time instead of trusting
            # thread_path, which can go stale if the Thread is renamed
            # between this proposal and its later approval.
            "conversation_id": thread_result["conversation_id"],
        },
        # ADR-056 (BUGFIX-08-US-01) -- closes BUG-030's own gap: a staged
        # Thread reprocessed as "new" on a later capture tick, before its
        # first proposal resolves, no longer creates a second, duplicate
        # proposal for the same conversation_id.
        dedupe_key=f"route_thread_to_project:{thread_result['conversation_id']}",
    )


def finalize_thread_project_routing(payload: dict) -> dict:
    """Called only once the operator approves route_to_project's own
    Pending Approval (app/api/pending_approvals_router.py's
    `_APPROVAL_HANDLERS["route_thread_to_project"]`, ADR-043 point 4) --
    performs the actual deferred write, never called for a declined
    record. Mirrors vault_filing_expert.finalize_new_top_level_area's own
    "payload-driven deferred write" shape exactly (ADR-021 point 5):
    creates the Project directory first when the routing proposed a
    brand-new Project (vault_writer.create_project_directory_baseline),
    then sets the Thread's own `project` frontmatter key unconditionally
    via T01's upsert_frontmatter_key (never
    insert_frontmatter_key_if_missing, which would no-op since `project`
    is absent-by-design on every newly created Thread per ADR-042 point
    7).

    The WRITE target (`thread_path` below) is re-resolved via
    vault_writer.resolve_thread_note_path(payload["conversation_id"])
    rather than trusted from the `thread_path` string captured at
    proposal time (REQ-SB-69-US-01-T06 / ADR-046 Decision 8) -- a Thread
    renamed between proposal and approval must still resolve to its real,
    current file. Falls back to the legacy `payload["thread_path"]`
    string when `conversation_id` is absent (any Pending Approval created
    before this task shipped) or when the resolved lookup genuinely finds
    nothing (a deleted/moved Thread, not expected in ordinary operation)
    -- honest degradation over a hard crash, mirroring this codebase's own
    standing posture.

    Calls project_customer_synthesizer.synthesize_project
    (REQ-SB-57-US-01-T02) immediately after setting the Thread's own
    `project` frontmatter key -- the real, first moment a Thread's own
    evidence attaches to a Project, so it is this function's own real
    trigger call site (purely additive; this function never itself
    performs the Glimpse/log.md write, per the Ownership rule,
    REQ-SB-54 point 7)."""
    customer = payload["customer"]
    project = payload["guessed_project"]

    resolved_path = None
    if "conversation_id" in payload:
        resolved_path = vault_writer.resolve_thread_note_path(payload["conversation_id"])
    thread_path = resolved_path if resolved_path is not None else Path(payload["thread_path"])

    if payload["is_new_project"]:
        vault_writer.create_project_directory_baseline(customer, project)

    vault_writer.upsert_frontmatter_key(thread_path, "project", project)

    project_customer_synthesizer.synthesize_project(customer, project)

    return {
        "path": payload["thread_path"],
        "message": f"Approved — Thread filed under project '{project}'.",
    }


def consult_librarian(thread_result: dict) -> dict:
    """The `Consult-Librarian` branch Job (REQ-SB-63-US-01-T02, ADR-041's
    own "branch to consult an Expert" precedent) -- a thin, LangGraph-
    ignorant plain function, ordinary Python data in/out, mirroring
    detect_recurring_pattern's own additive, non-gating branch shape.
    Wired to fire unconditionally after Thread-Match/Merge for EVERY
    Thread update (a brand-new Thread AND an update to an
    already-existing one alike) -- never gates route_to_project or the
    graph's own terminal step (this task's own Constraint).

    Reads the Thread's own just-regenerated `## Summary` region (via
    the new vault_writer.read_body_section -- never a second Compass
    call; the Librarian's own grounded decision is reached from the
    SAME real content thread_match_merge already wrote) and consults
    the generalized Vault Filing Expert
    (vault_filing_expert.determine_placement_and_file) with
    already_filed_path set to the Thread's own note path -- T01's own
    additive parameter, which skips a second, redundant write and
    instead only runs hub-linking against the already-filed Thread
    note.

    Never crashes the pipeline run for one email (this task's own
    Constraint): any exception raised by the composed call is caught
    and returned as an honest, non-fabricated {"status": "unavailable",
    ...} result -- an honest {"status": "unavailable", ...} result the
    Librarian itself may already return (its own Provider-unavailable
    path) needs no special handling beyond being returned as-is."""
    thread_path = thread_result["thread_path"]
    try:
        summary_content = vault_writer.read_body_section(Path(thread_path), "## Summary")
        return vault_filing_expert.determine_placement_and_file(
            content=summary_content,
            source_description=f"Thread update: {thread_path}",
            requesting_agent_id="email-capture-pipeline",
            already_filed_path=thread_path,
        )
    except Exception as exc:  # noqa: BLE001 -- honest per-item failure funnel (mirrors run_email_capture_pipeline's own broad per-email catch), so one Librarian-consult failure never aborts this email's own pipeline run or crashes the graph
        return {"status": "unavailable", "message": str(exc)}


def detect_recurring_pattern(email: dict, classification: dict) -> dict | None:
    """The `Detect-Recurring-Pattern` branch Job (REQ-SB-55-US-01-T06,
    ADR-043 point 3/5) -- a thin, LangGraph-ignorant plain function,
    ordinary Python data in/out, mirroring route_to_project's own shape.
    Returns None immediately when classification["recurring_candidate"]
    is falsy -- the detection signal itself lives entirely in `T02`
    (compass_client.classify_email's own extended prompt); this function
    only ACTS on that outcome, it never re-implements or duplicates any
    detection logic of its own (this task's own Constraint).

    When recurring_candidate is True: creates exactly one Pending
    Approval (trigger="direct", never "background" -- same reasoning as
    route_to_project/T04, multiple distinct proposals can legitimately
    coexist across one pipeline tick) proposing a NEW standing Pipeline,
    with a payload shaped to be usable as Agent Creation Wizard input
    (app/api/agents_router.py's own CreateAgentBody contract: `name`,
    `type: "worker"`, a `purpose`-style description) -- genuinely derived
    FROM the triggering email's own subject/customer/kind, never a
    generic/empty placeholder (Scenario 5's own locked-AC requirement).
    This function NEVER calls agent_registry.create_agent or any other
    agent-creation code path on any branch -- the proposed Pipeline is
    not built here, on approval, or anywhere else in this codebase; only
    the operator's own separate, later, manual completion of the
    existing Agent Creation Wizard (REQ-SB-37, Done) actually creates it.

    Returns the created pending-approval record, or None when
    recurring_candidate is falsy."""
    if not classification.get("recurring_candidate"):
        return None

    customer = classification["customer"]
    kind = classification["kind"]
    subject = email["subject"]
    sender = email["sender_email"] or email["sender_name"]

    suggested_name = f"{customer} {kind} Recurring Pipeline"
    purpose = (
        f"Proposed after a recurring, structured pattern was detected in an "
        f"email from {customer} ({sender}) -- subject \"{subject}\", "
        f"classified as {kind}. Automates this recurring artifact instead "
        f"of manually re-filing it each time it recurs."
    )
    description = (
        f"Detect-Recurring-Pattern proposes a new standing Pipeline for "
        f"customer {customer}'s recurring \"{subject}\" pattern."
    )
    return pending_approval_registry.create_pending_approval(
        agent_id="email-capture-pipeline",
        trigger="direct",
        action_id="propose_recurring_pipeline",
        description=description,
        payload={
            "name": suggested_name,
            "type": "worker",
            "purpose": purpose,
            "seed_source": {
                "subject": subject,
                "sender": sender,
                "received": email["received"],
            },
        },
    )


def finalize_recurring_pipeline_proposal(payload: dict) -> dict:
    """Called only once the operator approves detect_recurring_pattern's
    own Pending Approval (app/api/pending_approvals_router.py's
    `_APPROVAL_HANDLERS["propose_recurring_pipeline"]`, ADR-043 point 5)
    -- deliberately does almost nothing. Re-reading Scenario 5's own two
    Then-clauses together ("a Pending Approval is created... pre-filled
    into the existing Agent Creation Wizard" AND "the proposed Pipeline
    is NOT built or executed automatically... until the operator
    explicitly approves AND completes the wizard") describes TWO
    separate human steps -- approving this Pending Approval is
    deliberately not the same action as completing the wizard. This
    function NEVER calls agent_registry.create_agent, writes any new
    Agent-tier registry entry, or otherwise instantiates the proposed
    Pipeline on any branch -- payload is accepted only to match every
    other _APPROVAL_HANDLERS entry's own call shape
    (`_APPROVAL_HANDLERS[action_id](record["payload"])`), not because
    this handler acts on it."""
    return {
        "message": "Approved — seed data ready. Open the Agent Creation "
                    "Wizard to complete the new Pipeline.",
    }


# REQ-SB-55-US-01-T08 (ADR-043 point 6): dead code for the
# email-capture-pipeline path -- run_capture_for_agent dispatches
# "email-capture-pipeline" to pipelines.email_capture_pipeline.
# run_email_capture_pipeline instead, whose own Thread-Match/Merge Job
# already IS "the related emails, merged" (a conversation_id-scoped
# Thread note), making record_conversation_note/find_related_note_stems/
# the "## Related Emails" body region and this per-email one-note-per-
# message shape all superseded for that path. Deliberately NOT deleted
# this task (parent story's own Constraint) -- app/api/email_poc_router.py
# still calls this function directly as its own standalone, separate
# manual /poc/classify-emails endpoint, a real remaining caller outside
# this task's own Files to Modify.
def classify_recent_emails(limit: int = 10) -> list[dict]:
    emails = outlook_com.list_recent_mail(limit=limit)
    already_processed = vault_writer.load_processed_email_ids()
    results: list[dict] = []

    for email in emails:
        if email["id"] in already_processed:
            continue

        known_customers = vault_writer.list_known_customers()
        known_kinds = vault_writer.list_known_kinds()
        try:
            classification = compass_client.classify_email(
                subject=email["subject"],
                sender=email["sender_email"] or email["sender_name"],
                body=email["body"],
                known_customers=known_customers,
                known_kinds=known_kinds,
            )
        except compass_client.CompassError as exc:
            results.append({
                "subject": email["subject"],
                "error": str(exc),
            })
            continue

        customer = classification["customer"]
        kind = classification["kind"]
        subfolder = f"Work/{kind}"
        # Suffix with a short slice of the Outlook EntryID: same-subject,
        # same-day emails (a resend, a duplicate share notification) are
        # common enough that date+subject alone collides and silently
        # overwrites — EntryID is unique per item, so this can't.
        filename_stem = f"{email['received'][:10]}-{email['subject']}-{email['id'][-8:]}"

        saved_attachments = vault_writer.write_attachments(
            subfolder=subfolder,
            note_stem=filename_stem,
            message_segment=email["id"],
            attachments=email["attachments"],
        )
        related_note_stems = vault_writer.find_related_note_stems(email["conversation_id"])

        body = email["body"]
        if related_note_stems:
            body += "\n\n## Related Emails\n"
            for stem in related_note_stems:
                body += f"- [[{stem}]]\n"
        if saved_attachments:
            body += "\n\n## Attachments\n"
            for att in saved_attachments:
                if att["saved"]:
                    body += f"- [{att['filename']}]({att['relative_link']})\n"
                else:
                    body += f"- {att['filename']} (not saved — {att['size']} bytes exceeds the size cap)\n"

        note_path = vault_writer.write_note(
            subfolder=subfolder,
            filename_stem=filename_stem,
            frontmatter={
                "type": kind,
                "customer": customer,
                "tags": vault_writer.build_tags(customer, kind),
                "classification_confidence": classification["confidence"],
                "subject": email["subject"],
                "sender": email["sender_name"],
                "sender_email": email["sender_email"],
                "received": email["received"],
                "outlook_entry_id": email["id"],
                "conversation_id": email["conversation_id"],
                # JSON-encoded STRING, not a raw list[dict] -- vault_writer.py's
                # own _format_frontmatter_value/_parse_frontmatter_value cannot
                # round-trip a list-of-dicts literal (a Python dict-repr write
                # silently reads back as []); a JSON string round-trips
                # correctly through the existing string branch. Reuses the
                # exact workaround REQ-SB-43-US-01-T03's cockpit/people.py
                # already established for this same real gap (MEMORY.md,
                # 2026-08-14) -- cockpit/people.py's _coerce_people_list
                # already accepts this shape.
                "recipients": json.dumps(email.get("recipients", [])),
            },
            body=body,
        )
        vault_writer.mark_email_processed(email["id"])
        vault_writer.record_conversation_note(email["conversation_id"], filename_stem)
        customer_hub_linking.ensure_hub_note_and_link(note_path, customer)
        person_result = people_extraction.ensure_person_note_for_captured_email(
            email["sender_name"], email["sender_email"]
        )
        if person_result is not None:
            people_extraction.link_email_to_person(note_path, person_result["note_path"])
        results.append({
            "subject": email["subject"],
            "customer": customer,
            "kind": kind,
            "confidence": classification["confidence"],
            "attachments": len(saved_attachments),
            "related_emails": len(related_note_stems),
            "note_path": note_path,
        })

    return results


def classify_captured_email(
    email: dict, known_customers: list[str], known_kinds: list[str]
) -> dict:
    """The `Classify` Job (REQ-SB-55-US-01-T02, ADR-043 point 1) -- a thin,
    LangGraph-ignorant wrapper around compass_client.classify_email, plain
    Python data in/out, independently callable/testable outside any graph
    context. Exactly one Compass call per invocation -- no second,
    independent classification chain (parent story's own Constraint).
    Propagates CompassError; the caller (T07's pipeline assembly) decides
    how to handle a classification failure for one email, mirroring
    classify_recent_emails' own existing per-email try/except+skip
    pattern."""
    return compass_client.classify_email(
        subject=email["subject"],
        sender=email["sender_email"] or email["sender_name"],
        body=email["body"],
        known_customers=known_customers,
        known_kinds=known_kinds,
        prompt_override=agent_prompts.get_prompt("classify"),
    )


def classify_captured_email_with_fallback(
    email: dict, known_customers: list[str], known_kinds: list[str]
) -> dict:
    """BUG-015 follow-up (2026-08-17, operator-directed): a persistent
    Compass classification failure ("Forecast"-style emails) used to leave
    an email stuck retrying silently forever -- staged, never filed, never
    visible anywhere a human would look. Rather than let CompassError
    propagate (classify_captured_email's own documented contract), this
    wrapper catches it, falls back to the SAME honest "Unsorted rather
    than guessing" convention this module's own classify prompt already
    uses for a low-confidence customer guess (module docstring: customer
    is a tag, not a folder -- reclassifying it later is a tag edit in
    Obsidian, never a file move), and creates a real Pending Approval so
    the failure is visible and actionable instead of silent. The caller
    (the graph's own `classify` node) still gets a normal classification
    dict back either way -- the REST of the pipeline (Thread-Match-Merge,
    Store) runs exactly as it would for a real Compass success, so the
    email's own real content is captured into a real, visible Thread note
    immediately, never lost or left invisible in staging. Since this
    function never re-raises, the per-item loop treats the whole email as
    a normal success (staged item removed, marked processed) -- the
    Pending Approval, not silent infinite retry, is now BUG-015's own
    disclosed catch entry point for these specific known-bad emails."""
    try:
        return classify_captured_email(email, known_customers, known_kinds)
    except compass_client.CompassError as exc:
        _create_classification_failure_pending_approval(email, exc)
        return {
            "customer": "Unsorted",
            "kind": "Emails",
            "confidence": 0.0,
            "recurring_candidate": False,
        }


def _create_classification_failure_pending_approval(email: dict, exc: Exception) -> dict:
    """Mirrors route_to_project's own "propose, human confirms" Pending
    Approval shape (trigger="direct" -- a single tick can legitimately
    raise more than one of these across different failed emails, so the
    "background" trigger's idempotency-dedup guard, scoped to one entry
    per agent+action, must not apply here). Unlike route_to_project this
    is not really a "guess Compass gets to refine" -- there is nothing to
    approve INTO the vault; the real fix is the human editing the
    already-filed Unsorted Thread's own `customer`/`tags` frontmatter
    directly (a tag edit, this module's own established convention, see
    module docstring). Approving this record is purely an acknowledgement
    that clears it from the Pending Approvals list once the human has
    handled it (in Obsidian or otherwise) -- see
    finalize_classification_failure_acknowledgement, below."""
    description = (
        f"Compass couldn't classify \"{email['subject']}\" from "
        f"{email['sender_email'] or email['sender_name']} ({exc}). Filed "
        "under Unsorted so nothing is lost -- edit the Thread note's own "
        "customer/tags directly in Obsidian to move it, then Approve to "
        "clear this alert."
    )
    return pending_approval_registry.create_pending_approval(
        agent_id="email-capture-pipeline",
        trigger="direct",
        action_id="acknowledge_classification_failure",
        description=description,
        payload={
            "conversation_id": email["conversation_id"],
            "subject": email["subject"],
            "sender": email["sender_email"] or email["sender_name"],
            "error": str(exc),
        },
        # ADR-056 (BUGFIX-08-US-01) -- closes BUG-030's own gap for the
        # same email/Thread being reprocessed on a later capture tick.
        dedupe_key=f"acknowledge_classification_failure:{email['conversation_id']}",
    )


def finalize_classification_failure_acknowledgement(payload: dict) -> dict:
    """Called only once the operator approves _create_classification_
    failure_pending_approval's own record (pending_approvals_router.py's
    `_APPROVAL_HANDLERS["acknowledge_classification_failure"]`). No vault
    write happens here -- the real correction (if any) already happened
    directly in Obsidian (see that function's own docstring); this just
    lets the operator clear the alert from Pending Approvals once handled."""
    return {
        "path": payload.get("conversation_id", ""),
        "message": f"Acknowledged — \"{payload['subject']}\" reviewed.",
    }


def run_capture_for_agent(agent_id: str, limit: int = 10) -> list[dict]:
    """The one place both the composite direct/manual dispatch below and a
    Pending-Approvals approval (app/api/pending_approvals_router.py,
    T06) resolve "which function does this agent_id's own background
    capture step call" — so the mapping is never duplicated (ADR-018
    point 4).

    "email-capture" is retired (REQ-SB-55-US-01-T08, ADR-043 point 6) --
    "email-capture-pipeline" dispatches to run_email_capture_pipeline
    (T07's compiled StateGraph), never classify_recent_emails, which stays
    dead code for this path (see classify_recent_emails' own docstring).
    The import is deliberately INSIDE this branch, not at module top
    level -- app/business/pipelines/email_capture_pipeline.py imports
    five plain Job functions FROM this module at its own top level, so a
    module-level import here would complete a real circular import
    (email_classification -> pipelines.email_capture_pipeline ->
    email_classification). By the time this branch actually runs, both
    modules have already finished loading, so the deferred import is
    safe -- mirrors skill_tools.py's own build_knowledge/
    propose_person_note_update deferred-import precedent for the same
    reason.

    REQ-SB-69-US-01-T04 (ADR-046 Decision 3/4): Fetch's own Outlook-
    touching half now lives entirely in email_pull.pull_and_stage_emails
    -- run_email_capture_pipeline itself only reads from email_staging
    now (T03), it no longer pulls. This function's own email branch
    composes BOTH steps in one call (pull_and_stage_emails, THEN
    run_email_capture_pipeline) so every caller of THIS function --
    run_capture_now's own manual/chat dispatch (via run_capture_and_
    record_completion's own default "direct" trigger, below) and a
    Supervised background-capture approval's own Approve dispatch
    (pending_approvals_router.py, unmodified by this task) -- keeps
    seeing email fully captured end-to-end (staged AND processed) when
    this call returns, exactly as before this task (the parent story's
    own "run_capture_now keeps its own observable contract" Constraint).
    The SCHEDULED tick's own composite dispatch (run_capture_and_record_
    completion(trigger="scheduled"), below) deliberately does NOT call
    this function for its email leg -- it calls pull_and_stage_emails
    directly, alone, so Processing is never bundled under the same lock
    hold Pull runs under for that one real trigger path (ADR-046
    Decision 4's own hard Constraint)."""
    if agent_id == "email-capture-pipeline":
        from app.business.pipelines import email_pull
        from app.business.pipelines.email_capture_pipeline import run_email_capture_pipeline

        email_pull.pull_and_stage_emails(limit=limit)
        return run_email_capture_pipeline(limit=limit)
    if agent_id == "meeting-capture":
        return meeting_classification.classify_recent_meetings()
    if agent_id == "todo-capture":
        return todo_classification.classify_recent_todos()
    raise ValueError(f"No background capture step for agent_id={agent_id!r}")


def run_capture_and_record_completion(
    limit: int = 10, trigger: Literal["scheduled", "direct"] = "direct",
) -> list[dict]:
    """Scheduling-layer entry point (ADR-005): runs the scheduled capture
    step for each of the three capture agents below, then records
    completion via vault_writer so the shared last-run record reflects
    every scheduled run, not just manual ones. Also runs Meetings
    capture (REQ-SB-08, ADR-008) on the same tick — no second scheduled
    job, no second concurrency guard; app/scheduling/capture_scheduler.py
    calls this with trigger="scheduled" (below); every other caller
    (skill_tools.run_capture_now's own manual/chat dispatch,
    app/api/agents_router.py's legacy _ACTION_HANDLERS entry, both out of
    this task's own Files to Modify) omits it, keeping the default
    "direct" and this function's own pre-existing behavior byte-for-byte.

    REQ-SB-69-US-01-T04 (ADR-046 Decision 4): `trigger` distinguishes the
    SCHEDULED composite tick (capture_scheduler.py::run_capture_if_idle,
    the one real trigger surface ADR-046's own hard lock-separation
    Constraint binds) from every other, still fully backward-compatible
    caller. When trigger=="scheduled" and email-capture-pipeline is
    Autonomous, ONLY email_pull.pull_and_stage_emails() runs in this
    function's own email leg, under whatever lock the caller (the shared
    Outlook-COM dispatch lock) already holds -- Processing is dispatched
    SEPARATELY, by the caller, AFTER this function returns and that lock
    is released (never bundled here). This is what makes a stalled Pull
    unable to block already-staged mail, and a stalled Process unable to
    block the next Pull, true by construction for this real trigger path.
    Every other trigger value (the default "direct") is UNCHANGED from
    this function's own pre-existing behavior -- run_capture_for_agent's
    own email branch now composes Pull+Process in one call (see that
    function's own docstring), preserving run_capture_now's "fully
    captured end-to-end" contract exactly. Supervised/Manual mode
    handling for the email leg is identical regardless of trigger (this
    parameter only changes what the Autonomous branch actually runs).

    REQ-SB-55-US-01-T08 (ADR-043 point 6): the email step below now
    dispatches, via run_capture_for_agent("email-capture-pipeline", ...),
    to pipelines.email_capture_pipeline.run_email_capture_pipeline — the
    Fetch/Classify/Thread-Match-Merge/Route-to-Project Pipeline, not
    classify_recent_emails. This function's own gating/history/error-
    handling shape below is unchanged; only the underlying email-path
    function (and its agent_id string) changed. This has genuinely
    diverged from app/api/email_poc_router.py's own standalone manual
    /poc/classify-emails endpoint, which still calls classify_recent_
    emails directly and is unaffected by this task (out of this task's
    own Files to Modify).

    REQ-SB-21/ADR-018 point 4: each of the two capture steps below is
    now independently gated by that agent's own working mode.
    Autonomous runs the step exactly as before this story (no change to
    the default-path behaviour or history-entry text for
    email-capture-pipeline). Supervised creates a trigger="background"
    pending-approval record (idempotent per tick) plus a "proposal"
    history entry instead of running the step. Manual skips silently —
    no record, no history entry at all, the literal "stays dormant" PRD
    language for the one trigger context where Manual and Supervised are
    meant to differ (see app/api/agents_router.py, T04, for the
    chat/direct trigger context, where Manual does not gate).

    REQ-SB-11/architecture.md "Agent Activity & Error Observability":
    each Autonomous-mode capture step below is now independently
    wrapped in a try/except -- an exception escaping that step's own
    per-item handling (e.g. outlook_com.OutlookUnavailable) is caught
    here and recorded as a new "run_error"-kind history entry instead
    of propagating uncaught (mirrors ADR-015's own call-site
    honest-failure-funnel pattern, applied to this orchestration
    function). Meeting-capture's Autonomous branch also now writes its
    own "run_event" entry on success -- parity with email-capture-pipeline,
    closing REQ-SB-11's confirmed "meeting-capture runs are silently
    omitted" gap. record_capture_run_completed() is only called when
    neither step's try/except fired this tick -- preserving its
    existing "only reached when nothing raised" semantics
    (REQ-SB-31-US-01's own documented last_capture_run.json signal)
    unchanged.

    Return shape is unchanged: still exactly the email-capture-pipeline
    results list (REQ-SB-08-US-01-T04's own documented constraint) —
    empty when email-capture-pipeline's own mode is non-Autonomous, and
    now also empty on a caught email-capture-pipeline failure — both are
    the same honest "no items filed this tick" signal, new
    user-opted-into/failure-path behaviour, not a default-path
    regression, since Autonomous stays the default per this story's own
    behavior-preservation Constraint.
    """
    email_mode = working_mode_registry.get_agent_working_mode("email-capture-pipeline")
    email_capture_failed = False
    results: list[dict] = []
    if email_mode == "autonomous" and trigger == "scheduled":
        # REQ-SB-69-US-01-T04 (ADR-046 Decision 4) -- the scheduled tick's
        # own email leg stages ONLY, under the shared Outlook-COM lock the
        # caller already holds; Processing is dispatched separately, by
        # the caller, after this function returns and that lock is
        # released (never bundled here). `results` stays empty -- nothing
        # was filed yet, an honest signal, and no real caller of this
        # trigger value consumes this function's own return value anyway
        # (capture_scheduler.py discards it).
        from app.business.pipelines import email_pull

        try:
            pull_summary = email_pull.pull_and_stage_emails(limit=limit)
        except Exception as exc:  # noqa: BLE001 -- same honest-failure-reporting funnel as the composite branch below, scoped to Pull alone for this trigger
            email_capture_failed = True
            vault_writer.append_agent_history_entry(
                "email-capture-pipeline",
                "run_error",
                f"Pull failed — {exc}",
            )
        else:
            vault_writer.append_agent_history_entry(
                "email-capture-pipeline",
                "run_event",
                f"Pull completed — {pull_summary['newly_staged']} new email(s) staged",
            )
    elif email_mode == "autonomous":
        try:
            results = run_capture_for_agent("email-capture-pipeline", limit=limit)
        except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11 Scenario 2), extends ADR-015's existing pattern to this call site
            email_capture_failed = True
            results = []
            vault_writer.append_agent_history_entry(
                "email-capture-pipeline",
                "run_error",
                f"Capture run failed — {exc}",
            )
        else:
            # BUG-FIX 2026-08-17: `results` mixes real successes with
            # per-email failures (run_email_capture_pipeline's own
            # per-item try/except catches a failure -- e.g. a transient
            # Compass timeout/connection error -- and appends
            # {"subject":.., "error":..} into the SAME list rather than
            # letting it escape as an exception, per that function's own
            # documented "never crashes the whole tick's own loop" Job
            # boundary). The unmarked email is safely retried next tick
            # (no data loss), but this history line previously counted
            # every failed item as "filed" too, silently mislabeling a
            # transient Compass outage as success.
            filed = [r for r in results if "error" not in r]
            failed = [r for r in results if "error" in r]
            history_text = f"Capture run completed — {len(filed)} email(s) filed"
            if failed:
                history_text += f", {len(failed)} failed (will retry next run)"
            vault_writer.append_agent_history_entry(
                "email-capture-pipeline",
                "run_event",
                history_text,
            )
    elif email_mode == "supervised":
        approval = pending_approval_registry.create_pending_approval(
            agent_id="email-capture-pipeline",
            trigger="background",
            action_id=None,
            description="Run the scheduled email capture pipeline — checks "
                        "the inbox for new mail and files it into the vault.",
        )
        vault_writer.append_agent_history_entry(
            "email-capture-pipeline",
            "proposal",
            f"Proposed — {approval['description']} Awaiting your approval.",
            pending_approval_id=approval["id"],
        )
        results = []
    else:  # manual — stays dormant this tick, no record, no history entry
        results = []

    meeting_mode = working_mode_registry.get_agent_working_mode("meeting-capture")
    meeting_capture_failed = False
    if meeting_mode == "autonomous":
        try:
            meeting_results = run_capture_for_agent("meeting-capture")
        except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11 Scenario 2), extends ADR-015's existing pattern to this call site
            meeting_capture_failed = True
            vault_writer.append_agent_history_entry(
                "meeting-capture",
                "run_error",
                f"Capture run failed — {exc}",
            )
        else:
            vault_writer.append_agent_history_entry(
                "meeting-capture",
                "run_event",
                f"Capture run completed — {len(meeting_results)} meeting(s) filed",
            )
    elif meeting_mode == "supervised":
        approval = pending_approval_registry.create_pending_approval(
            agent_id="meeting-capture",
            trigger="background",
            action_id=None,
            description="Run the scheduled meeting-capture step — checks the "
                        "calendar for new events and files them into the vault.",
        )
        vault_writer.append_agent_history_entry(
            "meeting-capture",
            "proposal",
            f"Proposed — {approval['description']} Awaiting your approval.",
            pending_approval_id=approval["id"],
        )
    # else: manual — stays dormant this tick, no record, no history entry

    todo_mode = working_mode_registry.get_agent_working_mode("todo-capture")
    todo_capture_failed = False
    if todo_mode == "autonomous":
        try:
            todo_results = run_capture_for_agent("todo-capture")
        except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11), same shape as the email/meeting branches above
            todo_capture_failed = True
            vault_writer.append_agent_history_entry(
                "todo-capture",
                "run_error",
                f"Capture run failed — {exc}",
            )
        else:
            vault_writer.append_agent_history_entry(
                "todo-capture",
                "run_event",
                f"Capture run completed — {len(todo_results)} task(s) filed",
            )
    elif todo_mode == "supervised":
        approval = pending_approval_registry.create_pending_approval(
            agent_id="todo-capture",
            trigger="background",
            action_id=None,
            description="Run the scheduled To-Do capture step — checks "
                        "the Outlook Tasks folder for new/changed tasks "
                        "and files them into the vault.",
        )
        vault_writer.append_agent_history_entry(
            "todo-capture",
            "proposal",
            f"Proposed — {approval['description']} Awaiting your approval.",
            pending_approval_id=approval["id"],
        )
    # else: manual — stays dormant this tick, no record, no history entry

    # Vault indexing (REQ-SB-01-US-01, ADR-024): runs on every tick,
    # unconditionally -- not gated by either capture step's own
    # working mode (ADR-018/ADR-020) NOR by whether a capture step
    # failed above (REQ-SB-11) -- indexing is core plumbing, not an
    # Agents Map agent action, and re-indexing after a partial-failure
    # tick still correctly reflects whatever the other, non-failing
    # step actually wrote. Satisfies Scenario 9 ("no separate,
    # independent schedule was needed for the index specifically")
    # with zero changes to capture_scheduler.py itself, which already
    # treats this whole function as an opaque unit.
    vault_indexing.rebuild_index()

    if not email_capture_failed and not meeting_capture_failed and not todo_capture_failed:
        vault_writer.record_capture_run_completed()
    return results
