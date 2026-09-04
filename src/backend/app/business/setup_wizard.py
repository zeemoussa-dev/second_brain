"""First-run setup wizard (`REQ-SB-89`) -- the steps, and the read-only
Hermes health report that one of them shows.

Exists because a fresh install used to be configured entirely by hand-
editing `.env`: the operator's own 2026-09-03 second-machine deployment was
done that way, start to finish. The field definitions, per-field checks,
`.env` write path and restart all already live in `system_settings.py`; this
module only groups those fields into an ordered set of steps and adds the
one thing that has no equivalent there -- a look at the real Hermes install.

Very nearly read-only with respect to Hermes, with ONE deliberate exception.
The original scope (operator, 2026-09-04) was "App .env + Hermes health
checks", explicitly not a variant that would provision profiles. Later the
same day the operator asked for one write: "When I set the Vault URL it need
to reflect in Hermes Obsedian COnfig data" -- so `sync_vault_path_to_hermes`
below writes `OBSIDIAN_VAULT_PATH` into Hermes' own `.env` -- and, since
2026-09-04, `SECOND_BRAIN_DATA_PATH` alongside it, because the Hermes-side
Skill scripts resolve templates and their own state under that folder and
silently broke when the operator split config out of the vault.

Everything else here still only LOOKS: nothing creates a profile, deploys a
Skill, writes a cron job, or restarts anything. That leaves applying real
config as the operator's own action, matching
`Hermes-Provisioning/README.md`'s own standing discipline.
"""
from __future__ import annotations

import time
from pathlib import Path

from app.business import system_settings
from app.config import settings

# Grouped so each step is one decision the operator can actually answer in
# one sitting, in dependency order: where the notes live and who you are,
# then the model, then the agent runtime, then things with real defaults.
_STEPS: tuple[dict, ...] = (
    {
        "id": "vault",
        "title": "Your vault & data",
        "blurb": "Where your notes live, where Second Brain keeps its own data, and which email address is yours.",
        # second_brain_data_path belongs HERE, not buried in a later
        # "change these only if you need to" step. Left blank it silently
        # becomes <vault>/.second-brain -- putting the app's own state inside
        # the vault, which is exactly the layout the operator moved away from
        # on 2026-09-03 and whose absence then broke every Skill. A default
        # that quietly picks the shape you deliberately abandoned belongs in
        # front of the operator, not behind a "usually fine" label.
        "fields": ("vault_path", "second_brain_data_path", "self_email"),
    },
    {
        "id": "compass",
        "title": "Compass (the model)",
        "blurb": "The language model Second Brain calls to classify, summarize, and answer.",
        "fields": ("compass_base_url", "compass_api_key", "compass_model"),
    },
    {
        "id": "hermes",
        "title": "Hermes",
        "blurb": "The agent runtime that does the live capture and runs the scheduled jobs. Second Brain reads it -- provisioning it stays your own step.",
        "fields": ("hermes_base_url", "hermes_home_path"),
    },
    {
        "id": "storage",
        "title": "Access",
        "blurb": "Which addresses may call this backend. The default matches the ports this repo ships with -- change it only if you run the app from somewhere else.",
        "fields": ("cors_allowed_origins",),
    },
)

# A running gateway rewrites its heartbeat every tick. The real observed
# interval is ~60s, so this leaves room for several missed ticks before
# calling it stopped rather than merely between beats.
_HEARTBEAT_STALE_AFTER_SECONDS = 300


def _field_payload(field: str) -> dict:
    meta = system_settings._FIELDS[field]
    return {
        "key": field,
        "label": meta["label"],
        "icon": meta["icon"],
        "description": meta["description"],
        "value": system_settings._display_value(field),
        "secret": bool(meta.get("secret")),
        "required": field in system_settings.REQUIRED_FOR_STARTUP,
    }


def _hermes_home() -> Path | None:
    home = settings.hermes_home_path
    return Path(home) if home else None


def _check_installed(home: Path | None) -> dict:
    if home is None or not home.is_dir():
        return {"ok": False, "detail": "No Hermes install found at that folder"}
    # The CLI is what actually provisions profiles and cron jobs; a home dir
    # without it is a half-install that fails at the first real command.
    if not (home / "bin" / "hermes.exe").is_file():
        return {"ok": False, "detail": "Folder exists, but bin/hermes.exe is missing"}
    return {"ok": True, "detail": "Installed"}


