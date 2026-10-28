"""REQ-SB-89 -- the first-run setup wizard.

The behaviour that matters most here is the one that used to be impossible:
a fresh install with no .env must still IMPORT, still serve, and still be
able to describe what it is missing. Before this, `app.config` raised a
pydantic ValidationError at module scope and nothing below ever ran.
"""
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import frontend_dist
from app.business import setup_wizard, system_settings
from app.config import REQUIRED_FOR_STARTUP, settings
from app.main import app

client = TestClient(app)


@pytest.fixture
def unconfigured(monkeypatch):
    """Puts the real settings object into the state a fresh install has."""
    for field in REQUIRED_FOR_STARTUP:
        monkeypatch.setattr(settings, field, None if field == "vault_path" else "")
    return settings


def test_missing_settings_are_reported_not_raised(unconfigured) -> None:
    assert unconfigured.setup_required is True
    assert set(unconfigured.missing_required_settings) == set(REQUIRED_FOR_STARTUP)


def test_a_configured_install_is_not_in_setup_mode(monkeypatch) -> None:
    """Guards against the wizard hijacking an install that already works.

    Values are set explicitly rather than read from the ambient .env: pydantic
    resolves `env_file=".env"` relative to the CWD, so asserting against the
    real file passed under `pytest` from src/backend and failed from the repo
    root -- a test that depends on where it is run from is worse than no test.
    """
    for field in REQUIRED_FOR_STARTUP:
        monkeypatch.setattr(settings, field, Path("C:/vault") if field == "vault_path" else "set")

    assert settings.setup_required is False
    assert settings.missing_required_settings == []


def test_setup_status_is_served_while_unconfigured(unconfigured) -> None:
    response = client.get("/setup/status")

    assert response.status_code == 200
    body = response.json()
    assert body["setup_required"] is True
    assert [step["id"] for step in body["steps"]] == ["vault", "compass", "hermes", "storage"]
    # Every field that blocks startup must actually appear in some step, or
    # the wizard cannot possibly clear setup mode.
    offered = {field["key"] for step in body["steps"] for field in step["fields"]}
    assert set(REQUIRED_FOR_STARTUP) <= offered


def test_an_install_with_nowhere_to_keep_users_has_none(monkeypatch) -> None:
    """The real fresh-install state: no App Database Folder yet.

    Resolving the user store then raises instead of answering "no users", and
    the guard's fail-closed branch turned that into "this install is
    bootstrapped" -- which refused `/setup`, the one route a fresh install must
    reach. The boot screen read that 401 as "setup not needed" and polled
    forever for a boot that setup mode had deliberately not started, so a new
    install never got to a usable screen (found live, 2026-10-24).

    Asserted against the reader rather than through `client`: the app's
    middleware binds its UserManager at import, when the data path is still the
    sandbox conftest gave it, so a request would never see this state.
    """
    from app.api import auth_guard

    monkeypatch.setattr(settings, "second_brain_data_path", None)

    assert auth_guard._AuthenticationReader().has_any_user() is False


def test_an_unreadable_user_store_still_fails_closed(monkeypatch, tmp_path: Path) -> None:
    """The fix must not widen into "any failure opens setup".

    A CONFIGURED install whose user store cannot be read is a different case:
    it may well have users, so the setup routes stay shut.
    """
    from app.api import auth_guard

    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    reader = auth_guard._AuthenticationReader()
    monkeypatch.setattr(
        reader._users, "has_any_user", lambda: (_ for _ in ()).throw(OSError("store unreadable"))
    )

    assert reader.has_any_user() is True


def test_other_routes_are_refused_while_unconfigured(unconfigured) -> None:
    response = client.get("/vault/notes")

    assert response.status_code == 503
    assert response.json()["setup_required"] is True


def test_health_and_boot_stay_open_while_unconfigured(unconfigured) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/boot-status").status_code == 200


