"""The Company pass -- what each company's notes, and its People, learn from the
reads Enrichment saved. No model.

Operator, 2026-09-11: the Company pipeline fills the company Logs and Captures,
and "should pull the people as well". One owner for a company's History and
Captures notes, rather than every enrichment run writing them as it goes --
which is how two writers start overwriting each other.

    python run_company_pass.py [--vault-path P] [--quiet]

Steps -- independent of one another, each re-derived from the saved reads:

  1. history   a dated line per Thread in each named company's History
  2. captures  each important fact filed in its company's `## Captured`
  3. people    each person's revealed fields filled; a DIFFERENT value is logged
               to their History and the existing one kept

Idempotent throughout, so a missed write is simply made on the next run, and a
company or alias added later picks up everything already read about it. A
failed step is reported and does NOT stop the others.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import run_metadata_pass as rmp

_INVENTORY = rmp._INVENTORY_KEYS | {"extractions_read", "threads_not_found",
                                    "facts_unresolved", "people_not_in_vault"}


def plan_steps(vault: str) -> list[tuple[str, list[str], Path | None, str]]:
    threads = rmp._sibling_skill_scripts("summarize-and-tag-threads")
    return [
        ("history", ["history_from_extracts.py", "--vault-path", vault], threads,
         "history_from_extracts.py"),
        ("captures", ["captures_from_extracts.py", "--vault-path", vault], threads,
         "captures_from_extracts.py"),
        ("people", ["people_from_extracts.py", "--vault-path", vault], threads,
         "people_from_extracts.py"),
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
    parser = argparse.ArgumentParser(description="Nightly Company pass.")
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
