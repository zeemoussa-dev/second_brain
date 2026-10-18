"""Workflow entity -- ADR-032's seventh artifact kind: the ordered steps
the operator documented for one kind of request (each step naming a
catalogued Action, carrying that step's inputs and its own confirmation
flag), plus what is reported back. Instance data under the App Database
Folder at data/Workflows/<id>/Workflow.json, never the repository.

**Not a Pipeline.** A Workflow is intent-triggered and run step by step
by the framework against a run record (ADR-034); a Pipeline is
time-triggered by a real Hermes cron job. ADR-032 leaves Pipeline
exactly as it is -- `PipelineManager` is shape reference only, never a
shared store, Manager or migration target.

WorkflowManager is the sole gateway onto this one. See workflow.py for
the shape, workflow_manager.py for the Manager itself.
"""
