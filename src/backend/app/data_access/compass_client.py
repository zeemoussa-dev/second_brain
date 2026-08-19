"""Client for Core42's Compass API — an OpenAI-chat-completions-shaped HTTP
endpoint (see agentic-map's services/gateway/compass.py for the precedent
this mirrors). Second Brain talks to it directly over httpx; no SDK needed
since Compass speaks the same wire format as OpenAI's /chat/completions.
"""
from __future__ import annotations

import json
import time

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
    prompt_override: str | None = None,
) -> dict:
    customer_list = ", ".join(known_customers) if known_customers else "(none yet)"
    kind_list = ", ".join(known_kinds) if known_kinds else "(none yet — Emails and Files are common starting points)"
    default_instructions = (
        "Classify this inbox item along three axes. Respond with a single "
        "JSON object: {\"customer\": <name>, \"kind\": <label>, "
        "\"confidence\": <0-1 float, your confidence in the customer "
        "match>, \"recurring_candidate\": <true/false>}.\n\n"
        f"CUSTOMER — which customer/company it relates to. Already known: "
        f"{customer_list}. Reuse an exact existing name (same spelling/"
        "casing) when it clearly matches one. If it clearly relates to a "
        "real customer/company not yet in that list, propose a concise "
        "proper-noun name — new customers are expected. If you can't "
        "confidently tell, use an empty string \"\" rather than guessing.\n\n"
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
        "RECURRING_CANDIDATE — does this item look like a recurring, "
        "structured artifact: content that follows a repeating, patterned "
        "layout (consistent structure, labeled fields, tabular or "
        "itemized data) and reads like it was generated the same way each "
        "time, rather than a one-off free-form conversation? Judge this "
        "purely from the item's own structure and phrasing — never from "
        "which customer it's from or any specific known format. General "
        "illustrations of the category (an invoice, a weekly usage/"
        "consumption report, an automated recurring export) are just "
        "examples of the shape to recognize, not an exhaustive or "
        "matching list. Set true only when the structural signal is "
        "genuinely present; an ordinary conversational email is false.\n\n"
    )
    dynamic_content = f"From: {sender}\nSubject: {subject}\n\n{body[:4000]}"
    if prompt_override is not None:
        # Additive layering (ADR-044): the override REPLACES only the
        # hardcoded static instructions above -- the same real per-call
        # dynamic data (sender/subject/body) is still appended, verbatim.
        prompt = f"{prompt_override}\n\n{dynamic_content}"
    else:
        prompt = default_instructions + dynamic_content
    payload = {
        "model": settings.compass_model,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {settings.compass_api_key}",
        "Content-Type": "application/json",
    }
    # BUG-FIX 2026-08-17: found live that Compass intermittently times out
    # or returns an empty body for some real, large classify_email
    # requests (heavily-structured "Weekly Forecast"-style emails) --
    # up to 2 retries with a short backoff before giving up honestly.
    # Retries the WHOLE call (request + parse) since an empty-body
    # response is itself the observed failure mode, not just a transport
    # error httpx.HTTPError alone would catch.
    last_exc: Exception | None = None
    for attempt in range(3):
        if attempt:
            time.sleep(1.5 * attempt)
        try:
            response = httpx.post(
                settings.compass_base_url, headers=headers, json=payload, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {
                "customer": parsed.get("customer") or "",
                "kind": parsed.get("kind") or "Emails",
                "confidence": float(parsed.get("confidence", 0.0)),
                "recurring_candidate": bool(parsed.get("recurring_candidate", False)),
            }
        except httpx.HTTPError as exc:
            last_exc = CompassError(f"Compass call failed: {exc}")
        except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
            last_exc = CompassError(f"couldn't parse Compass response: {exc}")
    raise last_exc


def classify_task(
    subject: str,
    body: str,
    known_customers: list[str],
    prompt_override: str | None = None,
) -> dict:
    """Customer-only sibling to classify_email (ADR-027 point 4) -- a
    Task has no sender and needs no `kind` axis (its folder placement
    is fixed, Work/Tasks/, never Compass-classified), so reusing
    classify_email as-is would force a discarded kind guess into every
    call and misrepresent an absent sender inside a prompt worded
    around "inbox item"/`From:` framing designed for email. Same
    empty-string "unclassified" fallback posture as classify_email."""
    customer_list = ", ".join(known_customers) if known_customers else "(none yet)"
    default_instructions = (
        "Classify which customer/company this to-do task relates to. "
        "Respond with a single JSON object: {\"customer\": <name>, "
        "\"confidence\": <0-1 float>}.\n\n"
        f"Already known customers: {customer_list}. Reuse an exact "
        "existing name (same spelling/casing) when it clearly matches "
        "one. If it clearly relates to a real customer/company not yet "
        "in that list, propose a concise proper-noun name — new "
        "customers are expected. If you can't confidently tell, use "
        "an empty string \"\" rather than guessing.\n\n"
    )
    dynamic_content = f"Task subject: {subject}\n\n{body[:4000]}"
    if prompt_override is not None:
        prompt = f"{prompt_override}\n\n{dynamic_content}"
    else:
        prompt = default_instructions + dynamic_content
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
            "customer": parsed.get("customer") or "",
            "confidence": float(parsed.get("confidence", 0.0)),
        }
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise CompassError(f"couldn't parse Compass response: {exc}") from exc


