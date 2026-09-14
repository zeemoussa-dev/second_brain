"""Companies the reader NAMED but no email ever came from.

`find_new_entities.py` discovers a company from an email domain -- somebody at
it wrote to us. That misses the other half entirely: a company discussed inside
a thread that never sent us mail. "LIMAD", "Kyndryl", "Starwood Digital" appear
in real summaries, are recorded in `UnknownCompanies.json` by the tagging pass
when it cannot resolve them, and then sit there. 736 names had accumulated with
no way for the operator to act on them, because the file he curates
(`Entities.md`) only ever hears about domains.

This puts them in front of him, in that file, where marking one is the whole
point. Each lands as a row with:

  * `Ignore: Yes` and `Created: No` -- his standing rule is that the default is
    ignore and NOTHING is created until he has marked it himself. A row here
    changes nothing on its own; it is a question, not a decision.
  * an empty `Domain` -- these have none, and that is what distinguishes a
    mention-derived row from every domain-derived one.

Ordered by how often the name was actually seen, so the ones worth a decision
are at the top rather than buried behind a company mentioned once in a
newsletter. The evidence itself -- the threads each name appeared in -- goes to
a companion report, because Entities.md's own row schema has nowhere to put it
and inventing a field would mean teaching three separate renderers about it.

    python find_mentioned_entities.py --vault-path P [--min-mentions 1] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from find_new_entities import (_data_root, _split_domains, parse_entities,  # noqa: E402
                               render_entities)

_REPORT_NAME = "Unclassified-Companies.md"


def _add_engines_to_path() -> None:
    """Find the shared engines whatever layout this runs in.

    In the repo they are `skills/managers/`; deployed, Hermes puts them in
    `<hermes>/managers/` several levels above the flat Skill folder."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "managers" / "company_index.py"
        if candidate.is_file():
            if str(candidate.parent) not in sys.path:
                sys.path.insert(0, str(candidate.parent))
            return


_add_engines_to_path()

import company_index as ci  # noqa: E402

# Deciding whether a name is one we already track is exactly what company_index
# exists for. A second copy of the rule here is how "L'IMAD" and "LIMAD" end up
# on opposite sides of a comparison in one script and the same side in another.
normalise = ci.normalise_company


def already_known(entries: list[dict], vault_path: Path) -> set[str]:
    """Every spelling the vault can already resolve: a row's own name, its
    heading, each of its aliases, and the spellings on the hub notes
    themselves -- which is where an alias added by hand after the row was
    written actually lives."""
    known: set[str] = set()
    for entry in entries:
        fields = entry["fields"]
        spellings = [entry["heading"], fields.get("Company Name", "")]
        # Aliases is comma-separated and doubles as the place a second DOMAIN
        # gets merged in; a domain is not a spelling, so it is filtered out.
        spellings += [alias for alias in _split_domains(fields.get("Aliases", ""))
                      if "." not in alias]
        known |= {normalise(s) for s in spellings if normalise(s)}
    try:
        for record in ci.hubs(vault_path):
            known |= {normalise(s) for s in record["spellings"] if normalise(s)}
    except OSError:
        # The rows above are the authority for what is already tracked; an
        # unreadable vault must not turn into a flood of duplicate questions.
        pass
    return known


def unknown_companies(data_root: Path) -> dict:
    # `<data root>/data/`, which is where apply_thread_extract.py and
    # apply_file_review.py actually write it -- alongside the saved extracts,
    # not beside Settings/.
    path = data_root / "data" / "UnknownCompanies.json"
    if not path.is_file():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _threads_of(record) -> list[str]:
    threads = (record or {}).get("threads") or []
    names = [str(t.get("name") or "").strip() for t in threads if isinstance(t, dict)]
    return [n for n in names if n]


def _seen(record) -> int:
    try:
        return int((record or {}).get("seen") or 0)
    except (TypeError, ValueError):
        return 0