def test_compass_url_missing_the_endpoint_is_rejected() -> None:
    # data_access/compass_client.py POSTs to this URL verbatim, so a bare
    # host 404s at first real use rather than at setup.
    assert system_settings.validate_candidate("compass_base_url", "https://api.core42.ai")["ok"] is False
    assert system_settings.validate_candidate(
        "compass_base_url", "https://api.core42.ai/v1/chat/completions"
    )["ok"] is True


def test_vault_folder_check_rejects_a_path_that_does_not_exist(tmp_path: Path) -> None:
    assert system_settings.validate_candidate("vault_path", str(tmp_path / "nope"))["ok"] is False
    assert system_settings.validate_candidate("vault_path", str(tmp_path))["ok"] is True


def test_secret_is_masked_on_read_and_never_written_back(monkeypatch, tmp_path: Path) -> None:
    """A UI that submits a whole form round-trips the mask for any secret the
    operator did not touch -- writing that through would replace a working
    key with bullet characters."""
    monkeypatch.setattr(settings, "compass_api_key", "a-real-key")
    assert system_settings._display_value("compass_api_key") == system_settings.SECRET_MASK

    env_file = tmp_path / ".env"
    env_file.write_text("COMPASS_API_KEY=a-real-key\n", encoding="utf-8")
    monkeypatch.setattr(system_settings, "_ENV_PATH", env_file)

    result = system_settings.update_system_settings({"compass_api_key": system_settings.SECRET_MASK})

    assert result["restart_required"] is False
    assert "a-real-key" in env_file.read_text(encoding="utf-8")
    assert system_settings.SECRET_MASK not in env_file.read_text(encoding="utf-8")


def test_a_real_value_does_reach_the_env_file(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SELF_EMAIL=old@example.com\n", encoding="utf-8")
    monkeypatch.setattr(system_settings, "_ENV_PATH", env_file)

    system_settings.update_system_settings({"self_email": "new@example.com"})

    assert "SELF_EMAIL=new@example.com" in env_file.read_text(encoding="utf-8")


def test_hermes_health_reports_a_missing_install_without_raising(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "hermes_home_path", tmp_path / "not-installed")

    health = setup_wizard.get_hermes_health()

    assert health["all_ok"] is False
    assert health["read_only"] is True
    assert {check["key"] for check in health["checks"]} == {
        "installed",
        "gateway",
        "profiles",
        "skills",
        "cron",
        "profile_env",
        "vault_path",
    }


def _fake_hermes_home(tmp_path: Path, *, vault: str | None, profiles: dict[str, str] | None = None) -> Path:
    home = tmp_path / "hermes"
    (home / "bin").mkdir(parents=True)
    (home / "bin" / "hermes.exe").write_text("", encoding="utf-8")
    if vault is not None:
        (home / ".env").write_text(
            f"# Hermes env\nOBSIDIAN_VAULT_PATH={vault}\nOTHER_KEY=keep-me\n", encoding="utf-8"
        )
    for name, profile_vault in (profiles or {}).items():
        profile = home / "profiles" / name
        profile.mkdir(parents=True)
        (profile / ".env").write_text(f"OBSIDIAN_VAULT_PATH={profile_vault}\n", encoding="utf-8")
    return home


def test_vault_path_is_written_into_hermes_env(monkeypatch, tmp_path: Path) -> None:
    home = _fake_hermes_home(tmp_path, vault=r"C:\old\vault")
    monkeypatch.setattr(settings, "hermes_home_path", home)
    # This install is the one Hermes is already serving -- it is moving its own
    # vault, which is an ordinary save and not a takeover of somebody else's
    # agents. Without this the conflict guard cannot tell the two apart.
    monkeypatch.setattr(settings, "vault_path", Path(r"C:\old\vault"))

    result = setup_wizard.sync_settings_to_hermes(r"C:\new\vault")

    assert result["ok"] is True
    assert result["restart_required"] is True
    written = (home / ".env").read_text(encoding="utf-8")
    assert r"OBSIDIAN_VAULT_PATH=C:\new\vault" in written
    # Unrelated keys and comments must survive -- this is a live Hermes file.
    assert "OTHER_KEY=keep-me" in written
    assert "# Hermes env" in written


def test_a_fresh_install_syncs_exactly_one_file(monkeypatch, tmp_path: Path) -> None:
    """The operator's own point: a new setup has no profiles yet, so this is
    one file, and later `hermes profile create --clone` copies it onward."""
    home = _fake_hermes_home(tmp_path, vault=None)
    monkeypatch.setattr(settings, "hermes_home_path", home)

    result = setup_wizard.sync_settings_to_hermes(r"C:\new\vault")

    assert result["files_written"] == 1
    assert r"OBSIDIAN_VAULT_PATH=C:\new\vault" in (home / ".env").read_text(encoding="utf-8")


def test_existing_profiles_are_not_left_pinned_to_the_old_vault(monkeypatch, tmp_path: Path) -> None:
    home = _fake_hermes_home(
        tmp_path, vault=r"C:\old\vault", profiles={"opp-manager": r"C:\old\vault", "research-agent": r"C:\old\vault"}
    )
    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "vault_path", Path(r"C:\old\vault"))

    result = setup_wizard.sync_settings_to_hermes(r"C:\new\vault")

    assert result["files_written"] == 3
    for name in ("opp-manager", "research-agent"):
        assert r"OBSIDIAN_VAULT_PATH=C:\new\vault" in (
            home / "profiles" / name / ".env"
        ).read_text(encoding="utf-8")


