# Project Research Summary

**Project:** Family Hub (Future-Bridge-AI fork of JVarhol/HA-Family-Hub, HA custom integration `family_hub`)
**Domain:** Customising a forked Home Assistant custom integration (HACS, vanilla-JS Lovelace cards) with Dev / Family Preview / Home environments, a test and CI safety net, and a family-led change loop
**Researched:** 2026-10-26
**Confidence:** MEDIUM overall (STACK HIGH; ARCHITECTURE MEDIUM-HIGH; FEATURES and PITFALLS MEDIUM)

## Executive Summary

This is a brownfield project. The integration (about 13k lines of Python in `__init__.py`, about 66k lines of vanilla-JS cards, only `card/` and `panel/` served) already works. The milestone is not about new runtime features. It is about making the codebase safe to change, giving the non-technical product owner (the developer's wife) a real place to try changes, and then running a repeatable loop: she asks, we build in Dev, deploy to Preview, she signs off, and only then a tagged release goes to Home. Experts running HA custom integrations do this with a pinned HA container for dev and preview, a pytest harness built on `pytest-homeassistant-custom-component`, HACS installs from release tags, and API-driven seeding rather than hand-edited storage.

The recommended approach is a strict order: clean foundation first (delete the stale root-level duplicate cards and truncated translation files, untrack `__pycache__`, fix fork identity and version scheme), then a separate always-on Preview HA instance seeded through public APIs with date-relative data and a one-command deploy and reset, then the test and CI safety net, and finally the family feedback loop with release tagging. The safety net must come before any feature work touches the monoliths. Preview must be a separate HA instance (its own `core.uuid`, bridge networking, no real notify targets, no real calendars). Home only ever installs release tags.

The main risks are concrete and verified in the repo. Preview can share identity or notification targets with Home if built carelessly. A reset that only deletes `.storage` is undone by `store.py`, which restores `family_hub_backups/` when primary storage is empty. Root-level `.js` and `.json` copies are being edited upstream and have content that appears nowhere else, so they must be triaged before deletion, not just removed. The first hassfest and HACS run will almost certainly be red and must be spiked early, not discovered in the last phase. The declared minimum HA version (2024.1.0 in `hacs.json` and PROJECT.md) is already wrong for the code's `StaticPathConfig` usage and has to be decided in Phase 1.

## Key Findings

### Recommended Stack

Tooling only. The runtime stack (Python on HA Core APIs, vanilla JS web components, no bundler, no Python dependencies) does not change, and nothing new ships to users. All tooling lives outside `custom_components/family_hub/`.

- **Python 3.14 + `pytest-homeassistant-custom-component` 0.13.375** (pins `homeassistant==2026.10.4`, `pytest==9.0.3`): real HA fixtures (`hass`, `MockConfigEntry`, `hass_ws_client`). Requires Python >= 3.14; use `uv python install 3.14` locally and `actions/setup-python` in CI. Spiked on CPython 3.14.9.
- **Home Assistant container pinned to `2026.10.4`** for both Dev and Preview, the same tag the test plugin resolves to. Pin exactly, never `:stable` or `:latest`. Bump Preview first, then Home.
- **Docker Engine + Compose v2** (not Docker Desktop) on an always-on Linux host for Preview. Bridge networking with an explicit port, no `network_mode: host`, no `privileged`.
- **`ruff` 0.17.2, narrow rule set** `E4,E7,E9,F,B`: 9 findings today. Do not enforce `ruff format` or `E501`/`UP` yet (1,700+ findings, 25-file rewrite).
- **Vitest 5.0.5 + jsdom 30.1.3** for card smoke tests (spiked: 12 of 14 card and panel modules defined and rendered with zero errors against a mocked `hass`). Node 24 in CI. **Playwright 1.64.1** only for screenshots and layout, not logic.
- **ESLint 10.13.0** with `no-undef` as the JS gate (spiked: no parse errors, no `no-undef`). Turn off `no-empty`, `no-useless-assignment`, `no-useless-escape`, `no-control-regex`; fix the two `no-func-assign`.
- **`aiohttp`** in the seed tooling, in the same `uv` environment as the tests (user creation is WebSocket-only).
- **GitHub Actions:** `actions/checkout@v7`, `setup-python@v7`, `setup-node@v7`, `astral-sh/ruff-action@v4`, `hacs/action@main` (`category: integration`), `home-assistant/actions/hassfest@master`.
- **Brand assets already exist** (`custom_components/family_hub/brand/icon.png` etc.), so the HACS `brands` check should pass.

### Expected Features

Scope note: the existing feature set (calendar views, chores, rewards, goals, routines, to-dos, recipes, timers, screensaver, PIN, child accounts, reminders, themes, i18n) is validated and out of scope. The features below cover the Preview, feedback, and release workflow, plus the candidate backlog.

**Must have (Preview milestone):**
- Date-relative seeded data (events, meals, chores, rewards as offsets from "now") plus one-command `reset-preview`.
- Preview isolation: no real notifications, speakers, or calendars. Null or Preview-only `notify.*` target, no `mobile_app` devices, Grocy disabled.
- Always-on Preview at a stable LAN address. Remote access deferred.
- One-tap access on her phone (Companion app as second server, or home-screen or kiosk bookmark) with an unmistakable "PREVIEW" identity.
- Non-admin user for her with a Family-Hub-only dashboard and hidden sidebar. HA does not hide other dashboards from non-admins by default, so this needs explicit setup and a test logged in as her.
- `deploy-preview <branch>` followed by a plain-language "what changed, where to tap" message.
- Plain-language "Getting started" guide in `docs/family/` with screenshots from seeded Preview.
- Request template with "I do / I see" acceptance criteria and a three-answer UAT outcome (works / does not work / works but confusing). Sign-off checklist before anything reaches Home.
- Before the first Home release: tagged release, HA backup, rollback plan. `whats-new.md` with the first release.

**Should have (after she has used the loop once or twice):**
- Visible build stamp (version and content hash) in the UI.
- Playwright before/after screenshots, reusing seed data.
- Wall-tablet kiosk trial in Preview.
- Her own priority ranking of the backlog.

**Defer (her call, or v2+):**
- Edit an existing calendar event. The **most likely top gap** (DOCUMENTATION.md says only delete is supported; the info popup cannot change summary, time, or location). Touches the calendar monolith, so it needs module extraction and tests first. Confirm with her in week one of Preview rather than assuming.
- Month-view meal drag-to-reorder (Week view Edit mode already supports it).
- Finishing the Theme Builder panel (unfinished and undocumented; lowest priority unless she ranks it high).
- In-app "What's new" card, seed scenarios, ICS school-calendar import, photo screensaver (check first whether the existing screensaver does photos).

**Anti-features:** custom in-app feedback form with a backend; forcing her to use GitHub; self-updater on Home (no checksum, bypasses sign-off gate); per-branch preview environments; copying real family data into Preview; giving her an admin account; auto-promote or CI deploy to Home; auto-generated changelogs as "what's new"; AI paper-schedule scanning (cloud, violates locality).

### Architecture Approach

Three HA instances run the same code at different trust levels, sharing nothing at runtime (no volume, network, credentials, or calendars). They share only git code and seed-data definitions. Dev is a bind-mount of the working copy for live editing. Preview receives an exported copy of one git ref (`git archive` or rsync `--delete`), then a restart. Home receives only GitHub release tags via HACS. The integration package stays the only deployable artefact; tooling sits in `dev/` (compose overlays), `tools/seed/` (Python seeding through public HA APIs), `scripts/` (thin wrappers), and `tests/` (outside the package, so HACS never ships it).

**Major components:**
1. **Compose base + overlays** (`dev/compose.yaml`, `compose.dev.yaml`, `compose.preview.yaml`): one image tag, one `configuration.yaml` template; only mounts, port, and restart policy differ.
2. **Seed engine** (`tools/seed/`): onboards a fresh volume via `POST /api/onboarding/users`, creates users via WebSocket, Local Calendar and Local To-do via the config-flow REST API, events via `calendar.create_event`, to-do items via `todo.add_item`, and Family Hub data via the integration's own `family_hub/*` commands and services. Never writes `.storage` of a running HA. A hard `--target` allow-list (`dev|preview`) refuses Home.
3. **Deploy and reset tools:** `deploy-preview` (fetch ref, export, replace integration directory, restart, wait for `/api/onboarding`, verify served hash and stamp). `reset-preview` (stop, delete the **entire** config volume including `family_hub_backups/`, re-render template, start, onboard, seed).
4. **Test layers:** L0 static guards (`scripts/check-guards`: no stray `.js` outside `card/` and `panel/`, no tracked `.pyc` or `*.bak*`, translation key parity, manifest version format); L1 engine unit tests on dicts; L2 WebSocket and Store tests with permission checks, PIN lockout, migration fixtures; L3 setup smoke (`async_setup_entry`, registered `family_hub/*` commands compared to a checked-in `ws_commands.json` contract, 8 services, card URLs served, clean unload); L4 card smoke (jsdom or Playwright with mocked `hass`); L5 E2E screenshots against live Dev or Preview, not PR-blocking.
5. **Strangler extraction:** new logic in `<feature>_engine.py`; new websocket commands in `<feature>_websocket_api.py` with one `async_register(hass)` call from `__init__.py`; new card code in new files under `card/`. First extraction is `frontend.py`: table-driven registration of the 14 card and panel resources, replacing about 200 lines of repeated code. Move-only commits land separately and only after a characterization test covers the moved code.
6. **Release pipeline:** `release.yml` on tag `vX.Y.Z` verifies tag equals `manifest.json` version, reruns CI, and creates a GitHub Release with notes from `whats-new.md`. Home updates from HACS pointed at the fork (switch once, after a full HA backup).

### Critical Pitfalls

1. **Preview shares identity with Home.** Copying Home's config copies `.storage/core.uuid`, so the Companion app treats both as one server. Never clone Home's `config/`. Onboard Preview fresh by script. Give it a loud name ("Family Hub PREVIEW"), a distinct theme, its own port (8124), and bridge networking. Add Preview as a second server, never replace Home.

2. **Preview notifications and reminders reach real phones and speakers.** The integration auto-discovers `notify.mobile_app_*` per user (`__init__.py` around line 1971) and a 5-minute poller fires reminders. Set the per-person notify mapping explicitly to `notify.persistent_notification` in seed. Install no media players; disable discovery components (`ssdp`, `zeroconf`, `dhcp`, `bluetooth`) in Preview. `deploy-preview` and `reset-preview` should fail if any `notify.*` or `media_player.*` service outside an allow-list exists.

3. **Reset is undone by the integration's own backups.** `store.py` restores from `family_hub_backups/` whenever a Store loads empty (verified in repo), so a reset that deletes only `.storage` resurrects old data. HA also flushes in-memory Stores on shutdown, so editing `.storage` under a running instance is overwritten. Fix: `docker compose down`, delete the whole config volume, re-render from template, re-seed through public APIs. Acceptance test: seed, mutate, reset, confirm state equals seed and `family_hub_backups/` is empty. Dev reset must clear backups too.

4. **Root-level duplicates hold content that exists nowhere else.** Root `.js` copies differ from served copies by thousands of lines (2,531 in the calendar card). Root `de` and `es` JSON hold 9 keys found in no served card and no `translations/` file (orchestrator-verified). Upstream commit `8f7172d` edited root copies again. Fix: reviewed diff per root file, port anything wanted into `card/`, `panel/`, `translations/`, then delete in its own commit. Add a CI guard rejecting `*.js` outside `card/` and `panel/`.

5. **Card missing or stale on Preview, and nobody can tell.** Resource auto-registration is best-effort and silently no-ops on YAML-mode or changed Lovelace internals. Seed should create a storage-mode dashboard and register resources through `lovelace/resources/create`. Verify by reading `lovelace/resources` back and checking served `?v=<hash>` matches the repo file. Show a build stamp in the UI. Companion WebViews and wall tablets keep long-lived pages, so a refresh step is part of every UAT.

Also critical: **hassfest and HACS will fail on the first run.** Expect manifest key ordering, the non-standard `fh_ui` translation category, string rules (leading spaces, URLs, HTML in `translations/en.json`), `codeowners` format, Issues disabled on the fork, and missing description and topics. Spike early in Phase 1 to get the real list. Do not blanket-apply `continue-on-error`.

## Implications for Roadmap

Four phases, per PROJECT.md. The ARCHITECTURE build order (steps 0 to 10) compresses into these. Granularity is coarse.

### Phase 1: Clean foundation (invisible to the family)

**Rationale:** Every later step depends on this. Duplicated root files, stale translations, and wrong fork identity would ship to Preview and make edits land in dead files. HACS and hassfest cannot go green until manifest and identity are fixed.

**Delivers:**
- Triage of root-level duplicates (diff, port, then delete in a separate commit). Root `icon.png` stays where `ICON_URL` serves it; only `icon (1).png` goes, after a checksum compare.
- Translations: `git mv` `it`, `nl`, `pl`, `pt`, `pt-BR` into `translations/` (exact key parity with `en.json` already verified). Port the 9 orphan keys from root `de` and `es`, then delete the truncated root `de`, `en`, `es`, `fr`. Delete `strings.json` (custom integrations never read it). Do not rename the `fh_ui` category.
- Untrack the 49 `__pycache__/*.pyc` files (own commit); `.gitignore` entries for `.env`, `*.bak*`, `family_hub_backups/`, `.storage/`.
- Repo hygiene: rename or drop `\Screenshots/` (grep for references); delete the empty `custom_components/family_hub/readme.md` (verify HACS still shows root README).
- Fork identity: change only `manifest.json` `documentation`, `issue_tracker`, `codeowners` (replace `@bordello_labs` with the real handle), README badges and HACS links, Docusaurus `url`, `baseUrl`, `organizationName`, `projectName`. Keep `domain`, `name`, runtime identifiers, card tags, upstream credit, GPLv3.
- Decisions recorded: version scheme (recommend continuing upstream numbering, next release `1.169.0`, strictly monotonic above 1.168.85); minimum HA version (raise `hacs.json` to the tested version; update PROJECT.md's ">= 2024.1" constraint); one `versions.env` with the pinned HA tag.
- Spike: run hassfest and HACS validation on a throwaway branch; record the failure list.

**Addresses:** FEATURES foundation items; Active requirements for clean foundation.
**Avoids:** Pitfalls 4, 8, 9, 10, 14, 21, 22, 25, 26-28.

### Phase 2: Dev + Family Preview (first thing she sees)

**Rationale:** First user-visible milestone and the critical path to her involvement (ARCHITECTURE: 0, then 2, 3, 4, 5). Dev and Preview share compose base and seed, so build both together. The test harness (Phase 3) can start in parallel once Phase 1 is done.

**Delivers:**
- `dev/` compose base and overlays, pinned `ghcr.io/home-assistant/home-assistant:2026.10.4`, Dev on port 8130, throwaway volume under `dev/.ha-dev/` (gitignored), bind-mount of working copy.
- Preview on an always-on LAN Docker host (not the laptop, not co-hosted with Home), port 8124, bridge network, `restart: unless-stopped`, own volume, `homeassistant: name: "Family Hub PREVIEW"`, distinct theme, discovery components disabled. Same `TZ`, language, units as Home.
- `tools/seed/`: onboarding (fresh volume only), users (hers non-admin), Local Calendar per member, Local To-do lists Family Hub needs, relative-date events, Family Hub data via its own commands, storage-mode dashboard, card resources registered and verified. `--target` allow-list `dev|preview`.
- `deploy-preview <ref>` (`git archive` export, replace integration directory, restart, wait, verify hash and stamp) and `reset-preview` (full volume wipe, re-seed, backups cleared).
- Build stamp in UI and `console.info`.
- Her access: second Companion server (or kiosk bookmark) on a stable LAN address, tested on a spare phone as her non-admin user. Getting-started guide with Preview screenshots.
- End-to-end test of the first trivial visible change.

**Implements:** Seed engine, deploy and reset tools, Preview identity and isolation.
**Avoids:** Pitfalls 1, 2, 3, 5, 6, 11, 17, 18, 19, 20, 30, 31.

**Research flag:** NEEDS `/gsd-plan-phase --research-phase`. Open: whether `lovelace/dashboards/create` plus `lovelace/config/save`, or a YAML-mode dashboard with storage root, works for auto-registration; which `family_hub/*` commands can seed chores, rewards, meals, and PINs without a kiosk session; driving the 11-step Family Hub config flow with `member_profile` loops; HTTPS secure-context differences; reproducible non-admin dashboard and sidebar setup.

### Phase 3: Safety net (tests and CI)

**Rationale:** Gate before feature work touches a monolith. The calendar card (31k lines) and `__init__.py` (13k lines) have no tests, and the edit-event work in Phase 4 requires changing them. Engine tests are cheap and can start after Phase 1. Setup-smoke and the WebSocket contract must exist before any extraction.

**Delivers:**
- Python 3.14 via `uv`; `requirements_test.txt` pins plugin and ruff; `pytest.ini` with `asyncio_mode = auto`; `conftest.py` with autouse `enable_custom_integrations`; root `package.json` (devDependencies only, not shipped).
- Ordered tests: (1) trivial import of `chore_engine` green on pinned versions; (2) engine tests for chore, reward, goal, routine, timer on plain dicts with `freezer` (week, month, DST boundaries); (3) WebSocket and Store tests with frozen migration payloads; (4) setup smoke with `ws_commands.json` contract and unload at test end. Coverage reported, no global gate.
- JS: Vitest with a fresh `JSDOM` per card, stubbed `ResizeObserver`, `window.close()`, fake timers, shared `hass` mock. Smoke covers the 12 spiked cards; the two unresolved modules (`family-hub-my-chores-card.js`, `theme-builder-panel.js`) need their `customElements.define` names checked first. Playwright screenshots are artifacts, not gates.
- Lint and guard: ruff narrow set (fix 9 findings in the same PR), ESLint narrow set, `scripts/check-guards`, translation key-parity test against `en.json` (`{brace}` placeholders hard-fail; `%n%` report-only with an allow-list of the 16 intentional differences).
- CI: `ci.yml` (lint, pytest, JS smoke, guards) and `validate.yml` (hassfest, HACS, daily cron). Make validation required only once green; no `continue-on-error`.

**Avoids:** Pitfalls 12, 13, 16, 23, 24, 25.

**Research flag:** Partly. Engine tests and CI skeleton are standard (skip research-phase). NEEDS research: hassfest failure list and the `fh_ui` exception decision (narrow exception recommended); per-card `hass` and `callWS` mock surface, derived from recorded traffic on seeded Dev.

### Phase 4: Family-led customisation loop

**Rationale:** Meaningful only once she can see something (Phase 2) and the release path is safe (Phase 3). Turns the process into a repeatable, auditable loop. Backlog ordering depends on her answers.

**Delivers:**
- Loop as a written process with checklist and `docs/RELEASING.md`: request (template, quoting her words) to "I do / I see" criteria she confirms, to build and test in Dev, to `deploy-preview`, to three-answer UAT with build stamp, to sign-off checklist, to merge, to manifest bump, to `whats-new.md`, to tag `vX.Y.Z` (must equal manifest), to `release.yml`, to HACS update on Home at a quiet time after a full HA backup.
- `release.yml` enforcing tag equals manifest; a script checking `CHANGELOG.md`, website changelog, and `whats-new.md` agree.
- Home HACS cut-over: remove upstream custom repository, add `Future-Bridge-AI/HA-Family-Hub`, install from release. Once, deliberately, after a full HA backup.
- Rollback rehearsal on Preview.
- Rolling extraction gated on Phase 3 smoke tests: `frontend.py` first, then any monolith region she asks to change. Edit-event (likely top request) becomes a new module with engine tests before UI changes.
- Candidate backlog reviewed with her: edit event, meal drag, Theme Builder, anything from week one.

**Avoids:** Pitfalls 10, 11, 15, 16, 29, and the mid-day release UX pitfall.

**Research flag:** Partly. Release and HACS mechanics are standard. Edit-event needs phase research once ranked (calendar card internals, Local Calendar editability, recurrence). Theme Builder needs research only if ranked high.

### Phase Ordering Rationale

- **Foundation before Preview:** duplicates and stale files would ship to Preview and make UAT meaningless; clean identity is needed for hassfest and HACS.
- **Preview before the full harness, but after engine tests start:** the first user-visible milestone is on the critical path and not gated on CI beyond the Phase 1 skeleton. Engine tests run in parallel with Phase 2.
- **Safety net before feature work:** no Phase 4 change to a monolith without a covering smoke or engine test.
- **Loop last:** release-to-Home needs the version scheme (Phase 1), CI (Phase 3), and an existing sign-off gate (Phase 2).

### Research Flags

Needs `/gsd-plan-phase --research-phase`: Phase 2 (dashboard and resource creation path; `family_hub/*` seeding commands and permission gates; config-flow driving; non-admin kiosk setup; HTTPS parity; Preview host hardware and Companion setup). Phase 3 (hassfest failure list and `fh_ui` exception; per-card mock surface; the two unresolved card modules). Phase 4 (edit-event implementation once ranked; HACS repository switch on Home).

Standard patterns (skip research-phase): Phase 1 file triage, manifest and docs edits (the hassfest spike is itself the research); Phase 3 engine and pytest bootstrap (spiked); Phase 4 release mechanics (documented).

## Conflicts Between Research Files (resolved)

| Topic | Conflict | Resolution |
|-------|----------|------------|
| Card JS testing | STACK: Vitest + jsdom for smoke (spiked). ARCHITECTURE and PITFALLS: Playwright for all JS. | jsdom + Vitest for logic smoke; Playwright only for screenshots and layout. Revisit if jsdom fails on the two unresolved modules. |
| Dev port | STACK: 8123. ARCHITECTURE: 8130. | 8130, so Dev, Preview (8124), and Home (8123) never share an origin or `localStorage` token. |
| Preview remote access | STACK: Tailscale. ARCHITECTURE: LAN v1, Tailscale optional v2. | LAN-only for v1; Tailscale later if needed. Never Nabu Casa for Preview. |
| Seed location | STACK: `scripts/seed_preview.py`. ARCHITECTURE: `tools/seed/`. | `tools/seed/` with thin `scripts/` wrappers. |
| Minimum HA version | `hacs.json` and PROJECT.md: 2024.1. Code needs `StaticPathConfig` (about HA 2024.7). | Raise to tested version; update PROJECT.md constraint. Decide in Phase 1. |

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified against registries on 2026-10-26; four recommendations spike-tested. Gap: hassfest not run locally. |
| Features | MEDIUM | Workflow recommendations are general practice adapted to a household. Competitor claims are vendor content (LOW-MEDIUM). |
| Architecture | MEDIUM-HIGH | HA onboarding, auth, HACS verified against HA source and docs. Companion, Tailscale, sizing are training knowledge. |
| Pitfalls | MEDIUM | Repo-verified items HIGH (duplicates, translations, backup restore, notify discovery). HA runtime behaviour MEDIUM. |

### Gaps to Address

- **hassfest and HACS first-run failures:** spike at end of Phase 1; use output to size Phase 3.
- **`fh_ui` category vs hassfest:** narrow exception recommended for this milestone; confirm in Phase 3 spike.
- **Root `de`/`es` orphan keys (9) and root `fr`/`en`:** port the 9 keys; triage root `fr`/`en` the same way before deletion (orchestrator confirmed only `de`/`es` counts).
- **Dashboard creation path:** storage-mode via `lovelace/dashboards/create` vs YAML-mode with storage root. Spike on throwaway Dev.
- **Family Hub seeding commands:** confirm which `family_hub/*` commands can create chores, rewards, goals, routines, PINs, meals, and which need kiosk elevation.
- **Config-flow automation:** member to user to calendar mapping step IDs and field names must be validated by driving the flow.
- **Two unresolved card modules:** `card/family-hub-my-chores-card.js` and `panel/theme-builder-panel.js` did not register a `window.customCards` entry; check their `customElements.define` names.
- **Secure-context dependencies:** which card behaviours need HTTPS; whether Home is on HTTPS.
- **Preview host hardware:** a decision input, not research.
- **Python 3.14 on the developer machine:** confirm laptop or devcontainer provides it (`uv` pin).
- **Edit-event scope:** confirm with her in Preview week one.
- **Preview remote access:** LAN-only is the working assumption; confirm.

## Sources

**Primary (HIGH):** `.planning/PROJECT.md`; repository inspection 2026-10-26 (`store.py`, `__init__.py`, `manifest.json`, `hacs.json`, `card/`, `panel/`, `translations/`, `strings.json`, `.gitignore`, `DOCUMENTATION.md`, commit `8f7172d`); orchestrator-verified facts (translation parity 2,139 keys; root `de`/`es` truncated, 1,019 keys, 9 orphan keys; `store.py` backup restore; edit-event unsupported); PyPI and npm registry reads; HA core source (`onboarding/views.py`, `config/auth.py`, `local_calendar`/`local_todo` config flows, `pyproject.toml`); HACS publishing docs; HA Docker install docs.

**Secondary (MEDIUM):** HA contributor docs on custom-integration translations; HA Companion multi-server docs; HA community kiosk and non-admin threads; training knowledge flagged MEDIUM (Tailscale `serve`, Playwright `page.clock`, `async_register_static_paths` introduction).

**Tertiary (LOW):** competitor vendor and affiliate comparisons; generic UAT and release-note guidance; Fully Kiosk Plus licence cost (unverified); Playwright image tag convention (not fetched).

---
*Research completed: 2026-10-26*
*Ready for roadmap: yes (after the Phase 2 research-phase step closes the listed open questions)*
