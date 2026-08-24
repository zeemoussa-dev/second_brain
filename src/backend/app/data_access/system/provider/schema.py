"""Provider schema (2026-08-20 architecture pass).

Field naming decided directly (operator: "Schema Names is your job"), not
re-asked. `api_format` and `api_key` split apart deliberately -- the
operator's original "API" field was ambiguous between the two, and both
are genuinely needed: `api_format` is a real gap today's system has no
field for at all (Compass and Anthropic speak different wire protocols,
hardcoded per-client with no data-driven dispatch); `api_key` is renamed
from provider_registry.py's own current `credential` field to match the
naming already established in config.py (`compass_api_key`,
`anthropic_api_key`).
"""
from __future__ import annotations

from dataclasses import dataclass

# Known wire formats, evidenced by the two real providers this system
# talks to today. Grows as new providers are added -- not a closed enum.
API_FORMAT_OPENAI_CHAT_COMPLETIONS = "openai-chat-completions"
API_FORMAT_ANTHROPIC_MESSAGES = "anthropic-messages"


@dataclass
class Provider:
    id: str
    name: str
    description: str
    # Google Fonts (Material Symbols) icon name, e.g. "smart_toy" --
    # operator-decided, 2026-08-20, applies to every icon field in this
    # system. Never an image/SVG asset.
    icon: str
    url: str
    api_format: str
    api_key: str
    model: str
