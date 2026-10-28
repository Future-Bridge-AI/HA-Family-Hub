# Phase 2: Dev + Family Preview - Context

**Gathered:** 2026-10-27
**Status:** Ready for planning

<domain>
## Phase Boundary

One-command Dev and a separate Family Preview Home Assistant instance, both running the fork's
integration on HA 2026.10.4 (`versions.env`), with seeded family data, `deploy-preview <branch>`,
`reset-preview`, a visible build stamp, an auto-created Family Hub dashboard, and her one-tap,
non-admin access from her Android phone, plus a plain-language Getting started guide in
`docs/family/`. Requirements: DEV-01..03, PREV-01..08, ACCESS-01..05.

**Scope changes agreed in this discussion (the planner must reflect them; see D-03, D-07):**
- Preview runs on the developer's laptop for now, so "always-on" becomes "available whenever the
  laptop is on at home".
- Dev and Preview **connect read/write to a chosen list of the family's real Google calendars**. This
  overrides the earlier rule "Preview never connects to the real family calendars" (PREV-03's
  calendar clause, the PROJECT.md/REQUIREMENTS.md out-of-scope row "Real family calendars or data
  in Preview", and ROADMAP Phase 2 success criterion 2's "or touches the real family calendars").
  The notification/speaker isolation half of PREV-03 is unchanged.

</domain>

<decisions>
## Implementation Decisions

### Preview host and address
- **D-01:** Preview runs on the **developer's Dev laptop** (local, not cloud), as its own HA container, volume and port (8124), separate from Dev (8130). A cloud host was explained and declined. — **Reversibility:** reversible — tooling is host-agnostic (D-04).
- **D-02:** Cloud hosting is not used for Preview or Home. The no-cloud locality rule stands, apart from the Google Calendar API exception in D-07.
- **D-03:** "Always-on" is relaxed for Phase 2: Preview is available whenever the laptop is on and at home. Her try-outs happen at agreed times. Containers use `restart: unless-stopped` so Preview comes back by itself after a reboot or wake. Reword ROADMAP Phase 2 success criterion 1 ("at any time") and PREV-01 ("always-on") to match; always-on returns once Preview moves to a dedicated box.
- **D-04:** Portability: the tooling must work on any Linux or macOS host with Docker Engine/Compose v2, with no laptop-specific paths and all host-specific values in one gitignored env file. Moving hosts = copy repo + env file + run `reset-preview` (a fresh seed; no volume migration). The researcher checks Docker-on-laptop specifics (Docker Desktop on macOS vs Engine on Linux, sleep behaviour).
- **D-05:** Stable address = a **router DHCP IP reservation** for the laptop; Preview is reached at `https://<reserved-ip>:8124`. After a move, only the IP changes.
- **D-06:** **HTTPS from day one** for Preview (and Dev, for parity): a local CA or self-signed certificate that her Android phone trusts once. The researcher must confirm the Android HA Companion app accepts a user-installed CA. If it does not, report the fallback options before planning around it; do not silently drop to HTTP.
- **D-06a:** Home hardware is **not decided**. Record only the rule: Home never shares a volume, network identity (`core.uuid`), credentials or config with Dev or Preview. Where Home runs is decided in Phase 4.

### Family, calendars and seed data
- **D-07:** Dev and Preview use **HA's Google Calendar integration, read/write**, connected to a **chosen list** of the family's real Google calendars. The developer chose this knowing Family Hub can create and delete events. This needs Google OAuth application credentials (a Google Cloud project), the one accepted cloud exception. Update PROJECT.md (Out of Scope, Constraints, Key Decisions) and REQUIREMENTS.md (PREV-03, Out of Scope) to match. — **Reversibility:** one-way — any real event deleted or changed from Dev or Preview is gone from the family's Google calendars unless restored from the D-08 backup.
- **D-08:** Guardrail: before `deploy-preview` and `reset-preview` (and the Dev equivalents), export every connected Google calendar to a **dated local `.ics` backup** (gitignored, outside the HA volume so reset doesn't delete it). Document how to restore an event from it.
- **D-09:** Guardrail: in Dev and Preview only, deleting an event on a Google-backed calendar shows an extra loud confirmation ("This is the REAL family calendar"). It must not appear on Home. The planner picks the mechanism (e.g. an env- or setting-driven flag), keeping the change small and in the served `card/` copy (the delete flow is in `card/family-week-calendar-card.js` ~line 23682, websocket `family_hub/calendar/delete_event`).
- **D-10:** Guardrail: `reset-preview` keeps the Google sign-in, so the developer doesn't re-authorise after each reset, while everything else is still wiped (including `family_hub_backups/`). The researcher checks how HA stores the application credentials and OAuth token (`application_credentials` and the config entry in `.storage`) and whether restoring just those safely is feasible. If not, re-sign-in after reset is the fallback, documented as a step.
- **D-11:** The seed **does write tagged pretend events into Google**, prefixed `[PREVIEW]` (exact tag at the planner's discretion, but it must be unambiguous). Reset and re-seed delete **only** events carrying that tag, and never touch untagged events. The developer accepts that these show up on family phones. This is the highest-risk code in the phase: tag matching must be exact, and it needs a dry-run mode and a test.
- **D-12:** Family members use **real first names, kept out of git**: the seed reads members, roles, kids' ages, the chosen Google calendar list and similar values from a gitignored local file (e.g. `tools/seed/family.local.yaml`). The repo ships an invented example family file with the same schema, used when no local file exists.
- **D-13:** HA accounts for **every family member**: admin for the developer, non-admin for her, and non-admin accounts for each kid set up as Family Hub child accounts (so kid PIN sign-in can be tried).
- **D-14:** Seed content = core plus a little of each extra: Family Hub calendar mapping, meals for most nights, a handful of chores per kid, 3–5 rewards, the required `todo.*` lists, plus one goal, one morning routine and a few recipes. Grocy stays off. Chores, meals and other Family Hub data are date-relative (relative to today).
- **D-15:** Dev uses the **same Google calendar connection and guardrails** as Preview (D-07..D-11). Dev and Preview both writing tagged events to the same Google calendars must not clobber each other: tags or reset logic must tell Dev's seeded events from Preview's (e.g. `[PREVIEW]` vs `[DEV]`).

### Her access and what she sees
- **D-16:** She opens Preview via the **HA Companion app on Android, with Preview added as a second server** (Home can be added later as another server; never replace one with the other).
- **D-17:** PREVIEW identity = server/location name **"Family Hub PREVIEW"** plus a **distinct built-in Family Hub theme**, different from what Home will use. No banner strip.
- **D-18:** Her dashboard mirrors the **upstream documented layout**: Calendar (week card) first, then Today, Chores, Rewards, To-dos, Recipes/Pantry, using `DOCUMENTATION.md`'s card YAML. It is created automatically by the seed (storage-mode dashboard, resources verified), and she sees only this dashboard, with the admin sidebar items hidden (ACCESS-01).

### Change hand-off, build stamp, guide
- **D-19:** The developer tells her when a change is ready (in person or by text). `deploy-preview` prints a short plain-language "what changed, where to tap" note for him to pass on. No in-app notice.
- **D-20:** Build stamp = small footer text on the calendar card, e.g. `Preview · 2.0.0+a1b2c3d · 27 Oct 14:05` (environment, manifest version + short git hash, deploy time), plus a `console.info` line. `deploy-preview` verifies the served stamp/hash afterwards.
- **D-21:** The Getting started guide is **Markdown in `docs/family/`** with Preview screenshots, readable on GitHub from her phone and printable or saveable as PDF. It is not published to the docs site in this phase. It includes the Android steps: install Companion, trust the certificate, add the Preview server, sign in.
- **D-22:** The first end-to-end change (ACCESS-05) is **a tiny wording or title change she picks**, recorded in her words.

### Claude's Discretion
- Exact `[PREVIEW]`/`[DEV]` tag wording and the local family-file schema/path.
- Which distinct built-in theme Preview uses.
- Certificate tooling (mkcert-style local CA vs self-signed), as long as D-06 holds.
- Mechanism for the Dev/Preview-only delete warning (D-09).
- Layout of `dev/`, `tools/seed/`, `scripts/` (research suggests `dev/compose*.yaml`, `tools/seed/`, thin `scripts/` wrappers).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §Phase 2 — goal, success criteria (criteria 1 and 2 need rewording per D-03/D-07), research questions
- `.planning/REQUIREMENTS.md` — DEV-01..03, PREV-01..08, ACCESS-01..05; PREV-03 and Out of Scope need updating per D-07
- `.planning/PROJECT.md` — Constraints (Locality, Safety), Environments table, Key Decisions (update per D-01..D-07)
- `.planning/STATE.md` — Phase 2 blockers (reset must wipe `family_hub_backups/`; open research questions)

### Research
- `.planning/research/SUMMARY.md` — Phase 2 delivers list, pitfalls 1–3 and 5 (identity, notifications, backup resurrection, stale cards), port choices
- `.planning/research/ARCHITECTURE.md` — compose base/overlays, seed engine via public HA APIs, deploy/reset tool design
- `.planning/research/PITFALLS.md` — Preview identity and isolation pitfalls
- `.planning/research/STACK.md` — pinned image, Docker Engine + Compose v2, `aiohttp` seed tooling

### Versions and prior phase
- `versions.env` — HA_VERSION 2026.10.4 (single pin source), HA_MIN_VERSION 2024.12.0
- `.planning/phases/01-clean-foundation/01-CONTEXT.md` — D-10 (`dev/.ha-*` gitignored volumes), D-17 (never rename domain, websocket prefixes or card tags), D-19 (version scheme for the build stamp)

### Codebase maps and docs
- `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/INTEGRATIONS.md` — entry setup, Lovelace storage collection use (~`__init__.py` 12193–12330)
- `DOCUMENTATION.md` — card YAML for the dashboard (D-18), runtime requirements (`calendar.*`, `todo.*`, `notify.*`)
- `README.md` — current behaviour

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Lovelace resource auto-registration: `custom_components/family_hub/__init__.py` ~12193–12330 (`resource_collection.async_create_item`, dashboards lookup). It is best-effort, so the seed must verify resources by reading them back.
- Google calendar awareness already exists: calendar colours from Google (`__init__.py` ~1313, ~1380) and calendar-platform friendly names (~3699–3730). Recurring-edit handling references Google's dialog (~3895).
- Delete-event flow: `card/family-week-calendar-card.js` ~23682 (button), ~23698 (`family_hub/calendar/delete_event`), and the `can_delete_event` permission (~12160, ~23472). This is the hook point for D-09.
- Kiosk commands (`ws_kiosk_set_pin`, `ws_kiosk_elevate` in `chores_websocket_api.py` ~2140–2235) are relevant to seeding PINs and child accounts.

### Established Patterns
- Notify auto-discovery: per-user `notify.mobile_app_<slug>` (`__init__.py` ~1971–1995). Preview must map each person explicitly to `notify.persistent_notification`, because adding Companion servers creates `mobile_app` devices on Preview, which would otherwise receive reminders and timers on real phones.
- `store.py` `_maybe_restore_backup` (~371) restores `family_hub_backups/` when a Store loads empty, so reset must delete the whole volume.
- Only `card/` and `panel/` JS is served; the build stamp (D-20) and delete warning (D-09) go in `card/` copies.

### Integration Points
- Seed through public HA APIs (onboarding, auth WebSocket, config-flow REST for Google Calendar/Local To-do, `calendar.create_event`, `todo.add_item`, `family_hub/*` commands). Never write `.storage` of a running HA, except possibly the narrow credential preservation in D-10, which the researcher must validate.
- Google Calendar integration setup needs application credentials and an OAuth flow (browser step); this cannot be fully scripted on a fresh volume, which is why D-10 exists.

</code_context>

<specifics>
## Specific Ideas

- She uses an **Android** phone; every access step in the guide is written for Android.
- Example build stamp: `Preview · 2.0.0+a1b2c3d · 27 Oct 14:05`.
- The first change she sees is one she chose herself, recorded in her words.
- The Preview server is named "Family Hub PREVIEW".

</specifics>

<deferred>
## Deferred Ideas

- Moving Preview to dedicated always-on hardware (restores true always-on): later, once hardware is chosen.
- Home hardware choice (HA Green / mini PC / other): Phase 4.
- Wall-tablet bookmark/kiosk access: already v2 (ENVX-02).
- Publishing the family guide on the Docusaurus site: later.
- PREVIEW banner strip: not wanted now; reconsider if she confuses Preview with Home.

</deferred>

---

*Phase: 02-dev-family-preview*
*Context gathered: 2026-10-27*
