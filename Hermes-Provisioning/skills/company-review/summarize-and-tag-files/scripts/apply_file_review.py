"""CLI entry point: the mechanical half of Job 5 (files-summarize).
Mirrors apply_thread_review.py's own "the agent decides, the script
applies" split exactly -- reading and understanding a real file
(PDF/DOCX/PPTX/XLSX/image) is real judgment no script can do; this
script only ever applies a summary/short_summary/companies decision the
agent already made.

Given one captured File's already-agent-written summary + short_summary
+ a list of company names/aliases it's genuinely about, this script:

  1. Writes the summary (already wikilinked by the agent, same
     convention apply_thread_review.py uses for Threads) into the
     File's own "## Summary".
  2. Resolves each company name/alias against the REAL Customer/
     Partner/Affiliate hub notes create-companies-partners.py already
     created (matching each hub note's own `name`/`aliases`
     frontmatter) -- an unresolvable name is skipped and reported,
     never used to fabricate a new hub note.
  3. Adds `customer/<slug>`/`partner/<slug>` tags (one per resolved
     company) to the File note -- merged into its existing `tags`,
     never overwriting.
  4. Updates the File's own PARENT Thread's "## Files" section
     (operator, 2026-08-22: "create a log in every thread with files
     and the summary (shorter one)") -- the existing bare
     `- [[file-slug]]` line becomes `- [[file-slug]] -- <short_summary>`,
     replacing the line in place (never duplicated on a rerun) rather
     than a separate log file -- Threads don't get their own Log/
     Captures companion files (ADR-042's own Customer/Partner-only
     scope-lock), so the Thread's own existing "## Files" section IS
     this Job's own log, per the operator's own request.

`vault_manager.py`-based migration, ## Summary write + tag-merge only
(2026-09-02, REQ-SB-88-US-01-T01): the File's "## Summary" write now
goes through the newly-deployed `vault_manager.py` copy in this Skill's
own `scripts/` folder (`vm.modify_section`, `caller="apply_file_review"`
-- the File template's own `## Summary`/`## Details` sections declare no
`allowed_callers`, open to any machine-write caller). A real
pre-migration File note carries no `id` frontmatter field yet -- the
first migrated write mints one (`uuid4`) and backfills it via
`vm.update`, matching `apply_thread_review.py`'s own identical
precedent. Tag merging now goes through `vault_manager.py`'s shared
`merge_tags` instead of this file's own hand-rolled copy. Company
resolution (`build_company_index`/`resolve_companies`) were UNCHANGED by
that task.

Files-log + Details/`--append` migration (2026-09-02,
REQ-SB-88-US-01-T02): the Thread's own "## Files" line-replace and the
`--append` "## Details" follow-up pass now also go through
`vault_manager.py` (`vm.modify_section`, `caller="apply_file_review"`).
The real, deployed Thread `Template.json` `## Files` section's own
`allowed_callers` gained `apply_file_review` as a third, additive entry
alongside `capture_attachments`/`capture_file_link` -- the exact
`allowed_callers` extension mechanism ADR-017 already built. The
line-replace ALGORITHM itself is unchanged (still hand-rolled here);
only its persistence moved off the local `insert_body_section_if_missing`/
`read_body_section`/`replace_body_section` trio. The Details append no
longer manually reads-then-concatenates existing content -- `vm.
modify_section(..., mode="append")` already performs that merge. Image
copy/embed (`_attach_images`/`_unique_sibling_path`) is unrelated
filesystem work, unchanged. The now-fully-superseded local
`insert_body_section_if_missing`/`read_body_section`/`replace_body_section`/
`merge_tags`/`_format_frontmatter_value` primitives and their own
`_CALLER_ALLOW_LISTS`/`_HUMAN_OWNED_HEADERS` guard are removed -- zero
remaining callers in this file. `read_note`/`_parse_frontmatter_value`
stay -- still genuinely called by `build_company_index`/`resolve_companies`
and this file's own `source_thread` frontmatter read.

Mechanical already-summarized skip-guard (found live 2026-09-02, the
real `job5-summarize-tag-files` cron job re-processed 4/15 already-
summarized real Files in its own second run -- SKILL.md's documented
"skip any File whose own `## Summary` is already non-empty" rule had
zero code-level enforcement, 100% agent judgment): `apply_file_review`
now reads the File's own current `## Summary` via `vm.get_section_content`
BEFORE doing any real work and refuses (no-op, `"skipped": true`) a
redundant initial-summary write whenever it is already non-empty --
mirrors `summarize-and-tag-threads`/`job4`'s own existing mechanical
safety net one layer up, adapted to Files' own real shape: Files have no
`last_summarized_at`/`last_message_at`-equivalent freshness fields (the
File template's own `frontmatter_defaults` carries only `type`/`tags`,
confirmed live) because a captured File's own real content never changes
after capture (SKILL.md's own documented reason Files never needed
Threads' timestamp-based skip rule in the first place) -- so
"`## Summary` already non-empty" IS the complete, correct freshness
check for a File, not a partial substitute for one. A caller that
genuinely needs to overwrite an existing summary (e.g. a corrected
re-run) passes `--force` to bypass the guard explicitly. Only the
initial-review path (`apply_file_review`) gets this guard -- the
`--append`/`add_file_detail` "## Details" follow-up path is a
deliberate, repeatable multi-call operation and is unaffected.

Usage:
    python apply_file_review.py --vault-path P --input-file F [--force]

F: {"file_path": str, "summary": str, "short_summary": str,
    "companies": [str, ...]}
(file_path is the File's own concept .md path, vault-absolute or
relative.)

Prints {"tags_applied": [...], "companies_unresolved": [...],
"files_log_updated": bool} normally, or {"skipped": true, "reason":
"summary_already_present", "tags_applied": [], "companies_unresolved":
[], "files_log_updated": false} when the guard refuses a redundant
write.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import uuid
from pathlib import Path

import vault_manager as vm

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

_FILE_TEMPLATE_ID = "file"
_THREAD_TEMPLATE_ID = "thread"
# The File/Thread templates' own declared caller identity for their
# machine_write sections -- REQ-SB-88-US-01-T01/T02, mirrors
# apply_thread_review.py's own _VM_CALLER precedent (REQ-SB-87-US-04-T01).
_VM_CALLER = "apply_file_review"


def _tag_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9/]+", "-", text.lower()).strip("-")
    return slug or "untitled"


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


# ── company resolution (identical contract to apply_thread_review.py's
# own copy) ───────────────────────────────────────────────────────────

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
                continue
            yield md_path, kind


def build_company_index(vault_path: Path) -> dict[str, tuple[str, str, Path]]:
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


# ── Thread's own "## Files" section update ──────────────────────────────

def _resolve_thread_path(vault_path: Path, thread_wikilink: str) -> Path | None:
    match = _WIKILINK_PATTERN.match(thread_wikilink.strip())
    stem = match.group(1) if match else thread_wikilink.strip()
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.exists():
        return None
    candidate = threads_root / stem / f"{stem}.md"
    return candidate if candidate.exists() else None


def update_files_log_line(vault_path: Path, thread_path: Path, file_stem: str, short_summary: str) -> bool:
    """Replaces (never duplicates) this file's own bare `- [[stem]]` line
    in the Thread's own "## Files" section with `- [[stem]] --
    <short_summary>`. Idempotent -- a rerun with the same short_summary
    is a no-op; a genuinely different one (re-summarized) replaces the
    line in place."""
    existing = vm.get_section_content(thread_path, "Files")
    wikilink = f"[[{file_stem}]]"
    new_entry_line = f"- {wikilink} -- {short_summary.strip()}"
    lines = [line for line in existing.splitlines() if line.strip()]
    found = False
    changed = False
    new_lines = []
    for line in lines:
        if line.strip() == wikilink or line.strip().startswith(f"- {wikilink}"):
            found = True
            if line.strip() != new_entry_line:
                changed = True
            new_lines.append(new_entry_line)
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(new_entry_line)
        changed = True
    if changed:
        thread_template = vm.load_template(vault_path, _THREAD_TEMPLATE_ID)
        thread_frontmatter, _ = vm.read_note(thread_path)
        thread_id = thread_frontmatter.get("id")
        if not thread_id:
            # A real pre-migration Thread note carries no `id` field yet
            # whenever it was never touched by apply_thread_review.py --
            # mint one now and persist it, same id-mint-if-missing pattern
            # this file's own Summary write already established at T01.
            thread_id = str(uuid.uuid4())
            vm.update(vault_path, thread_path, frontmatter={"id": thread_id})
        vm.modify_section(
            vault_path, thread_template, section="Files", content="\n".join(new_lines), mode="replace",
            note_id=thread_id, caller=_VM_CALLER,
        )
    return changed


# ── deeper follow-up pass + diagram attachment (2026-08-22, ported from
# capture-files' own add_file_detail() -- operator's own explicit choice
# to reuse the same engine for Thread attachments, not just standalone
# uploads) ────────────────────────────────────────────────────────────

def _unique_sibling_path(folder: Path, name: str) -> Path:
    candidate = folder / name
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    n = 2
    while True:
        candidate = folder / f"{stem}-{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def _attach_images(folder: Path, images: list[dict]) -> list[str]:
    """Copies each already-rendered image (e.g. a diagram slide/page render)
    into the File's own folder and returns the list of copied filenames --
    embedding is the caller's own job (the details text already carries the
    ![[...]] blocks, same convention as this script's existing wikilink-
    in-the-summary contract)."""
    copied: list[str] = []
    for item in images or []:
        source = Path(str(item.get("source_path", "")))
        if not source.is_file():
            continue
        dest = _unique_sibling_path(folder, source.name)
        shutil.copy2(str(source), str(dest))
        copied.append(dest.name)
    return copied


def add_file_detail(vault_path: Path, file_path: str, details: str, images: list[dict] | None = None) -> dict:
    """Appends a deeper follow-up pass to an already-summarized File's own
    note, under '## Details' -- never a new file, never sent anywhere.
    Repeat calls append further points. `images` are ALREADY-rendered
    diagram/slide/page images (this script only places and embeds them --
    rendering is the agent's own job, same split as everywhere else in this
    vault's Skills)."""
    details = (details or "").strip()
    if not details and not images:
        return {"error": "empty details"}

    real_file = Path(file_path)
    if not real_file.is_absolute():
        real_file = vault_path / real_file
    if not real_file.is_file():
        return {"error": f"file not found: {real_file}"}
    md_path = real_file.parent / f"{real_file.parent.name}.md"
    if not md_path.is_file():
        return {"error": f"File note not found: {md_path}"}

    attached_images = _attach_images(real_file.parent, images or [])
    image_blocks = "\n\n".join(f"![[{name}]]" for name in attached_images)
    combined = "\n\n".join(part for part in (details, image_blocks) if part)

    file_template = vm.load_template(vault_path, _FILE_TEMPLATE_ID)
    file_frontmatter, _ = vm.read_note(md_path)
    file_id = file_frontmatter.get("id")
    if not file_id:
        file_id = str(uuid.uuid4())
        vm.update(vault_path, md_path, frontmatter={"id": file_id})
    vm.modify_section(
        vault_path, file_template, section="Details", content=combined, mode="append",
        note_id=file_id, caller=_VM_CALLER,
    )

    return {
        "appended": True,
        "description_path": str(md_path),
        "attached_images": attached_images,
    }


# ── main ─────────────────────────────────────────────────────────────────

def apply_file_review(vault_path: Path, data: dict, force: bool = False) -> dict:
    file_path = Path(data["file_path"])
    if not file_path.is_absolute():
        file_path = vault_path / file_path
    summary = data["summary"]
    short_summary = data["short_summary"]
    company_names = data.get("companies") or []

    # Mechanical already-summarized guard -- a captured File's own real
    # content never changes after capture (unlike a Thread, which keeps
    # receiving new messages), so "## Summary already non-empty" is a
    # complete, sufficient freshness check here, not a partial one.
    # Refuses a redundant write instead of relying purely on the calling
    # agent's own judgment (found live, `REQ-SB-88-US-01-T04`: the real
    # cron job re-processed 4/15 already-summarized real Files despite
    # SKILL.md's documented skip rule).
    if not force and file_path.is_file() and vm.get_section_content(file_path, "Summary"):
        return {
            "skipped": True,
            "reason": "summary_already_present",
            "tags_applied": [],
            "companies_unresolved": [],
            "files_log_updated": False,
        }

    resolved, unresolved = resolve_companies(vault_path, company_names)
    tags = [f"{kind}/{slug}" for kind, slug, _ in resolved]

    file_template = vm.load_template(vault_path, _FILE_TEMPLATE_ID)
    file_frontmatter, _ = vm.read_note(file_path)
    file_id = file_frontmatter.get("id")
    if not file_id:
        # A real pre-migration File note carries no `id` field yet
        # (confirmed live) -- mint one now and persist it, same pattern
        # REQ-SB-87-US-04-T01 established for Threads. Every later run
        # against this same File reads this same id back.
        file_id = str(uuid.uuid4())
        vm.update(vault_path, file_path, frontmatter={"id": file_id})
    vm.modify_section(
        vault_path, file_template, section="Summary", content=summary, mode="replace",
        note_id=file_id, caller=_VM_CALLER,
    )
    if tags:
        vm.merge_tags(file_path, tags)

    files_log_updated = False
    frontmatter, _ = read_note(file_path)
    source_thread = frontmatter.get("source_thread") or ""
    if source_thread:
        thread_path = _resolve_thread_path(vault_path, source_thread)
        if thread_path is not None:
            files_log_updated = update_files_log_line(vault_path, thread_path, file_path.stem, short_summary)

    return {
        "tags_applied": tags,
        "companies_unresolved": unresolved,
        "files_log_updated": files_log_updated,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--append", action="store_true", help="Add a Details pass (optionally with diagram images) to an already-summarized File instead of applying an initial review.")
    parser.add_argument("--force", action="store_true", help="Bypass the already-summarized skip-guard and overwrite an existing '## Summary' anyway.")
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))
    if args.append:
        result = add_file_detail(
            vault_path,
            file_path=data.get("file_path", ""),
            details=data.get("details", ""),
            images=data.get("images") or [],
        )
    else:
        result = apply_file_review(vault_path, data, force=args.force)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
