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

- **A long-path walk must hand back PLAIN paths - rebuild each result against the original root, never strip the `\?\` prefix by hand.** `os.walk(long_path(root))` yields prefixed paths; returning those breaks callers silently, because `relative_to(vault_path)` raises `ValueError` and every returned path compares unequal to the plain one the caller holds. Use `root / os.path.relpath(found, walk_root)`. Plain paths are safe to return only where the module's own I/O re-applies `long_path` (`read_note`/`write_note` do). Never re-guard the results with `is_file()`: past MAX_PATH it silently returns `False` and drops exactly the notes the long-path walk exists to reach.

- **Resolve a schema/format version ONCE and explicitly, never per-field with `.get(key, default)` fallbacks.** `.get()` with a default cannot tell "absent" from "named differently in this version" - it returns the default for both, silently. Reading v1 field names out of v2 Template files made all 11 parse to zero sections with `error=None`, for weeks, invisibly. When a format gains a second version, the FIRST change is a version field in the file.

## Capture pipelines

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

- **Before adding a delete action over data that a separate discovery or dedup process also reads, check what that process's "already seen" check keys on.** Removing the record it looks for silently un-suppresses whatever the record was suppressing - soft-delete with a flag instead.

- **The Entities file format has two independent implementations of `parse_entities`/`render_entities`/`_KNOWN_FIELDS`, in `find_new_entities.py` and `create_companies_partners.py`.** A schema change needs both edited and both redeployed.

- **Tokenized word-overlap matching against profile names and descriptions needs a stopword filter, including this domain's own boilerplate.** Without it a single coincidental shared word produces a confident false match.
