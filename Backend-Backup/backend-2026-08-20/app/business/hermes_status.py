"""Thin business-layer wrapper over hermes_client.py (ADR-005 point 5's own
"router never reaches into data_access/ directly" shape) -- turns a raw
connection failure into an honest, structured "unavailable" result rather
than a 500, since no Hermes gateway is deployed yet and that is an
expected, not exceptional, state today."""
from __future__ import annotations

from app.data_access import hermes_client


def get_health() -> dict:
    try:
        return {"reachable": True, **hermes_client.health()}
    except hermes_client.HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}


def get_capabilities() -> dict:
    try:
        return {"reachable": True, **hermes_client.list_capabilities()}
    except hermes_client.HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}


def get_jobs() -> dict:
    try:
        return {"reachable": True, **hermes_client.list_jobs()}
    except hermes_client.HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}


def get_sessions() -> dict:
    try:
        return {"reachable": True, **hermes_client.list_sessions()}
    except hermes_client.HermesUnavailableError as exc:
        return {"reachable": False, "error": str(exc)}
