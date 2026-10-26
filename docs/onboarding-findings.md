# Family Hub: Onboarding Findings & Recommendations

Captured 2026-10-26 from an initial exploration of this repo, before any GSD
planning existed. Point `/gsd-onboard` (or `/gsd-ingest-docs`) at this file so
the codebase map and roadmap start from what is already known.

## Goal

Use this repo as the base for our own home dashboard / family hub and
**customise and extend it**. It is not a greenfield project: it is a fork of
[`JVarhol/HA-Family-Hub`](https://github.com/JVarhol/HA-Family-Hub), now
hosted at `Future-Bridge-AI/HA-Family-Hub`, licensed **GPLv3** (derivative
work must stay GPLv3 if distributed).

## Who is involved and how we want to work

- **Developer** (repo owner): writes the code, using GSD + Claude Code.
- **Family product owner** (my wife, non-technical): the real user. She
  should be able to use a **working app** day to day, get familiar with it,
  ask for changes in plain language, and **see each change appear** in that
  app before it reaches the family's real setup.

This shapes the plan: a shared, always-on **Family Preview** environment
comes early, every phase ends with something she can try, and her feedback
is a first-class input to the roadmap (not an afterthought).

## What the codebase is

A Home Assistant **custom integration** (`custom_components/family_hub`,
domain `family_hub`, version 1.168.85, HA >= 2024.1, installable via HACS as
a custom repository) that ships its own Lovelace cards. Everything runs
locally on Home Assistant; no cloud services.

### Backend (Python, ~25k lines)

| File | Role |
|---|---|
| `__init__.py` (~13k lines) | Core: setup, settings sync, calendar/meal logic, reminders, notifications, Grocy client, theme registry injection, backups, static path + dashboard resource registration (~line 12500) |
| `chores_websocket_api.py` (~4.5k) | Websocket API for chores, rewards, goals, routines, permissions, kiosk, timers |
| `chore_engine.py`, `reward_engine.py`, `goal_engine.py`, `routine_engine.py`, `routine_library.py`, `timer_engine.py`, `pantry_engine.py` | Domain logic per feature |
| `store.py` | Persistence via HA `Store` (per-feature storage key prefixes in `const.py`) |
| `config_flow.py` | Integration setup/options flow |
| `device_settings_websocket_api.py`, `device_settings_entity_shared.py`, `privacy_mode_shared.py` | Per-device (tablet) settings and privacy mode |
| `sensor.py`, `switch.py`, `number.py`, `select.py`, `text.py`, `button.py`, `todo.py`, `device_trigger.py` | HA entities and device triggers exposed for automations |
| `grocery_reference.py` | Grocery/pantry reference data |
| `const.py` | Constants, storage keys, card JS URLs |
| `services.yaml` | 8 services: `create_chore`, `complete_chore`, `approve_chore`, `reject_chore`, `nudge_user`, `start_timer`, `cancel_timer`, `stop_timer_alarm` |

Frontend <-> backend communication is ~60 `family_hub/...` websocket
commands. Data is polled every 60s by cards; a backend poller (reminders,
alerts, chore resets, Daily Digest) runs every ~5 minutes.

### Frontend (vanilla JS web components, ~66k lines)

**Only `card/` and `panel/` are served** (see `__init__.py` around line 12503).

| Card (`type: custom:...`) | Purpose |
|---|---|
| `family-week-calendar-card` (~31k lines) | Main hub: Week/Month/Planner/Agenda, meals, in-card Settings, More menu, Right Now bar |
| `family-today-card`, `family-right-now-card` | At-a-glance today / presence + current/next event |
| `family-hub-chores-card`, `family-hub-my-chores-card`, `family-hub-rewards-card`, `family-hub-goals-card` | Chores -> stars -> rewards, goals, routines |
| `family-hub-todo-card` | Any HA to-do lists side by side |
| `family-hub-recipe-box-card`, `family-hub-pantry-card` | Recipes and pantry (optional Grocy integration) |
| `family-hub-active-timers-card` | Timers/alarms ringing on screens, phones, speakers |
| `family-screensaver-card` | Wall-tablet screensaver |
| `theme-selector-card`, Theme Builder panel (`panel/`) | 10 built-in themes + custom; builder is undocumented/beta |

Other features: kiosk PIN sign-in, child accounts, per-person permissions,
Privacy/Discreet modes, HA-side notifications, Daily Digest, settings
backups every 12h, i18n.

### Runtime requirements

- At least one `calendar.*` entity.
- `todo.*` entities for recipe box, meal plan, meal templates, suggestions,
  reminders (Local To-do works; some are auto-created).
- A `notify.*` target for reminders/alerts.
- Most configuration lives in the calendar card's in-card Settings, synced
  via backend storage. See `DOCUMENTATION.md` for card YAML.

### Other repo contents

- `README.md`, `DOCUMENTATION.md` (user docs), `CHANGELOG.md`.
- `PROJECT_CONTEXT.md` (~800 KB): the original author's AI-session handoff
  notes. Valuable for architecture rationale and gotchas, but partly stale
  (Windows paths, ephemeral `/tmp` test-harness paths). Read selectively;
  do not treat as current truth.
- `website/`: Docusaurus docs site, deployed by
  `.github/workflows/deploy-docs.yml` on changes to `website/**`.
- `images/`, `\Screenshots/` (directory name literally starts with a
  backslash; a Windows upload artifact).
- `.claude/`: GSD Core 1.18.0 (local install).

## Problems found

Ordered by how much they affect safe customisation.

1. **Stale duplicate card files.** Every card/panel `.js` also exists at the
   integration root (`custom_components/family_hub/*.js`), and the root
   copies differ from (are older than) the served copies in `card/` and
   `panel/` (e.g. calendar: 23.5k vs 31k lines). The most recent upload
   commit (`8f7172d`) edited root copies, which have **no effect at
   runtime**. Risk: edits land in the wrong file.
   Also `card/family-week-calendar-card.js.bak_divfix` is a stray backup.
2. **Translations are inconsistent.** HA only loads `translations/*.json`,
   which contains only `de`, `en`, `es`, `fr` (full, 2373 lines).
   `it`, `nl`, `pl`, `pt`, `pt-BR` exist only at the integration root, so
   HA **does not load them** despite the README advertising those
   languages. The root `de`/`en`/`es.json` are truncated older copies
   (~1.1–1.3k lines, cut by `8f7172d`). `strings.json` matches the
   `translations/en.json` top-level structure.
3. **Compiled Python committed.** 49 `__pycache__/*.pyc` files are tracked
   even though `.gitignore` already ignores them.
4. **No tests in the repo.** `PROJECT_CONTEXT.md` references 15 `test_*.py`
   files, a hand-built fake `homeassistant` stub package and jsdom-based JS
   tests; none of these are committed. No CI runs Python or JS checks; the
   only workflow builds the docs site.
5. **Upstream identity everywhere.** `manifest.json` (`documentation`,
   `issue_tracker`, codeowner `@bordello_labs`), README badges/links and
   HACS one-click links all point to `JVarhol/HA-Family-Hub`.
6. **Very large single files.** `__init__.py` (13k lines) and
   `family-week-calendar-card.js` (31k lines) concentrate most logic, which
   makes changes risky without tests.
7. **Repo hygiene.** `\Screenshots/` directory name, duplicated icon/logo
   files (`icon (1).png`, root vs `brand/`), empty
   `custom_components/family_hub/readme.md`, unversioned upload-style
   commits ("Add files via upload").
8. **Known feature gaps** (from `DOCUMENTATION.md`): no drag-to-reorder of
   meals in Month view; Theme Builder panel not finished/documented; not in
   the default HACS store.

## Environments

Three places the integration runs, each with a clear job:

| Environment | Who uses it | Data | How it gets updated |
|---|---|---|---|
| **Dev** | Developer | Throwaway demo data | Live: integration folder mounted from the working copy; restart HA for Python changes, hard-refresh the browser for card JS changes |
| **Family Preview** | Wife + developer, on a real tablet/phone | Realistic seeded family data (our names, routines, chores, meals), **never** the real family calendars, so trying things can't break anything | One command (`deploy-preview`) from a branch, after the developer has checked it in Dev |
| **Home** (production) | Whole family, wall tablet | Real calendars, real to-do lists | Only after she has tried the change in Preview and said yes |

Open decisions for the developer (resolve during the Family Preview phase):

- Does a Home Assistant already run at home? If yes, Preview should be a
  **separate** HA instance (Docker container on another port, or a spare
  machine/Pi) so experiments never touch the family's real setup.
- Where Preview runs: an always-on home machine (recommended: Docker
  Compose on a NAS/mini PC/Pi) vs. the developer's laptop (not always on,
  so not good for her).
