# Phase 2: Dev + Family Preview - Pattern Map

**Mapped:** 2026-11-02
**Files analyzed:** 27 new/modified (2 card edits, 1 backend read-only reference, the rest new tooling/docs)
**Analogs found:** 4 in-repo analogs + RESEARCH.md sections for everything else / 27

Phase 2 is almost entirely new tooling. The repo has no `dev/`, `scripts/`, `tools/` or `tests/` directory, no `.gitattributes`, and only `docs/onboarding-findings.md` under `docs/`. For those files the pattern source is a **02-RESEARCH.md section**, not a forced weak analog. In-repo analogs exist only for the two card edits, the `?v=` hash behaviour, and the Phase 1 config files.

All analog paths below were verified as git-tracked (`git ls-files`): `custom_components/family_hub/card/family-week-calendar-card.js` and `custom_components/family_hub/__init__.py` are tracked. Only `card/` JS is served, so card edits target the `card/` copy only.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `custom_components/family_hub/card/family-week-calendar-card.js` (S3 build stamp) | component | request-response (render) | same file: `<ha-card>` template end (L16077) + `FAMILY_HUB_SHARED_STYLE_BLOCK` (L3604) | exact (self) |
| `custom_components/family_hub/card/family-week-calendar-card.js` (S4 loud delete confirm) | component | request-response | same file: `_wireEventInfoDeleteButton` (L23683-23717), `_getCalendarDeleteSupport` (L13249) | exact (self) |
| `dev/compose.yaml`, `dev/compose.dev.yaml`, `dev/compose.preview.yaml` | config | n/a | none in repo; RESEARCH Pattern 1 | no in-repo analog |
| `dev/config-template/configuration.yaml` | config | n/a | none; RESEARCH Pattern 2 | no in-repo analog |
| `dev/host.env.example` | config | n/a | `versions.env` (Phase 1) | role-match |
| `.gitignore` (add `dev/host.env`, `tools/seed/*.local.*`, backups) | config | n/a | existing `.gitignore` (`dev/.ha-*`) | exact |
| `.gitattributes` (new) | config | n/a | none; RESEARCH Pitfall 8 | no in-repo analog |
| `scripts/doctor` | utility | batch (checks) | none; RESEARCH Host layer "doctor checks" | no in-repo analog |
| `scripts/dev-up`, `dev-reset`, `dev-cards`, `deploy-preview`, `reset-preview`, `refresh-preview`, `make-certs`, `preview-down` | utility | batch / file-I/O | none; RESEARCH Architecture diagram, Pitfalls 9, 12; `_file_content_hash` for `dev-cards` | no in-repo analog |
| `tools/seed/client.py`, `onboard.py`, `users.py`, `entries.py`, `dashboard.py`, `verify.py`, `cli.py` | service | request-response (HA REST/WS) | none; RESEARCH Pattern 3, 4, 7, 8, Code Examples | no in-repo analog |
| `tools/seed/family_hub.py` | service | request-response (WS) | backend command schemas in `chores_websocket_api.py` (read-only reference) | partial |
| `tools/seed/google.py`, `calendar_tags.py` | service / utility | CRUD + transform | none; RESEARCH Pattern 5 (D-11 matcher) | no in-repo analog |
| `tools/seed/data/family.example.yaml` | config | n/a | none; UI-SPEC S5 (invented family) | no in-repo analog |
| `tools/seed/tests/*` | test | transform | none (repo has no tests); RESEARCH Pattern 5.6 test spec | no in-repo analog |
| `docs/family/getting-started.md`, `docs/family/img/*` | docs | n/a | none; UI-SPEC S7 (headings, voice, vocab) | no in-repo analog |
| `.planning/ROADMAP.md`, `PROJECT.md`, `REQUIREMENTS.md` wording edits | docs | n/a | n/a, edit per D-03/D-07/D-28 | n/a |

## Pattern Assignments

### `card/family-week-calendar-card.js` - S3 build stamp (component, render)

