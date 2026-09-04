"""CLI entry point: for a file referenced only by a URL in an email body
(not a real attachment), create a link-only companion note. Deliberately
dumb -- whether a link is worth capturing is the agent's own judgment
call (reading the message body), made before calling this script, never
decided in here.

Usage:
    python capture_file_link.py --vault-path P --conversation-id ID \\
        --message-path MP --received R --label LABEL --url URL

Prints {"companion_path": str} or {"reason": str} to stdout.

2026-09-02 (REQ-SB-87-US-02-T03): Thread resolution now goes through
`vault_manager.find_by_id`, and the "## Files" accumulation now goes
through `vault_manager.get_section_content`/`vault_manager.modify_section(
..., caller="capture_file_link")` -- mirrors `capture_attachments.py`'s
own identical migration (see that file's own docstring for the full
frontmatter-fence-vs-raw-attachment-bytes non-reproduction reasoning,
which applies here unchanged since this script never globs over
`files/**/*.md` either). `write_file_link_companion` (the real companion
note write) stays entirely hand-written, unchanged.
"""
from __future__ import annotations

import argparse
import os
import json
from pathlib import Path

import vault_lib
import vault_manager

_CALLER = "capture_file_link"


def capture_file_link(vault_path: Path, conversation_id: str, message_path: str, received: str, label: str, url: str) -> dict:
    thread_template = vault_manager.load_template(vault_path, "thread")
    concept_path = vault_manager.find_by_id(vault_path, conversation_id, note_name="Threads")
    if concept_path is None:
        return {"reason": "no Thread found for this conversation_id"}
    directory = concept_path.parent

    thread_link = f"[[{directory.name}]]"
    email_link = f"[[{Path(message_path).stem}]]"
    file_slug = f"{received[:10]} {label}"

    result = vault_lib.write_file_link_companion(
        subfolder=directory, file_slug=file_slug, url=url,
        source_thread=thread_link, source_email=email_link,
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
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault-path",
        # Defaults to what Second Brain's setup wizard writes into Hermes'
        # own .env, so a Skill never has to name a machine-specific
        # absolute path and a bundle never has to have one rewritten on
        # import. Pass it only to override.
        default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""),
    )
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--message-path", required=True)
    parser.add_argument("--received", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        # An empty value would become Path("") -> the CWD, which is exactly the
        # silent-wrong-folder failure this whole change exists to remove.
        raise SystemExit(
            "No vault path. Set SECOND_BRAIN_VAULT_PATH in Hermes' own .env "
            "(Second Brain's setup wizard writes it) or pass --vault-path."
        )

    result = capture_file_link(
        Path(args.vault_path), args.conversation_id, args.message_path, args.received, args.label, args.url,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