- How she reaches it: home Wi-Fi only (simplest) vs. from anywhere
  (Tailscale or Nabu Casa). Use the **HA Companion app** on her phone and a
  bookmarked dashboard on a tablet so it feels like an app, not a dev tool.
- Seed data: scripted (repeatable, can reset to a known state) vs.
  entered by hand. Scripted is recommended, with a "reset Preview" command.

## Recommendations

### Phase 1: Clean foundation (small, invisible to the family; do first)

- Delete root-level duplicate `.js` files and the `.bak_divfix` file;
  confirm nothing references them (served paths are `card/` and `panel/`).
- Move `it`, `nl`, `pl`, `pt`, `pt-BR` JSON into `translations/` (verify
  key parity with `translations/en.json` first); delete the stale root
  `de`/`en`/`es`/`fr.json`.
- `git rm -r --cached` all `__pycache__/`.
- Rename `\Screenshots/` to `screenshots/` (or remove if redundant with
  `images/readme/`); dedupe icons.
- Decide on the fork's identity: update `manifest.json` links/codeowners
  and README links to `Future-Bridge-AI/HA-Family-Hub` (keep credit to the
  upstream author per GPLv3), and decide versioning (continue 1.168.x or
  start our own scheme).

### Phase 2: Dev + Family Preview environments (first thing she sees)

