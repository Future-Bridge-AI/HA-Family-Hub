# Phase 1: Clean Foundation - Research

**Researched:** 2026-10-26
**Domain:** Repo hygiene and fork identity for a Home Assistant custom integration (HACS), plus the first hassfest/HACS validation baseline
**Confidence:** HIGH (repo facts, HA-source API dating, hassfest result reproduced locally); MEDIUM on how the hosted GitHub run will differ from the local one

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Root-level duplicate cards (FOUND-01)**
- **D-01:** Triage each root-level `.js` against its served copy in `card/`/`panel/` before deleting. Default outcome is **delete the root copy without porting**: the served copies are the newer, live code (e.g. calendar 31k vs 23.5k lines), and root edits (including upstream commit `8f7172d`) never ran. Port a root-only hunk only if it is a clearly self-contained fix that is absent from the served copy; anything ambiguous is recorded, not ported.
- **D-02:** Record the triage outcome per file (kept / ported hunk / discarded, one line each) in a phase artifact `01-TRIAGE.md`, so the deletion is auditable later.
- **D-03:** Delete `card/family-week-calendar-card.js.bak_divfix` (≈1.2 MB). It is the only consumer of the 9 "orphan" translation keys (verified: `chore_due_label`, `small_screen_mode_hint`, `goals_in_chores_*` appear only there), so it is debris, not unfinished served work.
- **D-04:** Deletions go in their own commit(s), separate from any ported hunk, so a port can be reviewed and reverted independently.

**Translations (FOUND-02, FOUND-03)**
- **D-05:** `git mv` `it`, `nl`, `pl`, `pt`, `pt-BR` from the integration root into `translations/` unchanged (key parity with `translations/en.json` already verified: 2,139 keys each, 0 missing, 0 extra).
- **D-06:** **Do not port** the 9 orphan keys from root `de`/`es`: no served code references them (only the `.bak_divfix` file does). Note them in `01-TRIAGE.md` in case upstream later ships the feature they belonged to.
- **D-07:** Delete the truncated root `de.json`, `en.json`, `es.json`, `fr.json` after a key diff against their `translations/` counterparts confirms nothing served is lost; record the diff summary in `01-TRIAGE.md`.
- **D-08:** Delete `strings.json` — custom integrations do not read it and it has diverged from `translations/en.json`.
- **D-09:** Preserve the non-standard `fh_ui` top-level category exactly as is (cards load it via `loadBackendTranslation("fh_ui", …)`). Any hassfest objection to it is recorded for Phase 3, not fixed here.

**Untracking and hygiene (FOUND-04, FOUND-05)**
- **D-10:** `git rm -r --cached` all `custom_components/family_hub/__pycache__/` in its own commit (49 files). `.gitignore` already covers them; add `.env`, `*.bak*`, `family_hub_backups/`, `.storage/` (and `dev/.ha-*` style local HA volumes for Phase 2).
- **D-11:** Remove the `\Screenshots/` directory (15 tracked files, name begins with a literal backslash) rather than renaming it: `images/readme/` already holds the README/site screenshots and no file references `\Screenshots/` (the README "Screenshots" anchor points at its own `#a-look-around` section). If any image there has no equivalent in `images/readme/`, list it in `01-TRIAGE.md` before deleting.
- **D-12:** Icons — keep root `custom_components/family_hub/icon.png` (served: `ICON_URL` → `{integration_dir}/icon.png`, `__init__.py` ~12550) and the `brand/` folder (HACS/HA brand assets). Delete the byte-identical, unserved root duplicates `icon (1).png`, `icon@2x.png`, `logo.png`, `logo@2x.png` (md5 matches `brand/` copies).
- **D-13:** Delete the empty `custom_components/family_hub/readme.md` (1 byte); HACS renders the repo-root `README.md` (`render_readme: true`).

**Fork identity (FOUND-06)**
- **D-14:** Codeowner becomes `@Future-Bridge-AI` (authenticated GitHub login); `documentation` → `https://github.com/Future-Bridge-AI/HA-Family-Hub`, `issue_tracker` → `…/issues`. — **Reversibility:** reversible.
- **D-15:** README badges, HACS one-click links and documentation links point at `Future-Bridge-AI/HA-Family-Hub`; docs site config (`website/docusaurus.config.js`: `url`, `organizationName`, `editUrl`, navbar/footer links, issues/releases links) points at the fork and `https://future-bridge-ai.github.io/HA-Family-Hub/`.
- **D-16:** Keep visible upstream credit: a short "Based on [JVarhol/HA-Family-Hub](…) by its original author, licensed GPLv3" line in README (and site footer if a credit line fits). `LICENSE` unchanged.
- **D-17:** Do NOT change `domain` (`family_hub`), integration `name`, service names, `family_hub/...` websocket prefixes, card element tags, storage keys or static URL paths — renaming any of these orphans saved dashboards/automations. — **Reversibility:** one-way — renaming after release breaks every saved dashboard, automation and stored data key.
- **D-18:** No ongoing upstream sync in this milestone. Record (in `01-TRIAGE.md` or a short note in `CONTRIBUTING`/README dev section) that any future upstream pull must map root-file edits onto `card/`/`panel/`/`translations/`.

**Versioning and HA versions (FOUND-07, FOUND-08)**
- **D-19:** Continue upstream numbering, strictly monotonic: next fork version **1.169.0** set in `manifest.json` (fork-identity release). Git tags will be `vX.Y.Z` equal to `manifest.json`. Record the scheme in PROJECT.md Key Decisions. — **Reversibility:** one-way — once Home installs a fork release via HACS, a lower or reset number looks like a downgrade and no update is offered.
- **D-20:** Pinned HA version for Dev, Preview and tests: **2026.10.4** (the version `pytest-homeassistant-custom-component` 0.13.375 pins; requires Python 3.14). Record it once in a single `versions.env` (or equivalent) at repo root that Phase 2/3 tooling reads.
- **D-21:** `hacs.json` `homeassistant` minimum is set to the **lowest version the code actually needs**, not the pinned test version: verify when `StaticPathConfig` / `hass.http.async_register_static_paths` (and any other newest API used, e.g. calendar `DATA_COMPONENT`) became available and set the minimum to that release (expected ~2024.7+). Rationale: raising it to 2026.10.4 could block the family's Home HA from updating if it runs an older version. Update PROJECT.md's "HA >= 2024.1" constraint to match.

**Validation baseline (FOUND-09)**
- **D-22:** Add a GitHub Actions workflow (`validate.yml`: `hacs/action@main` with `category: integration`, `home-assistant/actions/hassfest@master`, plus `workflow_dispatch`) in this phase, **non-blocking** (not a required check), run it once after the identity changes, and record the full failure list in `01-VALIDATION-BASELINE.md`. Fixing failures is Phase 3 work; do not add `continue-on-error` blankets.
- **D-23:** Repo-settings items HACS checks that can't be fixed in code (Issues enabled on the fork, repository description, topics) are listed in `01-VALIDATION-BASELINE.md` as manual steps for the developer.

**Commit structure**
- **D-24:** One logical change per commit (untrack pyc; delete root JS; move translations; delete root translations + strings.json; hygiene deletions; identity; version + hacs.json; validate workflow), so each is independently revertible.

### Claude's Discretion
- Exact wording of the upstream credit line and of `01-TRIAGE.md` / `01-VALIDATION-BASELINE.md`.
- How to verify the minimum-HA API dates (HA release notes / source tags).
- Whether `versions.env` is a plain env file or another single-source format, as long as Phase 2/3 can read it.

### Deferred Ideas (OUT OF SCOPE)
- Fixing hassfest/HACS failures and making validation a required check — Phase 3 (CI-03).
- CI guards against stray root `.js`/`.pyc`/`*.bak*` and translation key drift — Phase 3 (CI-04).
- Moving `fh_ui` to a schema-valid location — decide in Phase 3 based on hassfest output.
- Bumping `deploy-docs.yml` off Node 20 — low priority, Phase 3 CI work.
- Reconciling `CHANGELOG.md` (stops at v1.135.4) with the manifest version history — Phase 4 release work (REL-01/LOOP-04).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FOUND-01 | Root duplicate `.js` + `.bak_divfix` removed after per-file diff review | Per-file triage table (§Root duplicate triage): all 14 root files are stale snapshots (max version tag ≤ v1.147.0 vs served ≥ v1.168.76); 2 are byte-identical to served; no reference to root paths anywhere |
| FOUND-02 | `it/nl/pl/pt/pt-BR` live in `translations/` | Verified 2,139 leaf keys each, same top-level keys; `pt.json` and `pt-BR.json` are byte-identical; exact `git mv` commands |
| FOUND-03 | Translations exist once; root de/en/es/fr + `strings.json` removed; `fh_ui` preserved | Key diff results (§Root translation diffs): 9 orphan keys only in root de/es; root en/fr have none; `strings.json` has 2 stale-only keys, nothing reads it |
| FOUND-04 | No tracked `.pyc`; `.gitignore` covers `.env`, `*.bak*`, `family_hub_backups/`, `.storage/` | 49 tracked pyc (25 cpython-310, 24 cpython-314); current `.gitignore` quoted; additions listed |
| FOUND-05 | `\Screenshots/`, duplicate icons, empty readme removed | Exact working `git rm` pathspec; equivalence map for the 15 files; md5 table for icons |
| FOUND-06 | Fork identity everywhere; credit + GPLv3 kept; domain etc. unchanged | Exhaustive reference list split must-change / keep, including 14 README `raw.githubusercontent.com` image URLs not named in CONTEXT |
| FOUND-07 | Version scheme recorded; next version in manifest | HACS update detection uses GitHub Release tags, not `manifest.json` — implications for 1.169.0 |
| FOUND-08 | `hacs.json` minimum = real need; one pinned HA recorded | **Real minimum is 2024.12.0, not ~2024.7** (§Minimum HA version); pin 2026.10.4 confirmed on PyPI |
| FOUND-09 | First hassfest + HACS failure list recorded | Hassfest baseline reproduced locally with HA 2026.10.4's own hassfest (2 errors, 1 warning); HACS checks predicted from HACS source (3 repo-settings failures verified against the fork's live GitHub metadata) |
</phase_requirements>

