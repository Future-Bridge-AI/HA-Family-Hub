<!-- GSD:project-start source:PROJECT.md -->

## Project

**Family Hub (Future-Bridge-AI fork)**

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

**Core Value:** The family product owner can use a working Family Hub every day and see each change she asks for
appear in a safe Preview before it reaches the family's real Home setup — without anything breaking
the real calendars and lists.

### Constraints

- **License**: GPLv3 — the fork is a derivative work; distribution must stay GPLv3 and keep upstream credit
- **Platform**: Home Assistant custom integration, HA >= 2024.12.0 (declared in hacs.json; Dev, Preview and tests pinned to 2026.10.4 in versions.env), HACS custom repository — the install path the family setup already depends on
- **Tech stack**: Python on HA Core APIs (no extra Python deps), vanilla JS web components with no bundler — keep the existing build-free delivery
- **Locality**: everything runs locally; no cloud services — upstream design and family privacy
- **Safety**: Preview must be isolated from the family's real HA and real calendars — experiments must never break the real setup
- **Usability**: every phase from the Preview phase on ends in something she can try; acceptance criteria and UAT are written as things she does and sees in the app — she is non-technical and the real user
- **Code health**: changes to `__init__.py` or the calendar card prefer extracting focused modules over growing the monoliths — no tests exist yet, so large files are risky to change
- **Served paths**: only `card/` and `panel/` JS is served — edits must target those copies

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python (3.10+ implied; `dict | None` annotations and `from __future__ import annotations` used throughout; `__pycache__` contains `cpython-310` and `cpython-314` bytecode) - Home Assistant custom integration backend in `custom_components/family_hub/*.py` (largest file: `custom_components/family_hub/__init__.py`, ~13,175 lines)
- JavaScript (ES modules / custom elements, no transpilation) - Lovelace cards and panels in `custom_components/family_hub/card/*.js`, `custom_components/family_hub/panel/*.js`, and root-level copies of the same files in `custom_components/family_hub/*.js`
- JSON - translations and HA metadata: `custom_components/family_hub/en.json`, `de.json`, `es.json`, `fr.json`, `it.json`, `nl.json`, `pl.json`, `pt.json`, `pt-BR.json`, `custom_components/family_hub/translations/{en,de,es,fr}.json`, `custom_components/family_hub/strings.json`, `custom_components/family_hub/manifest.json`, `hacs.json`
- YAML - HA service definitions in `custom_components/family_hub/services.yaml`
- Markdown / MDX - documentation in `website/docs/**`, `DOCUMENTATION.md`, `README.md`, `CHANGELOG.md`
- JavaScript (React JSX in `.js`) - docs site components in `website/src/components/HomepageFeatures/index.js`, `website/src/pages/index.js`
- CSS - docs site styling in `website/src/css/custom.css` and CSS modules under `website/src/**`
- YAML - CI workflow `.github/workflows/deploy-docs.yml`; CMS config `website/static/admin/config.yml`

## Runtime

- Home Assistant Core (custom integration loaded from `custom_components/family_hub/`); minimum supported HA version declared as `homeassistant: 2024.12.0` in `hacs.json`; Dev, Preview and tests pinned to 2026.10.4 in `versions.env`
- Asyncio event loop; blocking work is pushed to executors (e.g. `hass.async_add_executor_job` used for PBKDF2 PIN hashing in `custom_components/family_hub/chores_websocket_api.py` and the zip updater in `custom_components/family_hub/updater.py`)
- Browsers and HA companion/kiosk WebViews rendering Lovelace dashboards; cards are registered as Web Components via `customElements.define(...)` in each file under `custom_components/family_hub/card/` and `custom_components/family_hub/panel/`
- Node.js `>=20.0` (`website/package.json` `engines`); CI uses Node 20 (`.github/workflows/deploy-docs.yml`)
- Backend: none. No `requirements.txt`, `pyproject.toml`, or `setup.py` exists; Python dependencies are provided by Home Assistant itself.
- Docs: npm
- Frontend cards: none. No `package.json` at the integration level; JS files are plain modules shipped as-is.

