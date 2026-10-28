---
last_mapped_commit: f811e9172bf425ade1c9580c6de2b1b0ef0637ee
last_mapped_at: 2026-10-26
---
# Codebase Structure

**Analysis Date:** 2026-10-26

## Directory Layout

```
HA-Family-Hub/                           # Repository root
├── custom_components/
│   └── family_hub/                      # The Home Assistant integration (Python + frontend assets)
│       ├── __init__.py                  # Integration entry point (13,175 lines)
│       ├── *_engine.py                  # Domain logic modules
│       ├── *_websocket_api.py           # Websocket command modules
│       ├── *_shared.py                  # Helpers shared by entities and API modules
│       ├── store.py                     # Storage factories, defaults, backups
│       ├── const.py                     # Constants, URLs, storage keys
│       ├── config_flow.py               # Config flow
│       ├── sensor.py switch.py number.py select.py text.py button.py todo.py device_trigger.py
│       ├── card/                        # Lovelace card JS (served at /family_hub_*_card/)
│       ├── panel/                       # Theme Builder panel and theme selector JS
│       ├── translations/                # de, en, es, fr (HA translation format)
│       ├── brand/                       # Integration logo and icon (HA brands)
│       ├── *.json                       # Root-level language files and strings
│       ├── *.js                         # Duplicate root-level card/panel copies (see Notes)
│       ├── services.yaml                # family_hub.* service definitions
│       ├── manifest.json                # HA integration manifest (version 1.168.85)
│       └── readme.md                    # Integration readme
├── website/                             # Docusaurus documentation site
│   ├── docs/                            # Markdown docs (features, installation, changelog)
│   ├── src/                             # React components and pages
│   ├── static/                          # Images, admin CMS config, favicon
│   ├── docusaurus.config.js
│   ├── sidebars.js
│   └── package.json
├── docs/                                # Standalone notes (onboarding-findings.md)
├── images/readme/                       # Screenshots used in README (.webp)
├── .github/
│   ├── workflows/deploy-docs.yml        # Docs deployment workflow
│   └── ISSUE_TEMPLATE/                  # bug_report, feature_request, family_request
├── README.md                            # Project overview
├── DOCUMENTATION.md                     # Long-form feature documentation
├── CHANGELOG.md                         # Release notes
├── PROJECT_CONTEXT.md                   # Large project context file (about 800 KB)
├── hacs.json                            # HACS metadata
├── LICENSE
├── .gitignore
└── \Screenshots/                        # Windows-style directory name with screenshots (literal backslash in name)
```

Ignored by this map: `.claude/` (GSD tooling) and `__pycache__/` directories inside `custom_components/family_hub/`.

## Directory Purposes

**`custom_components/family_hub/`:**
- Purpose: The only deployable code. Home Assistant loads this folder as the `family_hub` domain.
- Contains: About 28,800 lines of Python across 24 modules, JavaScript cards and panels, translations, icons, and `services.yaml`.
- Key files: `__init__.py`, `const.py`, `store.py`, `manifest.json`.

**`custom_components/family_hub/card/`:**
- Purpose: Canonical location of the Lovelace card and panel JavaScript served to browsers.
- Contains: `family-*.js` and `family-hub-*-card.js` custom elements. Includes `family-week-calendar-card.js.bak_divfix`, a backup file that is not referenced by code.
- Key files: `family-week-calendar-card.js` (served as `CARD_JS_URL`), `family-today-card.js`, `family-hub-chores-card.js`, `family-hub-rewards-card.js`, `family-hub-goals-card.js`, `family-hub-pantry-card.js`, `family-hub-todo-card.js`, `family-hub-recipe-box-card.js`, `family-hub-active-timers-card.js`, `family-hub-my-chores-card.js`, `family-right-now-card.js`, `family-screensaver-card.js`.

**`custom_components/family_hub/panel/`:**
- Purpose: Sidebar panel and theme selector frontends.
- Contains: `theme-builder-panel.js`, `theme-selector-card.js`.

**`custom_components/family_hub/translations/`:**
- Purpose: Home Assistant translation files for integration strings (`en.json`, `de.json`, `es.json`, `fr.json`).

**Root-level JSON in `custom_components/family_hub/`:**
- Purpose: Additional language files and base strings: `strings.json`, `en.json`, `de.json`, `es.json`, `fr.json`, `it.json`, `nl.json`, `pl.json`, `pt.json`, `pt-BR.json`.

