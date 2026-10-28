# Phase 2: Dev + Family Preview - Research

**Researched:** 2026-10-28
**Domain:** Docker Compose HA environments (Dev + Preview) for a Home Assistant custom integration, API-driven seeding through public HA APIs, deploy/reset tooling, Google Calendar (read/write) in a non-production instance, local-CA HTTPS for an Android Companion client
**Confidence:** MEDIUM-HIGH. Backend, seeding, dashboard, sidebar, HTTP/TLS and Google-entry mechanics are HIGH: they were executed against a real Home Assistant Core 2026.10.4 started from `pip` (no Docker) in this session. Docker-on-laptop, Android Companion trust of a user CA, and Google OAuth behaviour are MEDIUM/LOW (documentation and issue-tracker evidence; no phone, no Docker daemon, no Google account in this sandbox).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Preview host and address
- **D-01:** Preview runs on the **developer's Dev laptop** (local, not cloud), as its own HA container, volume and port (8124), separate from Dev (8130). A cloud host was explained and declined. — **Reversibility:** reversible — tooling is host-agnostic (D-04).
- **D-02:** Cloud hosting is not used for Preview or Home. The no-cloud locality rule stands, apart from the Google Calendar API exception in D-07.
- **D-03:** "Always-on" is relaxed for Phase 2: Preview is available whenever the laptop is on and at home. Her try-outs happen at agreed times. Containers use `restart: unless-stopped` so Preview comes back by itself after a reboot or wake. Reword ROADMAP Phase 2 success criterion 1 ("at any time") and PREV-01 ("always-on") to match; always-on returns once Preview moves to a dedicated box.
- **D-04:** Portability: the tooling must work on any Linux or macOS host with Docker Engine/Compose v2, with no laptop-specific paths and all host-specific values in one gitignored env file. Moving hosts = copy repo + env file + run `reset-preview` (a fresh seed; no volume migration). The researcher checks Docker-on-laptop specifics (Docker Desktop on macOS vs Engine on Linux, sleep behaviour).
- **D-05:** Stable address = a **router DHCP IP reservation** for the laptop; Preview is reached at `https://<reserved-ip>:8124`. After a move, only the IP changes.
- **D-06:** **HTTPS from day one** for Preview (and Dev, for parity): a local CA or self-signed certificate that her Android phone trusts once. The researcher must confirm the Android HA Companion app accepts a user-installed CA. If it does not, report the fallback options before planning around it; do not silently drop to HTTP.
- **D-06a:** Home hardware is **not decided**. Record only the rule: Home never shares a volume, network identity (`core.uuid`), credentials or config with Dev or Preview. Where Home runs is decided in Phase 4.