Goal: she has the **unmodified** app running on a tablet/phone with our
family's (pretend) data, and the developer can push a change to it with one
command.

- `docker-compose` (or devcontainer) for **Dev**: Home Assistant +
  this integration mounted from the repo + demo seed data.
- **Family Preview** HA instance with the same compose setup, its own
  config volume, and a `deploy-preview` script that copies
  `custom_components/family_hub` from a chosen branch and restarts HA.
  The integration already cache-busts card JS by content hash, so a reload
  shows new cards.
- Seed script creating: Local Calendar entities per family member, the
  `todo.*` lists the integration needs, a realistic week of events, meals,
  chores, rewards, and HA user accounts for each family member (hers as a
  normal, non-admin user). Plus a `reset-preview` command.
- Set up her access (Companion app and/or tablet kiosk dashboard) and a
  short, plain-language **"Getting started" guide** (`docs/family/`) with
  screenshots: what each screen is for and how to ask for a change.
- Done when: she can open it herself, find today's plan, tick a chore and
  redeem a reward, and the developer has deployed one trivial visible change
  (e.g. a title text) that she confirms she can see.

### Phase 3: Safety net before feature work

- Rebuild a minimal Python test harness: `pytest` plus either
  `pytest-homeassistant-custom-component` (preferred: real HA test
  fixtures) or a small stub package as described in `PROJECT_CONTEXT.md`.
  Start with the pure engines (`chore_engine`, `reward_engine`,
  `goal_engine`, `routine_engine`, `timer_engine`), which are the easiest
  to unit test.
- Add JS smoke tests (jsdom or Playwright) that load each card module and
  render with a mocked `hass` object. Playwright can also capture
  **screenshots of the Preview**, which double as before/after pictures for
  her.
- Add CI (GitHub Actions): ruff/flake8 + pytest for Python, a JS syntax
  check (`node --check`) or tests for cards, and HACS/hassfest validation
  (`hacs/action`, `home-assistant/actions/hassfest`).

### Phase 4 onward: Family-led customisation loop

Each feature goes round this loop:

1. **Ask.** She describes a need in plain language ("I want to see who's
   doing school pickup at a glance"), either by telling the developer or by
   filing a GitHub issue using the **Family request** template
   (`.github/ISSUE_TEMPLATE/family_request.md`). The developer captures it
   with `/gsd-capture` or triages issues with `/gsd-inbox`.
2. **Agree what "done" looks like.** In `/gsd-discuss-phase`, write
   acceptance criteria as things she will do and see in the app, not
   technical tasks. Use `/gsd-sketch` for a throwaway HTML mockup she can
   react to before any real code is written.
3. **Build** with `/gsd-plan-phase` + `/gsd-execute-phase`, tested in Dev.
4. **Try it.** `deploy-preview`, then she uses it for a few days. Run
   `/gsd-verify-work` (conversational UAT) **with her answers** as the
   verification.
5. **Release.** Only after her sign-off: ship to Home. Add a short,
   jargon-free entry to `docs/family/whats-new.md` (what changed, where to
   find it, a screenshot).

Candidate backlog to show her early (she decides priority): Month-view meal
drag-to-reorder, finishing the Theme Builder, and anything that comes out of
her first week using Preview.

Engineering guardrail: where new work touches `__init__.py` or the calendar
card, prefer extracting focused modules rather than growing the monoliths.

## Notes for GSD

- Treat this as a **brownfield** project: use `/gsd-onboard`, not
  `/gsd-new-project`.
- Use the four phases above as the first milestone. Phases 1 and 2 are
  prerequisites; Phase 3 can overlap Phase 2's tail.
- The non-technical family product owner is a core user: acceptance
  criteria and UAT should be written so she can verify them by using the
  Preview app, and every phase from Phase 2 on should end in something she
  can try.
- When ingesting docs, prefer `README.md` and `DOCUMENTATION.md` for current
  behaviour; use `PROJECT_CONTEXT.md` for rationale only (it is stale in
  places).
