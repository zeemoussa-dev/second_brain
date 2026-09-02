"""CLI entry point: save real attachment bytes into the Thread's own
files/ folder with a bare companion note (empty ## Summary -- Capture
phase never summarizes). Reads attachment content from the temp_path
list_recent_emails.py already saved it at, and deletes that temp file
once written into the vault.

Usage:
    python capture_attachments.py --vault-path P --input-file F

F is a JSON file:
{
  "conversation_id": str, "message_id": str, "received": str,
  "message_path": str,   // ingest_email's own returned message_path
  "attachments": [{"filename": str, "temp_path": str|null, "size": int}, ...]
}

Prints {"captured": [...], "skipped": [...]} to stdout -- both lists of
filenames. An attachment with temp_path null (oversized, per
outlook_lib.py's own size cap) is skipped, never written.

2026-09-02 (REQ-SB-87-US-02-T03): Thread resolution now goes through
`vault_manager.find_by_id`, and the "## Files" accumulation now goes
through `vault_manager.get_section_content`/`vault_manager.modify_section(
..., caller="capture_attachments")` instead of `vault_lib.
insert_body_section_if_missing`/`read_body_section`/`replace_body_section`
(via the old `link_file_to_thread` helper) -- the Thread template's own
"## Files" `allowed_callers` declaration (`REQ-SB-87-US-01-T05`) now
enforces this section's per-caller restriction. `write_file_companion`
(the real byte-level attachment write) stays entirely hand-written,
unchanged -- it never touches the Thread's own concept note, so the
frontmatter-fence-vs-raw-attachment-bytes regression `REQ-SB-87-US-02-T02`
found in `rename_thread.py`'s own companion-backlink glob loop does not
reproduce here: this script never globs over `files/**/*.md`, it only
ever writes the Thread's own single concept note (resolved by `id`) and
the two files `write_file_companion` itself explicitly names.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import vault_lib
import vault_manager

_CALLER = "capture_attachments"


def capture_attachments(vault_path: Path, data: dict) -> dict:
    conversation_id = data["conversation_id"]
    message_id = data["message_id"]
    received = data["received"]
    message_path = data["message_path"]
    attachments = data.get("attachments") or []

    thread_template = vault_manager.load_template(vault_path, "thread")
    concept_path = vault_manager.find_by_id(vault_path, conversation_id, note_name="Threads")
    if concept_path is None:
        return {"captured": [], "skipped": [], "reason": "no Thread found for this conversation_id"}
    directory = concept_path.parent

    thread_link = f"[[{directory.name}]]"
    email_link = f"[[{Path(message_path).stem}]]"
    captured: list[str] = []
    skipped: list[str] = []

    for attachment in attachments:
        filename = attachment["filename"]
        temp_path = attachment.get("temp_path")
        if temp_path is None:
            skipped.append(filename)
            continue
        content = Path(temp_path).read_bytes()
        message_hash = hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:8]
        file_slug = f"{received[:10]} {message_hash}-{filename}"
        result = vault_lib.write_file_companion(
            vault_path,
            subfolder=directory,
            file_slug=file_slug,
            original_filename=filename,
            content=content,
            summary="",
            source_thread=thread_link,
            source_email=email_link,
        )
        companion_stem = Path(result["companion_path"]).stem
        wikilink = f"[[{companion_stem}]]"
        existing = vault_manager.get_section_content(concept_path, "Files")
        if wikilink not in existing:
            lines = [line for line in existing.splitlines() if line.strip()]
            lines.append(f"- {wikilink}")
            vault_manager.modify_section(
                vault_path, thread_template, section="Files", content="\n".join(lines), mode="replace",
                note_id=conversation_id, note_name="Threads", caller=_CALLER,
            )
        captured.append(filename)
        os.remove(temp_path)

    return {"captured": captured, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    # utf-8-sig: see ingest_email.py's own identical comment.
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))
    result = capture_attachments(vault_path, data)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
