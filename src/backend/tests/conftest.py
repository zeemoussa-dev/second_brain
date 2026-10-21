"""Suite-wide sandbox: no test can reach the operator's real Hermes install.

Added by `REQ-SB-95-US-03-T01` (resolves `ESC-072`). Until this file existed
nothing isolated Hermes for any test in this suite, and that was only harmless
because nothing the suite exercised wrote a profile. `ActionManager`'s
catalogue-publication trigger changed that: publication rewrites the real
`SOUL.md` of every agent a catalogue change affects, so the four Action test
files -- which isolate the Action *store* and nothing else -- were measured
attempting **123 real SOUL.md writes across all 41 profiles of the install
they ran on**, plus 40 `Agent.json` writes, in 5m36s instead of ~2s.

The fix is here rather than in those four files on purpose: any test file
added tomorrow would otherwise have to remember the same isolation, and a
suite that corrupts the machine running it must fail safe by default, not by
convention.

Two seams, because sandboxing only one leaves the other wide open:

- **The files.** `settings.hermes_home_path` points at a directory that does
  not exist under pytest's own tmp root. Every file path in `app/hermes/
  profiles.py` is derived from `home_path` (`_profile_dir`), so a real profile
  write is impossible by construction rather than by assertion -- and
  `HermesProfiles.get_all()`'s documented "returns [] if home_path doesn't
  exist" makes a roster-wide pass a no-op instead of an error.
- **The CLI.** `HermesCLI._hermes_exe()` falls back to `shutil.which("hermes")`
  when the configured home has no `bin/hermes.exe`, so a sandboxed home alone
  would still let a subprocess act on the REAL install (its own default home
  comes from the environment, not from our config). Returning None puts every
  CLI call onto its existing, already-handled "No real Hermes install found"
  path.

The cached client singleton is reset around each test because it captures
`hermes_home_path` once, at first use: without this a client built before the
sandbox was applied would keep the real home for the rest of the session.

A test that wants a Hermes install monkeypatches `settings.hermes_home_path`
to its own `tmp_path` as usual -- that patch is applied after this fixture and
undone before it, so nothing here gets in its way (several already do).

The teardown join is not housekeeping. Catalogue publication runs on a
background thread that nothing waits for, so without it a pass started late in
a test would still be running when this fixture restored the REAL home path --
and would then publish into the operator's install, which is the exact
accident the sandbox exists to prevent, merely delayed by a race.
"""
from __future__ import annotations

import pytest

import app.business.hermes.client as hermes_client_module
from app.business.core.actions import action_manager
from app.config import settings
from app.hermes.cli import HermesCLI


@pytest.fixture(autouse=True)
def hermes_install_is_sandboxed(tmp_path_factory, monkeypatch):
    sandboxed_home = tmp_path_factory.mktemp("hermes-sandbox") / "no-hermes-install-here"
    monkeypatch.setattr(settings, "hermes_home_path", sandboxed_home)
    monkeypatch.setattr(HermesCLI, "_hermes_exe", lambda self: None)
    monkeypatch.setattr(hermes_client_module, "_client", None)
    yield
    action_manager.join_background_publications(timeout=30.0)


@pytest.fixture(autouse=True)
def every_request_is_signed_in_as_an_admin(monkeypatch):
    """REQ-SB-101 made every route default-deny, which turned 106 existing
    tests into 401s overnight. They were all written before sign-in existed
    and none of them is about authentication, so the suite runs as an
    Admin unless a test says otherwise.

    Patched at `_AuthenticationReader.identity_for` -- the one seam both
    the middleware and the `current_identity` dependency go through -- so
    production code carries no test switch. A flag like
    `settings.auth_disabled` would be a line of real code whose only
    purpose is to turn the guard off, and the day it is read from the
    environment by mistake is the day the install has no auth at all.

    **A test about authentication undoes this**, with
    `monkeypatch.setattr(auth_guard._AuthenticationReader, "identity_for", ...)`
    of its own or by restoring the real method: tests/test_authentication.py
    does exactly that, which is what keeps this fixture from quietly
    hiding the behaviour it bypasses.

    The identity is synthetic and writes nothing -- no row in the user
    store, so a test that counts users still sees an empty install.
    """
    from app.api import auth_guard
    from app.business.core.users.user import Identity, Role, User

    the_suite_admin = Identity(
        user=User(
            id="00000000-0000-0000-0000-00000000test",
            username="suite-admin",
            display_name="The Test Suite",
            role=Role.ADMIN,
            is_disabled=False,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            last_login_at=None,
        ),
        session_token_sha256="test-session",
    )
    monkeypatch.setattr(
        auth_guard._AuthenticationReader,
        "identity_for",
        lambda self, request: the_suite_admin,
    )