def _render_names(lines: list[str], items: list[dict]) -> None:
    for item in items:
        lines.append(f"### {item['name']}")
        lines.append("")
        lines.append(f"Seen {item['seen']} time{'s' if item['seen'] != 1 else ''}"
                     f" across {len(item['threads'])} thread"
                     f"{'s' if len(item['threads']) != 1 else ''}.")
        lines.append("")
        for subject in item["threads"][:5]:
            lines.append(f"- {subject}")
        if len(item["threads"]) > 5:
            lines.append(f"- ...and {len(item['threads']) - 5} more")
        lines.append("")


def render_report(added: list[dict], held_back: list[dict], min_mentions: int) -> str:
    """The evidence, so a name can be judged without opening a thread.

    Reports EVERY unresolved name, not only the ones written into Entities.md:
    the threshold decides how many rows the operator hand-curates, never how
    much he is allowed to see."""
    lines = [
        "# Unclassified companies",
        "",
        "Names the summariser read inside a thread that resolve to no company we",
        "track, and that no email has ever come from -- so they reach this list",
        "rather than being discovered from a domain.",
        "",
        "This file is regenerated. Edit `Entities.md`, never this one.",
        "",
        f"## In Entities.md now -- {len(added)} to mark",
        "",
        "Each is a row with `Ignore: Yes`, `Created: No` and an empty `Domain`.",
        "Nothing is created from them. **Mark the real ones**: set `Ignore: No`,",
        "and move it under `## Partners` if that is what it is. Leave the rest.",
        "",
    ]
    _render_names(lines, added)
    lines += [
        f"## Not added -- {len(held_back)} seen fewer than {min_mentions} times",
        "",
        "Here for the record, not in `Entities.md`. Re-run with a lower",
        "`--min-mentions` to bring any of these in.",
        "",
    ]
    _render_names(lines, held_back)
    return "\n".join(lines) + "\n"


def surface(vault_path: Path, entities_path: Path, *, min_mentions: int,
            dry_run: bool) -> dict:
    data_root = _data_root(vault_path)
    content = entities_path.read_text(encoding="utf-8-sig")
    entries = parse_entities(content)
    known = already_known(entries, vault_path)

    unclassified: list[dict] = []
    resolved_since = 0
    for name, record in unknown_companies(data_root).items():
        clean = str(name or "").strip()
        if not clean:
            continue
        if normalise(clean) in known:
            resolved_since += 1
            continue
        unclassified.append({"name": clean, "seen": _seen(record),
                             "threads": _threads_of(record)})
    # Most-mentioned first: the operator reads this top-down and the names worth
    # a decision should not be behind one mentioned once in a newsletter.
    unclassified.sort(key=lambda item: (-item["seen"], item["name"].lower()))
    to_add = [item for item in unclassified if item["seen"] >= min_mentions]
    held_back = [item for item in unclassified if item["seen"] < min_mentions]

    for item in to_add:
        entries.append({
            "section": "customer",
            "heading": item["name"],
            "fields": {"Company Name": item["name"], "Aliases": "", "Affiliate of": "",
                       "Created": "No", "Ignore": "Yes", "Domain": "", "Deleted": "No"},
        })

    report_path = entities_path.parent / _REPORT_NAME
    if unclassified and not dry_run:
        if to_add:
            entities_path.write_text(render_entities(entries), encoding="utf-8")
        report_path.write_text(render_report(to_add, held_back, min_mentions), encoding="utf-8")

    return {
        "added": len(to_add),
        "held_back": len(held_back),
        "already_tracked": resolved_since,
        "entities_path": str(entities_path),
        "report_path": str(report_path) if unclassified else "",
        "names": [item["name"] for item in to_add[:20]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Put company names read inside threads into Entities.md to be marked.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--entities-name", default="Entities.md")
    parser.add_argument("--min-mentions", type=int, default=1,
                        help="Skip a name seen fewer times than this.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    vault_path = Path(args.vault_path)
    entities_path = _data_root(vault_path) / "Settings" / args.entities_name
    if not entities_path.is_file():
        print(json.dumps({"error": f"no Entities file at {entities_path}"}))
        return 2
    print(json.dumps(surface(vault_path, entities_path,
                             min_mentions=args.min_mentions, dry_run=args.dry_run),
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
