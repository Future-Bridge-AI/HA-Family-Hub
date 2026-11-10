# Phase 2: Dev + Family Preview - Research

**Researched:** 2026-11-02 (refresh of the 2026-10-28 research, after CONTEXT.md D-23..D-31 were added)
**Domain:** Docker Compose HA environments (Dev + Preview) on a Windows 11 laptop via WSL2 + Docker Engine, API-driven seeding through public HA APIs, deploy/reset/refresh tooling, Google Calendar (read/write) in a non-production instance, local-CA HTTPS for an Android Companion client
**Confidence:** MEDIUM-HIGH. HA-side mechanics (onboarding, users, config flow, dashboard, sidebar, HTTP promote, Google entry preservation, resource update) are HIGH: executed against a real HA Core 2026.10.4 on 2026-10-28 and spot re-run in this session. The Windows/WSL2 host layer, Android CA trust and real Google token behaviour are MEDIUM/LOW: documentation and issue-tracker evidence only, no Windows machine, phone or Google account in this sandbox.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Scope changes agreed in discuss-phase (the planner must reflect them; see D-03, D-07):**
- Preview runs on the developer's laptop for now, so "always-on" becomes "available whenever the laptop is on at home".
- Dev and Preview **connect read/write to a chosen list of the family's real Google calendars**. This overrides the earlier rule "Preview never connects to the real family calendars" (PREV-03's calendar clause, the PROJECT.md/REQUIREMENTS.md out-of-scope row "Real family calendars or data in Preview", and ROADMAP Phase 2 success criterion 2's "or touches the real family calendars"). The notification/speaker isolation half of PREV-03 is unchanged.

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

#### Answers to the research open questions (02-RESEARCH.md §Open Questions, answered 2026-11-02)
- **D-23:** The laptop runs **Windows**. Dev and Preview run in **WSL2 (Ubuntu) with Docker Engine installed inside WSL2**, not Docker Desktop (HA does not support Desktop). Her phone reaches Preview through **WSL mirrored networking** (Windows 11 22H2+), with a Windows Firewall rule for 8124. This refines D-04: tooling stays Linux-shell and host-agnostic; Windows/WSL2 is the primary host. Research did not test Windows/WSL2: the planner adds `scripts/doctor` checks (WSL version, mirrored mode, Engine not Desktop, clock) and a human-verify checkpoint on the laptop. `restart: unless-stopped` only helps once WSL and Docker are running, so start-on-login for WSL/Docker must be covered.
- **D-24:** The laptop is on **Wi-Fi**. The guide/doctor tells the developer to turn off Windows "random hardware addresses" for the home network so the D-05 router reservation holds.
- **D-25:** Seeded `[PREVIEW]`/`[DEV]` events go onto the **real family calendars** (as D-11), and the developer **accepts that family phones may buzz** from Google default reminders. No dedicated seed calendar.
- **D-26:** The **developer's own Google account** owns the Google Cloud project and OAuth client, and the OAuth app is **published** (avoids the 7-day refresh-token expiry that would break D-10).
- **D-27:** Having to **sign in again on Preview after each `reset-preview`** is acceptable. The guide documents the re-login; test on her phone what exactly happens (re-login vs re-adding the server).
- **D-28:** `refresh-preview` runs on a **daily schedule plus at laptop start-up**, and manually. Reword ROADMAP success criterion 2 "whenever she opens Preview" to "at agreed times" (with D-03).
- **D-29:** Preview uses the **`midnight`** built-in theme.
- **D-30:** D-08 backups use each calendar's **secret iCal address**, stored in the gitignored family file, with a non-empty check and a hard stop on failure.
- **D-31:** HA core settings (time zone, country, currency, units) for Dev and Preview come from the **gitignored host env file**; reconcile with Home in Phase 4.

### Claude's Discretion
- Exact `[PREVIEW]`/`[DEV]` tag wording and the local family-file schema/path.
- Which distinct built-in theme Preview uses. (Now fixed by D-29: `midnight`.)
- Certificate tooling (mkcert-style local CA vs self-signed), as long as D-06 holds.
- Mechanism for the Dev/Preview-only delete warning (D-09).
- Layout of `dev/`, `tools/seed/`, `scripts/` (research suggests `dev/compose*.yaml`, `tools/seed/`, thin `scripts/` wrappers).

### Deferred Ideas (OUT OF SCOPE)
- Moving Preview to dedicated always-on hardware (restores true always-on): later, once hardware is chosen.
- Home hardware choice (HA Green / mini PC / other): Phase 4.
- Wall-tablet bookmark/kiosk access: already v2 (ENVX-02).
- Publishing the family guide on the Docusaurus site: later.
- PREVIEW banner strip: not wanted now; reconsider if she confuses Preview with Home.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEV-01 | One-command Dev HA (Compose, pinned image, own port, integration mounted live) | Compose base + overlay (rendered and checked with `docker compose config` this session); image `2026.10.4`; Dev on `127.0.0.1:8130`; `:ro` bind mount + `PYTHONDONTWRITEBYTECODE=1`; WSL ext4 repo location |
| DEV-02 | Python changes after HA restart, card JS after browser refresh, no copying | **Soft reload does NOT reliably pick up edited card JS** (reproduced in Chromium, Pitfall 12); fix = `dev-cards` helper that rewrites the `?v=` hash through `lovelace/resources/update` (verified), plus hard-reload fallback |
| DEV-03 | Dev seeded from the same tool, resettable incl. `family_hub_backups/` | Same `tools/seed` entry point; reset = stop, wipe via helper container, re-seed; Google entry preserved per env |
| PREV-01 | Reachable at a stable address, separate instance sharing nothing with Home | D-01/D-05/D-23; bridge networking; own identity; WSL mirrored networking + Hyper-V firewall rule (NOT only a Defender rule); reworded for "whenever laptop is on" (D-03) |
| PREV-02 | Distinct name, theme, server entry | `config/core/update` `location_name` (verified); theme `midnight` (verified in `__init__.py:405`, default is `slate`) |
| PREV-03 | Nothing reaches the real world (notifications); calendar clause rewritten per D-07 | Notification opt-in model + allow-list verify; Google guardrails D-08..D-11; week-anchored diff sync limits churn on real calendars |
| PREV-04 | Realistic current week, date-relative, never stale | Seed commands verified; `refresh-preview` (D-28) via Windows Task Scheduler; week-anchored keys |
| PREV-05 | `deploy-preview <branch>` restarts and verifies served cards | `git archive`, stamp substitution, restart, host-side readiness, served-hash check |
| PREV-06 | `reset-preview` clears everything incl. backups | Whole-volume wipe via helper container; Google entry preservation; HTTP promote step; her stable credentials (D-27) |
| PREV-07 | Visible build stamp | Placeholder substitution in the exported copy only (Pattern 6) |
| PREV-08 | Dashboard + resources created and verified automatically | `lovelace/dashboards/create` + `lovelace/config/save`; integration's own resource registration verified; read-back assertion |
| ACCESS-01 | Her non-admin account sees only Family Hub | `frontend/set_user_data` `sidebar` as her token; `theme-builder` panel id must be hidden too |
| ACCESS-02 | One tap from phone | Companion second server (D-16); CA trust evidence and fallback ladder |
| ACCESS-03 | Plain-language guide in `docs/family/` with screenshots | Headless Chromium recipe (token injection); real-phone screenshots only for Android install screens |
| ACCESS-04 | She ticks a chore and redeems a reward unaided | Verified as non-admin (2026-10-28) |
| ACCESS-05 | She confirms one trivial deployed change | Build stamp + deploy flow; first change is D-22 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Extracted from `/home/user/HA-Family-Hub/.claude/CLAUDE.md` (same authority as locked decisions):

- **License:** GPLv3 derivative; keep upstream credit.
- **Platform:** HA custom integration, HA >= 2024.12.0 declared (`hacs.json`); Dev, Preview and tests pinned to 2026.10.4 in `versions.env`.
- **Tech stack:** Python on HA Core APIs, no extra Python deps in the integration; vanilla JS web components, no bundler.
- **Locality:** everything runs locally, no cloud services (Phase 2 exception: Google Calendar API, D-07).
- **Safety:** Preview isolated from the family's real HA; experiments never break the real setup.
- **Usability:** acceptance criteria and UAT are things she does and sees; she is non-technical.
- **Code health:** changes to `__init__.py` or the calendar card prefer extracting focused modules; no tests exist yet. Keep the D-09 and D-20 card changes tiny and additive.
- **Served paths:** only `card/` and `panel/` JS is served; edit those copies only.
- **Conventions:** double quotes; `from __future__ import annotations` first in Python modules; `_LOGGER` with `%s` lazy formatting; no `print()` in integration code (seed tooling under `tools/` is not integration code); no debug `console.log` in cards (`console.info` for the stamp is decided in D-20); no `.bak_*` files; new backend constants in `const.py`; new websocket commands in the matching `*_websocket_api.py` `ALL_COMMANDS`.
- **GSD workflow:** file changes go through a GSD command.
- **Project skills:** none (`.claude/skills/`, `.agents/skills/` absent).

## Summary

The HA-side half of this phase is feasible with public HA APIs only. On 2026-10-28 a real HA Core 2026.10.4 was started with this repository's integration and a script onboarded it, created her non-admin account and kid accounts, created Local Calendar/To-do entries, drove the 11-step Family Hub config flow (including the `member_profile` loop), created a storage-mode dashboard, hid every panel except Family Hub for her and rendered her dashboard in headless Chromium. In this session the key mechanics were spot re-run on the same version: onboarding (4 steps), `mobile_app` registration (201 with the minimal `mobile_app:` + `my:` config), `lovelace/resources/create|update` (works, key `resource_id`), `config/core/update` (location name), and the pending-HTTP behaviour (`active_config_type: "pending"` with a `revert_at` timestamp for **any** `http:` YAML, even just a port).

**What changed since the 2026-10-28 research (CONTEXT D-23..D-31):**

