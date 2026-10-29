"""Saving one parent's routing conditions REPLACES that parent's whole
set (`REQ-SB-102`).

Written because the Flow page now offers the `when` for a route from a
page other than the parent's own -- the operator could see a missing
condition on the child and had no way to set it there (2026-10-24:
"I can't edit the when inside the Adnoc agent itself, yet it shows
what's missing and I can't do anything about it").

An editor opened on the child knows only the one edge it cares about.
If it saved just that, every OTHER condition on the parent would be
deleted, silently, by a person who was fixing something unrelated. The
page therefore seeds that editor with the parent's complete edge set,
and this test is why that is not optional: it pins the replace
semantics, so the day someone "simplifies" the page to send one edge,
a test says what that costs.

Deliberately NOT a test that the endpoint should merge instead.
Replacing is correct for the parent's own editor -- clearing a field is
how a condition is removed, and a merge would make removal impossible.
The rule is "send the whole set", not "make the endpoint forgiving".
"""
import pytest
from fastapi.testclient import TestClient

import app.main as main_app

client = TestClient(main_app.app)

A_PARENT = "a-parent-this-test-invented"


@pytest.fixture(autouse=True)
def conditions_are_this_tests_own(tmp_path, monkeypatch):
    """The real reader and writer over a file in `tmp_path`, so what is
    asserted is what the shipped code really wrote -- and nothing here
    touches the operator's `routing-conditions.json`."""
    store = tmp_path / "routing-conditions.json"
    monkeypatch.setattr(
        "app.data_access.routing_conditions.routing_conditions_path", lambda: store,
    )
    return store


def read_back(agent_id: str) -> dict:
    from app.data_access import routing_conditions as data
    return data.read_all().get(agent_id, {})


def test_saving_every_edge_keeps_every_edge() -> None:
    """[REQ-SB-102] The ordinary case, and what the child's page must
    do: send the parent's whole set, change one of them."""
    whole_set = {"first-child": "when it is about the first thing",
                 "second-child": "when it is about the second"}
    assert client.put(f"/hermes/agents/{A_PARENT}/routing-conditions",
                      json=whole_set).status_code == 200

    changed = {**whole_set, "second-child": "a different reason"}
    assert client.put(f"/hermes/agents/{A_PARENT}/routing-conditions",
                      json=changed).status_code == 200

    assert read_back(A_PARENT) == changed


def test_saving_one_edge_deletes_the_parents_other_conditions() -> None:
    """[REQ-SB-102] The hazard, stated so it cannot be rediscovered the
    expensive way. This is exactly what an editor opened on a child
    would send if it only knew its own edge -- and the parent's other
    route loses its condition without anyone being told."""
    client.put(f"/hermes/agents/{A_PARENT}/routing-conditions", json={
        "first-child": "when it is about the first thing",
        "second-child": "when it is about the second",
    })

    # A well-meaning partial save, from a page that knew one edge.
    client.put(f"/hermes/agents/{A_PARENT}/routing-conditions",
               json={"second-child": "a different reason"})

    survived = read_back(A_PARENT)
    assert survived == {"second-child": "a different reason"}
    assert "first-child" not in survived, (
        "the other condition was deleted -- which is why the child's page seeds the "
        "editor with the parent's FULL edge set"
    )


def test_an_emptied_condition_is_removed_rather_than_stored_blank() -> None:
    """[REQ-SB-102] Why replacing is right for the parent's own editor:
    clearing the box is how a condition is deleted, and a merging
    endpoint could never express that."""
    client.put(f"/hermes/agents/{A_PARENT}/routing-conditions",
               json={"first-child": "when it is about the first thing"})

    client.put(f"/hermes/agents/{A_PARENT}/routing-conditions",
               json={"first-child": "   "})

    assert read_back(A_PARENT) == {}, "a blank condition is removed, not stored empty"


def test_one_parents_conditions_never_touch_anothers() -> None:
    """[REQ-SB-102] The replace is scoped to the agent in the path. A
    child's page may show several parents at once, each with its own
    editor, and saving one must leave the others exactly as they
    were."""
    other = "another-parent-this-test-invented"
    client.put(f"/hermes/agents/{A_PARENT}/routing-conditions", json={"kid": "parent one's"})
    client.put(f"/hermes/agents/{other}/routing-conditions", json={"kid": "parent two's"})

    client.put(f"/hermes/agents/{A_PARENT}/routing-conditions", json={"kid": "rewritten"})

    assert read_back(A_PARENT) == {"kid": "rewritten"}
    assert read_back(other) == {"kid": "parent two's"}
