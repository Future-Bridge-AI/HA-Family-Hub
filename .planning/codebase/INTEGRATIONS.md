---
last_mapped_commit: f811e9172bf425ade1c9580c6de2b1b0ef0637ee
last_mapped_at: 2026-10-26
---
# External Integrations

**Analysis Date:** 2026-10-26

## APIs & External Services

**Grocy (optional, self-hosted grocery/ERP):**
- Purpose: recipes, product/stock lookup, shopping list, stock consume/purchase, file (image) storage, quantity-unit conversions
- SDK/Client: none; raw REST calls via `aiohttp` through HA's shared session (`async_get_clientsession(hass)`) in `custom_components/family_hub/__init__.py`
- Helpers: `_grocy_api_get`, `_grocy_api_post`, `_grocy_api_put`, `_grocy_api_delete`, `_grocy_api_upload_file`, `_grocy_api_get_file_bytes` in `custom_components/family_hub/__init__.py` (~lines 4201-4330)
- Endpoints used (examples): `{url}/api/objects/recipes`, `{url}/api/objects/recipes/{id}`, `{url}/api/objects/products`, `{url}/api/objects/quantity_unit_conversions/{id}`, `{url}/api/objects/shopping_list/{id}`, `{url}/api/recipes/{id}/add-not-fulfilled-products-to-shoppinglist`, `{url}/api/files/{group}/{base64-filename}`, `{url}/recipe/{id}` (link only)
- Auth: `GROCY-API-KEY` request header, value from config-entry option `CONF_GROCY_API_KEY` (`grocy_api_key`) defined in `custom_components/family_hub/const.py`
- Timeouts: 10 s for JSON calls, 20 s for file transfers
- Config UI: `async_step_grocy` in `custom_components/family_hub/config_flow.py`
- Feature docs: `website/docs/features/grocy-integration.md`, `DOCUMENTATION.md` (section "Grocy integration (optional)")

**Arbitrary recipe web pages (user-supplied URLs):**
- Purpose: "Import a Recipe" pulls schema.org `Recipe` JSON-LD from a web page the user names
- Implementation: `_extract_json_ld_recipe` and the recipe-import websocket handler in `custom_components/family_hub/__init__.py` (~lines 6470-6600); fetched via `async_get_clientsession(hass)` with manual redirect handling
- Safety: only `http://` / `https://` accepted; `_recipe_url_block_reason` blocks private/local addresses for non-admin users; admins may reach the home network (for self-hosted recipe servers). Redirects re-checked per hop.
- Auth: none (public pages)

**Google Fonts:**
- Purpose: display font "Varela Round"
- Loaded at runtime by injecting `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Varela+Round&display=swap">` into cards: `custom_components/family_hub/card/family-hub-chores-card.js` (line ~74), `family-hub-rewards-card.js`, `family-right-now-card.js`, `family-today-card.js`, `family-week-calendar-card.js` (line ~122), and the root-level duplicates in `custom_components/family_hub/*.js`
- Auth: none

**Images from user-supplied URLs:**
- Recipe photos, dish images, link previews, screensaver video/images, and wish-list images are referenced by URL in the cards (`custom_components/family_hub/card/family-week-calendar-card.js`, `family-hub-todo-card.js`, `family-hub-recipe-box-card.js`). Image URLs can be proxied/fetched through the HA server in `custom_components/family_hub/__init__.py` (image-type detection by path extension near line ~4348).
- Local paths like `/local/...` are also accepted.

**Documentation site / project links (not runtime):**
- GitHub repository `https://github.com/JVarhol/HA-Family-Hub` (issues, releases, badges in `README.md`; `documentation` / `issue_tracker` in `custom_components/family_hub/manifest.json`)
- Docs site `https://jvarhol.github.io/HA-Family-Hub/` (`.github/workflows/deploy-docs.yml`, `website/docusaurus.config.js`)
- Shields.io badges in `README.md`
- Holiday background and product reference data are static content in the repo (e.g. `custom_components/family_hub/grocery_reference.py`); no runtime holiday API was detected.

## Home Assistant Services Used (internal to HA, not external)