| Decision | Effect on this research |
|----------|-------------------------|
| D-23 Windows + WSL2 + Docker Engine + mirrored networking | New host-layer section. Material new risks: the required firewall rule is a **Hyper-V firewall** rule (VMCreatorId GUID quoted below), not only a Defender rule; WSL distros shut down despite systemd (open WSL regression), so a **Windows-side keep-alive scheduled task** is required; 2026 WSL builds (2.9.x) have a reported mirrored-mode Docker bind regression; line endings and filesystem location (WSL ext4, never `/mnt/c`) become plan requirements. Needs a laptop checkpoint with a fallback ladder. |
| D-24 Wi-Fi | `scripts/doctor` + guide step for random hardware addresses; DHCP reservation keys on the Wi-Fi adapter MAC, which mirrored mode shares with WSL. |
| D-25 events on the real calendars, buzz accepted | Closes old Open Question 2 (no dedicated calendar). Added a **week-anchored, diff-based sync** recommendation so daily refreshes do not delete/re-create events every morning (which would buzz family phones daily). |
| D-26 developer's own Google account, app published | Consistent with the verified 7-day rule; re-checked against HA docs and Google OAuth docs today. Closes old Open Question 3. |
| D-27 re-login after reset acceptable | Closes old Open Question 4 as a decision. Recommend seeding **her same username/password** (generated once, kept in `dev/.ha-secrets/`) so the guide's re-login line is literally "sign in with your usual details". Pinning `core.uuid` is dropped as default (still a fallback). |
| D-28 daily + at start-up refresh | Windows Task Scheduler is the scheduler (WSL is not always running); closes old Open Question 5. |
| D-29 `midnight` theme | Verified the id exists and differs from the default `slate`. Closes old assumption A15 and Open Question 6. |
| D-30 secret iCal address | Closes old Open Question 7. Added caveats: Google documents no refresh interval for the feed; only calendars you own expose it (unverified). Optional supplement: a fresh HA-API JSON snapshot. |
| D-31 core settings from host env | `config/core/update` accepts `country, currency, elevation, language, latitude, longitude, time_zone, unit_system, internal_url` (verified). Closes old Open Question 8. |

**Primary recommendation:** Build `tools/seed/` as a small `aiohttp` client over HA's public APIs (steps verified below), driven by thin bash `scripts/*`, targeting `https://127.0.0.1:<port>` from inside WSL; test the D-11 tag matcher as a pure function plus once against a Local Calendar in a pip-installed HA 2026.10.4; and make the Windows/WSL2 host layer, Google OAuth and her Android phone explicit human-verify checkpoints with written fallbacks.

## Answers to the Questions CONTEXT and ROADMAP Assign to Research

| Question | Answer | Confidence |
|----------|--------|------------|
| **D-10**: how HA stores app credentials and the OAuth token; is preserving only those safe? | Credentials: `.storage/application_credentials` (id derived from the client id; fields `domain, client_id, client_secret, name`). Token: inside the Google config entry in `.storage/core.config_entries` (`data.token`, `data.auth_implementation`), entry `unique_id` = the account's primary calendar id. Preserving **only the Google entry** is feasible: pre-write a `core.config_entries` holding just that entry into the empty volume (`{"version": 1, "minor_version": 5, "key": "core.config_entries", "data": {"entries": [...]}}`; version/minor_version re-read from a live file this session), start HA, create the credential via WS `application_credentials/create`, reload the entry, state becomes `loaded`. Without the credential the entry goes to `setup_error`. Fallback: one-time UI re-sign-in. Prerequisite: app published (D-26). | HIGH (mechanics, 2026-10-28 execution with a fake token), MEDIUM (real Google token) |
| **D-06**: does Android Companion accept a user-installed CA? | Yes since PR #7044 (merged 2026-06-18, "Use default Trust manager and fallback to user installed CA"); first fixed in app release 2026.6.5. **Open caveat:** issue #7346 (opened 2026-08-18, still open) reports "Trust anchor for certification path not found" on app 2026.6.5 when the server sends only a leaf signed by an **intermediate** of a custom root. Our design therefore uses a single **root** CA signing the leaf directly (no intermediate) and serves leaf + CA in the PEM. Fallbacks if the phone still rejects: Chrome "Add to Home screen"; a publicly trusted certificate on a domain you own; Tailscale HTTPS (deferred); plain HTTP only as an explicit decision. | MEDIUM |
| **D-04/D-23**: Docker-on-laptop specifics | Windows 11 22H2+ + WSL2 + Docker Engine in the distro. Mirrored mode shares the Windows IP with WSL (MS docs), so the Wi-Fi reservation applies. Inbound LAN access needs a Hyper-V firewall rule; Docker published ports in mirrored mode work for LAN clients in reports but are version-sensitive (Pitfalls 4-5). Sleep pauses everything (D-03). | MEDIUM-LOW |
| Dashboard + resource creation path | Storage-mode: WS `lovelace/dashboards/create` then `lovelace/config/save`. The integration's own best-effort resource registration worked on 2026.10.4 (13 card resources); the seed reads them back and asserts, falling back to `lovelace/resources/create`. | HIGH |
| Which `family_hub/*` commands seed data without a kiosk session | An admin token suffices: `chores/create`, `rewards/add_catalog_item`, `rewards/adjust_balance`, `goals/create`, `routines/create`, `kiosk/set_pin` (admin only), `get_settings`/`set_settings`, `set_recipes`, `permissions/set` (executed 2026-10-28; schemas re-read today). Meals are `todo.add_item` on `todo.meal_plan`. | HIGH |
| Driving the 11-step config flow | Step order and field names below (field constants re-verified by grep today). | HIGH |
| Non-admin dashboard and sidebar | Create the dashboard (non-admin visible), log in **as her** (login flow) and call `frontend/set_user_data` key `sidebar` with `hiddenPanels` computed from her `get_panels`. | HIGH |
| HTTPS secure-context differences | Only the clipboard fallback in the calendar card is secure-context sensitive (Pitfall 14). | HIGH |
| Preview host + Companion second server | D-01/D-23; multi-server is an official Android feature; each server gets its own `mobile_app` device (verified registration works). | MEDIUM |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Run HA instances (Dev/Preview) | WSL2 Docker Engine | Compose base + overlay | No shared volume, own identity |
| Make Preview reachable from her phone | Windows host (mirrored networking, Hyper-V firewall rule, DHCP reservation) | Router | Phone talks to the laptop's Wi-Fi IP |
| Keep WSL/Docker running and schedule refresh | Windows Task Scheduler | systemd inside WSL (Docker only) | WSL is not reliably always running (Pitfall 5) |
| TLS termination | HA Core `http` in-container | Cert files bind-mounted ro | Simplest; no reverse proxy |
| Bootstrapping users/entries/dashboard | Seed tool (in WSL, public HA APIs) | -- | Never write `.storage` of a running HA |
| Family data | Family Hub backend via its own commands | Seed tool | No new backend code needed |
| Meals, to-do lists, local calendars | HA built-ins | Seed tool | Meals live in `todo.meal_plan` descriptions |
| Real family calendars | HA Google Calendar integration | Seed tool (tag + disable non-chosen entities) | Read/write per D-07 |
| Google sign-in persistence | Seed tool + host secrets dir (0600) | HA `application_credentials` | Only the config entry JSON is preserved |
| Calendar `.ics` backups | Host script | Google secret iCal address | Outside the HA volume (D-08) |
| Build stamp + deploy | `deploy-preview` (host) | Card placeholder constants | Stamp substituted into the deployed copy only |
| Delete-event warning (D-09) | Calendar card (browser) | `family_hub/calendar/delete_support` | Tiny additive card change |
| Her sidebar/default dashboard | HA frontend user data (her token) | Seed tool login flow | Per-user, cannot be set from an admin token |
| Guide + screenshots | Static Markdown `docs/family/` | Headless Chromium against seeded Dev | Android install screens need her real phone |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Home Assistant container `ghcr.io/home-assistant/home-assistant` | `2026.10.4` (manifest HTTP 200 on ghcr.io, 2026-10-28) | Dev + Preview runtime | Pinned in `versions.env` (`HA_VERSION=2026.10.4`) |
| Docker Engine + Compose v2 inside WSL2 Ubuntu | Engine >= 23.0.0 [CITED: home-assistant.io/installation/linux]; Compose 5.6.1 rendered the planned files in this sandbox | Run containers | HA docs: Docker Desktop is unsupported (D-23) |
| WSL2 with systemd | `[boot] systemd=true` in `/etc/wsl.conf` [CITED: learn.microsoft.com/windows/wsl/wsl-config] | Start dockerd with the distro | Documented key |
| Python | 3.14 via `uv` (CPython 3.14.9 used) | pip-installed HA for tests; seed tool | `versions.env` `PYTHON_VERSION=3.14` |
| `aiohttp` | 3.14.5 | Seed REST + WebSocket client | Already a dependency of the pinned HA |
| `PyYAML` | 6.0.3 | Read `family.local.yaml` | HA dependency |
| `openssl` | 3.x | Name-constrained local CA + leaf | No mkcert dependency |
| `playwright` (Python) | 1.64.1 (installed and launched Chromium in this sandbox) | Guide screenshots (Phase 3 TEST-05 later) | Matches Phase 3 stack |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `homeassistant` (pip) | 2026.10.4 | Automated seed-tool tests without Docker | The D-11 live test; same venv Phase 3 will use |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Name-constrained `openssl` root CA | `mkcert` | mkcert's CA is unconstrained; fine for the laptop browser only. Either satisfies D-06 |
| `http:` YAML + `http/config/promote` | `http/config/configure` WS | YAML import is deprecated (`breaks_in_ha_version 2027.2.0`); plan the move on the next HA bump |
| Bind-mounted config dir | Named Docker volume | Bind mount keeps host tooling simple and matches Phase 1 D-10 (`dev/.ha-*`) |
| WSL mirrored networking | NAT + `netsh interface portproxy` | NAT is the WSL default and avoids mirrored-mode Docker regressions, but the WSL VM IP changes per start so the proxy must be re-created by a boot task (fallback only) |
| Secret iCal address for backups (D-30, locked) | HA API JSON snapshot | Fresh and available for any readable calendar; not ICS. Add as a supplement, not a replacement |

**Installation (seed tool environment, inside WSL):**
```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python "aiohttp==3.14.5" "PyYAML==6.0.3"        # seed tool
uv pip install --python .venv/bin/python "homeassistant==2026.10.4"               # only for the live D-11 test
uv pip install --python .venv/bin/python playwright && .venv/bin/python -m playwright install chromium   # screenshots only
```

**Version verification:** `aiohttp 3.14.5`, `PyYAML 6.0.3` read from the HA venv this session; `playwright 1.64.1` installed from PyPI this session; `homeassistant 2026.10.4` is the venv at `~/.cache/fh-hassfest/venv` (`homeassistant.const.__version__` printed `2026.10.4`).

## Package Legitimacy Audit

`gsd-tools query package-legitimacy check --ecosystem pypi aiohttp pyyaml playwright homeassistant` was re-run this session and again returned **SUS for all four**, for data-artefact reasons: `unknown-downloads` (PyPI exposes no download counts), `too-new` (the latest release is days old: aiohttp 2026-10-11, playwright 2026-10-22, homeassistant 2026-10-24) and `no-repository` for playwright. All are long-established projects; aiohttp and PyYAML arrive transitively with the pinned `homeassistant`.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| aiohttp | PyPI | long-established (aio-libs) | unavailable | github.com/aio-libs/aiohttp | SUS (too-new, unknown-downloads) | Flagged: planner adds one `checkpoint:human-verify` for the seed environment install |
| PyYAML | PyPI | long-established | unavailable | pyyaml.org | SUS (unknown-downloads) | Flagged: same single checkpoint |
| playwright | PyPI | Microsoft project | unavailable | none in PyPI metadata | SUS (too-new, unknown-downloads, no-repository) | Flagged: optional (screenshots); `checkpoint:human-verify` before installing |
| homeassistant | PyPI | long-established | unavailable | home-assistant.io | SUS (too-new, unknown-downloads) | Flagged: test venv only; same checkpoint |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** aiohttp, PyYAML, playwright, homeassistant (one `checkpoint:human-verify` covering the seed environment before first install).