def _check_gateway(home: Path | None) -> dict:
    """Reads the cron ticker's own heartbeat file rather than asking the
    gateway over HTTP -- the gateway can be up while `hermes serve`'s REST
    port is not, and it is the SCHEDULER being alive that decides whether any
    standing pipeline actually runs."""
    if home is None:
        return {"ok": False, "detail": "Nowhere to look"}
    heartbeat = home / "cron" / "ticker_heartbeat"
    if not heartbeat.is_file():
        return {"ok": False, "detail": "Gateway has never run (no heartbeat)"}
    age_seconds = time.time() - heartbeat.stat().st_mtime
    if age_seconds > _HEARTBEAT_STALE_AFTER_SECONDS:
        return {"ok": False, "detail": f"Gateway looks stopped -- last beat {int(age_seconds // 60)} min ago"}
    return {"ok": True, "detail": "Gateway running"}


def _check_profiles(home: Path | None) -> dict:
    if home is None or not home.is_dir():
        return {"ok": False, "detail": "Nowhere to look"}
    # "default" IS the home dir itself and has no folder under profiles/
    # (app/hermes/profiles.py documents this real layout), so it is counted
    # separately or it goes missing from the total.
    profiles_dir = home / "profiles"
    named = sorted(p.name for p in profiles_dir.iterdir() if p.is_dir()) if profiles_dir.is_dir() else []
    if not named:
        return {"ok": False, "detail": "Only the default profile -- no specialist agents provisioned yet"}
    shown = ", ".join(named[:4])
    suffix = ", ..." if len(named) > 4 else ""
    return {"ok": True, "detail": f"{len(named) + 1} profiles (default, {shown}{suffix})"}


def _check_deployed_skills(home: Path | None) -> dict:
    """Counts real SKILL.md files across every profile. A profile cloned from
    `default` inherits the bundled catalogue, so a non-zero count here is not
    proof this repo's OWN Skills were copied in -- it only distinguishes "the
    skills tree exists" from "nothing was ever deployed"."""
    if home is None or not home.is_dir():
        return {"ok": False, "detail": "Nowhere to look"}
    roots = [home / "skills"]
    profiles_dir = home / "profiles"
    if profiles_dir.is_dir():
        roots += [p / "skills" for p in profiles_dir.iterdir() if p.is_dir()]
    count = sum(len(list(root.rglob("SKILL.md"))) for root in roots if root.is_dir())
    if count == 0:
        return {"ok": False, "detail": "No skills deployed"}
    return {"ok": True, "detail": f"{count} skill files deployed"}


def _check_cron_jobs(home: Path | None) -> dict:
    if home is None or not home.is_dir():
        return {"ok": False, "detail": "Nowhere to look"}
    if not (home / "cron" / "jobs.json").is_file():
        return {"ok": False, "detail": "No scheduled jobs -- standing pipelines are not running"}
    return {"ok": True, "detail": "Scheduled jobs configured"}


def _check_vault_path_agrees(home: Path | None, candidate_vault_path: str = "") -> dict:
    """Whether Hermes is pointed at the same vault the app is. This is the
    one health row the wizard CAN fix -- saving rewrites it.

    Compares against `candidate_vault_path` (what the operator has typed but
    not yet saved) when given. On a fresh install the SAVED vault path is
    still empty while they are standing on the Hermes step having just
    entered one, so reading settings here would always report "set your
    vault path first" at the exact moment they had."""
    if home is None or not home.is_dir():
        return {"ok": False, "detail": "Nowhere to look"}
    ours = _normalized_vault_path(candidate_vault_path or str(settings.vault_path or ""))
    if not ours:
        return {"ok": False, "detail": "Set your vault path first"}
    env_file = home / ".env"
    if not env_file.is_file():
        return {"ok": False, "detail": "Hermes has no .env yet — saving will create it"}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(f"{_OBSIDIAN_VAULT_ENV_KEY}="):
            theirs = _normalized_vault_path(line.split("=", 1)[1].strip())
            if theirs == ours:
                return {"ok": True, "detail": "Same vault"}
            return {"ok": False, "detail": f"Hermes points at {theirs} — saving will update it"}
    return {"ok": False, "detail": "Not set in Hermes — saving will add it"}


