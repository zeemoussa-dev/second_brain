"""CLI entry point: Step 4 (the mechanical half) of the company/partner
discovery sequence. The agent itself does ALL the real judgment --
reading a Thread's messages, writing its summary, deciding which known
companies it's about, deciding where to insert wikilinks in the summary
text -- this script only ever applies decisions the agent already made.
(Operator, 2026-08-21: "This should be done by Prompts as much as
possible... Tagging is the only task that needs code.")

Given one Thread's already-agent-written summary + short_summary + a
list of company names/aliases it's about, this script:

  1. Writes the summary (already wikilinked by the agent) into the
     Thread's own "## Summary".
  2. Resolves each company name/alias against the REAL Customer/Partner/
     Affiliate hub notes Step 3 already created (matching against each
     hub note's own `name` and `aliases` frontmatter) -- an unresolvable
     name is skipped and reported, never used to fabricate a new hub
     note (that stays Step 3/the operator's own gated job).
  3. Adds `customer/<slug>` / `partner/<slug>` tags (one per resolved
     company -- a thread can genuinely be about more than one) to the
     Thread and every message under it -- merged into each note's
     existing `tags` list, never overwriting it. Deliberately NEVER
     touches Person notes (2026-08-21 bug fix, see below).
  4. Appends one dated log line (short_summary + a link back to the
     Thread) to each resolved company's own `<Name>-log.md`, then
     re-sorts that file's whole entry list newest-to-oldest -- entries
     arrive in whatever order the agent processes Threads in, not
     necessarily chronological, so a re-sort (not a plain append) is
     what keeps the ordering promise true after every call.

An Affiliate is tagged with ITS OWN slug, never rolled up to its parent
(operator: "the company in message is the company not the parent") --
the parent relationship is already discoverable via the Affiliate's own
`affiliate_of` frontmatter field and the parent's own "## Affiliates"
backlink, so no second, redundant tag is needed.

Person notes are NEVER tagged here, even though a Thread's own messages
carry participant_links -- an earlier version did cascade the Thread's
company tags onto every participant, which is wrong: being CC'd on a
thread about a company doesn't mean you belong to it (an internal
@core42.ai person on a G42-related thread got tagged `partner/g42` this
way, and the operator's own account got tagged onto nearly every
company in the vault). Person tagging is exclusively domain-based (does
THIS person's own email match a real hub note's own domain) and lives in
create-companies-partners's own retag_people_by_domain, run once,
idempotently, independent of any Thread content.

Usage:
    python apply_thread_review.py --vault-path P --input-file F

F: {"thread_path": str, "summary": str, "short_summary": str,
    "companies": [str, ...]}
(thread_path is the Thread's own concept .md file, vault-absolute or
relative -- whatever the agent's own read_file call used.)

Prints {"tags_applied": [...], "companies_unresolved": [...],
"messages_tagged": int, "log_entries_added": [...], "last_message_at":
str, "last_summarized_at": str}.

Also stamps the Thread's own `last_message_at` (its latest message's own
`received`) and `last_summarized_at` (now) frontmatter fields on every
call -- 2026-08-21, operator: a recurring run needs to tell "already
summarized, nothing new since" apart from "needs a summary" without
re-reading every Thread. See SKILL.md's own Resumability section for the
skip rule this enables.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)
_LOG_LINE_PATTERN = re.compile(r"^- (\d{4}-\d{2}-\d{2}): (.+)$")

_CALLER = "apply_thread_review.apply_thread_review"
_HUMAN_OWNED_HEADERS = frozenset({"## Personal Notes", "## Actions"})


def _tag_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9/]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def _format_frontmatter_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_format_frontmatter_value(v) for v in value) + "]"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def _parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [
            match.group(1).replace('\\"', '"').replace("\\\\", "\\")
            for match in _LIST_ITEM_PATTERN.finditer(inner)
        ]
    return raw


def read_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter_block = text[4:end]
    body = text[end + 5:]
    frontmatter: dict = {}
    for line in frontmatter_block.splitlines():
        match = _FRONTMATTER_LINE.match(line)
        if match:
            frontmatter[match.group(1)] = _parse_frontmatter_value(match.group(2))
    return frontmatter, body


def merge_tags(path: Path, new_tags: list[str]) -> bool:
    """Unions new_tags into path's own `tags` frontmatter list (creating
    it if absent), preserving every other line -- including the body --
    byte-for-byte. Returns True if the file was changed."""
    frontmatter, _ = read_note(path)
    existing = list(frontmatter.get("tags") or [])
    merged = existing + [tag for tag in new_tags if tag not in existing]
    if merged == existing:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    new_line = f"tags: {_format_frontmatter_value(merged)}\n"
    replaced = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == "tags":
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(-1, new_line)  # just before the closing "---\n"
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def upsert_frontmatter_key(path: Path, key: str, value) -> bool:
    """2026-08-21, operator: recurring runs need to tell "already
    summarized, no new message since" apart from "needs a summary"
    without re-reading every Thread's body -- this sets last_message_at/
    last_summarized_at (see apply_thread_review below). Returns False,
    no-op, if the key already holds this exact value."""
    frontmatter, _ = read_note(path)
    if key in frontmatter and frontmatter[key] == value:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    new_line = f"{key}: {_format_frontmatter_value(value)}\n"
    replaced = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == key:
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(-1, new_line)
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def insert_body_section_if_missing(path: Path, header: str) -> bool:
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    if header_line_pattern.search(text) is not None:
        return False
    separator = "" if text.endswith("\n") else "\n"
    path.write_text(text + separator + f"\n{header}\n", encoding="utf-8")
    return True


def replace_body_section(path: Path, header: str, new_content: str, *, caller: str) -> bool:
    if header in _HUMAN_OWNED_HEADERS or caller != _CALLER:
        raise PermissionError(f"caller {caller!r} is not allowed to write {header!r}")
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        return False
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    new_text = text[:region_start] + "\n\n" + new_content.strip("\n") + "\n\n" + text[region_end:]
    path.write_text(new_text, encoding="utf-8")
    return True


# ── company resolution ──────────────────────────────────────────────────

def _iter_hub_notes(vault_path: Path):
    for root_name, kind in (("Customers", "customer"), ("Partners", "partner")):
        root = vault_path / "Work" / root_name
        if not root.exists():
            continue
        for md_path in root.rglob("*.md"):
            if not md_path.is_file():
                continue
            if md_path.stem.endswith("-log") or md_path.stem.endswith("-captures"):
                continue
            if md_path.parent.name != md_path.stem:
                continue  # only <Name>/<Name>.md concept files, not stray same-level files
            yield md_path, kind


def build_company_index(vault_path: Path) -> dict[str, tuple[str, str, Path]]:
    """lowercased name/alias -> (kind, tag_slug, hub_md_path)."""
    index: dict[str, tuple[str, str, Path]] = {}
    for md_path, kind in _iter_hub_notes(vault_path):
        frontmatter, _ = read_note(md_path)
        name = frontmatter.get("name") or md_path.stem
        slug = _tag_slug(md_path.stem)
        entry = (kind, slug, md_path)
        index[name.strip().lower()] = entry
        for alias in frontmatter.get("aliases") or []:
            index[alias.strip().lower()] = entry
    return index


def resolve_companies(vault_path: Path, company_names: list[str]) -> tuple[list[tuple[str, str, Path]], list[str]]:
    index = build_company_index(vault_path)
    resolved: list[tuple[str, str, Path]] = []
    unresolved: list[str] = []
    seen_slugs: set[str] = set()
    for name in company_names:
        entry = index.get(name.strip().lower())
        if entry is None:
            unresolved.append(name)
            continue
        kind, slug, hub_md = entry
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        resolved.append((kind, slug, hub_md))
    return resolved, unresolved


# ── company log entries ─────────────────────────────────────────────────

def append_log_entry(hub_md: Path, date: str, short_summary: str, thread_wikilink: str) -> None:
    log_path = hub_md.parent / f"{hub_md.stem}-log.md"
    if not log_path.exists():
        log_path.write_text(f"# {hub_md.stem}\n\n", encoding="utf-8")
    text = log_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header_lines = [l for l in lines if not _LOG_LINE_PATTERN.match(l)]
    entries = [m.groups() for l in lines if (m := _LOG_LINE_PATTERN.match(l))]
    new_line_text = f"{short_summary.strip()} -- {thread_wikilink}"
    if (date, new_line_text) not in entries:
        entries.append((date, new_line_text))
    entries.sort(key=lambda e: e[0], reverse=True)
    rendered_entries = [f"- {d}: {t}" for d, t in entries]
    while header_lines and not header_lines[-1].strip():
        header_lines.pop()
    new_text = "\n".join(header_lines) + "\n\n" + "\n".join(rendered_entries) + "\n"
    log_path.write_text(new_text, encoding="utf-8")


# ── main ─────────────────────────────────────────────────────────────────

def apply_thread_review(vault_path: Path, data: dict) -> dict:
    thread_path = Path(data["thread_path"])
    if not thread_path.is_absolute():
        thread_path = vault_path / thread_path
    summary = data["summary"]
    short_summary = data["short_summary"]
    company_names = data.get("companies") or []

    resolved, unresolved = resolve_companies(vault_path, company_names)
    tags = [f"{kind}/{slug}" for kind, slug, _ in resolved]

    insert_body_section_if_missing(thread_path, "## Summary")
    replace_body_section(thread_path, "## Summary", summary, caller=_CALLER)
    if tags:
        merge_tags(thread_path, tags)

    # 2026-08-21 bug fix: this used to ALSO tag every Person linked from
    # each message with the Thread's own company tags -- wrong (operator:
    # "naima.bikbi@core42.ai is tagged to every single Customer she was
    # in an email with, which is not right"). Being a participant on a
    # thread about a company does not mean you BELONG to that company --
    # an internal @core42.ai person on a G42-related thread is not
    # thereby G42's own. Person tagging is now exclusively domain-based
    # (does THIS person's own email domain match a real hub note's own
    # domain), handled once, idempotently, by create-companies-partners's
    # own retag_people_by_domain -- never here. Only the Thread and its
    # own Messages get these company tags.
    thread_dir = thread_path.parent
    messages_dir = thread_dir / "messages"
    messages_tagged = 0
    if tags and messages_dir.exists():
        for message_path in sorted(messages_dir.glob("*.md")):
            if not message_path.is_file():
                continue
            if merge_tags(message_path, tags):
                messages_tagged += 1

    # log date: the Thread's own latest message date, matching
    # rename_thread.py's own convention -- never re-derived differently.
    message_paths = sorted(messages_dir.glob("*.md")) if messages_dir.exists() else []
    date = ""
    last_message_at = ""
    if message_paths:
        latest_frontmatter, _ = read_note(message_paths[-1])
        last_message_at = latest_frontmatter.get("received") or ""
        date = last_message_at[:10]
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 2026-08-21, operator: stamp both timestamps every time a summary is
    # applied, so a future recurring run can skip this Thread outright
    # (last_summarized_at >= last_message_at) instead of re-reading it --
    # and correctly re-flags it the moment a genuinely new message's own
    # last_message_at moves past this run's last_summarized_at.
    if last_message_at:
        upsert_frontmatter_key(thread_path, "last_message_at", last_message_at)
    last_summarized_at = datetime.now().isoformat(timespec="seconds")
    upsert_frontmatter_key(thread_path, "last_summarized_at", last_summarized_at)

    thread_wikilink = f"[[{thread_path.stem}]]"
    log_entries_added = []
    for _, _, hub_md in resolved:
        append_log_entry(hub_md, date, short_summary, thread_wikilink)
        log_entries_added.append(hub_md.stem)

    return {
        "tags_applied": tags,
        "companies_unresolved": unresolved,
        "messages_tagged": messages_tagged,
        "log_entries_added": log_entries_added,
        "last_message_at": last_message_at,
        "last_summarized_at": last_summarized_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))
    result = apply_thread_review(vault_path, data)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
