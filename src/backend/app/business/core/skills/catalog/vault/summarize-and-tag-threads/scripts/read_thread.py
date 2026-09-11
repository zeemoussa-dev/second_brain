"""Reads one Thread as a plain-text transcript, for summarization.

Why this exists rather than reading the message notes directly: capture stores
each message body exactly as it arrived, which for Outlook mail means HTML --
and measured on this vault, **83% of every stored body is tags and entities**
(3.9 M raw chars reducing to 0.66 M of text across 151 messages). An agent
reading the notes raw pays for all of it and learns nothing from any of it.

Stripping happens HERE, at read, deliberately -- not at capture. An email's real
body IS the HTML, and capture's job is to preserve the evidence faithfully; if a
summary ever looks wrong you want the original to check it against. Converting
on the way out costs nothing next to the model call it feeds.

    python read_thread.py --thread-dir "<vault>/Work/Threads/<Name>"
    python read_thread.py --thread-dir ... --max-chars 40000

Prints a transcript: the Thread's own frontmatter facts, then each message in
time order with its direction, sender and text.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path

# Everything inside these is markup or code, never content the reader wants --
# dropped whole, before tags are stripped, so their bodies do not survive as
# loose text (a <style> block otherwise flattens into a wall of CSS).
_DROP_WHOLE = re.compile(
    r"<(script|style|head|title)\b[^>]*>.*?</\1>", re.I | re.S)
# Block-level boundaries become newlines rather than vanishing, so paragraphs
# and list items do not run together into one unreadable line.
_BLOCK_BREAK = re.compile(
    r"</?(p|div|br|tr|li|h[1-6]|table|blockquote)\b[^>]*>", re.I)
_ANY_TAG = re.compile(r"<[^>]+>")
_MANY_BLANKS = re.compile(r"\n{3,}")
_TRAILING_SPACE = re.compile(r"[ \t]+\n")


def html_to_text(raw: str) -> str:
    """HTML email body -> readable text, preserving line structure."""
    if not raw:
        return ""
    if "<" not in raw:                      # already plain
        return raw.strip()
    text = _DROP_WHOLE.sub(" ", raw)
    text = _BLOCK_BREAK.sub("\n", text)
    text = _ANY_TAG.sub("", text)
    text = html.unescape(text)
    # NBSP and the narrow no-break space real signatures use; left as literal
    # characters they read as ordinary spaces but tokenize as their own thing.
    text = text.replace(" ", " ").replace(" ", " ")
    text = _TRAILING_SPACE.sub("\n", text)
    text = _MANY_BLANKS.sub("\n\n", text)
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def _split_note(path: Path) -> tuple[dict, str]:
    """Frontmatter dict + body. Deliberately tolerant: a note that does not
    parse still yields its body, because a summary from a slightly-degraded
    note beats skipping a real conversation."""
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter: dict = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" not in line:
                    continue
                key, _, value = line.partition(":")
                frontmatter[key.strip()] = value.strip().strip('"')
            body = text[end + 4:]
    return frontmatter, body


def read_thread(thread_dir: Path, *, max_chars: int = 0) -> str:
    thread_note = thread_dir / f"{thread_dir.name}.md"
    if not thread_note.is_file():
        raise SystemExit(f"no Thread note at {thread_note}")
    frontmatter, _ = _split_note(thread_note)

    lines = [
        f"THREAD: {thread_dir.name}",
        f"classification: {frontmatter.get('classification') or '-'}",
        f"last_message_at: {frontmatter.get('last_message_at') or '-'}",
        "",
    ]

    messages = []
    for note in (thread_dir / "messages").glob("*.md"):
        message_frontmatter, body = _split_note(note)
        messages.append((message_frontmatter.get("received") or "", message_frontmatter, body))
    messages.sort(key=lambda item: item[0])

    for received, message_frontmatter, body in messages:
        direction = (message_frontmatter.get("direction") or "").strip()
        arrow = "SENT" if direction == "sent" else "RECEIVED"
        lines.append(f"--- {received[:16]} | {arrow} | "
                     f"{message_frontmatter.get('sender') or '?'} "
                     f"<{message_frontmatter.get('sender_email') or '?'}>")
        subject = message_frontmatter.get("subject") or ""
        if subject:
            lines.append(f"Subject: {subject}")
        lines.append("")
        lines.append(html_to_text(body))
        lines.append("")

    transcript = "\n".join(lines).strip()
    # Truncating is a last resort and says so in the output -- a silently
    # truncated thread would be summarized as though it were complete.
    if max_chars and len(transcript) > max_chars:
        transcript = (transcript[:max_chars]
                      + f"\n\n[TRUNCATED at {max_chars} chars -- this Thread is longer; "
                        "say so in the summary rather than implying it is complete]")
    return transcript


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread-dir", required=True)
    parser.add_argument("--max-chars", type=int, default=0,
                        help="truncate the transcript (0 = no limit, the default)")
    parser.add_argument("--stats", action="store_true",
                        help="report the reduction instead of printing the transcript")
    args = parser.parse_args()

    thread_dir = Path(args.thread_dir)
    transcript = read_thread(thread_dir, max_chars=args.max_chars)

    if args.stats:
        raw = sum(len(p.read_text(encoding="utf-8", errors="replace"))
                  for p in (thread_dir / "messages").glob("*.md"))
        print(json.dumps({
            "thread": thread_dir.name,
            "raw_chars": raw,
            "transcript_chars": len(transcript),
            "reduction_pct": round((1 - len(transcript) / max(1, raw)) * 100, 1),
        }, ensure_ascii=False))
        return 0

    sys.stdout.reconfigure(encoding="utf-8")
    print(transcript)
    return 0


if __name__ == "__main__":
    sys.exit(main())