def detect_customer_for_thread(
    thread_content: str,
    known_customers: list[str],
    prompt_override: str | None = None,
) -> dict:
    """Narrower sibling of classify_task (ADR-027 point 4's own "narrower
    sibling of classify_email" precedent, applied a fourth time --
    guess_project_for_thread and detect_customer_durable_fact were the
    second and third) -- REQ-SB-74-US-01-T01, ADR-055 Decision 2. Asks
    Compass for a Thread's own PRIMARY customer: reuse an exact known name
    when it clearly matches one, propose a new proper-noun name when it
    clearly relates to a real company not yet known, or answer with an
    empty string rather than guess -- the same honest three-way outcome classify_email/
    classify_task already established, so no extra Python-side confidence
    threshold logic is needed here. No retry loop (mirrors classify_task's
    own precedent, not classify_email's separate, unrelated retry
    bugfix)."""
    customer_list = ", ".join(known_customers) if known_customers else "(none yet)"
    default_instructions = (
        "Which real customer/company does this email thread primarily "
        "relate to? Respond with a single JSON object: {\"customer\": "
        "<name>, \"confidence\": <0-1 float>}.\n\n"
        f"Already known customers: {customer_list}. Reuse an exact "
        "existing name (same spelling/casing) when it clearly matches "
        "one. If it clearly relates to a real customer/company not yet "
        "in that list, propose a concise proper-noun name — new "
        "customers are expected. If you can't confidently tell, use "
        "an empty string \"\" rather than guessing.\n\n"
    )
    dynamic_content = f"{thread_content[:8000]}"
    if prompt_override is not None:
        prompt = f"{prompt_override}\n\n{dynamic_content}"
    else:
        prompt = default_instructions + dynamic_content
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
            "customer": parsed.get("customer") or "",
            "confidence": float(parsed.get("confidence", 0.0)),
        }
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise CompassError(f"couldn't parse Compass response: {exc}") from exc


def guess_project_for_thread(
    thread_summary: str,
    open_projects: list[str],
    prompt_override: str | None = None,
) -> dict:
    """Narrower sibling of classify_email/classify_task (ADR-027 point 4's
    own "narrower sibling of classify_email" precedent, applied a second
    time) -- the `Route-to-Project` Job's own Compass call
    (REQ-SB-55-US-01-T04, ADR-043 point 4). Asks Compass to pick the
    best-fitting name from the customer's own currently-open Projects, or
    propose a new, concise proper-noun Project name if none genuinely
    fit -- the same "don't guess wildly, propose a new one instead"
    posture classify_email's own `customer` axis already uses. Never
    forces a bad fit onto `open_projects` just because the list is
    non-empty; an empty `open_projects` list always produces a new-
    Project proposal."""
    project_list = ", ".join(open_projects) if open_projects else "(none currently open)"
    default_instructions = (
        "Which currently-open Project does this email conversation belong "
        "to? Respond with a single JSON object: {\"project\": <name>, "
        "\"confidence\": <0-1 float>}.\n\n"
        f"Currently-open Projects for this customer: {project_list}. Reuse "
        "an exact existing name (same spelling/casing) when it clearly "
        "matches one. If it clearly relates to a genuinely new, distinct "
        "piece of work not covered by any of those, propose a concise "
        "proper-noun Project name instead -- never force a bad fit onto an "
        "existing Project just because the list is non-empty.\n\n"
    )
    dynamic_content = f"{thread_summary[:4000]}"
    if prompt_override is not None:
        prompt = f"{prompt_override}\n\n{dynamic_content}"
    else:
        prompt = default_instructions + dynamic_content
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
        project = parsed.get("project")
        if not project:
            raise CompassError("Compass returned an empty project guess")
        return {
            "project": project,
            "confidence": float(parsed.get("confidence", 0.0)),
        }
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise CompassError(f"couldn't parse Compass response: {exc}") from exc


