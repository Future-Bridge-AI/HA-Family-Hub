---
last_mapped_commit: f811e9172bf425ade1c9580c6de2b1b0ef0637ee
last_mapped_at: 2026-10-26
---
# Codebase Concerns

**Analysis Date:** 2026-10-26

## Tech Debt

**Monolithic backend entry module:**
- Issue: `custom_components/family_hub/__init__.py` is ~13,175 lines and holds websocket handlers, Grocy API clients, todo/wish-list plumbing, static-path registration, dashboard-resource registration, settings-history export, and setup/teardown. The integration as a whole is ~28,845 lines of Python across `custom_components/family_hub/*.py`.
- Files: `custom_components/family_hub/__init__.py`, `custom_components/family_hub/config_flow.py` (~1,336 lines), `custom_components/family_hub/chores_websocket_api.py`
- Impact: Very hard to review or test in isolation; changes to one feature risk regressions in unrelated setup code. Import-time side effects and shared module-level constants make partial refactors risky.
- Fix approach: Extract per-domain modules (grocy client, todo/wishlist, static paths, websocket registration) out of `__init__.py`, keeping `async_setup_entry` as a thin orchestrator. Move one domain per change with the existing websocket type names kept stable.

**Duplicated frontend card bundles (two copies of every card):**
- Issue: Every card exists twice: once at `custom_components/family_hub/<name>.js` and once under `custom_components/family_hub/card/<name>.js`. Content has already diverged for `family-hub-chores-card.js`, `family-week-calendar-card.js`, and `family-today-card.js` (byte-level differences). `panel/theme-builder-panel.js` and `theme-builder-panel.js` (root) also differ. `family-right-now-card.js` is identical in both locations.
- Files: `custom_components/family_hub/card/*.js`, `custom_components/family_hub/*.js` (root-level copies), `custom_components/family_hub/panel/*.js`, `custom_components/family_hub/theme-builder-panel.js`, `custom_components/family_hub/theme-selector-card.js`
- Impact: It is unclear which copy `__init__.py` serves (static paths are registered from the `card/` and `panel/` directories, see `__init__.py` around lines 12553-12571). Fixes applied to one copy silently do not reach the other. Maintainers can ship the wrong behaviour.
- Fix approach: Pick one canonical location (the `card/` and `panel/` directories are what the static-path registration uses), delete the root-level duplicates, and add a CI check that fails if the copies differ.

**Backup and stale artifacts committed to the card directory:**
- Issue: `custom_components/family_hub/card/family-week-calendar-card.js.bak_divfix` (~1.2 MB) is a leftover backup tracked in git.
- Files: `custom_components/family_hub/card/family-week-calendar-card.js.bak_divfix`
- Impact: Ships to every HACS install, inflates the repo, and invites accidental edits to the wrong file.
- Fix approach: Remove the file from git and rely on git history for recovery.

**Compiled bytecode committed to git despite `.gitignore`:**
- Issue: `.gitignore` lists `__pycache__/` and `*.pyc`, but 49 `.pyc` files under `custom_components/family_hub/__pycache__/` (cpython-310 and cpython-314 builds) are tracked. They were added before the ignore rule or force-added.
- Files: `custom_components/family_hub/__pycache__/*.pyc`, `.gitignore`
- Impact: Stale bytecode can mask source changes on some Python versions, bloats diffs, and leaks local interpreter versions into the repo. Every local test run produces diffs.
- Fix approach: Run `git rm -r --cached custom_components/family_hub/__pycache__` and commit. Confirm `.gitignore` covers nested paths.

**Oversized, generated-looking frontend bundle:**
- Issue: `custom_components/family_hub/card/family-week-calendar-card.js` is ~30,900 lines (~1.7 MB) and the root copy is ~23,500 lines. Each card is a single file with inline translations, styles, and logic.
- Files: `custom_components/family_hub/card/family-week-calendar-card.js`, `custom_components/family_hub/family-week-calendar-card.js`
- Impact: Slow to load on low-powered wall tablets (the target dashboard hardware), hard to diff in review, and most edits touch the same huge file.
- Fix approach: Split shared helpers (escaping, i18n lookup, websocket calls) into a shared module and build bundles from source, or at least document the source of truth for the bundle.

