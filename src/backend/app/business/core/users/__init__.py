"""Users, roles and sessions -- who a person is and what they may do
(REQ-SB-101). Instance data in a SQLite database at
`<SECOND_BRAIN_DATA_PATH>/auth/users.db`, never the repository.

**Configuration, not a catalogue.** Accounts are not an artifact kind:
there is no export, no import, no bundle and no Marketplace package that
carries them. A user store is the one thing in this install that must not
travel to another machine.

**Identity is personal; the knowledge base is shared** (REQ-SB-101, the
operator's choice of shape). One vault, one set of agents, one Operator
Profile -- and now several people, each signing in as themselves. That is
why nothing here touches `SELF_EMAIL`, the Operator Profile or the vault:
a user is a person who uses this install, not a second operator it acts
for.

**The three roles are a matrix, in `user.py`, as data.** Correcting what
a Power User may do is one edit there. One row -- authoring Actions and
Workflows -- is deliberately still open and sits with Admin until the
operator settles it.

Three modules, by layer: `user.py` is the shape and the matrix,
`password_hashing.py` is the one place a credential is turned into a
digest, and `user_manager.py` is the sole gateway onto the store. Raw I/O
is `app/data_access/users_db.py` and nothing above the Manager touches it.
"""
