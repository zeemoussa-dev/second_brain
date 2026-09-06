"""Installing a Blueprint: preconditions first, then create.

A Blueprint is a recipe, not a snapshot -- so its install path has to check
that what it references actually exists on THIS install before it creates
anything. Refusing up front is the point: the alternative is an Agent that
installs cleanly and then fails inside a cron worker at 03:00.
"""
import pytest

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.blueprints.blueprint_manager import BlueprintManager
from app.business.core.sections.section_manager import SectionManager
from app.business.core.skills.skill_manager import SkillManager


def test_the_shipped_blueprints_parses() -> None:
    blueprint = BlueprintManager().get_by_id("notes-capture")

    assert blueprint is not None and blueprint.error is None
    # One capability per Blueprint (BUG-047): the retired `librarian` bundle
    # shipped three concerns as one all-or-nothing Section.
    assert [a.id for a in blueprint.agents] == ["notes-manager"]
    assert blueprint.skill_ids == ["capture-notes"]


def test_required_templates_are_derived_from_the_skills_not_authored() -> None:
    """The Blueprint names no Templates at all -- they follow from what its
    Skills declare. A second authored list would be a fact that can drift."""
    import json
    from app.data_access import blueprints as bd

    raw = json.dumps(bd.read_blueprint_json("notes-capture"))
    assert "template" not in raw.lower(), "a Blueprint must not author its Template list"
    assert BlueprintManager().preflight("notes-capture")["templates"] == ["note"]


def test_preflight_reports_which_skills_it_could_not_check() -> None:
    """The Template closure is only as complete as the Skills' declarations,
    so preflight names the ones it could not check. Every librarian Skill now
    declares `writes:`, so that list is empty and the check is total -- the
    point is that the field EXISTS, because a partial check reading as a
    clean one is worse than no check."""
    result = BlueprintManager().preflight("notes-capture")

    assert result["unchecked_skills"] == []
    assert result["templates"] == ["note"]


def test_an_undeclared_skill_is_reported_as_unchecked(monkeypatch) -> None:
    monkeypatch.setattr(SkillManager, "_declared_writes", lambda self, sid: [])

    result = BlueprintManager().preflight("notes-capture")

    assert set(result["unchecked_skills"]) == set(result["skills"])
    assert result["ok"] is True, "unchecked is not the same as failing"


def test_a_missing_skill_blocks_the_install(monkeypatch) -> None:
    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: None)
    manager = BlueprintManager()

    result = manager.preflight("notes-capture")

    assert result["ok"] is False
    assert any("not in the catalog" in p for p in result["problems"])


def test_an_unsatisfied_template_precondition_blocks_the_install(monkeypatch) -> None:
    monkeypatch.setattr(
        SkillManager, "validate_declared_writes",
        lambda self, sid: ["template 'thread' has no section 'Ghost'"],
    )

    result = BlueprintManager().preflight("notes-capture")

    assert result["ok"] is False
    assert any("no section 'Ghost'" in p for p in result["problems"])


def test_install_creates_nothing_when_preflight_fails(monkeypatch) -> None:
    """The guarantee that matters: a refusal must not leave a half-built
    Section behind."""
    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: None)
    monkeypatch.setattr(
        SectionManager, "create", lambda self, name: pytest.fail("must not create a Section"),
    )
    monkeypatch.setattr(
        AgentManager, "create", lambda self, *a, **k: pytest.fail("must not create an Agent"),
    )

    result = BlueprintManager().install("notes-capture")

    assert result["installed"] is False
    assert result["problems"]


def test_an_unknown_blueprint_is_refused_not_guessed() -> None:
    result = BlueprintManager().preflight("no-such-blueprint")

    assert result["ok"] is False
    assert "no Blueprint" in result["problems"][0]


def test_a_malformed_blueprint_stays_visible_in_the_library(monkeypatch) -> None:
    """Listed carrying `error`, never silently dropped -- a broken Blueprint
    the operator cannot see is worse than one that fails loudly."""
    from app.data_access import blueprints as bd

    monkeypatch.setattr(bd, "list_blueprint_ids", lambda: ["broken"])
    monkeypatch.setattr(bd, "read_blueprint_json", lambda bid: {"agents": [{"no_id": True}]})

    [blueprint] = BlueprintManager().get_all()

    assert blueprint.id == "broken" and blueprint.error is not None


def test_a_hand_configured_primary_is_not_given_duplicate_routing(monkeypatch, tmp_path) -> None:
    """apply_primary_routing_snippet is idempotent by MARKER, not content. On
    a machine whose Primary SOUL.md was written by hand there is no marker,
    so a naive apply appends a SECOND set of routing instructions for the
    same agent -- and two descriptions of how to reach one agent is worse
    than none, because the Primary has to pick."""
    soul = tmp_path / "SOUL.md"
    soul.write_text("- **`notes-manager`** -- quick capture, route here.\n", encoding="utf-8")

    class _S:
        hermes_home_path = tmp_path
    monkeypatch.setattr("app.config.settings", _S)

    assert BlueprintManager()._primary_already_describes("notes-manager") is True
    assert BlueprintManager()._primary_already_describes("research-agent") is False


