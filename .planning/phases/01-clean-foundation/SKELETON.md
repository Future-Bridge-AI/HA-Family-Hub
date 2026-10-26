# Walking Skeleton — Family Hub (Future-Bridge-AI fork)

**Phase:** 1
**Generated:** 2026-10-26
**Kind:** Brownfield. The full stack already exists and works upstream (see `.planning/PROJECT.md` → Validated). Phase 1 does not scaffold anything. This file records the architecture that already exists, as the contract later phases build on. Phase 1 makes the contract true in the repository: one served copy of every file, a pinned Home Assistant (HA) version, and a known validation baseline.

## Capability Proven End-to-End

> The `family_hub` integration loads in Home Assistant and serves its cards and panels only from `custom_components/family_hub/card/` and `custom_components/family_hub/panel/`. HA loads its translations only from `custom_components/family_hub/translations/`.

How Phase 1 proves it, without a running HA:

- **Served-path contract check.** Every `f"{integration_dir}/…"` path that `async_setup_entry` registers through `StaticPathConfig` (`custom_components/family_hub/__init__.py`, around lines 12503-12571) is a tracked file. No tracked `.js` file exists outside those registered paths.
- **Validator check.** HA 2026.10.4's own hassfest validates a `git archive HEAD` copy of `custom_components/family_hub`. That copy is what a fresh clone or a HACS download gets.
- **Live check.** Proof on a running HA (the integration loads and the cards render in a browser) comes in Phase 2, when Dev starts with one command (DEV-01).

## Architectural Decisions

All of these exist already, unless the row says Phase 1 sets them.

| Decision | Choice | Rationale |
|---|---|---|
| Runtime / framework | Home Assistant custom integration, domain `family_hub`, Python on HA Core APIs only. No `requirements` in `manifest.json` and no dependency manifest. | HA provides everything. Keeps install as a plain folder copy or HACS download. |
| Integration lifecycle | `async_setup` sets up the domain once (theme store, websocket commands, the `hass.data["family_hub"]` container). `async_setup_entry` / `async_unload_entry` run per config entry. Only one config entry is expected. | Upstream design. Phase 4 REL-04 extracts modules behind tests, never as a big-bang rewrite. |
| Data layer | HA `Store` (`homeassistant.helpers.storage`). There is one store per feature, keyed under `family_hub`. `store.py` writes backup files to `family_hub_backups/` and restores from them when primary storage loads empty. | Local-only persistence, as upstream. Storage keys are frozen (D-17). Phase 2's `reset-preview` must also wipe the backups. |
| Business logic | Pure `*_engine.py` modules (chore, reward, goal, pantry, timer, routine). They raise `<Domain>Error` with a `code`. Websocket handlers in `*_websocket_api.py` check permissions and call the engines. | Engines can be tested without `hass` (Phase 3 TEST-02). |
| Frontend | Vanilla JS web components, with no bundler and no build step. Each card is one self-contained file that registers with `customElements.define`. | Build-free delivery (PROJECT.md constraint). |
| Frontend delivery | Static paths registered with `hass.http.async_register_static_paths([StaticPathConfig(...)])`. Only `card/*.js`, `panel/*.js` and the root `icon.png` are served, under the `/family_hub_*` URL constants in `const.py`. Cards are cache-busted by content hash. | Served paths are the only edit targets. Phase 1 removes every unserved duplicate (FOUND-01). |
| Backend API surface | About 60 `family_hub/...` websocket commands, 8 services, and entities (sensor, switch, number, select, text, button, todo) plus device triggers. | Frozen identifiers (D-17). Phase 3 TEST-03 checks them against a checked-in contract. |
| Auth | HA users and permissions (`connection.user.is_admin` plus the permission catalog), and kiosk PIN sign-in (PBKDF2, lockout) inside the integration. No auth of its own outside HA. | Upstream design. In Preview, her account is non-admin (Phase 2 ACCESS-01). |
| Translations | `custom_components/family_hub/translations/{de,en,es,fr,it,nl,pl,pt,pt-BR}.json`, with the non-standard top-level `fh_ui` category that cards load through `hass.loadBackendTranslation("fh_ui", …)`. `translations/en.json` is the key-parity reference (2,139 leaf keys). | Phase 1 makes all nine languages loadable (FOUND-02) and keeps `fh_ui` as it is (D-09). Phase 3 decides whether `fh_ui` moves. |
| Distribution | HACS custom repository: `hacs.json` (`render_readme: true`) plus `custom_components/family_hub/manifest.json`. HACS reads the "available version" from GitHub **Release** tags, not from `manifest.json`. | The install path the family's Home already depends on. Releases arrive in Phase 4 (REL-01). |
| Version scheme | **Phase 1 sets this.** It continues upstream numbering, strictly above 1.168.85. The next version is `1.169.0`. Git tags are `vX.Y.Z` and equal `manifest.json` (D-19, confirmed at a decision checkpoint in plan 01-04). | Monotonic, so HACS on Home sees an upgrade. A lower or reset number would look like a downgrade. |
| HA versions | **Phase 1 sets this.** Dev, Preview and tests are pinned to 2026.10.4 in `versions.env` (`HA_VERSION`). The declared minimum is 2024.12.0 in `hacs.json` (mirrored as `HA_MIN_VERSION` in `versions.env`). | 2026.10.4 is what `pytest-homeassistant-custom-component` 0.13.375 pins. 2024.12.0 is the lowest release that has every API the code imports (D-20, D-21). |
| Validation | **Phase 1 sets this.** `.github/workflows/validate.yml` has two jobs, `hacs` (`hacs/action@main`, `category: integration`) and `hassfest` (`home-assistant/actions/hassfest@master`). It is non-blocking (not a required check). The first failure list is in `01-VALIDATION-BASELINE.md`. | Phase 3 (CI-03) fixes the failures and makes the checks required. |
| Deployment target | Dev comes in Phase 2: Docker Compose with the pinned HA image and the integration mounted live from the working copy. Family Preview is a separate always-on HA instance. Home receives only tagged releases (Phase 4). | Three environments, so experiments never touch Home. |
| Directory layout | `custom_components/family_hub/` (flat Python modules; `card/`, `panel/`, `translations/` and `brand/` subfolders; the served root `icon.png`). Repo root: `hacs.json`, `README.md`, `versions.env`, `website/` (Docusaurus docs site), `.github/workflows/`. Planning lives in `.planning/`. | Upstream layout. Phase 1 removes everything that duplicates a served file. |

