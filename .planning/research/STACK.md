# Stack Research

**Domain:** Dev / Preview / test / CI tooling for a Home Assistant custom integration (HACS) with build-free vanilla-JS Lovelace cards
**Milestone:** subsequent (adds tooling around the existing `custom_components/family_hub`; the shipped runtime stack does not change)
**Researched:** 2026-10-26
**Confidence:** HIGH overall (versions verified against PyPI / npm / GitHub releases on 2026-10-26; four recommendations spike-tested locally, marked "SPIKED")

> Scope note: this file covers tooling only. The runtime stack (Python on HA Core APIs, vanilla JS web components, no bundler, no Python deps) is documented in `.planning/codebase/STACK.md` and stays unchanged. Nothing recommended here is shipped to users; all of it lives outside `custom_components/family_hub/`.

## Headline Findings (read these first)

1. **The test harness needs Python 3.14.** `pytest-homeassistant-custom-component` 0.13.375 (HA 2026.10.4, 2026-10-24) declares `requires_python >=3.14`, and HA Core itself is now `requires-python >=3.14.2`. This sandbox and many laptops have 3.13 and cannot install the latest. Use `uv` to get 3.14 locally. SPIKED: on CPython 3.14.9 the plugin installed in about 24 s and a test importing the real `custom_components.family_hub.reward_engine` passed.
2. **Pure-engine tests are cheap.** The engines (`reward_engine`, `routine_engine`, `timer_engine`, `pantry_engine`) operate on plain dicts. `chore_engine` and `goal_engine` import `homeassistant.core` types, and every engine import also runs the 13k-line `__init__.py`. That is fine with HA installed, and no `hass` fixture is needed for most tests.
3. **jsdom is enough for card smoke tests.** SPIKED: with jsdom 30.1.3 plus a stub `ResizeObserver` and a mocked `hass`, 12 custom elements (from 12 of the 14 files in `card/` and `panel/`) defined and rendered (3k to 330k chars of shadow DOM) with zero errors. The other two, `card/family-hub-my-chores-card.js` and `panel/theme-builder-panel.js`, did not add a `window.customCards` entry, so the spike skipped them. They need a check of how they register (element name from `customElements.define`) before their smoke tests are written. Playwright is only needed for real layout and screenshots.
4. **Ruff is nearly clean today.** SPIKED: ruff 0.17.2 with `E4,E7,E9,F,B` finds only 9 issues in 29k lines (6 unused imports, 1 unused variable, 1 `B904`, 1 `B905`). `ruff format --check` would rewrite 25 of 26 files, and the broad `E,W,I,UP` set gives 1,740 findings (1,542 are `E501`). Gate on the narrow set and do not enforce formatting yet.
5. **ESLint is viable as a gate.** SPIKED: ESLint 10.13.0 `recommended` over `card/` and `panel/` found no parse errors and no `no-undef`. The only noise is `no-empty` (129), `no-useless-assignment` (25), `no-useless-escape` (7), `no-control-regex` (2) and `no-func-assign` (2). Turn off the first four, fix or suppress the last two.
6. **Brand assets are already in place.** `custom_components/family_hub/brand/{icon,icon@2x,logo,logo@2x}.png` exist and are tracked. Since HA 2026.3 custom integrations serve their own `brand/` images, and HACS requires `brand/icon.png`, so the HACS `brands` check should pass without a PR to `home-assistant/brands`.
7. **hassfest could not be run locally.** The sandbox's code-execution safety check refused to run an externally cloned `script.hassfest`. Treat "hassfest passes on first CI run" as unverified and budget a triage task (see Pitfalls and Version Compatibility).

## Recommended Stack

