---
last_mapped_commit: f811e9172bf425ade1c9580c6de2b1b0ef0637ee
last_mapped_at: 2026-10-26
---
# Coding Conventions

**Analysis Date:** 2026-10-26

## Naming Patterns

**Files:**
- Python modules use `snake_case` and are flat inside the integration package: `custom_components/family_hub/chore_engine.py`, `reward_engine.py`, `pantry_engine.py`, `chores_websocket_api.py`, `device_settings_websocket_api.py`.
- Home Assistant platform modules are named after the platform: `sensor.py`, `switch.py`, `number.py`, `select.py`, `text.py`, `button.py`, `todo.py`, `device_trigger.py`.
- Engine modules (pure business logic, no `hass` dependency) use the suffix `_engine.py`. Websocket handler modules use the suffix `_websocket_api.py`. Shared helpers use `_shared.py` (`privacy_mode_shared.py`, `device_settings_entity_shared.py`).
- Frontend cards are kebab-case JavaScript files under `custom_components/family_hub/card/`, named `family-hub-<name>-card.js` (e.g. `family-hub-pantry-card.js`) or `family-<name>-card.js` (e.g. `family-today-card.js`, `family-right-now-card.js`). Panels live in `custom_components/family_hub/panel/`.
- Translation files are locale codes: `en.json`, `de.json`, `pt-BR.json`. Both `custom_components/family_hub/translations/` and the top-level `custom_components/family_hub/*.json` exist; treat `translations/` as the location Home Assistant reads.
- Do not add files with a `.bak_*` suffix. One exists (`card/family-week-calendar-card.js.bak_divfix`) and is leftover debris, not a convention to copy.

**Functions:**
- `snake_case` for all Python functions. Private helpers are prefixed with a single underscore: `_check_user_enabled`, `_now_iso`, `_get_extra`, `_entry_data_or_error`.
- Async Python functions use the `async_` prefix for Home Assistant-facing entry points (`async_setup_entry`, `async_load_locked_popups`) and are `async def` directly. Websocket handlers are named `ws_<feature>_<action>` (e.g. `ws_more_menu_locked_set`, `ws_more_menu_unlock_options` in `custom_components/family_hub/chores_websocket_api.py`).
- Factory helpers for new records are named `default_<thing>` (`default_pantry_extra`) and ID generators `new_<thing>_id` (`new_chore_id`, `new_group_id`, `new_pantry_extra_id`).
- JavaScript card methods are `camelCase` and private methods are underscore-prefixed (`_applyThemeVars`, `_headerTitleFontSize`, `_saveSettings`, `_onClick`).
- Global helpers in card files use the `__fh` prefix for shared, byte-identical copies across cards: `__fhI18n`, `__fhEsc`, `__fhT`, `__fhSweep` (`custom_components/family_hub/card/family-hub-pantry-card.js`). Keep these identical across files.

**Variables:**
- Python: `snake_case` locals. Module-level constants are `UPPER_SNAKE_CASE` and are defined in `custom_components/family_hub/const.py`.
- Storage key constants follow `<THING>_KEY_<FIELD>` for record field names (`CHORE_KEY_COMPLETED_AT`, `CHORE_KEY_QUANTITY_REMAINING`) and `<THING>_STATUS_*` for state values (`CHORE_STATUS_*`). Always reference these constants rather than string literals when touching chore records.
- Assignment-mode and unit enums are constant tuples: `CHORE_ASSIGNMENT_MODES`, `CHORE_RECUR_INTERVAL_UNITS`.
- Logger: `_LOGGER = logging.getLogger(__name__)` at module top (`custom_components/family_hub/chore_engine.py`, `button.py`, `__init__.py`). Some modules use `logger`/`LOGGER` via `logging.getLogger(__name__)` directly; prefer `_LOGGER`.
- JavaScript: `camelCase` for everything. Config keys in settings are camelCase too (`useGlobalTheme`, `globalThemeId`, `notifyRewardClaimed`, `userProfiles`).

**Types and classes:**
- Python classes are `PascalCase`. Domain error classes follow `<Domain>Error` and subclass `Exception` with a `code` attribute: `ChoreError` (`chore_engine.py:95`), `RewardError` (`reward_engine.py:68`), `GoalError`, `PantryError` (`pantry_engine.py:43`), `RoutineError`, `TimerError`, `UpdateError` (`updater.py:31`).
- Frontend custom elements are `FamilyHub<Name>Card` classes registered with `customElements.define("family-hub-<name>-card", ...)`, with a matching `FamilyHub<Name>CardEditor` for the Lovelace editor (`family-hub-pantry-card.js:371`, `:1634`).
- Custom element names must contain a hyphen, and element tag names are the kebab-case registration string.