def test_sync_reports_rather_than_raises_when_hermes_is_absent(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "hermes_home_path", tmp_path / "no-hermes-here")

    result = setup_wizard.sync_settings_to_hermes(r"C:\new\vault")

    assert result["ok"] is False
    assert result["files_written"] == 0


def test_trailing_separator_is_not_reported_as_drift(monkeypatch, tmp_path: Path) -> None:
    """Second Brain's VAULT_PATH conventionally ends in a separator and
    Hermes' does not -- the same folder must not read as a mismatch."""
    home = _fake_hermes_home(tmp_path, vault=r"C:\the\vault")
    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "vault_path", Path(r"C:\the\vault" + "\\"))

    agrees = setup_wizard._check_vault_path_agrees(home)

    assert agrees["ok"] is True


def test_drift_is_reported_on_the_hermes_step(monkeypatch, tmp_path: Path) -> None:
    home = _fake_hermes_home(tmp_path, vault=r"C:\somewhere\else")
    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "vault_path", Path(r"C:\the\vault"))

    agrees = setup_wizard._check_vault_path_agrees(home)

    assert agrees["ok"] is False
    assert "somewhere" in agrees["detail"]


def test_data_path_is_synced_alongside_the_vault_path(monkeypatch, tmp_path: Path) -> None:
    """The Hermes-side Skill scripts resolve templates and their own state
    under SECOND_BRAIN_DATA_PATH. Before it was synced they fell back to the
    historical <vault>/.second-brain and silently dropped every email once
    the operator split config out of the vault."""
    home = _fake_hermes_home(tmp_path, vault=r"C:\old\vault")
    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "vault_path", Path(r"C:\old\vault"))

    setup_wizard.sync_settings_to_hermes(r"C:\new\vault", r"C:\somewhere\config")

    written = (home / ".env").read_text(encoding="utf-8")
    assert r"OBSIDIAN_VAULT_PATH=C:\new\vault" in written
    assert r"SECOND_BRAIN_DATA_PATH=C:\somewhere\config" in written


def test_data_path_falls_back_to_the_configured_setting(monkeypatch, tmp_path: Path) -> None:
    home = _fake_hermes_home(tmp_path, vault=r"C:\old\vault")
    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "second_brain_data_path", Path(r"C:\configured\data"))
    monkeypatch.setattr(settings, "vault_path", Path(r"C:\old\vault"))

    setup_wizard.sync_settings_to_hermes(r"C:\new\vault")

    assert r"SECOND_BRAIN_DATA_PATH=C:\configured\data" in (home / ".env").read_text(encoding="utf-8")


