"""The Vault Filing Expert's own placement/write mechanism (ADR-021) --
a distinct registry agent, reached exclusively via REQ-SB-20's Hub
routing, never a shared skill (operator-confirmed, "This is an Agent").
determine_placement_and_file is this module's one public entry point.
Grounding is deterministic context injection (the three known-value
lists are pre-fetched in plain Python, never left to the model's own
discretion to tool-call), not a bound-tool reasoning loop -- ADR-021
point 2's own "prefer a real deterministic call over hoping the model
tool-calls correctly" precedent, one layer over ADR-016's
extract_memory reasoning. Tier 1 (existing category, or a new tag/
subfolder within an existing top-level area) writes immediately.
Tier 2 (a genuinely new top-level area) is handled in finalize_new_
top_level_area / the local _create_tier_2_proposal import inside this
same function -- deliberately a LOCAL, not module-level, import of
pending_approval_registry, so this whole module loads and every Tier-1
scenario works correctly even before REQ-SB-21-US-01-T03 ships that
module (ADR-021's own Consequences: "Tier 1... has no such dependency
and can be built and verified independently")."""
import json
from pathlib import Path

from app.business import (
    agent_prompts,
    customer_hub_linking,
    partner_hub_linking,
    vault_filing_methodology,
)
from app.business.agent_orchestration import model_factory
from app.data_access import vault_writer

_UNCERTAINTY_PREFIX = "> ⚠️ **Low-confidence placement.** {note}\n\n"


def _unique_filename_stem(subfolder: str, filename_stem: str) -> str:
    """write_note() overwrites unconditionally on a filename collision
    (confirmed by direct reading of its own implementation) -- a
    model-proposed filename_stem is not guaranteed unique. Applies this
    project's own standing filename-uniqueness Constraint (MEMORY.md):
    append a numeric suffix until the target path is free, mirroring
    the Meeting-note dedup-suffix precedent one layer up (ADR-019's own
    "never trust a single proposed key as unique" lesson, applied here
    to a model-proposed stem instead of an Outlook-provided id)."""
    from app.config import settings

    base = filename_stem
    candidate = base
    suffix = 2
    target_dir = settings.vault_path / subfolder
    while (target_dir / f"{candidate}.md").exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _parse_decision(raw_content: str) -> dict:
    """The real, installed langchain_openai.ChatOpenAI completion
    sometimes wraps a JSON reply in a ```json ... ``` markdown fence
    despite the prompt's own explicit "no markdown code fence"
    instruction -- stripped here defensively before parsing, an ordinary
    implementation-latitude adaptation to the real model's own observed
    behaviour (mirrors REQ-SB-20-US-01-T05's own identical "adapt to the
    real installed API" caveat), not a scope change."""
    text = raw_content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def _placement_frontmatter(decision: dict) -> dict:
    """list_known_customers()/list_known_partners() scan a `customer:`/
    `partner:` FRONTMATTER field, never the tags list (ADR-004, confirmed
    by direct reading of vault_writer.list_known_customers) -- AC-02's own
    "discoverable the same vault-derived way list_known_kinds/
    list_known_customers already work" requirement is only satisfied if
    the written note carries that frontmatter field too, not just the
    corresponding customer/<slug> tag. Additive on top of `tags` alone;
    never both customer and partner set together, mirroring
    referenced_customer/referenced_partner's own mutual-exclusivity."""
    frontmatter = {"tags": decision["tags"]}
    referenced_customer = decision.get("referenced_customer")
    referenced_partner = decision.get("referenced_partner")
    if referenced_customer:
        frontmatter["customer"] = referenced_customer
    elif referenced_partner:
        frontmatter["partner"] = referenced_partner
    return frontmatter