**Large repository artifacts:**
- Issue: `PROJECT_CONTEXT.md` (~797 KB) sits at the repo root, and `CHANGELOG.md` says it is behind the manifest version (`CHANGELOG.md` says entries run through v1.135.4, while `custom_components/family_hub/manifest.json` is at 1.168.85). `CHANGELOG_ARCHIVE.md` is referenced by `CHANGELOG.md` but does not exist; the website has its own `website/docs/changelog.md` and `website/docs/changelog-archive.md`.
- Files: `PROJECT_CONTEXT.md`, `CHANGELOG.md`, `custom_components/family_hub/manifest.json`, `website/docs/changelog.md`
- Impact: Three changelog sources disagree; users reading the root changelog miss roughly 30 releases; a broken link is visible on the repo front page.
- Fix approach: Make the website changelog the single source, regenerate `CHANGELOG.md` from it, and fix or remove the dangling `CHANGELOG_ARCHIVE.md` reference.

**Screenshot directory with a backslash in its name:**
- Issue: The top-level directory is literally named `\Screenshots` (a Windows-style path committed on Linux), and it contains files such as `\Screenshots/Chores.png`.
- Files: `\Screenshots/` (repo root)
- Impact: Breaks cross-platform paths and tooling, and renders awkwardly in GitHub and on Linux checkouts.
- Fix approach: Rename to `screenshots/` and update any README or docs references.

**Lack of an automated test suite:**
- Issue: The repository contains no test files (no `tests/` directory, no `test_*.py`, no `conftest.py`) and no CI workflow beyond `.github/workflows/deploy-docs.yml`, which deploys the docs site.
- Files: `.github/workflows/deploy-docs.yml`, `custom_components/family_hub/`
- Impact: Nothing guards the chore, reward, goal, pantry, and timer engines (`chore_engine.py`, `reward_engine.py`, `goal_engine.py`, `pantry_engine.py`, `timer_engine.py`, `routine_engine.py`) or the self-updater (`updater.py`). Regressions are caught only by household use.
- Fix approach: Add pytest unit tests for the pure engine modules first (they take plain data), then a CI job that runs them plus `python -m compileall` and a JS syntax check on each card.

## Known Bugs

**Silent failure on best-effort dashboard registration:**
- Symptoms: The calendar card may never be registered as a Lovelace resource, with no user-visible error.
- Files: `custom_components/family_hub/__init__.py` (`_register_dashboard_resource`, around line 12200)
- Trigger: Any Home Assistant version whose internal Lovelace storage collection changes shape. The function is documented to "silently no-op" on failure.
- Workaround: Add the resource by hand (URL and type are printed in the function docstring).

**View-switch repaint race (reported in changelog, fix status unverified):**
- Symptoms: The Week/Month/Day label updates before the grid repaints, so the UI can briefly show mismatched view and grid.
- Files: `custom_components/family_hub/card/family-week-calendar-card.js`, described in `CHANGELOG.md` under v1.135.4
- Trigger: Any view switch while the `_fetchEvents()` round-trip is slow.
- Workaround: Wait for the grid to refresh.

## Security Considerations

**Grocy API key stored in plain config-entry options:**
- Risk: The Grocy API key (`CONF_GROCY_API_KEY`) is kept in `entry.options` and sent in the `GROCY-API-KEY` header on every request. It is persisted in Home Assistant's `.storage` directory in clear text.
- Files: `custom_components/family_hub/const.py` (`CONF_GROCY_API_KEY`), `custom_components/family_hub/config_flow.py`, `custom_components/family_hub/__init__.py` (`_grocy_api_get`, `_grocy_api_post`, `_grocy_api_put`, `_grocy_api_delete`, around lines 4201-4330)
- Current mitigation: Only admins can change config flow options. The key is not written to the frontend in the code paths reviewed.
- Recommendations: Document that `.storage` must be protected, and confirm the key is never echoed in websocket responses (for example in the `grocy_configured` status at `__init__.py` line 2213, which only reports a boolean). Consider the HA secrets/keyring pattern for future versions.

**Grocy HTTP requests have no explicit TLS or timeout policy:**
- Risk: The Grocy URL is user-provided and trimmed of trailing slashes only (`config_flow.py` lines 629 and 982). Requests go to whatever scheme the user entered, so an `http://` URL sends the API key in clear text. Several call sites build their own aiohttp requests without a documented timeout.
- Files: `custom_components/family_hub/config_flow.py` (lines 629, 982), `custom_components/family_hub/__init__.py` (around lines 4201-4330 and the recipe/picture fetch around 4574-4700)
- Current mitigation: The URL is validated as non-empty before use.
- Recommendations: Reject or warn on `http://` for non-local hosts, add an explicit `aiohttp.ClientTimeout` to every Grocy call, and surface TLS verification failures to the admin.

