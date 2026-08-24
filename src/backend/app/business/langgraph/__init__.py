"""Business layer over LangGraph (2026-08-20 architecture pass, ADR-059
follow-up). Invokes/manages LangGraph execution -- no data-access layer
beneath this block, since LangGraph owns its own execution data (out of
our control, per the operator's own 3-data-type split). Empty skeleton
for now.
"""
