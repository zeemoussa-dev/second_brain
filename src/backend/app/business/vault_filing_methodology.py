"""Builds the Vault Filing Expert's own placement-decision prompt (ADR-021
point 2) -- a condensed excerpt of Documentation/References/beyond-the-
second-brain-methodology.md's own principles plus ADR-004's tag/folder
split, embedded alongside the three deterministically pre-fetched
known-value lists (never left to the model's own discretion to tool-call
for them) and the content awaiting placement. build_placement_prompt is
this module's one public entry point, returning the message list
determine_placement_and_file passes straight to model.invoke(...).
"""
from langchain_core.messages import HumanMessage, SystemMessage

_METHODOLOGY_EXCERPT = (
    "You are the Vault Filing Expert for a personal Obsidian-based Second "
    "Brain vault, deciding where new content belongs. Ground every "
    "decision in this vault's own documented design methodology "
    "(condensed from Beyond the Second Brain):\n"
    "- Atomic but Connected: a note is about one idea, and is only "
    "valuable once linked to what it touches -- never leave a note with "
    "no links to related vault entities.\n"
    "- Output-Oriented: prefer placements that reflect what the content "
    "is FOR, not just what topic it mentions.\n"
    "- Durable over Clever: reuse an existing, already-established "
    "category whenever it genuinely fits; propose a new one only when "
    "nothing existing genuinely fits -- never force a stretch-fit, and "
    "never invent a new category when an existing one is a real match.\n"
    "- Extensibility over enumeration: this vault's own categories are "
    "never a fixed, hardcoded enum -- proposing a genuinely new one is "
    "expected and correct when the content warrants it.\n"
    "- Tag/folder split (ADR-004): a `kind` (Emails, Meetings, Notes, "
    "etc.) is a stable, single-home property of a note and is the "
    "top-level folder (Work/<kind>/); a `customer` or `partner` is "
    "multidimensional and is NEVER a folder level -- it lives only as a "
    "`customer/<slug>` or `partner/<slug>` tag plus a real "
    "`[[wikilink]]` to that entity's own hub note, never a folder."
)

_JSON_SCHEMA_INSTRUCTIONS = (
    "Reply with EXACTLY one JSON object (no markdown code fence, no other "
    "commentary) with these keys:\n"
    '- "kind": string -- the top-level Work/<kind>/ folder this content '
    "belongs under. Reuse one of the known kinds below whenever it "
    "genuinely fits; propose a new, short, Title-Case kind name only when "
    "none of them genuinely fits.\n"
    '- "is_new_top_level_area": boolean -- true ONLY when "kind" is not '
    "one of the known kinds below (this is re-checked mechanically after "
    "your reply, so answer honestly).\n"
    '- "tags": array of strings -- lowercase, hyphenated tag values '
    'following this vault\'s own convention: always include "kind/<kind-'
    'slug>"; include "customer/<slug>" or "partner/<slug>" if this '
    "content is genuinely about a specific customer or partner "
    "organization, whether or not that organization is already in the "
    "known lists below -- a brand-new customer/partner this vault has "
    "never seen before still gets a customer/<slug> or partner/<slug> "
    "tag, exactly like an already-known one.\n"
    '- "referenced_customer": string or null -- REQUIRED, non-null, '
    'whenever "tags" includes a "customer/<slug>" tag: the customer '
    "organization's real display name (e.g. \"Acme Corp\"), reused "
    "verbatim from the known customers list below if it matches one of "
    "them, or the content's own genuinely new customer name otherwise. "
    "null only when no customer/<slug> tag was set.\n"
    '- "referenced_partner": string or null -- REQUIRED, non-null, '
    'whenever "tags" includes a "partner/<slug>" tag, by the identical '
    "rule as referenced_customer above (reuse a known partner name "
    "verbatim, or the content's own genuinely new partner name). null "
    "only when no partner/<slug> tag was set. Never set both "
    "referenced_customer and referenced_partner.\n"
    '- "filename_stem": string -- a short, descriptive filename stem for '
    "the new note (no extension, no folder).\n"
    '- "body": string -- the note\'s own Markdown body content, written '
    "from source_description/content. If it genuinely references a "
    "known customer/partner, also include an inline "
    '`[[wikilink]]`-style reference to it in the body text.\n'
    '- "confidence": "high" or "low" -- "low" whenever you are not '
    "genuinely confident in this placement even after reasoning from the "
    "methodology and the vault's own current structure.\n"
    '- "uncertainty_note": string or null -- when confidence is "low", a '
    "short, honest explanation of what you are unsure about; null "
    "otherwise. Never fabricate confidence you do not have.\n"
    '- "cross_cutting_implication": object or null -- set ONLY when this '
    "content ALSO implies a KB update for a DIFFERENT customer or partner "
    "than the one named by referenced_customer/referenced_partner above "
    "(e.g. this content is primarily about one customer but also affects "
    "another, already-known customer or partner elsewhere in the vault). "
    'When set, an object with exactly these keys: {"customer": string or '
    'null, "partner": string or null -- exactly one of these two non-null, '
    "naming the OTHER, different customer or partner this content "
    'affects; "reason": string -- a short, honest explanation of why this '
    "content also implies a KB update for that other entity}. null "
    "whenever no such different-entity implication genuinely exists -- "
    "never fabricate one just to fill the field."
)


def build_placement_prompt(
    content: str,
    source_description: str,
    known_kinds: list[str],
    known_customers: list[str],
    known_partners: list[str],
    prompt_override: str | None = None,
) -> list:
    """prompt_override (REQ-SB-66-US-01-T03/ADR-044, optional, additive) --
    when set, REPLACES _METHODOLOGY_EXCERPT as the returned SystemMessage's
    own content verbatim; the HumanMessage (known_lists_text/
    source_description/content/_JSON_SCHEMA_INSTRUCTIONS) is never made
    overridable and is built identically either way. None (the default)
    reproduces today's byte-for-byte _METHODOLOGY_EXCERPT text -- the
    Scenario 4/AC-04 regression bar."""
    known_lists_text = (
        f"Known kinds (existing Work/<kind>/ folders): {known_kinds}\n"
        f"Known customers: {known_customers}\n"
        f"Known partners: {known_partners}"
    )
    human_content = (
        f"{known_lists_text}\n\n"
        f"Source description: {source_description}\n\n"
        f"Content awaiting placement:\n{content}\n\n"
        f"{_JSON_SCHEMA_INSTRUCTIONS}"
    )
    system_message_text = prompt_override if prompt_override is not None else _METHODOLOGY_EXCERPT
    return [
        SystemMessage(content=system_message_text),
        HumanMessage(content=human_content),
    ]