## Stack Touched in Phase 1

Every scaffold item already exists upstream. Phase 1 changes repository contents only. It makes no runtime change.

- [x] Project scaffold (framework, build, lint, test runner): **already exists** (HA custom integration and build-free JS). Lint and test runner arrive in Phase 3.
- [x] Routing: **already exists** (static paths for cards and panels; websocket and service registration).
- [x] Database: **already exists** (HA `Store` per feature, with backups).
- [x] UI: **already exists** (Lovelace cards and the Theme Builder panel calling `family_hub/...` websocket commands).
- [ ] Deployment: Phase 2 (one-command Dev, then the always-on Family Preview).
- [x] Phase 1 contract work: one served copy (plans 01-01, 01-02), fork identity (01-03), version scheme and HA versions (01-04), validation baseline (01-05).

## Out of Scope (Deferred to Later Slices)

- Running HA (Dev, Preview) and seed data: Phase 2.
- Tests, lint, JS smoke tests, required CI checks, fixing hassfest and HACS failures, moving `fh_ui`, pinning actions to commit SHAs: Phase 3.
- GitHub Releases, switching Home's HACS to the fork, release and rollback docs, extracting modules out of `__init__.py`: Phase 4.
- Renaming `domain`, services, websocket prefixes, card tags, storage keys or static URL paths: never (D-17).

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without changing the decisions above:

- Phase 2: She opens an isolated, seeded Family Preview on her phone; the developer deploys a branch to it with one command.
- Phase 3: She trusts that no change quietly breaks Preview (engine and setup-smoke tests, card smoke tests, screenshots, green required CI).
- Phase 4: She asks for a change in her own words and signs it off in Preview; Home gets only tagged, rehearsed, rollback-ready releases.