## Code Style

**Python formatting:**
- No formatter config is committed (no `pyproject.toml`, `setup.cfg`, `.flake8`, `ruff.toml`, or `.pre-commit-config.yaml`). Follow the observed style rather than a tool default.
- Strings: double quotes dominate (`custom_components/family_hub/chore_engine.py`: about 290 lines containing `"` versus about 100 containing `'`). Use double quotes.
- Line length: long lines are common. About 1 in 125 Python lines exceeds 120 characters across the package; the longest seen is about 150. Break long dict literals and function signatures across lines when they grow past about 120, but do not reflow existing long lines just to shorten them.
- Every Python module that defines functions starts with `from __future__ import annotations` (verified in all modules except `const.py`). Keep that as the first statement after the module docstring.
- Type hints are used on public functions: `dict[str, Any]`, `Optional[...]`, `Callable[...]`. Prefer `Optional[X]` and `dict[...]` (PEP 585 builtins) as already used in `chore_engine.py`.

**JavaScript formatting:**
- No ESLint or Prettier config is committed. Cards are hand-formatted with semicolons and double quotes.
- Modern declarations (`const`, `let`) are the norm in cards. A few shared bootstrap blocks use `var` on purpose so they attach to `window` identically across files (`var __fhI18n = (window.__familyHubI18n = ...)` in `custom_components/family_hub/card/family-hub-pantry-card.js`). Do not change those to `let`/`const`.
- Cards are standalone IIFE-free single files. Each card copies shared boilerplate (`PALETTE`, theme handling, `_esc`/`_escAttr`, the translation helper) rather than importing it, per the project's documented convention. When changing shared helpers, update every card copy.

**Linting:**
- Not configured. There is no lint step in CI (`.github/workflows/deploy-docs.yml` only builds the Docusaurus site under `website/`).

## Import Organization

**Python order (observed in `custom_components/family_hub/chore_engine.py`):**
1. Standard library (`calendar`, `logging`, `uuid`, `datetime`, `typing`)
2. Home Assistant imports (`homeassistant.core`, `homeassistant.config_entries`, `homeassistant.util`)
3. Relative sibling imports (`from . import timer_engine`)
4. Relative `from .const import (...)` block, one name per line, alphabetical-ish and grouped by feature

**Rules:**
- Engine modules must not import `homeassistant` at runtime when avoidable. Their module docstrings state this explicitly (e.g. `chore_engine.py` and `reward_engine.py` deliberately stay hass-free). Side effects such as notifications and bus events belong in the call sites (`chores_websocket_api.py`, `__init__.py`).
- Circular imports are avoided by duplicating small helpers rather than importing across the boundary. `chores_websocket_api.py` keeps a local copy of `_split_notify_target`/`_notification_click_data`, and `__init__.py` keeps `_notify_chore_approved_native` as a deliberate duplicate of the websocket-side function. Follow that pattern rather than adding an import cycle.
- Path aliases: not applicable (Python package-relative imports only). Frontend cards load via absolute `/family_hub/...` resource URLs registered in `__init__.py`, not via bundler aliases.

## Error Handling

**Backend (Python) pattern:**
- Engine modules raise a domain error with a machine-readable `code` and a human message:
  ```python
  raise PantryError("invalid_name", "This item needs a name.")
  raise PantryError("not_found", f"No pantry item with id {extra_id!r}")
  ```
  (`custom_components/family_hub/pantry_engine.py:86`, `:102`)
