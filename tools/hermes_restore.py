"""Restores a *.sbb (Second Brain Backup, see hermes_backup.py) onto a
NEW machine's already-installed, already-configured Hermes (Deployment.md
Sections 1-2 done first: hermes installed, `default` profile authenticated
with the NEW machine's own real secrets/model config) and the new vault's
own `.second-brain/` tree.

This is deliberately NOT a substitute for the initial Hermes install --
it restores structural content (Agents/Profiles' own identity, Cron,
Skills) onto an already-real, already-secret-configured install, the
same "reflect the backed-up structure onto a fresh, working install"
shape as every other real onboarding step in this vault.

Real, disclosed behaviour, not silent:
  - `default`'s own content is OVERLAID onto the target's already-real
    default profile (never replaces its own config.yaml/secrets, which
    this backup never captured in the first place).
  - Every OTHER profile that doesn't yet exist on the target is created
    fresh via a real `hermes profile create <name> --clone` (inherits
    the TARGET's own now-configured default -- its own real secrets, not
    the source machine's), then the backed-up SOUL.md/skills/memories
    are overlaid on top.
  - Every `@@SECOND_BRAIN_VAULT_PATH@@`/`@@SECOND_BRAIN_HERMES_HOME@@`/
    `@@SECOND_BRAIN_DATA_PATH@@` placeholder (in cron job prompts,
    SOUL.md, anywhere -- hermes_backup.py substitutes the real values for
    these at bundle time) is substituted back for this restore's own
    real, resolved target paths -- both the raw and JSON-double-
    backslash-escaped forms.
  - cron/jobs.json (top-level AND every real per-profile
    `profiles/<id>/cron/jobs.json`, e.g. `meeting-prep-agent`) is MERGED
    by real job `id`, never overwritten wholesale -- a job id that
    already exists on the target is left alone and reported, never
    silently replaced.
  - The Second Brain app's own data (Registry `data/`, `pipelines/`) is
    written to the TARGET's own real, configured location -- read from
    ITS OWN `src/backend/.env`'s `SECOND_BRAIN_DATA_PATH` if set (the new
    machine may relocate this off the vault entirely; never assumed
    vault-relative), falling back to `<vault-path>/.second-brain` only if
    unset, same resolution `hermes_backup.py` itself uses. Only written
    if that location doesn't already have real content there -- same
    "refuse to overwrite already-curated data" discipline as
    `build_entities_report.py`'s own guard. `--force` overrides.

Usage:
    python hermes_restore.py --archive backup.sbb --vault-path NEW_P
        [--hermes-home H] [--force]

Prints a real JSON summary: profiles created, profiles overlaid, cron
jobs added/skipped, app-data restored or refused, and files rewritten.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SUPPORTED_FORMAT_VERSION = 1
_TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt"}


# Placeholder tokens, matching hermes_backup.py's own identically-named
# constants exactly (duplicated, not imported, per this tool-pair's own
# established convention) -- hermes_backup.py substitutes real paths for
# these at BUNDLE time; this module substitutes them back for the
# TARGET's own real, resolved paths at restore time. Chosen over the
# older "rewrite literal old-path -> literal new-path" design (operator,
# 2026-09-03: "C:\myWorx\Moussa MD\Moussa Brain should be a place holder
# and pass it on Restore and same for the other Path") after a real bug
# in that design: second_brain_data_path is a real, longer string that
# CONTAINS the vault path as its own prefix whenever it's vault-relative
# (the common case) -- rewriting the vault path first silently consumed
# that shared prefix, leaving the data-path rewrite nothing left to
# match, and restore fell back to the wrong (vault-relative) location
# instead of the real, resolved target. A placeholder is a fixed, unique
# token with no such overlap risk by construction, and restore no longer
# needs to know the SOURCE machine's own old values at all -- only the
# target's own real, resolved paths.
_PLACEHOLDER_VAULT_PATH = "@@SECOND_BRAIN_VAULT_PATH@@"
_PLACEHOLDER_HERMES_HOME = "@@SECOND_BRAIN_HERMES_HOME@@"
_PLACEHOLDER_DATA_PATH = "@@SECOND_BRAIN_DATA_PATH@@"


def _substitute_placeholder(text: str, placeholder: str, real_value: str, *, json_escaped: bool) -> str:
    """Replaces every occurrence of placeholder with real_value -- the
    JSON-double-backslash-escaped form when the containing file is JSON
    (a Windows path in a JSON string always carries doubled backslashes),
    the raw form otherwise.

    BUG FIX (2026-09-03, found live testing the Artifacts export/import
    path that reuses this exact mechanism): the original version of this
    function tried BOTH forms unconditionally, in sequence --
    `text.replace(placeholder, real_value)` followed by
    `text.replace(placeholder, escaped_value)`. That is safe on the
    EXPORT side (hermes_backup.py's own identically-shaped helper), which
    searches for two DIFFERENT candidate real-value spellings and
    replaces both with the SAME placeholder -- no conflict. It is wrong
    here: the first `.replace()` call consumes every real placeholder
    occurrence in the text, so the second call (the one a `.json` file
    actually needs) always finds nothing left to replace -- silently
    leaving raw, unescaped backslashes inside a JSON string, which is
    invalid JSON. Confirmed live: a bundled `.json` file referencing
    `@@SECOND_BRAIN_VAULT_PATH@@` came back holding a raw, single-
    backslash path where a JSON string needs doubled backslashes -- an
    unparsable string. Since the placeholder token itself carries no backslashes, it
    looks identical whether it originated in a `.json` file or a
    `.py`/`.md`/`.txt` one -- there is no way to recover which form is
    needed from the token alone, so the caller must say so via
    `json_escaped` instead of this function blindly trying both."""
    value = real_value.replace("\\", "\\\\") if json_escaped else real_value
    return text.replace(placeholder, value)


def _substitute_placeholders(
    text: str, vault_path: str, hermes_home: str, second_brain_data_path: str, *, json_escaped: bool,
) -> str:
    """No ordering concern here (unlike the old rewrite-based design) --
    each placeholder is a unique, non-overlapping token, so substitution
    order genuinely doesn't matter; kept in the same vault/hermes_home/
    data_path order as hermes_backup.py's own substitution purely for
    readability."""
    text = _substitute_placeholder(text, _PLACEHOLDER_VAULT_PATH, vault_path, json_escaped=json_escaped)
    text = _substitute_placeholder(text, _PLACEHOLDER_HERMES_HOME, hermes_home, json_escaped=json_escaped)
    text = _substitute_placeholder(text, _PLACEHOLDER_DATA_PATH, second_brain_data_path, json_escaped=json_escaped)
    return text


def _rewrite_tree(root: Path, vault_path: str, hermes_home: str, second_brain_data_path: str) -> int:
    rewritten = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new_text = _substitute_placeholders(
            text, vault_path, hermes_home, second_brain_data_path, json_escaped=path.suffix.lower() == ".json",
        )
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            rewritten += 1
    return rewritten


def _overlay(src: Path, dst: Path) -> int:
    """Copies every real file from src onto dst, creating dst's own
    parent dirs as needed, overwriting file-for-file (never a wholesale
    directory replace, so anything on the target that this backup never
    touched -- e.g. a target-only .env -- is left alone)."""
    if not src.exists():
        return 0
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return 1
    count = 0
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        target = dst / path.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        count += 1
    return count


def _profile_root(hermes_home: Path, profile_id: str) -> Path:
    return hermes_home if profile_id == "default" else hermes_home / "profiles" / profile_id


def _ensure_profile_exists(hermes_home: Path, profile_id: str) -> str:
    """Returns "existing" if the profile is already real on this
    machine, "created" if a real `hermes profile create --clone` was
    just run for it. Never touches `default` -- that one is assumed
    already real (Deployment.md Sections 1-2 done first)."""
    if profile_id == "default":
        return "existing"
    root = _profile_root(hermes_home, profile_id)
    if root.exists():
        return "existing"
    result = subprocess.run(
        ["hermes", "profile", "create", profile_id, "--clone"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"hermes profile create {profile_id!r} --clone failed: {result.stderr.strip()}")
    return "created"


class RestoreValidationError(Exception):
    """Raised when validation finds one or more real problems -- carries
    the full list, never just the first. Raising this means NOTHING has
    been written to the real target yet (operator, 2026-09-03: "should
    say error in restore instead of Destroying my self") -- every check
    in _validate() runs read-only, against the extracted scratch copy and
    the target's own current state, before restore() does its first real
    write."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


def _validate(scratch: Path, manifest: dict, hermes_home: Path, vault_path: Path) -> None:
    problems: list[str] = []

    if "source_vault_path" not in manifest:
        problems.append("manifest.json is missing source_vault_path -- archive is malformed or from an incompatible version")

    # Every real JSON file this restore will actually read (cron jobs.json,
    # any Agent.json under the app-data bundle) must parse -- a corrupt
    # archive member is caught HERE, read-only, not mid-write.
    for path in scratch.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            problems.append(f"{path.relative_to(scratch)}: invalid JSON ({exc})")

    # "default" must already be real on the target -- Deployment.md
    # Sections 1-2 (install + `hermes setup`) done first, with the
    # target's OWN real secrets. Restoring onto a machine with no Hermes
    # install at all is out of this tool's own scope by design.
    if not hermes_home.exists():
        problems.append(
            f"target Hermes home {hermes_home} doesn't exist -- install and configure Hermes there first "
            f"(Deployment.md Sections 1-2), then restore onto it"
        )
    elif not (hermes_home / "SOUL.md").exists():
        problems.append(
            f"{hermes_home} exists but has no SOUL.md -- doesn't look like a real, already-configured "
            f"default profile yet (Deployment.md Sections 1-2)"
        )

    if not vault_path.exists():
        problems.append(f"target vault path {vault_path} doesn't exist -- copy the real vault there first, then restore")

    hermes_cli = shutil.which("hermes")
    if hermes_cli is None:
        problems.append("the `hermes` CLI isn't on PATH -- needed to create any profile this backup carries that doesn't already exist on the target")

    if problems:
        raise RestoreValidationError(problems)


def _resolve_second_brain_data_path(vault_path: Path, repo_root: Path, override: str | None) -> Path:
    """Same resolution as hermes_backup.py's own identically-named
    function (duplicated deliberately, not imported -- each of this
    tool-pair's two scripts owns its own copy, matching this project's
    own established "no shared import across this kind of boundary"
    convention): real `SECOND_BRAIN_DATA_PATH` from THIS machine's own
    `src/backend/.env` if set, else the same vault-relative default the
    backend itself falls back to. `override` (the CLI flag) wins over
    both."""
    if override:
        return Path(override)
    env_path = repo_root / "src" / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("SECOND_BRAIN_DATA_PATH="):
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return Path(value)
    return vault_path / ".second-brain"


def _merge_cron_jobs(target_path: Path, backed_up_jobs_path: Path) -> dict:
    if not backed_up_jobs_path.exists():
        return {"added": [], "skipped_existing": []}
    backed_up = json.loads(backed_up_jobs_path.read_text(encoding="utf-8"))
    target_data = json.loads(target_path.read_text(encoding="utf-8")) if target_path.exists() else {"jobs": [], "updated_at": None}
    existing_ids = {j.get("id") for j in target_data.get("jobs", [])}

    added, skipped = [], []
    for job in backed_up.get("jobs", []):
        job_id = job.get("id")
        if job_id in existing_ids:
            skipped.append({"id": job_id, "name": job.get("name")})
            continue
        target_data.setdefault("jobs", []).append(job)
        added.append({"id": job_id, "name": job.get("name")})

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(target_data, indent=2), encoding="utf-8")
    return {"added": added, "skipped_existing": skipped}


def restore(
    archive_path: Path, hermes_home: Path, vault_path: Path, force: bool,
    second_brain_data_path_override: str | None = None,
) -> dict:
    scratch = Path(tempfile.mkdtemp(prefix="second-brain-restore-"))
    try:
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(scratch)

        manifest_path = scratch / "manifest.json"
        if not manifest_path.exists():
            raise RestoreValidationError(["archive has no manifest.json -- not a real .sbb backup, or corrupted"])
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RestoreValidationError([f"manifest.json is not valid JSON ({exc})"]) from exc
        if manifest.get("format_version") != _SUPPORTED_FORMAT_VERSION:
            raise RestoreValidationError([f"unsupported backup format_version {manifest.get('format_version')!r} (this tool supports {_SUPPORTED_FORMAT_VERSION})"])

        # Full validation pass -- read-only, against the extracted scratch
        # copy and the target's own current state. Raises with every real
        # problem found (not just the first) if anything is wrong; NOTHING
        # below this line has run yet, so a validation failure leaves the
        # real target completely untouched.
        _validate(scratch, manifest, hermes_home, vault_path)

        # Resolved BEFORE the rewrite step (not just before its own later
        # use restoring second-brain-data-root) -- a SKILL.md example can
        # embed the @@SECOND_BRAIN_DATA_PATH@@ placeholder directly (e.g.
        # vault-index's own --data-path), and needs the real, resolved
        # TARGET value to substitute in, same as vault/hermes-home below.
        second_brain_data_path = _resolve_second_brain_data_path(
            vault_path, Path(__file__).resolve().parent.parent, second_brain_data_path_override,
        )

        # Substitute every real @@SECOND_BRAIN_VAULT_PATH@@/
        # @@SECOND_BRAIN_HERMES_HOME@@/@@SECOND_BRAIN_DATA_PATH@@
        # placeholder INSIDE the extracted scratch copy first, before
        # anything is overlaid onto the real install -- so what lands on
        # disk is already correct. No dependency on the manifest's own
        # source_* values here (placeholders, not old->new string
        # rewriting -- see _substitute_placeholders's own docstring).
        files_rewritten = _rewrite_tree(scratch, str(vault_path), str(hermes_home), str(second_brain_data_path))

        profile_results = {}
        for profile_id in manifest["profiles"]:
            state = _ensure_profile_exists(hermes_home, profile_id)
            src_root = scratch / "hermes" / profile_id
            target_root = _profile_root(hermes_home, profile_id)
            copied = _overlay(src_root, target_root)
            profile_results[profile_id] = {"state": state, "files_overlaid": copied}

        # Top-level "cron/jobs.json" archive member, deliberately separate
        # from "hermes/<profile>/" -- see hermes_backup.py's own comment.
        # This is the ONLY code path that ever touches the target's own
        # top-level cron/jobs.json; the profile-overlay loop above never
        # includes it.
        cron_result = {"default": _merge_cron_jobs(hermes_home / "cron" / "jobs.json", scratch / "cron" / "jobs.json")}

        # Same for every real per-profile cron/jobs.json this backup
        # carries -- also its own dedicated archive member (see
        # hermes_backup.py's own comment for why), also the ONLY code
        # path that ever touches that profile's own cron/jobs.json.
        profiles_cron_dir = scratch / "cron" / "profiles"
        if profiles_cron_dir.exists():
            for profile_cron_dir in sorted(profiles_cron_dir.iterdir()):
                if not profile_cron_dir.is_dir():
                    continue
                profile_id = profile_cron_dir.name
                target_cron_path = _profile_root(hermes_home, profile_id) / "cron" / "jobs.json"
                cron_result[profile_id] = _merge_cron_jobs(target_cron_path, profile_cron_dir / "jobs.json")

        # One wholesale root, matching hermes_backup.py's own
        # _add_second_brain_data_root shape (Registry data/, Pipelines/,
        # Settings/ -- real curated data, deliberately included, see that
        # function's own docstring -- AND every loose top-level file:
        # agent_visuals.json, agent_sections.json, cockpit_chat.json,
        # email_staging/, tools/registry.json, ...). The "already has
        # real content" refuse-check looks at the whole real target root,
        # excluding only index/ (which the backup itself never touches
        # either, so its real presence on the target is never a reason to
        # refuse) -- same guard, correctly scoped to what this restore
        # step actually writes.
        existing_count = 0
        if second_brain_data_path.exists():
            existing_count = sum(
                1 for p in second_brain_data_path.rglob("*")
                if p.is_file() and p.relative_to(second_brain_data_path).parts[0] != "index"
            )
        if existing_count and not force:
            app_data_result = {"status": "refused", "reason": "already has real content", "existing_files": existing_count}
        else:
            copied = _overlay(scratch / "second-brain-data-root", second_brain_data_path)
            app_data_result = {"status": "restored", "files": copied}

        return {
            "profiles": profile_results,
            "cron": cron_result,
            "second_brain_data_path": str(second_brain_data_path),
            "second_brain_data": app_data_result,
            "path_rewrite": {
                # Purely informational here -- the actual substitution
                # never reads these; the manifest's own real source_*
                # values are kept only so this summary can show a human
                # what changed.
                "vault": {"from": manifest.get("source_vault_path"), "to": str(vault_path)},
                "hermes_home": {"from": manifest.get("source_hermes_home"), "to": str(hermes_home)},
                "second_brain_data_path": {"from": manifest.get("source_second_brain_data_path"), "to": str(second_brain_data_path)},
                "files_rewritten": files_rewritten,
            },
            "manual_follow_ups": [
                "hermes setup model  # config.yaml was never backed up -- point the default profile at Compass on THIS machine",
                "hermes -p <profile> whatsapp  # per profile that needs WhatsApp delivery -- pairing never travels in a backup, real QR scan required each time",
                "hermes gateway install / verify Startup-folder entries for any profile a restored cron job targets",
                "hermes cron list  # confirm every merged job's own schedule/state before trusting it to fire unattended",
            ],
        }
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--hermes-home", default=None, help="Defaults to the real, current machine's own Hermes home (%%LOCALAPPDATA%%\\hermes).")
    parser.add_argument("--force", action="store_true", help="Overwrite already-present Second Brain app data instead of refusing.")
    parser.add_argument(
        "--second-brain-data-path",
        default=None,
        help="Defaults to reading SECOND_BRAIN_DATA_PATH from THIS machine's own src/backend/.env, "
             "falling back to <vault-path>/.second-brain only if that's unset -- same resolution "
             "the backend itself uses. Override explicitly if needed.",
    )
    args = parser.parse_args()

    import os
    hermes_home = Path(args.hermes_home) if args.hermes_home else Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes"))

    # Never a raw traceback -- operator, 2026-09-03: "should say error in
    # restore instead of Destroying my self". RestoreValidationError means
    # the real target was never touched at all (validation runs before
    # the first write); any OTHER exception means something failed
    # mid-restore (e.g. a real `hermes profile create` call) -- reported
    # just as cleanly, but real partial state on the target is possible
    # in that case and is named explicitly, not papered over.
    try:
        result = restore(
            Path(args.archive), hermes_home, Path(args.vault_path), args.force,
            second_brain_data_path_override=args.second_brain_data_path,
        )
    except RestoreValidationError as exc:
        print(json.dumps({"status": "refused", "problems": exc.problems}, indent=2, ensure_ascii=False))
        return 1
    except Exception as exc:  # noqa: BLE001 -- last resort, must never leak a raw traceback to the operator
        print(json.dumps({"status": "failed_mid_restore", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps({"status": "ok", **result}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