**Analog:** same file. Edit target is `custom_components/family_hub/card/family-week-calendar-card.js` only.

**Insertion point for the footer** (L16074-16079). The single `</ha-card>` at L16077 closes the card; the FAB follows it. The stamp row goes inside the card root but outside any modal, as a non-scrolling flex row. Do not put it after the `.add-event-fab` or inside the add-event modal that ends at L16076:
```html
<div class="modal-actions">
<button class="btn-cancel add-event-cancel" data-i18n="common.cancel">Cancel</button>
<button class="btn-save add-event-save" data-i18n="common.save">Save</button>
</div>
</div>
</div>
</ha-card>
<button data-fh-title="text.add" class="add-event-fab" ...>&#65291;</button>
```
Planner note: the visible calendar grid scrolls internally and the host is height-clamped (`:host` at L3606, `:host { height: auto !important ... }` override at L4567), so the stamp row must be `flex: 0 0 auto` outside the scroll area. Verify the real container structure when editing; this map did not trace the grid wrapper.

**Style block pattern:** CSS lives in template strings such as `FAMILY_HUB_SHARED_STYLE_BLOCK` (L3604) using `--fc-*` variables. The FAB shows the existing style (L3926): `right: 18px`, `width: 56px`. UI-SPEC fixes stamp padding at `4px 96px 8px 16px`, 12px, `color: var(--fc-text)`, no hex colours.

**Token constant:** add near the top of the file, after the `__fhI18n` bootstrap (L47), a block per RESEARCH Pattern 6:
```js
const __FH_BUILD = { env: "__FH_BUILD_ENV__", version: "__FH_BUILD_VERSION__", deployed: "__FH_BUILD_TIME__" };
```
Render rules from UI-SPEC S3: `Preview · <ver> · <time>` after substitution, `Dev · live` when tokens are literal AND `hass.config.location_name` matches `/\b(DEV)\b/`, and render nothing otherwise. One `console.info` with the same text (project rule: no other `console.log`). English literal, no `_t()`/translation keys. Style conventions: double quotes, semicolons, tokens must not be altered by `deploy-preview` anywhere except the exported copy.

### `card/family-week-calendar-card.js` - S4 loud delete confirm (component, request-response)

**Analog:** same file, `_wireEventInfoDeleteButton` (L23683-23717).

**Hook point: existing first confirm** (L23683-23693), to be kept unchanged:
```js
btn.addEventListener("click", async () => {
if (
!window.confirm(
this._t(
"event_info.delete_confirm",
`Delete "${detail.summary}"? This can't be undone here - it removes the event from ${detail.personName}'s calendar.`,
{ summary: detail.summary, person: detail.personName }
)
)
)
return;
btn.disabled = true;
```
Add the second `window.confirm` (UI-SPEC S4 copy) directly after the `return;` and before `btn.disabled = true;`. It must only fire when (1) `this._hass.config.location_name` matches `/\b(PREVIEW|DEV)\b/`, (2) `support.platform === "google"`, (3) `detail.summary` does not start with `[PREVIEW] ` or `[DEV] `. `support` is already in scope here (the surrounding function reads it at L23637 via `this._getCalendarDeleteSupport(detail.calendarEntity)`). Failure path stays the existing `window.alert` (L23703-23709).

**Pass `platform` through** (L13260-13272, `_getCalendarDeleteSupport`). The backend already sends it: `_ws_get_calendar_delete_support` in `__init__.py` returns `"platform": platform` in `connection.send_result` (L3764+, around the `"platform": platform,` line). Only the card drops it today. One added property:
```js
result = {
supported: !!res.supported,
updateSupported: !!res.update_supported,
createSupported: !!res.create_supported,
integrationName: res.integration_name || "your calendar's own app",
// add: platform: res.platform || null,
known: !!res && Object.prototype.hasOwnProperty.call(res, "create_supported") && !res.unavailable,
_at: Date.now(),
};
```
No backend change is needed, which respects the "prefer small, additive edits to monoliths" constraint. Other callers of `window.confirm` in this file (e.g. L23505, L23081) show the same inline-native-confirm style; do not build a custom modal.

