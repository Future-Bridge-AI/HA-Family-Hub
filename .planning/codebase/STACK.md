---
last_mapped_commit: f811e9172bf425ade1c9580c6de2b1b0ef0637ee
last_mapped_at: 2026-10-26
---
# Technology Stack

**Analysis Date:** 2026-10-26

## Languages

**Primary:**
- Python (3.10+ implied; `dict | None` annotations and `from __future__ import annotations` used throughout; `__pycache__` contains `cpython-310` and `cpython-314` bytecode) - Home Assistant custom integration backend in `custom_components/family_hub/*.py` (largest file: `custom_components/family_hub/__init__.py`, ~13,175 lines)
- JavaScript (ES modules / custom elements, no transpilation) - Lovelace cards and panels in `custom_components/family_hub/card/*.js`, `custom_components/family_hub/panel/*.js`, and root-level copies of the same files in `custom_components/family_hub/*.js`

**Secondary:**
- JSON - translations and HA metadata: `custom_components/family_hub/en.json`, `de.json`, `es.json`, `fr.json`, `it.json`, `nl.json`, `pl.json`, `pt.json`, `pt-BR.json`, `custom_components/family_hub/translations/{en,de,es,fr}.json`, `custom_components/family_hub/strings.json`, `custom_components/family_hub/manifest.json`, `hacs.json`
- YAML - HA service definitions in `custom_components/family_hub/services.yaml`
- Markdown / MDX - documentation in `website/docs/**`, `DOCUMENTATION.md`, `README.md`, `CHANGELOG.md`
- JavaScript (React JSX in `.js`) - docs site components in `website/src/components/HomepageFeatures/index.js`, `website/src/pages/index.js`
- CSS - docs site styling in `website/src/css/custom.css` and CSS modules under `website/src/**`
- YAML - CI workflow `.github/workflows/deploy-docs.yml`; CMS config `website/static/admin/config.yml`

## Runtime

**Backend environment:**
- Home Assistant Core (custom integration loaded from `custom_components/family_hub/`); minimum supported HA version declared as `homeassistant: 2024.1.0` in `hacs.json`
- Asyncio event loop; blocking work is pushed to executors (e.g. `hass.async_add_executor_job` used for PBKDF2 PIN hashing in `custom_components/family_hub/chores_websocket_api.py` and the zip updater in `custom_components/family_hub/updater.py`)

**Frontend environment:**
- Browsers and HA companion/kiosk WebViews rendering Lovelace dashboards; cards are registered as Web Components via `customElements.define(...)` in each file under `custom_components/family_hub/card/` and `custom_components/family_hub/panel/`

**Docs site environment:**
- Node.js `>=20.0` (`website/package.json` `engines`); CI uses Node 20 (`.github/workflows/deploy-docs.yml`)

**Package Manager:**
- Backend: none. No `requirements.txt`, `pyproject.toml`, or `setup.py` exists; Python dependencies are provided by Home Assistant itself.
- Docs: npm
  - Lockfile: present (`website/package-lock.json`)
- Frontend cards: none. No `package.json` at the integration level; JS files are plain modules shipped as-is.

## Frameworks

**Core (backend):**
- Home Assistant Core APIs - the integration is built on:
  - `homeassistant.config_entries`, `homeassistant.core`, `homeassistant.helpers.*` (`storage.Store`, `event`, `entity`, `typing`, `aiohttp_client`, `trigger`)
  - Entity platforms: `button.py`, `number.py`, `select.py`, `sensor.py`, `switch.py`, `text.py`, `todo.py`, plus `device_trigger.py`
  - `homeassistant.components.http` (`HomeAssistantView`, `StaticPathConfig`), `homeassistant.components.calendar` (`DATA_COMPONENT`), `homeassistant.components.todo`, `homeassistant.components.device_automation`, `homeassistant.components.homeassistant.triggers`
- Config flow UI: `custom_components/family_hub/config_flow.py` (`config_flow: true` in `custom_components/family_hub/manifest.json`)
- Declared HA dependencies (`custom_components/family_hub/manifest.json`): `frontend`, `http`, `lovelace`, `file_upload`, `image_upload`; after-dependency: `timer`

**Core (frontend):**
- Vanilla Web Components / custom elements; no UI framework and no bundler. Examples: `custom_components/family_hub/card/family-week-calendar-card.js`, `custom_components/family_hub/card/family-hub-todo-card.js`, `custom_components/family_hub/panel/theme-builder-panel.js`
- Cards are served as static JS through `StaticPathConfig` registrations (URL constants in `custom_components/family_hub/const.py`, e.g. `CARD_JS_URL = "/family_hub_card/family-week-calendar-card.js"`)

**Testing:**
- Not detected. No test directories, test files, or pytest/vitest/jest configuration are tracked in the repository (`.pytest_cache/` is git-ignored in `.gitignore`).

