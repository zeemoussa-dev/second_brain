"""CLI entry point: the plain mechanical write half of the Meeting
Preparation Agent's one-time Person-note web lookup (REQ-SB-82-US-05-T01,
ADR-010 Decision 3). Appends real findings text -- already gathered by the
calling agent's own real `web_search` tool call, never by this script --
into an ALREADY-EXISTING Person note's own body.

Mirrors `app/business/cockpit/notes.py::add_person_note`'s established
append-only-to-an-existing-note shape (ADR-010's own named precedent):
this script never creates a new note (errors honestly if the given path
doesn't exist -- Person notes are created elsewhere, REQ-SB-10) and never
overwrites or removes any existing body content -- append only, whatever
was already there (whether written by a prior agent run or by the user
directly) is preserved byte-for-byte, findings are added after it.

Performs no web lookup itself -- purely mechanical (check via
check_person_note_empty.py, look up via the calling agent's own
`web_search`, then append what was actually found). Never called by the
calling agent's own documented flow (see this Skill's SKILL.md) when
nothing real was found -- this script itself does not verify that; it
trusts the caller not to invoke it with fabricated content, the same
honesty contract `research-kb-writer`'s own SKILL.md already establishes.

Usage:
    python append_person_findings.py --note-path P --input-file F

F: {"findings": str}

Prints {"appended": true} or {"error": str}.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def append_person_findings(note_path: Path, findings: str) -> dict:
    findings = (findings or "").strip()
    if not findings:
        return {"error": "findings is required"}
    if not note_path.exists():
        return {"error": f"note does not exist: {note_path}"}

    text = note_path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        fence_end = text.find("\n---\n", 4)
        if fence_end != -1:
            frontmatter_block = text[: fence_end + 5]
            body = text[fence_end + 5:]
        else:
            frontmatter_block = ""
            body = text
    else:
        # No parseable frontmatter fence -- treat the whole file as body
        # content rather than guessing at a malformed shape (should not
        # happen for a real Person note -- REQ-SB-10).
        frontmatter_block = ""
        body = text

    existing_body = body.strip()
    if existing_body:
        # Defensive: the calling agent's own documented flow only reaches
        # this script after check_person_note_empty.py reported empty, but
        # this script's own append-only contract must hold regardless --
        # existing real content (agent- or user-written) is preserved
        # verbatim, never truncated or overwritten.
        new_body = "\n" + existing_body + "\n\n" + findings + "\n"
    else:
        new_body = "\n" + findings + "\n"

    note_path.write_text(frontmatter_block + new_body, encoding="utf-8")
    return {"appended": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--note-path", required=True)
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))
    result = append_person_findings(Path(args.note_path), findings=data.get("findings", ""))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
