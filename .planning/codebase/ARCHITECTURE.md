---
last_mapped_commit: f811e9172bf425ade1c9580c6de2b1b0ef0637ee
last_mapped_at: 2026-10-26
---
<!-- refreshed: 2026-10-26 -->

# Architecture

**Analysis Date:** 2026-10-26

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────┐
│                 Home Assistant frontend (browser / kiosk)             │
│  Lovelace cards (`custom_components/family_hub/card/*.js`)            │
│  Sidebar panel (`custom_components/family_hub/panel/*.js`)            │
│  Shared i18n helper (`__fhT`) and theme helpers inlined per file      │
└──────────────┬───────────────────────────────┬───────────────────────┘
               │ websocket commands            │ HTTP static + services
               ▼                               ▼
┌──────────────────────────────┐   ┌──────────────────────────────────┐
│ Websocket / HTTP layer        │   │ Service layer (hass.services)     │
│ `__init__.py` (`@websocket_   │   │ `__init__.py` `_async_register_*` │
│   api` commands, HomeAssistant│   │ `family_hub.*` services           │
│   View endpoints)             │   │ (`services.yaml`)                 │
│ `chores_websocket_api.py`     │   └───────────────┬──────────────────┘
│ `device_settings_websocket_   │                   │
│   api.py`                     │                   │
└──────────────┬───────────────┘                   │
               ▼                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Domain engines (pure-ish logic, called from handlers)                 │
│ `chore_engine.py` `reward_engine.py` `goal_engine.py`                 │
│ `pantry_engine.py` `timer_engine.py` `routine_engine.py`              │
│ `routine_library.py` `grocery_reference.py` `updater.py`              │
│ `privacy_mode_shared.py` `device_settings_entity_shared.py`           │
└──────────────┬───────────────────────────────────┬───────────────────┘
               ▼                                   ▼
┌──────────────────────────────┐   ┌──────────────────────────────────┐
│ Persistence                   │   │ Entity platforms (HA entities)    │
│ `store.py` (helpers.storage   │   │ `sensor.py` `switch.py` `number.py`│
│  `Store` factories, backups)  │   │ `select.py` `text.py` `button.py` │
│ JSON files in HA `.storage/`  │   │ `todo.py` (todo.* entities)       │
│ + `*_backup` files            │   │ `device_trigger.py`               │
└──────────────────────────────┘   └──────────────────────────────────┘
               ▲
               │ external reads/writes
