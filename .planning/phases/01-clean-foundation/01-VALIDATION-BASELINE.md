# Phase 1 Validation Baseline (FOUND-09)

- **Date:** 2026-10-26
- **Branch:** `ccr-ab9176f1-jbs2rg`
- **HEAD when the local run was taken:** `c2571b0`
- **Workflow:** `.github/workflows/validate.yml` (jobs `hacs` = "HACS validation" and `hassfest` = "hassfest")
- **Status:** the local result below is a working note (predicted). FOUND-09 is satisfied by the executed hosted run recorded under "Hosted run (authoritative)" (run 40422777272, both jobs executed, both concluded failure as expected).

Nothing in this file is fixed in Phase 1. Every failure is copied as the validator printed it. Fixing is Phase 3 (CI-03).

## Local reproduction (predicted)

Recipe (harness outside the repo at `$HOME/.cache/fh-hassfest`, nothing from it is committed):

- venv: `uv venv --python 3.14`, with exactly `homeassistant==2026.10.4`, `infrared-protocols==10.1.0`, `tqdm==4.70.1`
- core checkout: `git clone --depth 1 --branch 2026.10.4 home-assistant/core`; `homeassistant/const.py` shows MAJOR 2026, MINOR 10, PATCH "4"
- export of the index (leaves the repo's index untouched):
  `git ls-files -z custom_components/family_hub | xargs -0 git --work-tree="$W/tree" checkout-index --`
- run, from `$W/core`:
  `PYTHONDONTWRITEBYTECODE=1 "$W/venv/bin/python" -B -m script.hassfest --action validate --integration-path "$W/tree/custom_components/family_hub"`
- header printed: `Integrations: 1`, `Invalid integrations: 1`; exit status 1 (errors present)

Verbatim `* [ERROR]` and `* [WARNING]` lines (the long `fh_ui` dump is truncated after about 200 characters with an ellipsis; the two continuation lines belong to the second error):

```
* [ERROR] [MANIFEST] Manifest keys are not sorted correctly: domain, name, then alphabetical order
* [ERROR] [TRANSLATIONS] Invalid translations/en.json: not a valid option at 'fh_ui'. Got {'nav': {'legend_events': 'Events', 'legend_reminders': 'Reminders', 'meal_block_breakfast': 'Breakfast', 'meal_block_lunch': 'Lunch', 'meal_block_dinner': 'Din...
the string should not contain URLs, please use description placeholders instead at 'config.step.grocy.data.grocy_url'. Got 'Grocy URL (e.g. http://homeassistant.local:9192)'
the string should not contain URLs, please use description placeholders instead at 'options.step.grocy.data.grocy_url'. Got 'Grocy URL (e.g. http://homeassistant.local:9192)'
* [WARNING] [CONFIG_SCHEMA] Integrations which implement 'async_setup' or 'setup' must define either 'CONFIG_SCHEMA', 'PLATFORM_SCHEMA' or 'PLATFORM_SCHEMA_BASE'. If the integration has no configuration parameters, can only be set up from platforms or can only be set up from config entries, one of the helpers cv.empty_config_schema, cv.platform_only_config_schema or cv.config_entry_only_config_schema can be used.
```

Failure table, in validator order:

| ID | Check | Severity | Message | Phase 3 note |
|----|-------|----------|---------|--------------|
| HF-01 | MANIFEST | ERROR | Manifest keys are not sorted correctly: domain, name, then alphabetical order | Sort `manifest.json` keys: `domain`, `name`, then alphabetical |
| HF-02 | TRANSLATIONS | ERROR | Invalid translations/en.json: not a valid option at 'fh_ui' | Phase 3 decides whether to relocate `fh_ui`; D-09 kept it in Phase 1 |
| HF-03 | TRANSLATIONS | ERROR | the string should not contain URLs, please use description placeholders instead at 'config.step.grocy.data.grocy_url' | Use description placeholders |
| HF-04 | TRANSLATIONS | ERROR | the string should not contain URLs, please use description placeholders instead at 'options.step.grocy.data.grocy_url' | Use description placeholders |
| HF-W01 | CONFIG_SCHEMA | WARNING | Integrations which implement 'async_setup' or 'setup' must define either 'CONFIG_SCHEMA', 'PLATFORM_SCHEMA' or 'PLATFORM_SCHEMA_BASE' | Add `cv.config_entry_only_config_schema` |

The run printed no further error or warning line, so no extra IDs were assigned.

No `Invalid strings.json` error remains: `strings.json` was deleted in plan 01-07, and the run output contains no `strings.json` line.

## HACS checks (predicted)

`hacs/action` cannot run locally here. These predictions come from its validator rules (research, `hacs/integration` `custom_components/hacs/validate/`) and from the fork's live public metadata, read on 2026-10-26 with `curl -sS https://api.github.com/repos/Future-Bridge-AI/HA-Family-Hub`:

- `has_issues`: false
- `topics`: `[]`
- `license`: key `other`, spdx_id `NOASSERTION`
- `description`: "A Family hub and meal planning dashboard for home assistant like skylight tablets"
- `archived`: false; `fork`: true; parent repository: `JVarhol/HA-Family-Hub`; default branch `main`; `has_pages`: false

| Rule | Predicted result | Evidence |
|------|------------------|----------|
| archived | pass | live metadata: `archived` false |
| brands | pass | `custom_components/family_hub/brand/` holds icon.png, icon@2x.png, logo.png, logo@2x.png |
| description | pass | live metadata: description is set |
| hacsjson | pass | `hacs.json` in the root with `name`, `render_readme`, `homeassistant` (2024.12.0), all allowed keys |
| images | pass | `README.md` contains `<img` (18 occurrences) |
| information | pass | `README.md` is tracked in the root |
| integration_manifest | pass | `manifest.json` has `codeowners`, `documentation`, `domain`, `issue_tracker`, `name`, `version` |
| integration_categories | warning | HACS-W01: the validator warns when `categories` is absent; it does not fail the check |
| issues | FAIL | HACS-01: live metadata `has_issues` is false |
| topics | FAIL | HACS-02: live metadata `topics` is empty |
| license | FAIL | HACS-03: live metadata `license.spdx_id` is `NOASSERTION` |

Failure IDs:

| ID | Rule | Severity | Message (as the validator words it) | Phase 3 note |
|----|------|----------|-------------------------------------|--------------|
| HACS-01 | issues | FAIL | The repository does not have issues enabled | Enable Issues after the baseline run (manual step 2) |
| HACS-02 | topics | FAIL | The repository has no topics | Add topics after the baseline run (manual step 3) |
| HACS-03 | license | FAIL | The repository license could not be identified (SPDX: NOASSERTION) | GitHub does not detect GPL-3.0 because `LICENSE` starts and ends with a custom Bordello Labs notice. D-16 keeps `LICENSE` unchanged in Phase 1, so this is recorded only; the fix is the developer's Phase 3 call (manual step 6) |
| HACS-W01 | integration_categories | WARNING | `categories` not present | No action required for a pass |

The HACS messages above are the wording predicted from the validator source; the hosted run replaces them with the real text.

## Hosted run (authoritative)

Run: https://github.com/Future-Bridge-AI/HA-Family-Hub/actions/runs/40422777272

- **Workflow:** Validate (run number 8), event `push`, branch `ccr-ab9176f1-jbs2rg`
- **Date:** 2026-10-26 (created 23:53:19Z; hassfest finished 23:53:45Z, HACS finished 23:54:03Z)
- **Head commit:** `bd8de7a6cfed4b39c7e781e5d23a832103a7d2bf` (`docs(01-05): record predicted validation baseline`, an ancestor of this branch's HEAD)
- **Run conclusion:** failure (expected: the failures below are the baseline)
- **Source of every line below:** the public GitHub API, read without authentication on 2026-10-27: the run, its jobs and steps, the check-run annotations, and the job logs (the log endpoint answered HTTP 200 after redirect without credentials). The developer pasted no log lines. Only validator output lines and check names are copied here, never full logs.

Job hacs (HACS validation): failure
Job hassfest (hassfest): failure

Both validator steps executed: `Run hacs/action@main` finished with conclusion failure, and `Run home-assistant/actions/hassfest@master` finished with conclusion failure. Neither job was cancelled or skipped.

### hassfest (job 121921017600)

Header printed by the job: `Integrations: 1`, `Invalid integrations: 1`; step exit code 1. Verbatim validator lines:

```
* [ERROR] [MANIFEST] Manifest keys are not sorted correctly: domain, name, then alphabetical order
* [ERROR] [TRANSLATIONS] Invalid translations/en.json: not a valid option at 'fh_ui'. Got {'nav': {'legend_events': 'Events', 'legend_reminders': 'Reminders', 'meal_block_breakfast': 'Breakfast', 'meal_block_lunch': 'Lunch', 'meal_block_dinner': 'Dinner', 'tap_to_add_block': 'Tap to add %block%', 'settings': 'Settings', 'week': 'Week', 'week_view_title': 'Week view', 'month': 'Month', 'month_view_title': 'Month view', 'day': 'Day', 'switch_view_title': 'Switch view', 'label_today': 'Today', 'label_tomorrow': 'Tomorrow', 'label_yesterday': 'Yesterday', 'edit_meals_title': 'Rearrang...
the string should not contain URLs, please use description placeholders instead at 'config.step.grocy.data.grocy_url'. Got 'Grocy URL (e.g. http://homeassistant.local:9192)'
the string should not contain URLs, please use description placeholders instead at 'options.step.grocy.data.grocy_url'. Got 'Grocy URL (e.g. http://homeassistant.local:9192)'
* [WARNING] [CONFIG_SCHEMA] Integrations which implement 'async_setup' or 'setup' must define either 'CONFIG_SCHEMA', 'PLATFORM_SCHEMA' or 'PLATFORM_SCHEMA_BASE'. If the integration has no configuration parameters, can only be set up from platforms or can only be set up from config entries, one of the helpers cv.empty_config_schema, cv.platform_only_config_schema or cv.config_entry_only_config_schema can be used.
```

(The `fh_ui` dump is truncated after about 200 characters here and is cut at a similar point by the API annotation; the two URL lines belong to the second error, as in the local run.)

| ID | Check | Severity | Message | Status |
|----|-------|----------|---------|--------|
| HF-01 | MANIFEST | ERROR | Manifest keys are not sorted correctly: domain, name, then alphabetical order | same as predicted |
| HF-02 | TRANSLATIONS | ERROR | Invalid translations/en.json: not a valid option at 'fh_ui' | same as predicted |
| HF-03 | TRANSLATIONS | ERROR | the string should not contain URLs, please use description placeholders instead at 'config.step.grocy.data.grocy_url' | same as predicted |
| HF-04 | TRANSLATIONS | ERROR | the string should not contain URLs, please use description placeholders instead at 'options.step.grocy.data.grocy_url' | same as predicted |
| HF-W01 | CONFIG_SCHEMA | WARNING | Integrations which implement 'async_setup' or 'setup' must define either 'CONFIG_SCHEMA', 'PLATFORM_SCHEMA' or 'PLATFORM_SCHEMA_BASE' | same as predicted |

No further hassfest error or warning line was printed, so there is no hosted-only hassfest ID. No `strings.json` error appears.

### HACS (job 121921017510)

Header printed by the job: `Category: integration`, `Repository: Future-Bridge-AI/HA-Family-Hub@refs/heads/ccr-ab9176f1-jbs2rg`; final line `3/10 checks failed`. Verbatim validator lines:

```
 <Validation license> failed:  The repository license could not be identified (SPDX: NOASSERTION) (More info: https://hacs.xyz/docs/publish/include#check-license )
 <Integration Future-Bridge-AI/HA-Family-Hub> The integration manifest has no categories, see https://contributors.home-assistant.io/core/integrations/categories/
 <Validation issues> failed:  The repository does not have issues enabled (More info: https://hacs.xyz/docs/publish/include#check-repository )
 <Validation topics> failed:  The repository has no valid topics (More info: https://hacs.xyz/docs/publish/include#check-repository )
 <Integration Future-Bridge-AI/HA-Family-Hub> 3/10 checks failed
```

Validators that completed without a failure: integration_categories (with the warning above), information, description, brands, integration_manifest, archived, hacsjson.

| ID | Rule | Severity | Message | Status |
|----|------|----------|---------|--------|
| HACS-01 | issues | FAIL | The repository does not have issues enabled | same as predicted |
| HACS-02 | topics | FAIL | The repository has no valid topics | same as predicted (wording differs from the prediction) |
| HACS-03 | license | FAIL | The repository license could not be identified (SPDX: NOASSERTION) | same as predicted |
| HACS-W01 | integration_categories | WARNING | The integration manifest has no categories | same as predicted (wording differs from the prediction) |

No further HACS failure was reported, so there is no hosted-only HACS ID.

### Runner notices (not validator findings)

The API also lists two GitHub runner annotations. They are recorded for the Phase 3 action-pinning work (CI-03/CI-04) and carry no failure ID:

- hassfest job, warning: `Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4.`
- both jobs, notice: `The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026.`

## Differences (local vs hosted)

The hosted run (authoritative) and the local run (predicted) are kept in separate sections above. This table pairs them per ID.

| ID | Local (predicted) | Hosted (authoritative) | Difference |
|----|-------------------|------------------------|------------|
| HF-01 | error | error | same |
| HF-02 | error | error | same |
| HF-03 | error | error | same |
| HF-04 | error | error | same |
| HF-W01 | warning | warning | same |
| HACS-01 | fail | fail | same |
| HACS-02 | fail | fail | same (hosted wording: "The repository has no valid topics") |
| HACS-03 | fail | fail | same |
| HACS-W01 | warning | warning | same (hosted wording: "The integration manifest has no categories") |
| images rule | pass (predicted from README `<img` count) | not executed | predicted only: the hosted integration run lists ten validators and `images` is not one of them. It is not a failure either way |
| hosted-only IDs | none | none | 0 hosted-only failures |

Result: every predicted failure was reproduced by the hosted run and nothing new appeared. The unpinned hosted hassfest image added no check beyond HA 2026.10.4 on this date; this can still change, because the image is not pinned (see Out of scope notes).

## Manual repo-settings steps (D-23)

1. Enable Actions on the fork (needed for the baseline run): https://github.com/Future-Bridge-AI/HA-Family-Hub/actions, "I understand my workflows, go ahead and enable them".
2. After the baseline run only: enable Issues (Settings, General, Features).
3. Add topics, for example `home-assistant`, `hacs`, `homeassistant-integration`, `family-calendar`.
4. Confirm the repository description.
5. Settings, Pages, Source = GitHub Actions, so `deploy-docs.yml` can publish https://future-bridge-ai.github.io/HA-Family-Hub/.
6. Phase 3 decision: restore the canonical GPLv3 text in `LICENSE` and move the notice to README or a `NOTICE` file, so HACS-03 passes. This touches the license file, so it is the developer's call.
7. Home Assistant version on Home: there is no Home installation yet (the family has not set up Home Assistant; hardware is not chosen). Nothing to check now. When Home is installed (Phase 2 or later), install a Home Assistant release of at least 2024.12.0 (the minimum declared in `hacs.json`); the pinned Dev/Preview version is 2026.10.4.

## Out of scope notes

- `website/static/admin/config.yml` holds upstream's Decap CMS `turbo_site_id` and is not reconfigured.
- The floating action refs (`hacs/action@main`, `home-assistant/actions/hassfest@master`) are pinned to SHAs in Phase 3.
- The hosted hassfest docker image is unpinned and may add checks that HA 2026.10.4 does not have, so the hosted list can be longer than the local one.
- Making validation a required check, and the CI guards, are Phase 3 (CI-03, CI-04).
- Fixing any HF or HACS item is Phase 3.

## Phase 1 success-criteria sweep

All checks were run on 2026-10-26 at HEAD `c2571b0`, before this file was committed:

| Check | Result | Printed counts |
|-------|--------|----------------|
| Served-path contract: all 15 paths registered in `__init__.py` are tracked, no unregistered tracked `.js` | pass | `reg 15`, `contract missing []`, `unregistered_js []` |
| Nine-language parity: each of de, en, es, fr, it, nl, pl, pt, pt-BR in `translations/` has the same leaf keys as `en.json` and keeps `fh_ui` | pass | `en_keys 2139`, `parity bad []` |
| No tracked bytecode | pass | `.pyc` / `__pycache__` paths: 0 |
| No tracked `\Screenshots` path | pass | 0 |
| No tracked `.bak` file | pass | 0 |
| Only `manifest.json` left as a root-level `.js` or `.json` under `custom_components/family_hub/` | pass | 1 |
| Upstream-owner mentions limited to credit lines | pass | non-credit mentions 0; "based on" credit lines 2 |
| No runtime file changed against `bc7e90c` (Python, `services.yaml`, `LICENSE`, de/en/es/fr translations, icon, brand) | pass | `git diff --quiet` exit 0 |
| Served card/panel JS changed only by 01-TRIAGE.md ported-hunk port commits | pass | triage rows 14, served changed `[]`, foreign `[]`, unported `[]` (research expected none) |
| `versions.env` and `.github/workflows/validate.yml` present | pass | both present |