### Environments (Dev and Family Preview)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Docker Engine + Compose v2 | Engine >= 23.0 (HA's stated minimum) | Runs Dev and Preview HA | The official container install is a compose file. No Docker Desktop on the always-on Preview host (HA docs say Docker Desktop is unsupported for the container install). | HIGH |
| `ghcr.io/home-assistant/home-assistant` | **pin `2026.10.4`** (not `:stable`) | HA runtime for Dev and Preview | The same tag the test plugin resolves to (0.13.375 pins `homeassistant==2026.10.4`), so tests, Dev and Preview run the same HA. Pinning makes "what did she just try" reproducible. Bump deliberately, together with the plugin. | HIGH (version), MEDIUM (tag existence not fetched from ghcr, but it follows the documented `YYYY.M.P` scheme) |
| Dev compose project | `dev/compose.yml`, port 8123 | Developer's scratch HA | Bind-mounts `./custom_components/family_hub` into `/config/custom_components/family_hub`, so edits are live. Python changes need `docker compose restart`. Card JS is served from the mount. | HIGH |
| Preview compose project | `preview/compose.yml`, port 8124, `restart: unless-stopped` | Always-on Family Preview | A separate project, container name and config dir gives full isolation from any Home HA. | HIGH |
| Bridge networking, not `network_mode: host`, no `privileged`, no `/run/dbus` | n/a | Isolation of Preview and Dev | The official snippet uses host networking and privileged mode for device discovery, which Preview must not do: it would let Preview discover the real home's devices and fight Home HA for port 8123. Bridge mode with `8124:8123` hides the LAN. (Reduces risk, does not eliminate it, because the container still has outbound internet.) | HIGH |
| Preview config as bind mount `./preview/config` (gitignored) | n/a | Seedable, resettable state | `reset-preview` becomes down, wipe, up, reseed, and the volume is easy to back up. | HIGH |

Compose settings that matter (both projects): `TZ` set to the family's timezone, `PYTHONDONTWRITEBYTECODE=1` (stops `__pycache__` appearing in the mounted working copy, which is already a repo-hygiene problem), `stop_grace_period: 60s`, a minimal `configuration.yaml` with `default_config:`. First boot downloads Python requirements for the default-config integrations, so the host needs internet and the seed script must poll `GET /api/onboarding` until it answers (expect minutes, not seconds).

### Seed and deploy scripts

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python 3.14 script using `aiohttp` (`scripts/seed_preview.py`) | aiohttp 3.14.x (the version HA 2026.10 pins) | Onboard HA, create users, calendars, to-do lists and events | Needs both REST and WebSocket (user creation is WebSocket-only), and `aiohttp` does both with one dependency. Run it in the same `uv` env as the tests so the dependency set is one thing. | HIGH |
| Bash wrappers: `deploy-preview`, `reset-preview`, `dev-up` (plus a `Makefile`/`justfile` front door) | n/a | One-command operations | "One command" is a requirement. Keep logic in the Python script, with thin shell wrappers over `docker compose`. | HIGH |
| `git archive <branch> custom_components/family_hub \| tar -x -C <tmpdir>`, then swap into `preview/config/custom_components/`, then `docker compose restart` | git | Deploy-from-branch | Deploys exactly the committed state of a branch with no working-tree leakage, no git needed inside the container, and an atomic dir swap. Do not use HACS to install a branch. | HIGH |

Seed flow, each step from HA's own endpoints (onboarding endpoints verified in `homeassistant/components/onboarding/views.py`; the others MEDIUM, from HA source and docs, to confirm in the Preview phase):

