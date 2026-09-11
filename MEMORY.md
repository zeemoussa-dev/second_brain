# MEMORY

Framework memory: the standing rules an agent must know to change this
codebase without breaking it. Rules only - no history, no narrative.

## Which memory am I writing to?

| Memory | Where | Scope |
|---|---|---|
| **Framework** | this file | true on every install; ships with the product |
| **Instance** | `<SECOND_BRAIN_DATA_PATH>/AGENT-MEMORY.md` | one machine's paths, vault, mailbox, model, keys, live state |
| **Another operator's instance** | their machine | never read or written from here |

**The test:** would this still be true on a fresh install with a different
vault and mailbox? **Yes -> here. No -> that machine's `AGENT-MEMORY.md`.**
Never put a real vault path, mailbox, key or machine name in this file; use
`<OPERATOR_VAULT>` / `<operator>` placeholders.

Where a rule does not belong here:

- an architectural choice about tools, frameworks or boundaries -> `Implementation/Architecture/ADR.md`
- a sprint-level heuristic ("when X, prefer Y") -> `Implementation/Learnings.md`
- what was built, fixed or discovered on a date -> `CHANGELOG.md`
- how the product is shaped, for building a new install -> `Documentation/Framework/`

## Rules for writing to this file

1. **Budget: 40 KB.** Check the file size before appending. Over budget you
   may not append - either REPLACE a rule this one supersedes, or route the
   entry to one of the four destinations above. Never append and promise to
   trim later.
2. **One entry is one rule.** What is forbidden or required, then why, under
   400 characters. No date stamp, no story or sprint ID, no symptom
   description, no investigation narrative. If the story matters it belongs
   in `CHANGELOG.md`, and the rule carries a pointer, not a retelling.
3. **Never write here while investigating.** When a failure is fixed AND
   verified, write at most one rule stating what must never happen again.
   The symptom, the false starts and the root-cause trail go to `BUGS.md` or
   the task's own Implementation Log. A failure that produced no reusable
   rule produces no entry at all.
4. **Reason from the current code, not from this file.** If a rule names a
   subsystem, check it still exists before building on it.

---

## Vault engine and templates

- **`src/backend/app/vault/vault_manager.py` is an OLDER engine than the canonical copy at `app/business/core/skills/managers/vault_manager.py`.** It has no `create_dynamic_child()`, no `_section_allowed_callers` and no `data_root()`. Never assume a capability documented for the engine exists in the backend's copy - check the file you are actually importing.

- **Never key a cross-directory collection by bare filename or stem.** Collisions are real wherever the same entity is legitimately linked from more than one folder: whichever note collides second silently wins, and the other becomes invisible to index, overview and search. Key by full path. `vault_indexing.py` still carries this defect.

- **`modify_section()`/`create()` match the `section` argument against `Template.json`'s `root.sections[].name` by exact string equality, and that name is the bare title with no `## ` prefix.** Passing `"## Related"` does not raise; it silently falls through to the undeclared-section path.

- **`vault_manager.update()` has no safe no-op on a file without a frontmatter fence.** It always prepends a synthetic block, where `vault_lib.upsert_frontmatter_key()` silently no-ops on the same input. Never point `update()` at a file that may legitimately carry no frontmatter.

- **`create_dynamic_child()` can only write a body through its declared `"## Header"` sections list; it cannot write a flat headerless body.** A note kind whose body is raw text needs the explicit `body` parameter instead of a sections list.

- **`vault_manager.py`'s frontmatter reader is hand-rolled, not YAML: it round-trips scalars and homogeneous lists of quoted strings only.** A list of dicts writes a plausible-looking line and silently reads back as an empty list, with no error on either side.

- **Every Hermes-side Skill script must resolve the App Database Folder through `vault_manager.data_root()`, never a hardcoded `<vault>/.second-brain`.** `data_root()` honours `SECOND_BRAIN_DATA_PATH` and falls back to the historical in-vault location. Hardcoding it caused a full day of silently dropped email capture after the config/vault split.

- **An `_iter_*` scan that identifies records by folder shape must also check content - a frontmatter `type`, an `id` - before treating a match as authoritative.** Path shape alone is not identity: an Opportunity's folder satisfies the same shape test as a Customer hub, and a scan that trusted shape corrupted 10 of 13 real Opportunities.

- **`create_companies_partners.py` gates hub creation on a local path-existence check at the exact location the Entities row implies, not a vault-wide title search.** A real hub nested under a different parent is therefore not found and a duplicate is created. Search by title before creating.

- **Never trust a previously-recorded inventory of deployed file copies - re-enumerate live before any resync.** The last recorded count of `vault_manager.py` copies was badly stale: 9 in-repo and 73 deployed when actually checked.

- **Message-note filenames need time-of-day, not just date: `<date> <HH:MM> <sender>`.** Date plus sender collapses whenever the same sender posts twice in a thread on one day, and the hash-suffix fallback still reads as a duplicate name in Obsidian.

