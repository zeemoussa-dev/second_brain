"""The single entry point into this library. Every capability (REST
status/sessions, live chat, profile/skill CRUD, cron, the CLI, inbound
auth) is reached through one `HermesClient` instance -- nothing under
app/hermes is meant to be imported or constructed directly by a caller
outside this package; `HermesClient.init(...)` is the one real door in.

Profile create/delete/describe live here rather than on `profiles`
directly -- they're the one real cross-namespace operation in this
library (fire the CLI command via `self.cli`, then read the result back
via `self.profiles`), the exact "compose two namespaces for one real
job" shape this library's own top level exists for."""
from __future__ import annotations

from pathlib import Path

from app.hermes.chat_session import HermesChatSession
from app.hermes.cli import HermesCLI
from app.hermes.config import HermesConfig
from app.hermes.cron import HermesCron
from app.hermes.errors import HermesUnavailableError
from app.hermes.inbound_auth import RequireHermesSharedSecret
from app.hermes.profiles import HermesAgent, HermesProfiles
from app.hermes.rest import HermesRestAPI
from app.hermes.skills import HermesSkills


class HermesClient:
    def __init__(self, config: HermesConfig) -> None:
        self.config = config
        self.rest = HermesRestAPI(config)
        self.skills = HermesSkills(config)
        self.profiles = HermesProfiles(config, self.skills)
        self.cron = HermesCron(config)
        self.cli = HermesCLI(config)

    @classmethod
    def init(
        cls,
        *,
        base_url: str,
        home_path: Path,
        api_key: str = "",
        inbound_shared_secret: str = "",
    ) -> "HermesClient":
        return cls(HermesConfig(
            base_url=base_url,
            home_path=Path(home_path),
            api_key=api_key,
            inbound_shared_secret=inbound_shared_secret,
        ))

    def open_chat_session(self, agent_id: str | None) -> HermesChatSession:
        """A single live WS chat bridge (not reusable across agents --
        one instance per (agent_id, caller) connection). Not yet
        connected; the caller awaits `.connect()`."""
        return HermesChatSession(self.config, self.rest.get_session_token, agent_id)

    def wrap_inbound(self, asgi_app):
        """Wraps an ASGI app (a mounted MCP server) so only Hermes itself
        -- or a loopback caller -- can reach it."""
        return RequireHermesSharedSecret(asgi_app, shared_secret=self.config.inbound_shared_secret)

    def create_profile(
        self, name: str, *, clone: bool = False, clone_all: bool = False,
        clone_from: str | None = None, no_alias: bool = False,
        no_skills: bool = False, description: str | None = None,
    ) -> HermesAgent:
        ok, output = self.cli.create_profile(
            name, clone=clone, clone_all=clone_all, clone_from=clone_from,
            no_alias=no_alias, no_skills=no_skills, description=description,
        )
        if not ok:
            raise HermesUnavailableError(f"hermes profile create failed: {output}")
        agent = self.profiles.find_by_id(name)
        if agent is None:
            raise HermesUnavailableError(
                f"hermes profile create reported success but {name!r} isn't readable on disk"
            )
        return agent

    def delete_profile(self, name: str) -> None:
        ok, output = self.cli.delete_profile(name)
        if not ok:
            raise HermesUnavailableError(f"hermes profile delete failed: {output}")

    def describe_profile(self, name: str, *, text: str | None = None, auto: bool = False, overwrite: bool = False) -> HermesAgent:
        ok, output = self.cli.describe_profile(name, text=text, auto=auto, overwrite=overwrite)
        if not ok:
            raise HermesUnavailableError(f"hermes profile describe failed: {output}")
        agent = self.profiles.find_by_id(name)
        if agent is None:
            raise HermesUnavailableError(f"hermes profile describe succeeded but {name!r} isn't readable on disk")
        return agent
