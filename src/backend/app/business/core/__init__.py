"""Core block (2026-08-20 architecture pass, ADR-059 follow-up;
populated 2026-08-27).

Second Brain's own Business Entities -- distinct from the Data Access
layer's "system" block (operational bookkeeping). One folder per
entity (Section, Agent, Skill, Pipeline, Vault, Template), each holding
`type.py` (the entity's own dataclass) and `type_manager.py` (a Manager
returning Array<Entity> to business logic -- methods not yet
implemented, scaffolding only). Provider's status (Core entity, or
infrastructure alongside Tool) is still an open question, not yet
settled.
"""