**Broad exception handling hides failures and can hide security errors:**
- Risk: About 145 `except` clauses in the Python backend catch `Exception` broadly (`__init__.py` has ~115, `chores_websocket_api.py` ~18, `config_flow.py` ~6, `chore_engine.py` ~3, `store.py` ~2). This can swallow authorization or validation errors and return success-looking responses.
- Files: `custom_components/family_hub/__init__.py`, `custom_components/family_hub/chores_websocket_api.py`, `custom_components/family_hub/config_flow.py`, `custom_components/family_hub/chore_engine.py`, `custom_components/family_hub/store.py`
- Current mitigation: Many handlers log and return an error payload to the client.
- Recommendations: Narrow the exception types at boundaries that talk to network or disk, and let authorization and validation errors propagate to the HA websocket error path.

**Self-updater accepts uploaded code and overwrites the installed integration:**
- Risk: `custom_components/family_hub/updater.py` (`install_update_from_zip`) extracts an uploaded zip and copies its contents over the live integration directory. It validates member names (no absolute paths, no `..`) and caps size (20 MB compressed, 200 MB uncompressed), but there is no signature or hash check, and the install path is only protected by config-flow admin gating.
- Files: `custom_components/family_hub/updater.py`, `custom_components/family_hub/config_flow.py` (around line 1314)
- Current mitigation: Path-traversal checks in `_check_member_name`; a backup is written via `backup_root`; the install is only performed after validation.
- Recommendations: Verify a checksum or signature against a published manifest, reject symlink members (zipfile does not block symlinks by default), and keep the `backup_root` rollback path tested.

**Settings-history export is signed and admin-gated, but relies on HA internals:**
- Risk: `FamilyHubSettingsHistoryExportView` (`__init__.py` around line 1724) is registered on the shared aiohttp app and depends on `homeassistant.components.http.auth.async_sign_path` signing behaviour. Export files contain the full Settings blob (people and calendars at minimum; whether any secret is included was not verified).
- Files: `custom_components/family_hub/__init__.py` (around lines 1724-1760 and 13026-13031), `custom_components/family_hub/config_flow.py` (`async_step_export_backup`)
- Current mitigation: Signed short-lived URL, `requires_auth = True`, explicit `is_admin` check, and fresh lookup per request.
- Recommendations: Confirm the export does not include the Grocy key or other secrets, and add a test that a non-admin token receives 403.

**Frontend renders translated strings and API data with `innerHTML`:**
- Risk: The card and panel bundles build markup with template literals and assign it through `innerHTML` in roughly 390 places across `card/` and `panel/` (per-file counts from a grep of `innerHTML`) (for example `card/family-week-calendar-card.js` has ~212 sites, `card/family-hub-recipe-box-card.js` ~32, `card/family-hub-todo-card.js` ~25). Several sites interpolate `this._t(...)` results and data such as list names or item text without consistent escaping. A local `esc` helper exists in each file but is not applied uniformly (for example `card/family-hub-todo-card.js` lines 3423-3854 interpolate `_t` output directly).
- Files: `custom_components/family_hub/card/*.js`, `custom_components/family_hub/panel/*.js`
- Current mitigation: Per-file `esc` helpers (escape `&`, `<`, `"`) at lines such as `card/family-week-calendar-card.js:498`.
- Recommendations: Centralise escaping in one helper, escape translations and user-entered names (todo items, recipe titles, person names), or build DOM with `textContent`. Add a lint rule that flags `innerHTML` with `${` interpolation outside the helper.

**Compiled bytecode and local state committed:**
- Risk: Committed `.pyc` files (see Tech Debt) and screenshot files may contain environment details. No secrets were found in tracked source files by a keyword scan of `custom_components/`, but `.env` handling is not documented.
- Files: `custom_components/family_hub/__pycache__/`, `.gitignore`
- Current mitigation: `.gitignore` ignores `__pycache__/`, `*.pyc`, `node_modules/`, `.DS_Store`, and `*.zip`, but does not explicitly ignore `.env` files.
- Recommendations: Add `.env`, `*.env`, and `secrets*` to `.gitignore`.

