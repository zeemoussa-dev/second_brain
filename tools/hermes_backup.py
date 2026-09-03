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
Every real TEXT file's own content (a SKILL.md example command, a cron
job's own prompt, ...) has the real vault path/Hermes home/second-brain-
data path substituted for a fixed placeholder token BEFORE it's written
into the zip (see `_substitute_placeholders`) -- `hermes_restore.py`
substitutes the placeholders back for its OWN real, resolved target paths
on the way out, never needing to know this machine's own source values.
A `manifest.json` at the root records the real `source_*` path values
too, but purely as informational metadata for a human inspecting the
archive -- restore's own substitution never reads them.

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

# Placeholder tokens, not literal old-path string rewriting -- operator,
# 2026-09-03: "C:\myWorx\Moussa MD\Moussa Brain should be a place holder
# and pass it on Restore and same for the other Path". A real, live bug
# was found testing the previous "rewrite old absolute path -> new
# absolute path" design (hermes_restore.py's own _rewrite_path_refs):
# when second_brain_data_path is vault-relative on the source machine (the
# common case), it's a LONGER string that CONTAINS the vault path as a
# literal prefix -- rewriting the vault path first silently consumed that
# shared prefix, leaving the data-path rewrite nothing left to find, and
# restore fell back to the wrong (vault-relative) target location instead
# of the real, resolved one. Placeholders have no such overlap risk by
# construction (three fixed, distinct, never-colliding tokens) and don't
# require restore to even know the source values -- only the target's own
# real, resolved paths. Chosen format: unlikely to collide with anything
# a real Skill/config file would ever legitimately contain (no valid
# Windows path, no real JSON key, no real prose sentence looks like this).
_PLACEHOLDER_VAULT_PATH = "@@SECOND_BRAIN_VAULT_PATH@@"
_PLACEHOLDER_HERMES_HOME = "@@SECOND_BRAIN_HERMES_HOME@@"
_PLACEHOLDER_DATA_PATH = "@@SECOND_BRAIN_DATA_PATH@@"

_TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt"}


def _substitute_both_forms(text: str, real_value: str, placeholder: str) -> str:
    """Replaces every real occurrence of real_value with placeholder, in
    both its raw form and its JSON-double-backslash-escaped form (a
    Windows path embedded in a JSON string value always carries doubled
    backslashes) -- mirrors hermes_restore.py's own _replace_both_forms
    exactly (duplicated, not imported, matching this tool-pair's own
    established no-shared-import convention)."""
    text = text.replace(real_value, placeholder)
    text = text.replace(real_value.replace("\\", "\\\\"), placeholder)
    return text


def _substitute_placeholders(text: str, vault_path: Path, hermes_home: Path, second_brain_data_path: Path) -> str:
    """Order matters: the LONGEST/most-specific real value must be
    substituted first. second_brain_data_path is either unrelated to the
    vault path entirely, or (the common case) vault-relative -- a real
    string that literally CONTAINS the vault path as its own prefix.
    Substituting the vault path first would consume that shared prefix
    and leave nothing left for the data-path substitution to match
    (found live testing the OLDER rewrite-based design this replaced)."""
    data_str, vault_str, hermes_str = str(second_brain_data_path), str(vault_path), str(hermes_home)
    if data_str != vault_str:
        text = _substitute_both_forms(text, data_str, _PLACEHOLDER_DATA_PATH)
    text = _substitute_both_forms(text, vault_str, _PLACEHOLDER_VAULT_PATH)
    text = _substitute_both_forms(text, hermes_str, _PLACEHOLDER_HERMES_HOME)
    return text

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
    # The curator's own skill rollback/restore-point history (`hermes
    # curator restore`/`rollback`) -- top-level only, no per-profile
    # equivalent. Tiny (real size: 109 KB) and explicitly recoverable
    # data per the curator's own "Archives are recoverable" design;
    # operator's own explicit call, 2026-09-03, over leaving it out for
    # consistency with the deliberate non-canonical-skill exclusion
    # elsewhere in this tool (a real, considered tradeoff, not an
    # oversight either way).
    ".curator_backups",
]
# Per-profile "_disabled-skills*" staging folders -- name varies per
# profile (e.g. "_disabled-skills", "_disabled-skills-unused-by-files-manager"),
# so these are discovered by prefix match, not a fixed list.
_DISABLED_SKILLS_PREFIX = "_disabled-skills"


_SECOND_BRAIN_DATA_ROOT_EXCLUDE = {"index", "email_staging"}


