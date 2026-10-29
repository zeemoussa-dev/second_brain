"""Who hands work to whom, and how many times it is drawn (`REQ-SB-102`;
operator, 2026-10-24: "when I added Adnoc as linked to the Primary it
added it twice").

Two separate faults met in that one sentence, and each gets its own
test here because fixing either alone would still have looked wrong:

1. **Hermes reports `default` (Primary) twice.** A duplicated agent
   duplicates every edge drawn to it, so one link rendered on two
   copies of the same node.
2. **The link was written backwards.** A child's `depends_on` names its
   parent, so A's specialists are the agents whose `depends_on` holds
   A -- and the editor was PATCHing that derived list of children into
   A's OWN `depends_on`, which says the opposite thing.
"""
import pytest

from app.business.hermes import profiles as hermes_profiles
from app.business.logic import flow_map


class _Profile:
    """Just enough of a Hermes profile for `without_duplicate_ids`,
    which reads an attribute rather than a key when given `id_of`."""

    def __init__(self, profile_id: str) -> None:
        self.id = profile_id


def test_a_profile_hermes_reports_twice_is_listed_once() -> None:
    """[REQ-SB-102] Measured on the operator's install: 42 profiles
    back from Hermes with `default` appearing twice, byte-identical.
    `<HERMES_HOME>` IS the default profile's directory and is also
    enumerated among the profiles, so Primary is counted from both
    ends."""
    reported = [_Profile("default"), _Profile("adnoc-expert"), _Profile("default")]

    listed = hermes_profiles.without_duplicate_ids(reported, id_of=lambda p: p.id)

    assert [p.id for p in listed] == ["default", "adnoc-expert"]


def test_de_duplication_keeps_hermes_own_order_and_the_first_copy() -> None:
    """[REQ-SB-102] The copies are identical, so which one survives is
    arbitrary -- but the ORDER is not, and a list that reshuffled itself
    would move every agent on the map for no reason."""
    reported = [_Profile(name) for name in ("zulu", "alpha", "zulu", "mike")]

    assert [p.id for p in hermes_profiles.without_duplicate_ids(
        reported, id_of=lambda p: p.id,
    )] == ["zulu", "alpha", "mike"]


def test_dicts_are_de_duplicated_too_without_being_told_how_to_read_an_id() -> None:
    """[REQ-SB-102] `profiles.get_all()` hands dicts and `AgentManager`
    hands dataclasses; one helper serves both, and the dict case is the
    default so the common caller says nothing."""
    assert hermes_profiles.without_duplicate_ids(
        [{"id": "default"}, {"id": "default"}, {"id": "other"}],
    ) == [{"id": "default"}, {"id": "other"}]


class _Agent:
    """The shape `flow_map.build` reads off an Agent."""

    def __init__(self, agent_id: str, depends_on: list[str]) -> None:
        self.id = agent_id
        self.name = agent_id
        self.depends_on = depends_on
        self.prompt = ""
        self.routing_conditions = {}
        self.skill_ids = []
        self.type = "worker"


def _routes_to(agents, actions=None, workflows=None, doors=None):
    built = flow_map.build(agents, actions or [], workflows or [], doors or [])
    return {node["id"]: node["routes_to"] for node in built["agents"]}


def test_a_specialist_is_an_agent_whose_depends_on_names_its_parent() -> None:
    """[REQ-SB-102] The direction, pinned. Making Adnoc a specialist of
    Primary means writing **Adnoc's** file, not Primary's -- the editor
    used to write Primary's, which said Primary depends on Adnoc and
    put the link on the wrong node entirely."""
    agents = [_Agent("default", []), _Agent("adnoc-expert", ["default"])]

    routes = _routes_to(agents)

    assert routes["default"] == ["adnoc-expert"], "Primary hands work to Adnoc"
    assert routes["adnoc-expert"] == [], "and Adnoc hands work to nobody"


def test_writing_the_parents_own_depends_on_points_the_link_the_other_way() -> None:
    """[REQ-SB-102] The bug, stated as a test so it cannot come back
    quietly: the old editor's write produced exactly this, and it reads
    as Adnoc being the one that hands work out."""
    agents = [_Agent("default", ["adnoc-expert"]), _Agent("adnoc-expert", [])]

    routes = _routes_to(agents)

    assert routes["default"] == []
    assert routes["adnoc-expert"] == ["default"], (
        "this is what the old editor wrote -- the link on the wrong node"
    )


def test_one_link_to_a_duplicated_parent_would_have_been_drawn_twice() -> None:
    """[REQ-SB-102] Why the two faults were one complaint. With Primary
    present twice, a single `depends_on` entry yields a node list with
    the same edge in it twice -- one link, drawn two times."""
    duplicated = [_Agent("default", []), _Agent("default", []),
                  _Agent("adnoc-expert", ["default"])]

    built = flow_map.build(duplicated, [], [], [])
    primary_nodes = [node for node in built["agents"] if node["id"] == "default"]
    edges_to_adnoc = [e for e in built["edges"] if e["to"] == "adnoc-expert"]

    assert len(primary_nodes) == 2, "the premise: Hermes reported Primary twice"
    assert len(edges_to_adnoc) == 2, "and so the one link was drawn twice"

    # De-duplicated first, the same single link is drawn once.
    once = hermes_profiles.without_duplicate_ids(duplicated, id_of=lambda a: a.id)
    built_once = flow_map.build(once, [], [], [])
    assert len([e for e in built_once["edges"] if e["to"] == "adnoc-expert"]) == 1