---

### `dev/host.env.example` (config)

**Analog:** `/home/user/HA-Family-Hub/versions.env` (tracked, Phase 1).

Style to copy: a header comment naming the consumers and a short rationale per key, plain `KEY=value` lines, no quoting:
```
# Single source of truth for Dev, Preview and tests (read by Phase 2 and Phase 3 tooling).
# HA_VERSION is the homeassistant version pytest-homeassistant-custom-component 0.13.375 pins (needs Python 3.14).
HA_VERSION=2026.10.4
```
`dev/host.env.example` is committed with placeholders; the real `dev/host.env` is gitignored. Keys per RESEARCH: `TZ`, country, currency, units, lat/long, elevation, language, `PREVIEW_HOST_IP`, `PREVIEW_BIND`, `HA_CONFIG_DIR`. Compose reads it as `--env-file versions.env --env-file dev/host.env` (RESEARCH Pattern 1). Do not duplicate `HA_VERSION` here.

### `.gitignore` (config)

**Analog:** current `.gitignore` already contains `dev/.ha-*`, `.env`, `*.bak*`, `family_hub_backups/`, `.storage/`. Append (do not reorder):
```
dev/host.env
tools/seed/*.local.*
```
`dev/.ha-*` already covers `.ha-dev/ .ha-preview/ .ha-certs/ .ha-secrets/ .ha-backups/` if the `.ics` backups and secrets are kept there (RESEARCH structure). Note `.env` alone does not cover `dev/host.env`.

### `.gitattributes` (new, config)

No in-repo analog (none exists). Source: RESEARCH "Recommended Project Structure" and Pitfall 8: `*.sh text eol=lf`, `scripts/* text eol=lf`, `*.yaml text eol=lf`.

### `.github/workflows/validate.yml` (reference only, not planned for edit)

Phase 1 analog if a lint/test job for `tools/seed/tests` is later wanted. Conventions seen: `permissions: {}` at top, per-job `permissions: contents: read`, `actions/checkout@v4`, `on: push/pull_request/workflow_dispatch`, header comment citing sources. Phase 2 does not require CI changes (seed tests are run locally); if the planner adds one, keep it non-blocking like the existing jobs.

---

### `dev/compose*.yaml`, `dev/config-template/configuration.yaml` (config)

**No in-repo analog.** Pattern source: 02-RESEARCH.md "Pattern 1: Compose base + per-environment overlay" (full sketch of base/dev/preview overlays) and "Pattern 2: Minimal configuration.yaml (not default_config)". Key constraints to carry: image `ghcr.io/home-assistant/home-assistant:${HA_VERSION:?}`, `PYTHONDONTWRITEBYTECODE=1`, Dev binds `127.0.0.1:8130`, Preview `${PREVIEW_BIND:-0.0.0.0}:8124`, `restart: unless-stopped` on Preview, Dev mounts `custom_components/family_hub` `:ro`, Preview mounts none (exported copy), no `server_port` under `http:`, `my:` and `mobile_app:` present.

### `scripts/*` (utility)

**No in-repo analog** (no shell scripts exist). Pattern sources in 02-RESEARCH.md:
- Orchestration order and backup-first rule: "System Architecture Diagram" (steps 1-5) and D-08.
- Wipe via helper container, keep `custom_components/`: Pitfall 9 (`docker run --rm -v ... busybox sh -c 'find /config -mindepth 1 -maxdepth 1 ! -name custom_components -exec rm -rf {} +'`). Must also remove `family_hub_backups/` because `store.py` `_maybe_restore_backup` restores from it.
- `scripts/doctor` check list: "Host layer" section, "`scripts/doctor` checks (D-23)".
- `scripts/dev-cards`: Pitfall 12. The hash must match the integration's own function (`__init__.py` L12172-12187):
```python
def _file_content_hash(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:10]
    except OSError:
        return "0"
```
`dev-cards` and `deploy-preview`'s served-hash check recompute `sha256(file)[:10]` and compare with the `?v=` of `lovelace/resources` (Pattern 4). `_register_dashboard_resource` (L12190) updates existing resources in place when the hash changes, so the seed must update, never duplicate.
- Terminal reset prompt and `--yes` flag copy: UI-SPEC "Destructive actions" paragraph. `deploy-preview` hand-off block: UI-SPEC S6.
- Project convention to follow: thin bash wrappers calling `tools/seed`, no laptop-specific paths, all host values from `dev/host.env` (D-04).