#### Family, calendars and seed data
- **D-07:** Dev and Preview use **HA's Google Calendar integration, read/write**, connected to a **chosen list** of the family's real Google calendars. The developer chose this knowing Family Hub can create and delete events. This needs Google OAuth application credentials (a Google Cloud project), the one accepted cloud exception. Update PROJECT.md (Out of Scope, Constraints, Key Decisions) and REQUIREMENTS.md (PREV-03, Out of Scope) to match. — **Reversibility:** one-way — any real event deleted or changed from Dev or Preview is gone from the family's Google calendars unless restored from the D-08 backup.
- **D-08:** Guardrail: before `deploy-preview` and `reset-preview` (and the Dev equivalents), export every connected Google calendar to a **dated local `.ics` backup** (gitignored, outside the HA volume so reset doesn't delete it). Document how to restore an event from it.
- **D-09:** Guardrail: in Dev and Preview only, deleting an event on a Google-backed calendar shows an extra loud confirmation ("This is the REAL family calendar"). It must not appear on Home. The planner picks the mechanism (e.g. an env- or setting-driven flag), keeping the change small and in the served `card/` copy (the delete flow is in `card/family-week-calendar-card.js` ~line 23682, websocket `family_hub/calendar/delete_event`).
- **D-10:** Guardrail: `reset-preview` keeps the Google sign-in, so the developer doesn't re-authorise after each reset, while everything else is still wiped (including `family_hub_backups/`). The researcher checks how HA stores the application credentials and OAuth token (`application_credentials` and the config entry in `.storage`) and whether restoring just those safely is feasible. If not, re-sign-in after reset is the fallback, documented as a step.
- **D-11:** The seed **does write tagged pretend events into Google**, prefixed `[PREVIEW]` (exact tag at the planner's discretion, but it must be unambiguous). Reset and re-seed delete **only** events carrying that tag, and never touch untagged events. The developer accepts that these show up on family phones. This is the highest-risk code in the phase: tag matching must be exact, and it needs a dry-run mode and a test.
- **D-12:** Family members use **real first names, kept out of git**: the seed reads members, roles, kids' ages, the chosen Google calendar list and similar values from a gitignored local file (e.g. `tools/seed/family.local.yaml`). The repo ships an invented example family file with the same schema, used when no local file exists.
- **D-13:** HA accounts for **every family member**: admin for the developer, non-admin for her, and non-admin accounts for each kid set up as Family Hub child accounts (so kid PIN sign-in can be tried).
- **D-14:** Seed content = core plus a little of each extra: Family Hub calendar mapping, meals for most nights, a handful of chores per kid, 3–5 rewards, the required `todo.*` lists, plus one goal, one morning routine and a few recipes. Grocy stays off. Chores, meals and other Family Hub data are date-relative (relative to today).
- **D-15:** Dev uses the **same Google calendar connection and guardrails** as Preview (D-07..D-11). Dev and Preview both writing tagged events to the same Google calendars must not clobber each other: tags or reset logic must tell Dev's seeded events from Preview's (e.g. `[PREVIEW]` vs `[DEV]`).

#### Her access and what she sees
- **D-16:** She opens Preview via the **HA Companion app on Android, with Preview added as a second server** (Home can be added later as another server; never replace one with the other).
- **D-17:** PREVIEW identity = server/location name **"Family Hub PREVIEW"** plus a **distinct built-in Family Hub theme**, different from what Home will use. No banner strip.
- **D-18:** Her dashboard mirrors the **upstream documented layout**: Calendar (week card) first, then Today, Chores, Rewards, To-dos, Recipes/Pantry, using `DOCUMENTATION.md`'s card YAML. It is created automatically by the seed (storage-mode dashboard, resources verified), and she sees only this dashboard, with the admin sidebar items hidden (ACCESS-01).

#### Change hand-off, build stamp, guide
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

### Deferred Ideas (OUT OF SCOPE)
- Moving Preview to dedicated always-on hardware (restores true always-on): later, once hardware is chosen.
- Home hardware choice (HA Green / mini PC / other): Phase 4.
- Wall-tablet bookmark/kiosk access: already v2 (ENVX-02).
- Publishing the family guide on the Docusaurus site: later.
- PREVIEW banner strip: not wanted now; reconsider if she confuses Preview with Home.

**Scope changes agreed in discuss-phase (CONTEXT `<domain>`; the planner must reflect them):** (1) Preview runs on the developer's laptop for now, so "always-on" becomes "available whenever the laptop is on at home". (2) Dev and Preview connect read/write to a chosen list of the family's real Google calendars. This overrides PREV-03's calendar clause, the PROJECT.md/REQUIREMENTS.md out-of-scope row "Real family calendars or data in Preview", and ROADMAP Phase 2 success criterion 2's "or touches the real family calendars". The notification/speaker isolation half of PREV-03 is unchanged.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEV-01 | One-command Dev HA (Compose, pinned image, own port, integration mounted live) | Compose base + overlay pattern; image tag `2026.10.4` verified on ghcr.io; Dev port 8130 bound to loopback; `:ro` bind mount + `PYTHONDONTWRITEBYTECODE=1` |
| DEV-02 | Python changes after HA restart, card JS after browser refresh, no copying | Static paths serve straight from the mounted dir; served JS has `ETag`/`Last-Modified` and no `Cache-Control` (heuristic caching caveat, A9) |
| DEV-03 | Dev seeded from the same tool, resettable incl. `family_hub_backups/` | Same `tools/seed` entry point; reset = stop, delete whole volume (helper container), re-seed; Google entry preservation pattern |
| PREV-01 | Reachable stable address, separate HA instance sharing nothing with Home | D-01/D-05; bridge networking; discovery integrations omitted; own `core.uuid` (never copy Home config) |
| PREV-02 | Distinct name, theme, server entry | `config/core/update` `location_name` verified; built-in theme ids quoted; Companion server list |
| PREV-03 | Nothing reaches the real world (notifications) and calendar clause rewritten per D-07 | Notifications only go to explicit `notifyTargets`/`alarmDevices` (all default off); verification checks listed; Google guardrails D-08..D-11 |
| PREV-04 | Realistic current week, date-relative, never stale | Seed commands all verified; refresh command + scheduling recommended (Pitfall 9) |
| PREV-05 | `deploy-preview <branch>` restarts and verifies served cards | `git archive` export, stamp substitution, restart, readiness (not `/api/onboarding`), served-hash check against `lovelace/resources` |
| PREV-06 | `reset-preview` clears everything incl. backups | Whole-volume wipe; Google entry preservation; HTTP-config promote step |
| PREV-07 | Visible build stamp | Placeholder substitution at deploy time (Pattern 6); `hass.config.location_name` gives the environment |
| PREV-08 | Dashboard + resources auto-created and verified | `lovelace/dashboards/create` + `lovelace/config/save` verified; 13 resources auto-registered and read back |
| ACCESS-01 | Her non-admin account sees only Family Hub | `frontend/set_user_data` key `sidebar` as her token verified in a real browser; panel id `theme-builder` must be hidden too |
| ACCESS-02 | One tap from phone | Companion second server (D-16); CA trust evidence and fallbacks in Standard Stack/Pitfalls |
| ACCESS-03 | Plain-language guide in `docs/family/` with screenshots | Headless Chromium screenshot recipe verified (token injection into `hassTokens`) |
| ACCESS-04 | She ticks a chore and redeems a reward unaided | Verified as a non-admin: assignee can `chores/complete`, user can `rewards/redeem` own balance |
| ACCESS-05 | She confirms one trivial deployed change | Build stamp + deploy flow; first change is D-22 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Extracted from `/home/user/HA-Family-Hub/.claude/CLAUDE.md` (treated as locked, same authority as CONTEXT decisions):

- **License:** GPLv3 derivative; keep upstream credit.
- **Platform:** HA custom integration, HA >= 2024.12.0 declared (`hacs.json`); Dev, Preview and tests pinned to 2026.10.4 in `versions.env`.
- **Tech stack:** Python on HA Core APIs with no extra Python deps in the integration; vanilla JS web components, no bundler, build-free delivery.
- **Locality:** everything runs locally; no cloud services (Phase 2 exception: Google Calendar API, D-07).
- **Safety:** Preview isolated from the family's real HA; experiments must never break the real setup.
- **Usability:** acceptance criteria and UAT are things she does and sees; she is non-technical.
- **Code health:** changes to `__init__.py` or the calendar card should extract focused modules rather than grow the monoliths; no tests exist yet, so large files are risky. Keep the D-09 and D-20 card changes tiny and additive.
- **Served paths:** only `card/` and `panel/` JS is served; edits must target those copies.
- **Conventions:** double quotes, `from __future__ import annotations` first in Python modules, `_LOGGER` with `%s` lazy formatting, no `print()` in integration code, no debug `console.log` in committed cards (`console.info` for the build stamp is explicitly decided in D-20), no `.bak_*` files, new backend constants in `const.py`, new websocket commands in the matching `*_websocket_api.py` `ALL_COMMANDS`.
- **GSD workflow:** file changes go through a GSD command; no direct repo edits outside a GSD workflow.
- **Project skills:** none found (`.claude/skills/` and `.agents/skills/` do not exist).

## Summary

The whole backend half of this phase is feasible with public HA APIs only, and it was demonstrated end to end. In this session a real Home Assistant Core 2026.10.4 (Python 3.14.9, installed with `uv pip install homeassistant==2026.10.4`, no Docker) was started with this repository's integration, and a script onboarded it, created a non-admin account for her and kid accounts, created Local Calendar and Local To-do entries, drove the Family Hub config flow (including the `member_profile` loop), created a storage-mode dashboard, confirmed 13 card resources auto-registered, seeded chores/rewards/goals/routines/PINs/settings/theme/meals/events, hid every sidebar panel except Family Hub for her, and then rendered her dashboard in headless Chromium as her. Family Hub's `voluptuous`-based websocket commands work unchanged on HA 2026.10.4 even though HA core itself moved to its `probatio` fork.

Four findings change the plan materially. (1) **HA 2026.10 imports `http:` YAML once as a *pending* config and restarts back to the default (HTTP, port 8123) after 5 minutes unless an admin calls `http/config/promote`.** HTTPS on a fresh Preview volume therefore needs the seed to promote it, or it silently disappears five minutes after every reset. (2) **D-10 is feasible**: only the Google *config entry* (it holds the token) needs preserving; the OAuth client can be re-created through `application_credentials/create`, and a pre-written `core.config_entries` containing only that entry loads once the credential exists and the entry is reloaded. Two hard prerequisites: the Google OAuth app must be published ("In production"), or Google expires the refresh token every 7 days, and the `my:` integration must be loaded or HA will not use the `my.home-assistant.io` redirect that Google accepts. (3) **Companion trust of a user-installed CA is supported but only recently stable**: the Android app fixed a user-CA regression in release 2026.6.5 (PR #7044, merged 2026-06-18); custom ROMs (/e/OS, LineageOS) had failures. A name-constrained CA created with plain `openssl` was verified to work with HA's TLS and to refuse public names. (4) **`reset-preview` logs her phone out**: wiping the volume removes the auth store, so her Companion session on the Preview server is invalid until she signs in again; this is a plan-level UX item, not a bug.

Seeding the tagged Google events (D-11) is the highest-risk code and is testable without Google: Local Calendar exposes the same create/read/delete API surface (`calendar.create_event`, `GET /api/calendars/<entity>` returning `uid`, WS `calendar/event/delete`), so the tag-matching logic can have an automated test and dry-run against a Local Calendar in a pip-installed HA.

**Primary recommendation:** Build `tools/seed/` as a small `aiohttp` client that only talks to HA's public APIs (steps verified below), drive it from thin `scripts/*` wrappers, run its automated tests against a pip-installed HA 2026.10.4 (not Docker), and treat Docker/Android/Google steps as explicit human-verify checkpoints on the developer's laptop and her real phone.

## Answers to the Questions CONTEXT and ROADMAP Assign to Research

| Question | Answer | Confidence |
|----------|--------|------------|
| **D-10**: how HA stores app credentials and the OAuth token; is preserving only those safe? | Credentials: `.storage/application_credentials`, item `id` = slug of `google.<client_id>` (e.g. `google_fake_client_apps_googleusercontent_com`), fields `domain, client_id, client_secret, name`. Token: inside the Google config entry in `.storage/core.config_entries` (`data.token`, `data.auth_implementation`, `data.credential_type`), entry `unique_id` = the account's primary calendar id. Preserving **only the Google entry** is feasible and was verified mechanically: pre-write a `core.config_entries` holding just that entry, start HA, create the credential via WS `application_credentials/create`, `POST /api/config/config_entries/entry/<id>/reload` -> state `loaded`. Without the credential the entry goes to `setup_error` ("re-authentication required"). The OAuth client id/secret need not be preserved (recreate from the local file). Fallback: re-sign-in via the UI (Google "Web application" client, redirect `https://my.home-assistant.io/redirect/oauth`). | HIGH (mechanics, spike), MEDIUM (real Google token behaviour) |
| **D-06**: does Android Companion accept a user-installed CA? | Yes, with caveats. Home Assistant Android PR #7044 (merged 2026-06-18) "Use default Trust manager and fallback to user installed CA" shipped in 2026.6.5; issue #5565 (Fairphone/e-OS) shows earlier failures and that a name-constrained CA worked for a reporter. Maintainer position: the app relies on the device trust store. Fallbacks if it fails on her phone: Chrome "Add to Home screen" shortcut (Chrome trusts user CAs; ACCESS-02 allows a home-screen shortcut), a publicly trusted cert on a domain you own (DNS-01 challenge) pointing at the LAN IP, Tailscale HTTPS (deferred), or plain HTTP only as an explicit, documented decision. | MEDIUM |
| **D-04**: Docker-on-laptop specifics | HA docs: "Docker *Desktop* will not work; you must use Docker *Engine*" (for the documented host-network install). With bridge networking + a published port Desktop is technically usable but unsupported by HA, and has a known VM clock-drift-after-sleep problem. Engine on Linux is the recommended target. Published ports bind all interfaces by default. See Pitfalls 6-8. | MEDIUM |
| Dashboard + resource creation path | Storage-mode: WS `lovelace/dashboards/create` then `lovelace/config/save`. The integration's own best-effort resource registration **worked** on 2026.10.4 (13 resources logged and returned by `lovelace/resources`), so the seed only needs to read back and assert, and falls back to `lovelace/resources/create` if any is missing. | HIGH |
| Which `family_hub/*` commands seed data without a kiosk session | An admin token alone suffices: `chores/create`, `rewards/add_catalog_item`, `rewards/adjust_balance`, `goals/create`, `routines/create`, `kiosk/set_pin`, `permissions/set`, `get_settings`/`set_settings`, `set_recipes` all succeeded. Meals are plain `todo.add_item` calls on `todo.meal_plan`. | HIGH |
| Driving the 11-step config flow | Step ids and field names below (verified by running the flow). `async_step_user` returns the `features` form directly. | HIGH |
| Non-admin dashboard and sidebar | Create the dashboard (non-admin visible), log in **as her** (login_flow) and call `frontend/set_user_data` key `sidebar` with `hiddenPanels` computed from her `get_panels` (everything except `family-hub`). Verified in headless Chromium: before including `theme-builder` in the list it still showed, proving the id must be exact. | HIGH |
| HTTPS secure-context differences | Only one secure-context-sensitive API use exists in the served JS (clipboard, with an `execCommand` fallback), see Pitfall 12. | HIGH |
| Preview host + Companion second server | Laptop per D-01; multi-server in the Android app is official ("Settings > Companion app", add server). Companion registers a `mobile_app` device per server and shares sensors/location with every server. | MEDIUM |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Run HA instances (Dev/Preview) | Host / Docker | -- | Compose base + per-env overlay; no shared volume, own `core.uuid` |
| TLS termination | HA Core `http` (in-container) | Host cert files (bind-mounted ro) | Simplest; same cert for Dev and Preview; no reverse proxy needed |
| Bootstrapping users/entries/dashboard | Seed tool (host, public HA APIs) | -- | Never write `.storage` of a running HA |
| Family data (chores, rewards, goals, routines, PINs, settings, theme) | Family Hub backend via its own `family_hub/*` commands | Seed tool | Admin-gated commands already exist; no new backend code needed |
| Meals, to-do lists, local calendars | HA built-ins (`todo.add_item`, `calendar.create_event`) | Seed tool | Family Hub stores meals in `todo.meal_plan` item descriptions |
| Real family calendars | HA Google Calendar integration | Seed tool (tag + disable non-chosen entities) | Read/write per D-07 |
| Google sign-in persistence | Seed tool + host secrets dir (`dev/.ha-*`, 0600) | HA `application_credentials` | Only the config entry JSON is preserved |
| Calendar backups (`.ics`) | Host script | Google secret iCal address | Outside the HA volume (D-08) |
| Build stamp + deploy | `deploy-preview` (host) | Card JS placeholder constants | Stamp substituted into the deployed copy; Dev shows "live" |
| Delete-event warning (D-09) | Calendar card (browser) | `family_hub/calendar/delete_support` already returns `platform` | Tiny additive change in `card/` |
| Her sidebar/default dashboard | HA frontend user data (her token) | Seed tool login-flow | Per-user; cannot be set from an admin token |
| Guide + screenshots | Static Markdown (`docs/family/`) | Headless Chromium against seeded Dev | Verified token-injection recipe |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Home Assistant container `ghcr.io/home-assistant/home-assistant` | `2026.10.4` (manifest HTTP 200 on ghcr.io) [VERIFIED: ghcr.io registry API, this session] | Dev + Preview runtime | Pinned in `versions.env` as `HA_VERSION=2026.10.4`; same version the Phase 3 test plugin pins |
| Docker Engine + Compose v2 | Engine >= 23.0.0 [CITED: home-assistant.io/installation/linux] | Run containers | HA's stated minimum; Docker Desktop not supported by HA docs |
| Python | 3.14 via `uv` (3.14.9 installed in the spike) [VERIFIED: `uv venv --python 3.14`] | Seed tool + optional pip-installed HA for tests | HA 2026.10 core requires 3.14 (core source uses PEP 758 `except A, B:`) |
| `aiohttp` | 3.14.5 (installed as an HA dependency) | Seed tool REST + WebSocket client | Already part of HA's dependency set; user creation is WebSocket-only |
| `PyYAML` | 6.0.3 (installed as an HA dependency) | Read `family.local.yaml` / example family file | HA dependency; avoids a new pin |
| `openssl` | 3.0.13 here; any 3.x [VERIFIED: ran it] | Name-constrained local CA + leaf cert | No mkcert dependency; constraint verified to reject public names |
| `playwright` (Python) | 1.64.1 (Chromium headless shell 156) [VERIFIED: installed and rendered her dashboard] | Guide screenshots (and Phase 3's TEST-05 later) | Matches the Phase 3 stack decision |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `homeassistant` (pip) | 2026.10.4 | Automated seed-tool tests without Docker | CI/sandbox verification; the same venv the Phase 3 pytest plugin will use |
| `gcal-sync` / `ical` | 9.2.0 / 14.3.0 (pulled by HA's `google` integration at runtime) | Google Calendar integration requirements | Not installed by us; listed in `google/manifest.json` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Name-constrained `openssl` CA | `mkcert` | mkcert's CA is unconstrained (a stolen root key can impersonate any site on every device that trusts it); mkcert is fine for the laptop browser only. Either satisfies D-06 |
| `http:` YAML + `http/config/promote` | `http/config/configure` WS (sets pending, restarts, then promote) | YAML import is deprecated, with a repair issue, `breaks_in_ha_version="2027.2.0"` [VERIFIED: homeassistant/components/http/config.py]. YAML is one start fewer; revisit when HA is bumped |
| Bind-mounted config dir | Named Docker volume | Bind mount keeps host tooling simple and matches Phase 1 D-10 (`dev/.ha-*`); root-owned files need a helper container to delete (Pitfall 7) |
| Secret iCal address for `.ics` backups | Google Calendar API export with the preserved token | iCal address needs no OAuth but exposes a read URL per calendar; API export is lossless but needs custom ICS conversion |
| Google "Device Auth" client | Web application client | Device auth is legacy: "those credentials are no longer recommended" [CITED: home-assistant.io/integrations/google]; but the HA flow still tries device auth first when the credential is of that type |

**Installation (seed tool environment):**
```bash
uv venv --python 3.14 .venv            # versions.env: PYTHON_VERSION=3.14
uv pip install --python .venv/bin/python "homeassistant==2026.10.4"   # tests only; brings aiohttp, PyYAML
uv pip install --python .venv/bin/python playwright && .venv/bin/python -m playwright install chromium   # screenshots only
```

**Version verification:** `homeassistant 2026.10.4`, `aiohttp 3.14.5`, `pyyaml 6.0.3`, `playwright 1.64.1`, `gcal-sync 9.2.0`, `ical 14.3.0`, `home-assistant-frontend 20260930.5` were read from `uv pip list` after installing in this session. The image tag `2026.10.4` returned HTTP 200 for its manifest on ghcr.io.

## Package Legitimacy Audit

`gsd-tools query package-legitimacy check --ecosystem pypi aiohttp pyyaml playwright homeassistant` returned **SUS for all four**. The reasons are data artefacts, not malice signals: `unknown-downloads` (PyPI JSON exposes no download counts), `too-new` (the *latest release* was published days ago: aiohttp 2026-10-11, playwright 2026-10-22, homeassistant 2026-10-24), and `no-repository` for playwright (PyPI metadata has no `repoUrl`). All four are long-established projects and three arrive transitively with the pinned `homeassistant` package.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| aiohttp | PyPI | long-established (aio-libs) | unavailable | github.com/aio-libs/aiohttp | SUS (seam: too-new, unknown-downloads) | Flagged: already a hard dependency of the pinned HA; planner adds one `checkpoint:human-verify` for the seed environment install |
| PyYAML | PyPI | long-established | unavailable | pyyaml.org | SUS (seam: unknown-downloads) | Flagged: HA dependency; same single checkpoint |
| playwright | PyPI | Microsoft project | unavailable | none in PyPI metadata | SUS (seam: too-new, unknown-downloads, no-repository) | Flagged: optional (screenshots); planner adds `checkpoint:human-verify` before installing |
| homeassistant | PyPI | long-established | unavailable | home-assistant.io | SUS (seam: too-new, unknown-downloads) | Flagged: test/CI venv only; same checkpoint |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** aiohttp, PyYAML, playwright, homeassistant (all data-artefact SUS; the planner inserts one `checkpoint:human-verify` covering the seed environment before first install).

*Package names were taken from the project's own STACK.md and the pinned HA dependency set, and were installed from PyPI in this session; they are `[ASSUMED]` for gating purposes because the seam did not return OK. No npm packages are introduced in this phase.*

## Architecture Patterns

### System Architecture Diagram

```
                     versions.env (HA_VERSION=2026.10.4)  +  dev/host.env (gitignored: IP, TZ, ports, creds paths)
                                         |
        +--------------------------------+----------------------------------+
        |                                                                   |
 scripts/dev-up, dev-reset                                  scripts/deploy-preview <branch>, reset-preview, refresh-preview
        |                                                                   |
        |  (1) calendar .ics backup (Google secret iCal URLs) -> dev/.ha-backups/<date>/      [D-08]
        |  (2) docker compose down; wipe volume via helper container (keep custom_components/)
        |  (3) write fresh config: configuration.yaml (rendered), .storage/core.config_entries
        |      containing ONLY the preserved Google entry (if any)                            [D-10]
        |  (4) deploy: git archive <branch> -> stamp substitution -> rsync --delete into volume
        |  (5) docker compose up -d   (HA first boot ~1-3 min; pending HTTP config starts 5 min revert timer)
        v                                                                   v
+-------------------------+                              +-----------------------------------+
| DEV HA   :8130 (127.0.0.1)                             | PREVIEW HA  :8124 (LAN)            |
| bind-mount working copy (:ro)                          | exported branch copy, restart      |
| https cert from dev/.ha-certs                          | https cert from dev/.ha-certs      |
+-----------^-------------+                              +-----------------^-----------------+
            |                                                              |
            |       tools/seed (aiohttp; public HA APIs; --target dev|preview allow-list)
            |   a. wait RUNNING   b. POST /api/onboarding/users, /core_config, /analytics, /integration
            |   c. http/config/promote  d. config/core/update  e. config/auth/create (her=system-users, kids)
            |   f. Local Calendar / Local To-do / Google entry (credential create + reload; disable non-chosen entities)
            |   g. family_hub config flow (features..finish)  h. family_hub/* commands + todo.add_item + calendar.create_event
            |   i. lovelace dashboard create/save; resources read-back  j. login as her -> frontend/set_user_data(sidebar, core)
            |   k. verify: notifyTargets allow-list, no media_player, entries allow-list, resources==served hash
            v                                                              v
   Google Calendar API (OAuth, read/write, tagged events "[DEV] ..." / "[PREVIEW] ...")   [D-07, D-11]
            ^
            |  Companion (Android) --HTTPS (user-installed CA)--> https://<reserved-ip>:8124  (her phone)
```

### Recommended Project Structure
```
dev/
├── compose.yaml                # base: image ghcr.io/home-assistant/home-assistant:${HA_VERSION:?}, TZ, PYTHONDONTWRITEBYTECODE=1, stop_grace_period: 60s
├── compose.dev.yaml            # 127.0.0.1:8130:8123, mounts custom_components/family_hub :ro
├── compose.preview.yaml        # ${PREVIEW_BIND:-0.0.0.0}:8124:8123, restart: unless-stopped, no source bind-mount
├── config-template/configuration.yaml   # rendered per env (name, time zone, http ssl block, my:, mobile_app:, frontend, lovelace, config)
├── host.env.example            # committed; copy to dev/host.env (gitignored): TZ, PREVIEW_HOST_IP, ports, paths to secrets
├── .ha-dev/ .ha-preview/       # HA volumes (gitignored by existing `dev/.ha-*`)
├── .ha-certs/ .ha-secrets/ .ha-backups/   # CA/leaf (0600 keys), preserved Google entry (0600), dated .ics backups (all matched by `dev/.ha-*`)
tools/seed/
├── client.py                   # REST + WS wrapper, ssl context from CA file, target allow-list (dev|preview only)
├── onboard.py  users.py  entries.py  family_hub.py  google.py  calendar_tags.py  dashboard.py  verify.py
├── cli.py                      # seed / refresh / verify / google-signin / backup-calendars, with --dry-run
├── data/family.example.yaml    # invented family, same schema as the local file (default provider: local calendars)
└── family.local.yaml           # gitignored (add `tools/seed/*.local.*` to .gitignore)
scripts/                        # thin wrappers only: dev-up dev-reset deploy-preview reset-preview refresh-preview make-certs check-preview
docs/family/                    # getting-started.md + img/ (screenshots taken from seeded Dev/Preview)
```

### Pattern 1: Compose base + per-environment overlay
**What:** One base file; overlays add mounts, port and restart policy. Both environments use the same image tag from `versions.env`. Bridge networking, no `privileged`, no `/run/dbus`, no `network_mode: host`.
**When to use:** Always (same as ARCHITECTURE.md; confirmed by HA docs that the stock snippet's host network/privileged are not required for this use).
**Example:**
```yaml
# dev/compose.yaml (sketch)
services:
  ha:
    image: ghcr.io/home-assistant/home-assistant:${HA_VERSION:?set in versions.env}
    environment: { TZ: "${TZ:?}", PYTHONDONTWRITEBYTECODE: "1" }
    stop_grace_period: 60s          # [CITED: home-assistant.io/installation/linux compose example]
    volumes:
      - ${HA_CONFIG_DIR:?}:/config
      - ./.ha-certs:/ssl:ro         # fullchain.pem + privkey.pem referenced by the http: block
# dev/compose.preview.yaml
services:
  ha:
    restart: unless-stopped         # [CITED: docs.docker.com start-containers-automatically]
    ports: ["${PREVIEW_BIND:-0.0.0.0}:8124:8123"]
# dev/compose.dev.yaml
services:
  ha:
    ports: ["127.0.0.1:8130:8123"]
    volumes: ["../custom_components/family_hub:/config/custom_components/family_hub:ro"]
```
Start with `docker compose -p familyhub-preview --env-file versions.env --env-file dev/host.env -f dev/compose.yaml -f dev/compose.preview.yaml up -d`. (`versions.env` uses plain `KEY=VALUE` with `#` comments, which Compose env files accept; unused keys are ignored.) [ASSUMED: Compose env-file tolerance of the unused `PYTHON_VERSION`/`PYTEST_HACC_VERSION` keys; test once.]

### Pattern 2: Minimal `configuration.yaml` (not `default_config:`)
**What:** `DEFAULT_INTEGRATIONS` already contains `application_credentials`, `backup`, `frontend`, `person`, `zone` etc. [VERIFIED: homeassistant/bootstrap.py:215-252]. `default_config` adds `bluetooth, cloud, dhcp, ssdp, usb, zeroconf, go2rtc, stream, assist_pipeline, conversation, homeassistant_alerts` and others [VERIFIED: default_config/manifest.json] that should not run in an isolated Preview. Add only what is needed.
**Must include `my:`** or Google OAuth cannot use the `my.home-assistant.io` redirect: `async_get_redirect_uri` returns `https://my.home-assistant.io/redirect/oauth` only `if "my" in hass.config.components` [VERIFIED: helpers/config_entry_oauth2_flow.py:131-135]. Otherwise it builds `<frontend base>/auth/external/callback`, which Google will not accept for a private IP.
**Example:**
```yaml
homeassistant:
  name: "Family Hub PREVIEW"      # also set/asserted via WS config/core/update (verified)
  time_zone: Europe/London        # from host.env; must equal Home's later
http:
  ssl_certificate: /ssl/fullchain.pem
  ssl_key: /ssl/privkey.pem
frontend:
lovelace:
config:
my:
mobile_app:                       # needed by the Companion app  [ASSUMED: not exercised in the spike; PyNaCl installs at first start]
```
The `http:` block is imported **once** into `.storage/http` as *pending* and the seed must promote it (Pitfall 1).

### Pattern 3: API-driven seed, in this order (all steps executed against HA 2026.10.4)
1. **Wait for RUNNING** (not `/api/onboarding`; Pitfall 2).
2. **Onboard** a pristine volume: `POST /api/onboarding/users` with `{client_id, name, username, password, language}` -> `auth_code`; `POST /auth/token` (authorization_code, `client_id` equal); then `POST /api/onboarding/core_config` `{}`, `POST /api/onboarding/analytics` `{}`, `POST /api/onboarding/integration` `{client_id, redirect_uri}` (redirect must start with `client_id`). All four steps must be done or `/api/onboarding` still lists them. [VERIFIED: ran; `onboarding/const.py` `STEPS = [STEP_USER, STEP_CORE_CONFIG, STEP_ANALYTICS, STEP_INTEGRATION]`]
3. **`http/config/promote`** (admin WS) within 5 minutes of start. [VERIFIED]
4. **Remove unwanted onboarding side effects**: finishing `core_config` auto-starts config flows for `google_translate`, `met`, `radio_browser`, `shopping_list` [VERIFIED: onboarding/views.py `onboard_integrations`]. Delete `radio_browser` and `google_translate` entries (outbound services) via `DELETE /api/config/config_entries/entry/<id>`; `shopping_list` is harmless.
5. **Core config**: WS `config/core/update` `{location_name: "Family Hub PREVIEW", ...}`; `hass.config.location_name` then equals it. [VERIFIED]
6. **Users**: WS `config/auth/create` `{name, group_ids: ["system-users"], local_only: false}` then `config/auth_provider/homeassistant/create` `{user_id, username, password}`. Admin is the onboarding user. [VERIFIED]
7. **Local Calendar / Local To-do** via `POST /api/config/config_entries/flow` `{handler: "local_calendar"}` then step data `{calendar_name, import: "create_empty"}`; `{handler: "local_todo"}` then `{todo_list_name}`. Entity ids are the slug of the name (`Meal Plan` -> `todo.meal_plan`). Create **all five** lists the cards ask for: `todo.recipe_box`, `todo.meal_plan`, `todo.meal_plan_templates`, `todo.meal_suggestions`, `todo.family_reminders`; the headless run logged `Referenced entities todo.meal_plan_templates ... missing` and `todo.meal_suggestions ... missing` when they were absent. [VERIFIED]
8. **Google entry** (Pattern 5) or Local Calendars when no Google file exists.
9. **Family Hub config flow** (below).
10. **Family Hub data** via commands (below), meals via `todo.add_item`, events via `calendar.create_event`.
11. **Dashboard** (Pattern 4), then **her sidebar/default** (Pattern 7), then **verify** (Pattern 8).

**Family Hub config flow, verbatim values** (`config_flow.py` read this session):
- `_FEATURES_FIELD = "setup_features"` (:158), options `_FEATURE_CHORES = "chores"`, `_FEATURE_GROCY = "grocy"`, `_FEATURE_DIGEST = "digest"` (:148-150). Pick only `["chores"]` to skip the Grocy and Digest steps (Grocy off, D-14).
- Users step field `CONF_INITIAL_MEMBER_USER_IDS = "initial_member_user_ids"` (const.py:843).
- Member profile (one form **per member**, loop): `_MEMBER_COLOR_FIELD = "member_color"` (:234), `_MEMBER_INCLUDE_FIELD = "member_include_in_chores"` (:235), `_MEMBER_CALENDAR_FIELD = "member_calendar"` (:238); colors come from `_PEOPLE_COLOR_PALETTE = ["#d9bf7e", "#7ec9d9", "#d97e9e", "#9ed97e", "#b07ed9", "#d9a67e"]` (:343).
- Chores features: `_ROUTINES_FIELD = "routines_enabled"`, `_GOALS_IN_CHORES_FIELD = "goals_in_chores"`, `_GOALS_IN_REWARDS_FIELD = "goals_in_rewards"` (:272-274).
- Calendars step field `CONF_CALENDARS = "calendars"` (const.py:86); notifications field `CONF_DEFAULT_NOTIFY = "default_notify_target"` (const.py:87); dashboard step `_ADD_DASHBOARD_FIELD = "add_dashboard"` (:339, answer `false`: the seed creates the dashboard itself); finish step takes `{}`.
- Executed sequence (all `type: form` until the last): `features` -> `users` -> `member_profile` x N -> `chores_features` -> `calendars` -> `notifications` -> `dashboard` -> `finish` -> `create_entry`.

**Family Hub commands the seed uses (admin token; verified OK):** `family_hub/chores/create` (`title`, `assigned_to`, `star_value`, `due_date` ISO with offset), `family_hub/rewards/add_catalog_item` (`title`, `cost_stars`, `icon`), `family_hub/rewards/adjust_balance` (`user_id`, `delta`, `reason`), `family_hub/goals/create` (`title`, `assigned_to`, `target_count`, `reward_type: "stars"`, `star_value`), `family_hub/routines/create` (`user_id`, `category: "morning"`, `title`, `due_time`, `star_value`), `family_hub/kiosk/set_pin` (`user_id`, `pin` 4-8 digits, admin only), `family_hub/get_settings` + `family_hub/set_settings` (full replace: always GET, modify, SET), `family_hub/set_recipes`. For kid PIN sign-in to work, `settings["kioskLoginEnabledUserIds"]` must contain the kid id (chores_websocket_api.py:2148, :2205) and a PIN must be set; then any authenticated connection can `family_hub/kiosk/elevate` (verified, and the elevation token then completes a kid's chore).

### Pattern 4: Dashboard (storage mode) and resource verification
`lovelace/dashboards/create` `{url_path: "family-hub", title, icon, show_in_sidebar: true, require_admin: false, mode: "storage"}` then `lovelace/config/save` `{url_path, config}` (admin). `lovelace/resources` lists the 13 `family_hub_*` resources the integration registered itself (log lines `Family Hub: registered /family_hub_card/... as a dashboard resource`); the seed asserts the count and the `?v=<hash>` equals the served file's hash, else creates the missing ones with `lovelace/resources/create` `{res_type: "module", url}`. [VERIFIED]
Recommended layout (D-18): one **panel-type view per card** (the calendar card is documented as a single full-screen `panel` view): Calendar, Today, Chores, Rewards, To-dos, Recipes (and Pantry only if it renders sensibly with Grocy off, A8). Card YAML comes from `DOCUMENTATION.md` (Read this session): `type: custom:family-week-calendar-card` with `people: [{entity, name, color}]` plus `recipe_entity`, `meal_plan_entity`, `meal_templates_entity`, `suggestions_entity`, `reminders_entity`, `weather_entity`; `custom:family-hub-chores-card`, `-rewards-card`, `-goals-card` with optional `title`/`fab_position`; `custom:family-hub-todo-card` with `entities: [todo.*]`; `custom:family-hub-recipe-box-card`; `custom:family-today-card` with `people`, `meal_plan_entity`, `reminders_entity` (family-today-card.js:486-487).

### Pattern 5: Google Calendar in a non-production instance
1. **Once per Google Cloud project (human):** Web-application OAuth client with redirect URI `https://my.home-assistant.io/redirect/oauth`; consent screen **published** ("Publish app"), otherwise "your credentials will expire every 7 days" [CITED: home-assistant.io/integrations/google]; Google's own rule: Testing status issues a refresh token that expires in 7 days [CITED: developers.google.com/identity/protocols/oauth2#expiration]. Calendar scopes are sensitive, so an unpublished-verification warning screen appears for a personal app; acceptable for one account.
2. **After each fresh start (seed):** `application_credentials/create` `{domain: "google", client_id, client_secret, name}` from the gitignored local file; if a preserved entry exists it was already written pre-start, so `POST /api/config/config_entries/entry/<entry_id>/reload` and poll until `state == "loaded"`. [VERIFIED mechanics with a fake token]
3. **Pre-start restore:** write `.storage/core.config_entries` as `{"version": 1, "minor_version": 5, "key": "core.config_entries", "data": {"entries": [<google entry only>]}}` into the empty volume (format taken from the live file written by this HA). Keep the entry's `entry_id`, `unique_id`, `data.auth_implementation`, `data.token`. The preserved copy is taken from the **stopped** instance's file (HA flushes on stop) into `dev/.ha-secrets/google-<env>.json` with mode 0600. If this file is absent, the seed stops with the documented one-time sign-in instruction (D-10 fallback).
4. **Choose calendars:** the integration creates entities for **every** calendar on the account (`async_list_calendars` loop; unique_id `f"{config_entry.unique_id}-{entity_description.key}"` with `key = calendar_id` [VERIFIED: google/calendar.py:120-130, 239-246]), plus a Birthdays entity for the primary calendar (enabled) and a disabled Work Location one. The `track` YAML option is deprecated. So after the entry loads, list `config/entity_registry/list`, keep entities whose `unique_id` ends with a chosen `calendar_id`, and disable the rest with `config/entity_registry/update` `{entity_id, disabled_by: "user"}`. Include the primary account's Birthdays entity in the disable set unless chosen (it exposes family contacts' birthdays).
5. **Read-only calendars** (accessRole not writer) get no CREATE/DELETE features automatically (`read_only = not (calendar_item.access_role.is_writer and ... read_write)`), a free guard.
6. **Tagged events (D-11/D-15):** create with `calendar.create_event` (`summary`, `start_date_time`, `end_date_time`, optional `description`, `location`). Event summaries start with the env tag; the `description` carries a machine marker line, e.g. `family-hub-seed:preview`. **Delete only if both** the summary starts exactly with `[PREVIEW] ` (or `[DEV] `) **and** the description contains the marker for *that environment*, within a bounded date window, on allow-listed calendars. Find candidates with `GET /api/calendars/<entity>?start=&end=` (returns `uid`, `recurrence_id`) and delete with WS `calendar/event/delete` `{entity_id, uid, recurrence_id?}`. Default `--dry-run` prints what would be deleted; a test creates mixed tagged/untagged/other-env events on a Local Calendar in a pip-installed HA and asserts only the exact set is removed. Seeded events must be single (non-recurring) so deletion never needs `recurrence_range`.
7. **Reminder side effect to confirm with the developer:** HA's Google `create_event` cannot set reminders (it builds `Event(summary, description, start, end[, location])` only [VERIFIED: google/calendar.py:459-498, 547-600]), so Google applies each *subscriber's default reminders*. Tagged events inside a reminder window can buzz family phones that subscribe to the calendar. D-11 accepts events "showing up on family phones"; a phone notification is a stronger effect (Open Question 2).

### Pattern 6: Build stamp without touching `__init__.py`
Add one constant block near the top of `card/family-week-calendar-card.js`, e.g. `const __FH_BUILD = { env: "__FH_BUILD_ENV__", version: "__FH_BUILD_VERSION__", deployed: "__FH_BUILD_TIME__" };`, render it as a small footer inside the existing `<ha-card>` template (card file ~14392) and emit one `console.info`. `deploy-preview` substitutes the three tokens **in the exported copy only** (so git stays clean), which also changes the file hash, so the integration's own `?v=<hash>` logic updates the Lovelace resource at the next start (`_register_dashboard_resource` calls `async_update_item` when the hash differs, __init__.py:12238-12244). In Dev the tokens stay literal and the card shows `Dev · live from working copy`. After deploy, fetch `https://<ip>:8124/family_hub_card/family-week-calendar-card.js?v=<hash>` with the CA, assert the short git hash is present, and assert the `lovelace/resources` url hash equals `sha256(file)[:10]` (`_file_content_hash`, __init__.py:12172-12187).

### Pattern 7: Her account, sidebar and default dashboard
Log in with the seeder (login flow, not a long-lived token): `POST /auth/login_flow` `{client_id, handler: ["homeassistant", null], redirect_uri}`, `POST /auth/login_flow/<id>` `{client_id, username, password}`, then exchange the code. Using **her** token: `get_panels`, compute `hiddenPanels = [every url_path except "family-hub" (and the non-sidebar "profile", "notfound")]`, call `frontend/set_user_data` `{key: "sidebar", value: {panelOrder: [], hiddenPanels: [...]}}` and `{key: "core", value: {default_panel: "family-hub"}}`. The frontend reads `sidebar` `{panelOrder, hiddenPanels}` and `core.default_panel` [VERIFIED in hass_frontend 20260930.5 bundle]. On the spike her non-admin panel list was `calendar, climate, family-hub, home, light, lovelace, maintenance, map, media-browser, notfound, profile, security, theme-builder, todo`. The integration registers a **Theme Builder** sidebar panel with `require_admin=False` and `PANEL_URL = "theme-builder"` (const.py:939), so it shows to her unless hidden. The bell (Notifications) and her profile entry always remain; that is acceptable.

### Pattern 8: Isolation and safety verification (run by deploy/reset/refresh)
Assert, as admin: (a) every `userProfiles[*].notifyTargets` is empty or exactly `["notify.persistent_notification"]`; (b) the settings key `SETTINGS_KEY_ALARM_DEVICES = "alarmDevices"` (const.py:724) is empty/absent and no `media_player`/`assist_satellite` entity exists (timer alarms only reach speakers listed there, const.py:720-724); (c) config-entry domains are within an allow-list (`family_hub`, `local_calendar`, `local_todo`, `google`, `mobile_app`, HA built-ins such as `analytics`, `backup`, `sun`, `shopping_list`); (d) Grocy URL/key blank; (e) `location_name` matches the target (`Family Hub PREVIEW` / `Family Hub DEV`) **before** sending any credentials to the target and refuse otherwise (code-level guard behind "never test on Home"). Notification fan-out is opt-in everywhere: profile flags `notifyRewardClaimed`, `notifyChoreApproved`, `notifyChoreRejected`, `notifyChoreDue`, `notifyGoalApproved`, `notifyGoalRejected`, `notifyTimerAlarm` "All six default False" (const.py:1149-1151) and `notifyTargets` defaults to `[]`; a fresh install's `get_settings` returned `userProfiles` with `notifyTargets: []`. The only auto-discovery (`_detect_user_notify_targets`, __init__.py:1970-2000) runs in the one-time `_migrate_notify_profiles` at entry creation and on the card's "Auto-detect" button. So the real risks are the Auto-detect button and creating the Family Hub entry **after** a Companion device registered; the seed explicitly writes the safe value and the check enforces it. [VERIFIED by reading and by running: after the flow, the HA log said it "could not automatically match" `notify.persistent_notification` and wrote 4 profiles]

### Anti-Patterns to Avoid
- **Polling `/api/onboarding` for readiness** after onboarding: it returns `404 Not Found` once all steps are done [VERIFIED]; ARCHITECTURE.md's healthcheck sketch is wrong post-onboarding.
- **Putting `http:` SSL in YAML and forgetting `http/config/promote`**: HTTPS disappears 5 minutes later (Pitfall 1).
- **Writing `.storage` of a running HA**, or hand-writing more than the single Google entry before first start.
- **Deleting by summary prefix alone** on Google calendars (D-11): require the second marker and the env tag.
- **Copying Home's config** or reusing `core.uuid` (D-06a, PITFALLS 1).
- **`default_config:`** in Preview: pulls discovery, cloud and outbound integrations.
- **Hard-coding the sidebar hide list**: the panel list depends on loaded integrations; compute it from her `get_panels`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Creating users, entries, dashboards, entity-registry changes | Direct `.storage` edits | HA public REST/WS (verified list above) | `.storage` formats are internal and flushed on stop |
| OAuth token exchange for Google | Own OAuth client | HA's Google integration + `application_credentials` | HA refreshes tokens, stores them, handles reauth |
| Reading/deleting Google events | Raw Google API calls from the seed | `calendar.create_event`, `GET /api/calendars/...`, WS `calendar/event/delete` | Same surface as Local Calendar, so it is unit-testable; HA already carries the token |
| Certificate chain for LAN HTTPS | Self-signed leaf trusted directly | Name-constrained CA + leaf with IP SAN (script below) | A leaf-only cert cannot be revoked/rotated easily and Android wants a CA import; the CA key is bounded to private ranges |
| Dashboard resource registration | Custom JS resource injection | The integration's own `_register_dashboard_resource` (works on 2026.10.4) | Already handles hash updates; the seed only verifies |
| Per-user sidebar | Admin-side hacks | `frontend/set_user_data` as her | It is per-user data keyed to the connection's user |
| Reset wipe | `rm -rf` of a root-owned bind mount | Helper container (`docker run --rm -v <dir>:/config busybox ...`) | See Pitfall 7 |
| Screenshots for the guide | Manual phone captures for UI screens | Playwright + token injection into `localStorage.hassTokens` (verified) | Reproducible, themed, seeded; only the Android install screens need a real phone |

**Key insight:** every step the seed needs already has an official or integration-provided API; the work is ordering, idempotence, safety checks, and refusing to run against Home.

## Common Pitfalls

### Pitfall 1: Pending HTTP config reverts to plain HTTP after 5 minutes
**What goes wrong:** Preview serves HTTPS for five minutes after a reset, then HA restarts onto port 8123 with no TLS; her phone shows a connection error; the seed's HTTPS client dies mid-run.
**Why it happens:** HA 2026.10 migrates `http:` YAML to `.storage/http` once and stages a config that differs from the default as **pending**, scheduling `_async_revert_to_stable` after `AUTO_REVERT_DELAY = timedelta(minutes=5)` unless promoted [VERIFIED: homeassistant/components/http/config.py; reproduced: the first spike HA reverted to port 8123 with `pending ... error: not_promoted`].
**How to avoid:** after onboarding, call WS `http/config/promote` (admin); assert `http/config` shows `active_config_type: "stable"` and `revert_at: null`. Verified with TLS: pending (`revert_at` set) -> promote -> stable.
**Warning signs:** log line `Pending HTTP config was not confirmed within 0:05:00; reverting to the stable config and restarting`; `.storage/http` `pending.error == "not_promoted"`. A repair issue `deprecated_yaml` (breaks in 2027.2.0) is also created; plan the `http/config/configure` migration when HA is bumped.

### Pitfall 2: Readiness probe
**What goes wrong:** `deploy-preview` waits forever or proceeds early.
**Why:** `/api/onboarding` is 404 after onboarding; the container image may not even ship `curl` (A5).
**How to avoid:** probe from the host: login, `GET /api/config`, require `state == "RUNNING"`, then require the Family Hub entry `loaded` via `config_entries/get`. Allow a generous first-boot timeout: the pip-installed spike took about 60-80 s with runtime requirement installs; first boot on a fresh Docker volume also installs requirements (Local Calendar `ical`, Google `gcal-sync`) and needs internet.

### Pitfall 3: Google refresh token dies every 7 days
**What goes wrong:** D-10's "keep the sign-in across resets" silently stops working weekly; entries go to reauth.
**Why:** OAuth app left in "Testing" [CITED: developers.google.com/identity/protocols/oauth2#expiration]. Also tokens unused for six months and the 100-token-per-client limit.
**How to avoid:** publish the app (HA docs: "Publish app"); document re-sign-in as the fallback step; the seed's verify detects `setup_error`/reauth and prints the instruction.

### Pitfall 4: Google entry without its credential looks like an auth failure
**What goes wrong:** Pre-restoring the entry but forgetting `application_credentials/create` leaves the entry in `setup_error` with a reauth flow ("The configured authentication method is no longer available") [VERIFIED].
**How to avoid:** order = restore entry pre-start, create credential, reload entry, assert `loaded`. The credential `id` must equal the entry's `data.auth_implementation`; it is derived from the client id, so the local file's client id must not change.

### Pitfall 5: Chosen-calendars list is not a HA setting
**What goes wrong:** Every calendar on the Google account (including other people's shared calendars and birthdays) becomes an entity, and Family Hub may poll them.
**How to avoid:** disable non-chosen entities in the entity registry right after the first load (Pattern 5.4) and restrict `CONF_CALENDARS`/people to the chosen list. Reset re-creates the registry, so the disable step is part of every seed.

### Pitfall 6: Docker Desktop vs Engine on the laptop
**What goes wrong:** Desktop on macOS/Windows is unsupported by HA docs ("Docker *Desktop* will not work; you must use Docker *Engine*"), uses a helper VM, has bind-mount overhead, and its VM clock can drift after laptop sleep (long-standing reports; Docker published "Addressing Time Drift in Docker Desktop for Mac").
**How to avoid:** prefer Engine on Linux (matches D-04's "any Linux or macOS host with Engine/Compose v2"). On macOS, restart containers after wake if the time is off and keep `TZ` set; with Engine, suspended containers simply resume. `restart: unless-stopped` starts containers after a daemon/host restart; a container you stopped by hand stays stopped [CITED: docs.docker.com]. Laptop sleep does not trigger restarts; it pauses everything, so Preview is unavailable while asleep (D-03).

### Pitfall 7: Root-owned files in a bind-mounted volume
**What goes wrong:** HA runs as root in the container, so `.storage` and `family_hub_backups/` are root-owned on the host; `rm -rf` by the developer fails or needs sudo, and a half-reset resurrects data (PITFALLS 3).
**How to avoid:** `reset` stops the stack and wipes through a throwaway container (`docker run --rm -v "$HA_CONFIG_DIR":/config busybox sh -c 'find /config -mindepth 1 -maxdepth 1 ! -name custom_components -exec rm -rf {} +'`). Keep `custom_components/` (deployed code) so reset restores data, not code. Test: seed, mutate, reset, assert state equals seed and `family_hub_backups/` is empty (it lives at `<config>/family_hub_backups`: `SETTINGS_BACKUP_DIR_NAME = "family_hub_backups"` const.py:174, `hass.config.path(SETTINGS_BACKUP_DIR_NAME, filename)` store.py:319; the spike produced `chores_backup.json, goals_backup.json, permissions_backup.json, rewards_backup.json, routines_backup.json, settings_backup.json` there). [A3: root ownership not observable here (no Docker daemon)]

### Pitfall 8: Published ports and the laptop leaving the home network
**What goes wrong:** Docker publishes to all interfaces by default [CITED: docs.docker.com/engine/network/port-publishing]; on café Wi-Fi the Preview login page (and its Google token) is reachable. Binding the Preview port to the reserved LAN IP instead would make container start fail when the IP is absent [A4].
**How to avoid:** Dev bind `127.0.0.1:8130`; Preview `${PREVIEW_BIND:-0.0.0.0}` documented, with HA's default `ip_ban_enabled: true` [VERIFIED: http config defaults], strong generated passwords, no port forwarding, and a `scripts/preview-down` the developer runs before leaving home. The Google token on a laptop is the sensitive asset (Security Domain).

### Pitfall 9: "Whenever she opens Preview it shows a current week" needs a refresh job
**What goes wrong:** Seeded events/chores are date-relative at seed time; days later her view is stale (PITFALLS 4). Recurring chores only re-open after approval, so unticked chores simply go overdue; routines reset daily by themselves.
**How to avoid:** a tag-aware `refresh-preview` (re-lay events, meals, chores, balances; never touches accounts) that `deploy-preview` also runs; schedule it daily (systemd user timer/cron on Linux, launchd on macOS) plus a run at boot; the guide tells her the agreed test times. Flag the success-criterion wording in the plan.

### Pitfall 10: `reset-preview` logs her phone out
**What goes wrong:** The wipe removes `.storage/auth` and `core.uuid`; her Companion session for the Preview server is invalid, the app asks her to sign in again, and the registered `mobile_app` device is gone.
**How to avoid:** put one line in the guide ("If the app says it cannot sign in after the developer resets Preview, tap Log in and use the same username and password"). Consider writing a stable per-environment `core.uuid` (random, generated once, stored in `dev/.ha-secrets/`, never Home's) so the app sees the same instance; whether the Android app re-registers cleanly after a wipe is unverified (A10), so make it a checkpoint on her real phone.

### Pitfall 11: Companion registers on Preview and shares phone sensors
**What goes wrong:** Each added server gets its own `mobile_app` device and `notify.mobile_app_<device>`; the app can send sensors and location to every server [CITED: companion.home-assistant.io FAQ: "If you use multiple servers, make sure the correct servers have each sensor enabled."]. Preview's notify list then contains a real phone.
**How to avoid:** keep every `notifyTargets` empty/persistent-notification and let verify fail otherwise; tell the developer to disable sensors for the Preview server in app settings; also check the Android "Add server" screen can enter the URL manually since zeroconf is off [CITED: Android multi-server docs].

### Pitfall 12: Secure-context differences are small
HTTP vs HTTPS matters for Chrome/WebView features such as service workers and Assist microphone; in the served card code the only secure-context-dependent API is the clipboard, and it has a fallback: `_copyTextToClipboard` ("Best-effort clipboard write with a fallback for contexts where navigator.clipboard either doesn't exist or throws (an insecure context ...)", family-week-calendar-card.js:27719-27733). `isSecureContext`, `wakeLock`, `serviceWorker`, `mediaDevices`, `crypto.subtle` were not found in `card/`/`panel/` (grep). `http://localhost` is already a secure context, so Dev gains little from HTTPS parity beyond testing the same cert path.

### Pitfall 13: Non-admin event subscriptions
Her browser logged `Refusing to allow Her Name to subscribe to event family_hub_timer_alarm_ring` and `... family_hub_daily_digest_open` (HA allows only `SUBSCRIBE_ALLOWLIST` events to non-admins [VERIFIED: websocket_api/commands.py:194]). The chores card catches this (`_subscribeAlarmEvents`: "Best-effort - ... the same-tab-only local alarm ... still works exactly as before", family-hub-chores-card.js:1403-1425), so ticking chores and redeeming rewards are unaffected, but timer-alarm broadcast to her tab and the digest popup will not work for a non-admin. Record in the UAT notes; do not fix in Phase 2.

### Pitfall 14: Missing optional entities cause visible errors
With only some `todo.*` lists and no `weather.forecast_home`, the cards log service-call errors. Create all five lists; decide the `weather_entity` (omit `met`; check how the calendar card renders without it, A7).

### Pitfall 15: Stale JS in Dev/Preview
Served JS has `Etag` and `Last-Modified` and no `Cache-Control` [VERIFIED: curl -D]; the `?v=` hash only changes at HA start. Dev edits without restart rely on the browser revalidating on refresh (A9). Preview deploys restart HA, so the hash changes, but her phone must reload the dashboard (pull-to-refresh or reopen) to re-read `lovelace/resources` (PITFALLS 6); the build stamp makes this visible.

### Pitfall 16: Seed side effects of `core_config`
Onboarding auto-adds `radio_browser` and `google_translate` (outbound) and `met`; delete them in the seed (Pattern 3 step 4) to honour the locality rule.

## Code Examples

Verified by execution against HA 2026.10.4 unless noted. Helpers: `post(path, json, headers)` and a small WS wrapper (`{"id": n, "type": ..., ...}` -> read until matching `id`).

### Onboard a pristine instance (client_id must match the instance URL)
```python
# Source: homeassistant/components/onboarding/views.py + run in this session
BASE = "https://localhost:8124"; CID = BASE + "/"            # TLS: aiohttp ssl context built from the CA file (never verify=False)
r = await s.post(BASE + "/api/onboarding/users", json={"client_id": CID, "name": "Dev Admin",
        "username": "dev", "password": PASSWORD, "language": "en"})
code = (await r.json())["auth_code"]
tok = await (await s.post(BASE + "/auth/token", data={"grant_type": "authorization_code", "code": code, "client_id": CID})).json()
h = {"Authorization": "Bearer " + tok["access_token"]}
for step in ("core_config", "analytics"):
    await s.post(BASE + f"/api/onboarding/{step}", headers=h, json={})
await s.post(BASE + "/api/onboarding/integration", headers=h, json={"client_id": CID, "redirect_uri": CID + "?auth_callback=1"})
# then, over WS as admin:
#   {"type": "http/config/promote"}                         -> success (clears the 5-minute revert)
#   {"type": "config/core/update", "location_name": "Family Hub PREVIEW"}
```

### Create her non-admin account and a kid
```python
# WS (admin) - verified
r = await ws.call("config/auth/create", name="Her Name", group_ids=["system-users"], local_only=False)
uid = r["result"]["user"]["id"]
await ws.call("config/auth_provider/homeassistant/create", user_id=uid, username="her", password=PASSWORD)
```

### Drive the Family Hub config flow (field names quoted in Pattern 3)
```python
fid = (await post("/api/config/config_entries/flow", {"handler": "family_hub", "show_advanced_options": False}))["flow_id"]
step = lambda d: post(f"/api/config/config_entries/flow/{fid}", d)
await step({"setup_features": ["chores"]})
await step({"initial_member_user_ids": [her_id, kid1_id]})
await step({"member_color": "#d9bf7e", "member_include_in_chores": True, "member_calendar": "calendar.her_calendar"})
await step({"member_color": "#7ec9d9", "member_include_in_chores": True, "member_calendar": "calendar.kid_one_calendar"})
await step({"routines_enabled": True, "goals_in_chores": True, "goals_in_rewards": True})
await step({"calendars": []}); await step({"default_notify_target": "notify.persistent_notification"})
await step({"add_dashboard": False}); res = await step({})        # -> {"type": "create_entry", ...}
```

### Dashboard, sidebar (as her), default panel
```python
await ws.call("lovelace/dashboards/create", url_path="family-hub", title="Family Hub", icon="mdi:home-heart",
              show_in_sidebar=True, require_admin=False, mode="storage")
await ws.call("lovelace/config/save", url_path="family-hub", config=CONFIG)      # views of type "panel"
# login as her, then on HER websocket:
panels = (await her_ws.call("get_panels"))["result"]
hidden = [p for p in panels if p not in ("family-hub", "profile", "notfound")]    # includes "theme-builder"
await her_ws.call("frontend/set_user_data", key="sidebar", value={"panelOrder": [], "hiddenPanels": hidden})
await her_ws.call("frontend/set_user_data", key="core", value={"default_panel": "family-hub"})
```

### Google credential + preserved entry
```python
# credential id is derived: google_<slug of client id>; must equal entry["data"]["auth_implementation"]
await ws.call("application_credentials/create", domain="google", client_id=CLIENT_ID, client_secret=SECRET, name="Google")
await post(f"/api/config/config_entries/entry/{ENTRY_ID}/reload", {})     # -> {"require_restart": false}; state becomes "loaded"
# pre-start file (HA stopped, empty volume):  .storage/core.config_entries
# {"version": 1, "minor_version": 5, "key": "core.config_entries", "data": {"entries": [<google entry>]}}
```

### Name-constrained local CA + leaf (verified with `openssl verify` and with HA serving HTTPS)
```bash
# ca.cnf [v3_ca]: basicConstraints = critical, CA:TRUE, pathlen:0 ; keyUsage = critical, keyCertSign, cRLSign ;
#   nameConstraints = critical, permitted;IP:192.168.0.0/255.255.0.0, permitted;IP:127.0.0.0/255.0.0.0, permitted;DNS:localhost
openssl ecparam -name prime256v1 -genkey -noout -out ca.key
openssl req -x509 -new -key ca.key -sha256 -days 1095 -config ca.cnf -out ca.crt
# leaf.cnf [v3_req]: basicConstraints = critical, CA:FALSE ; keyUsage = critical, digitalSignature ;
#   extendedKeyUsage = serverAuth ; subjectAltName = IP:<PREVIEW_HOST_IP>, IP:127.0.0.1, DNS:localhost
openssl ecparam -name prime256v1 -genkey -noout -out leaf.key
openssl req -new -key leaf.key -config leaf.cnf -out leaf.csr
openssl x509 -req -in leaf.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -sha256 -extfile leaf.cnf -extensions v3_req -out leaf.crt
openssl verify -CAfile ca.crt leaf.crt                                   # leaf.crt: OK
# a leaf for DNS:evil.example.com fails: "error 47 ... permitted subtree violation"
```
Add `10.0.0.0/255.0.0.0` and `172.16.0.0/255.240.0.0` to `permitted` if the home LAN uses them. Keep leaf validity at or below ~1 year; the /e/OS issue thread reported a 10-year certificate failing while 180 days worked (anecdotal, unconfirmed). Install **only `ca.crt`** on the phone; never `ca.key`. Serve `fullchain.pem` (= leaf then CA is optional) and `privkey.pem`.

### Headless screenshot of her dashboard (for `docs/family/`)
```python
tokens = {"access_token": t["access_token"], "token_type": "Bearer", "expires_in": t["expires_in"],
          "hassUrl": BASE, "clientId": CID, "expires": int(time.time()*1000) + t["expires_in"]*1000,
          "refresh_token": t["refresh_token"]}
ctx = await browser.new_context(viewport={"width": 412, "height": 900}, device_scale_factor=2, is_mobile=True)
await ctx.add_init_script("localStorage.setItem('hassTokens', %s);" % json.dumps(json.dumps(tokens)))
page = await ctx.new_page(); await page.goto(BASE + "/"); await page.wait_for_timeout(30000)   # HA frontend is slow on first load
```
Result in the spike: landed on `/family-hub/home` (system default panel), calendar card rendered in the `blossom` theme with the seeded `[PREVIEW] Dentist` event, and the sidebar showed only Family Hub (+ Theme Builder before it was added to `hiddenPanels`).

### Meals and events (HA built-ins)
```python
desc = json.dumps({"description": "", "link": "", "color": "", "block": 0, "recur": None, "grocyRecipeId": None,
                   "servings": None, "spanDays": 1, "additionalRecipes": [], "leftoverDates": []})
await call_service("todo", "add_item", {"entity_id": "todo.meal_plan", "item": "Spaghetti night", "description": desc, "due_date": "2026-10-29"})
await call_service("calendar", "create_event", {"entity_id": cal, "summary": "[PREVIEW] Dentist",
                   "start_date_time": "2026-10-29 01:00:00", "end_date_time": "2026-10-29 02:00:00",
                   "description": "family-hub-seed:preview"})
```
(The meal description shape is the Python twin of the card's encoder, `_encode_dish_description`, __init__.py:3324-3365; keys quoted there.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `http:` options only in YAML | YAML imported once into `.storage/http` as pending; promote or auto-revert in 5 minutes; YAML deprecated (`breaks_in_ha_version 2027.2.0`) | HA 2026.x [VERIFIED in core source] | HTTPS seeding must promote; plan a move to `http/config/configure` later |
| `voluptuous` in core | `probatio` (a modern fork) in core; `voluptuous 0.16.0` still installed | HA 2026.x | This integration's `voluptuous` websocket schemas keep working (verified); watch on every HA bump |
| Python 3.12/3.13 | Python 3.14 (core uses `except A, B:`) | HA 2026.10 | Seed tooling and any pip HA need 3.14 (`uv`) |
| Companion trusts only system CAs | Default trust manager + fallback to user-installed CAs | Android 2026.6.5 | Needs app >= that release on her phone |
| Google device-auth credentials | Web-application credentials via `my.home-assistant.io` redirect | HA docs | Use a Web client; app must be published |
| `sidebar` order in localStorage | `frontend/set_user_data` key `sidebar` (`panelOrder`, `hiddenPanels`) | HA frontend 2026.x | Per-user, server-side; the frontend falls back to localStorage only if absent |

**Deprecated/outdated:** the ARCHITECTURE.md compose healthcheck against `/api/onboarding` (404 after onboarding); `track:` in `google_calendars.yaml` (deprecated, imported to the UI).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Android "install CA" menu path and success on her specific phone/OEM (Settings > Security > Encryption & credentials > Install a certificate > CA certificate varies by OEM/version) | Answers D-06, guide | The guide's Android steps are wrong or the app still rejects the CA; mitigated by a real-phone checkpoint and the fallback ladder |
| A2 | Her Companion app version is >= 2026.6.5 | Answers D-06 | User-CA fallback missing; app shows "SSL handshake failed" |
| A3 | HA runs as root in the container so bind-mounted `.storage` is root-owned on Linux Engine | Pitfall 7 | Reset helper container unnecessary (harmless) or, if some other uid, still fine |
| A4 | Docker fails to start a container whose published port is bound to an IP not present on the host | Pitfall 8 | If it works, binding to the reserved IP becomes a cleaner LAN-only option |
| A5 | The HA container image has `curl` (Compose healthcheck) | Pitfall 2 | Use host-side probes only (recommended anyway) |
| A6 | Companion app re-registers cleanly (or needs only a re-login) after Preview's volume is wiped; a stable `core.uuid` helps | Pitfall 10 | Re-adding the server may be needed after each reset |
| A7 | The calendar card renders acceptably without `weather.forecast_home` | Pitfall 14 | A visible error/blank weather row in her UI; create a dummy weather entity or set `weather_entity` |
| A8 | The Pantry card renders usefully with Grocy off | Pattern 4 | Omit it from the dashboard (D-18 lists Recipes/Pantry) |
| A9 | Browser refresh picks up edited card JS in Dev without a HA restart (no `Cache-Control`; ETag present) | DEV-02, Pitfall 15 | DEV-02 needs a "restart or hard-reload" instruction or a Dev cache header |
| A10 | `mobile_app:` in the minimal `configuration.yaml` is sufficient for Companion registration | Pattern 2 | Companion cannot register; add `webhook`/dependencies or `default_config` subset |
| A11 | The `my.home-assistant.io` redirect works to a LAN HTTPS IP with a private CA (the browser doing sign-in must trust it and have the instance URL set in My Home Assistant) | Pattern 5 | Google sign-in cannot complete; sign in via `http://localhost:<dev port>` on the laptop instead |
| A12 | Google's secret iCal address is enabled for the family calendars and is current enough for a safety backup (Google's feed can lag) | D-08 | Backup step must switch to API export; backups could miss very recent edits |
| A13 | Compose `--env-file versions.env` tolerates unused keys | Pattern 1 | Split pin vars into a compose-only env file |
| A14 | Docker Desktop clock-drift mitigation is Docker-side (blog exists) | Pitfall 6 | Only matters if the laptop is macOS/Windows |
| A15 | A theme such as `midnight` renders well in all cards and is visually unmistakable vs Home's likely `slate` | Discretion (theme) | Pick `blossom` (rendering verified in the spike) |
| A16 | Package legitimacy SUS verdicts for `aiohttp`, `PyYAML`, `playwright`, `homeassistant` are data artefacts | Package Legitimacy Audit | Add the human-verify checkpoint (already required) |

## Open Questions

1. **What OS is the developer's laptop, and is it on Wi-Fi or Ethernet?**
   - Known: D-04 says Linux or macOS with Docker Engine/Compose v2; HA says Desktop is unsupported. A DHCP reservation keys on the MAC; Wi-Fi "private/random MAC" modes defeat it.
   - Unclear: actual OS/Docker flavour and interface.
   - Recommendation: plan for Linux Engine; add a `scripts/doctor` that prints Docker flavour, interface, MAC-randomisation hint and clock; mark macOS as best-effort.

2. **Where should seeded `[PREVIEW]`/`[DEV]` events be written, given default reminders buzz subscribers' phones?**
   - Known: HA cannot set reminders on created Google events; default reminders apply. D-11 accepts events appearing on family phones, not necessarily notifications.
   - Unclear: whether the developer wants phones to buzz.
   - Recommendation: add a **dedicated Google calendar** ("Family Hub Preview events") that the seed writes to and that nobody subscribes to on a phone, plus mapping members to the real calendars read-only for display; or schedule seeded events outside reminder windows. Needs the developer's call before planning the Google seed.

3. **Which Google account and Cloud project own the OAuth client, and will it be published?**
   - Known: Web client, redirect `https://my.home-assistant.io/redirect/oauth`, app must be published to avoid the 7-day expiry.
   - Unclear: who creates it; whether the family calendars are visible to one account with writer access.
   - Recommendation: a human-verify checkpoint with exact console steps; record client id/secret paths in `host.env` only.

4. **After `reset-preview`, must she sign in again on her phone?**
   - Known: auth store and `core.uuid` are wiped.
   - Unclear: Android Companion behaviour (A6).
   - Recommendation: checkpoint on her real phone; adopt a stable per-env `core.uuid` if re-adding the server is needed; otherwise document a one-line re-login.

5. **How will `refresh-preview` be scheduled on the laptop?**
   - Recommendation: daily timer plus on-boot; ship the unit/plist as examples and document manual `refresh-preview` as the minimum; reword the success criterion to "at agreed times" (D-03).

6. **Does she want a dark theme?** Recommend Preview `midnight` (dark, unmistakably unlike a light Home) with `blossom` as the verified-rendering alternative; her choice.

7. **Backup method for D-08:** secret iCal URLs (simple, per calendar, stored in `family.local.yaml`) vs Google API export (lossless). Recommend iCal URLs with a non-empty check and a hard stop on failure.

8. **Which HA `configuration.yaml` core fields come from where?** Home does not exist yet; `TZ`, country, currency and units live in `host.env` now and must be reconciled in Phase 4.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker CLI | compose tooling | CLI only: `Docker version 29.9.2`; **daemon not running** (`dial unix /var/run/docker.sock`) | 29.9.2 | Automated tests run against pip-installed HA; Docker steps become human-verify checkpoints on the laptop |
| Python 3.14 via `uv` | seed tool, pip HA | yes (`uv venv --python 3.14` gave CPython 3.14.9) | 3.14.9 | -- |
| System Python | -- | 3.13.17 (too old for HA 2026.10) | 3.13.17 | use `uv` 3.14 |
| Node | not needed this phase | v22.22.0 | -- | -- |
| `openssl` | certs | yes | 3.0.13 | `mkcert` on the laptop |
| `git` | `git archive` deploy | yes | -- | -- |
| Headless Chromium (Playwright) | screenshots | yes after `playwright install chromium` (headless shell 156.0.8078.4) | 1.64.1 | manual phone screenshots |
| ghcr.io registry | image pull | reachable (manifest HTTP 200); image pull itself not attempted | -- | -- |
| PyPI | pip HA, requirements | reachable | -- | -- |
| Google account / OAuth client | D-07 | not available here | -- | Local Calendars (seed default when no Google file) |
| Android phone with Companion | D-06, ACCESS-* | not available here | -- | none: human-verify checkpoint |

**Missing dependencies with no fallback:** her real Android phone (CA trust, one-tap, Companion server, UAT) and the developer's Google Cloud project; both are human-verify checkpoints.
**Missing dependencies with fallback:** Docker daemon (use pip-installed HA for automated tests), Google (Local Calendar provider in the example family file).

## Security Domain

Security enforcement is enabled (`security_enforcement: true`, ASVS level 1, block on high). Validation Architecture is skipped because `workflow.nyquist_validation` is `false` in `.planning/config.json`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | HA accounts; generated per-environment passwords kept in gitignored files; no long-lived tokens (seed uses login flow); distinct passwords from Home; HA `ip_ban_enabled` default true |
| V3 Session Management | yes | HA tokens; seed never stores tokens; her Companion session is wiped by reset (Pitfall 10) |
| V4 Access Control | yes | Her account is non-admin (`system-users`); admin-gated Family Hub commands verified (she can only complete her chore and redeem her own balance); `--target` allow-list and `location_name` check refuse Home |
| V5 Input Validation | yes | Seed validates the family file against a schema; event tag matching is exact (prefix + marker + env + window); websocket schemas are enforced by HA |
| V6 Cryptography | yes | `openssl` CA with name constraints; never hand-roll TLS; keys 0600; HA `ssl_profile` default `modern` [VERIFIED: http config schema]; seed verifies TLS against the CA file, never `verify=False` |
| V8/V9 Data protection & Communications | yes | Preview traffic is HTTPS on the LAN; Google OAuth token treated as a secret (0600, outside git, outside the HA volume) |
| V14 Configuration | yes | Pinned image tag; no `privileged`, no host network; Dev bound to loopback; secrets paths covered by `dev/.ha-*` and `tools/seed/*.local.*` ignores |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Seeding or deleting events on the wrong Google calendar / untagged real events | Tampering | Exact tag + marker + env + date window + calendar allow-list, dry-run default, `.ics` backup before reset, loud delete warning in Dev/Preview only (D-08, D-09, D-11) |
| Google refresh token theft from the laptop (read/write family calendars) | Information disclosure / Tampering | File mode 0600 outside git and the HA volume; full-disk encryption on the laptop; publish the app but use a dedicated Google account or minimum-scope where possible; revoke at myaccount.google.com if lost |
| Preview reachable on hostile Wi-Fi | Spoofing / Elevation | Dev loopback bind; Preview down script; strong passwords; no port-forward; (optional) host firewall limiting 8124 to the home subnet |
| Name-constrained CA key compromise | Spoofing | Constraint to private ranges + localhost; key 0600, kept only on the laptop; `ca.crt` only on the phone |
| Seeder pointed at Home with real credentials | Tampering / Information disclosure | `--target dev|preview` allow-list, host allow-list, `location_name` assertion before auth, separate passwords |
| Real notification to a family phone from Preview | Repudiation / DoS | `notifyTargets` allow-list check on every deploy/reset/refresh; no `media_player`; discovery integrations omitted |
| Secrets/family names committed to the public fork | Information disclosure | `.gitignore` for local family file, env files, certs, backups, preserved entry; invented names in the example file; guide screenshots from seeded data only |

## Sources

### Primary (HIGH confidence)
- Real HA Core 2026.10.4 (`uv pip install homeassistant==2026.10.4`, Python 3.14.9) run with this repo's integration: onboarding, user creation, Local Calendar/To-do flows, Family Hub flow, dashboards, resources, `application_credentials`, `http/config`, user data, entity/service behaviour, headless Chromium render. Source files read from the installed package: `components/onboarding/views.py`, `const.py`; `components/http/config.py`, `websocket_api.py`; `components/lovelace/websocket.py`, `resources.py`, `const.py`; `components/application_credentials/__init__.py`; `components/google/__init__.py`, `config_flow.py`, `calendar.py`, `const.py`, `manifest.json`; `components/calendar/__init__.py`; `helpers/config_entry_oauth2_flow.py`; `bootstrap.py`; `components/default_config/manifest.json`; `components/websocket_api/commands.py`; `hass_frontend` 20260930.5 bundle (`sidebar`, `default_panel`).
- This repository (Read this session): `config_flow.py` 1-780, `chores_websocket_api.py` 60-2300 (permission gates, kiosk, rewards, chores, routines, goals), `__init__.py` (settings, notify profiles, delete support, dashboard resource registration, setup), `const.py` (excerpts), `store.py`, `DOCUMENTATION.md` 540-755, `card/family-week-calendar-card.js` delete flow and clipboard code, `versions.env`, `hacs.json`, `manifest.json`, `.gitignore`.
- ghcr.io registry API: `home-assistant/home-assistant:2026.10.4` manifest HTTP 200.
- OpenSSL 3.0.13: name-constrained CA, leaf verify and negative test run locally; HA served HTTPS with it.
- https://www.home-assistant.io/integrations/google/ (Web credentials, redirect URI, publish app, 7-day expiry)
- https://developers.google.com/identity/protocols/oauth2#expiration (Testing = 7 days; 6-month inactivity; 100 tokens per client)
- https://www.home-assistant.io/installation/linux (Engine >= 23.0.0, "Docker Desktop will not work", compose example)
- https://docs.docker.com/engine/containers/start-containers-automatically/ and https://docs.docker.com/engine/network/port-publishing/

### Secondary (MEDIUM confidence)
- https://github.com/home-assistant/android/pull/7044 (default TrustManager + user-installed CA fallback, merged 2026-06-18) and release 2026.6.5 notes
- https://github.com/home-assistant/android/issues/5565 (user-CA failures on e-OS/LineageOS, maintainer position, name-constrained CA workaround, 180-day vs 10-year anecdote)
- https://companion.home-assistant.io/docs/troubleshooting/faqs (self-signed certificate FAQ, multi-server sensor note) and Android docs for adding a server (Settings > Companion app)
- https://support.google.com/calendar/answer/37648 (secret address in iCal format)
- https://www.docker.com/blog/addressing-time-drift-in-docker-desktop-for-mac/ and forum reports of clock drift after sleep

### Tertiary (LOW confidence)
- Community report of Companion "failed to perform ssl handshake" in June 2026 (https://community.home-assistant.io/t/companion-app-home-assistant-companion-app-failed-to-perform-ssl-handshake-but-works-from-browser/1013695), unresolved in the thread.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH for HA/Python/aiohttp (installed and run); MEDIUM for Docker flavour on the unknown laptop.
- Architecture (seed order, dashboard, sidebar, HTTP promote, Google entry preservation): HIGH, executed against the pinned HA.
- Pitfalls: HIGH for items reproduced here (HTTP revert, readiness 404, auth failure without credential, theme-builder panel id, non-admin subscriptions); MEDIUM/LOW for Docker, Android, Google behaviour.

**Research date:** 2026-10-28
**Valid until:** 2026-11-11 (14 days: HA ships monthly and the 2026.10 `http`/`probatio` migrations are moving; Android Companion trust handling changed in June 2026). Re-verify when `HA_VERSION` changes.