1. `POST /api/onboarding/users` with `name`, `username`, `password`, `client_id`, `language`. It returns `auth_code` and creates the **owner/admin** (the developer). It works only once, on a virgin config.
2. Exchange the code at `POST /auth/token` (`grant_type=authorization_code`).
3. Complete the remaining onboarding steps: `core_config`, `analytics`, `integration` (the `STEPS` list is `user`, `core_config`, `analytics`, `integration`).
4. Over WebSocket, as admin: `config/auth/create` (`name`, `group_ids`) for each family member, then `config/auth_provider/homeassistant/create` (`user_id`, `username`, `password`). Her account gets the non-admin group (`system-users`). Children get non-admin plus `local_only` if wanted.
5. Create entries through the config-flow REST API `POST /api/config/config_entries/flow`. **Local Calendar** is step `user` with `calendar_name` and an optional `import` choice (`create_empty` or `import_ics_file`). **Local To-do** is a single `user` step with `todo_list_name`. Both integrations are UI-only (no YAML), so the flow API is the only scripted route.
6. Populate events and items with `calendar.create_event` and `todo.add_item` service calls. Compute all dates **relative to today at seed time** (see Pitfalls).
7. Create the family wall dashboard in storage mode over WebSocket (`lovelace/dashboards/create` then `lovelace/config/save`) so she lands on a ready-made screen.
8. Create the Family Hub config entry (and its required `calendar.*`, `todo.*` and `notify.*` mappings) via the same flow API.

A pre-baked `.storage/` snapshot (committed auth/config_entries JSON) is **not** recommended as the primary mechanism: it breaks across HA versions, contains password hashes, and cannot be re-dated. An optional tarball of the post-seed `config/` is fine as a fast-restore cache, but the seed script stays the source of truth.

### Python test stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | **3.14** (HA 2026.10 requires >= 3.14.2) | Test and lint runtime | Forced by the plugin and HA Core. Get it with `uv python install 3.14` locally, `actions/setup-python` in CI. | HIGH |
| `pytest-homeassistant-custom-component` | **0.13.375** (pins `homeassistant==2026.10.4`, `pytest==9.0.3`) | Real HA fixtures (`hass`, `MockConfigEntry`, `enable_custom_integrations`, snapshot ext.) | The community-standard harness, auto-released daily against each HA release. Matches the PROJECT.md decision. Pin exactly in `requirements_test.txt` and bump via Dependabot or Renovate. | HIGH |
| `pytest-asyncio` | 1.4.0 (transitive) | Async tests | Set `asyncio_mode = auto` in `pytest.ini` (the plugin README requires it). | HIGH |
| `pytest-freezer` / `freezegun` | 0.4.9 / 1.5.5 (transitive) | Time control | The engines are date-heavy (chore due dates, streaks, timers). Use the `freezer` fixture. | HIGH |
| `pytest-socket` | 0.8.1 (transitive) | Blocks real network in tests | Already on by default through the plugin. Use `socket_enabled` only if ever needed. | HIGH |
| `pytest-cov` | 7.1.0 (transitive) | Coverage | Report only, no threshold gate until the engines are covered. | HIGH |
| `syrupy` | 6.1.1 (transitive) | Snapshot tests | Optional, for websocket payload shapes. Wire the plugin's `HomeAssistantSnapshotExtension` in `conftest.py`. | MEDIUM |
| `ruff` | **0.17.2** (HA Core requires >= 0.17.1) | Lint | Matches HA Core's own pin. Config below. | HIGH |

`conftest.py` must request `enable_custom_integrations` (autouse), otherwise `custom_components.*` is not importable as an integration. SPIKED: this works with a symlinked or in-repo `custom_components/`.

Suggested `pyproject.toml` / `ruff.toml` lint config (gate on bug-finding rules only):

```toml
[tool.ruff]
target-version = "py314"
exclude = ["website", "node_modules", "preview", "dev/config"]

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "B"]   # 9 findings today; fix them in the same PR that adds CI
# Later, one rule family per PR: I, UP, then ruff format in a single mechanical commit.
```

