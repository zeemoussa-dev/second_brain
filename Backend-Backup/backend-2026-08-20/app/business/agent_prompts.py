"""Per-id Prompt override + Guardrails placeholder (REQ-SB-66-US-01, ADR-044),
backed by a new sibling `.second-brain/agent_prompts.json` store, composed
alongside app/business/agent_registry.py, not inside it -- agent_registry.py
itself is not modified (ADR-011 point 2's "agent identity/type/actions stay
hardcoded" reasoning stays untouched a further time over, mirroring
agent_keywords.py/working_mode_registry.py's own precedent).

id covers both a real Agent id (e.g. "vault-filing-expert") and a real Job id
(e.g. "classify") uniformly -- one flat id-keyed namespace, no special-casing
between the two (Scenario 8, REQ-SB-66-US-01-AC-08).

This module only builds the store's own get/set surface -- wiring the
override into any real prompt-building call site is T02/T03's own scope, and
any HTTP-reachable endpoint is T04/T06's own scope (out of this task's own
Files to Modify)."""
from app.data_access import vault_writer


def get_prompt(id: str) -> str | None:
    """None when no override has ever been saved for id -- the ordinary,
    expected starting state (mirrors load_agent_keywords's own "no
    assignment yet" no-raise reasoning, not working_mode_registry's seeded
    default, since Prompt has no sensible universal default text of its
    own to seed)."""
    return vault_writer.load_agent_prompt_record(id)["prompt"]


def set_prompt(id: str, prompt: str) -> None:
    """Whole-value replace for id's own prompt entry -- never alters any
    OTHER id's own stored record, and never alters id's own guardrails
    value."""
    record = vault_writer.load_agent_prompt_record(id)
    record["prompt"] = prompt
    vault_writer.save_agent_prompt_record(id, record)


def get_guardrails(id: str) -> str:
    """"" when unset (Decision 3/ADR-044 point 2: Guardrails is always
    present, defaulting to an empty string, never absent/None)."""
    return vault_writer.load_agent_prompt_record(id)["guardrails"]


def set_guardrails(id: str, guardrails: str) -> None:
    """Whole-value replace for id's own guardrails entry -- never alters
    any OTHER id's own stored record, and never alters id's own prompt
    value."""
    record = vault_writer.load_agent_prompt_record(id)
    record["guardrails"] = guardrails
    vault_writer.save_agent_prompt_record(id, record)