def _hermes_home_with_profiles(tmp_path: Path, home_env: str, profile_envs: dict[str, str]) -> Path:
    home = tmp_path / "hermes"
    (home / "bin").mkdir(parents=True)
    (home / "bin" / "hermes.exe").write_text("", encoding="utf-8")
    (home / ".env").write_text(home_env, encoding="utf-8")
    for name, contents in profile_envs.items():
        profile = home / "profiles" / name
        profile.mkdir(parents=True)
        (profile / ".env").write_text(contents, encoding="utf-8")
    return home


_HOME_ENV = (
    "OBSIDIAN_VAULT_PATH=C:\vault\n"
    "SECOND_BRAIN_VAULT_PATH=C:\vault\n"
    "SECOND_BRAIN_DATA_PATH=C:\config\n"
    "SECOND_BRAIN_SELF_EMAIL=me@example.com\n"
)


def test_profiles_matching_the_home_env_are_not_flagged(monkeypatch, tmp_path: Path) -> None:
    home = _hermes_home_with_profiles(tmp_path, _HOME_ENV, {"a": _HOME_ENV, "b": _HOME_ENV})
    monkeypatch.setattr(settings, "hermes_home_path", home)

    assert setup_wizard._check_profile_env_drift(home)["ok"] is True


def test_a_profile_left_on_a_stale_path_is_flagged(monkeypatch, tmp_path: Path) -> None:
    """Hermes gives each profile its own HERMES_HOME and loads only that
    profile's .env -- no chaining to the top-level file -- so a profile can sit
    on a stale vault path indefinitely with nothing noticing."""
    stale = _HOME_ENV.replace("C:\vault", "C:\old-vault")
    home = _hermes_home_with_profiles(tmp_path, _HOME_ENV, {"current": _HOME_ENV, "behind": stale})
    monkeypatch.setattr(settings, "hermes_home_path", home)

    result = setup_wizard._check_profile_env_drift(home)

    assert result["ok"] is False
    assert "behind" in result["detail"]
    assert "current" not in result["detail"]


def test_a_profile_missing_the_settings_entirely_is_flagged(monkeypatch, tmp_path: Path) -> None:
    """The state a restore leaves behind: backup excludes every .env, so a
    restored profile has none at all."""
    home = _hermes_home_with_profiles(tmp_path, _HOME_ENV, {"restored": "OTHER_KEY=x\n"})
    monkeypatch.setattr(settings, "hermes_home_path", home)

    assert setup_wizard._check_profile_env_drift(home)["ok"] is False


def test_extra_profile_keys_are_not_treated_as_drift(monkeypatch, tmp_path: Path) -> None:
    """Only the variables the wizard manages are compared -- a profile is
    free to carry its own extras, and flagging those would be noise."""
    home = _hermes_home_with_profiles(tmp_path, _HOME_ENV, {"a": _HOME_ENV + "PROFILE_ONLY=yes\n"})
    monkeypatch.setattr(settings, "hermes_home_path", home)

    assert setup_wizard._check_profile_env_drift(home)["ok"] is True


def test_no_profiles_yet_is_not_drift(monkeypatch, tmp_path: Path) -> None:
    home = _hermes_home_with_profiles(tmp_path, _HOME_ENV, {})
    monkeypatch.setattr(settings, "hermes_home_path", home)

    assert setup_wizard._check_profile_env_drift(home)["ok"] is True


# BUG-072: deleting an Agent made Hermes tombstone it into profiles/.deleted/,
# and every check here then counted `.deleted` as a profile -- one more in the
# total, and a failed path-agreement check that "saving" would have answered by
# writing settings into the tombstone. The Skill count is asserted too, so a
# tombstone's Skills never start counting as deployed.
def test_the_deleted_profiles_tombstone_is_not_a_profile(monkeypatch, tmp_path: Path) -> None:
    home = _hermes_home_with_profiles(tmp_path, _HOME_ENV, {"a": _HOME_ENV})
    (home / "profiles" / "a" / "skills" / "vault" / "kept").mkdir(parents=True)
    (home / "profiles" / "a" / "skills" / "vault" / "kept" / "SKILL.md").write_text("", encoding="utf-8")
    tombstoned = home / "profiles" / ".deleted" / "gone" / "skills" / "vault" / "old"
    tombstoned.mkdir(parents=True)
    (tombstoned / "SKILL.md").write_text("", encoding="utf-8")
    (home / "profiles" / ".deleted" / "gone" / ".env").write_text(
        _HOME_ENV.replace("C:\vault", "C:\old-vault"), encoding="utf-8")
    monkeypatch.setattr(settings, "hermes_home_path", home)

    assert setup_wizard._check_profile_env_drift(home) == {"ok": True, "detail": "All 1 profiles agree"}
    assert ".deleted" not in setup_wizard._check_profiles(home)["detail"]
    assert setup_wizard._check_profiles(home)["detail"].startswith("2 profiles")
    assert "1 skill" in setup_wizard._check_deployed_skills(home)["detail"]
    assert all(".deleted" not in str(path) for path in setup_wizard._hermes_env_files_holding_the_vault_path(home))


