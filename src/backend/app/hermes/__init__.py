"""Reusable Hermes client library. Zero awareness of Second Brain (or any
other embedding app) -- every value it needs is passed in explicitly via
HermesClient.init(...). The embedding app owns exactly one HermesClient
instance and reaches every Hermes capability through it; nothing outside
this package constructs a HermesConfig or a submodule class directly.
"""
from app.hermes.client import HermesClient
from app.hermes.config import HermesConfig
from app.hermes.errors import HermesUnavailableError
from app.hermes.profiles import HermesAgent
from app.hermes.skills import HermesSkill

__all__ = [
    "HermesClient", "HermesConfig", "HermesUnavailableError",
    "HermesAgent", "HermesSkill",
]