┌──────────────┴───────────────────────────────────────────────────────┐
│ Home Assistant core: calendar, todo, notify, timer, lovelace,         │
│ frontend, http, file_upload; optional Grocy REST API (`aiohttp`)      │
└──────────────────────────────────────────────────────────────────────┘
```

## Pattern Overview

**Overall:** Single Home Assistant custom integration (monolithic entry module plus domain-specific helper modules) with a thick websocket API layer and a static-asset frontend delivered by the integration itself.

**Key Characteristics:**
- One config entry per install (`config_flow: true` in `custom_components/family_hub/manifest.json`); the entry runtime bucket lives in `hass.data["family_hub"]["entries"][entry_id]` (see `_get_entry_data` in `custom_components/family_hub/chores_websocket_api.py` and `__init__.py` around line 2123).
- Global, domain-level setup happens once in `async_setup` (`custom_components/family_hub/__init__.py` ~line 12390): creates the theme `Store`, registers all websocket commands, and sets up the `hass.data["family_hub"]` container.
- Per-entry setup happens in `async_setup_entry` (`custom_components/family_hub/__init__.py` line 12501) and teardown in `async_unload_entry` (line 13126). Stores are loaded, backups restored if needed, services registered, and polling/timer listeners started via `async_track_time_interval` (lines ~12864 and ~12902).
- Business logic is split into engine modules named `*_engine.py`. Each owns one feature domain (chores, rewards, goals, pantry, timers, routines). Engines raise domain exceptions (`ChoreError` in `custom_components/family_hub/chore_engine.py` line 95, `GoalError` in `goal_engine.py` line 83, `UpdateError` in `updater.py` line 31).
- Frontend is not built or bundled: plain ES5-style JavaScript files are served directly through `homeassistant.components.http` static paths (`*_JS_URL` constants in `custom_components/family_hub/const.py`, e.g. `CARD_JS_URL` line 944, `CHORES_CARD_JS_URL` line 2277).
- Cards share state via `window` globals (for example `window.__familyHubI18n` in `custom_components/family_hub/card/family-today-card.js`), and each card file re-declares its own copy of the helper, so whichever file loads first wins.

## Layers

**Integration bootstrap (entry module):**
- Purpose: Register HA domain/services/websocket commands, static paths, panels, lovelace resources, and per-entry lifecycle.
- Location: `custom_components/family_hub/__init__.py` (13,175 lines; the largest file in the repo).
- Contains: `async_setup`, `async_setup_entry`, `async_unload_entry`, service handlers (`_handle_*`), websocket command handlers (`_ws_*`), theme-generation helpers, reminder/notification polling, Grocy integration, calendar event handling.
- Depends on: every `*_engine.py`, `store.py`, `const.py`, `chores_websocket_api.py`, `device_settings_websocket_api.py`, plus Home Assistant core components.
- Used by: Home Assistant loader (entry point only).

**Websocket API layer:**
- Purpose: Authorize and validate frontend requests, then delegate to engines and stores.
- Location: `custom_components/family_hub/chores_websocket_api.py` (4,543 lines), `custom_components/family_hub/device_settings_websocket_api.py` (859 lines).
- Contains: `_is_admin`, `_has_permission`, `_can_add_rewards` permission checks; PIN hashing and lockout (`_hash_pin`, `_pbkdf2`, `async_verify_pin`, `pin_lockout_remaining`); kiosk elevation; locked-popup handling; notification senders.
- Depends on: `store.py`, `chore_engine.py`, `reward_engine.py`, `pantry_engine.py`, `timer_engine.py`, `routine_engine.py`, `device_settings_entity_shared.py`, `privacy_mode_shared.py`.
- Used by: `__init__.py` imports these modules and registers their handlers. The module is imported as `chores_ws_api` to avoid clashing with HA's `websocket_api` name (see the docstring in `chores_websocket_api.py`).

**Domain engines:**
- Purpose: Feature-specific rules and state transitions.
- Location: `custom_components/family_hub/chore_engine.py`, `reward_engine.py`, `goal_engine.py`, `pantry_engine.py`, `timer_engine.py`, `routine_engine.py`, `routine_library.py`, `grocery_reference.py`, `privacy_mode_shared.py`, `device_settings_entity_shared.py`.
- Contains: Chore scheduling and approval, reward points and redemption, goal progress, pantry stock logic, timer lifecycle, routine templates (`routine_library.py` holds static routine definitions), Grocy reference data.
- Depends on: Store dictionaries passed in by callers; some engines call `hass` directly for notifications (e.g. `send_nudge` in `chore_engine.py` line 1030).
- Used by: websocket handlers, service handlers, and entity platforms.

**Persistence layer:**
- Purpose: Create and load per-feature `homeassistant.helpers.storage.Store` objects and mirror them to backup files.
- Location: `custom_components/family_hub/store.py` (452 lines).
- Contains: `create_*_store` factories (lines 71-103), `async_load_*` functions with defaults (`default_rewards`, `default_routines`, `default_privacy_mode`, and so on), and `_backup_data` / `_maybe_restore_backup` helpers (lines 314-451) that write to `<config>/.../*_backup` files and restore when storage is empty.
- Depends on: `homeassistant.helpers.storage`.
- Used by: `__init__.py` during `async_setup_entry`, and websocket handlers when they save.

**Entity platforms:**
- Purpose: Expose state to Home Assistant as entities.
- Location: `custom_components/family_hub/sensor.py`, `switch.py`, `number.py`, `select.py`, `text.py`, `button.py`, `todo.py`, `device_trigger.py`.
- Contains: Entity classes per platform. `todo.py` (152 lines) registers a `todo.*` entity used as the target for suggestions and lists (see `apply_menu_suggestion` in `__init__.py`). `device_trigger.py` exposes automation triggers.
- Depends on: engines and stores through `hass.data`.
- Used by: Home Assistant entity registry and automations.

**Configuration flow:**
- Purpose: Guided setup and options for the single config entry.
- Location: `custom_components/family_hub/config_flow.py` (1,336 lines). Translations are in `custom_components/family_hub/strings.json`, `en.json`, and `translations/*.json` (de, en, es, fr) plus root-level `de.json`, `en.json`, `es.json`, `fr.json`, `it.json`, `nl.json`, `pl.json`, `pt.json`, `pt-BR.json`.
- Used by: Home Assistant UI.

**Frontend (cards and panel):**
- Purpose: Dashboard cards and the Theme Builder sidebar panel.
- Location: `custom_components/family_hub/card/*.js` (served at `/family_hub_<name>_card/...`) and `custom_components/family_hub/panel/*.js` (served at `/family_hub_panel/...`). A second copy of several cards also sits at the top level of `custom_components/family_hub/` (for example `family-today-card.js`); see STRUCTURE.md.
- Contains: Each card is a self-contained custom element that talks to HA through `hass` and to the integration through `hass.callWS` websocket commands.
- Depends on: Websocket commands registered in `__init__.py` and the chores/device-settings API modules.
- Used by: Lovelace dashboards that reference the registered resource URLs.

## Data Flow

### Primary Request Path (card reads or writes data)

1. A card in `custom_components/family_hub/card/` calls `hass.callWS({type: "family_hub/..."})`, which HA routes to a handler registered in `async_setup` (`custom_components/family_hub/__init__.py` ~lines 12396-12417) or in the chores/device-settings API modules.
2. The handler checks the caller with helpers such as `_is_admin` and `_has_permission` (`custom_components/family_hub/chores_websocket_api.py` lines 314-331), and validates input with `voluptuous` schemas.
3. The handler reads the per-entry bucket from `hass.data["family_hub"]["entries"][entry_id]` (`_get_entry_data`, `chores_websocket_api.py` line 126) and calls the relevant engine (for example `chore_engine.py`).
4. The engine mutates the in-memory dict; the handler persists it through the `Store` (`store.py`) and writes a backup file.
5. The handler returns the result, and the card re-renders. Entity state updates reach other consumers through the entity platforms.

### Service Call Path (automation or script)

1. An automation calls a `family_hub.*` service declared in `custom_components/family_hub/services.yaml`.
2. The handler registered in `_async_register_chore_services` (`__init__.py` line 11975) or the timer registration block (around line 12162) runs in the event loop.
3. The engine updates state; persistence and entity state refresh follow the same steps as the websocket path.

### Polling and Reminder Path (no UI open)

1. `async_setup_entry` registers `async_track_time_interval` callbacks (`__init__.py` ~lines 12864 and 12902). One runs calendar reminder polling with `DEFAULT_POLL_MINUTES` and `DEFAULT_LOOKAHEAD_HOURS` from `const.py`.
2. The poll reads calendar entities through the calendar component (`DATA_COMPONENT` from `homeassistant.components.calendar.const`), fires `notify.*` calls, and records notified keys with retention `NOTIFIED_RETENTION_HOURS`.
3. A daily digest job is scheduled with `async_track_time_change` (`__init__.py` line ~1668 comment).

**State Management:**
- Durable state: Home Assistant `Store` files per feature (chores, rewards, permissions, routines, goals, pantry extras, device settings, privacy mode, settings history, themes) plus backup files written by `store.py`.
- Runtime state: `hass.data["family_hub"]` dictionary (theme store, per-entry buckets, PIN store, locked popups store, kiosk elevations).
- Frontend state: per-card JavaScript variables and `window.__familyHubI18n` shared translation cache.

## Key Abstractions

**Entry runtime bucket:**
- Purpose: One dictionary per config entry holding loaded stores, engine data, and cancel callbacks.
- Examples: `hass.data["family_hub"]["entries"][entry_id]` accessed in `custom_components/family_hub/__init__.py` line 2123 and `chores_websocket_api.py` line 126.
- Pattern: Accessed through small `_get_entry*` helpers; never accessed directly from engines.

**Engines:**
- Purpose: Pure feature rules separated from HA plumbing.
- Examples: `custom_components/family_hub/chore_engine.py`, `custom_components/family_hub/reward_engine.py`, `custom_components/family_hub/goal_engine.py`.
- Pattern: Module-level functions taking plain dicts, raising a module-specific exception class.

**Storage factories:**
- Purpose: Uniform creation and loading of `Store` objects with defaults and migrations.
- Examples: `create_chores_store`, `async_load_chores` in `custom_components/family_hub/store.py` lines 71-114.
- Pattern: Factory function returns `Store(hass, version, key)`; loader merges stored data with defaults.

**Shared module helpers:**
- Purpose: Logic used by both entities and websocket handlers.
- Examples: `custom_components/family_hub/privacy_mode_shared.py` (32 lines), `custom_components/family_hub/device_settings_entity_shared.py` (258 lines).
- Pattern: Import from both the platform files and the API modules to avoid circular imports.

## Entry Points

**Home Assistant integration loader:**
- Location: `custom_components/family_hub/__init__.py` (`async_setup` line 12390, `async_setup_entry` line 12501, `async_unload_entry` line 13126).
- Triggers: Home Assistant startup and config entry add, reload, or removal.
- Responsibilities: Global registration, per-entry store loading, services, polling, and cleanup.

**Config flow:**
- Location: `custom_components/family_hub/config_flow.py`.
- Triggers: User adds "Family Hub" in Settings > Devices & Services.
- Responsibilities: Initial configuration and options.

**Websocket commands:**
- Location: `custom_components/family_hub/__init__.py` lines 12396-12417 and the registration blocks in `chores_websocket_api.py` and `device_settings_websocket_api.py`.
- Triggers: Frontend cards and the Theme Builder panel.

**Frontend resources:**
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

**What happens:** `custom_components/family_hub/__init__.py` holds about 13,000 lines of service handlers, websocket commands, theme generation, reminder polling, Grocy integration, and calendar handling.
**Why it's wrong:** Changes are hard to review, and import-time side effects and name collisions (see the `websocket_api` note above) are easy to introduce.
**Do this instead:** Put new feature logic in a dedicated `*_engine.py` module and register its handlers from a dedicated `*_websocket_api.py` module, as `chores_websocket_api.py` and `device_settings_websocket_api.py` already do.

### Duplicated frontend helpers

**What happens:** Each card under `custom_components/family_hub/card/` re-declares `__fhT`, `__fhEsc`, and `__fhSweep` (see the header of `card/family-today-card.js`).
**Why it's wrong:** Fixes must be copied into every file, and the first file loaded sets the shared helper for all cards.
**Do this instead:** Keep the shared helper block identical across files and edit them together. Do not introduce a second helper variant.

### Duplicated card files at the package root

**What happens:** Files such as `custom_components/family_hub/family-today-card.js` and `custom_components/family_hub/card/family-today-card.js` both exist, and the same is true for the panel and theme-selector files.
**Why it's wrong:** It is unclear which copy is served. The URL constants in `const.py` point to the `card/` and `panel/` subdirectories.
**Do this instead:** Edit only the copy under `card/` or `panel/`, which are the paths referenced by `const.py`.

## Error Handling

**Strategy:** Domain exceptions inside engines (`ChoreError`, `RewardError`, `GoalError`, `RoutineError`, `TimerError`, `PantryError`, `UpdateError`) are caught by the websocket handler layer and returned to the frontend via `connection.send_error` (about 195 call sites). `ServiceValidationError` is not used.

**Patterns:**
- Engines raise, handlers catch and return a `result` string (for example `_send_pin_error` in `chores_websocket_api.py` line 519 and PIN outcomes returned by `async_verify_pin`).
- Storage loaders fall back to defaults when stored data is missing or invalid (`store.py` `async_load_*` functions).
- Backup restore runs only when primary storage is empty (`_maybe_restore_backup`, `store.py` line 371).

## Cross-Cutting Concerns

**Logging:** Standard `logging.getLogger(__name__)` through Home Assistant's logger; no custom sink.
**Validation:** `voluptuous` schemas on websocket and service inputs; `_hash_pin` and `_pbkdf2` for PIN storage.
**Authentication:** Home Assistant user context (`connection.user`, `_actor_id`); admin checks via `_is_admin`; per-feature permissions stored in the permissions store (`async_load_permissions`, `store.py` line 201); kiosk PIN elevation with lockout.

---

*Architecture analysis: 2026-10-26*