*Names came from the project's STACK.md and the pinned HA dependency set. They are installed from PyPI but remain `[ASSUMED]` for gating because the seam did not return OK. No npm packages are introduced in this phase.*

## Architecture Patterns

### System Architecture Diagram

```
 phone (Android, Companion)                         laptop (Windows 11, Wi-Fi, DHCP-reserved IP)
   |  https://<reserved-ip>:8124                      |
   v                                                  v
 router --------------------------> Windows host: Hyper-V firewall rule (TCP 8124, WSL creator GUID)
                                      |  WSL2 mirrored networking (VM shares the host IP)
                                      v
              +-------------------- WSL2 Ubuntu (systemd, dockerd, repo on ext4: ~/HA-Family-Hub) ----------------+
              |  versions.env + dev/host.env (gitignored: TZ, country, currency, units, lat/long, PREVIEW_HOST_IP)  |
              |                                                                                                       |
              |  scripts/dev-up | dev-reset | deploy-preview <branch> | reset-preview | refresh-preview | doctor      |
              |     (1) .ics backup of every connected Google calendar  -> dev/.ha-backups/<date>/ (hard stop)       |
              |     (2) compose down; wipe volume via helper container (keep custom_components/)                     |
              |     (3) write .storage/core.config_entries with ONLY the preserved Google entry (if any)             |
              |     (4) deploy: git archive <branch> -> stamp substitution -> replace custom_components/family_hub   |
              |     (5) compose up -d; poll host-side until state RUNNING                                            |
              |                                                                                                       |
              |   DEV  127.0.0.1:8130 (working copy :ro)        PREVIEW  0.0.0.0:8124 (exported copy)               |
              |        ^                                              ^                                              |
              |        +----- tools/seed (aiohttp, https://127.0.0.1:<port>, --target dev|preview allow-list) ------+|
              |   a. RUNNING  b. onboard (4 steps)  c. http/config/promote  d. delete outbound onboarding entries    |
              |   e. config/core/update (host.env)  f. users (stable creds)  g. local calendars/todos + Google entry |
              |   h. Family Hub config flow  i. family_hub/* data + todo.add_item + tagged events (diff sync)        |
              |   j. dashboard + resources read-back  k. her sidebar/default  l. verify (isolation, hash, name)       |
              +----------------------------------------------------------------------------------------------------+
                         |                                                    ^
                         v                                                    |
              Google Calendar API (read/write, tagged "[DEV] ..."/"[PREVIEW] ...")      Windows Task Scheduler:
                                                                                         keep-alive (wsl.exe -e sleep infinity),
                                                                                         refresh at logon + daily
```

