"""ToolManager -- the sole gateway onto Tool data (mirrors Section/Agent/
Pipeline/Vault/Template/Index/Provider Manager's own "one real gateway"
rule). Raw I/O lives entirely in data_access/tools.py."""
from __future__ import annotations

from app.business.core.tools.tool import Tool
from app.data_access import tools as tools_data


class ToolManager:
    def _to_tool(self, tool_id: str, data: dict) -> Tool:
        return Tool(
            id=tool_id,
            name=data.get("name") or tool_id,
            description=data.get("description") or "",
            icon=data.get("icon"),
        )

    def get_all(self) -> list[Tool]:
        tools: list[Tool] = []
        for tool_id in tools_data.list_tool_ids():
            data = tools_data.read_tool_json(tool_id)
            if data is not None:
                tools.append(self._to_tool(tool_id, data))
        return tools

    def get_by_id(self, tool_id: str) -> Tool | None:
        data = tools_data.read_tool_json(tool_id)
        return self._to_tool(tool_id, data) if data is not None else None

    def create(self, tool_id: str, name: str, description: str = "", icon: str | None = None) -> Tool:
        tools_data.write_tool_json(
            tool_id, {"id": tool_id, "name": name, "description": description, "icon": icon},
        )
        return self.get_by_id(tool_id)

    def update(
        self, tool_id: str, *, name: str | None = None, description: str | None = None,
        icon: str | None = None,
    ) -> Tool | None:
        """`None` (omitted) = leave unchanged, same convention every
        other Manager's own update() uses."""
        data = tools_data.read_tool_json(tool_id)
        if data is None:
            return None
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if icon is not None:
            data["icon"] = icon
        tools_data.write_tool_json(tool_id, data)
        return self.get_by_id(tool_id)

    def delete(self, tool_id: str) -> dict:
        """Refuses while real Skills are still grouped under it (ADR-014's
        result-dict convention) -- reassign them to another Tool first via
        SkillManager.update(tool_id=...)."""
        if self.get_by_id(tool_id) is None:
            return {"deleted": False}
        if tools_data.has_skills(tool_id):
            return {"deleted": False, "reason": "Tool still has Skills assigned"}
        tools_data.delete_tool_dir(tool_id)
        return {"deleted": True}