def detect_customer_durable_fact(
    evidence_text: str,
    customer: str,
    existing_background: str,
    prompt_override: str | None = None,
) -> dict:
    """Narrower sibling of guess_project_for_thread (ADR-027 point 4's own
    "narrower sibling of classify_email" precedent, applied a third time)
    -- the Customer Synthesizer's own Background-amendment durable-fact
    detection call (REQ-SB-57-US-01-T04). Grounds the prompt in BOTH the
    new `evidence_text` AND the Customer's own CURRENT `## Background`
    prose, explicitly asking whether `evidence_text` names a genuinely NEW
    durable fact not already reflected there -- an already-recorded fact
    naturally yields `has_durable_fact: false` (the honest dedup boundary
    this task deliberately relies on instead of building a second,
    separate dedup mechanism). Distinguishes a genuinely durable, permanent
    claim about the customer (a signed agreement, an org/ownership change,
    a strategic commitment) from routine activity/status noise (an
    ordinary reply, a scheduling email) -- only the former ever produces
    `has_durable_fact: true`."""
    background_excerpt = existing_background.strip() or "(none recorded yet)"
    default_instructions = (
        "Does the NEW EVIDENCE below contain a genuinely NEW, durable fact "
        f"about the customer \"{customer}\" -- a permanent or long-lived "
        "claim (e.g. a signed agreement, a contract term, an org/ownership "
        "change, a strategic commitment) -- that is NOT already reflected "
        "in the customer's EXISTING BACKGROUND below? Routine activity or "
        "status noise (an ordinary reply, a scheduling email, a routine "
        "status update) is NOT a durable fact. Respond with a single JSON "
        "object: {\"has_durable_fact\": <true/false>, \"fact\": <string, a "
        "concise one-sentence statement of the new fact, or \"\" if "
        "has_durable_fact is false>}.\n\n"
        f"EXISTING BACKGROUND:\n{background_excerpt}\n\n"
        "NEW EVIDENCE:\n"
    )
    dynamic_content = f"{evidence_text[:4000]}"
    if prompt_override is not None:
        prompt = f"{prompt_override}\n\n{dynamic_content}"
    else:
        prompt = default_instructions + dynamic_content
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
            "has_durable_fact": bool(parsed.get("has_durable_fact", False)),
            "fact": parsed.get("fact") or "",
        }
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise CompassError(f"couldn't parse Compass response: {exc}") from exc