- Websocket handlers catch the engine error and forward `code` and message to the client with `connection.send_error(msg["id"], err.code, str(err))`. Do not build a big `if/elif` ladder that guesses the reason from message text.
- Websocket handlers check permissions themselves before calling engines, using `connection.user.is_admin` or the permission catalog. Engine functions never check permissions (documented in `chore_engine.py`'s module docstring).
- Standard send-error shape for websocket handlers, with a stable code and a user-facing sentence:
  ```python
  connection.send_error(msg["id"], "forbidden", "Only an admin can change a locked pop-up.")
  connection.send_error(msg["id"], "not_found", "That button isn't saved as locked.")
  ```
  (`custom_components/family_hub/chores_websocket_api.py:636`, `:640`)
- Broad `except Exception as err:` is common (about 145 occurrences) around best-effort operations such as notifications, external Grocy calls, and optional lookups. Use it only where failure must not break the caller, and log the failure at `_LOGGER.warning` or `_LOGGER.debug`. Do not swallow silently.
- `except (TypeError, ValueError)` is the standard guard when parsing user-supplied values such as dates and numbers.
- Storage writes are batched: callers do exactly one `await store.async_save(...)` per websocket or service call (documented in `chore_engine.py`'s module docstring). Engines never save the store themselves.

**Frontend (JavaScript) pattern:**
- Websocket calls are awaited inside `try`/`catch`. Show user feedback through the card's own status or toast helper and re-fetch state after a mutation (the rewards card re-fetches after `_deleteRedemption`/`_reverseRedemption`).
- Malformed client-side values are validated and degraded to a safe default rather than thrown, e.g. hex colors re-validated with `/^#[0-9a-fA-F]{6}$/` and falling back to no inline style.

## Logging

**Framework:** Python `logging` via `_LOGGER = logging.getLogger(__name__)`.

**Usage counts across the package:** `_LOGGER.warning` (about 70), `_LOGGER.debug` (about 30), `_LOGGER.info` (about 9). Errors that the user must act on are `warning`; routine tracing is `debug`.

**Patterns:**
- Log with `%s` lazy formatting, not f-strings, in new code.
- Do not use `print()` in integration code. Print statements exist only in legacy standalone test scripts (see TESTING.md).
- Frontend uses `console.warn`/`console.error` sparingly; do not leave debug `console.log` in committed cards.

## Comments

**When to comment:**
- The codebase is heavily commented with design rationale, not restatement. Module docstrings explain the state machine, permission model, storage ownership, and why a module is split the way it is (see `chore_engine.py`, `pantry_engine.py`, `const.py`).
- Version tags in comments are common (`v1.168.76`, `v122`). Keep them when editing nearby logic, but do not add new version-stamped narration to new code. Put the reasoning, not the changelog, in the comment.
- Explain non-obvious constraints: browser/WebView rendering quirks (the `background` on `<input type="color">` note), circular-import avoidance, storage key preservation for migrations (`THEME_STORAGE_KEY` in `const.py`).

**JSDoc/TSDoc and docstrings:**
- Python: triple-double-quoted module docstrings on every engine module, and one-line or short multi-line docstrings on public functions and websocket handlers. Argument and return types are documented in type hints, not docstrings.
- JavaScript: `//` line comments above classes and shared blocks. No JSDoc enforced.

## Function Design

**Size:** Engine functions are small and single-purpose. Websocket handler functions are longer because they include permission, lookup, validation, and save steps in sequence. Keep handler bodies in the same order: resolve entry data, check permission, load, mutate, save once, send result.

**Parameters:**
- Websocket handlers take `(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict)` and return `None`. They are decorated with `@websocket_api.websocket_command({vol.Required("type"): "family_hub/..."})` and `@websocket_api.async_response`.
- Engine functions take the plain record dict (or the store dict) and payload dict, not `hass`.

**Return values:**
- Engine mutators return the updated record dict. Websocket handlers reply with `connection.send_result(msg["id"], {...})`.
- Use `Optional[X]` plus an early `return` for lookups that may be absent, and let the caller decide whether that is an error (`_entry_data_or_error` returns `None` after sending the error).

## Module Design

**Exports:**
- No `__all__` convention. Public names are plain, underscore-free functions and constants; internal helpers are underscore-prefixed.
- Platform modules (`sensor.py`, `switch.py`, etc.) expose `async_setup_entry` and entity classes. Entity classes are `PascalCase` and named after the feature.

**Barrel files:**
- None. Import the specific engine module (`from . import timer_engine`) rather than re-exporting through `__init__.py`.

**Data shape:**
- Records are plain dicts keyed by `*_KEY_*` constants, not dataclasses. Keep new fields as dict keys defined in `const.py` and default them in a `default_<thing>()` factory.
- Settings and per-user profiles are stored under the `settings` store and normalized on read (`_normalizeUserProfiles` on the card side, `_get_user_profiles` on the server side). New fields need defaults in both places.

## Where to Place New Conventions

- New backend constants: `custom_components/family_hub/const.py`.
- New engine logic: a new `*_engine.py` module with a `<Domain>Error` class and no `hass` import.
- New websocket commands: the matching `*_websocket_api.py` module, registered in that module's `ALL_COMMANDS` list.
- New card: a new file under `custom_components/family_hub/card/` following the `FamilyHub<Name>Card` / `FamilyHub<Name>CardEditor` pattern and copying the shared `__fh*` boilerplate.

---

*Convention analysis: 2026-10-26*