### JavaScript test and lint stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Node.js | **24 (LTS)** in CI and locally | JS tooling runtime | jsdom 30 needs `^22.22.2 \|\| ^24.15.0 \|\| >=26`. The sandbox's Node 22.22.0 is below that floor, so jsdom ran but is formally unsupported there. Use `node-version: 24` in CI. | HIGH |
| `vitest` | **5.0.5** | Test runner | SPIKED. Fake timers matter because cards poll every 60 s (they kept a plain Node process alive until killed), and watch mode and a readable reporter suit a non-JS-specialist developer. | HIGH |
| `jsdom` | **30.1.3** | DOM for card smoke tests | SPIKED: supports custom elements and shadow DOM, which is all the cards need. | HIGH |
| `eslint` + `@eslint/js` + `globals` | 10.13.0 / 10.0.1 / 17.13.0 | JS syntax and `no-undef` gate | SPIKED (see headline finding 5). Flat config, `sourceType: "script"` (cards are classic scripts with no `import`/`export`). | HIGH |
| `@playwright/test` (+ browsers) | **1.64.1** | Real-browser screenshots and layout checks | Not for logic tests. Used for (a) an offline card-harness page screenshot (deterministic, runs in CI) and (b) a manual script that screenshots Preview with a tablet viewport for her before/after pictures. | HIGH (version), MEDIUM (auth-injection recipe) |
| `mcr.microsoft.com/playwright` | `v1.64.1-noble` | Pre-baked browsers for CI and Preview-host screenshots | Avoids a browser-install step. The image tag must match the npm version exactly. | MEDIUM (naming convention, not fetched) |

Key smoke-test pattern (SPIKED): create a **fresh `JSDOM` per card** (`runScripts: "outside-only"`, `pretendToBeVisual: true`), stub `ResizeObserver`, `window.eval()` the card source, create the element, call `setConfig()`, assign a minimal mocked `hass` (`states`, `user`, `language`, `locale`, `callWS`, `callService`, `config`, `themes`), advance fake timers, assert the shadow root is non-empty and no `error` event fired. A fresh window per card is mandatory because `customElements` is a global registry, and `window.close()` must be called or poll timers hold the process open. Put JS tooling in a **root-level `package.json`** (devDependencies only, not shipped). Do not add a `package.json` inside `custom_components/`.

### CI (GitHub Actions)