## Summary

This phase is deletions, moves, link rewrites and one new workflow file. No runtime behaviour changes. The research found four things that change the plan relative to CONTEXT.md:

1. **The real minimum HA is 2024.12.0, not ~2024.7.** `StaticPathConfig` needs 2024.7.0, but `calendar.const.DATA_COMPONENT` first appears in 2024.10.0 and `FamilyHubOptionsFlow()` (no-arg, reads `self.config_entry`) only works from 2024.12.0. D-21's own rule ("lowest version the code actually needs") therefore yields `"homeassistant": "2024.12.0"`. Nothing the integration imports has been removed by HA 2026.10.4.
2. **Root duplicates are all stale snapshots.** Upstream's last commit `8f7172d` did not add fixes to the root copies; it *regressed* four of them (active-timers, chores, goals, my-chores) to older content. Before that commit those four were byte-identical to the served copies. Every root file's newest version tag (≤ v1.147.0) is older than its served copy's (≥ v1.168.76). The correct triage outcome is "discard all 14, port nothing".
3. **The README embeds 14 absolute image URLs on `raw.githubusercontent.com/JVarhol/HA-Family-Hub/main/images/readme/...`.** CONTEXT lists badges and links but not these. They must move to the fork or the fork's README renders upstream's images.
4. **The first validation run is predictable.** Running HA 2026.10.4's own hassfest on a copy of the repo in the post-Phase-1 state gives 2 errors and 1 warning (manifest key order; `fh_ui` category + `grocy_url` string containing a URL in `translations/en.json`; a CONFIG_SCHEMA warning). HACS will fail 3 checks on the fork as it stands today (Issues disabled, no topics, license not detected) — all three verified against the fork's live GitHub metadata and HACS's validator source. The license failure touches D-16 ("`LICENSE` unchanged"): GitHub reports `NOASSERTION` because `LICENSE` has a custom header before the GPLv3 text.

**Primary recommendation:** Set `hacs.json` `homeassistant` to `2024.12.0`, delete all root duplicates without porting, rewrite identity surfaces per the exhaustive list below (including README raw-image URLs), keep the manifest key order untouched so the baseline is honest, and record the local hassfest reproduction plus the HACS predictions in `01-VALIDATION-BASELINE.md`, replacing them with the hosted-run output once the developer has pushed the branch and enabled Actions.

## Architectural Responsibility Map

This phase has no runtime tiers; "tier" here is the delivery surface that owns each concern.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Served card/panel JS | `custom_components/family_hub/card/`, `panel/` (static paths in `__init__.py`) | — | Only these two folders are registered via `StaticPathConfig` |
| HA translations | `custom_components/family_hub/translations/*.json` | `fh_ui` category read by cards via `loadBackendTranslation` | HA loads only `translations/` |
| HACS update/min-version gating | `hacs.json` + GitHub Releases | `manifest.json` version | HACS reads release tag for "available version"; `hacs.json` enforced at download |
| Identity (links/credit) | `manifest.json`, README, `website/` | `.github/` | Pure metadata; nothing at runtime reads the upstream URL |
| Validation | `.github/workflows/validate.yml` | GitHub repo settings (Issues/topics) | Some HACS checks depend on repo settings, not files |

## Standard Stack

No application packages are installed in this phase. The "stack" is GitHub Actions plus local reproduction tooling.

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| `hacs/action` | `@main` (docs-prescribed; docker image `ghcr.io/hacs/action:main`) | HACS repository validation | Official HACS publisher action [CITED: hacs.xyz/docs/publish/action/; VERIFIED: raw.githubusercontent.com/hacs/action/main/action.yml] |
| `home-assistant/actions/hassfest` | `@master` | hassfest manifest/translation/dependency validation | Official HA action [CITED: github.com/home-assistant/actions] |
| `actions/checkout` | `@v4` | Checkout for the hassfest job | Same major as the existing `deploy-docs.yml` (`actions/checkout@v4`) [VERIFIED: `.github/workflows/deploy-docs.yml`] |

### Supporting (local reproduction only, nothing committed)
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `uv` + Python 3.14.9 | present on this machine | venv for HA 2026.10.4 | Reproduce hassfest locally; Python 3.14 is already installed by `uv` [VERIFIED: `uv python list` shows `cpython-3.14.9-linux-x86_64-gnu` installed] |
| `homeassistant==2026.10.4` | 2026.10.4 (PyPI, 2026-10-24) | hassfest runtime + pinned version | Latest on PyPI today [VERIFIED: pypi.org/pypi/homeassistant/json] |
| `pytest-homeassistant-custom-component` | 0.13.375, `requires_python >=3.14`, pins `homeassistant==2026.10.4` | Confirms D-20 pin (used in Phase 3) | [VERIFIED: pypi.org/pypi/pytest-homeassistant-custom-component/json, uploaded 2026-10-25] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Floating `@main`/`@master` action refs (D-22) | Pin to full commit SHA + Dependabot `github-actions` ecosystem | Safer supply chain; D-22 locks the floating refs, so keep them now and raise pinning in Phase 3 (see Security Domain) |
| Plain `versions.env` | `.tool-versions`, `pyproject` | `versions.env` (KEY=VALUE) is readable by bash `source`, `docker compose --env-file`, `make include` and Python without a parser — recommended |

