"""TemplateManager -- returns Array<Template> to whatever business-logic
caller needs it. Methods not implemented yet (scaffolding only, per
operator: "type_manager as the methods getting to that part later")."""
from __future__ import annotations

from app.business.core.templates.template import Template


class TemplateManager:
    def get_all(self) -> list[Template]:
        raise NotImplementedError
