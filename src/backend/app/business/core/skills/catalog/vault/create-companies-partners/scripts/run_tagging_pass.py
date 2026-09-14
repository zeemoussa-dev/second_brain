"""The Tagging pass -- every company tag, and the engagement label, mechanically.

Enrichment and Tagging are two pipelines (operator, 2026-09-11: "Enrich is
different from Tagging, 2 Pipelines now"), and Tagging owns ALL of it. Enrichment
is the model reading; Tagging applies what can be decided without one. Nothing
here needs a model: Enrichment's reads are already saved on disk.

    python run_tagging_pass.py [--vault-path P] [--quiet]

Steps, in order:

  1. domain            company tags on People, Threads and Meetings from email
                       domains, with each Thread's company links
  2. content-threads   company tags from each Thread's SAVED extraction
  3. content-files     company tags from each attachment summary's wiki-links
  4. engagement        engagement/<classification>, derived from the tags the
                       three steps above wrote -- LAST, so it sees both sources

Everything is re-derived from what is on disk, so a run is idempotent and a
write lost to a concurrent one is simply made again on the next run. A failed
step is reported and does NOT stop the others.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import run_metadata_pass as rmp

SCRIPTS_DIR = Path(__file__).resolve().parent

# Counters that describe what was LOOKED AT, not what was changed. Treating them
# as work would make the quiet mode print every single night.
_INVENTORY = rmp._INVENTORY_KEYS | {"extractions_read", "summarized_files",
                                    "names_still_unresolved", "threads_not_found"}


def plan_steps(vault: str) -> list[tuple[str, list[str], Path | None, str]]:
    """(label, argv, working folder, script) for each step, in order."""
    threads = rmp._sibling_skill_scripts("summarize-and-tag-threads")
    files = rmp._sibling_skill_scripts("summarize-and-tag-files")
    return [
        ("domain", ["create_companies_partners.py", "--vault-path", vault, "--domain-tags"],
         SCRIPTS_DIR, "create_companies_partners.py"),
        ("content-threads", ["retag_threads_from_extracts.py", "--vault-path", vault],
         threads, "retag_threads_from_extracts.py"),
        ("content-files", ["retag_files_from_summaries.py", "--vault-path", vault],
         files, "retag_files_from_summaries.py"),
        ("engagement", ["create_companies_partners.py", "--vault-path", vault, "--engagement"],
         SCRIPTS_DIR, "create_companies_partners.py"),
    ]


def _did_something(steps: list[dict]) -> bool:
    for step in steps:
        for key, value in (step.get("result") or {}).items():
            if key in _INVENTORY or isinstance(value, bool):
                continue
            if isinstance(value, (list, int)) and value:
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Nightly Tagging pass.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--quiet", action="store_true",
                        help="Print nothing on a night with no failures and no changes.")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2

    steps: list[dict] = []
    for label, argv, cwd, script in plan_steps(args.vault_path):
        if cwd is None or not (cwd / script).is_file():
            steps.append({"step": label, "ok": False,
                          "error": f"{script} not found -- is its Skill deployed?"})
            continue
        steps.append(rmp._run(label, argv, cwd))

    failed = [s["step"] for s in steps if not s["ok"]]
    if args.quiet and not failed and not _did_something(steps):
        return 0
    print(json.dumps({"status": "complete" if not failed else "completed_with_failures",
                      "failed_steps": failed, "steps": steps}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
