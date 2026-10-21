"""What a user is, what the three roles may do, and the verified identity
a request carries once it has been authenticated (REQ-SB-101).

**The capability matrix is data, in one place, on purpose.** The operator
asked to correct the role split after seeing a draft, and a matrix spread
across `if role == ADMIN` checks in twenty routers cannot be corrected --
it can only be re-audited. Here, changing what a Power User may do is one
edit to `_CAPABILITIES_BY_ROLE`, and `test_user_roles.py` asserts the
table against the routers rather than restating it.

**Roles are not ranks.** It is tempting to give each role a number and
compare, and it reads fine until the first capability that a Power User
has and an Admin does not, or a fourth role that is not above or below
the others. Each role names its own set; Admin's happens to be a superset
today, and nothing depends on that staying true.

**One row is deliberately undecided.** `AUTHOR_AUTOMATIONS` -- creating
and editing Actions and Workflows -- is Admin-only here, and that is the
row the operator marked `?` in the PRD because it is what decides what
"Power User" means. Denied is the safe placeholder while it is open:
granting a capability by accident is discovered when something goes
wrong, denying one is discovered immediately by the person who needed it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    POWER_USER = "power_user"
    ADMIN = "admin"


class Capability(StrEnum):
    """Named by what a person does, not by the route that does it. A
    capability outlives the endpoint that happens to implement it, and
    the same capability usually guards several routes."""

    READ_VAULT = "read_vault"
    CHAT_WITH_AGENTS = "chat_with_agents"
    USE_PLUGIN_SCREENS = "use_plugin_screens"
    RESOLVE_ENTITIES = "resolve_entities"
    VIEW_AGENTS = "view_agents"
    READ_AGENT_TRANSCRIPTS = "read_agent_transcripts"
    CALL_ACTIONS = "call_actions"
    CONFIRM_ACTIONS = "confirm_actions"
    RUN_WORKFLOWS = "run_workflows"
    REBUILD_VAULT_INDEX = "rebuild_vault_index"
    AUTHOR_AUTOMATIONS = "author_automations"
    MANAGE_AGENTS = "manage_agents"
    MANAGE_PLUGINS = "manage_plugins"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_HERMES = "manage_hermes"
    EXPORT_AND_BACKUP = "export_and_backup"
    MANAGE_OPERATOR_PROFILE = "manage_operator_profile"
    MANAGE_USERS = "manage_users"


_EVERYONE_SIGNED_IN = frozenset(
    {
        Capability.READ_VAULT,
        Capability.CHAT_WITH_AGENTS,
        Capability.USE_PLUGIN_SCREENS,
        Capability.RESOLVE_ENTITIES,
        Capability.VIEW_AGENTS,
    }
)

_POWER_USER_ADDS = frozenset(
    {
        Capability.READ_AGENT_TRANSCRIPTS,
        Capability.CALL_ACTIONS,
        Capability.CONFIRM_ACTIONS,
        Capability.RUN_WORKFLOWS,
        Capability.REBUILD_VAULT_INDEX,
    }
)

_ADMIN_ADDS = frozenset(
    {
        # The open row: Admin-only until the operator settles it.
        Capability.AUTHOR_AUTOMATIONS,
        Capability.MANAGE_AGENTS,
        Capability.MANAGE_PLUGINS,
        Capability.MANAGE_SETTINGS,
        Capability.MANAGE_HERMES,
        Capability.EXPORT_AND_BACKUP,
        Capability.MANAGE_OPERATOR_PROFILE,
        Capability.MANAGE_USERS,
    }
)

_CAPABILITIES_BY_ROLE: dict[Role, frozenset[Capability]] = {
    Role.USER: _EVERYONE_SIGNED_IN,
    Role.POWER_USER: _EVERYONE_SIGNED_IN | _POWER_USER_ADDS,
    Role.ADMIN: _EVERYONE_SIGNED_IN | _POWER_USER_ADDS | _ADMIN_ADDS,
}


def capabilities_of(role: Role) -> frozenset[Capability]:
    """Raises KeyError on a role this build does not know, rather than
    returning an empty set. A row whose `role` column holds something
    unrecognised is a corrupted or hand-edited database, and answering
    "no capabilities" would quietly turn that into a confusing but
    survivable login instead of the loud failure it should be."""
    return _CAPABILITIES_BY_ROLE[role]


def role_allows(role: Role, capability: Capability) -> bool:
    return capability in capabilities_of(role)


@dataclass(frozen=True)
class User:
    """An account as the business layer sees it. Carries no digest, no
    salt and no parameters: nothing above `data_access` has a reason to
    hold a credential, and a dataclass that cannot hold one cannot leak
    one into a response model by being returned directly."""

    id: str
    username: str
    display_name: str
    role: Role
    is_disabled: bool
    created_at: str
    updated_at: str
    last_login_at: str | None

    @property
    def capabilities(self) -> frozenset[Capability]:
        return capabilities_of(self.role)

    def may(self, capability: Capability) -> bool:
        return not self.is_disabled and role_allows(self.role, capability)


@dataclass(frozen=True)
class Identity:
    """A verified caller: the user a request proved it is, and the
    session that proved it. This -- not a username and not a role string
    -- is what a route guard receives, so that replacing local accounts
    with Entra later changes who constructs an `Identity` and nothing
    about who consumes one (REQ-SB-101, Finding 5)."""

    user: User
    session_token_sha256: str

    def may(self, capability: Capability) -> bool:
        return self.user.may(capability)