## Performance Bottlenecks

**Blocking file I/O on the event loop risk:**
- Problem: Several helpers perform synchronous file reads and writes (`open`, `json.dump`, `os.replace`) and are documented as "always call via hass.async_add_executor_job". Any new call site that forgets the executor will block the event loop.
- Files: `custom_components/family_hub/__init__.py` (`_write_settings_backup_file` around line 1518, `_read_settings_backup_file` around line 1532, `_file_content_hash` around line 12184), `custom_components/family_hub/store.py` (lines 335 and 348), `custom_components/family_hub/updater.py` (zip extraction and copy)
- Cause: The convention is enforced by comments only.
- Improvement path: Keep the executor wrapper at every call site, add a lint or code-review checklist item, and move the file helpers into a dedicated module so the rule is visible.

**Full-file hashing at setup for cache busting:**
- Problem: `_file_content_hash` reads and hashes entire card bundles (up to 1.7 MB for the calendar card) on each setup to build the `?v=` URL.
- Files: `custom_components/family_hub/__init__.py` (around line 12184)
- Cause: Hash recomputed on every start.
- Improvement path: Cache the hash by file mtime and size, or use the integration version from `manifest.json`.

**Large card payloads on wall tablets:**
- Problem: Sending and parsing 0.1 to 1.7 MB of JS per dashboard load is heavy for kiosk hardware.
- Files: `custom_components/family_hub/card/*.js`
- Cause: Each card is a single self-contained file with inline CSS, translations, and logic.
- Improvement path: Gzip or brotli at the HTTP layer if HA does not already, lazy-load the calendar card's rarely used modes, and remove the `.bak_divfix` copy.

## Fragile Areas

**Dual-copy frontend sources:**
- Files: `custom_components/family_hub/card/family-week-calendar-card.js`, `custom_components/family_hub/family-week-calendar-card.js`, `custom_components/family_hub/card/family-week-calendar-card.js.bak_divfix`
- Why fragile: Three near-identical copies of the calendar card exist. Edits are easy to make in the wrong one.
- Safe modification: Confirm which path the static registration serves (`card/`), edit only that file, and delete the others once the canonical copy is chosen.
- Test coverage: None (no frontend tests).

**Home Assistant internals used by best-effort code:**
- Files: `custom_components/family_hub/__init__.py` (`_register_dashboard_resource`, around line 12200; sign-path usage in the export view at line 1724)
- Why fragile: Uses Lovelace storage collection internals and `async_sign_path`, neither of which is a public API. Upgrades of Home Assistant can break them silently.
- Safe modification: Pin the minimum tested HA version in `custom_components/family_hub/manifest.json` (currently only `hacs.json` declares `homeassistant: 2024.1.0`), and add a startup log line when the best-effort path no-ops.
- Test coverage: None.

**Sprawling websocket surface area with `vol` schemas:**
- Files: `custom_components/family_hub/__init__.py` (dozens of `family_hub/...` websocket types, for example `family_hub/update_grocy_product` at line 8582 and `family_hub/update_grocy_stock_entry` at line 8978), `custom_components/family_hub/chores_websocket_api.py`, `custom_components/family_hub/device_settings_websocket_api.py`
- Why fragile: Each handler re-implements entry lookup and Grocy-configured checks (`api_key = (entry.options.get(CONF_GROCY_API_KEY) ...)`), so a missed guard in one handler creates an inconsistent authorization or configuration path.
- Safe modification: Route all new handlers through one helper that resolves the entry and enforces admin and Grocy-configured checks, then add the new type to the schema table.
- Test coverage: None.

**Shared mutable state across modules:**
- Files: `custom_components/family_hub/__init__.py` (`hass.data[DOMAIN]["entries"]`), `custom_components/family_hub/store.py`, `custom_components/family_hub/chore_engine.py`
- Why fragile: Module-level caches and the `hass.data` dict are read and written from many handlers, so ordering of setup and unload matters.
- Safe modification: Keep reads through a single accessor, and guard unload paths against stale entries.
- Test coverage: None.

## Scaling Limits

**Single-instance, file-backed storage:**
- Current capacity: Settings and per-feature state are stored through HA `Store` objects (`custom_components/family_hub/store.py`) and JSON backup files under `<config>/family_hub_backups/`.
- Limit: Whole-document rewrites on every change; history snapshots are retained in a store that is rewritten each time.
- Scaling path: Move history to an append-only file or the HA recorder, and cap retained snapshots explicitly.

