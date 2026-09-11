"""Picks the next batch of Threads to enrich, and nothing else.

Enrichment is the expensive half of the system -- one model read per thread --
so WHICH threads a run touches is a decision worth making in code, once, rather
than leaving to an agent's judgment on every run. This script decides; the Skill
reads what it is handed.

A thread is due when either is true:

  - it has never been enriched (`last_summarized_at` empty), or
  - it has GROWN since it was: today's message count differs from the
    `summarized_message_count` stamped at enrichment.

The count, not just the timestamp, is what makes this safe to run DURING a
history backfill -- which is the whole reason it exists. The inherited rule
`last_summarized_at >= last_message_at` only notices a thread that grew at the
newest end. A backfill walks history BACKWARDS and appends to the oldest end of
conversations that already exist, without touching `last_message_at`: a thread
whose earlier half arrives tomorrow would stay marked fresh against a summary
that never read it. Comparing counts catches growth at either end.

So enrichment does not have to wait for capture to finish. It costs one re-read
of each thread that later grows, and buys starting weeks earlier.

    python select_threads.py [--vault-path P] [--limit 50] [--newest-first]
                             [--include-noise]

Prints JSON: {"due": N, "selected": [{"thread_id", "thread_dir", "name", "messages",
"last_message_at", "reason"}], "total_threads": N}.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import vault_manager as vm

# A thread capture judged to be noise carries this; enriching it spends a model
# call to summarize a newsletter. Skipped by default, never deleted -- the
# classification is capture's opinion, and --include-noise exists for when it
# turns out to be wrong.
_NOISE_TAG = "kind/noise"


def _thread_notes(vault_path: Path):
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.is_dir():
        return
    for thread_dir in sorted(p for p in threads_root.iterdir() if p.is_dir()):
        note = thread_dir / f"{thread_dir.name}.md"
        if note.is_file():
            yield thread_dir, note


def select(vault_path: Path, *, limit: int = 50, newest_first: bool = False,
           include_noise: bool = False) -> dict:
    due: list[dict] = []
    total = 0
    for thread_dir, note in _thread_notes(vault_path):
        total += 1
        frontmatter, _ = vm.read_note(note)
        if frontmatter.get("type") != "Thread":
            continue
        if not include_noise and _NOISE_TAG in (frontmatter.get("tags") or []):
            continue

        messages = len(list((thread_dir / "messages").glob("*.md")))
        if not messages:
            continue                      # nothing to read yet

        summarized_at = (frontmatter.get("last_summarized_at") or "").strip()
        stamped = (frontmatter.get("summarized_message_count") or "").strip()
        if not summarized_at:
            reason = "never enriched"
        elif stamped != str(messages):
            reason = f"grew: {stamped or '?'} -> {messages} messages"
        else:
            continue

        due.append({
            # How an agent names this Thread -- never by a path it types.
            "thread_id": frontmatter.get("id") or "",
            "thread_dir": str(thread_dir),
            "name": frontmatter.get("thread_name") or thread_dir.name,
            "messages": messages,
            "last_message_at": frontmatter.get("last_message_at") or "",
            "reason": reason,
        })

    # Oldest first by default: the operator's own instinct, and it means a run
    # interrupted halfway leaves a contiguous enriched span rather than holes.
    due.sort(key=lambda t: t["last_message_at"], reverse=newest_first)
    return {"total_threads": total, "due": len(due),
            "selected": due[:limit] if limit > 0 else due}


def main() -> int:
    parser = argparse.ArgumentParser(description="Pick the next Threads to enrich.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--limit", type=int, default=50,
                        help="Maximum threads to return. 0 for all -- reporting only, "
                             "since a run that reads them all is unbounded in cost.")
    parser.add_argument("--newest-first", action="store_true",
                        help="Most recent threads first, instead of oldest first.")
    parser.add_argument("--include-noise", action="store_true",
                        help="Also select threads capture classified as noise.")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    # A Thread name can carry any character a subject line did -- a zero-width
    # space among them -- and a piped stdout on Windows defaults to cp1252,
    # which cannot encode it: the whole batch failed on one name.
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(select(Path(args.vault_path), limit=args.limit,
                            newest_first=args.newest_first,
                            include_noise=args.include_noise), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