- **[2026-09-06] Entity Templates ("Master Templates") ship with the product, and every Template file declares its own `schema_version`.** Reason: nothing shipped before — all 11 lived only in one operator's App Database Folder, no `Template.json` was tracked in the repo, and the setup wizard seeded none, so a fresh install had **no vault structure at all** and every capture Skill would have failed. They live at `src/backend/app/business/core/templates/masters/<id>/Template.json`. A Master Template is a **vault structure and nothing else**, and the dependency is strictly one-directional: a Skill needs a Template; a Template knows nothing about Skills. That is what makes it shippable and versionable independently of the capability layer. `allowed_callers` — which names Skill Actions inside a Template — is a **reverse edge** that contradicts the dependency resolver's own "a Template has no further real dependencies of its own", and is to be removed in the same change that lets a Skill declare `writes: [thread.Summary, ...]`; removing it earlier would silently *loosen* access control rather than relocate it. Note what it does and does not protect: across all 11 templates it appears only on `machine_write` sections, never on `human_only`, so what keeps agents out of the operator's own writing is `access`, which names nobody.

- **[2026-09-06] `allowed_callers` no longer lives in an Entity Template. A Skill declares `writes:` in its `SKILL.md` frontmatter, and the backend derives `<data>/data/section_access.json` from what is actually DEPLOYED; the shared `vault_manager` reads that map at write time.** Reason: naming Skill Actions inside `Template.json` was a **reverse edge** — a vault *structure* definition depending on the capability layer — which contradicted the dependency resolver's own "a Template has no further real dependencies of its own" and meant a Master Template could not be shipped or versioned without knowing which Skills exist. `ADR-017`'s per-caller enforcement is **preserved**, not dropped: the migration was verified lossless (the derived map reproduced exactly what the templates declared) before the field was removed. Derived beats authored — the map is a projection of the deployed set, republished on every deploy/undeploy, so it cannot name an Action that is not deployed, and it cannot rot against a renamed script the way the hand-maintained string list silently did. `SkillManager.validate_declared_writes` enforces the intersection the model rests on (a Skill may write `T.S` only if it declares `T.S` **and** `T` marks `S` `machine_write`) and `deploy()` refuses rather than shipping something that fails only when it runs. Be precise about what moved: `allowed_callers` only ever appeared on `machine_write` sections, never on `human_only` — what keeps agents out of the operator's own writing is `access`, which names nobody and stays in the Template.

- **[2026-09-06] Three versions, deliberately distinct: `Template.schema_version` (how to PARSE the file), `Template.version` (what the CONTENT promises — which sections exist), and the Skill's own `version` (what is shipped).** A Skill declares `requires:` against the *content* version, never the schema one. The comparison is **EXACT, not `>=`**: a content bump means a section was removed or renamed, so an older Skill is wrong rather than merely behind — `>=` would wave through a Skill written for v1 against a v2 that dropped the very section it writes, which is the failure the check exists to catch. `requires` is optional; without it a declaration is checked structurally only. Conflating schema with content version is what the v1/v2 defect already cost a debugging session over.

