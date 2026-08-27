"""Generic attachment/Files-companion primitives -- saving raw bytes
alongside a note, and a Files/OKF-lite companion note (frontmatter +
`## Summary` + `## Personal Notes`) for a real file or a URL-only
reference. Parameterized by (vault_path, subfolder, ...) throughout --
no note-kind knowledge baked in."""
from __future__ import annotations

from pathlib import Path

from app.obsidian.frontmatter import write_frontmatter_note
from app.obsidian.notes import slugify


def write_attachments(
    vault_path: Path, subfolder: str, note_stem: str, message_segment: str, attachments: list[dict]
) -> list[dict]:
    """Saves each attachment next to its note, Obsidian-convention
    style: <subfolder>/attachments/<note_stem>/<slug-of-message_segment>/
    <filename> -- nested one level deeper per message so two different
    messages sharing one note can never silently overwrite same-named
    attachments. Returns one entry per attachment with a vault-relative
    link (relative to the note's own location) for embedding in the
    note body -- oversized attachments (content already None) are
    recorded but not written, never silently dropped."""
    results: list[dict] = []
    if not attachments:
        return results

    note_slug = slugify(note_stem)
    message_slug = slugify(message_segment)
    attachments_dir = Path(vault_path) / subfolder / "attachments" / note_slug / message_slug

    for attachment in attachments:
        filename = attachment["filename"]
        if attachment["content"] is None:
            results.append({"filename": filename, "size": attachment["size"], "saved": False})
            continue
        attachments_dir.mkdir(parents=True, exist_ok=True)
        file_path = attachments_dir / filename
        file_path.write_bytes(attachment["content"])
        relative_link = f"attachments/{note_slug}/{message_slug}/{filename}"
        results.append({
            "filename": filename,
            "size": attachment["size"],
            "saved": True,
            "relative_link": relative_link,
        })

    return results


def staged_attachment_files(vault_path: Path, subfolder: str, message_scope_id: str, message_id: str) -> list:
    """Lists every real attachment file write_attachments's own
    convention durably persisted for one message. Returns [] if no
    attachments were ever saved for this message."""
    directory = (
        Path(vault_path) / subfolder / "attachments"
        / slugify(message_scope_id) / slugify(message_id)
    )
    if not directory.exists():
        return []
    return sorted(path for path in directory.iterdir() if path.is_file())


def write_file_companion(
    vault_path: Path,
    subfolder: str,
    file_slug: str,
    original_filename: str,
    content: bytes,
    summary: str,
    source_thread: str | None = None,
    source_email: str | None = None,
) -> dict:
    """Generic Files/OKF-companion primitive -- <subfolder>/files/
    <slug-of-file_slug>/<original_filename> (raw bytes, untouched)
    beside <subfolder>/files/<slug-of-file_slug>/<slug-of-file_slug>.md
    (an OKF-lite companion note: frontmatter + `## Summary` + `##
    Personal Notes`). `subfolder` accepts either a vault-relative string
    or an already vault-absolute path -- pathlib's own Path.joinpath
    semantics make `vault_path / subfolder` resolve correctly either
    way."""
    slug = slugify(file_slug)
    files_dir = Path(vault_path) / subfolder / "files" / slug
    files_dir.mkdir(parents=True, exist_ok=True)
    file_path = files_dir / original_filename
    file_path.write_bytes(content)
    companion_path = files_dir / f"{slug}.md"
    frontmatter = {
        "type": "File",
        "file_slug": file_slug,
        "original_filename": original_filename,
    }
    if source_thread is not None:
        frontmatter["source_thread"] = source_thread
    if source_email is not None:
        frontmatter["source_email"] = source_email
    write_frontmatter_note(
        companion_path,
        frontmatter,
        f"## Summary\n\n{summary}\n\n## Personal Notes\n",
    )
    return {
        "file_path": str(file_path),
        "companion_path": str(companion_path),
    }


def write_file_link_companion(
    vault_path: Path,
    subfolder: str,
    file_slug: str,
    url: str,
    source_thread: str | None = None,
    source_email: str | None = None,
) -> dict:
    """Sibling to write_file_companion -- for a file referenced ONLY by
    URL (e.g. a SharePoint/OneDrive "shared with you" link), never a
    real attachment's bytes. Writes JUST the companion note -- no
    sibling raw-bytes file, since there are no bytes to save."""
    slug = slugify(file_slug)
    files_dir = Path(vault_path) / subfolder / "files" / slug
    files_dir.mkdir(parents=True, exist_ok=True)
    companion_path = files_dir / f"{slug}.md"
    frontmatter = {
        "type": "File",
        "file_slug": file_slug,
        "url": url,
    }
    if source_thread is not None:
        frontmatter["source_thread"] = source_thread
    if source_email is not None:
        frontmatter["source_email"] = source_email
    write_frontmatter_note(
        companion_path,
        frontmatter,
        f"[{url}]({url})\n\n## Summary\n\n\n\n## Personal Notes\n",
    )
    return {"companion_path": str(companion_path)}
