"""A name, an alias or an email domain -> `(kind, tag, hub)`
(`REQ-SB-95-US-05-T03`, `ADR-037`, `ADR-035`).

Generic over any `<namespace>/<slug>` tag. This module knows no kinds, no
vocabulary and no plugin: every name it can answer to was handed to it by
whoever registered the namespace, and `kind` travels back out exactly as it
came in. That is `ADR-022`'s test in code -- a second brain built for someone
who tracks nothing but books must get the same resolver.

**A registry lookup, never a fuzzy search over note titles.** Nothing here
reads a note, searches the vault or asks the index what a note is called. A
name that is not registered does not resolve, however many notes are titled
after it: guessing from a title is the failure this story exists to remove,
because a guess that happens to be right teaches a caller to trust the one
that is wrong.

**Asked at the moment of the question, every time.** The registered
`entries()` callable is invoked per resolution and nothing it returns is kept
between calls -- the registry behind it is edited while the app runs
(`ADR-037`), so a cached answer is a wrong answer waiting for lunchtime.

**Synthesis first, then evidence -- carried in the shape, not in a
convention.** A resolution hands back the `hub` (the entity's own synthesis
note) and, separately, the `tag` that scopes its evidence. It returns no notes
at all, so nothing downstream can serve thirty tagged Threads ahead of the one
hub note without having first been told where that hub is. An entry that
registers no hub resolves with `hub = None` and says so in its message, rather
than letting a reader quietly lead with evidence.

**Three non-answers, three shapes, never one borrowed for another.** A
resolution is `resolved`, `ambiguous` (named candidates, never silently picked
-- the `provide_service` precedent) or `did_not_resolve` (the name repeated
exactly as asked). A namespace whose callable raises is skipped and logged and
its failure is carried on the result (the `register_agent_matcher` precedent),
so "nothing knows that name" is never confused with "something could not be
asked". The same rule governs `report_unknown_tags`: a tag key whose namespace
could not answer is reported as exactly that and never counted as unknown, and
when the index itself cannot be read every payload is `None` rather than an
empty list a caller could mistake for "we looked, there was nothing".

Zero registered namespaces therefore means nothing resolves, honestly --
`ADR-035`'s "degrade to nothing rather than to a wrong answer".
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.business.core.plugins.plugin_manager import PluginManager
from app.business.core.vault.vault_manager import VaultManager

_logger = logging.getLogger(__name__)

RESOLVED = "resolved"
AMBIGUOUS = "ambiguous"
DID_NOT_RESOLVE = "did_not_resolve"

_TAG_NAMESPACE_SEPARATOR = "/"
_EMAIL_ADDRESS_SEPARATOR = "@"

_plugin_manager = PluginManager()
_vault_manager = VaultManager()


@dataclass
class NamespaceCouldNotAnswer:
    """One registered namespace that was asked and did not answer, with the
    verbatim reason. Its existence is what stops a thin answer being read as a
    confident one."""
    namespace: str
    plugin_id: str
    failure: str


@dataclass
class TagCandidate:
    """One registered entry as the resolver sees it: the tag that scopes its
    evidence, the hub that holds its synthesis, and the `kind` its own
    registrar gave it -- carried, never interpreted."""
    kind: object
    tag: str
    hub: str | None
    namespace: str
    plugin_id: str
    registered_name: object


@dataclass
class TagResolution:
    """What one name resolved to, or honestly did not.

    `resolved` is the one field a caller must branch on, for the reason
    `ActionCallVerdict.accepted` is separate from its `outcome`: a caller that
    had to enumerate outcomes to learn whether it got an answer would read any
    outcome added later as success.
    """
    name_as_asked: str
    outcome: str
    resolved: bool
    message: str
    kind: object = None
    tag: str | None = None
    hub: str | None = None
    namespace: str | None = None
    plugin_id: str | None = None
    candidates: list[TagCandidate] = field(default_factory=list)
    namespaces_that_could_not_answer: list[NamespaceCouldNotAnswer] = field(default_factory=list)

    @property
    def every_namespace_answered(self) -> bool:
        """False when this answer was reached without every registered
        namespace having been heard from -- a `did_not_resolve` that is
        incomplete rather than final."""
        return not self.namespaces_that_could_not_answer


@dataclass
class UnknownTagReport:
    """Every `<namespace>/<slug>` tag the vault holds, sorted into what is
    known about it -- and what could not be found out.

    The lists are `None`, not empty, when the index could not be read: an
    empty list means "it was read and there were none", and a failed read may
    never borrow that look (`SPRINT-091` retro).
    """
    index_was_read: bool
    index_failure: str | None
    unknown_tags: list[str] | None
    known_tags: list[str] | None
    tags_whose_namespace_could_not_answer: list[str] | None
    registered_tags_with_no_notes: list[str] | None
    namespaces_that_could_not_answer: list[NamespaceCouldNotAnswer]
    message: str

    @property
    def is_complete(self) -> bool:
        return self.index_was_read and not self.namespaces_that_could_not_answer


def resolve(name: str) -> TagResolution:
    """Turn one name, alias or email domain into `(kind, tag, hub)` by asking
    every registered namespace what it currently holds.

    Matching is case-insensitive and exact: a name equal to the entry's own
    name or to one of its aliases, or a domain equal to one of its domains --
    given either bare (`example.invalid`) or as an address at it
    (`someone@example.invalid`). Nothing is matched by prefix, substring or
    similarity, because a near-miss answered confidently is the whole problem.
    """
    name_as_asked = name if isinstance(name, str) else str(name)
    candidates, namespaces_that_could_not_answer = _candidates_matching(name_as_asked)

    if len(candidates) == 1:
        matched = candidates[0]
        hub_note = (
            f"; synthesis in {matched.hub}" if matched.hub
            else "; it registers no hub note, so there is no synthesis to read before its evidence"
        )
        return TagResolution(
            name_as_asked=name_as_asked,
            outcome=RESOLVED,
            resolved=True,
            message=f'"{name_as_asked}" resolves to {matched.tag}{hub_note}',
            kind=matched.kind,
            tag=matched.tag,
            hub=matched.hub,
            namespace=matched.namespace,
            plugin_id=matched.plugin_id,
            candidates=candidates,
            namespaces_that_could_not_answer=namespaces_that_could_not_answer,
        )

    if len(candidates) > 1:
        named = "; ".join(
            f"{candidate.tag} (kind {candidate.kind!r}, registered by {candidate.plugin_id})"
            for candidate in candidates
        )
        return TagResolution(
            name_as_asked=name_as_asked,
            outcome=AMBIGUOUS,
            resolved=False,
            message=(
                f'"{name_as_asked}" is ambiguous: {len(candidates)} registered entries match it, '
                f"and none of them is being picked for you -- {named}"
            ),
            candidates=candidates,
            namespaces_that_could_not_answer=namespaces_that_could_not_answer,
        )

    unheard = ""
    if namespaces_that_could_not_answer:
        unheard = (
            f"; {len(namespaces_that_could_not_answer)} registered namespace(s) could not be asked "
            f"({', '.join(failure.namespace for failure in namespaces_that_could_not_answer)}), "
            f"so this is incomplete rather than final"
        )
    return TagResolution(
        name_as_asked=name_as_asked,
        outcome=DID_NOT_RESOLVE,
        resolved=False,
        message=(
            f'"{name_as_asked}" did not resolve: no registered tag namespace knows that name, '
            f"alias or domain{unheard}"
        ),
        namespaces_that_could_not_answer=namespaces_that_could_not_answer,
    )


def report_unknown_tags() -> UnknownTagReport:
    """Every tag key the vault holds, named and sorted into known, unknown,
    and could-not-be-found-out -- plus the registered tags no note carries.

    The index keys every `<namespace>/<slug>` tag present whether or not its
    namespace is registered (`T01`, AC-07), so an unknown key is a real fact
    about the install and is reported by name rather than dropped. "Unknown"
    is reserved for a tag whose namespace nobody claims: a tag whose namespace
    is registered but could not answer is a separate list, because calling it
    unknown would turn a failed read into a finding.
    """
    try:
        tag_keys = _vault_manager.get_tag_index_keys()
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
        _logger.warning("the tag-keyed index could not be read, so no tag can be called unknown: %s", failure)
        return UnknownTagReport(
            index_was_read=False,
            index_failure=failure,
            unknown_tags=None,
            known_tags=None,
            tags_whose_namespace_could_not_answer=None,
            registered_tags_with_no_notes=None,
            namespaces_that_could_not_answer=[],
            message=(
                "the tag-keyed index could not be read, so nothing is being reported as unknown: "
                f"{failure}"
            ),
        )

    registered_tags: set[str] = set()
    namespaces_that_could_not_answer: list[NamespaceCouldNotAnswer] = []
    unanswered_prefixes: set[str] = set()
    for registration in _plugin_manager.get_tag_namespaces():
        entries, could_not_answer = _entries_of(registration)
        if could_not_answer is not None:
            namespaces_that_could_not_answer.append(could_not_answer)
            unanswered_prefixes.add(could_not_answer.namespace)
            continue
        for entry in entries:
            candidate = _candidate_from(registration, entry)
            if candidate is not None:
                registered_tags.add(candidate.tag)

    known_tags: list[str] = []
    unknown_tags: list[str] = []
    tags_whose_namespace_could_not_answer: list[str] = []
    for tag in tag_keys:
        if tag in registered_tags:
            known_tags.append(tag)
        elif tag.partition(_TAG_NAMESPACE_SEPARATOR)[0] in unanswered_prefixes:
            tags_whose_namespace_could_not_answer.append(tag)
        else:
            unknown_tags.append(tag)

    unheard = ""
    if namespaces_that_could_not_answer:
        unheard = (
            f"; {len(tags_whose_namespace_could_not_answer)} further tag(s) could not be classified "
            f"because {len(namespaces_that_could_not_answer)} namespace(s) could not be asked "
            f"({', '.join(failure.namespace for failure in namespaces_that_could_not_answer)})"
        )
    return UnknownTagReport(
        index_was_read=True,
        index_failure=None,
        unknown_tags=unknown_tags,
        known_tags=known_tags,
        tags_whose_namespace_could_not_answer=tags_whose_namespace_could_not_answer,
        registered_tags_with_no_notes=sorted(registered_tags.difference(tag_keys)),
        namespaces_that_could_not_answer=namespaces_that_could_not_answer,
        message=(
            f"{len(tag_keys)} tag(s) in the vault: {len(known_tags)} registered, "
            f"{len(unknown_tags)} with no registered entry behind them{unheard}"
        ),
    )


def _candidates_matching(name_as_asked: str) -> tuple[list[TagCandidate], list[NamespaceCouldNotAnswer]]:
    asked_spelling = _normalized(name_as_asked)
    asked_domain = _normalized_domain(name_as_asked)
    matched: list[TagCandidate] = []
    already_matched_identity_keys: set[tuple] = set()
    namespaces_that_could_not_answer: list[NamespaceCouldNotAnswer] = []

    for registration in _plugin_manager.get_tag_namespaces():
        entries, could_not_answer = _entries_of(registration)
        if could_not_answer is not None:
            namespaces_that_could_not_answer.append(could_not_answer)
            continue
        for entry in entries:
            if not _entry_answers_to(entry, asked_spelling, asked_domain):
                continue
            candidate = _candidate_from(registration, entry)
            if candidate is None:
                continue
            # Two registrations of the identical thing are one candidate; two
            # that differ in tag, kind or hub are a genuine ambiguity, because
            # picking either would be answering a question the data cannot.
            identity = (candidate.tag, repr(candidate.kind), candidate.hub)
            if identity in already_matched_identity_keys:
                continue
            already_matched_identity_keys.add(identity)
            matched.append(candidate)
    return matched, namespaces_that_could_not_answer


def _entries_of(registration: dict) -> tuple[list, NamespaceCouldNotAnswer | None]:
    """What one namespace holds right now, or why it could not say."""
    namespace = str(registration.get("namespace") or "")
    plugin_id = str(registration.get("plugin_id") or "")
    ask = registration.get("entries")

    if not callable(ask):
        return [], _could_not_answer(
            namespace, plugin_id, f"its entries are a {type(ask).__name__}, not a callable",
        )
    try:
        # Arbitrary third-party code: anything it raises is its failure to
        # answer, never this resolver's failure to run (`ADR-037`).
        entries = ask()
    except Exception as exc:
        return [], _could_not_answer(namespace, plugin_id, f"{type(exc).__name__}: {exc}")
    if not isinstance(entries, list):
        return [], _could_not_answer(
            namespace, plugin_id, f"it returned a {type(entries).__name__}, not a list of entries",
        )
    return entries, None


def _could_not_answer(namespace: str, plugin_id: str, failure: str) -> NamespaceCouldNotAnswer:
    _logger.warning(
        "tag namespace %r (plugin %r) could not be asked for its entries and is skipped for this "
        "resolution; every other namespace still answers: %s",
        namespace, plugin_id, failure,
    )
    return NamespaceCouldNotAnswer(namespace=namespace, plugin_id=plugin_id, failure=failure)


def _entry_answers_to(entry: object, asked_spelling: str, asked_domain: str) -> bool:
    if not isinstance(entry, dict):
        return False
    if asked_spelling:
        spellings = [entry.get("name"), *_texts(entry.get("aliases"))]
        if any(_normalized(spelling) == asked_spelling for spelling in spellings if _normalized(spelling)):
            return True
    if asked_domain:
        domains = _texts(entry.get("domains"))
        if any(_normalized_domain(domain) == asked_domain for domain in domains if _normalized_domain(domain)):
            return True
    return False


def _candidate_from(registration: dict, entry: object) -> TagCandidate | None:
    if not isinstance(entry, dict):
        return None
    namespace = str(registration.get("namespace") or "").strip().strip(_TAG_NAMESPACE_SEPARATOR)
    slug = entry.get("slug")
    slug = slug.strip().strip(_TAG_NAMESPACE_SEPARATOR) if isinstance(slug, str) else ""
    if not namespace or not slug:
        _logger.warning(
            "an entry registered under tag namespace %r (plugin %r) names no slug, so it has no "
            "`<namespace>/<slug>` tag and is skipped: resolving it would scope a read to nothing",
            namespace, registration.get("plugin_id"),
        )
        return None
    hub = entry.get("hub")
    return TagCandidate(
        # Opaque, both ways: never coerced, defaulted, enumerated or checked
        # against a list. What kinds exist belongs to whoever registered them.
        kind=entry.get("kind"),
        tag=f"{namespace}{_TAG_NAMESPACE_SEPARATOR}{slug}",
        hub=hub if isinstance(hub, str) and hub.strip() else None,
        namespace=namespace,
        plugin_id=str(registration.get("plugin_id") or ""),
        registered_name=entry.get("name"),
    )


def _texts(value: object) -> list[object]:
    """A list-valued field as a list. A bare string is one value, never its
    own characters."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return []


def _normalized(text: object) -> str:
    return text.strip().casefold() if isinstance(text, str) else ""


def _normalized_domain(text: object) -> str:
    """The domain part, whether a bare domain or an address at it was given --
    `Example.Invalid`, `@example.invalid` and `Someone@Example.Invalid` are
    one domain."""
    return _normalized(text).lstrip(_EMAIL_ADDRESS_SEPARATOR).rpartition(_EMAIL_ADDRESS_SEPARATOR)[2]
