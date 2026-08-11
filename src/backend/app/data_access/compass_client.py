"""Client for Core42's Compass API — an OpenAI-chat-completions-shaped HTTP
endpoint (see agentic-map's services/gateway/compass.py for the precedent
this mirrors). Second Brain talks to it directly over httpx; no SDK needed
since Compass speaks the same wire format as OpenAI's /chat/completions.
"""
from __future__ import annotations

import json

import httpx

from app.config import settings


class CompassError(Exception):
    """Compass call failed or returned an unparseable response."""


def classify_email(
    subject: str,
    sender: str,
    body: str,
    known_customers: list[str],
    known_kinds: list[str],
) -> dict:
    customer_list = ", ".join(known_customers) if known_customers else "(none yet)"
    kind_list = ", ".join(known_kinds) if known_kinds else "(none yet — Emails and Files are common starting points)"
    prompt = (
        "Classify this inbox item along two axes. Respond with a single JSON "
        "object: {\"customer\": <name>, \"kind\": <label>, \"confidence\": "
        "<0-1 float, your confidence in the customer match>}.\n\n"
        f"CUSTOMER — which customer/company it relates to. Already known: "
        f"{customer_list}. Reuse an exact existing name (same spelling/"
        "casing) when it clearly matches one. If it clearly relates to a "
        "real customer/company not yet in that list, propose a concise "
        "proper-noun name — new customers are expected. If you can't "
        "confidently tell, use \"Unsorted\" rather than guessing.\n\n"
        f"KIND — what this item actually is, as a short folder-friendly "
        "label (letters only, Title Case, e.g. \"Emails\", \"Files\"). "
        f"Already known kinds: {kind_list}. Reuse an existing kind when it "
        "fits. A real back-and-forth conversation is \"Emails\". An "
        "automated notification about a shared file/document (e.g. "
        "SharePoint/OneDrive 'shared with you' alerts) is \"Files\", not "
        "\"Emails\", even though it arrived as mail. Propose a new kind "
        "label if something doesn't fit any existing one (e.g. an "
        "automated system alert, a newsletter) — new kinds are expected as "
        "more filtering needs come up over time.\n\n"
        f"From: {sender}\nSubject: {subject}\n\n{body[:4000]}"
    )
    payload = {
        "model": settings.compass_model,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {settings.compass_api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(
            settings.compass_base_url, headers=headers, json=payload, timeout=30.0
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise CompassError(f"Compass call failed: {exc}") from exc

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return {
            "customer": parsed.get("customer") or "Unsorted",
            "kind": parsed.get("kind") or "Emails",
            "confidence": float(parsed.get("confidence", 0.0)),
        }
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise CompassError(f"couldn't parse Compass response: {exc}") from exc