def test_the_data_folder_is_offered_beside_the_vault(unconfigured) -> None:
    """Not buried in a later "change these only if you need to" step.

    Left blank, `second_brain_data_path` silently becomes
    <vault>/.second-brain -- putting the app's own state back inside the
    vault, the exact layout the 2026-09-03 split moved away from and whose
    absence then broke every Hermes-side Skill. A default that quietly picks
    the shape you deliberately abandoned has to be visible.
    """
    body = client.get("/setup/status").json()
    vault_step = next(s for s in body["steps"] if s["id"] == "vault")
    keys = [f["key"] for f in vault_step["fields"]]

    assert "second_brain_data_path" in keys
    assert keys.index("second_brain_data_path") == keys.index("vault_path") + 1


def test_the_data_folder_says_what_leaving_it_blank_does(unconfigured) -> None:
    body = client.get("/setup/status").json()
    field = next(
        f for s in body["steps"] for f in s["fields"] if f["key"] == "second_brain_data_path"
    )

    assert "BLANK" in field["description"]
    assert ".second-brain" in field["description"]


def test_a_restart_can_be_asked_for_from_a_plain_sync_route(monkeypatch, tmp_path) -> None:
    """The wizard's "Restart now" is accepted, and acted on.

    It used to answer 500, for a reason worth keeping a test for: the route is
    a plain `def`, so FastAPI serves it from the threadpool where there is no
    running event loop, and the old code scheduled its work with
    `asyncio.create_task`, which raises there. Nothing noticed, because the
    frontend read a failed restart request as the backend going away -- so the
    operator's settings were ignored and they reported the SAVE as broken
    (2026-10-24).
    """
    monkeypatch.chdir(tmp_path)
    spawned: list[list[str]] = []
    monkeypatch.setattr(
        system_settings.subprocess, "Popen", lambda argv, **kwargs: spawned.append(argv)
    )
    monkeypatch.setattr(system_settings, "_raise_terminate", lambda: None)

    response = client.post("/setup/restart")

    assert response.status_code == 200
    assert response.json()["restarting"] is system_settings.launcher_is_available()
    assert spawned, "the restart was accepted but nothing was ever started"


def test_the_restart_helper_outlives_the_app_it_restarts(monkeypatch, tmp_path) -> None:
    """It restarts us by KILLING us, so it cannot be our own child.

    `backend.ps1` collects every child of a backend process -- that is how it
    finds reload workers -- so a helper spawned directly would be stopped
    halfway through its own stop, leaving the app down. Going through
    `cmd /c start` leaves it parented to a shell that has already exited.
    """
    spawned: list[list[str]] = []
    monkeypatch.setattr(
        system_settings.subprocess, "Popen", lambda argv, **kwargs: spawned.append(argv)
    )

    system_settings.request_restart()

    argv = spawned[0]
    assert argv[:3] == ["cmd", "/c", "start"]
    assert "backend.ps1' restart" in argv[-1]
    assert "Start-Sleep" in argv[-1], "the response must get out before we are killed"