**Upload size limits:**
- Current capacity: 20 MB compressed and 200 MB uncompressed for self-update (`custom_components/family_hub/updater.py`, `MAX_ZIP_BYTES`, `MAX_UNCOMPRESSED_BYTES`).
- Limit: The uncompressed cap is far larger than the ~200 KB integration itself, so a crafted package can consume disk on a small device before it is rejected.
- Scaling path: Lower `MAX_UNCOMPRESSED_BYTES` to a few megabytes, close to the real package size.

## Dependencies at Risk

**Home Assistant platform coupling:**
- Risk: The integration depends on HA internals (Lovelace storage, `homeassistant.components.http.auth`, `local_todo` service calls at `__init__.py` around lines 3080-3151). `manifest.json` lists `frontend`, `http`, `lovelace`, `file_upload`, and `image_upload` with no version floor.
- Impact: HA releases can break setup or the todo bridge with no code change in this repo.
- Migration plan: Declare the minimum tested HA version in `manifest.json`, and isolate internal-API calls behind a single adapter module.

**External Grocy API:**
- Risk: The integration calls Grocy's REST API directly (`/api/objects/*`, `/api/files/*`), with no versioning or schema check.
- Impact: A Grocy upgrade that changes object or field names breaks pantry, shopping list, and recipe features.
- Migration plan: Check the Grocy version at connection time and log a clear warning for unsupported versions.

## Missing Critical Features

**No automated release or integrity gate:**
- Problem: Releases are assembled by hand (`manifest.json` version is 1.168.85, but the changelog stops at 1.135.4). No script verifies that `manifest.json`, `CHANGELOG.md`, and the website changelog agree.
- Blocks: Trustworthy release notes and reproducible HACS installs.

**No uninstall-time cleanup documented:**
- Problem: Backups under `<config>/family_hub_backups/` and the `.storage` files for Family Hub are not removed on uninstall, and no docs tell the admin to remove them.
- Blocks: Clean removal of the integration; leftover household data remains on disk.

## Test Coverage Gaps

**Pure engine logic:**
- What's not tested: Chore, reward, goal, pantry, timer, and routine calculations (`custom_components/family_hub/chore_engine.py`, `reward_engine.py`, `goal_engine.py`, `pantry_engine.py`, `timer_engine.py`, `routine_engine.py`, `routine_library.py`, `grocy_reference.py` unit conversions).
- Files: `custom_components/family_hub/chore_engine.py`, `custom_components/family_hub/reward_engine.py`, `custom_components/family_hub/goal_engine.py`, `custom_components/family_hub/pantry_engine.py`, `custom_components/family_hub/timer_engine.py`, `custom_components/family_hub/routine_engine.py`, `custom_components/family_hub/grocy_reference.py`
- Risk: Arithmetic and date-boundary errors (week rollover, recurring chores, unit conversions) go unnoticed until a household sees a wrong number.
- Priority: High

**Self-updater:**
- What's not tested: Zip validation, path-traversal rejection, size caps, backup and rollback.
- Files: `custom_components/family_hub/updater.py`
- Risk: A broken update can leave the integration partially installed on a live system.
- Priority: High

**Settings backup and restore:**
- What's not tested: `_write_settings_backup_file`, `_read_settings_backup_file`, and the import/export flows in `config_flow.py`.
- Files: `custom_components/family_hub/__init__.py` (around lines 1510-1540), `custom_components/family_hub/config_flow.py`
- Risk: Restoring an old snapshot could silently drop people, calendars, or Grocy settings.
- Priority: High

**Frontend cards and XSS handling:**
- What's not tested: No JS tests, no escaping tests, and no visual regression checks for the 13 card and panel bundles.
- Files: `custom_components/family_hub/card/*.js`, `custom_components/family_hub/panel/*.js`
- Risk: Escaping regressions and layout breaks ship unnoticed.
- Priority: Medium

**Grocy integration:**
- What's not tested: Request construction, error mapping, and the Grocy-missing and Grocy-unreachable paths (`custom_components/family_hub/__init__.py` lines 4201-5100).
- Files: `custom_components/family_hub/__init__.py`
- Risk: Pantry and shopping features fail silently when Grocy is down or the key is wrong.
- Priority: Medium

---

*Concerns audit: 2026-10-26*