def detect_mentioned_companies(
    content: str,
    source_description: str,
    prompt_override: str | None = None,
) -> dict:
    """The Librarian's own company-mention-extraction call
    (`REQ-SB-72-US-01-T05`, `ADR-049` Decision 5) -- mirrors `summarize_
    content`'s own TECHNIQUE (payload construction, `httpx.post`,
    `CompassError` handling) but with its OWN prompt and its OWN parse
    contract: `{"mentions": [{"name": str, "confidence": "high" | "low"},
    ...]}`. A genuinely different-shaped question from `summarize_
    content`'s single-string summary -- extracting POTENTIALLY MULTIPLE
    company names a Thread's own already-filed content mentions, never
    reused as a `prompt_override` layered onto `summarize_content` itself
    (that function's own parse contract only ever reads a `"summary"` key,
    never a list). Malformed/missing `"mentions"` raises `CompassError`,
    mirroring every other primitive in this module's own honest-failure
    contract -- never fabricates an empty or guessed list silently."""
    default_instructions = (
        "Identify every real company or organization name this content "
        "genuinely mentions -- distinct from whatever company this "
        "content's own primary Customer/account already is (do not "
        "include the primary Customer itself, only OTHER companies "
        "mentioned). Respond with a single JSON object: {\"mentions\": "
        "[{\"name\": <string, the company's proper name as written>, "
        "\"confidence\": \"high\" or \"low\"}, ...]}. Use \"high\" "
        "confidence only when the name is unambiguous and clearly a real "
        "company/organization; use \"low\" when it's a plausible but "
        "uncertain match, an abbreviation, or a name that could plausibly "
        "refer to more than one entity. Return {\"mentions\": []} if no "
        "other company is genuinely mentioned -- never invent or guess a "
        "name that isn't really there.\n\n"
    )
    dynamic_content = f"Source: {source_description}\n\n{content[:8000]}"
    if prompt_override is not None:
        prompt = f"{prompt_override}\n\n{dynamic_content}"
    else:
        prompt = default_instructions + dynamic_content
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
        raw_content = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
        mentions = parsed["mentions"]
        if not isinstance(mentions, list):
            raise CompassError("Compass returned a non-list 'mentions' value")
        return {
            "mentions": [
                {"name": m["name"], "confidence": m.get("confidence", "low")}
                for m in mentions
            ]
        }
    except (KeyError, IndexError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise CompassError(f"couldn't parse Compass response: {exc}") from exc


def extract_thread_companies_for_review(
    thread_content: str,
    known_companies: list[str],
    prompt_override: str | None = None,
) -> dict:
    """A new, narrower sibling of detect_mentioned_companies (ADR-049
    Decision 5's own multi-mention TECHNIQUE), never an edit to the frozen,
    Done detect_customer_for_thread (ADR-055 Decision 2) -- REQ-SB-76-US-01,
    ADR-057 Decision 1. Explicitly instructs Compass to DISREGARD any
    company/product/device name appearing ONLY inside an email-client or
    device signature line ("Sent from my iPhone," "Get Outlook for
    Android"), a mailing-list footer, or a legal disclaimer -- these are
    NOT genuine mentions, the root-cause fix for this requirement's own
    self-reinforcing-noise finding. Identifies EVERY real company the
    Thread's own substantive content genuinely relates to (not scoped to
    "besides an already-known primary Customer" -- detect_mentioned_
    companies's own different framing), reusing an exact known name from
    known_companies (the UNION of list_customer_folders() + list_known_
    partners(), never hardcoded) when it clearly matches one. Returns
    {"companies": [{"name": str, "confidence": float}, ...]}. Malformed/
    missing "companies" raises CompassError, mirroring every sibling
    primitive's own honest-failure contract."""
    company_list = ", ".join(known_companies) if known_companies else "(none yet)"
    default_instructions = (
        "Identify every real company or organization this email thread's "
        "own substantive content genuinely relates to. Respond with a "
        "single JSON object: {\"companies\": [{\"name\": <string, the "
        "company's proper name as written>, \"confidence\": <0-1 float>}, "
        "...]}.\n\n"
        f"Already known companies: {company_list}. Reuse an exact existing "
        "name (same spelling/casing) when it clearly matches one.\n\n"
        "IMPORTANT — DO NOT include a name that appears ONLY inside an "
        "email-client or device signature line (e.g. \"Sent from my "
        "iPhone,\" \"Get Outlook for Android\"), a mailing-list footer, or "
        "a legal disclaimer -- these are not genuine mentions of that "
        "company, only boilerplate text automatically appended by the "
        "email client or device, and must never be returned as a company. "
        "Only include a company that the thread's own substantive, "
        "human-written content genuinely relates to. Return {\"companies\": "
        "[]} if no real company is genuinely mentioned -- never invent or "
        "guess a name that isn't really there.\n\n"
    )
    dynamic_content = f"{thread_content[:8000]}"
    if prompt_override is not None:
        prompt = f"{prompt_override}\n\n{dynamic_content}"
    else:
        prompt = default_instructions + dynamic_content
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
        raw_content = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
        companies = parsed["companies"]
        if not isinstance(companies, list):
            raise CompassError("Compass returned a non-list 'companies' value")
        return {
            "companies": [
                {"name": c["name"], "confidence": float(c.get("confidence", 0.0))}
                for c in companies
            ]
        }
    except (KeyError, IndexError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise CompassError(f"couldn't parse Compass response: {exc}") from exc


def summarize_content(
    content: str,
    source_description: str,
    prompt_override: str | None = None,
) -> dict:
    """Summarizes already-extracted text content (never a raw binary --
    T01's upload_storage.extract_text_content has already produced plain
    text by the time this is called). Same payload construction and
    CompassError handling as classify_email/classify_task (ADR-034 point
    3) -- no new dependency, no new error-handling shape."""
    default_instructions = (
        "Summarize the following document's actual content, concisely "
        "and accurately, for filing into a personal knowledge base. "
        "Respond with a single JSON object: {\"summary\": <string>}. "
        "Base the summary strictly on the real content below -- never "
        "invent, generalize, or pad with placeholder content.\n\n"
    )
    dynamic_content = f"Source: {source_description}\n\n{content[:8000]}"
    if prompt_override is not None:
        prompt = f"{prompt_override}\n\n{dynamic_content}"
    else:
        prompt = default_instructions + dynamic_content
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
        raw_content = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
        summary = parsed.get("summary")
        if not summary:
            raise CompassError("Compass returned an empty summary")
        return {"summary": summary}
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise CompassError(f"couldn't parse Compass response: {exc}") from exc
