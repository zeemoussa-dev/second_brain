"""CLI entry point: the plain mechanical eligibility check for the Meeting
Preparation Agent's one-time Person-note web lookup (REQ-SB-82-US-05-T01,
ADR-010 Decision 3). Reads an EXISTING Person note's own body (everything
after its closing `---` frontmatter fence, mirroring
`app/data_access/vault_writer.py::read_note`'s own frontmatter-fence-split
convention) and reports whether it is empty/whitespace-only.

This IS the one-time gate -- no separate "already looked up" tracking
field or file exists anywhere (ADR-010): once ANY real content lands in
the body (written by this agent's own `append_person_findings.py`, or by
the user directly), this check honestly reports `empty: false` forever
after, regardless of who added that content.

Purely mechanical and read-only -- performs no web lookup itself; that is
the calling agent's own real `web_search` tool call, per ADR-010's
"neither script performs the web lookup itself" constraint.

Usage:
    python check_person_note_empty.py --note-path P

Prints {"empty": true|false} or {"error": str}.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def check_person_note_empty(note_path: Path) -> dict:
    if not note_path.exists():
        return {"error": f"note does not exist: {note_path}"}

    text = note_path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        fence_end = text.find("\n---\n", 4)
        body = text[fence_end + 5:] if fence_end != -1 else text
    else:
        # No parseable frontmatter fence -- treat the whole file as body
        # content rather than guessing at a malformed shape (should not
        # happen for a real Person note, which is always created with
        # baseline frontmatter -- REQ-SB-10).
        body = text

    return {"empty": not body.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--note-path", required=True)
    args = parser.parse_args()

    result = check_person_note_empty(Path(args.note_path))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