def _managed_env_values(env_file: Path) -> dict[str, str]:
    """Just the variables this wizard writes -- a profile is free to carry its
    own extra keys, and flagging those would be noise, not drift."""
    managed = {_OBSIDIAN_VAULT_ENV_KEY, _SB_VAULT_ENV_KEY, _DATA_PATH_ENV_KEY, _SELF_EMAIL_ENV_KEY}
    values: dict[str, str] = {}
    if not env_file.is_file():
        return values
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        if key.strip() in managed:
            values[key.strip()] = value.strip()
    return values


def _check_profile_env_drift(home: Path | None) -> dict:
    """Whether every profile agrees with the home `.env` on the paths.

    Hermes gives each profile its OWN home: `hermes_constants` puts
    HERMES_HOME at `<root>/profiles/<name>` in profile mode, and
    `env_loader.load_hermes_dotenv` then loads exactly `<that home>/.env`
    with NO chaining up to the top-level file. So the same values genuinely
    have to exist in 41 places, and nothing in Hermes notices when one of
    them falls behind -- a profile silently running against a stale vault
    path is precisely the failure this whole 2026-09-04 session was made of.
    Cheap to check, so it is checked."""
    if home is None or not home.is_dir():
        return {"ok": False, "detail": "Nowhere to look"}
    expected = _managed_env_values(home / ".env")
    if not expected:
        return {"ok": False, "detail": "Hermes' own .env carries none of these settings yet"}
    profiles_dir = home / "profiles"
    if not profiles_dir.is_dir():
        return {"ok": True, "detail": "No profiles yet -- nothing to drift"}

    stale: list[str] = []
    for profile in sorted(p for p in profiles_dir.iterdir() if p.is_dir()):
        if _managed_env_values(profile / ".env") != expected:
            stale.append(profile.name)
    if stale:
        shown = ", ".join(stale[:4])
        suffix = ", ..." if len(stale) > 4 else ""
        return {
            "ok": False,
            "detail": f"{len(stale)} profile(s) disagree with Hermes' own .env ({shown}{suffix}) -- saving re-syncs them",
        }
    return {"ok": True, "detail": f"All {len(list(profiles_dir.iterdir()))} profiles agree"}


def get_hermes_health(candidate_vault_path: str = "") -> dict:
    """Everything this wizard can honestly say about the real Hermes install.

    Reads only. The one value it will later WRITE (OBSIDIAN_VAULT_PATH) is
    reported here first, so the change is visible before it happens."""
    home = _hermes_home()
    checks = [
        {"key": "installed", "label": "Hermes installed", **_check_installed(home)},
        {"key": "gateway", "label": "Gateway (scheduler) running", **_check_gateway(home)},
        {"key": "profiles", "label": "Agent profiles", **_check_profiles(home)},
        {"key": "skills", "label": "Skills deployed", **_check_deployed_skills(home)},
        {"key": "cron", "label": "Scheduled jobs", **_check_cron_jobs(home)},
        {"key": "profile_env", "label": "Profiles agree on the paths", **_check_profile_env_drift(home)},
        {
            "key": "vault_path",
            "label": "Vault path agrees with Hermes",
            **_check_vault_path_agrees(home, candidate_vault_path),
        },
    ]
    return {
        "home_path": str(home) if home else "",
        "checks": checks,
        "all_ok": all(check["ok"] for check in checks),
        # The wizard never fixes any of this itself -- say so, so a red row
        # doesn't read as something the Next button is going to resolve.
        "read_only": True,
    }


_OBSIDIAN_VAULT_ENV_KEY = "OBSIDIAN_VAULT_PATH"
# The App Database Folder. Hermes-side Skill scripts resolve templates, the
# noise definition and the person ignore list under this; before it was
# synced they fell back to the historical <vault>/.second-brain and silently
# failed once the operator split config out of the vault (2026-09-03) --
# every email pulled between then and 2026-09-04 was consumed and never
# written. Kept in the same .env as the vault path so the two can never
# disagree about which install they describe.
_DATA_PATH_ENV_KEY = "SECOND_BRAIN_DATA_PATH"
# The Skill scripts' own established SECOND_BRAIN_* family. These are the
# names the scripts actually read -- distinct from OBSIDIAN_VAULT_PATH above,
# which is what Hermes' own BUNDLED note-taking/obsidian Skill reads. Both are
# needed; they have different consumers and neither substitutes for the other.
# Three scripts (run_delta_capture, run_full_capture, run_full_meeting_capture)
# used to default SECOND_BRAIN_VAULT_PATH to a since-deleted absolute path, so
# an unset variable meant silently operating on a folder that no longer
# exists. Pushing these here at setup is what makes that default unreachable.
_SB_VAULT_ENV_KEY = "SECOND_BRAIN_VAULT_PATH"
_SELF_EMAIL_ENV_KEY = "SECOND_BRAIN_SELF_EMAIL"