def _link_referenced_entity(note_path: str, decision: dict) -> None:
    """Mechanically ensures the written note carries a real [[wikilink]]
    to whatever customer/partner the model says this content references
    (ADR-021's own Consequences: "reusing customer_hub_linking/
    partner_hub_linking's existing granular primitives"), rather than
    trusting the model's own free-text body to have produced a correctly
    formed/slugged wikilink -- satisfies the standing tags-and-wikilinks
    rule (MEMORY.md) mechanically, idempotent if the model's own body
    text already included an equivalent line. Deliberately NOT gated on
    the entity already being a KNOWN customer/partner -- ensure_customer_
    hub_note/ensure_partner_hub_note already create the hub note baseline
    on first reference (REQ-SB-14/REQ-SB-16's own established "new
    customer/partner" pattern, email_classification.py's own identical,
    unconditional call shape), and Scenario 2's own new-tag-within-an-
    existing-kind case is exactly a customer appearing for the first
    time -- gating on prior existence would silently skip the hub-note/
    wikilink step for precisely that case."""
    referenced_customer = decision.get("referenced_customer")
    referenced_partner = decision.get("referenced_partner")
    if referenced_customer:
        customer_hub_linking.ensure_hub_note_and_link(note_path, referenced_customer)
    elif referenced_partner:
        partner_hub_linking.ensure_partner_hub_note(referenced_partner)
        partner_hub_linking.link_note_to_partner_hub(note_path, referenced_partner)


def determine_placement_and_file(
    content: str, source_description: str, requesting_agent_id: str,
    *, already_filed_path: str | None = None,
) -> dict:
    """already_filed_path (REQ-SB-63-US-01-T01, additive, keyword-only) --
    set by a Job-style caller (e.g. REQ-SB-55's Thread pipeline) whose
    content is already written to a Pipeline-controlled deterministic
    path before the Librarian is even consulted. When set and the
    decision resolves Tier 1, this function NEVER calls
    vault_writer.write_note (writing a second, redundant note for
    already-filed content would be wrong) -- it instead runs
    _link_referenced_entity against that already-filed path, exactly
    the same mechanical hub-linking every other caller already gets.
    All 3 pre-existing callers omit this parameter, so behavior for
    them is byte-for-byte unchanged. The Tier 1/Tier 2 boundary itself
    is computed identically either way -- this parameter only changes
    what happens AFTER a Tier-1 decision, never the decision itself."""
    model = model_factory.resolve_agent_model("vault-filing-expert")
    if model is None:
        return {
            "status": "unavailable",
            "message": "The Vault Filing Expert's selected Provider is not available.",
        }

    known_kinds = vault_writer.list_known_kinds()
    known_customers = vault_writer.list_known_customers()
    known_partners = vault_writer.list_known_partners()

    # The ONE owning identity for this prompt is always "vault-filing-expert"
    # itself -- never requesting_agent_id, which stays Pending-Approval
    # bookkeeping-only, regardless of caller (REQ-SB-20 Hub routing or
    # email_classification.consult_librarian's own internal call alike).
    prompt_override = agent_prompts.get_prompt("vault-filing-expert")

    prompt = vault_filing_methodology.build_placement_prompt(
        content=content,
        source_description=source_description,
        known_kinds=known_kinds,
        known_customers=known_customers,
        known_partners=known_partners,
        prompt_override=prompt_override,
    )
    raw = model.invoke(prompt)
    decision = _parse_decision(raw.content)

    # Never trust the model's own boolean alone -- re-check the Tier
    # boundary against the real, live vault structure (ADR-021 point 2).
    is_new_top_level_area = decision["kind"] not in known_kinds

    if is_new_top_level_area:
        # Cross-cutting detection is deliberately NOT evaluated for Tier 2
        # in this task's own scope (no locked AC exercises that
        # combination -- see the task's own disclosed scope note).
        return _create_tier_2_proposal(
            content=content,
            source_description=source_description,
            requesting_agent_id=requesting_agent_id,
            decision=decision,
        )

    body = decision["body"]
    if decision.get("confidence") == "low":
        body = _UNCERTAINTY_PREFIX.format(note=decision.get("uncertainty_note") or "This placement is a best guess.") + body

    if already_filed_path is not None:
        _link_referenced_entity(already_filed_path, decision)
        result = {
            "status": "linked",
            "path": already_filed_path,
            "kind": decision["kind"],
            "tags": decision["tags"],
            "confidence": decision.get("confidence", "high"),
        }
    else:
        subfolder = f"Work/{decision['kind']}"
        filename_stem = _unique_filename_stem(subfolder, decision["filename_stem"])
        path = vault_writer.write_note(subfolder, filename_stem, _placement_frontmatter(decision), body)
        _link_referenced_entity(path, decision)
        result = {
            "status": "written",
            "path": path,
            "kind": decision["kind"],
            "tags": decision["tags"],
            "confidence": decision.get("confidence", "high"),
        }

    # Independent of whichever Tier-1/linked outcome above -- both a write/
    # link AND a cross-cutting proposal can legitimately happen for the
    # same call (the task's own explicit "not mutually exclusive" Constraint).
    cross_cutting_approval_id = _maybe_create_cross_cutting_proposal(
        decision=decision,
        known_customers=known_customers,
        known_partners=known_partners,
        already_filed_path=result["path"],
        source_description=source_description,
        requesting_agent_id=requesting_agent_id,
    )
    if cross_cutting_approval_id is not None:
        result["cross_cutting_approval_id"] = cross_cutting_approval_id

    return result