- **A long-path walk must hand back PLAIN paths - rebuild each result against the original root, never strip the `\?\` prefix by hand.** `os.walk(long_path(root))` yields prefixed paths; returning those breaks callers silently, because `relative_to(vault_path)` raises `ValueError` and every returned path compares unequal to the plain one the caller holds. Use `root / os.path.relpath(found, walk_root)`. Plain paths are safe to return only where the module's own I/O re-applies `long_path`: `read_note`, `write_note` and the section writers do. **`write_note` did NOT until 2026-09-11** -- this entry claimed it did, and every engine write to a note past the limit failed, including the `id` an applier mints on first touch. Verify a claim like this against the code before relying on it. Never re-guard the results with `is_file()`: past MAX_PATH it silently returns `False` and drops exactly the notes the long-path walk exists to reach.

- **Resolve a schema/format version ONCE and explicitly, never per-field with `.get(key, default)` fallbacks.** `.get()` with a default cannot tell "absent" from "named differently in this version" - it returns the default for both, silently. Reading v1 field names out of v2 Template files made all 11 parse to zero sections with `error=None`, for weeks, invisibly. When a format gains a second version, the FIRST change is a version field in the file.

- **[2026-09-11] A Template change only shapes notes created AFTERWARDS. Adding or renaming a section is half a change; the other half is a migration script for the notes already in the vault.** Reason: renaming `Log & Captures` to `History & Captures` in three templates left 195 real hubs untouched, and the code that CREATED `<Name>-log.md` was a separate concern again — so the next creation pass would have recreated the old child beside the migrated one, and `apply_thread_review` would have appended history entries into a file nothing indexed. A rename lands in three places, not one: the Template, every writer that constructs the path or heading by hand, and a migration for existing notes. Grep the whole catalog for the old name before calling a rename done.

- **[2026-09-11] A child note must be findable on its own, not only through its parent.** A `parent:` field links it structurally, but tag search is how the vault is actually queried — a search for a company returned the hub and silently skipped the History and Captures notes holding its entire relationship record. Every child note carries both its parent entity's tag and its own `kind/<type>` tag. Use `merge_tags` (additive) so an operator's own tags survive.

- **[2026-09-11] Section order on an existing note is not self-correcting.** A backfill that inserts missing sections appends them, so a hub repaired after a template change ends up with `Summary` below `Affiliates` while a freshly-created one is correct. Two notes of the same type reading differently is the mess. Reorder against the template's declared order, moving each block WITH its content, and keep any unrecognised heading after the known ones — it is far more likely to be something a human added than something safe to drop.

- **[2026-09-11] A recurring `--no-agent` cron delivers its stdout verbatim, so a job with nothing to report must print NOTHING.** Reason: the 30-minute hub job printed the ~200 entity names it had correctly done nothing about, which would have reached the operator 48 times a day. Silence is the "nothing happened" signal. The rule has one hard exception: a FAILURE always prints, because silence has to mean "healthy", never "did not run".

- **[2026-09-11] A cron script must set `PYTHONPATH` and the `SECOND_BRAIN_*` paths itself, not inherit them.** Hermes writes them into its own `.env`, but that only reaches a job after a gateway restart. The failure is silent: `ModuleNotFoundError` inside a `--no-agent` job whose stdout nobody reads when it is quiet.

- **[2026-09-11] A helper taking `namespace` and `tag` as SEPARATE arguments must compose them.** `upsert_namespaced_tag(path, "engagement", "internal")` appended the bare value, and because a bare tag never matched the `namespace/` strip the function does first, every run appended one more copy — 1,897 real Threads carried `["internal", "internal", "internal"]`, and the caller's own idempotency check looked for a tag that was never written. A split signature makes the bare form the natural call; if a helper wants the qualified form it should not take the namespace separately.

- **[2026-09-11] An invariant that holds on only one of two write paths is not an invariant.** Hub creation gated on `Ignore: Yes` alone, documented as safe because the Settings UI sets `Deleted` alongside it. A hand edit does not — and hand-editing is the documented way to curate `Entities.md` — so creation rebuilt the folder of a deleted entity every 30 minutes and the nightly reconcile deleted it again, forever.

- **[2026-09-11] Never nest a full-vault walk inside a per-entity loop.** Every entity asks the same question of the same files: build the index once, then walk once. `retag_people_by_domain` did 195 hubs x 12,722 notes = 2.4M reads and did not finish in 25 minutes; inverted, the whole five-step pass takes 39 seconds.

- **[2026-09-11] Hermes runs a `hermes cron --script` file AS PYTHON. Only `.sh`/`.bash` are handed to a shell -- a `.cmd` or `.bat` is read as Python and dies on its first `REM`.** Reason: two scheduled jobs failed on every single run while looking healthy in `hermes cron list`; a `--no-agent` failure is only a line in `hermes cron runs`, so a job can appear scheduled while doing nothing for hours. Write cron entry points as `.py`. And VERIFY THEM THROUGH `hermes cron run` + `hermes cron tick`, never by executing the file yourself -- running a `.cmd` in a shell proves the batch file works, not that the scheduler can run it.

- **[2026-09-11] Two capture processes must never write the same Person notes concurrently.** A backward-walking backfill and a forward-walking delta never fight over a Thread, but they do read-modify-write the same People, which is how meeting capture lost ~60 events. Prefer a job that DETECTS the other and exits quietly over pausing a cron by hand: a paused cron depends on someone remembering to resume it.

- **[2026-09-11] A cron agent resolves `--skill` from the SHARED skills hub (`<hermes>/skills/`), NOT from the profile a Skill is deployed to.** Attaching a Skill that lives only in a profile is skipped with a notice inside the prompt -- the job still "succeeds" having done nothing. Do not fix this by copying SKILL.md into the hub: that is a second copy to keep in sync, the same drift that once left 228 stale script copies across 41 profiles. Have the job's `--script` READ the deployed SKILL.md and print it, so the instructions injected into the prompt are by construction the ones deployed.

- **[2026-09-11] `hermes cron create` takes the prompt as a POSITIONAL immediately after the schedule.** Placing it after the options makes argparse reject the whole command with "unrecognized arguments".

- **[2026-09-11] Bound an agent batch by CONTEXT, not by cost.** When the operator says money is not the constraint, the limit that still matters is how much one agent session can read: a Thread transcript averages ~5,000 tokens, so a batch of 20 is ~100k tokens of reading before the agent writes anything.

- **[2026-09-11] Attachment paths routinely pass Windows' 260-character MAX_PATH, so every attachment write AND scan goes through `vault_manager.long_path`.** A Thread folder name, the file slug and the original filename together exceed it often: capture created the folder (just under the limit) and then failed writing the file inside it, losing 256 attachments as empty folders with no error anywhere. The read side fails worse -- a plain `is_file`/`iterdir` past the limit returns nothing rather than raising, so an attachment that exists is reported as missing. A regression fixture must genuinely exceed 260 characters, or it passes against the bug.

- **[2026-09-11] Capture meets the same message again -- an overlapping backfill page, a resumed run, the delta catching up -- and calls attachment capture every time.** Ingest returns the existing message path, so "has a message path" is not a gate. Anything capture writes that a later stage enriches must therefore be written only if absent: an attachment note carries File Enrichment's Summary and the operator's Personal Notes, and rewriting it blanked both.

- **[2026-09-11] The uv-managed Hermes runtime refuses package installs ("externally managed"). Dependencies for Skill scripts go in a dedicated venv, and the job that needs them names that interpreter explicitly.** Forcing packages into the managed interpreter would be undone or conflict on the next Hermes update.

- **[2026-09-11] A deployed Skill is FLAT: Hermes copies `scripts/` contents to the Skill root.** Instructions written against the repo layout (`<skill>/scripts/<name>.py`) name a path that does not exist on the machine running the job. A scheduled job's launcher should print the exact interpreter and script paths into the prompt.

- **[2026-09-11] A script run outside Hermes does not have Hermes' `.env`.** Delegated Graph auth needs `GRAPH_TENANT_ID` and `GRAPH_CLIENT_ID`; a launcher that merely inherits them works only while the gateway happened to load that file. Launchers load the keys they need from `.env` themselves.

- **[2026-09-11] The Agents Map shows only delta pipelines -- what happens to NEW data.** A one-time backfill or migration displayed beside them, with a stale last run and no schedule, reads as a broken pipeline. Build pipelines are recorded as reference only under `src/CBO Agents Build/`; their scripts stay in their Skills, since several are also live.

- **[2026-09-11] Hub creation looks for the entity ANYWHERE in the vault before creating it, never only at the path Entities.md implies.** When an entity's parent or section changes, the 30-minute creator runs before the nightly move: checking only the new path created a second copy, and the move then refused to merge onto it, so the duplicate became permanent. The creator leaves an entity that exists elsewhere where it is and reports it as waiting to move.

- **[2026-09-11] A Pipeline's `cron_job_id` is the Hermes job ID, and `hermes cron create` writes the SHARED cron store, not a profile's.** The manager matched `job.name` against it and searched the named profile, so it resolved nothing and the Agents Map showed every pipeline unscheduled -- which made live delta pipelines read as abandoned one-off runs.

- **[2026-09-11] An attachment's name on DISK is sanitized separately from its folder slug; the note's `original_filename` keeps the real name.** Many attachments are attached emails named after their subject, carrying `:` and `|`. And a slug must be trimmed AFTER truncation: the plain Windows API silently drops a trailing space or dot from a path component, the long-path form keeps it, so the two disagree about which folder is meant.

- **[2026-09-11] Every capture process that writes People must exclude every other one** -- backfill, email delta and meeting capture alike. Deferring only to the backfill left the email delta at :04 and the meeting delta at :44 free to overlap on a long catch-up.

- **[2026-09-11] On Windows a rename or delete FAILS while any other process holds the file open (WinError 32), and capture holds Person notes constantly.** A bulk pass that moves or deletes notes must skip a busy file and retry it next run -- never let one exception end the run. A check for "is a capture running" at start is not enough: a capture can begin mid-run. The first People run filed 1,521 people and then died on one busy file.

- **[2026-09-11] Every lookup of a Person must search flat Work/People AND both hub roots at any depth (`Customers/**/People`, `Partners/**/People`).** People are filed under Partners and under Affiliates one level deeper. Capture's lookups already did; enrichment's and the backend's did not, and would have lost every filed partner contact.

- **[2026-09-11] When one applier replaces another, carry over EVERY rule the old one enforced -- list them before deleting it.** The extraction applier replaced `apply_thread_review` and silently dropped its company tagging, the operator's own "tag all companies" rule: named companies fed only the review list, and 149 of 179 enriched Threads went untagged by content. Persisting each extraction before applying it is what made the repair cheap -- a backfill from disk, no model.

- **[2026-09-11] Enrichment reads and saves; Tagging tags; Metadata is structure.** Three pipelines, split by the operator's own test -- "does it need a model to decide?" -- and then by what they write. Company tags from ANY source (domains, a Thread's saved extraction, an attachment summary's links) and the engagement label derived from them all belong to Tagging, which runs after Metadata so every tag points at where each company finally sits, and computes engagement last so it sees every source. Putting a tag write inside an enrichment applier is the mistake this rule exists to stop.

- **[2026-09-11] The operator's enrichment design fans ONE read out to four places: the Thread, People, Customer Logs (each named company's History) and Important Captures.** Check a new applier against all four. The extraction applier shipped writing one and a half of them; company History and tagging were both silently dropped from the applier it replaced.

- **[2026-09-11] A pipeline that reads with a model writes only the note it read; everything else that read feeds is filed from the SAVED read by the pipeline that owns that note.** Enrichment writes the Thread's Summary and Actions and saves the extraction; Tagging files company tags from it, Company files each company's History and Captures and each person's details. Two writers on one note is how they overwrite each other, and a filer working from saved reads is re-derivable: idempotent, healed on the next run, and a company or alias added later picks up everything already read about it.

- **[2026-09-11] A value copied from Entities.md at creation is not kept in sync by anything unless something syncs it.** Hubs took Domain and Aliases once, at creation; every later curation edit (the aliases added for EY, TAQA, Core42) stayed in Entities.md while People and Tagging read the hub notes -- so nobody at those domains was ever filed, silently. Hub upkeep now copies them, adding only.

- **[2026-09-11] Before changing what a company matches on, check what the change will tag.** Correcting Core42's misspelled domain would have stamped the operator's own company on 2,046 of 2,627 Threads and relabelled 964 colleague-only Threads from internal to partner, because the engagement rule counts any partner not in the internal set. Count the notes a matching change reaches, and settle internal/own-company status first.

- **[2026-09-11] Parallel jobs over one queue need a stable partition and a lock on every file they all update.** Each job asks the same oldest-first question, so without a partition all of them read the same items; partition by CRC32 of the item id, never Python's `hash()`, which is salted per process. A shared read-modify-write file loses one job's update to the other's rename unless it is locked.

- **[2026-09-11] Never let an agent type a file path; hand it an id and resolve the path in code.** Given each Thread's folder, the enrichment agent rebuilt paths from Thread titles and got them wrong -- a `|` Windows never allows, a name cut at 80 characters, a zero-width space Hermes strips from every prompt -- so those Threads failed on every run, at the head of every oldest-first batch. An id is plain ASCII and survives the prompt; scripts take `--thread-id` and find the note with `find_by_id`.

- **[2026-09-11] A recurring job must save its progress as it goes, never only at the end.** Hermes kills a script at 3600s. The email delta paged backward from "now" and saved its watermark once, after the last page: a backlog bigger than one run was killed every hour with nothing saved, and each next run started from the newest mail again -- it could never catch up. Walk oldest first and persist after each unit of work, so a run that is cut off is progress, not a loss; and stop cleanly inside the limit so the report says "more to do" rather than "failed".

- **[2026-09-11] Every step of a Pipeline except its first must name a `depends_on`.** The Agents Map draws a pipeline as its steps, connected only by those edges: three steps with empty `depends_on` rendered as three unrelated agents, not one pipeline. Draw the order the steps actually run in; never invent a step only to connect the others -- an extra node reads as a new worker that does not exist.

- **[2026-09-11] Test a frontmatter VALUE, never the presence of its key.** Every Thread carries `last_summarized_at: ""` from its template, so counting notes that contain the key reported 2,569 of 2,605 Threads enriched when 179 were -- nearly a wrong answer to the operator about how complete History was.

## Capture pipelines

- **[2026-09-10] Strip HTML at READ, never at capture -- 83% of a stored Outlook body is markup.** Measured on 119 real Threads: 6.66 M raw chars reduce to 1.14 M of text, i.e. ~14,000 input tokens per Thread become ~2,400 for identical content. An agent reading captured message notes raw pays for every `<div style="font-family:Aptos,...">` and learns nothing from it. But convert on the way OUT, not on the way in: an email's real body IS the HTML, capture's job is to preserve the evidence faithfully, and if a summary ever looks wrong the original is what you check it against. `summarize-and-tag-threads/scripts/read_thread.py` is the converter.

- **[2026-09-09] A refresh token is single-use: Entra rotates it on every redemption and invalidates the one just redeemed.** Persist the replacement in the same step that redeems it, or the pipeline works EXACTLY ONCE and every later run fails with `invalid_grant` -- a failure shape that looks like a revoked grant and sends you to the admin instead of to the code. Equally: a delegated sign-in that returns no `refresh_token` means `offline_access` was not consented, so unattended running is impossible; fail loudly at authorize time rather than at the first unattended run. Both are pinned by tests in `catalog/*/email-thread-capture/scripts/tests/test_graph_auth.py`.

- **[2026-09-09] A credential must never be written under the repo tree, and the path it lands in is not always the path you configured.** Sourcing a Windows `.env` from bash (`. .env`) silently eats the backslashes, so `C:\The-Vault\config` became the RELATIVE directory `C:The-Vaultconfig` and a Graph refresh token was written inside `src/`. It was caught only by looking at the printed path. Echo the resolved absolute path before writing any credential, and check `git status` afterwards -- an untracked secret in the working tree is one `git add -A` from being published.

- **[2026-09-07] The email capture pipeline is READ-ONLY, and stays read-only even when the token would permit more.** A tenant may consent an app to a broader set than was asked for -- one live grant came back with `Mail.ReadWrite`, `Mail.Send`, `Files.Read.All` and `Sites.Read.All` attached to a request for `Mail.Read`/`Mail.Read.Shared` alone. The scopes on the token are not a licence to use them: capture reads mail and writes only to the vault, never back to the mailbox. Concretely, no `sendMail`, no flag/move/delete, no draft creation -- every Graph call stays a GET. Verified 2026-09-07: the Skill's only Graph URLs are `/users/<mailbox>/mailFolders/<folder>/messages` and `/users/<mailbox>/messages/`, and its only POST is the token request. Keep it that way; an agent that can send mail as the operator is a different risk class from one that files notes, and nothing in this product needs it.

- **A capture watermark may never advance past an item that failed to write.** Advancing past a failure converts a transient error into permanent data loss, because the next run treats those items as already captured. Re-ingesting an already-written email is idempotent; skipping one is not recoverable. Never write `if code == 0:` with no `else` around a subprocess whose failure means data was dropped.

- **A dedup-by-id scan only sees duplicates in the shape it knows.** Changing a note's directory shape makes every note captured under the old shape invisible to the new scan, so the next pass creates a second copy instead of topping up the first. Plan a migration pass alongside any shape change.

- **A rename or repair function that is correct in isolated calls is not thereby safe inside an always-on capture pipeline.** Verify against a real, repeated live run before wiring it in - a single hand-picked case will not surface repeat-invocation behaviour.

- **A driver that calls `ingest_email.py` directly does not get `rename_thread.py` or `link_person_to_thread.py`.** Those run only inside `run_full_capture.py`/`run_delta_capture.py`'s per-email loop, so a direct-ingest retrofit leaves its threads unrenamed and unlinked.

- **A skip rule that matters must be mechanical.** `summarize-and-tag-files`' documented `## Summary`-non-empty skip has no code-level enforcement and relies on the cron agent's per-file judgement, which re-processed already-summarised files in practice.

- **A mechanical already-done guard belongs inside the mutating script, not in the calling agent's prompted judgement.** Its freshness check must match what that note kind actually stores - a check borrowed from a sibling note kind silently never fires.

- **Every script that prints JSON must call `sys.stdout.reconfigure(encoding="utf-8")` first.** Without it a single emoji in a subject raises `UnicodeEncodeError` on the final print, after the real work has already succeeded - a completed write that looks like a failure to its caller.

- **A locked safety-critical rule must be enforced structurally in the calling script, never by trusting a relayed model's prompted compliance.** That holds even when the target profile's SOUL.md documents the rule as a secondary safety net. Make the unsafe path structurally unreachable.

- **`email-capture-classifier`'s SOUL.md documents `direction` as `"inbound"`/`"sent"`; the real field carries `"received"`/`"sent"`.** Any branch on the received value must use the real one, not the profile's stale wording.

- **Validate the shape of any Outlook COM field that can fall back to an internal identifier, never just its truthiness.** A failed GAL lookup returns a LegacyExchangeDN, which is truthy and is not an email address. Check the shape before using such a value as a dedup key, filename or displayed field.

- **A note's customer signal is not reliably in one place.** Meeting notes always carry a `customer:` frontmatter field, while Thread and RawMessage notes can carry only a `customer/<slug>` tag. Any customer resolution must check both.

- **`run_full_capture.py` has never written the watermark file; only `run_delta_capture.py` reads or writes it.** This is correct, pre-existing behaviour - do not add a watermark write to the full-history orchestrator on the assumption that it is missing.

- **`job4`, `job5` and `email-delta-capture` can each run about 40 minutes against a 20-minute interval, so at least one vault-writing job is running almost continuously.** Never gate work on waiting for a simultaneous idle window across them; it may never appear.

- **`## Actions` and `## Personal Notes` are human-owned (`section_ownership.py::_HUMAN_OWNED_HEADERS`) - no pipeline or agent writes them automatically.** An agent may read them; writing into them reopens the undecided approval question.

## Hermes runtime and provisioning

- **Hermes gives every profile its own home, and env files do not chain.** `env_loader.load_hermes_dotenv` loads exactly `<that home>/.env` with no fallback to the top-level file, so a value must exist in all 41 places to be visible everywhere. That is also why `profile create --clone` copies `.env`.

- **Backup carries no `.env` and restore never recreates one.** `hermes_backup.py::_is_excluded` skips any `.env` file anywhere as a secret, so a restored install has every profile, Skill and cron job but zero environment variables - nothing resolves until the setup wizard is re-run.

- **Second Brain's `COMPASS_BASE_URL` is the full chat-completions URL; Hermes' own Compass `base_url` must NOT end in `/chat/completions`.** The two conventions are opposites and both are correct for their own consumer: this app POSTs to the value verbatim, Hermes appends the suffix itself.

- **The app Registry cannot bootstrap Hermes - Hermes' profiles are the driver, the Registry only decorates them.** `list_agent_summaries` iterates the real profiles and enriches each from the Registry, so a Registry entry whose profile is missing is invisible on the Agents Map entirely.

- **`hermes cron create` takes a bare duration (`"20m"`) as a ONE-TIME job regardless of `--repeat`; only the `"every "` prefix creates a recurring one.** The CLI's success output looks near-identical either way - read the `Schedule:` line, or the created job's JSON, before trusting it.

- **A cron job's `--skill` resolves only against the running profile's enabled skill catalog, not the specialized profile the script lives under.** Jobs live in one central `cron/jobs.json` with no per-job profile field and fire from whichever gateway is running, so the Skill must be deployed to that profile too.

- **The vault path for `job4-summarize-tag-threads` and `email-delta-capture` is embedded in the cron job's own prompt text, not a separate `--vault-path` field.** A vault cutover for these two is a code deployment swap, not a job-definition edit.

- **`hermes -p <profile> chat -q` has no back-channel.** If the target agent calls `clarify`, the call blocks and times out rather than reaching a human. Resolve all Q&A on the calling agent's own live channel first, then relay one consolidated call marking unanswered fields explicitly.

- **A relayed specialist's reply must never expose the relay mechanism - no command text, no profile name, no "let me check with the specialist".** The calling agent translates the raw reply into one natural confirmation or error, as if it had done the work itself.

- **Hermes' `lazy_deps.py` auto-installs only its own curated allowlist for built-in features; it does not generalize.** A custom Skill needing a third-party package declares it as a `## Prerequisites` step in its `SKILL.md` instructing an explicit `pip install`.

- **Raw tool-call text reaching WhatsApp is a gateway display setting, not a disobedient model.** Check `display.tool_progress` and its per-platform override before touching SOUL.md - a global `all` left over from CLI use applies to every platform unless overridden.

- **Hermes' built-in remember mechanism decides for itself whether a fact lands in `memories/MEMORY.md` or `memories/USER.md`.** The calling agent cannot control the filename, and its own report of where it wrote is not evidence - read both files to confirm.

- **`Agent.depends_on` has no Hermes backing, same-install or cross-install.** `hermes peer` reaches a different gateway over the network; it is not a local dependency mechanism. Treat `depends_on` as Second Brain metadata only.

- **Primary must never open, process, or transmit a captured file itself, even after a successful capture.** Deeper analysis is offered only as a relay to the specialist that owns the domain, which appends its findings into the vault. Output that reaches the operator without landing in the vault is lost work.

- **When a new specialist takes over a domain, audit Primary's entire skill list for any pre-existing skill that could also claim that domain - bundled skills included, not only the custom ones the specialist was built around.** A general-purpose bundled skill with a strong trigger match will intercept the input before the specialist ever sees it.

- **A Skill must NOT bundle a shared library it sibling-imports; put one copy in `<hermes_home>/managers/` and on `PYTHONPATH`.** `sys.path[0]` is the script's own directory, so a bundled copy silently WINS over the shared one - bundling does not merely duplicate, it makes staleness invisible. Hermes APPENDS a configured `PYTHONPATH` to its own and the gateway mutates `os.environ` globally, so cron scripts and agent-invoked Skills both inherit it. Two consequences: `.env` is read at gateway start, so a change needs `hermes gateway restart`; and the configured entry lands LAST, so never name a shared manager after a Hermes module.

- **Never infer a cron job's behaviour from running its script by hand - measure it inside the scheduler.** They are different execution paths. A `--no-agent --script` job DOES inherit Hermes' environment including `.env` values; a manual shell does not. A disposable `--no-agent --script` job that dumps what it actually sees, removed afterwards, settles such a question in one run.

- **Changing a shared library's contract means redeploying every consumer, and they may not share a deploy path.** The shared `vault_manager` and the index engine install through different functions (`deploy_shared_managers` vs `deploy_index_builder`). Refreshing only one left the other compensating for the old behaviour and every index cron job failing. List a contract's consumers and confirm each one's deploy path runs.

- **Ask `SkillManager.check_deployment_drift()` after any deploy, and before trusting the catalog.** It reports `missing`/`stale`/`modified`/`current` per deployment; `modified` is the sharp one - same version, different content, so the version claims current and is not. Match a deployed Skill on its SLUG, never `<category>/<slug>`: Hermes keys it by the folder it landed in. Bump a Skill's `version` whenever its `SKILL.md` contract changes, or the check reports `modified` instead of the honest `stale`.

- **`deployed_to` and an Agent's `skill_ids` record INTENT; Hermes holds reality. Never treat either as a survey of what is installed.** `deployed_to` was found recording 85 deployments against 348 real ones, so everything keyed off it was blind to most of the install. `reconcile_deployed_to()` re-derives it from disk. An Agent's `declared_skill_ids` (Registry) and `skill_ids` (live mirror) are likewise different questions.

- **[2026-09-07] Hermes' launcher is `<hermes_home>/bin/hermes.exe`; `hermes-agent/` beside it is the cloned SOURCE tree and has no `bin/` at all.** Reason: `HermesCLI._hermes_exe` built `<home>/hermes-agent/bin/hermes.exe`, which exists on no install, so every CLI call returned "No real Hermes install found at the configured home path" on a perfectly healthy Hermes — and that message names the *install* rather than the wrong constant, so it reads as a provisioning fault and sends you to the wrong layer. Fixed in `5f0f40e` (BUG-043). Only `hermes_home_path` is configuration; any subpath below it is our own assumption about the installer's layout, so resolve with a `shutil.which("hermes")` fallback rather than trusting one hardcoded shape.

## Backend architecture

- **`app/api/*.py` holds zero business logic.** A handler parses the request, calls ONE `business/` function, and maps the result or exception to a status. Mapping `None` to a 404 is the API layer's job; branching, computation and cross-manager composition belong in `business/logic/`.

- **All raw I/O happens in `data_access/`.** A Manager understands entities and calls into `data_access/` to get or persist them; it never opens, reads or writes a file itself. A missing `data_access/` function is a gap to build there, never a reason for the Manager to do the I/O.

- **A business-layer CRUD store that owns a file the Registry also mirrors must dual-write.** Its own store file stays the source of truth; the Registry copy is synced additively on every mutation via `registry_loader.agent_data_dir()`. Never let a store read the Registry copy as its primary - RegistryLoader hot-reloads that mirror, so the store would be reading its own stale echo.

- **A module absent from the live router's import list is not dead.** A lazy or deferred import elsewhere can keep it genuinely live - grep the whole `app/` tree for real call sites before deleting or archiving any module.

- **In a Pipeline Step tree, `type: "producer"` belongs on the terminal step that writes to the vault, never on the entry step that fetches external data.** Fetching produces nothing until the write happens. Every other step is `worker`.

- **One agent has exactly one `Agent.json`.** The Registry's directory scan lets a stray duplicate elsewhere silently shadow the correct one in memory, which presents as agents disappearing from a Section. Any write path must resolve the agent's real directory before writing.

- **`registry_loader.agent_data_dir()` returns `None` until `registry_loader.boot()` has run in-process.** An Agent exported from a raw script therefore loses its `Agent.json` and `soul.md` silently. Export through the running server, or boot the Registry first.

- **`chat_store.get_thread` is no longer side-effect-free.** The first read for any subject computes and persists `recommended_agent_ids`, including the empty case, so any caller must expect a write on first read.

- **A missing or invalid `.env` must never crash the backend.** The five required settings carry safe defaults so import succeeds, and the app boots into setup mode serving the first-run wizard. A config error the UI cannot reach is a config error nobody can fix.

- **The first-run wizard is read-only on the Hermes side.** It reports install, gateway, profile count and Skill deployment, and provisions nothing. Applying config to a real Hermes install stays the operator's own action.

- **Never write a bare `KEY=` into `.env` for a Path setting.** pydantic parses an empty string into `Path(".")`, not `None` - so an empty `SECOND_BRAIN_DATA_PATH` relocates the whole state folder to the backend's working directory AND suppresses the validator that would have defaulted it. Remove the line instead of blanking it.

- **The Artifacts placeholder mechanism cannot catch a hardcoded RELATIVE path.** It substitutes absolute paths only, so a literal like `.second-brain` in a script's source passes through untouched and importing a pre-fix bundle silently overwrites a corrected script. Screen incoming bundles at preview time - the last point the import can still be skipped.

- **When substituting a placeholder that must handle both raw and JSON-escaped forms, test both forms against the original text.** A first `.replace()` consumes every occurrence, so the second form never matches and `.json` files are silently left with raw values.

- **A secret-scan finding keyed as `<file>:<line>` stays unique only if the scanner takes at most one match per line, first-match-wins.** Two patterns can match the same substring, and reporting both breaks the keying that `apply_decisions` relies on.

- **Treat `artifact_dependency_resolver.resolve_closure`'s output as a superset needing review, never as a precise dependency list.** Every Skill ships a copy of `vault_manager.py`, which names every Template id, so almost any Skill's closure resolves to all Templates.

- **An unhandled exception's response carries no `CORSMiddleware` headers.** The same request that returns a readable status to `curl` is opaque-CORS-blocked in the browser, so a browser `TypeError: Failed to fetch` means look for a raw exception in the route, not a CORS misconfiguration.

- **[2026-09-06] An Index ships its own build engine from `src/backend/app/business/core/index/scripts/`, and Index is the fifth artifact kind.** Reason: `_INDEX_BUILDER_SOURCE_DIR` used to resolve into `Hermes-Provisioning/skills/vault-rebuild/vault-index/scripts/` — an Index reaching into a *Skill's* private scripts folder for its own engine. That folder is normally held outside the checkout, so `deploy_index_builder()` raised `FileNotFoundError` and Index creation was simply broken on any install without it. That folder is now backend-owned **payload**: code the backend ships to a Hermes cron worker and never imports itself (the naming test — does the backend ever `import` this? no → it is payload). Making the engine backend-owned is also what finally let Index join `skill`/`template`/`agent`/`pipeline` in the export/import machinery; before it, a `.sbf` bundle would have carried an Index definition whose implementation lived somewhere else entirely. `import_index` deliberately drops any incoming `cron_job_id`/`cron_profile_id` — opaque ids minted by the exporting machine's Hermes — so an imported Index arrives real and rebuildable but **unscheduled**, never silently running a job the operator never asked for.

## Frontend

- **`is_background_agent: true` is a hard visibility gate on the Agents Map, not a styling hint.** `layoutAgents.ts` excludes such agents from the ring entirely and their detail panel becomes unreachable. Never set it true for an agent that has no access point outside the map.

- **Never render a stored `*.icon` field directly as a Material Symbols ligature.** The stored value can be a VisualPicker id rather than a ligature name; always resolve through `getVisualIconName()`, which handles both conventions.

- **A solo agent - no `depends_on`, nothing depending on it - must be identified globally across all agents, not per Section.** `layoutAgents.ts` keys its depth-to-radius formula off the whole Section's `maxDepth`, so one pipeline in a Section pushes every solo agent there out to `AGENT_RADIUS_MAX`.

- **A frontend API function that needs the raw `Response` must bypass `api/client.ts::apiFetch`, which always resolves via `response.json()`.** The bypassing function re-implements the same non-2xx to `ApiError(status, text)` mapping so callers still see one error shape.

- **A blob download can report `receivedBytes` reaching `totalBytes` and then land in a terminal `canceled` state with no file on disk.** Under headless CDP download interception this is an environment quirk - confirm against an already-working sibling flow before treating it as a defect in new code.

## Windows host and environment

- **On this Windows host every `Path.exists()`/`is_file()`/`is_dir()` silently returns `False` once the full path exceeds about 260 characters.** Two of them on the same long path can therefore contradict the branch logic that decided its type. `iterdir()` still lists such files - never gate on a path predicate alone for deep vault paths.

- **`subprocess.run([name], shell=False)` on Windows resolves a bare command name via `CreateProcess`, which appends only `.exe` - never the rest of `PATHEXT`.** A `.cmd` or `.bat` on PATH will be found by `where.exe` and silently skipped by Python. Name the extension explicitly.

- **The backend serves port 8001, and a mismatch shows up as a completely empty UI with no console-visible cause.** Read the network tab's target port rather than assuming the backend is down. Before treating a bind failure as a reserved port, check which process already holds it.

- **A machine-specific literal in a Hermes cron-wrapper script must be read from an environment variable with the current value as fallback, never left as a bare constant.** A copied runner would otherwise run silently against the original machine's vault.

- **A command that succeeds in the agent's shell but fails in the operator's, on the same machine, is a network-path difference, not a flaky command.** Never build a theory on a result the operator's own shell has not reproduced.

## Working discipline

- **[2026-09-10] Do not leave backup copies behind. Deleting is the default; ASK before keeping a backup.** Operator rule, with a concrete reason: stray copies "generate lots of errors later". A `.bak` or a dated copy dropped next to the file it copies sits in a folder something SCANS -- `Settings/Entities.md` is read by the company pipeline, a Template folder is read by the seeder, a Skill's `scripts/` is deployed wholesale -- so the copy eventually gets parsed as real data, or deployed, or picked up by a glob. The safety a backup buys is already provided properly by git for anything in the repo, and by re-running the generator for anything derived. When a backup genuinely is warranted, ask first and put it OUTSIDE any tree the app reads.

- **Before adding a delete action over data that a separate discovery or dedup process also reads, check what that process's "already seen" check keys on.** Removing the record it looks for silently un-suppresses whatever the record was suppressing - soft-delete with a flag instead.

- **The Entities file format has two independent implementations of `parse_entities`/`render_entities`/`_KNOWN_FIELDS`, in `find_new_entities.py` and `create_companies_partners.py`.** A schema change needs both edited and both redeployed.

- **Tokenized word-overlap matching against profile names and descriptions needs a stopword filter, including this domain's own boilerplate.** Without it a single coincidental shared word produces a confident false match.

- **Never gate a deploy or commit on `pytest ... | tail -1`.** A pipeline reports the LAST command's exit status, so the gate is `tail`, which always succeeds: on 2026-09-11 a chain built that way deployed and committed with two failing tests, under a message claiming the fix worked. Use `set -o pipefail`, or pytest's own exit code.