def test_shutting_down_stops_the_whole_tree_not_just_this_process(monkeypatch) -> None:
    """Settings > System's Shut down had the same defect as Restart.

    A self-raised SIGTERM ends the --reload WORKER and leaves the reloader
    holding the port with nothing serving: neither up nor down, and the exact
    state Shut down exists to avoid. It goes through the launcher's `stop` --
    and `stop`, not `restart`: this one is meant to leave the app down.
    """
    spawned: list[list[str]] = []
    monkeypatch.setattr(
        system_settings.subprocess, "Popen", lambda argv, **kwargs: spawned.append(argv)
    )

    system_settings.request_shutdown()

    assert "backend.ps1' stop" in spawned[0][-1]


def test_an_install_with_no_launcher_still_stops(monkeypatch) -> None:
    """All a bare `uvicorn app.main:app` can do is end itself, so that is what
    it does -- on a thread, because the routes calling this are plain `def` and
    the threadpool they run on has no event loop to schedule on."""
    monkeypatch.setattr(system_settings, "launcher_is_available", lambda: False)
    terminated = threading.Event()
    monkeypatch.setattr(system_settings, "_raise_terminate", terminated.set)

    system_settings.request_shutdown()

    assert terminated.wait(timeout=5), "the shutdown was accepted but never scheduled"


def test_hermes_left_blank_is_not_a_failure(unconfigured, monkeypatch) -> None:
    """An install with no agent runtime is complete, not broken.

    Checking a blank setting anyway made `Path("")` "Folder does not exist" and
    an empty URL "Unreachable" -- two permanent red rows on a correct install,
    and in the wizard a failed check blocks Next, so "optional" was not
    actually optional.
    """
    monkeypatch.setattr(settings, "hermes_home_path", "")
    monkeypatch.setattr(settings, "hermes_base_url", "")

    for field in ("hermes_home_path", "hermes_base_url"):
        status = system_settings._run_check(field)
        assert status["ok"] is True, f"{field} blank reads as broken: {status['detail']}"
        assert status["optional"] is True


def test_no_hermes_configured_means_nothing_to_report(monkeypatch) -> None:
    """Rather than seven red rows about something nobody asked for."""
    monkeypatch.setattr(settings, "hermes_home_path", "")

    health = setup_wizard.get_hermes_health()

    assert health["configured"] is False
    assert health["checks"] == []
    assert health["all_ok"] is True


def test_saving_without_hermes_reports_skipped_not_failed(monkeypatch, tmp_path) -> None:
    """The Saved screen shows this line. "No Hermes install found" in red, on
    an install that deliberately has none, reads as a save that went wrong."""
    monkeypatch.setattr(settings, "hermes_home_path", "")

    result = setup_wizard.sync_settings_to_hermes(str(tmp_path))

    assert result["skipped"] is True
    assert result["ok"] is True
    assert result["files_written"] == 0


def test_a_configured_hermes_folder_that_is_missing_is_still_an_error(monkeypatch, tmp_path) -> None:
    """Optional means "may be left blank", not "never wrong". A path that was
    typed and does not exist is a mistake worth showing."""
    monkeypatch.setattr(settings, "hermes_home_path", str(tmp_path / "not-here"))

    result = setup_wizard.sync_settings_to_hermes(str(tmp_path))

    assert result["ok"] is False
    assert not result.get("skipped")


def test_a_hermes_already_serving_another_vault_is_not_taken_over(monkeypatch, tmp_path) -> None:
    """The 2026-10-24 incident, as a test.

    Two installs on one machine may name the same HERMES_HOME_PATH, and
    nothing stopped the second one's save from repointing the first one's
    agents: the home .env and all 40 profiles were rewritten, and for two
    hours every capture wrote into the new install's empty test vault.
    """
    home = tmp_path / "hermes"
    (home / "bin").mkdir(parents=True)
    live_vault = str(tmp_path / "LiveVault")
    (home / ".env").write_text(f"OBSIDIAN_VAULT_PATH={live_vault}\n", encoding="utf-8")
    monkeypatch.setattr(settings, "hermes_home_path", home)

    result = setup_wizard.sync_settings_to_hermes(str(tmp_path / "TestVault"))

    assert result["ok"] is False
    assert result["conflict"] is True
    assert result["files_written"] == 0
    assert result["vault_in_use"] == live_vault
    # Untouched on disk, not just reported as refused.
    assert live_vault in (home / ".env").read_text(encoding="utf-8")