| Action | Version | Purpose | Notes | Confidence |
|--------|---------|---------|-------|------------|
| `actions/checkout` | `v7` (latest 7.0.1) | Checkout | Existing docs workflow uses `v4`. Leave it alone unless touched. | HIGH |
| `actions/setup-python` | `v7` (latest 7.1.0) | Python 3.14 + pip cache | `cache: pip` keyed on `requirements_test.txt`. | HIGH |
| `actions/setup-node` | `v7` (latest 7.1.0) | Node 24 + npm cache | `cache: npm` at the root `package-lock.json`. | HIGH |
| `astral-sh/ruff-action` | `v4` (latest 4.1.0) | Ruff lint | Fast and zero-install. Setting `version: 0.17.2` explicitly keeps it aligned with the repo pin. | HIGH |
| `hacs/action` | `@main` (HACS docs' own example) | HACS validation | `with: category: integration`. Triggers: push, PR, daily cron, `workflow_dispatch`. Set `permissions: {}`. Needs repo description, topics, **Issues enabled** and a license on the fork (see Pitfalls). | HIGH |
| `home-assistant/actions/hassfest` | `@master` (the documented ref) | Manifest, services, translations validation | Same triggers as above. Runs on the repo root, which already has `custom_components/family_hub`. | HIGH (usage), LOW (that it passes today) |
| `actions/upload-artifact` | `v7` (latest 7.0.2) | Playwright screenshots and pytest reports | Only when a test fails or for the screenshot job. | HIGH |

Recommended workflow layout (separate files so a red badge says which thing broke):

- `.github/workflows/ci.yml` on push and PR, with jobs `python` (ruff, then pytest with coverage report), `js` (eslint, vitest, optional Playwright harness screenshots) and `translations` (see next paragraph).
- `.github/workflows/validate.yml` on push, PR and daily cron, with jobs `hacs` and `hassfest`.
- Keep `deploy-docs.yml` untouched except for a Node bump (the docs job runs Node 20, which is past end-of-life; low priority and out of this milestone's critical path).

Add a tiny custom check (a Python test, not a tool) for translation key parity across `translations/*.json` against `en.json`, because PROJECT.md already plans the `it/nl/pl/pt/pt-BR` move and this is the cheapest regression guard.

### Dependency pinning

| Tool | Purpose | Notes |
|------|---------|-------|
| `requirements_test.txt` | `pytest-homeassistant-custom-component==0.13.375` and `ruff==0.17.2` | The single source for local and CI. Do not add a Python manifest to `custom_components/`. |
| `uv` (locally) | Provisions Python 3.14 and the venv | `uv venv --python 3.14 && uv pip install -r requirements_test.txt`. CI can use plain pip, which is simpler to read. |
| Dependabot (`.github/dependabot.yml`) | Weekly bumps for pip, npm and github-actions | Needed because both the HA image tag and the plugin pin must move together. Add a README note: bump image tag and plugin in the same PR. |

## Installation

```bash
# Python tooling (needs Python 3.14; uv fetches it)
uv venv --python 3.14 .venv
uv pip install -r requirements_test.txt   # pytest-homeassistant-custom-component==0.13.375, ruff==0.17.2
.venv/bin/python -m pytest
.venv/bin/ruff check custom_components

# JS tooling (root package.json, devDependencies only; Node 24)
npm install -D vitest@5.0.5 jsdom@30.1.3 eslint@10.13.0 @eslint/js@10.0.1 globals@17.13.0 @playwright/test@1.64.1
npx vitest run
npx eslint custom_components/family_hub/card custom_components/family_hub/panel

# Dev environment
docker compose -f dev/compose.yml up -d     # http://localhost:8123

# Preview environment (on the always-on host)
docker compose -f preview/compose.yml up -d  # http://<host>:8124
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Plain Docker Compose for Dev | VS Code devcontainer (the `integration_blueprint` approach) | If the developer wants an in-container editor with debugger attached. Not required, and a devcontainer cannot serve as the always-on Preview, so compose is needed anyway. Reuse one mechanism. |
| Separate Preview HA container (bridge network, port 8124) | Second dashboard or user on the real Home HA | Never. The isolation requirement forbids it. |
| Script-driven seeding (onboarding API, WebSocket, config-flow API) | Committed `.storage/` snapshot | Only as an optional fast-restore cache. A snapshot is HA-version-fragile and cannot re-date events. |
| `git archive` + dir swap + container restart | HACS install of a branch, or `rsync` from a working tree | `rsync` from the working tree is fine for Dev (it is the bind mount). Never for Preview: uncommitted files leak in. |
| Vitest + per-card jsdom | `node --test` + jsdom | If zero extra dependencies matter. Works equally well (SPIKED with plain Node), but you hand-build fake timers and reporting. |
| jsdom for smoke tests | Playwright for all card tests | Only for layout, CSS and screenshot assertions. Playwright against 330k chars of calendar DOM is slower and gives no extra logic coverage. Use both, with different jobs. |
| `happy-dom` 21.0.4 | jsdom | Faster, but less complete web-platform fidelity (shadow DOM / custom-element edge cases). jsdom is already proven on these 12 cards. |
| `pytest-homeassistant-custom-component` | Hand-built `homeassistant` stub (as the stale `PROJECT_CONTEXT.md` describes) | Never. It drifts from real HA. The plugin already works against the real package (SPIKED). |
| ruff lint-only gate | `ruff format` + broad rule set from day one | After a dedicated mechanical formatting commit lands (25 files would change). |
| ESLint 10 | `node --check` only | `node --check` catches syntax only. ESLint adds `no-undef`, and since `no-undef` is currently clean, regressions get caught for free. |
| `hacs/action@main` | Pin to a commit SHA | If supply-chain strictness matters more than convenience. HACS's docs use `@main`. If pinning, Dependabot keeps it fresh. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `ghcr.io/home-assistant/home-assistant:stable` or `:latest` for Preview | The tag silently changes under a running family setup, and tests would drift from Preview. | Pin `2026.10.4`, bump on purpose with the test plugin. |
| `network_mode: host` + `privileged: true` (the stock snippet) for Dev or Preview | Port clash with Home HA, discovery of real devices, a larger blast radius. | Bridge networking, mapped port, no privileges. |
| Pointing Preview at real calendars, real `todo.*` lists, the real Grocy or real `notify.*` targets | Violates the core safety constraint. | Seeded Local Calendar and Local To-do, and a Preview-only notify (for example `notify.persistent_notification`). Leave Grocy unset. |
| Nabu Casa Cloud for the Preview instance | It binds one HA instance to a subscription account and would conflict with Home's. | LAN access to `http://host:8124`. For remote access, Tailscale (not verified in this research, flagged for the Preview phase). |
| Home Assistant add-ons / HAOS VM for Preview | Heavier to script and reset, and not needed. | Container install. |
| Python < 3.14 for the test venv | The latest plugin cannot install. An older plugin pairs with an older HA that no longer matches Dev and Preview. | `uv` with Python 3.14. |
| `network` mocks via `requests`/`httpx` in the engines tests | The engines are dict-based and need no I/O. For the few that call out (Grocy via aiohttp), the plugin ships `aioclient_mock`. | Pure dict fixtures, plus `aioclient_mock` where needed. |
| A hand-rolled HA "stub" package, or vendoring HA test fixtures | Drift and maintenance. | The published plugin. |
| Enforcing `ruff format`, `E501` or `UP` rules in the first CI PR | 1,700+ findings and a 25-file rewrite in a repo with no tests will bury the real signal and risk regressions. | Narrow bug-finding gate first, formatting as a separate mechanical commit later. |
| Testing JS in Playwright only | Slow and brittle, with no logic isolation. | jsdom via Vitest for smoke, Playwright for pixels. |
| Bundlers or npm packaging for the cards (Rollup, Vite build, Lit) | Breaks the project's build-free delivery constraint. | Keep `card/*.js` as served. Tooling only lints and loads them. |
| Committed `.storage/auth` snapshots | Contain credential material and cannot be regenerated safely. | Seed script with passwords from a gitignored env or `.env` file. |
| Docker Desktop on the Preview host | Not supported by HA's container docs. | Docker Engine on Linux (mini PC, NAS or Pi). |

## Stack Patterns by Variant

**If a Home HA already runs on the same always-on machine:**
- Preview runs bridge-networked on port 8124, with a different container name and project name, and no volume shared with Home.
- Because the Companion app discovers instances through mDNS and the bridge hides it, she adds Preview by URL (`http://<host>:8124`). That is deliberate: it keeps her from mistaking it for Home.

**If the Preview host is a laptop that sleeps:**
- Fails the "always-on" requirement. A Raspberry Pi 4/5, mini PC or NAS is the target. The compose file is identical, so moving later is a copy of `preview/`.

**If she should reach Preview away from home Wi-Fi:**
- Add Tailscale on the host (`tailscale serve` for HTTPS). Not researched in depth. Flag it for the Preview phase and do not expose port 8124 to the internet.

**If CI later needs an end-to-end test against real HA:**
- Add a job that runs the pinned HA container with the seed script, then runs the Playwright suite against it. Defer until the unit and smoke layers exist. The seed script being CLI-driven makes this nearly free.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `pytest-homeassistant-custom-component==0.13.375` | `homeassistant==2026.10.4`, `pytest==9.0.3`, Python >= 3.14 | The plugin pins HA exactly. Dev and Preview image tag should match `2026.10.4`. |
| HA 2026.10.x | Python >= 3.14.2, ruff >= 0.17.1 (HA Core's own pyproject) | Lint `target-version` is `py314` for CI. |
| `hacs.json` `"homeassistant": "2024.1.0"` | CI tests only HA 2026.10.4 | **Mismatch.** The claimed floor is untestable and almost certainly false (2024.1 ran on Python 3.11, and APIs have moved). Decide in the foundation phase: raise the floor to what is actually exercised (recommended: the version the family runs), or add a separate, explicitly best-effort legacy job. |
| `jsdom@30.1.3` | Node `^22.22.2 \|\| ^24.15.0 \|\| >=26` | Sandbox Node 22.22.0 is below the floor, so use Node 24 in CI and locally. |
| `vitest@5.0.5` | Node `^22.12.0 \|\| ^24.0.0 \|\| >=26.0.0` | OK on Node 24. SPIKED on 22.22.0. |
| `eslint@10.13.0` | Node `^20.19.0 \|\| ^22.13.0 \|\| >=24` | OK. |
| `@playwright/test@1.64.1` | `mcr.microsoft.com/playwright:v1.64.1-*` | Image tag and npm version must match exactly. |
| HA >= 2026.3 | `custom_components/<domain>/brand/` images | Already satisfied. Local images take priority over the brands CDN. HACS also wants `brand/icon.png`. |

## Sources

- PyPI `pytest-homeassistant-custom-component` JSON (0.13.375, `requires_python >=3.14`, pins `homeassistant==2026.10.4`, `pytest==9.0.3`) and the project README (`enable_custom_integrations`, `asyncio_mode = auto`, snapshot ext.): HIGH. Local spike on CPython 3.14.9 (install and a passing engine import test): HIGH.
- `pip index` / `npm view` for ruff 0.17.2, jsdom 30.1.3, vitest 5.0.5, eslint 10.13.0, @eslint/js 10.0.1, globals 17.13.0, playwright and @playwright/test 1.64.1, happy-dom 21.0.4, plus the `engines` fields: HIGH (registry reads on 2026-10-26).
- GitHub release pages (checkout 7.0.1, setup-python 7.1.0, setup-node 7.1.0, ruff-action 4.1.0, setup-uv 10.3.2, upload-artifact 7.0.2, home-assistant/core 2026.10.4 released 2026-10-24): HIGH. Release dates shown without a year on the page (WebFetch limitation), which fits today's date.
- HA Core `pyproject.toml` (`requires-python >=3.14.2`, ruff `required-version >=0.17.1`) and `package_constraints.txt` (aiohttp 3.14.5): HIGH (read from the `dev` branch).
- HA Core `homeassistant/components/onboarding/views.py` and `const.py` (endpoints, step order), `config/auth.py` and `config/auth_provider_homeassistant.py` (admin-only user-creation WebSocket commands), `local_calendar/config_flow.py` and `local_todo/config_flow.py` (flow fields): HIGH for the field names read, MEDIUM for the end-to-end sequence, which is unspiked.
- https://www.home-assistant.io/installation/linux (official compose snippet, Docker Engine >= 23.0, Docker Desktop unsupported): HIGH.
- https://www.home-assistant.io/integrations/local_calendar/ and /local_todo/ (UI-only setup): HIGH.
- https://hacs.xyz/docs/publish/action/ (workflow, `category`, ignorable checks: archived, brands, description, hacsjson, images, information, issues, license, topics) and https://hacs.xyz/docs/publish/integration/ (single integration dir, required manifest keys, `brand/icon.png`): HIGH.
- https://github.com/home-assistant/actions (`home-assistant/actions/hassfest@master`, `actions/checkout`): HIGH for usage. The page gives no custom-integration prerequisites.
- https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api (custom-integration `brand/` folder from HA 2026.3): HIGH.
- Local spikes in the session scratchpad (jsdom card load and render, Vitest with fake timers, ESLint over `card/`+`panel/`, ruff rule-set calibration on `custom_components/`): HIGH for the repo state as of this commit.
- Playwright Docker image tag format, Tailscale remote access, `git archive` deploy mechanics and the lovelace dashboard-creation WebSocket commands: MEDIUM / LOW, from general knowledge and not fetched. Verify in the Preview phase.
- Not verified: a real `hassfest` run against `custom_components/family_hub` (blocked in the sandbox).

---
*Stack research for: HA custom integration dev/preview/test/CI tooling*
*Researched: 2026-10-26*
