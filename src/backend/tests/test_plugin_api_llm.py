"""Plugin API: Compass for a plugin, optional under API 12 (`ADR-063`).

Worth pinning: a plugin gets one chat completion through `api.llm`; an install
without Compass says so instead of calling it; a failed call reaches the plugin
as `LlmError`, never as the framework's own exception type.
"""
import pytest

from app import plugin_api
from app.config import settings
from app.data_access import compass_client


@pytest.fixture
def compass(monkeypatch):
    monkeypatch.setattr(settings, "compass_base_url", "https://compass.example/v1/chat/completions")
    monkeypatch.setattr(settings, "compass_api_key", "test-key")
    monkeypatch.setattr(settings, "compass_model", "test-model")
    sent: list = []

    def answer(messages, *, timeout):
        sent.append((messages, timeout))
        return "a brief"

    monkeypatch.setattr(compass_client, "request_chat_completion", answer)
    return sent


def test_a_plugin_gets_a_completion(compass):
    api = plugin_api.PluginApi("azure-cost-manager")

    reply = api.llm.complete([{"role": "user", "content": "brief me"}], timeout=30)

    assert reply == "a brief" and compass == [([{"role": "user", "content": "brief me"}], 30)]
    assert api.llm.available()


def test_without_compass_the_plugin_is_told_and_nothing_is_sent(compass, monkeypatch):
    monkeypatch.setattr(settings, "compass_api_key", "")
    api = plugin_api.PluginApi("azure-cost-manager")

    assert not api.llm.available()
    with pytest.raises(plugin_api.LlmError, match="not configured"):
        api.llm.complete([{"role": "user", "content": "brief me"}])
    assert compass == []


def test_a_failed_call_reaches_the_plugin_as_llm_error(compass, monkeypatch):
    def fail(messages, *, timeout):
        raise compass_client.CompassClientError("HTTP 503")

    monkeypatch.setattr(compass_client, "request_chat_completion", fail)
    with pytest.raises(plugin_api.LlmError, match="503"):
        plugin_api.PluginApi("azure-cost-manager").llm.complete([{"role": "user", "content": "x"}])
