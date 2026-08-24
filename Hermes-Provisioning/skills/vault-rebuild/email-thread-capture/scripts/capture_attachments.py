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
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import vault_lib

_CALLER = "capture_attachments.capture_attachments"


def capture_attachments(vault_path: Path, data: dict) -> dict:
    conversation_id = data["conversation_id"]
    message_id = data["message_id"]
    received = data["received"]
    message_path = data["message_path"]
    attachments = data.get("attachments") or []

    directory = vault_lib.resolve_thread_directory(vault_path, conversation_id)
    if directory is None:
        return {"captured": [], "skipped": [], "reason": "no Thread found for this conversation_id"}

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
        vault_lib.link_file_to_thread(directory, f"[[{companion_stem}]]", caller=_CALLER)
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
