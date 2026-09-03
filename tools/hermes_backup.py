"""Creates a *.sbb (Second Brain Backup) archive of the real, live Hermes
install's own structural content -- Agents (Profiles' own SOUL.md +
identity), Cron (jobs.json + the no-agent runner scripts jobs actually
invoke), and Skills -- plus the Second Brain app's own matching data (the
Registry: Sections/Agents/Skills/Providers/Tools, and Pipelines) from the
vault's own `.second-brain/data/` and `.second-brain/pipelines/`.

Skills are NOT a blanket copy of each profile's own skills/ tree -- only
this project's OWN canonical skill ids (whatever
Hermes-Provisioning/skills/<category>/<name>/ in this repo actually has)
are bundled, per profile. A profile's real deployed skills/ tree also
carries every STOCK skill bundled with Hermes itself
(docx/pdf/pptx/xlsx/research-paper-writing/...) -- these are not unique
data, ship fresh with any new Hermes install via its own skill
management, and one of them alone (research-paper-writing's own LaTeX
conference templates) was real, non-trivial size; found live inflating
an early version of this tool's own real output to ~400 MB, most of
which was this plus a 39.6 MB-per-profile internal search-index cache
(also now excluded, see _is_excluded).

Deliberately excludes (operator, 2026-09-03):
  - Hermes instance-level config.yaml (top-level and per-profile) -- get
    this fresh via `hermes setup` on the new machine, never copied.
  - Every real secret: .env (top-level and per-profile), auth.json/.lock,
    channel_directory.json (WhatsApp session), shared/nous_auth.*.
  - All caches, session state, and logs: state.db(-wal/-shm), kanban.db,
    projects.db, verification_evidence.db, cache/, audio_cache/,
    image_cache/, sandboxes/, sessions/, workspace/, logs/, tmp/, temp/,
    gateway-service/, hermes-agent/ (the Hermes Agent install itself --
    re-cloned fresh per Deployment.md, not bundled), bin/, __pycache__/
    (Python-version-specific, regenerable), .hub/ (Hermes' own internal
    skill-search cache, regenerable), and every *.lock/*.pid file.
  - Every non-canonical (stock/bundled) skill in a profile's own deployed
    skills/ tree -- see above.
  - The vault's own `.second-brain/Settings/` -- vault-relative curated
    data that already travels with a real vault-folder copy; out of this
    tool's own scope, not re-bundled here.

The Second Brain app's own data folder is READ FROM REAL SETTINGS
(`src/backend/.env`'s own `SECOND_BRAIN_DATA_PATH`), never assumed to be
`<vault>/.second-brain` -- that's only the backend's own DEFAULT when the
setting is unset (`app/config.py::Settings._default_second_brain_data_path`),
not a guarantee. Found live, 2026-09-03: a real backup taken on a machine
where this had been relocated off the vault silently missed the entire
Registry (every Agent's own Section placement -- what the operator calls
"Visual", since it's the real data behind Agents Map positioning) because
the tool looked in the wrong place, not because that data doesn't exist.
`--second-brain-data-path` overrides this resolution explicitly if needed.

Per-profile cron schedules are ALSO real and separate from the top-level
`cron/jobs.json` -- a profile that has ever run `hermes -p <profile> cron
create` gets its own `profiles/<id>/cron/jobs.json`, confirmed live on
`meeting-prep-agent`/`azure-expert`/`compass-expert` (this is what the
operator calls "Schedule"). Each is bundled as its own dedicated archive
member (`cron/profiles/<id>/jobs.json`), same "never nested under the
generic profile-overlay tree" discipline as the top-level file, for the
exact same restore-side clobber-avoidance reason.

The archive is a plain zip -- no business logic, matching this project's
own established `sbf_archive.py`/`sbd_archive.py` "pure I/O" convention.
A `manifest.json` at the root records `source_vault_path` (so
`hermes_restore.py` can rewrite every real occurrence of it to the target
machine's own real vault path) and the list of every profile bundled.

Usage:
    python hermes_backup.py --vault-path P --output out.sbb
        [--hermes-home H]  # defaults to the real %LOCALAPPDATA%\\hermes

Prints {"output": str, "profiles": [str, ...], "size_bytes": int} on
success.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_FORMAT_VERSION = 1

# Relative-to-profile-root (or relative-to-hermes-home for the top-level
# default profile) paths to include, whole subtree -- everything else is
# excluded by construction (an allowlist, not a denylist), so a new,
# unrecognized Hermes-side file never accidentally rides along. "skills"
# is NOT listed here -- it's handled separately by _add_canonical_skills,
# filtered to only this project's own canonical skill ids (see that
# function's own docstring for why blanket-including it was real,
# unnecessary bloat).
_PROFILE_INCLUDE = [
    "SOUL.md",
    "profile.yaml",
    "memories",
]
# The top-level (default/primary) Hermes home has one extra real,
# non-secret, structural item no per-profile folder carries. Its own
# "_disabled-skills-on-primary" is NOT listed here -- the generic
# prefix-scan loop in _add_profile() already catches it (any
# "_disabled-skills*"-named child), and listing it twice double-added it
# into the zip (found live -- zipfile's own "Duplicate name" warning).
# "cron/jobs.json" is ALSO deliberately NOT here -- see the top-level
# "cron/jobs.json" archive member below; bundling it under the generic
# per-profile overlay tree let hermes_restore.py's own plain-file-copy
# overlay step silently clobber it before the dedicated merge-by-id cron
# logic ever ran (found live, 2026-09-03 -- the exact "destroying my
# self" risk this whole tool exists to avoid). Restore must have exactly
# ONE code path that ever touches a target's own cron/jobs.json.
_TOP_LEVEL_EXTRA_INCLUDE = [
    "scripts",
]
# Per-profile "_disabled-skills*" staging folders -- name varies per
# profile (e.g. "_disabled-skills", "_disabled-skills-unused-by-files-manager"),
# so these are discovered by prefix match, not a fixed list.
_DISABLED_SKILLS_PREFIX = "_disabled-skills"


def _is_excluded(path: Path) -> bool:
    """__pycache__/*.pyc(.pyo) is real, live-found bloat -- Python-
    version-specific compiled bytecode (cpython-311 vs cpython-314
    mismatches observed live this same session), fully regenerable, zero
    business content. Never bundled. Same for ".hub/" -- Hermes' own
    internal skill-search index cache (found live: a single
    "hermes-index.json" per profile, 39.6 MB, byte-for-byte near-
    identical across all 40 real profiles -- the actual cause of a
    ~400 MB archive the operator rightly questioned; regenerates itself,
    zero business content, same as __pycache__)."""
    return "__pycache__" in path.parts or ".hub" in path.parts or path.suffix in (".pyc", ".pyo")


def _canonical_skill_ids(repo_root: Path) -> set[str]:
    """{"company-review/create-companies-partners", ...} -- every real
    "<category>/<skill-name>" this project itself owns and canonically
    sources (Hermes-Provisioning/skills/), derived live rather than
    hand-listed so it never goes stale as skills are added. A profile's
    own deployed skill tree also carries every STOCK, bundled-with-Hermes
    skill (docx/pdf/pptx/xlsx/research-paper-writing/...) -- found live,
    these are NOT unique data, ship fresh with any new Hermes install via
    its own skill management, and one of them alone
    (research-paper-writing's own LaTeX conference templates) was real,
    non-trivial size. Only a profile's own skill folder matching one of
    these real, canonical ids is ever bundled; everything else in a
    profile's skills/ tree is assumed recoverable on the target machine
    without needing to travel in this backup at all."""
    skills_root = repo_root / "Hermes-Provisioning" / "skills"
    ids: set[str] = set()
    if not skills_root.exists():
        return ids
    for category_dir in skills_root.iterdir():
        if not category_dir.is_dir():
            continue
        for skill_dir in category_dir.iterdir():
            if skill_dir.is_dir():
                ids.add(f"{category_dir.name}/{skill_dir.name}")
    return ids


def _add_canonical_skills(zf: zipfile.ZipFile, skills_root: Path, canonical_ids: set[str], arc_prefix: str) -> int:
    """Walks skills_root at the real <category>/<skill-name> depth,
    bundling only the ones this project's own canonical source actually
    owns (see _canonical_skill_ids's own docstring for why the rest is
    deliberately left out)."""
    if not skills_root.exists():
        return 0
    count = 0
    for category_dir in skills_root.iterdir():
        if not category_dir.is_dir():
            continue
        for skill_dir in category_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            if f"{category_dir.name}/{skill_dir.name}" not in canonical_ids:
                continue
            count += _add_tree(zf, skill_dir, f"{arc_prefix}/{category_dir.name}/{skill_dir.name}")
    return count


def _add_tree(zf: zipfile.ZipFile, src: Path, arc_prefix: str) -> int:
    """Adds every real file under src into the zip under arc_prefix,
    preserving the real relative structure. Returns the count of files
    added; 0 (no error) if src doesn't exist -- an optional real path
    (e.g. a profile with no memories/ yet) is not a failure."""
    if not src.exists():
        return 0
    if src.is_file():
        zf.write(src, arc_prefix)
        return 1
    count = 0
    for path in src.rglob("*"):
        if not path.is_file() or _is_excluded(path):
            continue
        arcname = f"{arc_prefix}/{path.relative_to(src).as_posix()}"
        zf.write(path, arcname)
        count += 1
    return count


def _add_profile(zf: zipfile.ZipFile, profile_root: Path, profile_id: str, extra_include: list[str], canonical_skill_ids: set[str]) -> int:
    count = 0
    for rel in _PROFILE_INCLUDE + extra_include:
        count += _add_tree(zf, profile_root / rel, f"hermes/{profile_id}/{rel}")
    count += _add_canonical_skills(zf, profile_root / "skills", canonical_skill_ids, f"hermes/{profile_id}/skills")
    for child in profile_root.iterdir():
        if child.is_dir() and child.name.startswith(_DISABLED_SKILLS_PREFIX):
            count += _add_canonical_skills(zf, child, canonical_skill_ids, f"hermes/{profile_id}/{child.name}")
    return count


def _resolve_second_brain_data_path(vault_path: Path, repo_root: Path, override: str | None) -> Path:
    """Real settings, not a hardcoded vault-relative guess -- mirrors
    `app/config.py::Settings._default_second_brain_data_path` exactly:
    `SECOND_BRAIN_DATA_PATH` from the backend's own real `.env` if set to
    a non-empty value, else the same default the backend itself falls
    back to. `override` (the CLI flag) wins over both when given."""
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


def build_backup(
    hermes_home: Path, vault_path: Path, output_path: Path, repo_root: Path,
    second_brain_data_path_override: str | None = None,
) -> dict:
    profiles_root = hermes_home / "profiles"
    profile_ids = sorted(p.name for p in profiles_root.iterdir() if p.is_dir()) if profiles_root.exists() else []
    canonical_skill_ids = _canonical_skill_ids(repo_root)
    second_brain_data_path = _resolve_second_brain_data_path(vault_path, repo_root, second_brain_data_path_override)

    manifest = {
        "format_version": _FORMAT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_vault_path": str(vault_path),
        "source_second_brain_data_path": str(second_brain_data_path),
        # Skills' own SKILL.md files embed the FULL absolute path to their
        # deployed scripts in example commands (e.g. "C:\Users\<user>\
        # AppData\Local\hermes\skills\...\vault_manager.py") -- this
        # includes the Windows username, a real, separate rewrite target
        # from the vault path (found live, operator: "Skills that needs
        # the full Path of things like... entities.md this is different
        # path"). hermes_restore.py rewrites both.
        "source_hermes_home": str(hermes_home),
        "profiles": ["default"] + profile_ids,
        "canonical_skill_ids_bundled": sorted(canonical_skill_ids),
    }

    total_files = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Top-level = the "default" profile, real files live directly under hermes_home.
        total_files += _add_profile(zf, hermes_home, "default", _TOP_LEVEL_EXTRA_INCLUDE, canonical_skill_ids)

        # A DELIBERATELY SEPARATE top-level archive member, not nested
        # under "hermes/default/" -- see _TOP_LEVEL_EXTRA_INCLUDE's own
        # comment for why. hermes_restore.py's dedicated merge-by-id cron
        # logic is the only code path that ever reads this member.
        total_files += _add_tree(zf, hermes_home / "cron" / "jobs.json", "cron/jobs.json")

        for profile_id in profile_ids:
            total_files += _add_profile(zf, profiles_root / profile_id, profile_id, [], canonical_skill_ids)
            # A profile's own cron/jobs.json (real once that profile has
            # ever run `hermes -p <profile> cron create`) is, same as the
            # top-level one above, its OWN dedicated archive member --
            # never nested under "hermes/<profile>/" where the generic
            # overlay step in hermes_restore.py could reach it. "cron" is
            # not in _PROFILE_INCLUDE, so the loop above never touches it;
            # this is the only place it's ever bundled.
            total_files += _add_tree(
                zf, profiles_root / profile_id / "cron" / "jobs.json", f"cron/profiles/{profile_id}/jobs.json",
            )

        # The Second Brain app's own matching data -- Registry (Agents/
        # Skills/Sections/Providers/Tools) and Pipelines, both real,
        # non-secret. Read from the REAL configured location (see
        # _resolve_second_brain_data_path), not assumed vault-relative --
        # bundled here as a convenience copy (the primary copy of this
        # data travels with the real vault folder itself, which the
        # operator copies separately) so this .sbb is self-contained even
        # before the vault is in place.
        total_files += _add_tree(zf, second_brain_data_path / "data", "second-brain-data")
        total_files += _add_tree(zf, second_brain_data_path / "pipelines", "second-brain-pipelines")

    return {
        "output": str(output_path),
        "profiles": manifest["profiles"],
        "second_brain_data_path": str(second_brain_data_path),
        "files_bundled": total_files,
        "size_bytes": output_path.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--hermes-home",
        default=os.path.expandvars(r"%LOCALAPPDATA%\hermes"),
        help="Defaults to the real, current machine's own Hermes home.",
    )
    parser.add_argument(
        "--second-brain-data-path",
        default=None,
        help="Defaults to reading SECOND_BRAIN_DATA_PATH from src/backend/.env, "
             "falling back to <vault-path>/.second-brain only if that's unset -- "
             "same resolution the backend itself uses. Override explicitly if needed.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    result = build_backup(
        Path(args.hermes_home), Path(args.vault_path), Path(args.output), repo_root,
        second_brain_data_path_override=args.second_brain_data_path,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
