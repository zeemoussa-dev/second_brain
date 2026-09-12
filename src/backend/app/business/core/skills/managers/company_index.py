"""Resolving a company NAME to its hub note -- the one implementation.

Two callers face the same problem from different directions: a reader naming
companies in an email, and the CBO naming one out loud after a meeting. In both
cases the name that arrives is not the name on the hub. It carries a legal form
("Mubadala Health LLC"), an abbreviation ("WWT"), wiki brackets a reader left in
("[[ADNOC]]"), a dotted initialism ("BAYANAT G I Q - P.S.C"), or it is the
PARENT of the company actually meant.

Two rules this enforces, both bought with real mistakes (2026-09-12):

  * a parent and its affiliate are DIFFERENT companies -- "TAQA" must never
    resolve to "TAQA Distribution", nor "Mubadala" to "Mubadala Health"; and
  * a name that matches two companies is returned as ambiguous, never resolved
    by picking one. A capture filed against the wrong company is a false fact.

Lives beside vault_manager.py because both Skills need it and a second copy is
how two spellings of one rule start drifting apart.
"""
from __future__ import annotations

import re
from pathlib import Path

import vault_manager as vm

# The legal form a formal document carries, never part of what identifies the
# company.
_LEGAL_FORMS = {"llc", "ltd", "limited", "plc", "pjsc", "psc", "opc", "inc",
                "corp", "corporation", "fze", "fz", "gmbh", "sa", "nv", "bv",
                "pte", "pvt", "co"}
_NAME_PUNCT = re.compile(r"[^\w\s&+]+")
# "P.J.S.C" / "O.P.C" -- stripping punctuation alone would scatter a dotted
# initialism into single letters no legal-form list can match.
_DOTTED = re.compile(r"((?:\w\.){2,}\w?)")

_HUB_TYPES = {"Customer": "customer", "Partner": "partner"}


def normalise_company(name: str) -> str:
    """A company name reduced to what identifies it: lowercased, punctuation
    dropped, dotted initialisms collapsed, trailing legal forms removed."""
    text = _DOTTED.sub(lambda m: m.group(1).replace(".", ""), str(name or "").lower())
    words = _NAME_PUNCT.sub(" ", text).split()
    while words and words[-1] in _LEGAL_FORMS:
        words.pop()
    return " ".join(words)


def tag_slug(text: str) -> str:
    """The company tag slug, the same shape the hubs carry."""
    slug = re.sub(r"[^a-z0-9/]+", "-", str(text).lower()).strip("-")
    return slug or "untitled"


def iter_hubs(vault_path: Path):
    """(hub note, "customer"|"partner") for every real hub, Affiliates included.

    A folder is NOT a hub because of its shape: an Opportunity nests under a
    Customer with the identical own-folder shape, so the `type` field decides."""
    for root_name in ("Customers", "Partners"):
        base = vault_path / "Work" / root_name
        if not base.is_dir():
            continue
        for hub_dir in list(base.glob("*")) + list(base.glob("*/Affiliates/*")):
            hub_md = hub_dir / f"{hub_dir.name}.md"
            if not hub_md.is_file():
                continue
            frontmatter, _ = vm.read_note(hub_md)
            kind = _HUB_TYPES.get(str(frontmatter.get("type") or ""))
            if kind:
                yield hub_md, kind


def _spellings(frontmatter: dict, hub_md: Path) -> list[str]:
    aliases = frontmatter.get("aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    written = [str(n).strip() for n in [frontmatter.get("name") or hub_md.stem, *aliases]]
    return [n for n in written if n]


def hubs(vault_path: Path) -> list[dict]:
    """Every company in the vault, as records a caller can answer from."""
    records: list[dict] = []
    for hub_md, kind in iter_hubs(vault_path):
        frontmatter, _ = vm.read_note(hub_md)
        is_affiliate = hub_md.parent.parent.name == "Affiliates"
        affiliates_dir = hub_md.parent / "Affiliates"
        affiliates = sorted(
            child.name for child in affiliates_dir.iterdir()
            if affiliates_dir.is_dir() and child.is_dir()
            and (child / f"{child.name}.md").is_file()
        ) if affiliates_dir.is_dir() else []
        records.append({
            "stem": hub_md.stem,
            "name": str(frontmatter.get("name") or hub_md.stem),
            "kind": kind,
            "tag": f"{kind}/{tag_slug(hub_md.stem)}",
            "path": str(hub_md),
            "spellings": _spellings(frontmatter, hub_md),
            "domains": [d.strip().lower() for d in str(frontmatter.get("domain") or "").split(",") if d.strip()],
            "parent": str(frontmatter.get("affiliate_of") or "") if is_affiliate else "",
            "affiliates": affiliates,
        })
    return records


def resolve(vault_path: Path, query: str, *, records: list[dict] | None = None) -> list[dict]:
    """Every company a name could mean: none, one, or -- when it is genuinely
    ambiguous -- several, for the caller to ask about.

    A hub's own spelling wins outright: "Mubadala" is Mubadala even though
    "Mubadala Health" also begins with it. Only when nothing matches exactly is
    the identifying form compared, so a legal name still finds its own hub."""
    query = str(query or "").strip()
    if not query:
        return []
    records = hubs(vault_path) if records is None else records
    exact = [r for r in records if any(s.lower() == query.lower() for s in r["spellings"])]
    if exact:
        return exact
    wanted = normalise_company(query)
    if not wanted:
        return []
    return [r for r in records
            if any(normalise_company(s) == wanted for s in r["spellings"])]