**Installation (local hassfest reproduction, in a scratch dir outside the repo):**
```bash
uv venv --python 3.14 "$WORK/venv"
uv pip install --python "$WORK/venv/bin/python" "homeassistant==2026.10.4" infrared-protocols tqdm
git clone --depth 1 --branch 2026.10.4 https://github.com/home-assistant/core.git "$WORK/core"
```
(`infrared-protocols` and `tqdm` were the only two extra modules hassfest's imports needed when run this session [VERIFIED: ran it].)

## Package Legitimacy Audit

No external packages are added to the repository in this phase (no `requirements`, `package.json`, `pyproject` changes). The only third-party code introduced is three GitHub Actions referenced from `validate.yml`.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `hacs/action` | GitHub Actions | multi-year, official HACS org | n/a | github.com/hacs/action | n/a (not a registry package; documented in hacs.xyz) | Approved (docs-prescribed) |
| `home-assistant/actions` | GitHub Actions | official HA org | n/a | github.com/home-assistant/actions | n/a | Approved (docs-prescribed) |
| `actions/checkout` | GitHub Actions | official | n/a | github.com/actions/checkout | n/a | Approved (already used) |

The local-reproduction pip packages (`homeassistant`, `infrared-protocols`, `tqdm`) are installed only in a scratch venv outside the repo, not recommended into the repo, so the `package-legitimacy` gate does not apply; `homeassistant==2026.10.4` is verified on PyPI.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Minimum HA version (D-21) — highest priority finding

**Result: `hacs.json` `"homeassistant": "2024.12.0"`.** Confidence HIGH for the three binding constraints (each read from HA source at tags this session); MEDIUM that nothing else raises it, because the integration has not been run on 2024.12.

### Every HA API the integration imports or relies on

Imports enumerated by grepping `custom_components/family_hub/*.py` for `homeassistant` imports (49 distinct import lines). Each symbol was then checked in HA core source.

| API (where used) | First available | Present in 2026.10.4 | Source |
|------------------|-----------------|----------------------|--------|
| `StaticPathConfig` + `hass.http.async_register_static_paths` (`__init__.py:51`, `12553-12571`) | **2024.7.0** — absent in 2024.6.4 (no match), defined at `homeassistant/components/http/__init__.py:141` in 2024.7.0 | Yes (re-exported with `# noqa: F401`; method at `http/server.py:367`) | [VERIFIED: raw.githubusercontent.com/home-assistant/core/{2024.6.4,2024.7.0,2026.10.4}/homeassistant/components/http/] |
| `from homeassistant.components.calendar.const import DATA_COMPONENT` (`__init__.py:72`, used at `3850`, `3932`, `3994`) | **2024.10.0** — no match in `calendar/const.py` at 2024.9.1/.2/.3; first match at 2024.10.0b0 | Yes (`const.py:17`) | [VERIFIED: raw.githubusercontent.com/home-assistant/core/{2024.9.3,2024.10.0b0,2024.10.0,2026.10.4}/homeassistant/components/calendar/const.py] |
| `FamilyHubOptionsFlow()` created with no args (`config_flow.py:769`) and reading `self.config_entry.options` (`config_flow.py:963`) | **2024.12.0** — base `OptionsFlow` has `config_entry` property (`def config_entry(self) -> ConfigEntry`) in 2024.12.0b0 and 2024.12.0; absent from base `OptionsFlow` in 2024.10.0 and 2024.11.0/.3 (there it only exists on `OptionsFlowWithConfigEntry`) | Yes, read-only property at `config_entries.py:4174` (the explicit-set shim for custom integrations is gone; this code only reads it) | [VERIFIED: raw.githubusercontent.com/home-assistant/core/{2024.11.3,2024.12.0b0,2024.12.0,2026.10.4}/homeassistant/config_entries.py] |
| `CalendarEntityFeature.{CREATE,DELETE,UPDATE}_EVENT` (`__init__.py:3854,3936,3998`) | ≤2023.11.0 (`CREATE_EVENT = 1`, `DELETE_EVENT = 2`, `UPDATE_EVENT = 4`) | Yes | [VERIFIED: calendar/const.py at 2023.11.0 and 2026.10.4] |
| `TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature` (`todo.py:42`) | 2023.11 (platform introduced) — below the floor either way | Yes | [VERIFIED: todo/__init__.py at 2026.10.4 imports them] |
| `panel_custom.async_register_panel(frontend_url_path=…, webcomponent_name=…, sidebar_title=…, sidebar_icon=…, module_url=…, embed_iframe=…, trust_external=…, require_admin=…, config=…)` (`__init__.py:12610`) | long-standing | Yes, all those parameters exist (`panel_custom/__init__.py:80-103`) | [VERIFIED: 2026.10.4] |
| `frontend.async_remove_panel(hass, PANEL_URL)` (`__init__.py:13156`) | long-standing | Yes (`frontend/__init__.py:407`) | [VERIFIED: 2026.10.4] |
| `async_sign_path(hass, path, timedelta)` (`config_flow.py:1143`) | long-standing | Yes, `(hass, path, expiration, *, refresh_token_id=None, use_content_user=False)` | [VERIFIED: http/auth.py:52-59 at 2026.10.4] |
| `process_uploaded_file(hass, id)` as context manager (`config_flow.py:778,858`) | long-standing | Yes, `@contextmanager` at `file_upload/__init__.py:35-36` | [VERIFIED: 2026.10.4] |
| `async_at_started(hass, cb)` (`__init__.py:12378`) | long-standing | Yes | [VERIFIED: helpers/start.py:75] |
| `event_trigger.TRIGGER_SCHEMA`, `CONF_EVENT_TYPE`, `CONF_EVENT_DATA`, `CONF_PLATFORM`, `async_attach_trigger(..., platform_type="device")` (`device_trigger.py:44,154-162`) | long-standing | Yes (`platform_type: str = "event"` is keyword-only) | [VERIFIED: homeassistant/triggers/event.py:9-14, 116-123 at 2026.10.4] |
| `TriggerActionType`, `TriggerInfo` from `homeassistant.helpers.trigger` | long-standing | Yes — `helpers/trigger` is now a package; `TriggerActionType` at `__init__.py:305`, `TriggerInfo` at `:327` | [VERIFIED: 2026.10.4] |
| `DeviceInfo` from `homeassistant.helpers.entity` (`switch.py:55`, `device_settings_entity_shared.py:52`) | long-standing | Still importable (re-imported in `helpers/entity.py:60`) | [VERIFIED: 2026.10.4] |
| `DEVICE_TRIGGER_BASE_SCHEMA`, `cv.string/date/datetime`, `websocket_api.{websocket_command,async_response,ActiveConnection,event_message,async_register_command}`, `HomeAssistantView`, `__version__`, `async_get_integration`, selectors (`BooleanSelector`, `EntitySelector`, `FileSelector`, `NumberSelector`, `SelectSelector`, `TextSelector` + configs/modes/types) | long-standing | Yes | [VERIFIED: 2026.10.4 source checks; cv names grep-matched in `config_validation.py`] |

Python syntax: all 25 `.py` files parse with `ast.parse(..., feature_version=(3, 12))` (HA 2024.12 runs on Python 3.12) [VERIFIED: ran `python3 -B -I` AST parse, no files written]. Frontend JS uses only `hass.connection`, `hass.localize`, `hass.loadBackendTranslation`, `hass.callService`, `hass.themes`, `<ha-card>`, `<ha-form>`, `<ha-icon>` — all older than 2024.12 [VERIFIED: grep over `card/*.js` and `panel/*.js`].

### What 2026.10.x changed that affects this integration

- **Nothing the integration imports was removed.** Every symbol above resolves at 2026.10.4.
- **voluptuous replaced by probatio (core 2026.9).** HA aliases `voluptuous` to `probatio` at `import homeassistant` time (`homeassistant/__init__.py:3-11`: `from probatio.compat import install_as_voluptuous` … `install_as_voluptuous()`), so `import voluptuous as vol` in this integration keeps working and voluptuous is no longer a core requirement [VERIFIED: raw.githubusercontent.com/home-assistant/core/2026.10.4/homeassistant/__init__.py; CITED: contributors.home-assistant.io/blog/2026/09/30/probatio-validation-engine — "Custom integrations need no changes"]. Error message text changed; tests that assert validation error text may need updating (Phase 3).
- **`OptionsFlow.config_entry` explicit assignment** was removed after 2025.12; this integration only reads it, so it is fine.

### Why not a higher floor
Raising to the pinned 2026.10.4 would make HACS refuse downloads on older HA (`_ensure_download_capabilities` raises "This version requires Home Assistant X or newer" when `ha_version < hacs.json homeassistant`) [VERIFIED: hacs/integration `repositories/base.py:1449-1452`]. Home currently runs upstream v1.168.85, which already crashes on <2024.12 (options flow) — so Home is very likely already ≥ 2024.12 (see Open Questions Q1).

### Docs to update with the floor
`.planning/PROJECT.md:29` and `:110` say "HA >= 2024.1"; `.claude/CLAUDE.md:26,53,100` mirror it (generated from PROJECT.md — regenerate or edit both); `.planning/codebase/STACK.md` and `docs/onboarding-findings.md:30` also mention 2024.1 (historical; optional). `PROJECT_CONTEXT.md:3013` mentions `"homeassistant": "2024.1.0"` historically; leave.

## Root duplicate triage (D-01 / D-02)

Served path layout [VERIFIED: `__init__.py:12503-12512`]: `integration_dir = hass.config.path("custom_components", DOMAIN)`, `panel_path = f"{integration_dir}/panel/theme-builder-panel.js"`, `card_path = f"{integration_dir}/card/family-week-calendar-card.js"`, etc. Only `card/` and `panel/` are registered.

**Nothing references the root `.js` paths.** Grep over `*.py`, `*.js`, `*.json`, `*.yaml`, README, DOCUMENTATION, `website/`, `.github/`, `hacs.json`: only matches are Python docstring/comment mentions of card filenames and the `const.py` URL constants (`/family_hub_card/family-week-calendar-card.js` etc., which are URLs, not file paths), plus `PROJECT_CONTEXT.md:3002` (historical `content_in_root` note). [VERIFIED: grep this session]

### Key history facts (use in `01-TRIAGE.md`)
- Before upstream commit `8f7172d` (2026-10-25), root and served copies of `family-hub-active-timers-card`, `-chores-card`, `-goals-card`, `-my-chores-card` were **byte-identical** (blob hash equal at `8f7172d^`). `8f7172d` then overwrote only the root copies with *older* content (e.g. chores 6252 → 5869 lines, active-timers 1801 → 1524, goals 1937 → 1784, my-chores 160 → 1538). Served copies were untouched. [VERIFIED: `git rev-parse <commit>:path` compare, `git show --stat 8f7172d`]
- Root `family-right-now-card.js` and `theme-selector-card.js` are byte-identical to their served copies today (0 diff lines). [VERIFIED: `diff` hunk count 0]
- Version tags: the highest `1.xxx.y` tag mentioned in each root file is older than in its served copy for all 12 files that differ.

| Root file | Root lines | Served copy | Served lines | Newest tag root / served | Verdict |
|-----------|-----------:|-------------|-------------:|--------------------------|---------|
| `family-hub-active-timers-card.js` | 1524 | `card/` | 1801 | 1.119.0 / 1.168.79 | discard (root-only lines = older timer-alarm singleton) |
| `family-hub-chores-card.js` | 5869 | `card/` | 6252 | 1.132.61 / 1.168.79 | discard |
| `family-hub-goals-card.js` | 1784 | `card/` | 1937 | 1.132.59 / 1.168.79 | discard |
| `family-hub-my-chores-card.js` | 1538 | `card/` | 160 | 1.132.61 / 1.168.76 | discard — **served is smaller on purpose**: it is a deprecated shim ("DEPRECATED since v1.168.66") that renders the Chores card; root is the retired 1,500-line card |
| `family-hub-pantry-card.js` | 1600 | `card/` | 1704 | 1.132.59 / 1.168.79 | discard |
| `family-hub-recipe-box-card.js` | 2896 | `card/` | 3592 | 1.132.59 / 1.168.79 | discard |
| `family-hub-rewards-card.js` | 3958 | `card/` | 4285 | 1.132.61 / 1.168.79 | discard |
| `family-hub-todo-card.js` | 4310 | `card/` | 4414 | 1.132.59 / 1.168.79 | discard |
| `family-right-now-card.js` | 2047 | `card/` | 2047 | identical | discard (identical) |
| `family-screensaver-card.js` | 1558 | `card/` | 1643 | 1.132.61 / 1.168.76 | discard |
| `family-today-card.js` | 2738 | `card/` | 2901 | 1.132.59 / 1.168.79 | discard |
| `family-week-calendar-card.js` | 23534 | `card/` | 30925 | 1.147.0 / 1.168.85 | discard |
| `theme-builder-panel.js` | 1021 | `panel/` | 1131 | none / 1.168.76 | discard |
| `theme-selector-card.js` | 320 | `panel/` | 320 | identical | discard (identical) |

The 12 differing files each have roughly 125-140 root-only lines (the old timer-alarm block is the common one; calendar 1,003; my-chores 1,271 because the served file is a shim). Root-only lines in the sampled files are superseded older implementations, not fixes. The planner should still make the executor produce, per file, the evidence in the table (line counts, newest tag, identical-or-not) in `01-TRIAGE.md`; the executor can recompute the root-only-line count with a short script reading from stdin (no repo writes).

`card/family-week-calendar-card.js.bak_divfix` (1,244,693 bytes) is referenced by no file outside `.planning/` and `docs/onboarding-findings.md` (grep for `bak_divfix`). [VERIFIED]

Also note for D-18: upstream "Add files via upload" commits sometimes touched both copies (`74bb966` updated root and served) and sometimes only one; any future upstream pull must be mapped onto `card/`/`panel/`/`translations/`.

## Root translation diffs (D-05..D-09)

Leaf-key counts via recursive flatten [VERIFIED: ran `python3 -B -I`]:

| File | Leaf keys | vs `translations/<same>.json` |
|------|----------:|-------------------------------|
| `translations/en.json` | 2139 | reference |
| root `en.json` | 1117 | 0 only-in-root, 1022 only-in-translations, 13 shared keys with different value |
| root `de.json` / `es.json` | 1019 | **9 only-in-root**, 1129 only-in-translations, 6 shared keys with different value |
| root `fr.json` | 2139 | identical key set, 0 value diffs |
| root `it/nl/pl/pt/pt-BR.json` | 2139 each | symmetric difference vs `translations/en.json` = 0; top-level keys `['config', 'options', 'device_automation', 'fh_ui']` each; no `translations/` copy yet |

**The 9 orphan keys (root `de.json` and `es.json` only; not in `translations/en.json`; zero hits in served `*.js`/`*.py`; each hit exactly once in `card/family-week-calendar-card.js.bak_divfix`):**
`fh_ui.settings.chore_due_hint`, `fh_ui.settings.chore_due_label`, `fh_ui.settings.date_and_time`, `fh_ui.settings.date_only`, `fh_ui.settings.goals_in_chores_hint`, `fh_ui.settings.goals_in_chores_label`, `fh_ui.settings.goals_in_rewards_hint`, `fh_ui.settings.goals_in_rewards_label`, `fh_ui.settings.small_screen_mode_hint`.

Shared-key value differences (record the key names in `01-TRIAGE.md`; the `translations/` wording is the newer one, e.g. root en `config.step.calendars.title` "Calendars" vs translations "Family calendar"):
- root en vs translations en (13): `config.step.calendars.{data.calendars,description,title}`, `config.step.member_profile.{description,title}`, `fh_ui.add_event.reminder_hint`, `fh_ui.settings.{calendars_tap_hint,chores_rewards_color_hint}`, `fh_ui.today.add_event.reminder_hint`, `options.abort.{export_done,no_backups}`, `options.step.{export_backup.description,restore_backup_pick.description}`.
- root de/es vs translations (6 each): `fh_ui.add_event.reminder_hint`, `fh_ui.settings.{calendars_tap_hint,chores_rewards_color_hint,small_screen_mode_label}`, `fh_ui.today.add_event.reminder_hint`, `fh_ui.todo.create_modal.no_lists`. Root `small_screen_mode_label` wording ("… — nur dieses Gerät" / "… — solo este dispositivo") belongs to the same retired feature as the orphan keys.

`pt.json` and `pt-BR.json` are byte-identical (same md5 `2c33d85a4f5e8c6c7fc1701232a652ce`). Move both as-is (D-05); note it in triage. Placeholder tokens (`{x}`/`%x%`) differ from `en` in the same 16 keys for every language including already-live de/es/fr, so no new-language-specific placeholder problem was found. [VERIFIED]

**`strings.json`:** 566 leaf keys vs 2139 in `translations/en.json`; 2 keys only in `strings.json` (`fh_ui.settings.reminders_hint_html`, `fh_ui.settings.section_reminders`), 2 shared keys with different values; same four top-level keys. No code reads it — the only references anywhere are prose in `PROJECT_CONTEXT.md` (lines 63, 201, 292, 406, 575, 874, 950, 1074-1083) describing a convention of keeping it in sync. [VERIFIED: grep this session] Consider one line in the triage/CONTRIBUTING note that the "keep strings.json and translations/en.json in sync" convention in `PROJECT_CONTEXT.md` is retired.

Move commands (verified with `git mv -n`; run without `-n`): `git mv custom_components/family_hub/{it,nl,pl,pt,pt-BR}.json` each to `custom_components/family_hub/translations/<same name>`. `translations/` currently tracks only `de/en/es/fr.json`.

## `\Screenshots/` (D-11)

15 tracked files, no file references the directory (grep for `Screenshots/`, `\Screenshots`, `%5CScreenshots` outside `.git`/`.planning`/`.claude` found only unrelated `/img/screenshots/` site paths). [VERIFIED]

`git ls-files` prints the path quoted as `"\\Screenshots/…"`. **Working invocation (dry-run verified, it listed all 15 files):**
```bash
git rm -r -- ':(literal)\Screenshots'
```
`git rm -r -- '\Screenshots'` also worked in dry-run; `'\\Screenshots'` and `'[\]Screenshots'` fail with "pathspec did not match". Use the `:(literal)` form. Never use `rm -rf \Screenshots` unquoted in a shell.

Equivalence map (judgement from filenames; three images were opened and are an older UI with placeholder data — "Person 1", "Oceans Calling" — newer shots exist for the same views). The site folder `website/static/img/screenshots/` is the better comparison set than `images/readme/` alone:

| `\Screenshots/` file | Equivalent present |
|----------------------|--------------------|
| `Main Calendar.png` | `images/readme/view-planner.webp`, site `calendar-week.webp` |
| `Month View.png` | `images/readme/view-month.webp`, site `calendar-month.webp` |
| `Calendar Mobile.png` | `images/readme/phone.webp`, site `calendar-phone.webp` |
| `Chores.png` | `images/readme/card-chores.webp`, site `chores.webp` |
| `Rewards.png` | `images/readme/card-rewards.webp`, site `rewards.webp` |
| `Family Today Card.png` | `images/readme/card-today.webp`, site `today-card.webp` |
| `Shopping List.png` | `images/readme/card-todo.webp`, site `todo-lists.webp` |
| `Add Modal Main Screen.png` | site `add-event.webp` only |
| `Recipe Box.png` | site `recipe-box.webp` only |
| `My Chores and My Goals Mini Cards.png` | site `my-chores.webp` only (card is deprecated) |
| `Import Recipe to Grocy.png` | **none** — list in triage |
| `Screen Saver Card.png` (it is a card-config dialog) | **none** — list in triage |
| `Chores Mobile View.jpg` | **none** (closest: `phone.webp`) — list in triage |
| `Rewards Mobile View.jpg` | **none** — list in triage |
| `screenshots.txt` (1 byte) | n/a |

## Upstream identity surfaces (D-14..D-16)

Case-insensitive grep for `jvarhol|bordello` outside `.planning/`, `.claude/`, `node_modules/` and `.git/` [VERIFIED]. The `.github/` folder (issue templates, workflow) contains **no** upstream references.

### Must change (links and identity)

| File:line | Current | Change to |
|-----------|---------|-----------|
| `custom_components/family_hub/manifest.json:5` | `"@bordello_labs"` | `"@Future-Bridge-AI"` |
| `manifest.json:18` | `"documentation": "https://github.com/JVarhol/HA-Family-Hub"` | `https://github.com/Future-Bridge-AI/HA-Family-Hub` |
| `manifest.json:19` | `"issue_tracker": "https://github.com/JVarhol/HA-Family-Hub/issues"` | `…/Future-Bridge-AI/HA-Family-Hub/issues` |
| `README.md:4-6` | shields.io badges `github/v/release/JVarhol/…`, `github/issues/JVarhol/…`, `github/license/JVarhol/…` and their `<a href>` targets | `Future-Bridge-AI/HA-Family-Hub` (release badge will read "no releases" until Phase 4; license badge will read "not identifiable" until the LICENSE question is settled) |
| `README.md:17` | `https://jvarhol.github.io/HA-Family-Hub/` (lowercase; easy to miss) | `https://future-bridge-ai.github.io/HA-Family-Hub/` |
| `README.md:21,32,33,36,37,46,50,58,59,62,63,71,72,81` (**14 URLs**) | `https://raw.githubusercontent.com/JVarhol/HA-Family-Hub/main/images/readme/<file>.webp` | same path under `Future-Bridge-AI`; the images exist in this repo at `images/readme/`; they render once the branch is on `main` |
| `README.md:128` | HACS one-click `…/hacs_repository/?owner=JVarhol&repository=HA-Family-Hub&category=integration` | `?owner=Future-Bridge-AI&repository=HA-Family-Hub&category=integration` (line 132 `config_flow_start?domain=family_hub` has no owner — leave) |
| `website/docs/installation.md:14` | same HACS one-click link, `owner=JVarhol` | `owner=Future-Bridge-AI` (line 20 unchanged) |
| `website/docs/intro.md:37` | `[GitHub](https://github.com/JVarhol/HA-Family-Hub)` | fork URL (leave the HA Community thread link — upstream discussion, keep as is) |
| `website/docs/license.md:10` | `https://github.com/JVarhol/HA-Family-Hub/blob/main/LICENSE` | fork URL |
| `website/docusaurus.config.js:21` | `url: 'https://jvarhol.github.io'` | `url: 'https://future-bridge-ai.github.io'` |
| `:24` | `organizationName: 'JVarhol'` | `'Future-Bridge-AI'` |
| `:60` | `editUrl: 'https://github.com/JVarhol/HA-Family-Hub/tree/main/website/'` | fork URL |
| `:97`, `:133` | navbar and footer GitHub `href` | fork URL |
| `:124` | footer Issues `href` | fork `/issues` |
| `:137` | footer Releases `href` | fork `/releases` |

### Keep (credit / history — do not change)

- `LICENSE:2,654,674` (Copyright (C) 2026 Bordello Labs) — GPLv3 holder notice; D-16 says LICENSE unchanged.
- `README.md:151`, `DOCUMENTATION.md:758`, `website/docs/license.md:7`, `website/docusaurus.config.js:142` (footer copyright `Bordello Labs`) — copyright holder credit. Add a fork line next to them rather than replacing: e.g. README License section "Based on [JVarhol/HA-Family-Hub](https://github.com/JVarhol/HA-Family-Hub) by its original author, licensed GPLv3"; for the footer `copyright:` string append the same credit.
- `website/docs/changelog.md:6`, `website/docs/changelog-archive.md:6` — links to upstream's GitHub Releases pages for historical release notes (the fork has no releases yet; these are history, so keep).
- `custom_components/family_hub/card/family-week-calendar-card.js:18080` — a code comment containing the author's example entity id (`calendar.admin_jvarhol_com`); not a link, do not touch served JS in this phase.
- `PROJECT_CONTEXT.md` (7 hits, historical narrative), `docs/onboarding-findings.md` (3 hits, brief) — historical.
- Docs-site community thread links in `docusaurus.config.js` and `intro.md` — upstream discussion, keep.

### Related, easy to miss
- `website/static/admin/config.yml` (Decap CMS) holds `turbo_site_id: 9e6b9a7c-afd8-4355-b557-0ce70346a61f`, which belongs to upstream's Turbo site, plus `public_folder: "/HA-Family-Hub/img/uploads"`. It has no `JVarhol` string so grep missed it. The CMS will not work for the fork until reconfigured; harmless. Recommend leaving it and noting it in the baseline doc as out-of-scope.
- **Dangling `CHANGELOG_ARCHIVE.md` link** occurs twice: `README.md:143` and `CHANGELOG.md:4`. The docs site has its own `website/docs/changelog-archive.md` ("Older releases … before v1.103.0"). Recommended fix: link to `website/docs/changelog-archive.md` (a relative path that renders on GitHub, and root files are not subject to Docusaurus's `onBrokenLinks: 'throw'`). Alternative: drop the parenthetical.
- `.planning/PROJECT.md` and `.claude/CLAUDE.md` already say the project is hosted at `Future-Bridge-AI/HA-Family-Hub` (fine).

## Validation workflow, hassfest and HACS (D-22 / D-23)

### Recommended `validate.yml`

```yaml
# Source: hacs.xyz/docs/publish/action/ (HACS job) and github.com/home-assistant/actions (hassfest job)
name: Validate

on:
  push:
  pull_request:
  workflow_dispatch:

permissions: {}

jobs:
  hacs:
    name: HACS validation
    runs-on: ubuntu-latest
    steps:
      - uses: hacs/action@main
        with:
          category: integration

  hassfest:
    name: hassfest
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master
```

Notes:
- The HACS docs recommend `permissions: {}` and a daily `schedule` trigger; the hassfest README recommends `push`, `pull_request` and a daily `schedule`. Omit `schedule` for now (D-22 names only `workflow_dispatch`); add it in Phase 3 if wanted. [CITED: hacs.xyz, github.com/home-assistant/actions]
- `hacs/action` inputs: `category` (required), `ignore`, `repository`, `comment` (default `"true"`, posts PR comments), `github_token` (default `${{ github.token }}`) [VERIFIED: hacs/action `action.yml`]. With `permissions: {}` the PR comment cannot be written; the check result is still the job status.
- Two separate jobs so a failure in one does not hide the other, and each failure list is separately recorded.
- Own file, no `concurrency` group; `deploy-docs.yml` uses `group: pages`, so there is no interaction. `deploy-docs.yml` triggers only on `website/**` or its own file on `main`; `validate.yml` does not touch either.
- A `workflow_dispatch` button only appears in the Actions UI once the file is on the default branch (`main`); a `push` trigger runs it on whatever branch carries the file. Use the `push` trigger to get the baseline from the phase branch (`ccr-ab9176f1-jbs2rg` is the current branch; `main` is the default).
- **Manual step:** workflows on a fork are disabled until the owner clicks "I understand my workflows, go ahead and enable them" on the fork's Actions tab. [ASSUMED] — standard GitHub behaviour for forks, not tested here. Put it in D-23's manual-step list together with Issues, topics, Pages source.
- This session's `gh` has no access to the fork ("GitHub access to this repository is not enabled for this session"), so an executor in this environment cannot trigger or read the hosted run. Plan a `checkpoint:human-action` for the developer to push and paste/point to the run results, with the local reproduction (below) as the pre-recorded fallback.

### hassfest: what it enforces for a custom integration

Source: HA 2026.10.4 `script/hassfest/{manifest,dependencies,translations}.py` [VERIFIED: raw.githubusercontent.com/home-assistant/core/2026.10.4/script/hassfest/…].
- **Manifest key order is enforced.** `sort_manifest` sorts keys with `{"domain": ".domain", "name": ".name"}` so the required order is `domain`, `name`, then alphabetical; error text "Manifest keys are not sorted correctly: domain, name, then alphabetical order". Current manifest order (read this session): `domain, name, codeowners, config_flow, dependencies, after_dependencies, documentation, issue_tracker, iot_class, version`. Alphabetical would be `after_dependencies, codeowners, config_flow, dependencies, documentation, iot_class, issue_tracker, version`. So it fails today, independent of this phase.
- Custom schema (`CUSTOM_INTEGRATION_MANIFEST_SCHEMA`): `documentation` must be a URL not under the HA docs base; `version` required (via `validate_version`) and must parse as CalVer/SemVer/SimpleVer/BuildVer/PEP440; `issue_tracker` optional URL; `iot_class` required for non-virtual domains (present: `local_polling`); domain must equal directory name.
- Dependencies check: imports of other `homeassistant.components.*` must be in `dependencies`/`after_dependencies` unless in an allow-list that includes every `Platform` (calendar, todo, sensor, button, select, number, text, switch), `device_automation`, `frontend`, `panel_custom`, `websocket_api`. The integration declares `frontend, http, lovelace, file_upload, image_upload` + after `timer`. Ran clean.
- Translations: for the hosted/`--integration-path` run, hassfest validates **both** `strings.json` (if present) and `translations/en.json`. Other languages are not schema-checked.

### Reproduced baseline (post-Phase-1 state)

I ran HA 2026.10.4's own hassfest against **copies** in the scratch directory (never the repo): (a) the repo as it is now; (b) the simulated post-Phase-1 state (`strings.json`, root `*.json`, root `*.js`, duplicate icons, `readme.md` deleted; five languages moved into `translations/`; manifest identity + `1.169.0` applied; key order untouched).

State (b) result, which is what the hosted run should show, modulo hosted hassfest being a newer build:

```
* [ERROR] [MANIFEST] Manifest keys are not sorted correctly: domain, name, then alphabetical order
* [ERROR] [TRANSLATIONS] Invalid translations/en.json: not a valid option at 'fh_ui'. Got {'nav': {...
  the string should not contain URLs, please use description placeholders instead at 'config.step.grocy.data.grocy_url'. Got 'Grocy URL (e.g. http://homeassistant.local:9192)'
  the string should not contain URLs, please use description placeholders instead at 'options.step.grocy.data.grocy_url'. Got 'Grocy URL (e.g. http://homeassistant.local:9192)'
* [WARNING] [CONFIG_SCHEMA] Integrations which implement 'async_setup' or 'setup' must define either 'CONFIG_SCHEMA', 'PLATFORM_SCHEMA' or 'PLATFORM_SCHEMA_BASE'. …
```

Findings:
- State (a) shows the same plus duplicates for `strings.json` — deleting it (D-08) halves the translation noise.
- With `fh_ui` stripped from a scratch copy of `translations/en.json`, the only remaining translation errors are the two `grocy_url` URL strings. So Phase 3's translation work is: relocate `fh_ui` + reword two label strings. Sized small.
- `codeowners` `@Future-Bridge-AI`, the new documentation/issue_tracker URLs and `version: "1.169.0"` produced no hassfest error.
- Services, icons, dependencies, config_flow, requirements validators all passed.
- `config_schema` is only a WARNING (hassfest exit status is driven by errors).
- Not seen locally but possible in the hosted run: checks introduced after 2026.10.4 on `dev`; the hosted action pulls a docker image whose version is not pinned [ASSUMED].

Local reproduction recipe (all scratch, repo untouched; always `-B` and `PYTHONDONTWRITEBYTECODE=1`):
```bash
cd "$WORK/core" && PYTHONDONTWRITEBYTECODE=1 "$WORK/venv/bin/python" -B -m script.hassfest \
  --action validate --integration-path "$WORK/intcopy/family_hub"
```
`$WORK/intcopy/family_hub` is a `cp -r` of `custom_components/family_hub` minus `__pycache__` (hassfest needs the directory name to equal the domain). Run with the absolute venv path (a relative `../venv/bin/python` triggers a sys.prefix warning). Take care that a shallow `--branch 2026.10.4` clone gives the tag, not `dev`; the executor must confirm `homeassistant/const.py` shows `MINOR_VERSION = 10`, `PATCH_VERSION = "4"`. [VERIFIED: I fetched and checked out the tag in the scratch clone]

### HACS checks (hacs/action → `hacs/integration` `custom_components/hacs/validate/`)

Validators present: `archived, brands, description, hacsjson, images, information, integration_categories, integration_manifest, issues, license, topics` [VERIFIED: github.com/hacs/integration tree listing; each source read]. Predicted result for this repo as it will stand after Phase 1:

| Check | Rule (from source) | Predicted | Evidence |
|-------|--------------------|-----------|----------|
| archived | repo not archived | pass | — |
| brands | `custom_components/family_hub/brand/icon.png` in tree (else falls back to brands.home-assistant.io list) | **pass — keep `brand/`** | `brand/` contains icon.png, icon@2x.png, logo.png, logo@2x.png [VERIFIED: ls] |
| description | repository has a description | pass | fork description is "A Family hub and meal planning dashboard for home assistant like skylight tablets" [VERIFIED: api.github.com repos/Future-Bridge-AI/HA-Family-Hub] |
| hacsjson | `hacs.json` in root and matches schema (`name` required; `homeassistant`, `render_readme`, … allowed; extra keys rejected) | pass | schema read from `utils/validate.py` |
| images | README contains `<img` or `![` | pass | README uses `<img` |
| information | README.md in tree | pass | — |
| integration_manifest | `codeowners` list, `documentation` URL, `domain`, `issue_tracker` URL, `name`, `version` all present | pass after D-14 | — |
| integration_categories | warns only when `categories` absent | warning, no failure | source |
| **issues** | `has_issues` true | **FAIL** | fork API: `"has_issues": false` [VERIFIED: api.github.com] |
| **topics** | at least one topic | **FAIL** | fork API: `"topics": []` [VERIFIED] |
| **license** | GitHub license `spdx_id` present, not `NOASSERTION`, OSI-approved | **FAIL** | fork API: `license: {key: "other", spdx_id: "NOASSERTION"}` [VERIFIED]; the validator raises "The repository license could not be identified (SPDX: NOASSERTION)" |

The license failure has a root cause in-repo: `LICENSE` begins with a 16-line "Family Hub / Copyright (C) 2026 Bordello Labs / This program is free software…" notice before the GPLv3 text and appends another at the end, so GitHub's detector does not recognise GPL-3.0. D-16 says "LICENSE unchanged", so Phase 1 should only *record* this; the Phase 3 fix would be to restore the canonical GPLv3 text (move the notice into README / a `NOTICE` file) — a decision for the developer because it touches the license file. Put it in `01-VALIDATION-BASELINE.md` and Open Questions.

Manual repo-settings list for D-23 (`01-VALIDATION-BASELINE.md`): enable Issues; add topics (e.g. `home-assistant`, `hacs`, `homeassistant-integration`, `family-calendar`); confirm description; Settings → Pages → Source = GitHub Actions (needed before `deploy-docs.yml` can succeed on the fork); enable Actions on the fork.

## Versioning (D-19) and HACS update detection

- **HACS's "available version" is the latest GitHub Release tag, not `manifest.json`.** Docs: "If the repository uses GitHub releases, the tag name from the latest release is used to set the remote version … Just publishing tags is not enough, you need to publish releases." Otherwise "the 7 first characters of the last commit will be used." [CITED: hacs.xyz/docs/publish/start/]. Code: `pending_update` compares `display_available_version` and `display_installed_version` with `AwesomeVersion` (`version_left_higher_then_right`) when the repo has releases, else compares commits [VERIFIED: hacs/integration `repositories/base.py:408-427`, `utils/version.py`].
- Consequences for the plan: (1) setting `manifest.json` to `1.169.0` and creating a `v1.169.0` git tag is necessary but not sufficient for Home to be offered an update — Phase 4's release workflow must publish a GitHub **Release**. (2) The fork currently has **no releases** (`/releases` returns `[]`) [VERIFIED: api.github.com], so until Phase 4 HACS would track commit SHAs. (3) `AwesomeVersion` parses a leading `v`, so `v1.169.0` vs an installed `1.168.85` compares as 1.169.0 > 1.168.85 [ASSUMED — standard awesomeversion behaviour; not run]. The tag format of upstream's own releases could not be read (upstream API blocked this session) — see Open Questions Q2.
- Continuing at 1.169.0 is monotonic above 1.168.85 (the manifest value today) [VERIFIED: `manifest.json` `"version": "1.168.85"`]. No lower or reset number may ever be used (matches D-19 reversibility note).
- HACS enforces `hacs.json` `homeassistant` only at download time (see Minimum HA).

## Docs site

- `deploy-docs.yml` uses `actions/upload-pages-artifact` + `actions/deploy-pages` — it never pushes to `gh-pages`, so `organizationName`/`deploymentBranch` in `docusaurus.config.js` are not used by CI; change `organizationName` anyway for consistency (D-15). **No edit to `deploy-docs.yml` is needed.** [VERIFIED: file read]
- Site URL derives from `url` + `baseUrl`. `baseUrl: '/HA-Family-Hub/'` is already right (the fork's repo name is unchanged). New `url: 'https://future-bridge-ai.github.io'` (GitHub Pages hosts are lowercase).
- `onBrokenLinks: 'throw'` and `markdown.hooks.onBrokenMarkdownLinks: 'warn'` — any link edit inside `website/docs/` must stay valid or the Pages build fails. The `CHANGELOG_ARCHIVE.md` fix is in root files, outside the Docusaurus tree.
- Editing `website/**` on `main` triggers `deploy-docs.yml`; it will fail on the fork until Pages is enabled with source "GitHub Actions" (manual step).
- A docs build was not run (it would write `node_modules`/`build` into the repo). If the planner wants a build check, run it in a copy of `website/` under a scratch dir.

## `.gitignore` (current → needed)

Current (7 lines, read this session): `__pycache__/`, `*.pyc`, `.pytest_cache/`, `node_modules/`, `.DS_Store`, `*.zip`.

Add (D-10): `.env`, `*.bak*`, `family_hub_backups/`, `.storage/`, `dev/.ha-*`. Notes: `.env` matches only a file named exactly `.env`, so a repo-root `versions.env` is **not** ignored; `*.bak*` matches the tracked `….js.bak_divfix`, which is fine only because that file is being deleted in the same phase (an ignore rule never untracks a tracked file); the pyc untracking is separate: 49 tracked files (25 `cpython-310`, 24 `cpython-314`), `git rm -r --cached -n custom_components/family_hub/__pycache__` listed 49 [VERIFIED]. No other tracked `.bak`, `.DS_Store`, `.zip`, `.env`, `.orig`.

## Architecture Patterns

### Recommended plan/commit sequence (satisfies D-24, D-04, D-02)

```
0 (docs)   01-TRIAGE.md written first, from read-only checks          -> auditable record before any deletion
1 chore    git rm -r --cached __pycache__  (49 files)  [own commit, D-10]
2 chore    delete 14 root *.js + card/*.js.bak_divfix  [own commit(s); ported hunks: none expected, D-04]
3 chore    git mv it/nl/pl/pt/pt-BR.json -> translations/
4 chore    delete root de/en/es/fr.json + strings.json
5 chore    hygiene: git rm -r -- ':(literal)\Screenshots'; icon (1).png, icon@2x.png, logo.png, logo@2x.png; readme.md; .gitignore additions
6 chore    identity: manifest.json (3 values), README, website config/docs, CHANGELOG_ARCHIVE link, credit line
7 chore    version + hacs.json + versions.env + PROJECT.md/CLAUDE.md constraint + Key Decisions
8 ci       .github/workflows/validate.yml
9 docs     01-VALIDATION-BASELINE.md after the run
```
`.gitignore` can sit in commit 1 or 5; if it goes in commit 5, make sure `git rm --cached` in commit 1 does not leave pyc re-added by an editor (pyc are already ignored today, so safe either way).

### `manifest.json` target (keep existing key order so the baseline stays honest; Phase 3 sorts it)
```json
{
  "domain": "family_hub",
  "name": "Family Hub",
  "codeowners": ["@Future-Bridge-AI"],
  "config_flow": true,
  "dependencies": ["frontend", "http", "lovelace", "file_upload", "image_upload"],
  "after_dependencies": ["timer"],
  "documentation": "https://github.com/Future-Bridge-AI/HA-Family-Hub",
  "issue_tracker": "https://github.com/Future-Bridge-AI/HA-Family-Hub/issues",
  "iot_class": "local_polling",
  "version": "1.169.0"
}
```
Current values quoted from the file read this session: `"codeowners": ["@bordello_labs"]`, `"version": "1.168.85"`, `"iot_class": "local_polling"`. Keep the file's existing formatting/indent (one list item per line); only the four values change.

### `hacs.json` target
Current: `{"name": "Family Hub", "render_readme": true, "homeassistant": "2024.1.0"}`. Target: `"homeassistant": "2024.12.0"`. Valid per HACS schema (string) [VERIFIED: `utils/validate.py` `HACS_MANIFEST_JSON_SCHEMA`: `vol.Optional("homeassistant"): str`, `vol.Optional("render_readme"): bool`, `vol.Required("name"): str`].

### `versions.env` suggestion
```
# Single source of truth for Dev, Preview and tests (read by Phase 2/3 tooling)
HA_VERSION=2026.10.4
PYTHON_VERSION=3.14
PYTEST_HACC_VERSION=0.13.375
HA_MIN_VERSION=2024.12.0
```
`HA_MIN_VERSION` is informational (must match `hacs.json`); Phase 3 CI-04 can assert they agree.

### Anti-Patterns to Avoid
- **Porting root hunks because the root file "has newer upload date".** Upload date is not content age; root files carry older version tags. Port nothing unless a hunk is both absent and demonstrably newer than the served file's version tags.
- **Reordering `manifest.json` keys now.** It hides the first-run failure D-22 wants recorded.
- **Adding `continue-on-error` to hassfest/HACS jobs** (D-22). The workflow is non-blocking because it is not a required check, not because errors are swallowed.
- **Running the integration (`python -c "import custom_components…"`, `py_compile`, `pytest`) inside the repo.** It regenerates tracked `.pyc`. Use `ast.parse` from stdin, or work on copies.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HACS compliance check | A custom script re-implementing HACS rules | `hacs/action` | Rules change (license check was added recently); the official action tracks them |
| Manifest/translation validation | Ad-hoc JSON schema | HA's own hassfest (action or local script as above) | Same schema HA uses; custom integration rules differ from core rules |
| Key-parity check | Hand-diffing JSON | A 10-line flatten-and-compare run from stdin (Phase 3 turns it into CI-04) | Nested `fh_ui` makes plain `diff` useless |
| Removing a backslash-named directory | `rm -rf \\Screenshots` or manual renames | `git rm -r -- ':(literal)\Screenshots'` | Verified to match all 15; shell-quoting accidents can delete the wrong thing |

**Key insight:** every deletion here is verifiable from git itself (blob hashes, `git log`), so the triage record should be generated from those commands, not from eyeballing.

## Runtime State Inventory

This phase is a rebrand/refactor of repo metadata, so each category is answered explicitly.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None for this phase — no key, collection or storage-name contains `JVarhol`/`bordello`; HA storage keys and `family_hub_backups/` are keyed on `family_hub`, which D-17 keeps. Verified by grep of `custom_components/**/*.py` (no `jvarhol`/`bordello` hit; the only code hit is a JS comment, `family-week-calendar-card.js:18080`) | none |
| Live service config | Home's HACS has the **upstream** repo registered as a custom repository (outside git). Home currently has upstream v1.168.85 installed | Switch is Phase 4 REL-02 (after full HA backup) — do not do it in Phase 1. Upstream's Decap CMS `turbo_site_id` in `website/static/admin/config.yml` is upstream-owned config | none now; note in baseline doc |
| OS-registered state | None — nothing in the repo registers tasks/services; verified by grep for `systemd`, `launchd`, `schtasks`: no files exist for them | none |
| Secrets and env vars | None — the integration reads no env vars; `.env` is only being added to `.gitignore` | none |
| Build artifacts / installed packages | Tracked `__pycache__` (49 files) — the only build artifact in git. A local `custom_components/family_hub/__pycache__/` directory also exists on disk and stays (ignored) after `git rm --cached` | untrack only; do not delete from disk |

Canonical question — after every file is updated, what still has the old identity? Home's HACS custom-repository entry and the GitHub-side repo settings (Issues, topics, Pages). Both are manual and listed above.

## Common Pitfalls

### Pitfall 1: Pathspec with a leading backslash
**What goes wrong:** `git rm -r \Screenshots` is processed by the shell first (`\S` → `S`) and matches nothing or the wrong thing.
**How to avoid:** single-quote and use `:(literal)`: `git rm -r -- ':(literal)\Screenshots'`. Run `-n` first and expect exactly 15 `rm` lines.
**Warning signs:** `pathspec … did not match any files`; `git ls-files` shows the path as `"\\Screenshots/…"` (that is only display quoting).

### Pitfall 2: Raising `hacs.json` to the test version
**What goes wrong:** HACS refuses to download on any HA below the declared minimum; the family's Home could be blocked from updating.
**How to avoid:** `2024.12.0` per the API table; keep the pinned `2026.10.4` only in `versions.env`.

### Pitfall 3: Setting the floor at 2024.7 because `StaticPathConfig` is the famous one
**What goes wrong:** on 2024.7-2024.11, the integration fails at import (`DATA_COMPONENT`) or the options flow crashes (`self.config_entry`).
**How to avoid:** use 2024.12.0.

### Pitfall 4: Duplicate icon deletion removes the served icon
**What goes wrong:** `ICON_URL = "/family_hub_static/icon.png"` is served from root `icon.png` (`__init__.py:12550` `icon_path = f"{integration_dir}/icon.png"`; guarded by `os.path.isfile`, so deletion would fail silently — no icon in the sidebar panel).
**How to avoid:** delete exactly `icon (1).png`, `icon@2x.png`, `logo.png`, `logo@2x.png` (quote the one with a space and parentheses). All five root image files plus `brand/*` hash to two values: `aa5ee4ba0f0ab23d340b571eb2dc3ad9` (icon.png, icon (1).png, logo.png, brand/icon.png, brand/logo.png) and `5e65843d4f1702790a578ec995f858ca` (icon@2x.png, logo@2x.png, brand/icon@2x.png, brand/logo@2x.png) [VERIFIED: md5sum]. Success criterion 3 ("no duplicate icon files") is satisfied by the one allowed pair root `icon.png` (served) ↔ `brand/icon.png` (HACS brand check); state that exception in the verification.

### Pitfall 5: README images break or keep depending on upstream
**What goes wrong:** the 14 absolute `raw.githubusercontent.com/JVarhol/…` image URLs keep working (upstream's copies) so nobody notices; or, after rewriting to the fork, they 404 until the branch is merged to `main`.
**How to avoid:** rewrite them; verify with the grep in Verification Commands; accept that images show only on `main`.

### Pitfall 6: Treating the manifest `version` as the HACS update signal
See Versioning. A tag without a GitHub Release does nothing for HACS.

### Pitfall 7: Hosted hassfest differs from the local run
The action uses an unpinned docker image. Record the local result as "predicted" and the hosted result as authoritative; diff them in the baseline doc.

## Code Examples

### Verification: parity of nine languages (read-only)
```python
# run as: python3 -B -I - < script   (no bytecode, no repo writes)
import json, pathlib
def flat(d, p=""):
    return {k2: v2 for k, v in d.items() for k2, v2 in (flat(v, f"{p}{k}.") if isinstance(v, dict) else {f"{p}{k}": v}).items()}
base = pathlib.Path("custom_components/family_hub/translations")
en = flat(json.loads((base / "en.json").read_text(encoding="utf-8")))
for lang in ["de","en","es","fr","it","nl","pl","pt","pt-BR"]:
    t = flat(json.loads((base / f"{lang}.json").read_text(encoding="utf-8")))
    assert set(t) == set(en) and len(t) == 2139, lang
```

### Verification: success criteria checks (copy-paste for the plan's verify steps)
```bash
# SC1 – nothing at root except manifest.json; no bak
git ls-files custom_components/family_hub | grep -E '^custom_components/family_hub/[^/]+\.(js|json)$'    # expect only .../manifest.json
git ls-files | grep -E 'bak_'                                                                           # expect empty
# SC3 – hygiene
git ls-files | grep -cE '\.pyc$|__pycache__'                                                            # expect 0
git ls-files | grep -c 'Screenshots'                                                                    # expect 0
git ls-files custom_components/family_hub | grep -E 'readme.md|icon \(1\)|logo|icon@2x'                 # expect empty (brand/ copies live under brand/)
git check-ignore -v .env x.bak1 family_hub_backups/ .storage/ | wc -l                                  # expect 4
# SC4 – identity: remaining upstream mentions must all be on the "keep" list
grep -rIniE 'jvarhol|bordello' . --exclude-dir=.git --exclude-dir=.planning --exclude-dir=.claude --exclude-dir=node_modules --exclude=package-lock.json
git diff --stat HEAD~N -- custom_components/family_hub/const.py custom_components/family_hub/__init__.py     # expect empty (no domain/service/ws/tag change)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `hass.http.register_static_path` | `await hass.http.async_register_static_paths([StaticPathConfig(...)])` | 2024.7 | Already adopted; sets floor ≥ 2024.7 |
| `OptionsFlow.__init__(config_entry)` + `self.config_entry = …` | framework-provided read-only `self.config_entry` | 2024.12 (explicit set removed after 2025.12) | Already adopted; sets floor 2024.12 |
| `hass.data["calendar"]` | `hass.data[DATA_COMPONENT]` (`HassKey`) | 2024.10 | Already adopted; sets floor ≥ 2024.10 |
| voluptuous | probatio, with `voluptuous` aliased in `sys.modules` | core 2026.9 | No change needed for custom integrations; error wording differs |
| Custom-integration brand images via brands repo | `custom_components/<domain>/brand/` local images (HA 2026.3+) | 2026.3 | Already satisfied; HACS `brands` check looks for `brand/icon.png` |

**Deprecated/outdated:** nothing in the integration hits a removed API as of 2026.10.4.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Forks have Actions disabled until the owner enables them | Validation workflow | Baseline run silently does not happen; developer sees no runs. Low, easy to check |
| A2 | `AwesomeVersion` treats `v1.169.0` as newer than `1.168.85` | Versioning | If tag format breaks comparison, HACS shows an update inconsistently; check in Phase 4 (REL-01) before the first release |
| A3 | The hosted hassfest image is newer than 2026.10.4 and may add checks beyond the local run | Validation workflow | Baseline list gets extra rows; harmless, just record them |
| A4 | Home HA already runs ≥ 2024.12 (because upstream 1.168.85 cannot run its options flow on older HA) | Minimum HA | If Home is older, Home is already partly broken; the floor is still correct |
| A5 | Release date of HA 2024.12.0 is early December 2024 (not needed by any decision) | Minimum HA | None |
| A6 | Floor = 2024.12.0 is the maximum over *imported* APIs; no behaviour-only dependency (entity/registry semantics, frontend message formats) raises it further | Minimum HA | Integration might misbehave on 2024.12-2025.x in an untested path; mitigated by Home already running something recent and Phase 3 CI testing only 2026.10.4 |

## Open Questions

1. **What HA version does Home run today?**
   - Known: upstream v1.168.85 (currently installed) needs ≥ 2024.12 for its options flow, so Home is probably ≥ 2024.12.
   - Unclear: the exact version. If it is ≥ 2025.x, the floor could be raised later for free.
   - Recommendation: planner adds a one-line check to the developer's manual steps (Settings → About) and records it in PROJECT.md; do not block Phase 1.

2. **What tag format does upstream use for releases (`1.168.85` vs `v1.168.85`)?**
   - Known: fork has no releases; `git tag` is empty locally; D-19 chooses `vX.Y.Z`. HACS compares with AwesomeVersion.
   - Unclear: whether Home's HACS stored the installed version as `v…` or bare; matters at REL-02.
   - Recommendation: defer to Phase 4; read Home's HACS "installed version" then.

3. **LICENSE header vs HACS license check (D-16 conflict).**
   - Known: GitHub reports `NOASSERTION` for the fork; HACS fails on it; cause is the custom header/footer in `LICENSE`.
   - Unclear: developer's preference — keep the Bordello Labs notice inside `LICENSE` or move it out so GitHub recognises GPL-3.0.
   - Recommendation: Phase 1 records the failure only; ask the developer in Phase 3 before touching `LICENSE`.

4. **Does the developer want the README "release" badge pointing at a repo with zero releases?**
   - Recommendation: still point it at the fork per D-15; it will read "no releases" until Phase 4. Acceptable.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| git | all commits | ✓ | present | — |
| python3 | stdin verification scripts | ✓ | 3.13.17 | — |
| uv + Python 3.14 | local hassfest reproduction, Phase 3 | ✓ | uv present; `cpython-3.14.9` installed | — (also resolves STATE.md's "confirm `uv` provides 3.14") |
| Network to PyPI / raw.githubusercontent.com / hacs.xyz | version checks, reproduction | ✓ | — | — |
| `gh` CLI with access to the fork | trigger/read hosted validation run | ✗ | installed, but this session has no repo access | developer pushes the branch and reads the Actions run; use local reproduction meanwhile |
| Node/npm | docs build (not required) | ✓ node 22 | — | skip; do not build inside the repo |
| Docker | not needed in Phase 1 | not checked | — | — |

**Missing dependencies with no fallback:** none blocks writing the files.
**Missing dependencies with fallback:** hosted validation run — needs developer action (push, enable Actions, paste results).

## Security Domain

`security_enforcement` is enabled (ASVS level 1). This phase changes metadata and CI only.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | yes (CI token scope) | workflow-level `permissions: {}`, job-level `contents: read` only where checkout needs it |
| V5 Input Validation | no (no new input) | — |
| V6 Cryptography | no | — |
| V14 Configuration / supply chain | yes | see below |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Floating action ref (`hacs/action@main`, `hassfest@master`) pulls changed code on each run | Tampering | Accepted by D-22 for the baseline (both are first-party org actions, docs-prescribed). In Phase 3 pin to full commit SHAs and add Dependabot `github-actions` updates |
| Over-privileged `GITHUB_TOKEN` | Elevation of privilege | `permissions: {}` at workflow level; only the hassfest job gets `contents: read` |
| `pull_request_target` or secrets in a validation workflow | Elevation of privilege | Do not use; the workflow needs no secrets |
| Committing secrets/backups | Information disclosure | `.gitignore` adds `.env`, `family_hub_backups/`, `.storage/` (backups contain family data — restore source in `store.py`) |
| Third-party-looking identity strings | Spoofing | Codeowner `@Future-Bridge-AI` is the authenticated owner login (per D-14) |
| Local reproduction pulling code | Tampering | Done in a scratch venv outside the repo from pinned `homeassistant==2026.10.4` and a tag checkout; nothing from it is committed |

## Project Constraints (from CLAUDE.md)

`./.claude/CLAUDE.md` (generated from PROJECT.md) directives that apply:
- **License:** GPLv3, keep upstream credit — fork stays a derivative work.
- **Platform:** HA custom integration, HACS custom repository; the "HA >= 2024.1" wording is what D-21 updates (to 2024.12.0).
- **Tech stack:** no extra Python deps, vanilla JS, no bundler — nothing here adds any.
- **Served paths:** only `card/` and `panel/` JS is served; edits target those copies — consistent with deleting root copies.
- **Code health / no `.bak_*`** (`.planning/codebase/CONVENTIONS.md`): do not create backup files; `.gitignore` gets `*.bak*`.
- Do not run Python that imports the integration in-repo (regenerates tracked `.pyc` until commit 1 lands; even after, avoid committing new bytecode).
- `workflow.nyquist_validation` is `false` in `.planning/config.json`: no Validation Architecture section; the Verification Commands above stand in for it.
- `.claude/CLAUDE.md` mirrors PROJECT.md text; after PROJECT.md changes, update the mirrored lines (26, 53, 100) or regenerate with the GSD tool.

## Sources

### Primary (HIGH confidence — read this session)
- Repo files: `custom_components/family_hub/{manifest.json, config_flow.py, __init__.py, device_trigger.py, const.py, todo.py, switch.py}`, `hacs.json`, `.gitignore`, `README.md`, `CHANGELOG.md`, `website/docusaurus.config.js`, `website/static/admin/config.yml`, `.github/workflows/deploy-docs.yml`, `LICENSE`, git history (`8f7172d`, `74bb966`, blob-hash comparisons)
- HA core source at tags 2023.11.0, 2024.6.4, 2024.7.0, 2024.9.1-.3, 2024.10.0(b0), 2024.11.0/.3, 2024.12.0(b0), 2026.10.4 via raw.githubusercontent.com/home-assistant/core (http, calendar, config_entries, panel_custom, frontend, file_upload, helpers/trigger, helpers/start, helpers/entity, triggers/event, `homeassistant/__init__.py`, `script/hassfest/*`, `script/util.py`, `package_constraints.txt`, `pyproject.toml`)
- hacs/integration source (`validate/*.py`, `utils/validate.py`, `utils/version.py`, `repositories/base.py`) and `hacs/action` `action.yml` via raw.githubusercontent.com
- PyPI JSON for `homeassistant` and `pytest-homeassistant-custom-component`
- api.github.com metadata for `Future-Bridge-AI/HA-Family-Hub` (description, topics, has_issues, license, releases)
- Local run of HA 2026.10.4 hassfest on scratch copies

### Secondary (MEDIUM confidence — official docs fetched)
- https://hacs.xyz/docs/publish/action/ — workflow shape, inputs, checks
- https://hacs.xyz/docs/publish/start/ — hacs.json keys, version detection
- https://hacs.xyz/docs/publish/integration/ — manifest keys, brand assets
- https://github.com/home-assistant/actions — hassfest workflow
- https://contributors.home-assistant.io/blog/2026/09/30/probatio-validation-engine — probatio alias
- https://contributors.home-assistant.io/blog/2024/11/12/options-flow — options flow `config_entry` (surfaced via search; the source diff at 2024.11.3 vs 2024.12.0b0 is the authoritative evidence)

### Tertiary (LOW confidence)
- None relied on.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — official actions, docs-prescribed
- Minimum HA: HIGH for the 3 binding constraints (source-verified at tags); MEDIUM that no behavioural dependency raises it
- Architecture / commit plan: HIGH — every command dry-run or read-only verified
- Validation baseline: HIGH for hassfest (reproduced) and the 3 HACS repo-settings failures (live API); MEDIUM for hosted-run parity
- Pitfalls: HIGH

**Research date:** 2026-10-26
**Valid until:** 2026-11-09 (14 days — HA ships monthly and hassfest/HACS rules change; re-check the pin if a 2026.11.x release lands before execution)
