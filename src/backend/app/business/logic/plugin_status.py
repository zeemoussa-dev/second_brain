"""What the plugin host did with each installed plugin, as plain dicts.

Split out of `system_health` because two surfaces need the same answer for
different reasons (`BUG-088`): System Health reports it to the operator, and
the frontend needs it to decide whether to mount a plugin's screens at all.
A refused plugin's backend is not mounted, but its screens were compiled into
the frontend at install time and render regardless -- so without this the app
shows a working-looking page whose every call 404s.
"""
from __future__ import annotations

from app.business.core.plugins.plugin_manager import PluginManager

_plugin_manager = PluginManager()


def get_plugin_status() -> list[dict]:
    return [
        {
            "id": plugin.id, "name": plugin.name, "version": plugin.version,
            "status": plugin.status, "reason": plugin.reason,
            "routes_prefix": plugin.routes_prefix,
        }
        for plugin in _plugin_manager.get_load_report()
    ]
