"""Skill entity -- a capability an Agent can invoke, composed of a
SKILL.md (content/prompt) and optional supporting scripts. Content lives
in the checked-in Hermes-Provisioning/skills/ template repo
(data_access/skills.py); metadata (tool grouping, deployment list,
mutates, origin) lives in the Registry's Tools/<tool>/Skills/ tree
(data_access/tools.py). See skill.py for the shape, skill_manager.py for
the sole gateway (create/update/deploy/undeploy/delete/sync_from_hermes)."""