def test_a_peer_without_a_routing_snippet_is_refused(monkeypatch) -> None:
    """Marked peer but carrying nothing to route with -- the Agent would
    install and never be reached, which looks like success."""
    from app.data_access import blueprints as bd

    real = bd.read_blueprint_json("notes-capture")
    broken = {**real, "agents": [{**real["agents"][0], "primary_routing_snippet": None, "peer": True}]}
    monkeypatch.setattr(bd, "read_blueprint_json", lambda bid: broken)

    result = BlueprintManager().preflight("notes-capture")

    assert result["ok"] is False
    assert any("no primary_routing_snippet" in p for p in result["problems"])


def test_the_section_is_a_parameter_not_an_imposition() -> None:
    """BUG-046: install went straight to minting a sixth Section on a machine
    that already had five, and no layer of the chain took a Section at all."""
    result = BlueprintManager().preflight("notes-capture", section_id="librarian")

    assert result["section_id"] == "librarian"
    assert result["suggested_section"] == "Librarian", "the Blueprint still suggests"


def test_choosing_a_section_that_does_not_exist_is_refused() -> None:
    result = BlueprintManager().preflight("notes-capture", section_id="no-such-section")

    assert result["ok"] is False
    assert any("no Section" in p for p in result["problems"])


def test_a_failure_past_the_preconditions_rolls_back(monkeypatch) -> None:
    """BUG-044: the no-partial-install guarantee only ever covered
    PRECONDITION failures. A raise after them left the Section behind, and
    the operator was left with one they never asked for."""
    from app.business.core.agents.agent_manager import AgentManager
    from app.business.core.sections.section_manager import SectionManager

    created, deleted = [], []
    monkeypatch.setattr(SectionManager, "get_by_id", lambda self, sid: None)
    monkeypatch.setattr(
        SectionManager, "create",
        lambda self, name: created.append(name) or type("S", (), {"id": "brand-new"})(),
    )
    monkeypatch.setattr(SectionManager, "update", lambda self, sid, **kw: None)
    monkeypatch.setattr(SectionManager, "delete", lambda self, sid: deleted.append(sid))
    monkeypatch.setattr(AgentManager, "get_by_id", lambda self, aid: None)
    monkeypatch.setattr(
        AgentManager, "create",
        lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("hermes CLI not found")),
    )

    result = BlueprintManager().install("notes-capture", wire_peers=False)

    assert result["installed"] is False
    assert "hermes CLI not found" in result["problems"][0], "the ORIGINAL error must survive"
    assert deleted == ["brand-new"], "the Section it created must be gone"


def test_an_existing_section_is_never_deleted_by_a_rollback(monkeypatch) -> None:
    """Rollback undoes what the install created -- never what was already
    there. Deleting an operator's own Section would be far worse than the
    partial install it is cleaning up."""
    from app.business.core.agents.agent_manager import AgentManager
    from app.business.core.sections.section_manager import SectionManager

    deleted = []
    monkeypatch.setattr(SectionManager, "delete", lambda self, sid: deleted.append(sid))
    monkeypatch.setattr(AgentManager, "get_by_id", lambda self, aid: None)
    monkeypatch.setattr(
        AgentManager, "create",
        lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = BlueprintManager().install("notes-capture", section_id="librarian", wire_peers=False)

    assert result["installed"] is False
    assert deleted == [], "an existing Section must survive a failed install"


def test_peer_wiring_reports_that_primary_needs_a_session_reset(monkeypatch) -> None:
    """BUG-052 fault 2: a running Hermes session is given its prompt once and
    never re-reads it, so a Primary mid-conversation cannot see peers that
    were just wired -- which is exactly when the operator tries them."""
    from app.business.logic import artifact_import

    monkeypatch.setattr(BlueprintManager, "_primary_already_describes", lambda self, aid: False)
    monkeypatch.setattr(BlueprintManager, "_ensure_peer_section", lambda self: True)
    monkeypatch.setattr(
        artifact_import, "apply_primary_routing_snippet",
        lambda aid, snippet: {"agent_id": aid, "applied": True, "detail": "ok"},
    )
    monkeypatch.setattr(BlueprintManager, "preflight", lambda self, bid, sid=None: {
        "ok": True, "templates": [], "problems": [],
    })
    from app.business.core.agents.agent_manager import AgentManager
    from app.business.core.sections.section_manager import SectionManager
    monkeypatch.setattr(SectionManager, "get_by_id", lambda self, sid: type("S", (), {"id": "librarian"})())
    monkeypatch.setattr(AgentManager, "get_by_id", lambda self, aid: object())
    monkeypatch.setattr(AgentManager, "ensure_skills", lambda self, aid, skills: {})

    result = BlueprintManager().install("notes-capture", section_id="librarian")

    assert result["peers"]["notes-manager"] == "wired"
    assert result["primary_session_reset_required"] is True
