# Family Hub (Future-Bridge-AI fork)

## What This Is

Our own home dashboard / family hub, built on a fork of the Home Assistant custom integration
[`JVarhol/HA-Family-Hub`](https://github.com/JVarhol/HA-Family-Hub) (domain `family_hub`, v1.168.85),
now hosted at `Future-Bridge-AI/HA-Family-Hub`. It runs entirely locally on Home Assistant and ships
its own Lovelace cards: a shared family calendar with meals, chores → stars → rewards, goals,
routines, to-do lists, recipes and pantry, timers, and a wall-tablet screensaver. We are
**customising and extending** it for our family, not building from scratch.

It is for two people working together: the **developer** (repo owner, building with GSD + Claude
Code) and the **family product owner** (the developer's wife, non-technical), who uses the app day
to day, asks for changes in plain language, and sees each change in a safe **Family Preview** before
it reaches the family's real setup.

## Core Value

The family product owner can use a working Family Hub every day and see each change she asks for
appear in a safe Preview before it reaches the family's real Home setup — without anything breaking
the real calendars and lists.

## Requirements

### Validated

<!-- Inferred from the existing codebase (.planning/codebase/). Shipped upstream and working. -->

- ✓ HA custom integration installable via HACS custom repository, config flow + options flow (`config_flow.py`, HA >= 2024.12.0) — existing
- ✓ Family week calendar card: Week / Month / Planner / Agenda views, meals, in-card Settings, More menu, Right Now bar (`card/family-week-calendar-card.js`) — existing
- ✓ Today and Right Now cards: at-a-glance today, presence, current/next event — existing
- ✓ Chores → stars → rewards, goals and routines with engines and cards (`chore_engine.py`, `reward_engine.py`, `goal_engine.py`, `routine_engine.py`, chores/my-chores/rewards/goals cards) — existing
- ✓ To-do card showing any HA `todo.*` lists side by side — existing
- ✓ Recipe box and pantry, with optional Grocy integration (`pantry_engine.py`, recipe-box and pantry cards) — existing
- ✓ Timers/alarms ringing on screens, phones and speakers (`timer_engine.py`, active-timers card) — existing
- ✓ Wall-tablet screensaver card and per-device (tablet) settings, Privacy / Discreet modes — existing
- ✓ Kiosk PIN sign-in, child accounts, per-person permissions — existing
- ✓ Reminders, HA-side notifications and Daily Digest via a ~5-minute backend poller — existing
- ✓ Settings persisted in HA `Store` with backups every 12h and restore when primary storage is empty (`store.py`) — existing
- ✓ ~60 `family_hub/...` websocket commands and 8 services (`create_chore`, `complete_chore`, `approve_chore`, `reject_chore`, `nudge_user`, `start_timer`, `cancel_timer`, `stop_timer_alarm`) — existing
- ✓ HA entities and device triggers for automations (sensor, switch, number, select, text, button, todo) — existing
- ✓ 10 built-in themes plus custom themes via theme selector card — existing
- ✓ i18n with full `de`, `en`, `es`, `fr` translations loaded by HA — existing
- ✓ Docusaurus docs site deployed by `.github/workflows/deploy-docs.yml` — existing

### Active

<!-- Milestone 1 scope, from docs/onboarding-findings.md. Hypotheses until shipped and validated. -->

**Clean foundation (invisible to the family)**
- [ ] Remove stale root-level duplicate card `.js` files and the `card/family-week-calendar-card.js.bak_divfix` backup, so edits can only land in the served `card/` and `panel/` copies
- [ ] Make translations consistent: move `it`, `nl`, `pl`, `pt`, `pt-BR` into `translations/` after a key-parity check against `translations/en.json`; delete the stale, truncated root `de`/`en`/`es`/`fr.json`
- [ ] Untrack the 49 committed `__pycache__/*.pyc` files
- [ ] Repo hygiene: rename `\Screenshots/` (or drop it if redundant with `images/readme/`), dedupe icon/logo files, remove the empty `custom_components/family_hub/readme.md`
- [ ] Fork identity: `manifest.json` documentation / issue tracker / codeowners and README/HACS links point at `Future-Bridge-AI/HA-Family-Hub`, credit to the upstream author kept; versioning scheme decided

**Dev + Family Preview environments (first thing she sees)**
- [ ] Dev environment: Docker Compose (or devcontainer) running Home Assistant with this integration mounted from the working copy, plus demo seed data
- [ ] Family Preview: a separate, always-on HA instance with its own config volume, never connected to the real family calendars
- [ ] One-command `deploy-preview` that installs `custom_components/family_hub` from a chosen branch and restarts Preview HA
- [ ] Scripted seed data: Local Calendar per family member, the required `todo.*` lists, a realistic week of events, meals, chores, rewards, and HA users per family member (hers non-admin), plus a `reset-preview` command
- [ ] Her access set up (HA Companion app and/or bookmarked tablet kiosk dashboard) so it feels like an app, not a dev tool
- [ ] Plain-language "Getting started" guide in `docs/family/` with screenshots: what each screen is for and how to ask for a change
- [ ] She can open Preview herself, find today's plan, tick a chore and redeem a reward, and confirms she sees one trivial visible change the developer deployed

**Safety net before feature work**
- [ ] Python test harness (`pytest`, preferably `pytest-homeassistant-custom-component`) covering the pure engines first: chore, reward, goal, routine, timer
- [ ] JS smoke tests (jsdom or Playwright) that load each served card module and render it with a mocked `hass`
- [ ] Playwright screenshots of Preview, usable as before/after pictures for her
- [ ] CI on GitHub Actions: Python lint (ruff) + pytest, JS syntax check or tests for cards, HACS and hassfest validation

**Family-led customisation loop**
- [ ] A repeatable loop: she asks (in person or via the Family request issue template) → acceptance criteria written as things she will do and see → build and test in Dev → `deploy-preview` → she tries it and her answers are the UAT → release to Home only after her sign-off
- [ ] Jargon-free `docs/family/whats-new.md` entry (what changed, where to find it, screenshot) for every release to Home
- [ ] Early candidate backlog shown to her, with her deciding priority: Month-view meal drag-to-reorder, finishing the Theme Builder panel, anything from her first week in Preview

### Out of Scope

- Cloud services or a hosted backend — everything stays local on Home Assistant, matching the upstream design
- Testing changes directly on the real Home setup — all experiments go to Dev or Preview first; Home only receives changes she has signed off
- Using the real family calendars or lists in Preview — Preview uses seeded pretend data so trying things can't break anything
- Big-bang rewrite of `__init__.py` (~13k lines) or the calendar card (~31k lines) — new work extracts focused modules instead of growing the monoliths, but no wholesale refactor this milestone
- Getting into the default HACS store — remains installable as a custom repository
- Relicensing — derivative work stays GPLv3
- Treating `PROJECT_CONTEXT.md` as current truth — it is the upstream author's stale AI-handoff notes; used for rationale only

## Context

- **Brownfield fork.** Upstream is `JVarhol/HA-Family-Hub`; manifest, README badges and HACS links still point there (codeowner `@bordello_labs`). Codebase map in `.planning/codebase/` (mapped 2026-10-26).
- **Backend:** Python, ~25–29k lines, no dependency manifest (HA provides everything). `__init__.py` is the core monolith (setup, settings sync, calendar/meal logic, reminders, notifications, Grocy client, theme registry, backups, static path + dashboard resource registration around line 12500). Domain engines raise domain errors (`ChoreError`, `RewardError`, `GoalError`, `RoutineError`, `TimerError`, `PantryError`, `UpdateError`) that websocket handlers return via `connection.send_error`.
- **Frontend:** vanilla JS web components, no bundler, ~66k lines. **Only `card/` and `panel/` are served**; root-level copies are older and edits to them have no runtime effect (the latest upstream upload commit `8f7172d` edited root copies). Cards poll every 60s; card JS is cache-busted by content hash.
- **Translations:** HA loads only `translations/*.json` (`de`, `en`, `es`, `fr`). `it`, `nl`, `pl`, `pt`, `pt-BR` exist only at the integration root and are not loaded, despite the README advertising them.
- **No tests, no code CI.** `PROJECT_CONTEXT.md` describes ~15–20 Python test files, a fake `homeassistant` stub and jsdom JS tests; none are committed. Only the docs-deploy workflow exists.
- **Known concerns** (see `.planning/codebase/CONCERNS.md`): Grocy API key stored in plain config-entry options and Grocy URLs not forced to HTTPS; self-updater has no checksum/signature check; ~390 `innerHTML` uses with inconsistent escaping; ~145 broad `except Exception`; manifest version 1.168.85 vs changelog stopping at v1.135.4; `CHANGELOG_ARCHIVE.md` referenced but missing.
- **Runtime requirements:** at least one `calendar.*` entity, `todo.*` entities for recipe box / meal plan / templates / suggestions / reminders (Local To-do works; some auto-created), a `notify.*` target. Most configuration lives in the calendar card's in-card Settings, synced via backend storage. `DOCUMENTATION.md` has card YAML.
- **Docs to trust:** prefer `README.md` and `DOCUMENTATION.md` for current behaviour; `PROJECT_CONTEXT.md` (~800 KB) for rationale only.
- **Known feature gaps** (from `DOCUMENTATION.md`): no drag-to-reorder of meals in Month view; Theme Builder panel unfinished and undocumented.

### Environments

| Environment | Who uses it | Data | How it gets updated |
|---|---|---|---|
| **Dev** | Developer | Throwaway demo data | Integration folder mounted from the working copy; restart HA for Python changes, hard-refresh for card JS |
| **Family Preview** | Wife + developer, on a real tablet/phone | Realistic seeded family data, never the real family calendars | `deploy-preview` from a branch, after checking in Dev |
| **Home** (production) | Whole family, wall tablet | Real calendars, real to-do lists | Only after she has tried the change in Preview and said yes |

## Constraints

- **License**: GPLv3 — the fork is a derivative work; distribution must stay GPLv3 and keep upstream credit
- **Platform**: Home Assistant custom integration, HA >= 2024.12.0 (declared in hacs.json; Dev, Preview and tests pinned to 2026.10.4 in versions.env), HACS custom repository — the install path the family setup already depends on
- **Tech stack**: Python on HA Core APIs (no extra Python deps), vanilla JS web components with no bundler — keep the existing build-free delivery
- **Locality**: everything runs locally; no cloud services — upstream design and family privacy
- **Safety**: Preview must be isolated from the family's real HA and real calendars — experiments must never break the real setup
- **Usability**: every phase from the Preview phase on ends in something she can try; acceptance criteria and UAT are written as things she does and sees in the app — she is non-technical and the real user
- **Code health**: changes to `__init__.py` or the calendar card prefer extracting focused modules over growing the monoliths — no tests exist yet, so large files are risky to change
- **Served paths**: only `card/` and `panel/` JS is served — edits must target those copies

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build on the upstream fork rather than greenfield | Mature, working feature set the family can use immediately | — Pending |
| Wife is the product owner; her Preview sign-off gates every release to Home | She is the real user; changes must be visible and trusted before reaching the family | — Pending |
| Three environments: Dev, Family Preview, Home | Experiments never touch the family's real setup | — Pending |
| Clean foundation first, then Preview, then tests/CI, then feature loop (Phase 3 may overlap Phase 2's tail) | Stale duplicates and translations make edits land in the wrong place; she should see a working app early | — Pending |
| Preview uses scripted seed data with a reset command | Repeatable, resettable, never the real calendars | — Pending |
| Where Preview runs (always-on home machine via Docker Compose recommended vs laptop) | Must be always-on for her | — Pending (decide in Preview phase) |
| Separate Preview HA instance if a Home HA already runs | Isolation from real setup | — Pending (decide in Preview phase) |
| How she reaches Preview (home Wi-Fi only vs Tailscale / Nabu Casa) | Simplicity vs access from anywhere | — Pending (decide in Preview phase) |
| Fork versioning: continue 1.168.x or start own scheme | Manifest/changelog already disagree upstream | — Pending (decide in foundation phase) |
| Test harness: `pytest-homeassistant-custom-component` preferred over a hand-built stub | Real HA test fixtures | — Pending |
| Home Assistant versions: pinned 2026.10.4 for Dev, Preview and tests (versions.env); minimum 2024.12.0 in hacs.json | 2024.12.0 is the first release with every API the code imports (StaticPathConfig 2024.7, calendar DATA_COMPONENT 2024.10, no-arg OptionsFlow config_entry 2024.12); a higher floor could block Home from updating | ✓ Decided in Phase 1 (D-20, D-21) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-26 after initialization (from `docs/onboarding-findings.md`)*
