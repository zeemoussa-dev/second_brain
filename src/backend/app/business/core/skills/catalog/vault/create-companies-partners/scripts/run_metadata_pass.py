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

  1. discover   new companies from newly-captured threads -> Entities.md,
                appended as `Ignore: Yes` for a human to classify
  2. hubs       create any hub note that does not exist yet
  3. reconcile  make the folders agree with Entities.md -- reclassify between
                Customers and Partners, re-parent an Affiliate under its parent,
                remove a folder marked Deleted
  4. (people)   no longer here -- People run as their own hourly pipeline,
                people_pipeline.py, which files them AND folds duplicates
  5. retag      company tags on Threads, Meetings and People, from domains
  6. engagement engagement/<classification> on Threads and Meetings
  7. retrofit   Conversation index, kind/thread, kind/email, kind/attachment
                and self-link removal on Threads -- writes only what changed

Order is not arbitrary. `reconcile` runs AFTER `hubs` so an Affiliate whose
parent was only created tonight can still be filed under it, and BEFORE
`people`/`retag` so those two see every entity at its final path -- retagging a
folder that is about to move would write the old company's tag and then have to
be undone.

Discovery is APPEND-ONLY and runs by default: it adds an entry for a domain no
existing entry covers, defaulted to `Ignore: Yes` so nothing is created until a
human classifies it. `--skip-discovery` exists for a run that must not touch
Entities.md at all, not because discovery is dangerous.

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


def _sibling_skill_scripts(skill_id: str) -> Path | None:
    """Where another Skill's scripts live, in EITHER layout.

    In the repo a Skill is `catalog/<tool>/<skill>/scripts/`; deployed, Hermes
    flattens it to `<profile>/skills/<tool>/<skill>/` with no scripts/ level.
    Hardcoding the repo shape is why the previous discovery step resolved to a
    path that exists only in a checkout -- it would have reported "not found"
    every night on the machine that actually runs it."""
    for candidate in (
        SCRIPTS_DIR.parents[1] / skill_id / "scripts",          # repo, same tool
        SCRIPTS_DIR.parent / skill_id,                          # deployed, same tool
        # Another Tool: the retrofit lives under m365/, this Skill under vault/.
        *SCRIPTS_DIR.parents[2].glob(f"*/{skill_id}/scripts"),  # repo
        *SCRIPTS_DIR.parents[1].glob(f"*/{skill_id}"),          # deployed
    ):
        if candidate.is_dir():
            return candidate
    return None


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
                   "flat_people", "hubs_seen", "status", "hubs_only",
                   "threads_seen", "self_email", "total_threads"}


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
                        help="Do not look for new companies. Discovery is append-only "
                             "and safe to run nightly; this exists for a run that must "
                             "not touch Entities.md at all.")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set and "
                                   "--vault-path was not given"}))
        return 2

    vault = args.vault_path
    allow_delete = args.allow_delete
    steps: list[dict] = []

    if not args.skip_discovery:
        # find_new_entities, NOT entity-domain-extraction's build_entities_report.
        # The latter does a full destructive REWRITE of Entities.md -- correct for
        # a one-time first build, catastrophic nightly, because that file is now
        # the operator's own curation (classification, Ignore flags, merged
        # Aliases). This one parses the current file, APPENDS only domains no
        # existing entry covers, and defaults each to `Ignore: Yes` so nothing is
        # created until a human classifies it. Nothing new means the file is not
        # even re-rendered.
        #
        # Pointing at the destructive script is why discovery had to be skipped
        # at all -- and while it was skipped, 93 real companies went unrecorded
        # (2026-09-11).
        discovery_dir = _sibling_skill_scripts("new-company-discovery")
        if discovery_dir and (discovery_dir / "find_new_entities.py").is_file():
            steps.append(_run("discover", ["find_new_entities.py", "--vault-path", vault],
                              discovery_dir))
        else:
            steps.append({"step": "discover", "ok": False,
                          "error": "find_new_entities.py not found -- is the "
                                   "new-company-discovery Skill deployed?"})

    steps.append(_run("hubs", ["create_companies_partners.py", "--vault-path", vault,
                               "--hubs-only"], SCRIPTS_DIR))
    reconcile_args = ["reconcile_entities.py", "--vault-path", vault]
    if allow_delete:
        reconcile_args.append("--allow-delete")
    steps.append(_run("reconcile", reconcile_args, SCRIPTS_DIR))
    # People are no longer a step here: they run as their own hourly People
    # pipeline (people_pipeline.py), which both files them under their company
    # and folds the duplicates capture recreates (operator, 2026-09-11). This
    # step only ever did the second half -- and since hub creation stopped
    # moving people, nobody was filed at all.
    # retag-only covers People, Threads, Meetings and engagement in one call --
    # it builds its domain index once and reuses it, so splitting these apart
    # would rescan the vault per step for no benefit.
    steps.append(_run("retag", ["create_companies_partners.py", "--vault-path", vault,
                                "--retag-only"], SCRIPTS_DIR))

    # Mechanical, so it belongs here rather than waiting for a one-off run: new
    # Threads arrive every hour and each needs the same Conversation index,
    # kind tags and self-link removal the backlog got (2026-09-11).
    retrofit_dir = _sibling_skill_scripts("email-thread-capture")
    if retrofit_dir and (retrofit_dir / "retrofit_conversation_index.py").is_file():
        steps.append(_run("retrofit", ["retrofit_conversation_index.py", "--vault-path", vault],
                          retrofit_dir))
    else:
        steps.append({"step": "retrofit", "ok": False,
                      "error": "retrofit_conversation_index.py not found -- is the "
                               "email-thread-capture Skill deployed?"})

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
