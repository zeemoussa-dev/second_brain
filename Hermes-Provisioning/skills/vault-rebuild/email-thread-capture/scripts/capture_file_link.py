"""CLI entry point: for a file referenced only by a URL in an email body
(not a real attachment), create a link-only companion note. Deliberately
dumb -- whether a link is worth capturing is the agent's own judgment
call (reading the message body), made before calling this script, never
decided in here.

Usage:
    python capture_file_link.py --vault-path P --conversation-id ID \\
        --message-path MP --received R --label LABEL --url URL

Prints {"companion_path": str} or {"reason": str} to stdout.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import vault_lib

_CALLER = "capture_file_link.capture_file_link"


def capture_file_link(vault_path: Path, conversation_id: str, message_path: str, received: str, label: str, url: str) -> dict:
    directory = vault_lib.resolve_thread_directory(vault_path, conversation_id)
    if directory is None:
        return {"reason": "no Thread found for this conversation_id"}

    thread_link = f"[[{directory.name}]]"
    email_link = f"[[{Path(message_path).stem}]]"
    file_slug = f"{received[:10]} {label}"

    result = vault_lib.write_file_link_companion(
        subfolder=directory, file_slug=file_slug, url=url,
        source_thread=thread_link, source_email=email_link,
    )
    companion_stem = Path(result["companion_path"]).stem
    vault_lib.link_file_to_thread(directory, f"[[{companion_stem}]]", caller=_CALLER)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--message-path", required=True)
    parser.add_argument("--received", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    result = capture_file_link(
        Path(args.vault_path), args.conversation_id, args.message_path, args.received, args.label, args.url,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
