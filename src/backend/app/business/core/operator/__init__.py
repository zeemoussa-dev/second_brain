"""Operator Profile -- the one record of who this install's agents act
for: the operator's name, their OTHER mail addresses, their timezone,
and their team as `email` + `role` entries. Instance data under the App
Database Folder at data/Operator/Profile.json, never the repository.

**Configuration, not a catalogue** (ADR-032). It is a singleton: one
record, no list, no create, no delete, no id namespace -- which is why
this package has no `get_all` anywhere in it and why nothing here is an
exportable artifact kind.

**Membership, not copies.** A team entry is an email and a role and
nothing else about the person. The vault's Person notes are filenamed by
email, so the email IS the join key and a second description of a
colleague would only be a copy that goes stale.

**The operator's own address is mirrored, never owned** (ADR-038). It
stays the SELF_EMAIL setting, edited on Settings > System; this package
reads it and never writes it.

OperatorProfileManager is the sole gateway onto this record. See
operator_profile.py for the shape, operator_profile_manager.py for the
Manager itself.
"""