def _normalized_vault_path(raw: str) -> str:
    """Hermes stores this without a trailing separator; Second Brain's own
    VAULT_PATH conventionally carries one. Comparing them raw reports drift
    between two values that name the same folder."""
    return str(Path(raw)) if raw.strip() else ""


def _hermes_env_files_holding_the_vault_path(home: Path) -> list[Path]:
    """Hermes' home `.env` always, plus any profile `.env` that already
    declares the key.

    On a fresh install -- the case this wizard exists for -- there are no
    profiles yet, so this is exactly one file, and profiles created later
    inherit the value because `hermes profile create --clone` copies `.env`.
    Existing profiles are only touched when they ALREADY carry their own
    copy: on a re-run against a populated install, writing just the home
    file would leave every profile pinned to the old vault (40 stale copies
    on this machine, verified 2026-09-04) while the wizard reported success.
    """
    targets = [home / ".env"]
    profiles_dir = home / "profiles"
    if profiles_dir.is_dir():
        for profile in sorted(profiles_dir.iterdir()):
            env_file = profile / ".env"
            contents = env_file.read_text(encoding="utf-8") if env_file.is_file() else ""
            if any(key in contents for key in (_OBSIDIAN_VAULT_ENV_KEY, _SB_VAULT_ENV_KEY, _DATA_PATH_ENV_KEY)):
                targets.append(env_file)
    return targets


def sync_settings_to_hermes(vault_path: str, data_path: str = "", self_email: str = "") -> dict:
    """Writes the vault path into Hermes' own `.env` (operator-directed,
    2026-09-04: "When I set the Vault URL it need to reflect in Hermes
    Obsedian COnfig data").

    `OBSIDIAN_VAULT_PATH` is the documented convention Hermes' own bundled
    `note-taking/obsidian` Skill reads to find the vault; without this, a
    freshly-configured Second Brain and its agents point at different
    folders and only the app knows the right one.

    This is the ONE thing the wizard writes outside its own `.env`. It never
    creates a profile, deploys a Skill, or touches a cron job, and it never
    restarts anything -- a running gateway will not re-read `.env`, so the
    caller is told a restart is needed rather than one being performed.
    """
    normalized = _normalized_vault_path(vault_path)
    if not normalized:
        return {"ok": False, "detail": "No vault path to sync", "files_written": 0}
    updates = {_OBSIDIAN_VAULT_ENV_KEY: normalized, _SB_VAULT_ENV_KEY: normalized}
    normalized_data = _normalized_vault_path(data_path or str(settings.second_brain_data_path or ""))
    if normalized_data:
        updates[_DATA_PATH_ENV_KEY] = normalized_data
    resolved_email = (self_email or settings.self_email or "").strip()
    if resolved_email:
        updates[_SELF_EMAIL_ENV_KEY] = resolved_email
    home = _hermes_home()
    if home is None or not home.is_dir():
        return {
            "ok": False,
            "detail": "No Hermes install found — nothing to sync to",
            "files_written": 0,
        }
    targets = _hermes_env_files_holding_the_vault_path(home)
    written: list[str] = []
    for env_file in targets:
        try:
            system_settings.write_env_updates_to(env_file, updates)
            written.append(str(env_file))
        except OSError as exc:
            return {
                "ok": False,
                "detail": f"Wrote {len(written)} file(s), then failed on {env_file}: {exc}",
                "files_written": len(written),
            }
    profile_count = len(written) - 1
    detail = f"{len(updates)} settings written to Hermes ({len(written)} file{'s' if len(written) != 1 else ''}"
    detail += f", including {profile_count} profile{'s' if profile_count != 1 else ''})" if profile_count else ")"
    return {
        "ok": True,
        "detail": detail,
        "files_written": len(written),
        "restart_required": True,
    }


def get_setup_status() -> dict:
    return {
        "setup_required": settings.setup_required,
        "missing": settings.missing_required_settings,
        "steps": [
            {
                "id": step["id"],
                "title": step["title"],
                "blurb": step["blurb"],
                "fields": [_field_payload(field) for field in step["fields"]],
            }
            for step in _STEPS
        ],
    }
