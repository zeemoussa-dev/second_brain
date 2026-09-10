"""The nightly Metadata pass -- mechanical vault maintenance, no model anywhere.

The boundary this serves (operator, 2026-09-10): Metadata is everything that can
be decided without a model; Enrichment is everything that cannot. The test is
simply "does it need a model to decide?"

That split is what makes this runnable nightly. Every step here is cheap,
idempotent and safely repeatable, so the vault's structure stays correct even
when Enrichment is hours or days behind. Metadata never depends on Enrichment;
Enrichment depends on Metadata. One direction only.

    python run_metadata_pass.py [--vault-path P] [--skip-discovery]

Steps, in dependency order:

  1. discover   new companies from newly-captured threads -> Entities.md
  2. hubs       create any hub note that does not exist yet
  3. reconcile  make the folders agree with Entities.md -- reclassify between
                Customers and Partners, re-parent an Affiliate under its parent,
                remove a folder marked Deleted
  4. people     move People into their hub folder, and repair the duplicates
                capture continuously recreates
  5. retag      company tags on Threads, Meetings and People, from domains
  6. engagement engagement/<classification> on Threads and Meetings

Order is not arbitrary. `reconcile` runs AFTER `hubs` so an Affiliate whose
parent was only created tonight can still be filed under it, and BEFORE
`people`/`retag` so those two see every entity at its final path -- retagging a
folder that is about to move would write the old company's tag and then have to
be undone.

Discovery is skippable because it REWRITES Entities.md, and that file carries
the operator's own curation -- classification, Ignore flags, merged Aliases.
Everything else is additive.

Prints one JSON summary. A step that fails is reported and does NOT stop the
others: a broken retag should not also cost the night's hub creation.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable or "python"


def _run(label: str, args: list[str], cwd: Path) -> dict:
    """Runs one step and captures its outcome. Never raises -- a failed step is
    a reported result, because the whole point of a nightly pass is that it
    keeps running."""
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run([PYTHON, *args], cwd=str(cwd), capture_output=True,
                              text=True, encoding="utf-8")
    except OSError as exc:
        return {"step": label, "ok": False, "error": f"could not start: {exc}"}
    seconds = round((datetime.now(timezone.utc) - started).total_seconds(), 1)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return {"step": label, "ok": False, "seconds": seconds,
                # The TAIL of a traceback carries the exception; the head is
                # boilerplate that makes every failure look identical.
                "error": " | ".join(line.strip() for line in detail[-3:])}
    try:
        payload = json.loads((proc.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        payload = {"raw": (proc.stdout or "").strip()[:300]}
    return {"step": label, "ok": True, "seconds": seconds, "result": payload}


# Counters that only ever report inventory, never work performed -- a hub the
# pass correctly skipped is not a change, and treating it as one would make the
# quiet mode print every single night.
_INVENTORY_KEYS = {"skipped_ignored", "skipped_already", "skipped_unresolved",
                   "flat_people", "hubs_seen", "status", "hubs_only"}


def _did_something(steps: list[dict]) -> bool:
    for step in steps:
        for key, value in (step.get("result") or {}).items():
            if key in _INVENTORY_KEYS:
                continue
            if isinstance(value, list) and value:
                return True
            if isinstance(value, int) and value:
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Nightly mechanical metadata pass.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--allow-delete", action="store_true",
                        help="Let the reconcile step REMOVE the folder of an entry "
                             "marked Deleted in Entities.md. Off by default: every "
                             "other step is additive or a move, and a move can be "
                             "moved back.")
    parser.add_argument("--quiet", action="store_true",
                        help="Print nothing on a night with no failures and no "
                             "changes. Failures always print.")
    parser.add_argument("--skip-discovery", action="store_true",
                        help="Do not re-run company discovery. Discovery REWRITES "
                             "Entities.md, which carries the operator's own curation.")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set and "
                                   "--vault-path was not given"}))
        return 2

    vault = args.vault_path
    allow_delete = args.allow_delete
    steps: list[dict] = []

    if not args.skip_discovery:
        discovery_dir = SCRIPTS_DIR.parents[1] / "entity-domain-extraction" / "scripts"
        if (discovery_dir / "build_entities_report.py").is_file():
            steps.append(_run("discover", ["build_entities_report.py", "--vault-path", vault,
                                           "--force"], discovery_dir))
        else:
            steps.append({"step": "discover", "ok": False,
                          "error": f"build_entities_report.py not found at {discovery_dir}"})

    steps.append(_run("hubs", ["create_companies_partners.py", "--vault-path", vault,
                               "--hubs-only"], SCRIPTS_DIR))
    reconcile_args = ["reconcile_entities.py", "--vault-path", vault]
    if allow_delete:
        reconcile_args.append("--allow-delete")
    steps.append(_run("reconcile", reconcile_args, SCRIPTS_DIR))
    steps.append(_run("people", ["create_companies_partners.py", "--vault-path", vault,
                                 "--reconcile-people"], SCRIPTS_DIR))
    # retag-only covers People, Threads, Meetings and engagement in one call --
    # it builds its domain index once and reuses it, so splitting these apart
    # would rescan the vault per step for no benefit.
    steps.append(_run("retag", ["create_companies_partners.py", "--vault-path", vault,
                                "--retag-only"], SCRIPTS_DIR))

    failed = [s["step"] for s in steps if not s["ok"]]

    # A --no-agent cron delivers stdout verbatim, so a night where the pass
    # correctly found nothing to do should say nothing at all. A FAILURE always
    # prints -- silence has to mean "healthy", never "did not run".
    if args.quiet and not failed and not _did_something(steps):
        return 0

    print(json.dumps({
        "status": "complete" if not failed else "completed_with_failures",
        "failed_steps": failed,
        "steps": steps,
    }, ensure_ascii=False))
    # Non-zero when anything failed, so a cron job's own failure notice fires
    # rather than the pass reporting a healthy night it did not have.
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
