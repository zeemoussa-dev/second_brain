"""Generic 4-file directory note kind: index.md/<slug>.md/log.md/
captures.md inside a <directory_root>/<slug-of-slug>/ directory
("OKF" -- concept file plus an auto-generated index, a growing log, and
an append-only captures file). Parameterized entirely by directory_root/
slug/frontmatter -- zero knowledge of what kind of thing (Customer,
Project, ...) is being created; that's a business-layer concern."""
from __future__ import annotations

import json
from pathlib import Path

from app.obsidian.frontmatter import insert_frontmatter_key_if_missing, write_frontmatter_note
from app.obsidian.notes import slugify


def format_okf_provenance(by: str, at: str) -> str:
    """JSON-encodes an OKF actor-provenance value (`generated`/
    `verified`) as a string under the field's own literal name. `by`/
    `at` are stored verbatim; populating them with a real agent id/ISO
    timestamp is a business-layer concern, not this primitive's job."""
    return json.dumps({"by": by, "at": at})


def okf_directory_paths(directory_root: Path, slug: str) -> dict:
    """Resolves the deterministic path set for one OKF-conformant
    directory rooted at directory_root: index.md/<slug>.md/log.md/
    captures.md, all inside a <directory_root>/<slug-of-slug>/
    directory -- without checking whether any of them exist yet."""
    concept_slug = slugify(slug)
    base = Path(directory_root) / concept_slug
    return {
        "directory": base,
        "index": base / "index.md",
        "concept": base / f"{concept_slug}.md",
        "log": base / "log.md",
        "captures": base / "captures.md",
    }


def okf_concept_file_exists(directory_root: Path, slug: str) -> bool:
    return okf_directory_paths(directory_root, slug)["concept"].exists()


def move_okf_directory(source_directory: Path, target_parent_directory: Path) -> Path:
    """Generic, cross-parent OKF-directory archival-move primitive.
    Only the directory's LOCATION moves -- every file inside is moved
    byte-for-byte, untouched, in one atomic Path.rename(). Raises
    FileExistsError on a genuine collision at the target, never silently
    overwrites. Returns the new directory path."""
    target_parent_directory = Path(target_parent_directory)
    target_parent_directory.mkdir(parents=True, exist_ok=True)
    target_directory = target_parent_directory / Path(source_directory).name
    if target_directory.exists():
        raise FileExistsError(
            f"would overwrite existing directory at {target_directory}"
        )
    Path(source_directory).rename(target_directory)
    return target_directory


def _write_or_backfill_identifying_header(path: Path, identifying_name: str) -> None:
    """Writes/backfills the bare `# {name}` HALF of index.md's own header
    convention onto log.md/captures.md. Fresh creation (path does not
    exist yet): writes the header as the file's full content. Backfill
    (path already exists): a file is "headerless" iff its current first
    line does not start with "# " -- the header is prepended, every
    existing byte preserved, never reordered/duplicated. An already-
    headered file is left completely untouched -- idempotent on a repeat
    ensure_* run."""
    path = Path(path)
    header = f"# {identifying_name}\n\n"
    if not path.exists():
        path.write_text(header, encoding="utf-8")
        return
    text = path.read_text(encoding="utf-8")
    first_line = text.split("\n", 1)[0]
    if first_line.startswith("# "):
        return
    path.write_text(header + text, encoding="utf-8")


def create_okf_directory_baseline(
    directory_root: Path, slug: str, concept_frontmatter: dict, identifying_name: str,
    index_listing_body: str = "",
) -> dict:
    """Creates an OKF-conformant directory the first time: index.md
    (whole-file, auto-generated listing -- never header-scoped, never
    preserved on top-up), <slug>.md (the OKF concept file, with a body
    of exactly the two OKF-required empty sections ## Glimpse and ##
    Background), and log.md/captures.md each gaining/keeping their own
    identifying `# {identifying_name}` header. Always writes index.md/
    <slug>.md unconditionally -- callers must check
    okf_concept_file_exists() first. Returns the same path set
    okf_directory_paths() resolves, each value stringified."""
    paths = okf_directory_paths(directory_root, slug)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    paths["index"].write_text(index_listing_body, encoding="utf-8")
    write_frontmatter_note(paths["concept"], concept_frontmatter, "## Glimpse\n\n## Background\n")
    _write_or_backfill_identifying_header(paths["log"], identifying_name)
    _write_or_backfill_identifying_header(paths["captures"], identifying_name)
    return {key: str(value) for key, value in paths.items()}


def ensure_okf_directory_baseline(
    directory_root: Path, slug: str, concept_frontmatter_defaults: dict, identifying_name: str,
    index_listing_body: str = "",
) -> list[str]:
    """Tops up an already-existing OKF directory: surgically inserts any
    missing concept_frontmatter_defaults key into <slug>.md (never
    touches an already-present key or the body), creates log.md/
    captures.md with their own identifying header if missing, or
    backfills that header onto an already-existing headerless one
    without disturbing any already-appended real content, and
    unconditionally rewrites index.md. Returns the list of concept
    frontmatter keys actually inserted (empty if the concept file
    already had all of them)."""
    paths = okf_directory_paths(directory_root, slug)
    inserted: list[str] = []
    for key, value in concept_frontmatter_defaults.items():
        if insert_frontmatter_key_if_missing(paths["concept"], key, value):
            inserted.append(key)
    _write_or_backfill_identifying_header(paths["log"], identifying_name)
    _write_or_backfill_identifying_header(paths["captures"], identifying_name)
    paths["index"].write_text(index_listing_body, encoding="utf-8")
    return inserted