def _create_tier_2_proposal(*, content, source_description, requesting_agent_id, decision) -> dict:
    from app.business import pending_approval_registry  # local import -- see T02's own Context/Notes for why

    payload = {
        "content": content,
        "source_description": source_description,
        "kind": decision["kind"],
        "tags": decision["tags"],
        "referenced_customer": decision.get("referenced_customer"),
        "referenced_partner": decision.get("referenced_partner"),
        "filename_stem": decision["filename_stem"],
        "body": decision["body"],
    }
    description = (
        f"Vault Filing Expert proposes a new top-level vault area, "
        f"\"{decision['kind']}\", for: {source_description}"
    )
    record = pending_approval_registry.create_pending_approval(
        agent_id="vault-filing-expert",
        trigger="direct",
        action_id="propose_new_top_level_area",
        description=description,
        payload=payload,
    )
    return {"status": "pending_approval", "approval_id": record["id"]}


def finalize_new_top_level_area(payload: dict) -> dict:
    """Called only once the operator approves the pending record above
    (ADR-021 point 5) -- performs the actual write, never called for a
    declined record. Reuses _unique_filename_stem/_placement_frontmatter/
    _link_referenced_entity exactly as Tier 1 does (never a second,
    divergent write path), operating on the payload's own stored
    proposal fields instead of a freshly-resolved `decision`."""
    subfolder = f"Work/{payload['kind']}"
    filename_stem = _unique_filename_stem(subfolder, payload["filename_stem"])
    path = vault_writer.write_note(subfolder, filename_stem, _placement_frontmatter(payload), payload["body"])
    _link_referenced_entity(path, payload)
    return {"status": "written", "path": path, "kind": payload["kind"], "tags": payload["tags"]}