Family Hub is tightly coupled to HA core integrations via `hass.services.async_call` and `hass.components` APIs (`custom_components/family_hub/__init__.py`):

**Calendars:**
- `calendar.*` entities (local calendar, CalDAV, Google Calendar, etc.) are read through HA's calendar component (`homeassistant.components.calendar`, `DATA_COMPONENT`) and `calendar.get_events` via `hass.services` / `callApi`
- Writes: `calendar.create_event`, `calendar.update_event`, and a delete path via the calendar component (`custom_components/family_hub/__init__.py` ~lines 3818-3960)
- Frontend reads events with `this._hass.callApi(...)` in `custom_components/family_hub/card/family-week-calendar-card.js`

**To-do lists (primary data store for recipes, meal plan, reminders, wish lists):**
- `todo.*` entities via `homeassistant.components.todo` and the `todo` services `add_item`, `update_item`, `remove_item` (`custom_components/family_hub/todo.py`; `family-week-calendar-card.js` ~lines 14075-14270)
- Documented setup: `website/docs/requirements.md` (Local To-do integration recommended)

**Notifications:**
- `notify.*` services (e.g. `notify.mobile_app_<slug>`) used for calendar reminders, event alerts, daily digest, and chore/reward notifications
- Parsing and routing: `_parse_overrides`, `_split_notify_target`, notify target discovery near `custom_components/family_hub/__init__.py` lines ~655-2000, push payload building near line ~10195
- Companion app is the documented target (`website/docs/requirements.md`)

**Timers:**
- Native HA `timer` helpers are created automatically (`after_dependencies: ["timer"]` in `custom_components/family_hub/manifest.json`); `custom_components/family_hub/timer_engine.py`

**Media / TTS / Assist (alarm device candidates):**
- Enumerates `media_player`, `assist_satellite`, and `tts` entities for alarm/announcement targets (`__init__.py` ~line 9974)

**Lovelace / Frontend / HTTP:**
- `frontend` dependency: panel registration and `add_extra_js_url`-style card loading (`custom_components/family_hub/const.py` URL constants)
- `lovelace` dependency: storage-mode dashboards are inspected/modified via Lovelace's storage collection (`__init__.py` ~lines 12193-12330)
- `http` dependency: `HomeAssistantView` endpoints such as `FamilyHubSettingsHistoryExportView` (`__init__.py` ~line 1724, `requires_auth = True`), and static paths via `StaticPathConfig` (`__init__.py` ~lines 12553-12558)
- `file_upload` / `image_upload` dependencies: used for image upload into HA; theme/background images go through HA storage
- Lovelace theme sync: native HA theme integration is updated from Family Hub's Theme Builder (`custom_components/family_hub/panel/theme-builder-panel.js`, `__init__.py` theme section ~line 229)

## Data Storage

**Databases:**
- None. No SQL/NoSQL database client is used.

**Persistent storage (HA-managed):**
- `homeassistant.helpers.storage.Store` JSON files under HA's `.storage/` directory. Per-entry key prefixes from `custom_components/family_hub/const.py` (e.g. `SETTINGS_STORAGE_KEY_PREFIX`, `RECIPES_STORAGE_KEY_PREFIX`, `TIMERS_STORAGE_KEY_PREFIX`, `REMINDERS_STORAGE_KEY_PREFIX`, `GROCERY_PUSHED_STORAGE_KEY_PREFIX`, `THEME_STORAGE_KEY`, `DAILY_DIGEST_STORAGE_KEY_PREFIX`, `EVENT_CHECKLISTS_STORAGE_KEY_PREFIX`, `SETTINGS_HISTORY_STORAGE_KEY_PREFIX`, `DEVICE_SETTINGS_STORAGE_KEY_PREFIX`)
- Write-once snapshots in `__init__.py` (e.g. settings-history export at `/api/family_hub/settings_history_export/{entry_id}/{index}`)

**File Storage:**
- Local filesystem only, inside the HA config directory. Recipe/dish/screensaver images may also be uploaded to Grocy's file store when Grocy is configured (`_grocy_api_upload_file`).
- Self-update: uploaded zip is validated and extracted into the integration directory by `custom_components/family_hub/updater.py` (20 MB max upload, 200 MB max uncompressed, path-traversal checks).

