# Building a new Second Brain — the ordered checklist

For standing up a Second Brain for a **new person** on a **new machine**. Each
step names the page that explains it; this file is the order, not the detail.

Full deployment mechanics → **[`Deployment.md`](../../../Deployment.md)** at the
repo root.

---

## Before you touch the machine

- [ ] **Decide what this person actually captures.** Email, meetings, files,
      voice notes — each is a Template, not code. Do not start until you can name
      the note kinds.
- [ ] **Decide the identity key for each note kind.** The source's own stable id
      (conversation id, event id) keyed as the note's `id`. This is the single
      decision that makes re-runs idempotent instead of duplicating.
      → [Templates.md](../Templates.md)
- [ ] **Decide which sections are theirs.** `human_only` is enforced by the
      engine; an undeclared section defaults to open.

## Hermes first — it is the driver

- [ ] Install Hermes and confirm the version. The API surface differs between
      versions; do not build against documentation you have not verified.
- [ ] **Configure the `default` profile completely — model, provider, credentials
      — before cloning anything.** Every specialist inherits from it, so a
      default fixed late means fixing every profile by hand.
- [ ] Set `HERMES_DASHBOARD_SESSION_TOKEN` in Hermes' root `.env`.
- [ ] Verify `hermes serve` answers on `127.0.0.1:9119`.
      → [Hermes-Runtime.md](../Hermes-Runtime.md)

## The app

- [ ] Copy `src/backend/.env.example` to `.env` and fill it in. Set
      `HERMES_API_KEY` to the same value as the Hermes-side token.
- [ ] Set `SECOND_BRAIN_DATA_PATH` explicitly. **Never leave a Path key blank** —
      an empty value relocates the whole state folder to the working directory.
- [ ] `COMPASS_BASE_URL` here is the **full** chat-completions URL. Hermes' own
      Compass `base_url` must **not** end in `/chat/completions`. The two
      conventions are opposites and both are correct.
- [ ] Start it. A missing config boots the setup wizard rather than crashing — if
      it crashes instead, that is a bug.

## The vault

- [ ] Point at an empty or existing Obsidian vault. Keep the root path **short** —
      past ~260 characters Windows silently reports real files as missing.
- [ ] Drop each `Template.json` into `<SECOND_BRAIN_DATA_PATH>/data/Templates/<id>/`.
      Nothing registers a Template; the file being there is enough.
      → [Vault-Layout.md](../Vault-Layout.md)
- [ ] **Test every Template against a scratch vault first.** Second call on the
      same id must update, not duplicate; a `human_only` write must raise.

## Agents

- [ ] Create one Hermes profile per specialist, by cloning the configured default.
- [ ] `hermes profile describe <profile> --text "…"` on every one — an
      undescribed profile is invisible to routing.
- [ ] Pair each platform per profile. Cloning does not carry a WhatsApp pairing.
- [ ] Strip relay-only profiles structurally: delete `skills/` entirely.
- [ ] Create Sections in the app and place the agents. A clean install starts with
      **no Sections, no Templates and no Pipelines** — nothing is invented for you.

## Schedules

- [ ] One Pipeline per recurring job, plus the Hermes cron job that runs it.
- [ ] **`"every 20m"`, never `"20m"`** — the bare form creates a one-time job and
      the success message looks almost identical.
- [ ] Deploy each job's Skill to the profile whose gateway actually runs, not only
      to the specialist the script belongs to.

## Memory

- [ ] Copy [`AGENT-MEMORY.template.md`](AGENT-MEMORY.template.md) to
      `<SECOND_BRAIN_DATA_PATH>/AGENT-MEMORY.md` and leave it empty.
- [ ] Confirm this install's discoveries land there, not in the repo's
      `MEMORY.md`. Mixing the two is what makes one person's agent reason about
      another person's setup.

## Before you call it done

- [ ] Run one real capture end to end and **read the file on disk** — never infer
      success from a return value.
- [ ] Restart the backend and check Browse & Search still shows content. The index
      has no disk persistence and nothing rebuilds it automatically.
- [ ] Take a `.sbb` backup **with `Hermes-Provisioning/` present**. Without it the
      backup completes, reports success, and contains zero Skills.
- [ ] Confirm a restore is understood to recreate **no** `.env` anywhere.
