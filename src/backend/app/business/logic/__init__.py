"""Business Logic block (2026-08-20 architecture pass, ADR-059 follow-up).

The actual business rules -- email/meeting/todo classification, Customer/
Partner/People linking, Thread synthesis, Housekeeping, etc. Orchestrates
across the business/vault, business/core, business/hermes, and business/
langgraph blocks; owns no data-access logic of its own. Empty skeleton for
now.
"""
