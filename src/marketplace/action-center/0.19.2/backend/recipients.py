"""Who a chase about one action goes to.

An ask often names more than one person -- "Ahmed and Will", "Core42 (Maiyas,
Fares)" -- and until now that was a reason NOT to chase it: the note carries one
`owner_email`, so the mail could only go to one of them, and the split agent was
supposed to cut the ask in two first.

It goes to all of them instead, on one message (operator, 2026-09-26): they see
each other, so a reply tells everybody where the ask stands, and the one who
already did their half is not nudged for it again a week later.

So the parties in the owner field are resolved here, each to whatever address is
known for it:

1. the **owner book** -- what the operator or an agent already decided that name
   means (`Settings/Action-Owners.md`);
2. the **thread the ask was sent in** -- a name not in the book is often right
   there in the message's own recipients;
3. the **action's own `owner_email`**, which is what the capture recorded and is
   never dropped, even when it matches no party by name.

A party nothing resolves is still listed, without an address: the screen shows
it greyed rather than pretending the ask is owed by fewer people than it is.
"""
from __future__ import annotations

from .owner_book import read as read_book
from .parties import naming_words, parties


def _text(value) -> str:
    return str(value or "").strip()


def for_action(view, action: dict) -> list[dict]:
    """`[{"name", "email", "source"}]` -- everyone this action is owed by, in the
    order the owner field names them."""
    owner = _text(action.get("owner"))
    named = parties(owner) or ([owner] if owner else [])
    book = read_book(view.api)
    on_thread = view.people_on(action)
    noted = _text(action.get("owner_email")).lower()

    found: list[dict] = []
    for position, name in enumerate(named):
        email, source = "", ""
        decided = book.get(name.lower()) or {}
        if _text(decided.get("email")):
            email, source = _text(decided["email"]).lower(), "book"
        if not email:
            words = naming_words(name)
            for person in on_thread:
                if words and (words & naming_words(person["name"])
                              or words & naming_words(person["email"].split("@")[0])):
                    email, source = person["email"].lower(), "thread"
                    break
        # The first party is who the capture had in mind when it wrote the
        # address down, so that is where the action's own address belongs.
        if not email and position == 0 and noted:
            email, source = noted, "action"
        found.append({"name": name, "email": email, "source": source})

    # An address the note carries that matched nobody by name still owes the
    # thing -- the note says so, and a name it could not match is not a reason
    # to leave the one person we can actually write to off the mail.
    if noted and not any(person["email"] == noted for person in found):
        found.insert(0, {"name": named[0] if named else owner,
                         "email": noted, "source": "action"})

    # An owner field is not a list of people just because it contains a comma.
    # "Maldonado, Bobbie" is one person written surname first and "FP&A" is one
    # team, and taking either apart gives fragments -- which must never become
    # rows the screen offers to email. Two fragments of one name resolve to the
    # same address, or to none at all.
    placed: dict[str, dict] = {}
    shared = False
    for person in found:
        if not person["email"]:
            continue
        if person["email"] in placed:
            shared = True
        else:
            placed[person["email"]] = person
    if not placed:
        # Nothing could be placed: the ask is owed by whoever the field says,
        # written as it is written, with no address.
        return [{"name": owner, "email": "", "source": ""}] if owner else []

    people = list(placed.values())
    if shared and len(people) == 1:
        # Every fragment was the same person; call them what the action calls
        # them rather than by whichever fragment resolved first.
        people[0] = {**people[0], "name": owner}

    # A party nothing could place is still shown -- the ask is owed by that many
    # people whether or not the vault can say where to write -- unless its words
    # are already in somebody placed, which makes it half of their name.
    spoken_for = {word for person in people
                  for word in naming_words(person["name"]) | naming_words(
                      person["email"].split("@")[0].replace(".", " "))}
    people += [person for person in found
               if not person["email"] and not (naming_words(person["name"]) & spoken_for)]
    return people


def across_the_ask(view, action: dict) -> tuple[list[dict], list[str]]:
    """`(everyone who owes this ask, the actions it covers)`.

    One ask given to four people is four actions and one email (operator,
    2026-09-26), so the screen has to gather across all of them -- and chasing
    from any one of them chases the lot."""
    people = for_action(view, action)
    stems = [action["stem"]]
    for shared in view.same_ask(action):
        stems.append(shared["stem"])
        known = {person["email"] for person in people if person["email"]}
        for person in for_action(view, shared):
            if person["email"] and person["email"] not in known:
                people.append(person)
    return people, stems


def settled_on(action: dict) -> list[str]:
    """The addresses the operator settled on for this action, from its own
    `chase_to` field -- empty when he never narrowed it."""
    value = action.get("chase_to")
    parts = value if isinstance(value, list) else str(value or "").replace(";", ",").split(",")
    found = []
    for part in parts:
        address = _text(part).lower()
        if address and address not in found:
            found.append(address)
    return found


def addressable(people: list[dict]) -> list[str]:
    """Just the addresses, in order -- what a chase is actually sent to."""
    return [person["email"] for person in people if person["email"]]
