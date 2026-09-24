"""A leading @mention picks the Expert, including one named the way people say it.

Found live on a real thread (2026-09-24): "@compass Pricing Expert What is the Pay as
you go Model in Compass" went to the moderator, which answered that nobody in the chat
looked like a strong match. The pattern captured one word, "compass", which is no
agent's id or name -- and an agent's display name has spaces in it."""
import pytest

from app.business.cockpit import chat_turn
from app.business.hermes import agents_map_adapter

AGENTS = [
    {"id": "compass-expert", "name": "Compass Expert"},
    {"id": "compass-pricing-expert", "name": "Compass Pricing Expert"},
    {"id": "compass-models-expert", "name": "Compass Models Expert"},
    {"id": "research-agent", "name": "Research Agent"},
    {"id": "adnoc-expert", "name": "ADNOC Expert"},
]


@pytest.fixture(autouse=True)
def agents(monkeypatch):
    monkeypatch.setattr(agents_map_adapter, "list_agent_summaries", lambda: list(AGENTS))


@pytest.mark.parametrize("text, expected", [
    ("@compass Pricing Expert What is the Pay as you go Model in Compass", "compass-pricing-expert"),
    ("@Compass Pricing Expert what is the pay as you go model?", "compass-pricing-expert"),
    ("@compass-pricing-expert what is the pay as you go model?", "compass-pricing-expert"),
    ("@Research Agent find the latest pricing page", "research-agent"),
    ("@ADNOC Expert who owns this account?", "adnoc-expert"),
    ("@adnoc-expert who owns this account?", "adnoc-expert"),
])
def test_a_mention_resolves_however_the_name_is_typed(text, expected):
    assert chat_turn._leading_mention(text) == expected


def test_the_longest_matching_name_wins_over_a_shorter_one_that_prefixes_it():
    """"Compass Expert" is a prefix of "Compass Pricing Expert"; mentioning the
    longer name must not land on the shorter agent."""
    assert chat_turn._leading_mention("@Compass Pricing Expert hello") == "compass-pricing-expert"
    assert chat_turn._leading_mention("@Compass Expert hello") == "compass-expert"


@pytest.mark.parametrize("text", [
    "what does @compass think about this?",   # not leading: an @ mid-sentence never fires
    "@nobody-here please answer",             # resolves to no real agent
    "no mention at all",
    "",
    "@",
])
def test_routing_is_left_alone_when_there_is_no_real_leading_mention(text):
    assert chat_turn._leading_mention(text) is None


def test_a_mention_never_swallows_more_than_a_name():
    """A sentence whose words happen to follow a real mention stays a sentence:
    only the agent's own words are consumed, the rest is the question."""
    assert chat_turn._leading_mention("@Compass Expert Pricing Models are confusing") == "compass-expert"