def test_an_install_that_really_owns_hermes_can_say_so(monkeypatch, tmp_path) -> None:
    """The refusal has a way through, or the only route left is editing 41
    files by hand -- which is how people end up doing it blind."""
    home = tmp_path / "hermes"
    (home / "bin").mkdir(parents=True)
    (home / ".env").write_text(
        f"OBSIDIAN_VAULT_PATH={tmp_path / 'OldVault'}\n", encoding="utf-8"
    )
    monkeypatch.setattr(settings, "hermes_home_path", home)
    new_vault = str(tmp_path / "NewVault")

    result = setup_wizard.sync_settings_to_hermes(new_vault, repoint=True)

    assert result["ok"] is True
    assert new_vault in (home / ".env").read_text(encoding="utf-8")


def test_the_same_vault_is_never_a_conflict(monkeypatch, tmp_path) -> None:
    """Re-running the wizard on the install that owns Hermes must stay a
    no-question save -- a guard that fires on the normal case gets clicked
    through without being read."""
    home = tmp_path / "hermes"
    (home / "bin").mkdir(parents=True)
    live_vault = str(tmp_path / "LiveVault")
    (home / ".env").write_text(f"OBSIDIAN_VAULT_PATH={live_vault}\n", encoding="utf-8")
    monkeypatch.setattr(settings, "hermes_home_path", home)

    # Saved with a trailing separator, which is how a folder picker hands it
    # over -- and must still be the same vault, not a conflict with itself.
    result = setup_wizard.sync_settings_to_hermes(live_vault + "\\")

    assert result["ok"] is True
    assert not result.get("conflict")


def test_the_interface_loads_while_unconfigured_so_the_wizard_can_render(
    unconfigured, monkeypatch, tmp_path
) -> None:
    """The refusal above tells the operator to go to the wizard, which is
    served BY this app in production. Gating the shell answered their browser
    with the refusal JSON instead -- invisible in development, where Vite
    serves the UI on its own port and only API calls reach the gate."""
    shell = tmp_path / "index.html"
    shell.write_text("<!doctype html><title>Second Brain</title>", encoding="utf-8")
    monkeypatch.setattr(frontend_dist, "frontend_shell", lambda: shell)

    navigation = client.get("/browse/anything", headers={"Accept": "text/html"})

    assert navigation.status_code == 200
    assert "<!doctype html>" in navigation.text


def test_opening_the_interface_does_not_open_the_api(
    unconfigured, monkeypatch, tmp_path
) -> None:
    """The gate exists so no route runs against settings that do not exist.
    A browser navigation gets the shell; a `fetch` for data is still refused,
    even though both arrive at the same unconfigured install."""
    shell = tmp_path / "index.html"
    shell.write_text("<!doctype html>", encoding="utf-8")
    monkeypatch.setattr(frontend_dist, "frontend_shell", lambda: shell)

    refused = client.get("/vault/notes", headers={"Accept": "application/json"})

    assert refused.status_code == 503
    assert refused.json()["setup_required"] is True


def test_branding_is_refused_rather_than_opened_while_unconfigured(unconfigured) -> None:
    """Opening it was tried, because the first screen asks for it. It reads
    this install's data root, which an unconfigured install has none of, so
    it answered 500 -- strictly worse than the 503 the frontend already
    handles by rendering the default name."""
    assert client.get("/branding").status_code == 503


def test_which_paths_count_as_the_interface() -> None:
    """A fixed list, not "anything unmatched": plugin routers register late,
    and a gate that let every unknown path through would let their routes
    through too."""
    for path in ("/", "/index.html", "/favicon.svg", "/assets/index-abc123.js", "/fonts/x.woff2"):
        assert frontend_dist.is_user_interface_path(path) is True
    for path in ("/vault/notes", "/auth/session", "/my-day/today", "/assets", "/setup"):
        assert frontend_dist.is_user_interface_path(path) is False