## Frameworks

- Home Assistant Core APIs - the integration is built on:
- Config flow UI: `custom_components/family_hub/config_flow.py` (`config_flow: true` in `custom_components/family_hub/manifest.json`)
- Declared HA dependencies (`custom_components/family_hub/manifest.json`): `frontend`, `http`, `lovelace`, `file_upload`, `image_upload`; after-dependency: `timer`
- Vanilla Web Components / custom elements; no UI framework and no bundler. Examples: `custom_components/family_hub/card/family-week-calendar-card.js`, `custom_components/family_hub/card/family-hub-todo-card.js`, `custom_components/family_hub/panel/theme-builder-panel.js`
- Cards are served as static JS through `StaticPathConfig` registrations (URL constants in `custom_components/family_hub/const.py`, e.g. `CARD_JS_URL = "/family_hub_card/family-week-calendar-card.js"`)
- Not detected. No test directories, test files, or pytest/vitest/jest configuration are tracked in the repository (`.pytest_cache/` is git-ignored in `.gitignore`).
- Docusaurus `3.10.2` - `@docusaurus/core`, `@docusaurus/preset-classic`, `@docusaurus/faster`, `@docusaurus/module-type-aliases`, `@docusaurus/types` (`website/package.json`)
- Config: `website/docusaurus.config.js`, sidebars in `website/sidebars.js`
- Scripts: `build`, `start`, `serve`, `deploy`, `clear`, `swizzle`, `write-translations`, `write-heading-ids` (`website/package.json`)

## Key Dependencies