### Recommended Project Structure
```
dev/
├── compose.yaml                 # base: image ghcr.io/home-assistant/home-assistant:${HA_VERSION:?}, TZ, PYTHONDONTWRITEBYTECODE=1, stop_grace_period: 60s
├── compose.dev.yaml             # 127.0.0.1:8130:8123, ../custom_components/family_hub:/config/custom_components/family_hub:ro
├── compose.preview.yaml         # ${PREVIEW_BIND:-0.0.0.0}:8124:8123, restart: unless-stopped, no source bind-mount
├── config-template/configuration.yaml
├── host.env.example             # committed; copy to dev/host.env (gitignored; add `dev/host.env` to .gitignore)
└── .ha-dev/ .ha-preview/ .ha-certs/ .ha-secrets/ .ha-backups/     # all covered by the existing `dev/.ha-*` ignore
tools/seed/
├── client.py  onboard.py  users.py  entries.py  family_hub.py  google.py  calendar_tags.py  dashboard.py  verify.py  cli.py
├── data/family.example.yaml     # invented family, same schema as the local file
├── tests/                       # pure-function tests for calendar_tags + one live test against Local Calendar
└── family.local.yaml            # gitignored (add `tools/seed/*.local.*`)
scripts/                         # thin bash wrappers: dev-up dev-reset deploy-preview reset-preview refresh-preview make-certs doctor preview-down
docs/family/                     # getting-started.md + img/
.gitattributes                   # NEW: `*.sh text eol=lf`, `scripts/* text eol=lf`, `*.yaml text eol=lf` (Pitfall 8)
```

Suggested plan slicing for the planner (waves): (1) wording changes to ROADMAP/PROJECT/REQUIREMENTS per D-03/D-07/D-28, `.gitignore`/`.gitattributes`, `host.env.example`, `scripts/doctor`; (2) certs + compose + `dev-up` (DEV-01/02); (3) seed core: onboard, users, entries, Family Hub flow and data, dashboard, sidebar, verify; (4) Google: credential create, entry preservation, calendar disable set, backups, tagged-event sync with dry-run and tests; (5) `deploy-preview` / `reset-preview` / `refresh-preview`; (6) card changes (stamp, delete warning) in `card/family-week-calendar-card.js`; (7) human-verify checkpoint on the laptop (WSL host layer, Pitfalls 4-6); (8) Google Cloud project checkpoint; (9) guide + screenshots; (10) her phone checkpoint and ACCESS-05.

### Pattern 1: Compose base + per-environment overlay
**What:** One base file; overlays add mounts, port and restart policy; bridge networking, no `privileged`, no `network_mode: host`.
**Verified this session:** the planned files rendered correctly with `docker compose -p familyhub-preview --env-file versions.env --env-file host.env -f compose.yaml -f compose.preview.yaml config`; the unused keys in `versions.env` (`PYTHON_VERSION`, `PYTEST_HACC_VERSION`) are tolerated (resolved old A13). Relative paths in overlays resolve against the first `-f` file's directory.
```yaml
# dev/compose.yaml (sketch)
services:
  ha:
    image: ghcr.io/home-assistant/home-assistant:${HA_VERSION:?set in versions.env}
    environment: { TZ: "${TZ:?}", PYTHONDONTWRITEBYTECODE: "1" }
    stop_grace_period: 60s
    volumes:
      - ${HA_CONFIG_DIR:?}:/config
      - ./.ha-certs:/ssl:ro
# dev/compose.preview.yaml
services:
  ha:
    restart: unless-stopped
    ports: ["${PREVIEW_BIND:-0.0.0.0}:8124:8123"]
# dev/compose.dev.yaml
services:
  ha:
    ports: ["127.0.0.1:8130:8123"]
    volumes: ["../custom_components/family_hub:/config/custom_components/family_hub:ro"]
```
Start with `docker compose -p familyhub-preview --env-file versions.env --env-file dev/host.env -f dev/compose.yaml -f dev/compose.preview.yaml up -d`. Dev uses project `familyhub-dev` and `dev/compose.dev.yaml`.

### Pattern 2: Minimal `configuration.yaml` (not `default_config:`)
`default_config` pulls `bluetooth, cloud, dhcp, ssdp, usb, zeroconf, go2rtc, stream, assist_pipeline, conversation, homeassistant_alerts` and more (read from `default_config/manifest.json` this session) which do not belong in an isolated Preview. Use:
```yaml
homeassistant:
  name: "Family Hub PREVIEW"          # Dev: "Family Hub DEV"; also asserted via config/core/update
frontend:
lovelace:
config:
my:                                   # REQUIRED for the Google OAuth redirect (see below)
mobile_app:                           # verified this session: 201 registration; deps are http, intent, person, tag, webhook, websocket_api (cloud is only after_dependencies)
http:
  ssl_certificate: /ssl/fullchain.pem
  ssl_key: /ssl/privkey.pem
```
Core values (time zone, country, currency, units, lat/long, elevation, language, internal_url) come from `dev/host.env` (D-31) and are applied through WS `config/core/update` (accepted keys re-read today: `country, currency, elevation, external_url, internal_url, language, latitude, location_name, longitude, radius, time_zone, update_units, unit_system`). Do not put `server_port` in the `http:` block: the container maps the port and any `http:` YAML becomes a pending config (Pitfall 1). `my:` is needed because the OAuth redirect resolves to `https://my.home-assistant.io/redirect/oauth` only when `my` is loaded (`helpers/config_entry_oauth2_flow.py`, read 2026-10-28).

### Pattern 3: API-driven seed, in this order (executed against HA 2026.10.4)
1. **Wait for RUNNING** with a host-side probe: login, `GET /api/config` or WS `get_config`, require `state == "RUNNING"`. Do not poll `/api/onboarding` (it returns the finished-steps list or 404 once onboarded; this session it returned `[{"step":"user","done":true},...]`, so it never signals readiness). Calling too early gave `state NOT_RUNNING` and a 404 on `/api/mobile_app/registrations` this session.
2. **Onboard** a pristine volume: `POST /api/onboarding/users` `{client_id, name, username, password, language}` -> `auth_code`; `POST /auth/token`; then `core_config`, `analytics` (`{}`), `integration` (`{client_id, redirect_uri}` with the redirect starting with `client_id`). All four steps return 200 (re-run this session).
3. **`http/config/promote`** (admin WS) within 5 minutes of start; assert `active_config_type == "stable"` and `revert_at == null`.
4. **Delete unwanted onboarding side effects:** finishing `core_config` auto-adds `shopping_list`, `radio_browser`, `google_translate` (this session's entries list: `shopping_list, radio_browser, google_translate, analytics, backup, mobile_app`). Delete `radio_browser` and `google_translate` (outbound) via `DELETE /api/config/config_entries/entry/<id>`; `met` appears when location is set, delete it too.
5. **Core config** from `host.env` via `config/core/update`; set `location_name` to the environment name.
6. **Users:** WS `config/auth/create` `{name, group_ids: ["system-users"], local_only: false}` then `config/auth_provider/homeassistant/create` `{user_id, username, password}`. Admin = the onboarding user. **Credentials are generated once per environment into `dev/.ha-secrets/credentials-<env>.json` (0600) and reused on every reset**, so her re-login after a reset (D-27) uses the same username and password.
7. **Local To-do (five lists) and, when no Google file exists, Local Calendars** via `POST /api/config/config_entries/flow` `{handler: "local_todo"}` / `{handler: "local_calendar"}`. Create **all five** lists the cards ask for: `todo.recipe_box`, `todo.meal_plan`, `todo.meal_plan_templates`, `todo.meal_suggestions`, `todo.family_reminders`.
8. **Google entry** (Pattern 5).
9. **Family Hub config flow** (below), answering `add_dashboard: false`.
10. **Family Hub data** via commands, meals via `todo.add_item`, events via `calendar.create_event`.
11. **Theme (D-29):** `family_hub/get_settings`, set `globalThemeId` to `midnight` (and keep `useGlobalTheme` true), `family_hub/set_settings` (full replace: always GET, modify, SET). `__init__.py:405` has `_theme(` with `"midnight", "Midnight",` as its first two arguments; the default written at install is `DEFAULT_GLOBAL_THEME_ID = "slate"` (`__init__.py:1571`) and the card default `useGlobalTheme: true` (`card/family-week-calendar-card.js:9378`). **Dev should use a different theme than both** (suggest `blossom`, rendering verified in the 2026-10-28 spike) so Dev, Preview and Home are visually distinct.
12. **Dashboard** (Pattern 4), **her sidebar/default** (Pattern 7), **verify** (Pattern 8).

**Family Hub config flow, verbatim values** (re-verified by grep this session): `_FEATURES_FIELD = "setup_features"` (`config_flow.py:158`), `_FEATURE_CHORES = "chores"` (:148); pick only `["chores"]` to skip Grocy and Digest steps. `CONF_INITIAL_MEMBER_USER_IDS = "initial_member_user_ids"` (`const.py:843`). Member profile (one form per member, loop): `_MEMBER_COLOR_FIELD = "member_color"` (:234), `_MEMBER_INCLUDE_FIELD = "member_include_in_chores"` (:235), `_MEMBER_CALENDAR_FIELD = "member_calendar"` (:238). Chores features: `_ROUTINES_FIELD = "routines_enabled"`, `_GOALS_IN_CHORES_FIELD = "goals_in_chores"`, `_GOALS_IN_REWARDS_FIELD = "goals_in_rewards"` (:272-274). `CONF_CALENDARS = "calendars"` (`const.py:86`), `CONF_DEFAULT_NOTIFY = "default_notify_target"` (`const.py:87`), `_ADD_DASHBOARD_FIELD = "add_dashboard"` (:339), finish step takes `{}`. Executed sequence (2026-10-28): `features` -> `users` -> `member_profile` x N -> `chores_features` -> `calendars` -> `notifications` -> `dashboard` -> `finish` -> `create_entry`.

**Family Hub commands the seed uses** (schemas re-read today in `chores_websocket_api.py`): `family_hub/chores/create` (`title` required; `assigned_to`, `star_value`, `due_date`, `recur_type`, ... optional; :904), `family_hub/rewards/add_catalog_item` (`title`, `cost_stars` required; `icon`, `color` optional; :1474), `family_hub/rewards/adjust_balance` (`user_id`, `delta` required; `reason` optional; :1663), `family_hub/goals/create` (`title`, `assigned_to` required; `target_count`, `reward_type`, `star_value` optional; :2595), `family_hub/routines/create` (`user_id`, `category`, `title` required; `due_time`, `days_of_week`, `star_value` optional; :2332), `family_hub/kiosk/set_pin` (`user_id` required, `pin` optional, admin-only; :2165), `family_hub/kiosk/elevate` (`user_id`, `pin`; :2190), `family_hub/get_settings` (`__init__.py:2519`), `family_hub/set_settings` (:2568), `family_hub/set_recipes` (:4099). For kid PIN sign-in, `settings["kioskLoginEnabledUserIds"]` must contain the kid id (`chores_websocket_api.py` `ws_kiosk_list_login_users` reads `settings.get("kioskLoginEnabledUserIds")`) and a PIN must be set.

### Pattern 4: Dashboard (storage mode) and resource verification
`lovelace/dashboards/create` `{url_path: "family-hub", title, icon, show_in_sidebar: true, require_admin: false, mode: "storage"}` then `lovelace/config/save` `{url_path, config}` (admin-only; `lovelace/websocket.py` `@websocket_api.require_admin` on `lovelace/config/save`). The integration's `_register_dashboard_resource` (`__init__.py:12190`) matches existing resources by base path and updates the URL in place when the hash changes (`async_update_item`, :12240-12241), so a restart refreshes the hash. The seed lists `lovelace/resources`, diffs against the served `*_CARD_JS_URL` constants (do not hard-code the count; 13 were registered in the 2026-10-28 run) and compares each `?v=` to `sha256(file)[:10]` (`_file_content_hash`, :12172-12187), creating missing ones with `lovelace/resources/create` `{res_type: "module", url}` and **updating, never duplicating** (two resource URLs for one card makes `customElements.define` throw; PITFALLS.md Pitfall 6).
Layout (D-18): one **panel-type view per card**: Calendar, Today, Chores, Rewards, To-dos, Recipes. Card YAML from `DOCUMENTATION.md`: `custom:family-week-calendar-card` with `people`, `recipe_entity`, `meal_plan_entity`, `meal_templates_entity`, `suggestions_entity`, `reminders_entity`, `weather_entity`; `custom:family-hub-chores-card`, `-rewards-card`, `-goals-card`; `custom:family-hub-todo-card` with `entities`; `custom:family-hub-recipe-box-card`; `custom:family-today-card`. **Pantry:** the card is a Grocy stock list plus an "Also Tracking" notes list (`card/family-hub-pantry-card.js` header); with Grocy off, omit the Pantry view unless a Dev visual check shows the "Also Tracking" part is useful (D-18 says "Recipes/Pantry"; assumption A6).

### Pattern 5: Google Calendar in a non-production instance
1. **Once per Google Cloud project (human checkpoint, developer's own account, D-26):** create a **Web application** OAuth client, authorised redirect URI exactly `https://my.home-assistant.io/redirect/oauth`, and under Audience set Publishing status to **Publish app**; HA docs: "Otherwise, your credentials will expire every 7 days." [CITED: home-assistant.io/integrations/google, fetched 2026-11-02]. Google: a Testing-status external app "is issued a refresh token expiring in 7 days"; other expiry causes: unused for six months, and "a limit of 100 refresh tokens per Google Account per OAuth 2.0 client ID" (oldest silently revoked) [CITED: developers.google.com/identity/protocols/oauth2, fetched 2026-11-02]. Dev and Preview each hold their own token under the same client: 2 of 100. Google's page does not address the "In production but unverified, sensitive scope" case; that a published-unverified app keeps non-expiring tokens rests on HA's docs only (A9). The default requested scope is read/write: `FeatureAccess.read_write = "https://www.googleapis.com/auth/calendar"` and `DEFAULT_FEATURE_ACCESS = FeatureAccess.read_write` (`google/const.py:17-28`). An unverified-app warning screen appears at sign-in; acceptable for one account.
2. **After each fresh start (seed):** `application_credentials/create` `{domain: "google", client_id, client_secret, name}` from the gitignored local file; if a preserved entry exists it was written pre-start, so `POST /api/config/config_entries/entry/<entry_id>/reload` and poll for `state == "loaded"`.
3. **Pre-start restore:** write `.storage/core.config_entries` as `{"version": 1, "minor_version": 5, "key": "core.config_entries", "data": {"entries": [<google entry only>]}}` (version fields re-read from a live file this session). The entry copy is taken from the **stopped** instance (HA flushes on stop) into `dev/.ha-secrets/google-<env>.json` (0600). Absent file -> the seed stops with the documented one-time sign-in instruction (D-10 fallback).
4. **Sign-in on a Windows laptop:** the browser doing the OAuth dance runs on **Windows**, and `my.home-assistant.io` redirects back to the instance URL saved in that browser. Use `https://localhost:<port>` (Dev) / the laptop address (Preview); the Windows browser must trust the CA (import `ca.crt` into the Windows "Trusted Root Certification Authorities" store) or the redirect shows a certificate warning. Switching between Dev and Preview means changing the saved instance URL at my.home-assistant.io (A8).
5. **Choose calendars:** the integration creates entities for **every** calendar on the account (entity `unique_id` is `f"{config_entry.unique_id}-{entity_description.key}"` with `key = calendar_id` when one entity per calendar; `google/calendar.py` lines read 2026-10-28), plus Birthdays/Work Location entities. After the entry loads, list `config/entity_registry/list`, keep entities whose `unique_id` ends with a chosen `calendar_id` and disable the rest with `config/entity_registry/update` `{entity_id, disabled_by: "user"}`; include Birthdays in the disable set unless chosen. Read-only calendars get no create/delete (`read_only = not (calendar_item.access_role.is_writer and get_feature_access(config_entry) is FeatureAccess.read_write)`, `google/calendar.py:137-140`), a free guard. The entry option `calendar_access` (`CONF_CALENDAR_ACCESS`, `read_only`/`read_write`) exists if a Dev-only read-only mode is ever wanted; D-15 says Dev is read/write.
6. **Tagged events (D-11/D-15/D-25) with week-anchored diff sync.** Each seeded event has a stable key derived from (environment, calendar, weekday-in-week, slot), embedded as a marker line in `description`, e.g. `family-hub-seed:preview:<key>`; summary starts exactly `[PREVIEW] ` (Dev: `[DEV] `). The refresh computes the desired set for "this week and next" (anchored to calendar weeks, so keys and dates are stable all week), reads existing tagged events, **creates only the missing, deletes only the stale** (past the window), and never re-creates an unchanged event. A naive "delete all tagged, re-create" daily refresh would create new events each morning on the real calendars and buzz family phones daily (the developer accepted buzz for seeding, D-25, not daily churn). Deletion requires **all** of: summary starts with the exact env tag, description contains the exact env marker, within a bounded date window, on an allow-listed calendar; seeded events are single (non-recurring) so `recurrence_range` is never needed. Candidates come from `GET /api/calendars/<entity>?start=&end=` (returns `uid`, `recurrence_id`); delete with WS `calendar/event/delete` `{entity_id, uid, recurrence_id?}`. `--dry-run` is the default for the tag cleaner. Test: a pure-function suite for `calendar_tags.matches()` (tagged, untagged, other-env, tag-in-the-middle, marker missing, out-of-window) plus one live run against a Local Calendar in a pip-installed HA asserting only the exact set is removed.
7. **Reminders:** HA's Google `create_event` accepts `summary`, `description`, `location` and start/end only (read 2026-10-28, `google/calendar.py`), so each subscriber's default reminders apply; this is the D-25 accepted effect. The `[PREVIEW]` tag also makes seeded events self-explanatory on family phones.

### Pattern 6: Build stamp without touching `__init__.py`
Add a constant block near the top of `card/family-week-calendar-card.js`, e.g. `const __FH_BUILD = { env: "__FH_BUILD_ENV__", version: "__FH_BUILD_VERSION__", deployed: "__FH_BUILD_TIME__" };`, render it as a small footer inside the existing `<ha-card>` template (the single `</ha-card>` is at `card/family-week-calendar-card.js:16077`; the 2026-10-28 note citing ~14392 was stale) and emit one `console.info`. `deploy-preview` substitutes the three tokens **in the exported copy only**; that changes the file hash so the integration's `?v=` logic updates the resource at the next start. In Dev the tokens stay literal and the card shows `Dev · live`. After deploy fetch `https://127.0.0.1:8124/family_hub_card/family-week-calendar-card.js?v=<hash>` with the CA, assert the short git hash is present and the `lovelace/resources` hash equals `sha256(file)[:10]`.
**D-09 mechanism (recommendation):** do not reuse the build stamp for the delete warning, because a Home release is unsubstituted too and would look like Dev. Use `hass.config.location_name`: the card shows the loud confirm only when the HA location name matches `/\b(PREVIEW|DEV)\b/` and `family_hub/calendar/delete_support` reports the Google platform. Names are set by the seed (D-17) and a Home name would not contain these words. Hook point: the existing confirm in `_wireEventInfoDeleteButton` (`window.confirm(` at `card/family-week-calendar-card.js:23685`, `type: "family_hub/calendar/delete_event"` at :23698). No backend or settings-schema change is needed (avoids the "new fields need defaults in both places" rule).

### Pattern 7: Her account, sidebar and default dashboard
Log in with the seeder (login flow, not a long-lived token): `POST /auth/login_flow` `{client_id, handler: ["homeassistant", null], redirect_uri}`, `POST /auth/login_flow/<id>` `{client_id, username, password}`, exchange the code (re-ran this session). With **her** token: `get_panels`, compute `hiddenPanels` = every key except `family-hub` (plus non-sidebar `profile`, `notfound`) and call `frontend/set_user_data` `{key: "sidebar", value: {panelOrder: [], hiddenPanels: [...]}}` and `{key: "core", value: {default_panel: "family-hub"}}`. The integration registers a Theme Builder panel with `PANEL_URL = "theme-builder"` (`const.py:939`), which a non-admin sees unless hidden. The bell and her profile entry always remain. Compute the list per run, never hard-code (panel ids depend on loaded integrations; this session's admin panel list was `_my_redirect, climate, config, home, light, lovelace, maintenance, map, media-browser, notfound, profile, security`).

### Pattern 8: Isolation and safety verification (run by deploy/reset/refresh)
Assert, as admin: (a) every `userProfiles[*].notifyTargets` is empty or exactly `["notify.persistent_notification"]`; (b) settings key `SETTINGS_KEY_ALARM_DEVICES = "alarmDevices"` (`const.py:724`) is empty/absent and no `media_player`/`assist_satellite` entity exists; (c) config-entry domains are within an allow-list (`family_hub`, `local_calendar`, `local_todo`, `google`, `mobile_app`, `analytics`, `backup`, `sun`, `shopping_list`); (d) Grocy URL/key blank; (e) `location_name` matches the target **before** any credentials are sent and refuse otherwise. Notification fan-out is opt-in per profile flag and `notifyTargets` defaults to `[]`; the only auto-discovery is `_detect_user_notify_targets` (`__init__.py:1970`) called by `_migrate_notify_profiles` (:2003) at entry creation and by the card's Auto-detect button. The real risks are that button and creating the Family Hub entry **after** a Companion device registered, so the seed writes the safe value and the check enforces it. Adding Preview as a second server on her phone creates a `mobile_app` device on Preview (registration verified this session), so (a) must be re-asserted on every refresh.

### Anti-Patterns to Avoid
- **Polling `/api/onboarding` for readiness.**
- **Putting any `http:` YAML in and forgetting `http/config/promote`.**
- **Writing `.storage` of a running HA**, or hand-writing more than the single Google entry before first start.
- **Deleting by summary prefix alone** on Google calendars.
- **"Delete all tagged, re-create all" refresh** on real calendars (daily buzz).
- **Copying Home's config** or reusing its `core.uuid`.
- **`default_config:`** in Preview.
- **Keeping the repo or `dev/.ha-*` under `/mnt/c`** (permissions, speed, root-owned files).
- **Seeding via the LAN IP from inside WSL** (hairpin to the host's own LAN address is unreliable in mirrored mode; use `127.0.0.1`).
- **Hard-coding the sidebar hide list.**

## Host layer: Windows 11 + WSL2 + Docker Engine (new, D-23/D-24)

**One-time setup the guide for the developer must cover** (all are `[ASSUMED]` or `[CITED]` as marked; none could be tested here):

1. **Windows 11 22H2+ and WSL from the Store with systemd.** Mirrored mode needs 22H2+ [CITED: learn.microsoft.com/windows/wsl/networking]. `/etc/wsl.conf`: `[boot]` `systemd=true` [CITED: wsl-config]. Install Docker Engine in the distro (Docker's Ubuntu instructions), `sudo systemctl enable --now docker`, add the user to the `docker` group.
2. **`%UserProfile%\.wslconfig`:** `[wsl2]` `networkingMode=mirrored`; `firewall` defaults to `true` [CITED: wsl-config]. Run `wsl --shutdown` afterwards ("8 second rule", [CITED]). `[experimental]` `hostAddressLoopback=true` is the documented lever when Windows cannot reach container ports via the host's own addresses (issue #10494: Microsoft recommended it and a reporter confirmed it). The default kernel modules include `tun`, `ip_tables`, `br_netfilter` (`loadDefaultKernelModules` default true), which Docker bridge networking needs [CITED: wsl-config].
3. **Hyper-V firewall rule (replaces D-23's "Windows Firewall rule"):** on Windows 11 22H2+ with WSL 2.0.9+ the Hyper-V firewall is on by default, and Microsoft's mirrored-mode note gives the commands, run in an elevated PowerShell [VERIFIED: learn.microsoft.com/windows/wsl/networking, fetched 2026-11-02, quoted verbatim]:
   `New-NetFirewallHyperVRule -Name "MyWebServer" -DisplayName "My Web Server" -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 80`
   Use `-Name "FamilyHubPreview" ... -LocalPorts 8124` (Dev stays loopback-only, no rule). The broader `Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow` opens every WSL port to the LAN and is not recommended. Whether an additional Windows Defender inbound rule is also needed is `[ASSUMED: A3]`; the checkpoint tests from her phone. Also check the Wi-Fi network profile is **Private** (A3).
4. **Port space is shared in mirrored mode.** Windows must not already use 8124/8130, and Windows can reserve port ranges: `netsh interface ipv4 show excludedportrange protocol=tcp` (`doctor` check, `[ASSUMED]` as a likely failure source).
5. **Keep WSL alive and start it at login.** WSL stops the distro when idle: `[general] instanceIdleTimeout` defaults to 15000 ms and `[wsl2] vmIdleTimeout` to 60000 ms [CITED: wsl-config]. A systemd service does **not** keep it up: issue #13416 (open, reproduced on 2.4.13, 2.5.10, 2.6.1 and 2.7.3; August 2026) says only a Windows-side process works, e.g. a Scheduled Task running `wsl.exe -d Ubuntu -e sleep infinity` [CITED: github.com/microsoft/wsl/issues/13416]; setting `vmIdleTimeout` to `-1` had no effect there. Plan: Task Scheduler task "FamilyHub WSL keep-alive", trigger At log on of the developer, action `wsl.exe -d <distro> -e sleep infinity`. Containers then start by themselves (`restart: unless-stopped`) once dockerd is up. Consequence for D-03: Preview is available only while the developer's Windows user is **logged in** and the laptop is awake (or the task is configured to run whether logged on or not, which needs a stored password; leave to the developer). Windows power settings: "sleep: never" when plugged in is optional but recommended on agreed try-out days (`powercfg`, `[ASSUMED]`).
6. **Scheduler for D-28:** two more Scheduled Tasks calling `wsl.exe -d <distro> -e bash -lc '<repo>/scripts/refresh-preview'`: at log on (delay about 2 minutes so Docker and HA are up) and daily at a fixed time, with "run as soon as possible after a scheduled start is missed" `[ASSUMED: Task Scheduler setting]`. `refresh-preview` must itself wait for HA RUNNING and exit non-zero loudly otherwise.
7. **Wi-Fi random hardware addresses (D-24):** Windows 11 has a per-network "Random hardware addresses" setting (Settings > Network & internet > Wi-Fi > <network> > Properties) and a global one; set the home network to Off before creating the router DHCP reservation, then confirm the reservation is listed under the adapter's real MAC [CITED: third-party guides, e.g. elevenforum.com; no Microsoft page retrieved; `[ASSUMED]` for the reservation interplay].
8. **Clock:** WSL's clock has long drifted after Windows sleep/resume (issues since 2019; fixes are a resume-triggered `hwclock -s`/NTP resync) [CITED: github.com/microsoft/WSL/issues/8204, /4149 via search]. `doctor` compares `date -u` in WSL with `powershell.exe -c "(Get-Date).ToUniversalTime()"`. Clock skew matters for TLS validity and Google token refresh. `[wsl.conf] [time] useWindowsTimezone` is true by default; `TZ` still comes from `host.env`.
9. **Repo location and line endings:** keep the repo and `dev/.ha-*` on WSL ext4 (e.g. `~/HA-Family-Hub`). `chmod 0600` secrets only work reliably there: DrvFs permission masks "only apply when the Windows drive is mounted with metadata. By default metadata is not enabled" [CITED: wsl-config]. `doctor` refuses to run from `/mnt/*`. Add `.gitattributes` forcing LF for scripts and YAML so a Windows-side clone cannot produce `bash\r` failures (the repo has no `.gitattributes` today).
10. **Windows trust store:** import `ca.crt` into Windows so the developer's Windows browser can use `https://localhost:8130/8124` (needed for Google sign-in, Pattern 5.4).
11. **Localhost from Windows:** Dev is published as `127.0.0.1:8130`. In mirrored mode a Windows browser reaching `localhost` published container ports has needed `127.0.0.1` rather than `localhost` or `hostAddressLoopback=true` in reports (issue #10494, `[CITED]`); the checkpoint confirms.

**Fallback ladder if the phone cannot reach `https://<ip>:8124`** (the checkpoint decides, in this order): (1) re-check Hyper-V rule, profile, excluded port ranges, `wsl --version`; (2) `hostAddressLoopback=true`; (3) move off a regressed WSL build (see Pitfall 4); (4) switch `networkingMode` back to NAT and add a boot-time `netsh interface portproxy add v4tov4 listenport=8124 listenaddress=0.0.0.0 connectport=8124 connectaddress=<wsl hostname -I>` refreshed at every WSL start (documented by Microsoft for NAT, [CITED: networking]; the WSL VM address changes between starts, so this needs a script); (5) only as a last resort and an explicit decision, `network_mode: host` for Preview (departs from PREV-01's bridge rule).

**`scripts/doctor` checks (D-23):** `wsl.exe --version` (record it), `networkingMode` in `.wslconfig` (read via `cmd.exe /c type %UserProfile%\.wslconfig`), Engine not Desktop (`docker version` server platform / no `docker-desktop` distro), `docker compose version`, repo path not under `/mnt`, `dev/host.env` present and 0600 secrets, clock delta, ports free (`ss -ltn`) and not excluded, `PREVIEW_HOST_IP` equals the Windows Wi-Fi IPv4 (`powershell.exe Get-NetIPAddress`), cert SAN contains `PREVIEW_HOST_IP`, Hyper-V rule present (`Get-NetFirewallHyperVRule -Name FamilyHubPreview`, needs elevation, otherwise print the command), scheduled tasks present (`schtasks.exe /query`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Creating users, entries, dashboards, entity-registry changes | Direct `.storage` edits | HA public REST/WS (verified list) | `.storage` formats are internal and flushed on stop |
| OAuth token exchange for Google | Own OAuth client | HA's Google integration + `application_credentials` | HA refreshes tokens, stores them, handles reauth |
| Reading/deleting Google events | Raw Google API calls | `calendar.create_event`, `GET /api/calendars/...`, WS `calendar/event/delete` | Same surface as Local Calendar, so unit-testable |
| Certificate chain for LAN HTTPS | Self-signed leaf trusted directly; an intermediate | Name-constrained **root** CA + leaf with IP SAN (script below) | Android needs a CA import; a single root avoids the open #7346 intermediate failure |
| Dashboard resource registration | Custom JS injection | The integration's own `_register_dashboard_resource` + `lovelace/resources/update` | Already handles hash updates |
| Per-user sidebar | Admin-side hacks | `frontend/set_user_data` as her | Per-user server-side data |
| Reset wipe | `rm -rf` of a root-owned bind mount | Helper container (`docker run --rm -v <dir>:/config busybox ...`) | See Pitfall 9 |
| Keeping WSL awake | systemd service | Windows Scheduled Task running `wsl.exe -e sleep infinity` | Only approach reported to work (#13416) |
| Screenshots for the guide | Manual phone captures | Playwright + token injection into `localStorage.hassTokens` | Reproducible and seeded; only Android install screens need a real phone |

**Key insight:** every step the seed needs already has an official or integration-provided API; the work is ordering, idempotence, safety checks, and refusing to run against Home.

## Runtime State Inventory

Not a rename/refactor/migration phase. Omitted.

## Common Pitfalls

### Pitfall 1: Pending HTTP config reverts after 5 minutes
**What goes wrong:** Preview serves HTTPS for five minutes after a reset, then restarts onto plain HTTP on 8123; her phone fails and the seed's client dies.
**Why:** HA 2026.10 imports `http:` YAML once into `.storage/http` as **pending** and reverts after `AUTO_REVERT_DELAY: Final = timedelta(minutes=5)` unless promoted (`components/http/config.py:81`). Reproduced again this session: with only `server_port` in `http:` YAML, `http/config` returned `active_config_type: "pending"` with a `revert_at` timestamp and `.storage/http` held `pending.server_port: 8139` next to `stable.server_port: 8123`.
**How to avoid:** the seed calls WS `http/config/promote` (`websocket_api.py:143`) right after onboarding and asserts `active_config_type == "stable"`, `revert_at == null`. Warning signs: log `Pending HTTP config was not confirmed within 0:05:00`; `.storage/http` `pending.error == "not_promoted"`. The YAML import also raises a repair (`breaks_in_ha_version 2027.2.0`); plan `http/config/configure` on the next HA bump.

### Pitfall 2: Readiness probe
**What goes wrong:** `deploy-preview` waits forever or proceeds early. `/api/onboarding` never signals readiness; the image may not ship `curl` (A5).
**How to avoid:** host-side probe: login, WS `get_config`, `state == "RUNNING"`, then the Family Hub entry `loaded` via `config_entries/get`. Allow a generous first-boot timeout; a fresh Docker volume installs runtime requirements (Local Calendar `ical`, Google `gcal-sync`) and needs internet.

### Pitfall 3: Google refresh token dies every 7 days
**What goes wrong:** D-10 silently stops working weekly. **Why:** app left in Testing. **How to avoid:** publish the app (D-26); verify detects `setup_error`/reauth and prints the one-time sign-in instruction. Also: a token unused for six months, and the 100-token cap.

### Pitfall 4: WSL mirrored mode and Docker are version-sensitive in 2026
**What goes wrong:** Published container ports fail to bind or be reachable. **Evidence:** issue #40984 (opened 2026-07-02, still open 2026-10-01): on WSL 2.9.3/2.9.4 with `networkingMode=mirrored`, Docker fails with "failed to bind host port 0.0.0.0:8003/tcp: address already in use" although the port is free; NAT mode works; cause suspected as overlap between WSL's reserved guest ephemeral range and Windows' dynamic range (49152-65535), so low ports like 8124/8130 might be unaffected but the symptom was reported on port 8003, so this is not reliable. Older issues: #10494 (Docker 24-27 containers reachable from another machine on the LAN but not from the host itself; `hostAddressLoopback=true` confirmed as the fix), #10926 (container to Windows service refused in mirrored mode; fixed in WSL 2.3.11 with mixed later reports) [CITED: github.com/microsoft/WSL issues, fetched 2026-11-02].
**How to avoid:** record `wsl --version` in `doctor`; do not auto-update WSL on the laptop between try-out sessions (`wsl --update` is a deliberate step); make the laptop checkpoint the first executable task after compose exists; keep the fallback ladder above. Confidence MEDIUM-LOW.

### Pitfall 5: WSL shuts down when idle, taking Preview with it
**What goes wrong:** She opens Preview and it is down although the laptop is on. **Why:** the distro stops when no Windows-side process holds it (#13416); `restart: unless-stopped` cannot help because dockerd is gone. **How to avoid:** the keep-alive Scheduled Task (Host layer item 5); `refresh-preview` and `doctor` report when the keep-alive task is absent; the guide for her says Preview is available at agreed times.

### Pitfall 6: Google refresh churns the real calendars
**What goes wrong:** Daily refresh deletes and re-creates tagged events, producing notifications and edits on family phones every day. **How to avoid:** week-anchored keys and diff sync (Pattern 5.6). Also keep `refresh-preview` from running while a tagged-event delete is unverified: hard stop when the allow-listed calendar set or tag does not match the family file.

### Pitfall 7: Google entry without its credential looks like an auth failure
**What goes wrong:** the preserved entry goes to `setup_error` with a reauth flow. **How to avoid:** order = restore entry pre-start, create credential, reload entry, assert `loaded`; the credential id is derived from the client id, so the client id in the local file must not change.

### Pitfall 8: CRLF and wrong-filesystem traps from Windows
**What goes wrong:** `bash\r: No such file` on scripts cloned via Windows git; secrets cannot be `chmod 0600`; bind mounts are slow. **How to avoid:** `.gitattributes` (LF), clone inside WSL, `doctor` refuses `/mnt/*`.

### Pitfall 9: Root-owned files in a bind-mounted volume
**What goes wrong:** HA runs as root in the container, so `.storage` and `family_hub_backups/` are root-owned on the host; `rm -rf` fails, and a half-reset resurrects data (`store.py` `_maybe_restore_backup` restores from `family_hub_backups/` when a Store loads empty; backup dir name `SETTINGS_BACKUP_DIR_NAME = "family_hub_backups"` at `const.py:174`).
**How to avoid:** reset stops the stack and wipes through a throwaway container (`docker run --rm -v "$HA_CONFIG_DIR":/config busybox sh -c 'find /config -mindepth 1 -maxdepth 1 ! -name custom_components -exec rm -rf {} +'`), keeping `custom_components/`. Test: seed, mutate, reset, assert state equals seed and `family_hub_backups/` is empty. [A2: root ownership not observable here]

### Pitfall 10: Published ports and the laptop leaving home
**What goes wrong:** Docker publishes to all interfaces by default [CITED: docs.docker.com/engine/network/port-publishing]; on other Wi-Fi the Preview login (and its Google token) is reachable. Binding to the reserved IP would make start fail if the IP is absent [A4].
**How to avoid:** Dev `127.0.0.1:8130`; Preview `${PREVIEW_BIND:-0.0.0.0}:8124`, HA's `ip_ban_enabled: true` default (read from `http/config` output: `"ip_ban_enabled": true`), generated strong passwords, no port forwarding, a `scripts/preview-down` the developer runs before leaving home, and the Hyper-V rule only for 8124. Optionally restrict the rule's remote addresses to the home subnet.

### Pitfall 11: `reset-preview` logs her phone out (D-27)
**What goes wrong:** the wipe removes `.storage/auth`; her Companion session is invalid, and the registered `mobile_app` device and its webhook are gone. HA's developer docs say a webhook 410 "means the integration has been deleted. You should notify the user and most likely register again" [CITED: developers.home-assistant.io/docs/api/native-app-integration/sending-data], so the app should prompt, but the exact Android behaviour is unverified.
**How to avoid:** seed her with the **same username and password** every reset; guide line: "If the app asks you to sign in again after the developer has reset Preview, sign in with your usual details; if it still fails, tell the developer." Test on her phone (checkpoint), record whether re-login or re-adding the server was needed in the guide. Pinning a per-environment `core.uuid` (format read from `helpers/instance_id.py`: `{"uuid": <hex>}`) is the fallback only if re-adding is required; note `core.uuid` was not even created in a fresh run this session, so Companion may not depend on it (A7).

### Pitfall 12: Edited card JS is not reloaded by a normal browser refresh (DEV-02)
**What goes wrong:** the developer edits `card/*.js` in Dev, refreshes, and still sees the old code. **Evidence (reproduced this session):** a local aiohttp `FileResponse` (the same ETag + Last-Modified, no Cache-Control behaviour as the HA static handler registered with `cache_headers=False`, `__init__.py:12553-12561`) served a module whose `Last-Modified` was 30 days old; after editing the file and calling Playwright/Chromium `page.reload()` twice, the page still ran the old module (`one`, `one`, `one`). The `?v=<hash>` only changes at HA start. [VERIFIED: executed in this session]
**How to avoid:** ship `scripts/dev-cards` that recomputes each served file's hash and calls `lovelace/resources/update` `{resource_id, url: "<base>?v=<newhash>"}` (verified this session: `resource_id` + `url` accepted), after which a normal refresh fetches the new URL. Document the hard-reload (Ctrl+Shift+R, or DevTools "Disable cache") as the fallback. Python changes still need a container restart (`docker compose restart`).

### Pitfall 13: Companion registers on Preview and shares phone sensors
Each added server gets its own `mobile_app` device and `notify.mobile_app_<device>`; the app can send sensors and location to every server [CITED: companion.home-assistant.io FAQ]. Preview's notify list then contains a real phone. Keep every `notifyTargets` empty/persistent-notification and let verify fail otherwise; tell the developer to disable sensors for the Preview server in app settings; the Android "Add server" screen must accept a manual URL because zeroconf is off.

### Pitfall 14: Secure-context differences are small
The only secure-context dependent API in the served calendar card is the clipboard, and it has a fallback (`_copyTextToClipboard`, `card/family-week-calendar-card.js:27725`, comment names the insecure-context case). `http://localhost` is already a secure context, so Dev gains little from HTTPS beyond testing the same certificate path.

### Pitfall 15: Non-admin event subscriptions
Her browser logs `Refusing to allow ... to subscribe to event family_hub_timer_alarm_ring` / `family_hub_daily_digest_open` (HA allows only `SUBSCRIBE_ALLOWLIST` events to non-admins). The chores card catches this (`_subscribeAlarmEvents`), so chores and rewards work; timer-alarm broadcast and the digest popup do not work for a non-admin. Record in UAT notes; do not fix in Phase 2.

### Pitfall 16: Missing optional entities
Create all five `todo.*` lists. The week card handles a missing weather entity gracefully: `_fetchWeather` wraps the `weather.get_forecasts` call in try/catch and falls back to `this._forecast = {}` (`card/family-week-calendar-card.js:13291-13318`), so no UI error (HA logs a service error; resolved old A7). Omit `met` (the seed deletes it).

### Pitfall 17: Seed side effects of onboarding
`core_config` auto-adds `radio_browser`, `google_translate`, `shopping_list` (and `met` once a location exists). Delete the outbound ones in the seed (Pattern 3 step 4) to honour locality.

### Pitfall 18: The OAuth redirect and a private CA
The Google OAuth redirect lands in the developer's Windows browser; without the CA in the Windows store it shows a certificate warning, and `my.home-assistant.io` must hold the matching instance URL. Document both in the one-time Google checkpoint (A8).

## Code Examples

Verified by execution against HA 2026.10.4 on 2026-10-28 unless noted; `BASE` is `https://127.0.0.1:<port>` from inside WSL with an `ssl.SSLContext` built from `ca.crt` (never `verify=False`).

### Onboard a pristine instance
```python
# Source: homeassistant/components/onboarding/views.py; re-run (HTTP) in this session
CID = BASE + "/"
r = await s.post(BASE + "/api/onboarding/users", json={"client_id": CID, "name": "Dev Admin",
        "username": "dev", "password": PASSWORD, "language": "en"})
code = (await r.json())["auth_code"]
tok = await (await s.post(BASE + "/auth/token", data={"grant_type": "authorization_code", "code": code, "client_id": CID})).json()
h = {"Authorization": "Bearer " + tok["access_token"]}
for step in ("core_config", "analytics"):
    await s.post(BASE + f"/api/onboarding/{step}", headers=h, json={})
await s.post(BASE + "/api/onboarding/integration", headers=h, json={"client_id": CID, "redirect_uri": CID + "?auth_callback=1"})
# then over WS as admin: {"type": "http/config/promote"}; {"type": "config/core/update", "location_name": "Family Hub PREVIEW", "time_zone": TZ, ...}
```

### Login as a user (no stored token) and update a resource URL
```python
# Source: login flow + lovelace/resources/update, both re-run this session
r = await s.post(BASE + "/auth/login_flow", json={"client_id": CID, "handler": ["homeassistant", None], "redirect_uri": CID + "?auth_callback=1"})
fid = (await r.json())["flow_id"]
r = await s.post(BASE + f"/auth/login_flow/{fid}", json={"client_id": CID, "username": USER, "password": PW})
tok = await (await s.post(BASE + "/auth/token", data={"grant_type": "authorization_code", "code": (await r.json())["result"], "client_id": CID})).json()
# WS admin: {"type": "lovelace/resources/update", "resource_id": rid, "url": "/family_hub_card/x.js?v=<newhash>"}   -> {"id","url","type"}
```

### Create her non-admin account and a kid
```python
r = await ws.call("config/auth/create", name="Her Name", group_ids=["system-users"], local_only=False)
uid = r["result"]["user"]["id"]
await ws.call("config/auth_provider/homeassistant/create", user_id=uid, username="her", password=PASSWORD)
```

### Drive the Family Hub config flow
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
panels = (await her_ws.call("get_panels"))["result"]
hidden = [p for p in panels if p not in ("family-hub", "profile", "notfound")]    # includes "theme-builder"
await her_ws.call("frontend/set_user_data", key="sidebar", value={"panelOrder": [], "hiddenPanels": hidden})
await her_ws.call("frontend/set_user_data", key="core", value={"default_panel": "family-hub"})
```

### Name-constrained local root CA + leaf (verified with `openssl verify` and with HA serving HTTPS, 2026-10-28)
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
cat leaf.crt ca.crt > fullchain.pem; cp leaf.key privkey.pem; chmod 600 privkey.pem ca.key
```
The CA signs the leaf **directly** (no intermediate; see #7346). Add `10.0.0.0/255.0.0.0` and `172.16.0.0/255.240.0.0` to `permitted` if the home LAN uses them (read `PREVIEW_HOST_IP` in `make-certs` and fail clearly when it is outside the permitted ranges). Keep leaf validity at about a year (the /e/OS thread anecdote: a 10-year leaf failed, 180 days worked, unconfirmed). Install **only `ca.crt`** on the phone and in the Windows store; never `ca.key`. Regenerate the leaf when `PREVIEW_HOST_IP` changes (D-05, host move).

### Headless screenshot of her dashboard (for `docs/family/`)
```python
tokens = {"access_token": t["access_token"], "token_type": "Bearer", "expires_in": t["expires_in"],
          "hassUrl": BASE, "clientId": CID, "expires": int(time.time()*1000) + t["expires_in"]*1000,
          "refresh_token": t["refresh_token"]}
ctx = await browser.new_context(viewport={"width": 412, "height": 900}, device_scale_factor=2, is_mobile=True)
await ctx.add_init_script("localStorage.setItem('hassTokens', %s);" % json.dumps(json.dumps(tokens)))
page = await ctx.new_page(); await page.goto(BASE + "/"); await page.wait_for_timeout(30000)
```
Result in the 2026-10-28 spike: landed on `/family-hub/home`, calendar card rendered with the seeded `[PREVIEW] Dentist` event. Chromium launches in this sandbox (Playwright 1.64.1); in WSL it needs the usual `playwright install --with-deps chromium` (A10).

### Meals and events (HA built-ins)
```python
desc = json.dumps({"description": "", "link": "", "color": "", "block": 0, "recur": None, "grocyRecipeId": None,
                   "servings": None, "spanDays": 1, "additionalRecipes": [], "leftoverDates": []})
await call_service("todo", "add_item", {"entity_id": "todo.meal_plan", "item": "Spaghetti night", "description": desc, "due_date": "2026-11-04"})
await call_service("calendar", "create_event", {"entity_id": cal, "summary": "[PREVIEW] Dentist",
                   "start_date_time": "2026-11-04 16:00:00", "end_date_time": "2026-11-04 17:00:00",
                   "description": "family-hub-seed:preview:dentist-wed"})
```
(The meal description shape is the Python twin of the card's encoder, `_encode_dish_description`, `__init__.py:3324`; the keys were quoted there on 2026-10-28.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `http:` options only in YAML | YAML imported once as pending; promote or auto-revert in 5 min; YAML deprecated (2027.2.0) | HA 2026.x | Seed must promote; plan `http/config/configure` later |
| `voluptuous` in core | `probatio` fork in core (`lovelace`, `http`, `config` modules import it); this integration's `voluptuous` schemas still work | HA 2026.x | Watch on every HA bump |
| Python 3.12/3.13 | Python 3.14 (HA 2026.10) | HA 2026.10 | Seed/test tooling needs 3.14 via `uv` |
| Companion trusts only system CAs | Default trust manager + user-CA fallback | Android PR #7044, 2026-06-18; release 2026.6.5 | Needs app >= 2026.6.5; intermediate-chain bug #7346 open |
| Google device-auth credentials | Web-application credentials via `my.home-assistant.io` redirect | HA docs | Use a Web client; publish the app |
| WSL NAT networking | Mirrored mode (Windows 11 22H2+) with Hyper-V firewall | WSL 2.0.9+ | Needs the Hyper-V rule; version-sensitive with Docker |

**Deprecated/outdated:** the ARCHITECTURE.md compose healthcheck against `/api/onboarding`; `track:` in `google_calendars.yaml`; the Phase 2 research note "Docker Desktop on macOS" (the host is Windows + WSL2 Engine, D-23).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Android "install CA" menu path and success on her specific phone/OEM; her Companion app is >= 2026.6.5 | Answers D-06, guide | Guide steps wrong or app rejects the CA; mitigated by the phone checkpoint and the fallback ladder |
| A2 | HA runs as root in the container so bind-mounted `.storage` is root-owned on WSL ext4 | Pitfall 9 | Helper container unnecessary (harmless) |
| A3 | A Hyper-V firewall rule alone (not also a Defender rule) lets her phone reach 8124, and the Wi-Fi profile must be Private | Host layer 3 | Phone cannot connect until the second rule/profile is fixed; checkpoint catches it |
| A4 | Docker fails to start a container whose published port is bound to an IP not present on the host | Pitfall 10 | If it works, binding to the reserved IP becomes a cleaner LAN-only option |
| A5 | The HA container image has `curl` | Pitfall 2 | Use host-side probes only (recommended anyway) |
| A6 | The Pantry card is not useful with Grocy off and can be omitted | Pattern 4 | A requested view missing; check in Dev |
| A7 | Companion needs no stable `core.uuid` and re-login (same credentials) is enough after reset | Pitfall 11 | Re-adding the server needed each reset; pin a per-env uuid |
| A8 | The `my.home-assistant.io` redirect works to `https://localhost:<port>` with a private CA trusted in the Windows store, instance URL set per browser | Pattern 5.4, Pitfall 18 | Google sign-in cannot complete; sign in via HTTP localhost on Dev |
| A9 | A published-but-unverified Google app issues non-expiring refresh tokens (HA docs say "Publish app" avoids the 7-day expiry; Google's page does not address this case) | Pattern 5.1 | Weekly re-sign-in; D-10 degrades to the documented fallback |
| A10 | `playwright install --with-deps chromium` works inside WSL Ubuntu for guide screenshots | Code Examples | Screenshots taken from a Windows-side browser instead |
| A11 | Google's secret iCal address exists for every chosen calendar (only owners can see it) and its feed is fresh enough for a safety backup; Google documents no refresh interval | D-30 backups | Backup misses recent edits or is unavailable for shared calendars; use the HA-API JSON snapshot supplement and decide with the developer |
| A12 | Restoring one event from an `.ics` works via Google Calendar's Import (Settings > Import & export) | D-08 docs | Restore instructions wrong; test once with a throwaway calendar |
| A13 | Windows Task Scheduler "run as soon as possible after a scheduled start is missed" and `schtasks`/`powercfg` options behave as assumed on her laptop's Windows build | Host layer 5, 6 | Refresh misses a day; manual `refresh-preview` remains |
| A14 | Windows random-hardware-address setting is what breaks DHCP reservation, and turning it off per network fixes it | Host layer 7 | Reservation drifts; check the router's client list |
| A15 | Package legitimacy SUS verdicts (aiohttp, PyYAML, playwright, homeassistant) are data artefacts | Package Legitimacy Audit | Human-verify checkpoint is already required |

## Open Questions

1. **Does the laptop's current WSL build publish Docker ports to the LAN in mirrored mode?**
   - Known: reports of success for LAN clients; 2.9.x regression report; `hostAddressLoopback` for host-side access.
   - Unclear: this laptop's WSL version and behaviour.
   - Recommendation: first executable laptop checkpoint right after compose exists; follow the fallback ladder; record `wsl --version`.

2. **Does a Scheduled Task `wsl.exe -e sleep infinity` keep Preview up reliably across idle and sleep/resume on her laptop's WSL build?**
   - Known: only reported working approach (#13416, still open).
   - Unclear: behaviour after Windows sleep, hibernate and Windows Update restarts.
   - Recommendation: checkpoint over one overnight cycle before the first UAT with her; document the agreed-times model (D-03).

3. **Is the secret iCal address available for every chosen Google calendar?**
   - Known: it exists in Google Calendar settings under Integrate calendar; Google's page gives no refresh interval and no statement about calendars you do not own.
   - Unclear: whether each calendar the developer chooses is owned by him.
   - Recommendation: the Google checkpoint lists each calendar and its backup method; where no iCal address exists, either the developer asks the owner, or the HA-API JSON snapshot is the stated backup (developer's call); hard stop otherwise (D-30).

4. **Who owns the chosen real calendars, and does the developer's account have writer access to all of them?**
   - Known: read-only calendars get no create/delete automatically.
   - Unclear: the actual list (kept in the gitignored family file).
   - Recommendation: the family-file schema records `calendar_id`, `person`, `writable`, and `expect_events`; the seed refuses to write tagged events to a calendar not marked writable.

5. **Does Android's PKIX validation honour the IP name constraints on the CA?**
   - Known: a name-constrained CA was reported working in issue #5565 (2026-10-28 research); CA verified with `openssl`.
   - Unclear: her phone/ROM.
   - Recommendation: part of the phone checkpoint; fallback is regenerating an unconstrained CA (mkcert-style) for the home LAN only, a recorded trade-off.

6. **After a reset, does the Android app need only a re-login or re-adding the server (D-27)?**
   - Recommendation: checkpoint on her phone during the first `reset-preview` rehearsal; write the result into the guide.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker CLI + Compose | compose tooling | CLI only: Docker 29.9.2, Compose 5.6.1; **daemon not running** in this sandbox | 29.9.2 / 5.6.1 | Compose files verified via `docker compose config`; running containers is a laptop checkpoint |
| Python 3.14 via `uv` | seed tool, pip HA | yes (venv at `~/.cache/fh-hassfest/venv`, CPython 3.14.9, HA 2026.10.4) | 3.14.9 | -- |
| System Python | -- | 3.13.17 (too old for HA 2026.10) | 3.13.17 | use `uv` 3.14 |
| Node | not needed this phase | v22.22.0 | -- | -- |
| `openssl` | certs | yes | 3.0.13 | `mkcert` on the laptop |
| `git` | `git archive` deploy | yes | -- | -- |
| Playwright + Chromium | screenshots | installed and launched in this session | 1.64.1 | manual phone captures |
| ghcr.io / PyPI | image pull / pip | reachable (outbound HTTPS via agent proxy) | -- | -- |
| Windows 11 22H2+ laptop, WSL2, mirrored networking, Hyper-V firewall | D-23 | **not available here, untested** | -- | Fallback ladder; human-verify checkpoint |
| Google account / OAuth client | D-07 | not available here | -- | Local Calendars (seed default when no Google file) |
| Android phone with Companion | D-06, ACCESS-* | not available here | -- | none: human-verify checkpoint |

**Missing dependencies with no fallback:** the Windows laptop WSL host layer, her Android phone, and the developer's Google Cloud project; all are human-verify checkpoints.
**Missing dependencies with fallback:** Docker daemon (pip-installed HA for automated seed tests), Google (Local Calendar provider in the example family file).

## Validation Architecture

Skipped: `workflow.nyquist_validation` is `false` in `.planning/config.json`. Within the plan, still require: pure-function tests for the D-11 tag matcher, one live Local Calendar test in a pip-installed HA 2026.10.4, a reset test (seed, mutate, reset, assert equal and `family_hub_backups/` empty), and `deploy-preview` served-hash assertions. Phase 3 owns the formal test suite.

## Security Domain

Security enforcement is enabled (`security_enforcement: true`, ASVS level 1, block on high).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | HA accounts; generated per-environment passwords in `dev/.ha-secrets/` (0600, ext4 only); no stored tokens (login flow); distinct from Home; `ip_ban_enabled` default true |
| V3 Session Management | yes | HA tokens; seed never stores tokens; her session is wiped by reset (Pitfall 11) |
| V4 Access Control | yes | Her account is non-admin (`system-users`); admin-gated Family Hub commands; `--target` allow-list and `location_name` check refuse Home |
| V5 Input Validation | yes | Seed validates the family file against a schema; exact tag matching; HA enforces websocket schemas |
| V6 Cryptography | yes | `openssl` CA with name constraints; keys 0600; `ssl_profile` default `modern`; seed verifies TLS against the CA file, never `verify=False` |
| V8/V9 Data protection & Communications | yes | HTTPS on the LAN; Google OAuth token, secret iCal URLs and OAuth client secret are secrets (0600, outside git, outside the HA volume) |
| V14 Configuration | yes | Pinned image tag; no `privileged`, no host network; Dev loopback; ignore rules cover `dev/.ha-*`, `dev/host.env`, `tools/seed/*.local.*` |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Seeding/deleting events on the wrong Google calendar or untagged real events | Tampering | Exact tag + marker + env + date window + calendar allow-list, dry-run default, `.ics` backup (hard stop), loud delete warning in Dev/Preview, diff sync so deletes are rare (D-08, D-09, D-11) |
| Google refresh token theft from the laptop (read/write family calendars) | Information disclosure / Tampering | 0600 files outside git and the HA volume; disk encryption; revoke at myaccount.google.com if lost; the OAuth app is unverified so only the developer's account can consent |
| Preview reachable on hostile Wi-Fi | Spoofing / Elevation | Dev loopback bind; Hyper-V rule only for 8124; `preview-down`; strong passwords; no port-forward; optional remote-address limit on the rule |
| Broad WSL inbound allow (`-DefaultInboundAction Allow`) | Elevation | Use a per-port Hyper-V rule instead |
| Name-constrained CA key compromise | Spoofing | Constraint to private ranges + localhost; key 0600 on the laptop only; `ca.crt` only on phone and Windows store |
| Seeder pointed at Home with real credentials | Tampering / Information disclosure | `--target dev|preview` allow-list, host allow-list, `location_name` assertion before auth, separate passwords |
| Real notification to a family phone from Preview | Repudiation / DoS | `notifyTargets` allow-list check on every deploy/reset/refresh; no `media_player`; discovery integrations omitted |
| Secrets/family names committed to the public fork | Information disclosure | `.gitignore` for the local family file (holds real names, calendar ids and secret iCal URLs), env files, certs, backups, preserved entry; invented names in the example file; screenshots from seeded data |
| Real events on family phones (buzz) | Annoyance (accepted, D-25) | `[PREVIEW]` tag in the title; week-anchored creation; no daily churn |

## Sources

### Primary (HIGH confidence)
- Real HA Core 2026.10.4 run on 2026-10-28 (onboarding, users, Local Calendar/To-do, Family Hub flow, dashboards, resources, `application_credentials`, `http/config`, user data, Chromium render) and spot re-run 2026-11-02 (onboarding, `mobile_app` registration, `lovelace/resources/create|update`, `config/core/update`, pending HTTP config). HA source read at `~/.cache/fh-hassfest/core` (2026.10.4): `components/http/config.py`, `http/websocket_api.py`, `lovelace/resources.py`, `lovelace/websocket.py`, `lovelace/__init__.py`, `config/core.py`, `google/const.py`, `google/calendar.py`, `mobile_app/manifest.json`, `default_config/manifest.json`, `helpers/instance_id.py`.
- This repository (read this session): `custom_components/family_hub/__init__.py` (themes :385-410, `DEFAULT_GLOBAL_THEME_ID` :1571, resource registration :12190-12262, static paths :12553-12561), `config_flow.py` constants, `const.py` constants, `chores_websocket_api.py` command schemas, `card/family-week-calendar-card.js` (delete flow :23684-23700, weather :13291-13318, `</ha-card>` :16077), `card/family-hub-pantry-card.js` header, `versions.env`, `hacs.json`, `manifest.json`, `.gitignore`.
- Compose rendering via `docker compose config` and Playwright/Chromium caching experiment, both run in this session.
- https://learn.microsoft.com/en-us/windows/wsl/networking (mirrored mode, Hyper-V firewall commands and VMCreatorId GUID, fetched 2026-11-02)
- https://learn.microsoft.com/en-us/windows/wsl/wsl-config (`.wslconfig`/`wsl.conf` keys and defaults, fetched 2026-11-02)
- https://www.home-assistant.io/integrations/google/ (Web credentials, redirect URI, Publish app, fetched 2026-11-02)
- https://developers.google.com/identity/protocols/oauth2 (refresh token expiration, fetched 2026-11-02)
- https://www.home-assistant.io/installation/linux (Engine >= 23.0.0, Desktop unsupported)

### Secondary (MEDIUM confidence)
- https://github.com/home-assistant/android/pull/7044 (user-CA fallback, merged 2026-06-18) and https://github.com/home-assistant/android/issues/7346 (intermediate-chain failure on 2026.6.5, open), fetched 2026-11-02
- https://github.com/microsoft/WSL/issues/10494, /10926, /40984 and https://github.com/microsoft/wsl/issues/13416 (Docker in mirrored mode; systemd does not keep WSL alive), fetched 2026-11-02
- https://support.google.com/calendar/answer/37648 (secret iCal address; no refresh interval stated)
- https://developers.home-assistant.io/docs/api/native-app-integration/sending-data (webhook 410 means re-register, via search)
- https://github.com/home-assistant/android/issues/5565 (user-CA failures on e-OS/LineageOS; name-constrained CA workaround; 2026-10-28 research)
- https://companion.home-assistant.io/docs/troubleshooting/faqs (multi-server sensor note; 2026-10-28)

### Tertiary (LOW confidence)
- WSL clock-drift threads (https://github.com/microsoft/WSL/issues/8204, /4149, https://github.com/stuartleeks/wsl-clock), via search only
- Third-party guides for Windows "Random hardware addresses" (e.g. https://www.elevenforum.com/t/turn-on-or-off-random-hardware-addresses-for-wi-fi-networks-in-windows-11.4535)
- Companion "failed to perform ssl handshake" community report (June 2026), unresolved

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH for HA/Python/aiohttp (installed and run); MEDIUM-LOW for the Windows/WSL2 Docker host layer (documentation and issue reports only).
- Architecture (seed order, dashboard, sidebar, HTTP promote, Google entry preservation, resource update): HIGH, executed against the pinned HA.
- Pitfalls: HIGH for items reproduced (HTTP revert, readiness, auth failure without credential, theme-builder panel id, stale JS on soft reload); MEDIUM/LOW for WSL, Android and Google behaviour.

**Research date:** 2026-11-02
**Valid until:** 2026-11-09 (7 days: WSL 2.9.x networking regressions and the Android Companion trust handling are moving; HA ships monthly). Re-verify when `HA_VERSION` or the laptop's WSL version changes.
