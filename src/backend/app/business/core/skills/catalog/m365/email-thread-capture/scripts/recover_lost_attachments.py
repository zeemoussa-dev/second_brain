"""Re-fetches the attachments capture lost to Windows' MAX_PATH.

What was lost: capture created each attachment's folder, then failed writing
the file inside it once the full path passed 260 characters -- leaving EMPTY
folders, no file and no note, with no error surfaced anywhere (2026-09-11:
256 of them). `vault_lib.write_file_companion` now writes through `long_path`,
so a re-fetch lands. The bytes were never on disk, so there is nothing local
to recover them from: they come back from Microsoft Graph.

How a folder is traced to its message: it is named
`<date> <sha256(message_id)[:8]>-<filename>`, and every message note carries
its `message_id` -- so each of the Thread's messages is hashed and matched. A
folder whose hash matches none is reported, never guessed.

Safe to re-run, and safe to re-fetch a whole message: capture now skips an
attachment file already on disk and never resets a note that exists, so the
message's attachments that DID land are left exactly as they are -- summaries
included.

    python recover_lost_attachments.py [--vault-path P] [--dry-run] [--limit N]

--dry-run traces folders to messages and stops before any network call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
from pathlib import Path

import vault_manager as vm


def _scan(path: Path) -> list[os.DirEntry]:
    with os.scandir(vm.long_path(path)) as entries:
        return list(entries)


def _message_hash(message_id: str) -> str:
    return hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:8]


def _has_note(folder: Path) -> bool:
    return any(e.is_file() and e.name.lower().endswith(".md") for e in _scan(folder))


def plan(vault_path: Path) -> dict:
    """Every attachment folder with no note, grouped by the message it belongs to."""
    threads_root = vault_path / "Work" / "Threads"
    groups: dict[tuple[str, str], dict] = {}
    unmapped: list[str] = []
    empty = 0
    if not os.path.isdir(vm.long_path(threads_root)):
        return {"empty_folders": 0, "messages": [], "unmapped": []}

    for thread in sorted((e for e in _scan(threads_root) if e.is_dir()), key=lambda e: e.name):
        thread_dir = threads_root / thread.name
        files_dir = thread_dir / "files"
        if not os.path.isdir(vm.long_path(files_dir)):
            continue
        lost = [f.name for f in _scan(files_dir) if f.is_dir() and not _has_note(files_dir / f.name)]
        if not lost:
            continue
        empty += len(lost)

        by_hash: dict[str, tuple[Path, dict]] = {}
        messages_dir = thread_dir / "messages"
        if os.path.isdir(vm.long_path(messages_dir)):
            for entry in _scan(messages_dir):
                if not (entry.is_file() and entry.name.lower().endswith(".md")):
                    continue
                note = messages_dir / entry.name
                frontmatter, _ = vm.read_note(note)
                message_id = (frontmatter.get("message_id") or "").strip()
                if message_id:
                    by_hash[_message_hash(message_id)] = (note, frontmatter)

        for folder in lost:
            _, _, rest = folder.partition(" ")
            hit = by_hash.get(rest[:8])
            if hit is None:
                unmapped.append(f"{thread.name}/files/{folder}")
                continue
            note, frontmatter = hit
            group = groups.setdefault((thread.name, frontmatter["message_id"]), {
                "thread": thread.name,
                "message_id": frontmatter["message_id"],
                "message_path": str(note),
                "conversation_id": frontmatter.get("conversation_id") or "",
                "received": frontmatter.get("received") or "",
                "lost_folders": [],
            })
            group["lost_folders"].append(folder)

    return {"empty_folders": empty, "messages": list(groups.values()), "unmapped": unmapped}


def _fetch_attachments(graph_lib, mailbox: str, token: str, message_id: str) -> list[dict]:
    base = (f"{graph_lib._GRAPH}/users/{urllib.parse.quote(mailbox)}/messages/"
            f"{urllib.parse.quote(message_id)}/attachments")
    listing = graph_lib._get(base, token)
    return graph_lib._attachment_records(
        listing.get("value") or [],
        fetch=lambda a: (graph_lib._get_bytes(f"{base}/{urllib.parse.quote(a['id'])}/$value", token)
                         if a.get("id") else None),
    )


def recover(vault_path: Path, *, dry_run: bool = False, limit: int = 0) -> dict:
    traced = plan(vault_path)
    report = {
        "status": "dry-run" if dry_run else "complete",
        "empty_folders": traced["empty_folders"],
        "messages_to_refetch": len(traced["messages"]),
        "unmapped": len(traced["unmapped"]),
        "unmapped_sample": traced["unmapped"][:5],
    }
    if dry_run:
        return report

    import capture_attachments as capture
    import graph_lib

    mailbox = (os.environ.get("SECOND_BRAIN_SELF_EMAIL") or "").strip()
    if not mailbox:
        raise SystemExit("SECOND_BRAIN_SELF_EMAIL is not set -- Graph reads a named mailbox.")
    # ONE token for the run. Each redemption rotates the stored refresh token,
    # and there is no reason to rotate it once per message.
    token = graph_lib._access_token()

    recovered = still_missing = 0
    errors: list[str] = []
    batch = traced["messages"][:limit] if limit > 0 else traced["messages"]
    for group in batch:
        try:
            records = _fetch_attachments(graph_lib, mailbox, token, group["message_id"])
            capture.capture_attachments(vault_path, {
                "conversation_id": group["conversation_id"],
                "message_id": group["message_id"],
                "received": group["received"],
                "message_path": group["message_path"],
                "attachments": records,
            })
        except Exception as exc:
            errors.append(f"{group['thread']}: {type(exc).__name__}: {str(exc)[:160]}")
        files_dir = vault_path / "Work" / "Threads" / group["thread"] / "files"
        for folder in group["lost_folders"]:
            if _has_note(files_dir / folder):
                recovered += 1
            else:
                still_missing += 1

    report.update({
        "messages_refetched": len(batch),
        "recovered": recovered,
        # Over capture's size cap, or gone from the mailbox (a moved message can
        # change its Graph id). Reported so it is a known gap, not a silent one.
        "still_missing": still_missing,
        "errors": errors[:10],
        "errors_total": len(errors),
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-fetch attachments lost to MAX_PATH.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Messages to re-fetch. 0 = all.")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    print(json.dumps(recover(Path(args.vault_path), dry_run=args.dry_run, limit=args.limit),
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