def _is_excluded_second_brain_root(path: Path, root: Path) -> bool:
    """Applied only to the top-level children of second_brain_data_path
    itself, not the whole subtree.

    `index/` (real size, 3.7 MB, but fully regenerable via the
    `vault-index` Skill, same "don't bundle a real cache with zero unique
    content" reasoning already applied to Hermes' own `.hub/`).

    `email_staging/` -- found live, operator: "Now Email Staging Caused
    an Error" during a real restore/validation. Root cause: its own
    folder-naming convention is the RAW Outlook EntryID (130+ hex chars),
    and "email_staging/<id>/attachments/" alone, once nested inside a
    real restore scratch path ("%TEMP%/second-brain-restore-XXXXXXXX/
    second-brain-data-root/email_staging/<id>/attachments"), measured
    263 characters -- past Windows' 260-char MAX_PATH -- with a real
    attachment filename inside pushing it further still; `zipfile.
    extractall()` fails outright on a path like this (the same class of
    error hit independently earlier this same session auditing a backup
    archive's own extracted content). Confirmed genuinely safe to drop
    entirely, not just a risk/reward tradeoff like `.curator_backups`
    below: NO real script anywhere (this repo's own canonical Skills, the
    backend, or any real deployed Hermes profile) reads or writes this
    folder at all, and its own real content is stale (last touched
    2026-08-23, 11+ days before this fix, zero activity since) --
    orphaned data from a retired capture mechanism, not live state.

    `Settings/` is DELIBERATELY NOT excluded -- an earlier version of
    this tool excluded it entirely, on a real misunderstanding: the
    operator's own "Secrets is what i meant with settings" (MEMORY.md,
    2026-09-03) meant literal secret files, never the real, curated
    `Settings/` folder itself (Entities.md, Tag Taxonomy.md, Buying
    Signals.md, Volatile Facts.md, ...) -- corrected live, same day,
    operator: "Settings Shouldn't be excluded only .env files is what I
    meant by Settings." A literal `.env` file is guarded against
    separately (see `_is_excluded`'s own `.env` check) rather than by
    excluding the whole folder it might theoretically live in."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    return rel.parts and rel.parts[0] in _SECOND_BRAIN_DATA_ROOT_EXCLUDE


def _is_excluded(path: Path) -> bool:
    """__pycache__/*.pyc(.pyo) is real, live-found bloat -- Python-
    version-specific compiled bytecode (cpython-311 vs cpython-314
    mismatches observed live this same session), fully regenerable, zero
    business content. Never bundled. Same for ".hub/" -- Hermes' own
    internal skill-search index cache (found live: a single
    "hermes-index.json" per profile, 39.6 MB, byte-for-byte near-
    identical across all 40 real profiles -- the actual cause of a
    ~400 MB archive the operator rightly questioned; regenerates itself,
    zero business content, same as __pycache__). `*.lock`/`*.pid` was
    already documented as excluded (this module's own docstring), but
    that was only ever true for a lock file living OUTSIDE every included
    subtree -- one living INSIDE an included folder (`memories/MEMORY.md
    .lock`/`USER.md.lock`, real, found live, operator: "Shouldn't be
    included in a backup") rode along regardless, since the docstring's
    claim was never actually enforced at this level. A lock is real,
    process-local concurrency state -- meaningless (or actively
    misleading, if stale) on a different machine; excluded here now,
    matching what was always the real intent."""
    if "__pycache__" in path.parts or ".hub" in path.parts:
        return True
    if path.suffix in (".pyc", ".pyo", ".lock", ".pid"):
        return True
    # A literal secret file, wherever it might appear -- belt-and-
    # suspenders alongside the deliberate exclusion of the KNOWN real
    # secret locations (top-level/per-profile .env, auth.json/.lock,
    # channel_directory.json) elsewhere in this module; this catches an
    # ".env"-NAMED file anywhere else this tool ever walks, including
    # inside second_brain_data_path's own now-wholesale-included tree.
    return path.name == ".env" or path.name.startswith(".env.")


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


def _write_member(zf: zipfile.ZipFile, src: Path, arcname: str, ctx: "_PathContext") -> None:
    """The one place a real file's bytes actually enter the zip. A real
    TEXT file (.md/.json/.yaml/.yml/.py/.txt) gets read, placeholder-
    substituted (see _substitute_placeholders), then written via
    writestr; anything else (a profile tarball, a curator blob, binary
    content in general) is written as-is via zf.write -- substitution is
    never attempted on bytes that aren't real text."""
    if src.suffix.lower() in _TEXT_SUFFIXES:
        try:
            text = src.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            zf.write(src, arcname)
            return
        zf.writestr(arcname, _substitute_placeholders(text, ctx.vault_path, ctx.hermes_home, ctx.second_brain_data_path))
    else:
        zf.write(src, arcname)


class _PathContext:
    """The three real, resolved source paths every bundled text file's
    own content gets checked against -- threaded through every _add_*
    call rather than read from a global, so build_backup's own real
    inputs stay the only source of truth."""

    def __init__(self, vault_path: Path, hermes_home: Path, second_brain_data_path: Path):
        self.vault_path = vault_path
        self.hermes_home = hermes_home
        self.second_brain_data_path = second_brain_data_path


def _add_canonical_skills(zf: zipfile.ZipFile, skills_root: Path, canonical_ids: set[str], arc_prefix: str, ctx: _PathContext) -> int:
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
            count += _add_tree(zf, skill_dir, f"{arc_prefix}/{category_dir.name}/{skill_dir.name}", ctx)
    return count


def _add_second_brain_data_root(zf: zipfile.ZipFile, root: Path, arc_prefix: str, ctx: _PathContext) -> int:
    """Wholesale walk of the app's own real second_brain_data_path root
    (everything directly under it -- agent_visuals.json/agent_sections.json/
    agent_schedules.json/cockpit_chat.json/email_staging/tools/... plus
    the already-known data/ and pipelines/ subtrees), not a hand-picked
    list of subfolders. Found live, 2026-09-03, operator: "agent_sections.json
    is not included" then "The Data that is in the root is needed as well"
    -- a real, substantial set of loose top-level config/data files (18+,
    not just the one flagged) sat outside the two specific data/pipelines
    _add_tree calls this replaced, silently missed every single time.
    Deliberately a wholesale walk, not a growing allowlist, so the NEXT
    new file this app ever writes at this root travels automatically --
    same lesson as this tool's own earlier canonical-skill-id derivation.
    Excludes only index/ (see _is_excluded_second_brain_root's own
    docstring)."""
    if not root.exists():
        return 0
    count = 0
    for path in root.rglob("*"):
        if not path.is_file() or _is_excluded(path) or _is_excluded_second_brain_root(path, root):
            continue
        arcname = f"{arc_prefix}/{path.relative_to(root).as_posix()}"
        _write_member(zf, path, arcname, ctx)
        count += 1
    return count


def _add_tree(zf: zipfile.ZipFile, src: Path, arc_prefix: str, ctx: _PathContext) -> int:
    """Adds every real file under src into the zip under arc_prefix,
    preserving the real relative structure. Returns the count of files
    added; 0 (no error) if src doesn't exist -- an optional real path
    (e.g. a profile with no memories/ yet) is not a failure."""
    if not src.exists():
        return 0
    if src.is_file():
        _write_member(zf, src, arc_prefix, ctx)
        return 1
    count = 0
    for path in src.rglob("*"):
        if not path.is_file() or _is_excluded(path):
            continue
        arcname = f"{arc_prefix}/{path.relative_to(src).as_posix()}"
        _write_member(zf, path, arcname, ctx)
        count += 1
    return count


def _add_profile(zf: zipfile.ZipFile, profile_root: Path, profile_id: str, extra_include: list[str], canonical_skill_ids: set[str], ctx: _PathContext) -> int:
    count = 0
    for rel in _PROFILE_INCLUDE + extra_include:
        count += _add_tree(zf, profile_root / rel, f"hermes/{profile_id}/{rel}", ctx)
    count += _add_canonical_skills(zf, profile_root / "skills", canonical_skill_ids, f"hermes/{profile_id}/skills", ctx)
    for child in profile_root.iterdir():
        if child.is_dir() and child.name.startswith(_DISABLED_SKILLS_PREFIX):
            count += _add_canonical_skills(zf, child, canonical_skill_ids, f"hermes/{profile_id}/{child.name}", ctx)
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
    ctx = _PathContext(vault_path, hermes_home, second_brain_data_path)

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
        total_files += _add_profile(zf, hermes_home, "default", _TOP_LEVEL_EXTRA_INCLUDE, canonical_skill_ids, ctx)

        # A DELIBERATELY SEPARATE top-level archive member, not nested
        # under "hermes/default/" -- see _TOP_LEVEL_EXTRA_INCLUDE's own
        # comment for why. hermes_restore.py's dedicated merge-by-id cron
        # logic is the only code path that ever reads this member.
        total_files += _add_tree(zf, hermes_home / "cron" / "jobs.json", "cron/jobs.json", ctx)

        for profile_id in profile_ids:
            total_files += _add_profile(zf, profiles_root / profile_id, profile_id, [], canonical_skill_ids, ctx)
            # A profile's own cron/jobs.json (real once that profile has
            # ever run `hermes -p <profile> cron create`) is, same as the
            # top-level one above, its OWN dedicated archive member --
            # never nested under "hermes/<profile>/" where the generic
            # overlay step in hermes_restore.py could reach it. "cron" is
            # not in _PROFILE_INCLUDE, so the loop above never touches it;
            # this is the only place it's ever bundled.
            total_files += _add_tree(
                zf, profiles_root / profile_id / "cron" / "jobs.json", f"cron/profiles/{profile_id}/jobs.json", ctx,
            )

        # The Second Brain app's own matching data -- EVERYTHING real at
        # the second_brain_data_path root (Registry data/, Pipelines/,
        # and every loose top-level file: agent_visuals.json,
        # agent_sections.json, agent_schedules.json, cockpit_chat.json,
        # email_staging/, tools/registry.json, ...), except Settings/ and
        # index/ (see _add_second_brain_data_root's own docstring for
        # why this is a wholesale walk, not a hand-picked subfolder
        # list). Read from the REAL configured location (see
        # _resolve_second_brain_data_path), not assumed vault-relative --
        # bundled here as a convenience copy (the primary copy of this
        # data travels with the real vault folder itself, which the
        # operator copies separately) so this .sbb is self-contained even
        # before the vault is in place.
        total_files += _add_second_brain_data_root(zf, second_brain_data_path, "second-brain-data-root", ctx)

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