**Caching:**
- None external. In-memory caches within the Python process only.

## Authentication & Identity

**Auth Provider:**
- Home Assistant users/authentication. Websocket commands and HTTP views rely on HA's auth; admin-only operations use `@require_admin` decorators in `custom_components/family_hub/__init__.py` (~line 4025) and `require_admin=False` options on some websocket commands (~line 12619).
- Frontend calls authenticate through HA's `hass` object: `this._hass.fetchWithAuth` (preferred) falling back to `fetch` with headers (`custom_components/family_hub/card/family-week-calendar-card.js` ~lines 2228-2233).

**Kiosk / PIN:**
- Per-user kiosk PINs stored as PBKDF2-HMAC-SHA256 hashes (`custom_components/family_hub/chores_websocket_api.py`): `PIN_PBKDF2_ITERATIONS = 120_000`, random 16-byte salt via `secrets.token_hex(16)`, comparison with `hmac.compare_digest`. Hashing runs in an executor.
- A legacy SHA-256 salted-hash path exists (`chores_websocket_api.py` ~line 372) for migration.

**Grocy:**
- API key auth as described above (`GROCY-API-KEY` header). The key is held in config-entry options.

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry or similar detected.

**Logs:**
- Python `logging` via HA's logger (`_LOGGER = logging.getLogger(__name__)` pattern in `custom_components/family_hub/*.py`). No external log shipping.

## CI/CD & Deployment

**Hosting:**
- Integration: distributed through HACS as a custom repository (`hacs.json`); installed into a user's Home Assistant instance.
- Docs: GitHub Pages (`.github/workflows/deploy-docs.yml`, `website/build` artifact).

**CI Pipeline:**
- GitHub Actions: `.github/workflows/deploy-docs.yml` only. Triggered on push to `main` affecting `website/**` or the workflow file, plus manual dispatch. No backend test or lint workflow is tracked.

**Issue templates:**
- `.github/ISSUE_TEMPLATE/bug_report.md`, `family_request.md`, `feature_request.md`

## Environment Configuration

**Required env vars:**
- None read by the integration.

**Required HA configuration (documented in `website/docs/requirements.md`):**
- At least one `calendar.*` entity to show events
- `todo.*` entities for recipe box, meal plan, meal templates, meal suggestions, and standalone reminders (e.g. `todo.recipe_box`, `todo.meal_plan`, `todo.family_reminders`)
- Optional `notify.*` targets for reminders, event alerts, and Daily Digest

**Optional configuration:**
- Grocy URL and API key (`grocy_url`, `grocy_api_key`) set in Settings > Devices & Services > Family Hub > Configure > Grocy

**Secrets location:**
- Grocy API key is stored in the Family Hub config entry options (HA `.storage/core.config_entries`). No `.env` file is used by the integration. Repository `.gitignore` does not exclude `.env*`; none was found in the tracked tree.

## Webhooks & Callbacks

**Incoming:**
- HTTP views served by HA (`requires_auth = True` for the settings history export at `/api/family_hub/settings_history_export/{entry_id}/{index}`), plus websocket commands under `family_hub/*` (e.g. `family_hub/get_grocy_recipes`, `family_hub/create_grocy_recipe`, calendar and chore commands in `custom_components/family_hub/__init__.py`, `chores_websocket_api.py`, `device_settings_websocket_api.py`)
- Static asset endpoints: `/family_hub_card/...`, `/family_hub_panel/...`, `/family_hub_today_card/...`, `/family_hub_screensaver_card/...`, `/family_hub_chores_card/...`, `/family_hub_todo_card/...`, `/family_hub_recipe_box_card/...`, etc. (`custom_components/family_hub/const.py`)

**Outgoing:**
- Grocy REST calls (see above) and recipe page fetches for import (see above)
- Google Fonts CSS request from each card at load time
- HA service calls: `notify.*`, `calendar.*`, `todo.*`, timer services, and media/TTS services listed above. No direct third-party webhooks were detected.

---

*Integration audit: 2026-10-26*