**`custom_components/family_hub/brand/`:**
- Purpose: Icons and logos for the Home Assistant brands registry (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`).

**`website/`:**
- Purpose: Public documentation site built with Docusaurus (`website/package.json`). Not loaded by Home Assistant.
- Contains: `website/docs/features/*.md` (feature guides), `website/docs/installation.md`, `website/docs/changelog.md`, `website/static/admin/` (Netlify CMS config).

**`docs/`:**
- Purpose: Repository-level notes. Currently only `docs/onboarding-findings.md`.

**`images/readme/`:**
- Purpose: README screenshots in WebP format.

**`.github/`:**
- Purpose: GitHub issue templates and the docs deployment workflow.

## Key File Locations

**Entry Points:**
- `custom_components/family_hub/__init__.py`: Integration setup (`async_setup`, `async_setup_entry`, `async_unload_entry`).
- `custom_components/family_hub/config_flow.py`: Config flow.
- `custom_components/family_hub/manifest.json`: Domain, dependencies, version.

**Configuration:**
- `custom_components/family_hub/const.py`: Constants, storage keys, frontend URLs.
- `custom_components/family_hub/services.yaml`: Service schemas and descriptions.
- `custom_components/family_hub/strings.json`: Base UI strings.
- `hacs.json`: HACS installation metadata.

**Core Logic:**
- `custom_components/family_hub/chore_engine.py`: Chores.
- `custom_components/family_hub/reward_engine.py`: Rewards.
- `custom_components/family_hub/goal_engine.py`: Goals.
- `custom_components/family_hub/pantry_engine.py`: Pantry.
- `custom_components/family_hub/timer_engine.py`: Timers.
- `custom_components/family_hub/routine_engine.py`: Routines, with `routine_library.py` for templates.
- `custom_components/family_hub/grocery_reference.py`: Grocy reference data.
- `custom_components/family_hub/updater.py`: Update logic.
- `custom_components/family_hub/store.py`: Persistence.

**Websocket APIs:**
- `custom_components/family_hub/chores_websocket_api.py`: Chores, rewards, permissions, PINs, kiosk, and notifications (4,543 lines).
- `custom_components/family_hub/device_settings_websocket_api.py`: Device settings (859 lines).

**Entity Platforms:**
- `custom_components/family_hub/sensor.py`, `switch.py`, `number.py`, `select.py`, `text.py`, `button.py`, `todo.py`, `device_trigger.py`.

**Frontend:**
- `custom_components/family_hub/card/`: Card JavaScript.
- `custom_components/family_hub/panel/`: Panel JavaScript.

**Testing:**
- Not detected. No `tests/` directory or test files are tracked.

## Naming Conventions

**Files:**
- Python modules use `snake_case.py`. Feature engines end in `_engine.py`, websocket modules end in `_websocket_api.py`, and shared helpers end in `_shared.py`. Example: `chore_engine.py`, `device_settings_websocket_api.py`, `privacy_mode_shared.py`.
- Platform modules are named after the Home Assistant platform they implement: `sensor.py`, `todo.py`.
- Frontend files use `kebab-case` and the prefix `family-` or `family-hub-`. Example: `family-hub-chores-card.js`, `family-week-calendar-card.js`.
- Language files use BCP 47-style codes: `en.json`, `pt-BR.json`.
- Backup or temporary suffixes such as `.bak_divfix` should not be used for shipped code.

**Directories:**
- Lowercase, single word: `card`, `panel`, `translations`, `brand`.

**Constants:**
- Defined in `const.py` as `UPPER_SNAKE_CASE`. URL constants end in `_JS_URL`. Storage keys use `_STORAGE_KEY` or `_STORAGE_KEY_PREFIX` with `_STORAGE_VERSION` alongside.

## Where to Add New Code

**New feature domain (rules and state):**
- Primary code: `custom_components/family_hub/<feature>_engine.py`, with any static data in `<feature>_library.py` if needed.
- Storage factory and loader: add to `custom_components/family_hub/store.py` following the `create_*_store` and `async_load_*` pattern.
- Constants: add to `custom_components/family_hub/const.py`.

**New websocket command:**
- Implementation: in the matching `*_websocket_api.py` module if one exists (`chores_websocket_api.py` or `device_settings_websocket_api.py`). Otherwise add a `_ws_*` handler to `custom_components/family_hub/__init__.py`.
- Registration: add `websocket_api.async_register_command(hass, _ws_...)` in `async_setup` (`__init__.py` around line 12396). Declare the command schema with `voluptuous`.

**New service:**
- Handler: `_handle_*` in `custom_components/family_hub/__init__.py`, registered in the matching `_async_register_*` function.
- Schema: `custom_components/family_hub/services.yaml`.

**New entity:**
- Implementation: the platform file (`sensor.py`, `switch.py`, and so on). Add the platform to `PLATFORMS` if it is not already present.

**New card:**
- Implementation: `custom_components/family_hub/card/family-hub-<name>-card.js`.
- Register the URL as a `*_JS_URL` constant in `custom_components/family_hub/const.py`, and add the resource registration in `__init__.py` alongside the other card URLs.
- Copy the `__fhT` / `__fhEsc` / `__fhSweep` helper block from an existing card. Do not create a second variant.

**New translation:**
- Add `custom_components/family_hub/translations/<lang>.json` and update `strings.json`.

**Utilities:**
- Shared Python helpers: an existing `*_shared.py` module when entities and handlers both need the code. Otherwise a new `*_shared.py` module.

## Special Directories

**`custom_components/family_hub/__pycache__/`:**
- Purpose: Python bytecode cache for CPython 3.10 and 3.14.
- Generated: Yes
- Committed: No (ignored by `.gitignore`; present in the working tree only)

**`.planning/codebase/`:**
- Purpose: Generated codebase maps for GSD tooling.
- Generated: Yes
- Committed: Set by the orchestrator

**`\Screenshots/`:**
- Purpose: Screenshots referenced from README and docs.
- Generated: No
- Committed: Yes (file names include spaces)

**`website/node_modules/`:**
- Purpose: Docusaurus dependencies.
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-10-26*