- `aiohttp` - outbound HTTP client and `web` types; used with `async_get_clientsession(hass)` from `homeassistant.helpers.aiohttp_client` for Grocy REST calls, recipe URL fetching, and file uploads in `custom_components/family_hub/__init__.py` (imports at lines ~47, ~52, ~75)
- `voluptuous` - websocket and service schema validation (`vol.Required`, `vol.Coerce`, `vol.Any`) in `custom_components/family_hub/__init__.py` and `custom_components/family_hub/chores_websocket_api.py`
- Standard library only beyond the above: `asyncio`, `hashlib` (sha256, pbkdf2_hmac), `hmac` (`compare_digest`), `secrets` (`token_hex`), `uuid`, `zipfile`, `shutil`, `tempfile`, `base64`, `ipaddress`, `difflib`, `html`, `json`, `re`, `datetime`, `calendar`, `itertools`, `math`, `time`, `os`, `io`, `pathlib`, `urllib.parse`
- Google Fonts stylesheet `Varela Round` loaded at runtime by injecting a `<link>` into each card, e.g. `custom_components/family_hub/card/family-today-card.js` (line ~74), `custom_components/family_hub/card/family-week-calendar-card.js` (line ~122). No font files are bundled.
- `react` `^19.0.0`, `react-dom` `^19.0.0`, `@mdx-js/react` `^3.0.0`
- `clsx` `^2.0.0`, `prism-react-renderer` `^2.3.0`
- `@easyops-cn/docusaurus-search-local` `^0.55.3` (local search plugin)
- GitHub Actions (`.github/workflows/deploy-docs.yml`): `actions/checkout@v4`, `actions/setup-node@v4`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`
- HACS distribution metadata: `hacs.json` (`render_readme: true`) and `custom_components/family_hub/manifest.json` (`version: 1.168.85`, `iot_class: local_polling`)

## Configuration

- Configured entirely through the HA config-entry UI (`custom_components/family_hub/config_flow.py`); settings are stored in config-entry `options`.
- Constants and storage keys are defined in `custom_components/family_hub/const.py` (e.g. `CONF_GROCY_URL = "grocy_url"`, `CONF_GROCY_API_KEY = "grocy_api_key"` at lines ~984-985).
- Persistent data uses HA `Store` (`homeassistant.helpers.storage.Store`) with per-entry key prefixes (e.g. `SETTINGS_STORAGE_KEY_PREFIX`, `THEME_STORAGE_KEY`, `TIMERS_STORAGE_KEY_PREFIX` in `const.py`); the theme store is created in `custom_components/family_hub/__init__.py` (`Store(hass, THEME_STORAGE_VERSION, THEME_STORAGE_KEY)`).
- Environment variables: none read by the integration. Secrets (Grocy API key) live in config-entry options, not in env files.
- Lovelace card configuration in YAML (see `website/docs/card-configuration.md` and `DOCUMENTATION.md`). Card JS URLs are registered by the integration under `/family_hub_*` paths.
- `website/docusaurus.config.js` - Docusaurus site config
- `website/sidebars.js` - docs sidebar
- `website/static/admin/config.yml` and `website/static/admin/index.html` - Netlify/Decap-style CMS admin config
- `.gitignore` - ignores `__pycache__/`, `*.pyc`, `.pytest_cache/`, `node_modules/`, `.DS_Store`, `*.zip`
- Translations shipped in ten language files at `custom_components/family_hub/*.json` (en, de, es, fr, it, nl, pl, pt, pt-BR) plus `custom_components/family_hub/translations/` (en, de, es, fr). Frontend i18n uses `data-i18n` / `_t(key, fallback)` patterns inside the card JS.

## Platform Requirements

- Home Assistant Core development or test instance (pinned 2026.10.4 per `versions.env`; min 2024.12.0 per `hacs.json`)
- Python 3.10+ for editing/compiling backend modules
- Node.js 20+ and npm for the docs site in `website/`
- No linter, formatter, or test runner configuration is tracked in the repository
- Installed via HACS (custom repository) or manual copy of `custom_components/family_hub/` into a Home Assistant config directory
- Runs inside the Home Assistant process; `iot_class: local_polling`
- Optional: a self-hosted Grocy instance (URL + API key) for the grocery/recipe features
- Docs site deployed as a static build to GitHub Pages (`.github/workflows/deploy-docs.yml`, served at `https://jvarhol.github.io/HA-Family-Hub/`)

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- Python modules use `snake_case` and are flat inside the integration package: `custom_components/family_hub/chore_engine.py`, `reward_engine.py`, `pantry_engine.py`, `chores_websocket_api.py`, `device_settings_websocket_api.py`.
- Home Assistant platform modules are named after the platform: `sensor.py`, `switch.py`, `number.py`, `select.py`, `text.py`, `button.py`, `todo.py`, `device_trigger.py`.
- Engine modules (pure business logic, no `hass` dependency) use the suffix `_engine.py`. Websocket handler modules use the suffix `_websocket_api.py`. Shared helpers use `_shared.py` (`privacy_mode_shared.py`, `device_settings_entity_shared.py`).
- Frontend cards are kebab-case JavaScript files under `custom_components/family_hub/card/`, named `family-hub-<name>-card.js` (e.g. `family-hub-pantry-card.js`) or `family-<name>-card.js` (e.g. `family-today-card.js`, `family-right-now-card.js`). Panels live in `custom_components/family_hub/panel/`.
- Translation files are locale codes: `en.json`, `de.json`, `pt-BR.json`. Both `custom_components/family_hub/translations/` and the top-level `custom_components/family_hub/*.json` exist; treat `translations/` as the location Home Assistant reads.
- Do not add files with a `.bak_*` suffix. One exists (`card/family-week-calendar-card.js.bak_divfix`) and is leftover debris, not a convention to copy.
- `snake_case` for all Python functions. Private helpers are prefixed with a single underscore: `_check_user_enabled`, `_now_iso`, `_get_extra`, `_entry_data_or_error`.
- Async Python functions use the `async_` prefix for Home Assistant-facing entry points (`async_setup_entry`, `async_load_locked_popups`) and are `async def` directly. Websocket handlers are named `ws_<feature>_<action>` (e.g. `ws_more_menu_locked_set`, `ws_more_menu_unlock_options` in `custom_components/family_hub/chores_websocket_api.py`).
- Factory helpers for new records are named `default_<thing>` (`default_pantry_extra`) and ID generators `new_<thing>_id` (`new_chore_id`, `new_group_id`, `new_pantry_extra_id`).
- JavaScript card methods are `camelCase` and private methods are underscore-prefixed (`_applyThemeVars`, `_headerTitleFontSize`, `_saveSettings`, `_onClick`).
- Global helpers in card files use the `__fh` prefix for shared, byte-identical copies across cards: `__fhI18n`, `__fhEsc`, `__fhT`, `__fhSweep` (`custom_components/family_hub/card/family-hub-pantry-card.js`). Keep these identical across files.
- Python: `snake_case` locals. Module-level constants are `UPPER_SNAKE_CASE` and are defined in `custom_components/family_hub/const.py`.
- Storage key constants follow `<THING>_KEY_<FIELD>` for record field names (`CHORE_KEY_COMPLETED_AT`, `CHORE_KEY_QUANTITY_REMAINING`) and `<THING>_STATUS_*` for state values (`CHORE_STATUS_*`). Always reference these constants rather than string literals when touching chore records.
- Assignment-mode and unit enums are constant tuples: `CHORE_ASSIGNMENT_MODES`, `CHORE_RECUR_INTERVAL_UNITS`.
- Logger: `_LOGGER = logging.getLogger(__name__)` at module top (`custom_components/family_hub/chore_engine.py`, `button.py`, `__init__.py`). Some modules use `logger`/`LOGGER` via `logging.getLogger(__name__)` directly; prefer `_LOGGER`.
- JavaScript: `camelCase` for everything. Config keys in settings are camelCase too (`useGlobalTheme`, `globalThemeId`, `notifyRewardClaimed`, `userProfiles`).
- Python classes are `PascalCase`. Domain error classes follow `<Domain>Error` and subclass `Exception` with a `code` attribute: `ChoreError` (`chore_engine.py:95`), `RewardError` (`reward_engine.py:68`), `GoalError`, `PantryError` (`pantry_engine.py:43`), `RoutineError`, `TimerError`, `UpdateError` (`updater.py:31`).
- Frontend custom elements are `FamilyHub<Name>Card` classes registered with `customElements.define("family-hub-<name>-card", ...)`, with a matching `FamilyHub<Name>CardEditor` for the Lovelace editor (`family-hub-pantry-card.js:371`, `:1634`).
- Custom element names must contain a hyphen, and element tag names are the kebab-case registration string.

## Code Style

- No formatter config is committed (no `pyproject.toml`, `setup.cfg`, `.flake8`, `ruff.toml`, or `.pre-commit-config.yaml`). Follow the observed style rather than a tool default.
- Strings: double quotes dominate (`custom_components/family_hub/chore_engine.py`: about 290 lines containing `"` versus about 100 containing `'`). Use double quotes.
- Line length: long lines are common. About 1 in 125 Python lines exceeds 120 characters across the package; the longest seen is about 150. Break long dict literals and function signatures across lines when they grow past about 120, but do not reflow existing long lines just to shorten them.
- Every Python module that defines functions starts with `from __future__ import annotations` (verified in all modules except `const.py`). Keep that as the first statement after the module docstring.
- Type hints are used on public functions: `dict[str, Any]`, `Optional[...]`, `Callable[...]`. Prefer `Optional[X]` and `dict[...]` (PEP 585 builtins) as already used in `chore_engine.py`.
- No ESLint or Prettier config is committed. Cards are hand-formatted with semicolons and double quotes.
- Modern declarations (`const`, `let`) are the norm in cards. A few shared bootstrap blocks use `var` on purpose so they attach to `window` identically across files (`var __fhI18n = (window.__familyHubI18n = ...)` in `custom_components/family_hub/card/family-hub-pantry-card.js`). Do not change those to `let`/`const`.
- Cards are standalone IIFE-free single files. Each card copies shared boilerplate (`PALETTE`, theme handling, `_esc`/`_escAttr`, the translation helper) rather than importing it, per the project's documented convention. When changing shared helpers, update every card copy.
- Not configured. There is no lint step in CI (`.github/workflows/deploy-docs.yml` only builds the Docusaurus site under `website/`).

## Import Organization

- Engine modules must not import `homeassistant` at runtime when avoidable. Their module docstrings state this explicitly (e.g. `chore_engine.py` and `reward_engine.py` deliberately stay hass-free). Side effects such as notifications and bus events belong in the call sites (`chores_websocket_api.py`, `__init__.py`).
- Circular imports are avoided by duplicating small helpers rather than importing across the boundary. `chores_websocket_api.py` keeps a local copy of `_split_notify_target`/`_notification_click_data`, and `__init__.py` keeps `_notify_chore_approved_native` as a deliberate duplicate of the websocket-side function. Follow that pattern rather than adding an import cycle.
- Path aliases: not applicable (Python package-relative imports only). Frontend cards load via absolute `/family_hub/...` resource URLs registered in `__init__.py`, not via bundler aliases.

## Error Handling

- Engine modules raise a domain error with a machine-readable `code` and a human message:
- Websocket handlers catch the engine error and forward `code` and message to the client with `connection.send_error(msg["id"], err.code, str(err))`. Do not build a big `if/elif` ladder that guesses the reason from message text.
- Websocket handlers check permissions themselves before calling engines, using `connection.user.is_admin` or the permission catalog. Engine functions never check permissions (documented in `chore_engine.py`'s module docstring).
- Standard send-error shape for websocket handlers, with a stable code and a user-facing sentence:
- Broad `except Exception as err:` is common (about 145 occurrences) around best-effort operations such as notifications, external Grocy calls, and optional lookups. Use it only where failure must not break the caller, and log the failure at `_LOGGER.warning` or `_LOGGER.debug`. Do not swallow silently.
- `except (TypeError, ValueError)` is the standard guard when parsing user-supplied values such as dates and numbers.
- Storage writes are batched: callers do exactly one `await store.async_save(...)` per websocket or service call (documented in `chore_engine.py`'s module docstring). Engines never save the store themselves.
- Websocket calls are awaited inside `try`/`catch`. Show user feedback through the card's own status or toast helper and re-fetch state after a mutation (the rewards card re-fetches after `_deleteRedemption`/`_reverseRedemption`).
- Malformed client-side values are validated and degraded to a safe default rather than thrown, e.g. hex colors re-validated with `/^#[0-9a-fA-F]{6}$/` and falling back to no inline style.

## Logging

- Log with `%s` lazy formatting, not f-strings, in new code.
- Do not use `print()` in integration code. Print statements exist only in legacy standalone test scripts (see TESTING.md).
- Frontend uses `console.warn`/`console.error` sparingly; do not leave debug `console.log` in committed cards.

## Comments

- The codebase is heavily commented with design rationale, not restatement. Module docstrings explain the state machine, permission model, storage ownership, and why a module is split the way it is (see `chore_engine.py`, `pantry_engine.py`, `const.py`).
- Version tags in comments are common (`v1.168.76`, `v122`). Keep them when editing nearby logic, but do not add new version-stamped narration to new code. Put the reasoning, not the changelog, in the comment.
- Explain non-obvious constraints: browser/WebView rendering quirks (the `background` on `<input type="color">` note), circular-import avoidance, storage key preservation for migrations (`THEME_STORAGE_KEY` in `const.py`).
- Python: triple-double-quoted module docstrings on every engine module, and one-line or short multi-line docstrings on public functions and websocket handlers. Argument and return types are documented in type hints, not docstrings.
- JavaScript: `//` line comments above classes and shared blocks. No JSDoc enforced.

## Function Design

- Websocket handlers take `(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict)` and return `None`. They are decorated with `@websocket_api.websocket_command({vol.Required("type"): "family_hub/..."})` and `@websocket_api.async_response`.
- Engine functions take the plain record dict (or the store dict) and payload dict, not `hass`.
- Engine mutators return the updated record dict. Websocket handlers reply with `connection.send_result(msg["id"], {...})`.
- Use `Optional[X]` plus an early `return` for lookups that may be absent, and let the caller decide whether that is an error (`_entry_data_or_error` returns `None` after sending the error).

## Module Design

- No `__all__` convention. Public names are plain, underscore-free functions and constants; internal helpers are underscore-prefixed.
- Platform modules (`sensor.py`, `switch.py`, etc.) expose `async_setup_entry` and entity classes. Entity classes are `PascalCase` and named after the feature.
- None. Import the specific engine module (`from . import timer_engine`) rather than re-exporting through `__init__.py`.
- Records are plain dicts keyed by `*_KEY_*` constants, not dataclasses. Keep new fields as dict keys defined in `const.py` and default them in a `default_<thing>()` factory.
- Settings and per-user profiles are stored under the `settings` store and normalized on read (`_normalizeUserProfiles` on the card side, `_get_user_profiles` on the server side). New fields need defaults in both places.

## Where to Place New Conventions

- New backend constants: `custom_components/family_hub/const.py`.
- New engine logic: a new `*_engine.py` module with a `<Domain>Error` class and no `hass` import.
- New websocket commands: the matching `*_websocket_api.py` module, registered in that module's `ALL_COMMANDS` list.
- New card: a new file under `custom_components/family_hub/card/` following the `FamilyHub<Name>Card` / `FamilyHub<Name>CardEditor` pattern and copying the shared `__fh*` boilerplate.

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Pattern Overview

- One config entry per install (`config_flow: true` in `custom_components/family_hub/manifest.json`); the entry runtime bucket lives in `hass.data["family_hub"]["entries"][entry_id]` (see `_get_entry_data` in `custom_components/family_hub/chores_websocket_api.py` and `__init__.py` around line 2123).
- Global, domain-level setup happens once in `async_setup` (`custom_components/family_hub/__init__.py` ~line 12390): creates the theme `Store`, registers all websocket commands, and sets up the `hass.data["family_hub"]` container.
- Per-entry setup happens in `async_setup_entry` (`custom_components/family_hub/__init__.py` line 12501) and teardown in `async_unload_entry` (line 13126). Stores are loaded, backups restored if needed, services registered, and polling/timer listeners started via `async_track_time_interval` (lines ~12864 and ~12902).
- Business logic is split into engine modules named `*_engine.py`. Each owns one feature domain (chores, rewards, goals, pantry, timers, routines). Engines raise domain exceptions (`ChoreError` in `custom_components/family_hub/chore_engine.py` line 95, `GoalError` in `goal_engine.py` line 83, `UpdateError` in `updater.py` line 31).
- Frontend is not built or bundled: plain ES5-style JavaScript files are served directly through `homeassistant.components.http` static paths (`*_JS_URL` constants in `custom_components/family_hub/const.py`, e.g. `CARD_JS_URL` line 944, `CHORES_CARD_JS_URL` line 2277).
- Cards share state via `window` globals (for example `window.__familyHubI18n` in `custom_components/family_hub/card/family-today-card.js`), and each card file re-declares its own copy of the helper, so whichever file loads first wins.

## Layers

- Purpose: Register HA domain/services/websocket commands, static paths, panels, lovelace resources, and per-entry lifecycle.
- Location: `custom_components/family_hub/__init__.py` (13,175 lines; the largest file in the repo).
- Contains: `async_setup`, `async_setup_entry`, `async_unload_entry`, service handlers (`_handle_*`), websocket command handlers (`_ws_*`), theme-generation helpers, reminder/notification polling, Grocy integration, calendar event handling.
- Depends on: every `*_engine.py`, `store.py`, `const.py`, `chores_websocket_api.py`, `device_settings_websocket_api.py`, plus Home Assistant core components.
- Used by: Home Assistant loader (entry point only).
- Purpose: Authorize and validate frontend requests, then delegate to engines and stores.
- Location: `custom_components/family_hub/chores_websocket_api.py` (4,543 lines), `custom_components/family_hub/device_settings_websocket_api.py` (859 lines).
- Contains: `_is_admin`, `_has_permission`, `_can_add_rewards` permission checks; PIN hashing and lockout (`_hash_pin`, `_pbkdf2`, `async_verify_pin`, `pin_lockout_remaining`); kiosk elevation; locked-popup handling; notification senders.
- Depends on: `store.py`, `chore_engine.py`, `reward_engine.py`, `pantry_engine.py`, `timer_engine.py`, `routine_engine.py`, `device_settings_entity_shared.py`, `privacy_mode_shared.py`.
- Used by: `__init__.py` imports these modules and registers their handlers. The module is imported as `chores_ws_api` to avoid clashing with HA's `websocket_api` name (see the docstring in `chores_websocket_api.py`).
- Purpose: Feature-specific rules and state transitions.
- Location: `custom_components/family_hub/chore_engine.py`, `reward_engine.py`, `goal_engine.py`, `pantry_engine.py`, `timer_engine.py`, `routine_engine.py`, `routine_library.py`, `grocery_reference.py`, `privacy_mode_shared.py`, `device_settings_entity_shared.py`.
- Contains: Chore scheduling and approval, reward points and redemption, goal progress, pantry stock logic, timer lifecycle, routine templates (`routine_library.py` holds static routine definitions), Grocy reference data.
- Depends on: Store dictionaries passed in by callers; some engines call `hass` directly for notifications (e.g. `send_nudge` in `chore_engine.py` line 1030).
- Used by: websocket handlers, service handlers, and entity platforms.
- Purpose: Create and load per-feature `homeassistant.helpers.storage.Store` objects and mirror them to backup files.
- Location: `custom_components/family_hub/store.py` (452 lines).
- Contains: `create_*_store` factories (lines 71-103), `async_load_*` functions with defaults (`default_rewards`, `default_routines`, `default_privacy_mode`, and so on), and `_backup_data` / `_maybe_restore_backup` helpers (lines 314-451) that write to `<config>/.../*_backup` files and restore when storage is empty.
- Depends on: `homeassistant.helpers.storage`.
- Used by: `__init__.py` during `async_setup_entry`, and websocket handlers when they save.
- Purpose: Expose state to Home Assistant as entities.
- Location: `custom_components/family_hub/sensor.py`, `switch.py`, `number.py`, `select.py`, `text.py`, `button.py`, `todo.py`, `device_trigger.py`.
- Contains: Entity classes per platform. `todo.py` (152 lines) registers a `todo.*` entity used as the target for suggestions and lists (see `apply_menu_suggestion` in `__init__.py`). `device_trigger.py` exposes automation triggers.
- Depends on: engines and stores through `hass.data`.
- Used by: Home Assistant entity registry and automations.
- Purpose: Guided setup and options for the single config entry.
- Location: `custom_components/family_hub/config_flow.py` (1,336 lines). Translations are in `custom_components/family_hub/strings.json`, `en.json`, and `translations/*.json` (de, en, es, fr) plus root-level `de.json`, `en.json`, `es.json`, `fr.json`, `it.json`, `nl.json`, `pl.json`, `pt.json`, `pt-BR.json`.
- Used by: Home Assistant UI.
- Purpose: Dashboard cards and the Theme Builder sidebar panel.
- Location: `custom_components/family_hub/card/*.js` (served at `/family_hub_<name>_card/...`) and `custom_components/family_hub/panel/*.js` (served at `/family_hub_panel/...`). A second copy of several cards also sits at the top level of `custom_components/family_hub/` (for example `family-today-card.js`); see STRUCTURE.md.
- Contains: Each card is a self-contained custom element that talks to HA through `hass` and to the integration through `hass.callWS` websocket commands.
- Depends on: Websocket commands registered in `__init__.py` and the chores/device-settings API modules.
- Used by: Lovelace dashboards that reference the registered resource URLs.

## Data Flow

### Primary Request Path (card reads or writes data)

### Service Call Path (automation or script)

### Polling and Reminder Path (no UI open)

- Durable state: Home Assistant `Store` files per feature (chores, rewards, permissions, routines, goals, pantry extras, device settings, privacy mode, settings history, themes) plus backup files written by `store.py`.
- Runtime state: `hass.data["family_hub"]` dictionary (theme store, per-entry buckets, PIN store, locked popups store, kiosk elevations).
- Frontend state: per-card JavaScript variables and `window.__familyHubI18n` shared translation cache.

## Key Abstractions

- Purpose: One dictionary per config entry holding loaded stores, engine data, and cancel callbacks.
- Examples: `hass.data["family_hub"]["entries"][entry_id]` accessed in `custom_components/family_hub/__init__.py` line 2123 and `chores_websocket_api.py` line 126.
- Pattern: Accessed through small `_get_entry*` helpers; never accessed directly from engines.
- Purpose: Pure feature rules separated from HA plumbing.
- Examples: `custom_components/family_hub/chore_engine.py`, `custom_components/family_hub/reward_engine.py`, `custom_components/family_hub/goal_engine.py`.
- Pattern: Module-level functions taking plain dicts, raising a module-specific exception class.
- Purpose: Uniform creation and loading of `Store` objects with defaults and migrations.
- Examples: `create_chores_store`, `async_load_chores` in `custom_components/family_hub/store.py` lines 71-114.
- Pattern: Factory function returns `Store(hass, version, key)`; loader merges stored data with defaults.
- Purpose: Logic used by both entities and websocket handlers.
- Examples: `custom_components/family_hub/privacy_mode_shared.py` (32 lines), `custom_components/family_hub/device_settings_entity_shared.py` (258 lines).
- Pattern: Import from both the platform files and the API modules to avoid circular imports.

## Entry Points

- Location: `custom_components/family_hub/__init__.py` (`async_setup` line 12390, `async_setup_entry` line 12501, `async_unload_entry` line 13126).
- Triggers: Home Assistant startup and config entry add, reload, or removal.
- Responsibilities: Global registration, per-entry store loading, services, polling, and cleanup.
- Location: `custom_components/family_hub/config_flow.py`.
- Triggers: User adds "Family Hub" in Settings > Devices & Services.
- Responsibilities: Initial configuration and options.
- Location: `custom_components/family_hub/__init__.py` lines 12396-12417 and the registration blocks in `chores_websocket_api.py` and `device_settings_websocket_api.py`.
- Triggers: Frontend cards and the Theme Builder panel.
- Location: `custom_components/family_hub/card/*.js`, `custom_components/family_hub/panel/*.js`, and URL constants in `custom_components/family_hub/const.py` (lines 942-969 and 2277-2318).
- Triggers: Browser loads the Lovelace resource URL.

## Architectural Constraints

- **Threading:** Single asyncio event loop (Home Assistant). All handlers are `async def` or run via `hass` callbacks. Blocking file I/O is confined to the backup helpers in `store.py` (`_write_backup_file`, `_read_backup_file`).
- **Global state:** `hass.data["family_hub"]` (`__init__.py` line 12392) is the only shared mutable container. Module-level constants in `const.py` are read-only. Frontend uses `window.__familyHubI18n` and `window.__familyHub*` globals.
- **Circular imports:** Avoided by keeping `*_shared.py` modules independent and by importing the chores API as `chores_ws_api`. `__init__.py` is the only module that imports the API modules.
- **Naming collision:** `chores_websocket_api.py` must not be imported as `websocket_api` because that name is already bound to Home Assistant's `websocket_api` component.
- **Single entry:** Only one config entry is expected; per-entry buckets are keyed by `entry_id` but code assumes one install.
- **Dependencies:** `manifest.json` lists `frontend`, `http`, `lovelace`, `file_upload`, `image_upload`; `after_dependencies` includes `timer`.

## Anti-Patterns

### Monolithic entry module

### Duplicated frontend helpers

### Duplicated card files at the package root

## Error Handling

- Engines raise, handlers catch and return a `result` string (for example `_send_pin_error` in `chores_websocket_api.py` line 519 and PIN outcomes returned by `async_verify_pin`).
- Storage loaders fall back to defaults when stored data is missing or invalid (`store.py` `async_load_*` functions).
- Backup restore runs only when primary storage is empty (`_maybe_restore_backup`, `store.py` line 371).

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