**Build/Dev (docs site):**
- Docusaurus `3.10.2` - `@docusaurus/core`, `@docusaurus/preset-classic`, `@docusaurus/faster`, `@docusaurus/module-type-aliases`, `@docusaurus/types` (`website/package.json`)
- Config: `website/docusaurus.config.js`, sidebars in `website/sidebars.js`
- Scripts: `build`, `start`, `serve`, `deploy`, `clear`, `swizzle`, `write-translations`, `write-heading-ids` (`website/package.json`)

## Key Dependencies

**Backend (imported at runtime):**
- `aiohttp` - outbound HTTP client and `web` types; used with `async_get_clientsession(hass)` from `homeassistant.helpers.aiohttp_client` for Grocy REST calls, recipe URL fetching, and file uploads in `custom_components/family_hub/__init__.py` (imports at lines ~47, ~52, ~75)
- `voluptuous` - websocket and service schema validation (`vol.Required`, `vol.Coerce`, `vol.Any`) in `custom_components/family_hub/__init__.py` and `custom_components/family_hub/chores_websocket_api.py`
- Standard library only beyond the above: `asyncio`, `hashlib` (sha256, pbkdf2_hmac), `hmac` (`compare_digest`), `secrets` (`token_hex`), `uuid`, `zipfile`, `shutil`, `tempfile`, `base64`, `ipaddress`, `difflib`, `html`, `json`, `re`, `datetime`, `calendar`, `itertools`, `math`, `time`, `os`, `io`, `pathlib`, `urllib.parse`

**Frontend (external, runtime-loaded):**
- Google Fonts stylesheet `Varela Round` loaded at runtime by injecting a `<link>` into each card, e.g. `custom_components/family_hub/card/family-today-card.js` (line ~74), `custom_components/family_hub/card/family-week-calendar-card.js` (line ~122). No font files are bundled.

**Docs site (npm, `website/package.json`):**
- `react` `^19.0.0`, `react-dom` `^19.0.0`, `@mdx-js/react` `^3.0.0`
- `clsx` `^2.0.0`, `prism-react-renderer` `^2.3.0`
- `@easyops-cn/docusaurus-search-local` `^0.55.3` (local search plugin)

**Infrastructure:**
- GitHub Actions (`.github/workflows/deploy-docs.yml`): `actions/checkout@v4`, `actions/setup-node@v4`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`
- HACS distribution metadata: `hacs.json` (`render_readme: true`) and `custom_components/family_hub/manifest.json` (`version: 1.168.85`, `iot_class: local_polling`)

## Configuration

**Integration configuration:**
- Configured entirely through the HA config-entry UI (`custom_components/family_hub/config_flow.py`); settings are stored in config-entry `options`.
- Constants and storage keys are defined in `custom_components/family_hub/const.py` (e.g. `CONF_GROCY_URL = "grocy_url"`, `CONF_GROCY_API_KEY = "grocy_api_key"` at lines ~984-985).
- Persistent data uses HA `Store` (`homeassistant.helpers.storage.Store`) with per-entry key prefixes (e.g. `SETTINGS_STORAGE_KEY_PREFIX`, `THEME_STORAGE_KEY`, `TIMERS_STORAGE_KEY_PREFIX` in `const.py`); the theme store is created in `custom_components/family_hub/__init__.py` (`Store(hass, THEME_STORAGE_VERSION, THEME_STORAGE_KEY)`).
- Environment variables: none read by the integration. Secrets (Grocy API key) live in config-entry options, not in env files.

**Frontend configuration:**
- Lovelace card configuration in YAML (see `website/docs/card-configuration.md` and `DOCUMENTATION.md`). Card JS URLs are registered by the integration under `/family_hub_*` paths.

**Build / docs configuration:**
- `website/docusaurus.config.js` - Docusaurus site config
- `website/sidebars.js` - docs sidebar
- `website/static/admin/config.yml` and `website/static/admin/index.html` - Netlify/Decap-style CMS admin config
- `.gitignore` - ignores `__pycache__/`, `*.pyc`, `.pytest_cache/`, `node_modules/`, `.DS_Store`, `*.zip`

**Localization:**
- Translations shipped in ten language files at `custom_components/family_hub/*.json` (en, de, es, fr, it, nl, pl, pt, pt-BR) plus `custom_components/family_hub/translations/` (en, de, es, fr). Frontend i18n uses `data-i18n` / `_t(key, fallback)` patterns inside the card JS.

## Platform Requirements

**Development:**
- Home Assistant Core development or test instance (min 2024.1.0 per `hacs.json`)
- Python 3.10+ for editing/compiling backend modules
- Node.js 20+ and npm for the docs site in `website/`
- No linter, formatter, or test runner configuration is tracked in the repository

**Production:**
- Installed via HACS (custom repository) or manual copy of `custom_components/family_hub/` into a Home Assistant config directory
- Runs inside the Home Assistant process; `iot_class: local_polling`
- Optional: a self-hosted Grocy instance (URL + API key) for the grocery/recipe features
- Docs site deployed as a static build to GitHub Pages (`.github/workflows/deploy-docs.yml`, served at `https://jvarhol.github.io/HA-Family-Hub/`)

---

*Stack analysis: 2026-10-26*
