"""Action entity -- ADR-032's sixth artifact kind: one invocable
operation this app can actually perform (typed inputs with required
flags, the agent ids allowed to call it, a confirmation flag, and
exactly one implementation -- a deployed Skill, a route on this app, or
an in-app feature). Instance data under the App Database Folder at
data/Actions/<id>/Action.json, never the repository.

Unrelated to the OTHER thing this codebase calls an "Action": the
section-access map names a Skill's declared write caller that way too
(ADR-033). ActionManager is the sole gateway onto this one. See
action.py for the shape, action_manager.py for the Manager itself.
"""
