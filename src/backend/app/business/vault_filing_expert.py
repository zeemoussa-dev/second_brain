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

from app.business import customer_hub_linking, partner_hub_linking, vault_filing_methodology
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
    content: str, source_description: str, requesting_agent_id: str
) -> dict:
    model = model_factory.resolve_agent_model("vault-filing-expert")
    if model is None:
        return {
            "status": "unavailable",
            "message": "The Vault Filing Expert's selected Provider is not available.",
        }

    known_kinds = vault_writer.list_known_kinds()
    known_customers = vault_writer.list_known_customers()
    known_partners = vault_writer.list_known_partners()

    prompt = vault_filing_methodology.build_placement_prompt(
        content=content,
        source_description=source_description,
        known_kinds=known_kinds,
        known_customers=known_customers,
        known_partners=known_partners,
    )
    raw = model.invoke(prompt)
    decision = _parse_decision(raw.content)

    # Never trust the model's own boolean alone -- re-check the Tier
    # boundary against the real, live vault structure (ADR-021 point 2).
    is_new_top_level_area = decision["kind"] not in known_kinds

    if is_new_top_level_area:
        return _create_tier_2_proposal(
            content=content,
            source_description=source_description,
            requesting_agent_id=requesting_agent_id,
            decision=decision,
        )

    body = decision["body"]
    if decision.get("confidence") == "low":
        body = _UNCERTAINTY_PREFIX.format(note=decision.get("uncertainty_note") or "This placement is a best guess.") + body

    subfolder = f"Work/{decision['kind']}"
    filename_stem = _unique_filename_stem(subfolder, decision["filename_stem"])
    path = vault_writer.write_note(subfolder, filename_stem, _placement_frontmatter(decision), body)
    _link_referenced_entity(path, decision)

    return {
        "status": "written",
        "path": path,
        "kind": decision["kind"],
        "tags": decision["tags"],
        "confidence": decision.get("confidence", "high"),
    }


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