### `tools/seed/*.py` (service)

**No in-repo analog** for the HA REST/WS client, onboarding, users, entries, dashboard, sidebar and verify modules. Pattern sources in 02-RESEARCH.md, which has executed-and-verified request shapes:
- Ordered seed steps 1-12: "Pattern 3". Onboarding/login code: "Code Examples" (aiohttp, `ssl.SSLContext` from `ca.crt`, never `verify=False`).
- Dashboard + resource read-back: "Pattern 4"; her sidebar: "Pattern 7"; isolation asserts (refuse to run unless `location_name` matches target): "Pattern 8".
- Config-flow field names (`setup_features`, `member_calendar`, `add_dashboard`, ...): "Family Hub config flow, verbatim values" in Pattern 3.

**Python conventions to copy from the integration** (CLAUDE.md, applies to `tools/seed` even though it is outside the package): double quotes, `from __future__ import annotations` as first statement after the docstring, `_LOGGER = logging.getLogger(__name__)` with `%s` lazy formatting. The `print()` ban is for integration code; CLI output in `tools/` is allowed.

**`tools/seed/family_hub.py`** drives `family_hub/*` websocket commands. Schemas live in `chores_websocket_api.py` (cited with line numbers in RESEARCH Pattern 3, "Family Hub commands the seed uses": `chores/create` :904, `rewards/add_catalog_item` :1474, `rewards/adjust_balance` :1663, `goals/create` :2595, `routines/create` :2332, `kiosk/set_pin` :2165). Command registration convention to mirror in the client call shapes (not to copy):
```python
@websocket_api.websocket_command({vol.Required("type"): "family_hub/calendar/delete_support", vol.Required("entity_id"): str})
@websocket_api.async_response
```
Settings are full-replace: GET `family_hub/get_settings`, modify, then `family_hub/set_settings` (RESEARCH Pattern 3 step 11). Set `globalThemeId` to `midnight` (Preview) or `blossom` (Dev, UI-SPEC A1).

### `tools/seed/google.py`, `calendar_tags.py` (service / utility, highest risk)

**No in-repo analog.** Pattern source: 02-RESEARCH.md "Pattern 5: Google Calendar in a non-production instance", items 5-7 (disable non-chosen entities, week-anchored diff sync, delete only when ALL of: exact summary tag, exact description marker `family-hub-seed:<env>:<key>`, bounded date window, allow-listed calendar). `calendar_tags.matches()` must be a pure function; `--dry-run` is the default for the cleaner. Test cases listed in Pattern 5.6: tagged, untagged, other-env, tag-in-the-middle, marker missing, out-of-window. Tag strings fixed by UI-SPEC S5: `[PREVIEW] ` and `[DEV] ` with one trailing space.

### `tools/seed/tests/*` (test)

**No in-repo analog**: the repo has no tests (CLAUDE.md, `tests/` absent). Pattern source: RESEARCH Pattern 5.6 (pure-function suite) and Standard Stack (pip-installed `homeassistant==2026.10.4` in `.venv` for the one live Local Calendar run). Phase 3 will later introduce the repo's test conventions (pytest-homeassistant-custom-component per `versions.env`); keep these tests plain `pytest` to avoid pre-empting that.

### `docs/family/getting-started.md` (docs)

