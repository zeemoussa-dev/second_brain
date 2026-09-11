"""Apply already-decided `topic/*` tags to Thread/Meeting notes.

Applies a judgment the agent has already made; it never decides a topic
itself (the same split `apply_thread_review.py` uses -- prompts do the
reading, scripts do the mechanical part).

Two gates it will not let a caller past:

1. **Closed vocabulary.** Every topic is checked against
   `Settings/Tag Taxonomy.md`. An undeclared value is rejected and
   reported, never written and never quietly dropped -- the taxonomy's
   own rule is that an undeclared tag "is not a tag, it is a proposal".
2. **Confidence floor.** Anything below the floor is routed to
   `Tag Taxonomy Review.md` instead of the note, because a wrong tag is
   worse than no tag: it makes retrieval confidently incomplete.

Idempotent. Re-running with the same input rewrites the same tag set and
only moves the `topics_tagged_at` stamp.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import vault_manager as vm

from topic_vocabulary import load_closed_topics, taxonomy_path

_STAMP_FIELD = "topics_tagged_at"
_DEFAULT_FLOOR = 0.6
_MAX_TOPICS = 3


def _review_path() -> Path:
    return taxonomy_path().with_name("Tag Taxonomy Review.md")


def _append_review(entries: list[dict]) -> None:
    """Append low-confidence and rejected proposals for the operator to
    adopt or discard. Append-only: this file is a human inbox, and
    rewriting it would silently discard items not yet actioned."""
    if not entries:
        return
    path = _review_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## topic-tagging {stamp}\n"]
    for entry in entries:
        lines.append(f"- `{entry['note_path']}`")
        lines.append(f"  - {entry['why']}: {', '.join(entry['topics']) or '(none)'}")
        if entry.get("confidence") is not None:
            lines.append(f"  - confidence: {entry['confidence']}")
    header = "" if path.exists() else "# Tag taxonomy review\n\nProposals quarantined by the tagging pipelines. Adopt into `Tag Taxonomy.md` or discard.\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(header + "\n".join(lines) + "\n")


def apply_entry(entry: dict, allowed: set[str], floor: float) -> dict:
    note_path = entry.get("note_path") or entry.get("path")
    topics = list(dict.fromkeys(entry.get("topics") or []))
    confidence = entry.get("confidence")

    if not note_path:
        return {"note_path": None, "status": "error", "detail": "no note_path"}
    if not Path(note_path).is_file() and not Path(note_path).exists():
        return {"note_path": note_path, "status": "error", "detail": "note not found"}
    if not topics:
        return {"note_path": note_path, "status": "skipped", "detail": "no topics given"}

    unknown = [topic for topic in topics if topic not in allowed]
    if unknown:
        return {
            "note_path": note_path, "status": "rejected",
            "detail": f"undeclared topic(s): {', '.join(unknown)}",
            "quarantine": {"note_path": note_path, "topics": unknown,
                           "why": "undeclared in Tag Taxonomy.md",
                           "confidence": confidence},
        }
    if confidence is not None and confidence < floor:
        return {
            "note_path": note_path, "status": "quarantined",
            "detail": f"confidence {confidence} below floor {floor}",
            "quarantine": {"note_path": note_path, "topics": topics,
                           "why": "below confidence floor", "confidence": confidence},
        }
    if len(topics) > _MAX_TOPICS:
        return {"note_path": note_path, "status": "error",
                "detail": f"{len(topics)} topics given, maximum is {_MAX_TOPICS}"}

    frontmatter, body = vm.read_note(Path(note_path))
    existing = [str(tag) for tag in (frontmatter.get("tags") or [])]
    # Existing non-topic tags are preserved; previous topic tags are
    # replaced, so a re-run after new messages lands the current judgment
    # rather than accumulating every topic ever guessed. dict.fromkeys
    # also de-duplicates in place: real notes in this vault carry the
    # same bare tag repeated up to six times (one per attendee), and
    # writing the line back without de-duplicating would preserve a
    # defect on a line already being rewritten.
    merged = list(dict.fromkeys(
        [tag for tag in existing if not tag.startswith("topic/")] + topics
    ))
    frontmatter["tags"] = merged
    frontmatter[_STAMP_FIELD] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    vm.write_note(Path(note_path), frontmatter, body)
    return {"note_path": note_path, "status": "tagged", "topics": topics}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", required=True,
                        help='JSON: {"entries": [{"note_path":..., "topics":[...], "confidence":0.9}]}')
    parser.add_argument("--confidence-floor", type=float, default=_DEFAULT_FLOOR)
    args = parser.parse_args()

    payload = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        print(json.dumps({"error": "input must be a list, or {entries: [...]}"}))
        return 1

    allowed = set(load_closed_topics())
    results = [apply_entry(entry, allowed, args.confidence_floor) for entry in entries]
    _append_review([r["quarantine"] for r in results if r.get("quarantine")])

    summary: dict[str, int] = {}
    for result in results:
        summary[result["status"]] = summary.get(result["status"], 0) + 1
    json.dump(
        {"summary": summary,
         "review_file": str(_review_path()) if any(r.get("quarantine") for r in results) else None,
         "results": [{k: v for k, v in r.items() if k != "quarantine"} for r in results]},
        sys.stdout, indent=2,
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
