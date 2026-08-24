"""Provider block (2026-08-20 architecture pass, ADR-059 follow-up).

The lowest point in the system -- not dependent on anything else in this
codebase. Stores the list of LLM providers (Compass/OpenAI-shaped,
Anthropic, etc.) System Data needs to reach them. Schema still being
settled (Name, id, Description, Icon, URL, credential/API-shape, Model);
provider_registry.py's own current id/name/endpoint/credential/model
fields are the migration source once this block starts filling. Empty
skeleton for now.
"""