def _maybe_create_cross_cutting_proposal(
    *, decision, known_customers, known_partners, already_filed_path,
    source_description, requesting_agent_id,
) -> str | None:
    """Re-checks the model's own cross_cutting_implication in Python --
    never trusted from the model's own naming alone (the same discipline
    ADR-021 point 2 already applies to is_new_top_level_area). Silently
    discards (returns None) rather than raising or fabricating a proposal
    when the named entity isn't genuinely a DIFFERENT, already-known
    customer/partner than this SAME decision's own primary reference --
    known_customers/known_partners here are the SAME pre-fetched lists
    determine_placement_and_file already grounded this whole decision in,
    never a second, divergent lookup."""
    implication = decision.get("cross_cutting_implication")
    if not implication:
        return None

    entity_customer = implication.get("customer")
    entity_partner = implication.get("partner")
    if entity_customer:
        entity_type, entity_name = "customer", entity_customer
    elif entity_partner:
        entity_type, entity_name = "partner", entity_partner
    else:
        return None

    if entity_type == "customer":
        if entity_name not in known_customers:
            return None
        if entity_name == decision.get("referenced_customer"):
            return None
    else:
        if entity_name not in known_partners:
            return None
        if entity_name == decision.get("referenced_partner"):
            return None

    proposal = _create_cross_cutting_proposal(
        entity_type=entity_type,
        entity_name=entity_name,
        reason=implication.get("reason", ""),
        already_filed_path=already_filed_path,
        source_description=source_description,
        requesting_agent_id=requesting_agent_id,
    )
    return proposal["approval_id"]


def _create_cross_cutting_proposal(
    *, entity_type, entity_name, reason, already_filed_path,
    source_description, requesting_agent_id,
) -> dict:
    """Mirrors _create_tier_2_proposal's own exact shape -- a LOCAL (not
    module-level) pending_approval_registry import, trigger="direct"
    (never "background": a single pipeline tick can legitimately produce
    multiple distinct cross-cutting proposals across different content,
    and "background"'s idempotency guard would silently collapse them)."""
    from app.business import pending_approval_registry  # local import -- see _create_tier_2_proposal's own Context/Notes for why

    payload = {
        "entity_type": entity_type,
        "entity_name": entity_name,
        "reason": reason,
        "already_filed_path": already_filed_path,
        "source_description": source_description,
    }
    description = (
        f"Vault Filing Expert flags a possible cross-cutting KB update for "
        f"{entity_type} \"{entity_name}\": {reason}"
    )
    record = pending_approval_registry.create_pending_approval(
        agent_id="vault-filing-expert",
        trigger="direct",
        action_id="propose_cross_cutting_update",
        description=description,
        payload=payload,
    )
    return {"status": "pending_approval", "approval_id": record["id"]}


def finalize_cross_cutting_update(payload: dict) -> dict:
    """Called only once the operator approves a propose_cross_cutting_update
    Pending Approval (app/api/pending_approvals_router.py's
    `_APPROVAL_HANDLERS["propose_cross_cutting_update"]`, ADR-021 point 5)
    -- performs the deferred write, never called for a declined record.
    Mirrors finalize_thread_project_routing's own "payload-driven deferred
    write" shape exactly (REQ-SB-55-US-01-T04's own precedent). The ONLY
    write this handler performs is an additive `customer/<slug>` or
    `partner/<slug>` tag unioned into the already-filed note's own
    EXISTING `tags` list (ADR-004: customer/partner are tags, never
    folders) -- NEVER touches captures.md (ADR-042's operator-only
    invariant). Reuses REQ-SB-55-US-01-T01's own upsert_frontmatter_key
    for the write -- never insert_frontmatter_key_if_missing, which would
    silently no-op since `tags` is already present on an already-filed
    note. Idempotent by construction: a repeat approval with the same
    payload finds new_tag already in existing_tags and skips the write
    entirely, so no duplicate tag is ever produced."""
    note_path = Path(payload["already_filed_path"])
    entity_type = payload["entity_type"]
    entity_name = payload["entity_name"]
    new_tag = f"{entity_type}/{vault_writer.tag_slug(entity_name)}"

    frontmatter, _ = vault_writer.read_note(note_path)
    existing_tags = frontmatter.get("tags", [])
    if new_tag not in existing_tags:
        vault_writer.upsert_frontmatter_key(note_path, "tags", existing_tags + [new_tag])

    return {
        "path": payload["already_filed_path"],
        "message": (
            f"Approved — tagged {entity_type} \"{entity_name}\" "
            f"({new_tag}) on {payload['already_filed_path']}."
        ),
    }
