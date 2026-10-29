"""Core42 Insight -- a Second Brain plugin (`ADR-022`).

Per customer, how Insight (Core42's sovereignty product) is charged -- a
percentage of the month's consumption, an up-front fee or a yearly fee, in dated
lines in the customer's Insight note -- and the revenue that results, per customer and
across customers, with a forecast. Consumption comes from the Azure
Cost Manager plugin through its service.

Everything it needs from the framework arrives through the Plugin API handed to
`register`; this package imports nothing from the framework itself.
"""
from __future__ import annotations

from .insight_service import InsightService
from .routes import build_router
from .sources import Sources

SUMMARY_SERVICE = "core42-insight.summary"


class SummaryService:
    """`core42-insight.summary` for the Entities customer page: read-only, local."""

    def __init__(self, service: InsightService) -> None:
        self._service = service

    def for_entity(self, customer_stem: str) -> dict | None:
        try:
            return self._service.summary_for(customer_stem)
        except Exception:
            # A page load asks this; a missing Cost Manager must not break that page.
            return None


def register(api) -> None:
    service = InsightService(Sources(api))
    api.register_router(build_router(service))
    api.provide_service(SUMMARY_SERVICE, SummaryService(service))
