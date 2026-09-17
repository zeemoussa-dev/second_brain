"""Cockpit asks plugins which agents fit a conversation (`BUG-063` seam,
Entities plan Phase 2). Until a plugin registers a matcher, the framework's
own Customer matching still answers, so nothing changes before Entities."""
from types import SimpleNamespace

import pytest

from app.business.cockpit import chat_store, moderator
from app.business.core.plugins import plugin_manager as plugin_manager_module

_SUBJECT = {
    "stem": "2026-09-17 Pricing call",
    "frontmatter": {"type": "Thread", "customer": "Adnoc"},
    "tags": ["customer/adnoc"],
}
_EXPERTS = [SimpleNamespace(id="adnoc-expert", name="Adnoc Expert", description="", section_id="customer"),
            SimpleNamespace(id="azure-expert", name="Azure Expert", description="", section_id="tech")]
_ALL_AGENTS = _EXPERTS + [SimpleNamespace(id="customers-hub", name="Customers Hub", description="", section_id="customer")]


@pytest.fixture()
def cockpit(monkeypatch):
    """A Cockpit over one subject, with no plugin matchers and no framework Customer match."""
    monkeypatch.setattr(moderator._vault_manager, "get_index", lambda: {_SUBJECT["stem"]: _SUBJECT})
    monkeypatch.setattr(moderator._agent_manager, "get_expert_agents", lambda: list(_EXPERTS))
    monkeypatch.setattr(moderator._agent_manager, "get_all", lambda: list(_ALL_AGENTS))
    monkeypatch.setattr(moderator, "match_customer_expert", lambda stem: None)
    monkeypatch.setattr(moderator, "match_customer_fallback_agent", lambda stem: None)
    matchers: list = []
    monkeypatch.setattr(plugin_manager_module, "_plugin_agent_matchers", matchers)
    return matchers


def test_without_plugin_matchers_the_framework_customer_matching_still_answers(cockpit, monkeypatch):
    monkeypatch.setattr(moderator, "match_customer_expert", lambda stem: "adnoc-expert")
    monkeypatch.setattr(moderator, "match_customer_fallback_agent", lambda stem: "customers-hub")

    assert moderator.recommended_experts("email", _SUBJECT["stem"]) == ["adnoc-expert"]
    assert moderator.fallback_agent("email", _SUBJECT["stem"]) == "customers-hub"


def test_a_plugin_matcher_replaces_the_framework_customer_matching(cockpit, monkeypatch):
    monkeypatch.setattr(moderator, "match_customer_expert", lambda stem: pytest.fail("framework matching used"))
    seen = []

    def matcher(subject_kind, subject):
        seen.append((subject_kind, subject))
        return {"experts": ["azure-expert"], "fallback_agent_id": "customers-hub"}

    cockpit.append(matcher)

    assert moderator.recommended_experts("meeting", _SUBJECT["stem"]) == ["azure-expert"]
    assert moderator.fallback_agent("meeting", _SUBJECT["stem"]) == "customers-hub"
    assert seen[0] == ("meeting", _SUBJECT)


def test_ids_that_are_not_registered_agents_are_ignored(cockpit):
    cockpit.append(lambda kind, subject: {"experts": ["ghost-expert", "adnoc-expert", 7], "fallback_agent_id": "ghost"})

    assert moderator.recommended_experts("email", _SUBJECT["stem"]) == ["adnoc-expert"]
    assert moderator.fallback_agent("email", _SUBJECT["stem"]) is None


def test_a_failing_or_malformed_matcher_is_skipped_and_the_rest_still_apply(cockpit):
    def broken(kind, subject):
        raise RuntimeError("a plugin bug")

    cockpit.extend([broken, lambda kind, subject: ["not", "a", "dict"],
                    lambda kind, subject: {"experts": ["adnoc-expert"], "fallback_agent_id": "customers-hub"}])

    assert moderator.recommended_experts("email", _SUBJECT["stem"]) == ["adnoc-expert"]
    assert moderator.fallback_agent("email", _SUBJECT["stem"]) == "customers-hub"


def test_experts_from_several_matchers_are_combined_without_duplicates(cockpit):
    cockpit.extend([lambda kind, subject: {"experts": ["adnoc-expert"]},
                    lambda kind, subject: {"experts": ["azure-expert", "adnoc-expert"]}])

    assert moderator.recommended_experts("email", _SUBJECT["stem"]) == ["adnoc-expert", "azure-expert"]


def test_a_new_chat_recommends_the_plugin_experts_then_the_domain_experts(cockpit, monkeypatch):
    saved = {}
    monkeypatch.setattr(chat_store.vault_writer, "load_cockpit_chat_state", lambda: None)
    monkeypatch.setattr(chat_store.vault_writer, "save_cockpit_chat_state", lambda state: saved.update(state))
    monkeypatch.setattr(moderator, "match_domain_experts", lambda stem: ["azure-expert", "adnoc-expert"])
    cockpit.append(lambda kind, subject: {"experts": ["adnoc-expert"]})

    thread = chat_store.get_thread("email", _SUBJECT["stem"])

    assert thread["recommended_agent_ids"] == ["adnoc-expert", "azure-expert"]
    assert saved