**No in-repo analog** (the only `docs/` file is `docs/onboarding-findings.md`, developer-facing). Pattern source: 02-UI-SPEC.md S7 and Copywriting Contract: fixed ten headings in exact order, fixed vocabulary table, banned jargon list, verbatim error-state paragraphs, screenshot naming (`01-calendar.png` ... `phone-01-...`), under 400 KB each, alt text plus caption. Android install/certificate wording must come from the real phone checkpoint (A8).

## Shared Patterns

### Cache-busting hash (single definition)
**Source:** `custom_components/family_hub/__init__.py` L12172-12187 (`_file_content_hash`); registration L12190+.
**Apply to:** `scripts/dev-cards`, `scripts/deploy-preview` served-hash verification, `tools/seed/dashboard.py` resource read-back. All must reproduce `sha256(file)[:10]` exactly.

### Environment identity words
**Source:** UI-SPEC S1 + RESEARCH Pattern 6.
**Apply to:** seed (`config/core/update` `location_name` = `Family Hub PREVIEW` / `Family Hub DEV`), dashboard title, S3 stamp, S4 gate (`/\b(PREVIEW|DEV)\b/`). Home's name must never contain either word.

### Target allow-list / refuse-before-credentials
**Source:** RESEARCH Pattern 8 (e) and Architecture diagram (`--target dev|preview`).
**Apply to:** every `tools/seed` entry point and every `scripts/*` that sends credentials.

### Backup-before-destructive-action
**Source:** D-08, D-30; RESEARCH Architecture diagram step (1).
**Apply to:** `deploy-preview`, `reset-preview`, `dev-reset`, `refresh-preview` (hard stop on empty/failed iCal fetch).

### Card editing rules
**Source:** CLAUDE.md "Served paths", "Code style (JS)".
**Apply to:** both card edits: edit `card/` copy only, double quotes and semicolons, no debug `console.log` (only the decided `console.info`), no new translation keys, no `.bak_*` files, keep changes additive in the monolith.

### Gitignored host-specific values
**Source:** `.gitignore` existing `dev/.ha-*`; `versions.env` as the committed counterpart.
**Apply to:** `dev/host.env`, `tools/seed/family.local.yaml` (real first names, secret iCal URLs, Google client id/secret). Committed `*.example` files carry invented data only (Sam, Jordan, Riley, Casey, UI-SPEC S5).

## No Analog Found

| File | Role | Data Flow | Reason / Pattern source |
|------|------|-----------|-------------------------|
| `dev/compose*.yaml`, `dev/config-template/configuration.yaml` | config | n/a | No Docker/Compose files exist; RESEARCH Patterns 1-2 |
| `scripts/*` | utility | batch | No shell scripts exist; RESEARCH architecture diagram, Host layer, Pitfalls 9/12 |
| `tools/seed/*` (client, onboard, users, entries, dashboard, verify, cli, google, calendar_tags) | service | request-response / CRUD | No external-API tooling exists; RESEARCH Patterns 3-5, 7-8, Code Examples |
| `tools/seed/tests/*` | test | transform | Repo has no tests; RESEARCH Pattern 5.6 |
| `tools/seed/data/family.example.yaml` | config | n/a | UI-SPEC S5 defines content; schema is the planner's to define |
| `.gitattributes` | config | n/a | None exists; RESEARCH Pitfall 8 |
| `docs/family/*` | docs | n/a | UI-SPEC S7 + Copywriting Contract |

## Metadata

**Analog search scope:** `custom_components/family_hub/card/family-week-calendar-card.js`, `custom_components/family_hub/__init__.py`, repo root (`versions.env`, `.gitignore`, `.github/workflows/validate.yml`), `docs/`, `.planning/phases/01-clean-foundation/`
**Files scanned:** about 10 (targeted reads, large files via grep plus offset reads)
**Pattern extraction date:** 2026-11-02
**Unread:** 02-RESEARCH.md lines 506-725 (later sections, likely Validation/Assumptions/Open Questions) were not read; confirm nothing there adds files beyond those listed.
