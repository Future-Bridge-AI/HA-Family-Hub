---
phase: 02-dev-family-preview
plan: 01
subsystem: infra
tags: [home-assistant, seed-tool, https, local-ca, openssl, onboarding, lovelace-resources, aiohttp, unittest]

requires:
  - phase: 01-foundation
    provides: "Pinned HA 2026.10.4 (versions.env) and the owner-approved hassfest harness venv"
provides:
  - "python -m tools.seed --target {dev,preview} {wait,bootstrap,resources-sync}: brings a real HA over HTTPS, onboards it, promotes the HTTP config, names it and applies D-31 core settings"
  - "scripts/make-certs: name-constrained local root CA plus a leaf signed directly by it"
  - "dev/config-template/configuration.yaml: minimal HA config with http ssl and no default_config / homeassistant core block"
  - "tools/seed/envs.py ENVIRONMENTS table (single source for dev and preview identity, port, tag, theme)"
  - "tools/seed/client.py CA-pinned HAClient (rest, login, ws, drive_config_flow) and tools/seed/creds.py CredentialStore"
  - "tools/seed/resources.py: resources-sync keeps lovelace resource URLs on ?v=sha256(file)[:10]"
  - "LiveHA test harness: real HA 2026.10.4 on a temp config dir over HTTPS"
  - "Package-legitimacy approval recorded for every pip install later in this phase"
affects: [02-02, 02-05, 02-06, 02-07, 02-08, 02-09, 02-10]

# Actuals (#2632): chars/4 over the 14 files this plan changed (71677 bytes)
actuals:
  tokens: 17900
  tasks: 3
  commits: 3
plan_head_before: e9f9463a6b7dd78c3b4d1ba67bf04548870ce471
plan_head_after: c030abb

tech-stack:
  added: []
  patterns:
    - "Single ENVIRONMENTS table keyed by environment (dev, preview); no scattered is-preview checks"
    - "Refuse before credentials: loopback-only base URL, CA-pinned TLS, post-login location_name identity guard"
    - "COMMANDS dict of Command(help, run, configure) dataclasses so later plans add subcommands"
    - "Live tests copy the integration into a temp config dir; nothing runs from the repo tree"

key-files:
  created:
    - dev/config-template/configuration.yaml
    - scripts/make-certs
    - tools/seed/__init__.py
    - tools/seed/__main__.py
    - tools/seed/envs.py
    - tools/seed/client.py
    - tools/seed/creds.py
    - tools/seed/bootstrap.py
    - tools/seed/resources.py
    - tools/seed/tests/__init__.py
    - tools/seed/tests/live_ha.py
    - tools/seed/tests/live_dev.py
    - tools/seed/tests/test_envs.py
    - tools/seed/tests/test_resources.py
  modified: []

key-decisions:
  - "Name-constrained openssl root CA (pathlen 0, private ranges and localhost only) instead of mkcert; leaf signed directly by the root (no intermediate)"
  - "configuration.yaml carries no homeassistant core block, so config stays storage-sourced and the seed owns location_name and the D-31 keys through config/core/update"
  - "Seed credentials are one stored admin (fhtools) per environment, password generated once and reused; no long-lived tokens stored"
  - "panel/theme-builder-panel.js gets no lovelace resource (it is registered as a panel); panel/theme-selector-card.js does"
  - "Package installs for ical, gcal-sync, oauth2client, playwright, aiohttp, PyYAML are approved by the human at the Task 3 checkpoint, at exact pins, each to be installed by the later plan at its own step"

patterns-established:
  - "Pattern: tools refuse a non-loopback target with exit 2 before opening a socket, a wrong CA with exit 1 (TLS), a wrong identity with exit 3"
  - "Pattern: resources-sync never creates a second row for a path and fails on duplicate rows"

requirements-completed: [DEV-01, DEV-02]

coverage:
  - id: D1
    description: "The seed tool brings a fresh HA 2026.10.4 up over HTTPS from the local CA, onboards it, promotes the HTTP config (stable, revert_at null), names it Family Hub DEV and applies the TZ/HA_* core settings, with the family_hub integration loaded"
    requirement: DEV-01
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_dev.py (python -B -m unittest discover -s tools/seed/tests -t . -p live_dev.py): 7 tests OK, 15-21 s"
        status: pass
    human_judgment: false
  - id: D2
    description: "Guards refuse everything but a loopback Dev or Preview: non-loopback URL exits 2 before connecting, a foreign CA fails TLS, a wrong location_name exits 3 with no write; credentials file is 0600 in a 0700 dir and a second bootstrap is idempotent"
    requirement: DEV-01
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_dev.py (loopback, TLS, identity, file-mode and idempotence cases)"
        status: pass
    human_judgment: false
  - id: D3
    description: "resources-sync rewrites each changed lovelace resource to ?v=sha256(file)[:10], is idempotent (second run reports 0 updates) and keeps one resource row per served path"
    requirement: DEV-02
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_resources.py (python -B -m unittest discover -s tools/seed/tests -t . -p 'test_*.py'): 22 tests OK with test_envs.py"
        status: pass
      - kind: integration
        ref: "tools/seed/tests/live_dev.py resources-sync live case"
        status: pass
    human_judgment: false
  - id: D4
    description: "Environment table invariants: every field unique per environment, location names and dashboard titles match PREVIEW or DEV exactly once, themes fixed, base_url refuses http, public hosts and nip.io"
    requirement: DEV-01
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_envs.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Package-legitimacy approval for every pip install this phase needs, answered by a human before any install"
    verification: []
    human_judgment: true
    rationale: "A human decision recorded verbatim under Package approvals; no test can assert it"

# Metrics
duration: ~25 min active (first executor through Task 2; checkpoint wait excluded)
completed: 2026-11-04
status: complete
---

# Phase 02 Plan 01: Seed Tool for Dev and Preview Summary

**Seed tool (`python -m tools.seed`) that boots a real HA 2026.10.4 over HTTPS from a name-constrained local CA, onboards it, promotes the HTTP config, names it "Family Hub DEV", refuses any non-loopback or wrongly named target, and keeps card resource URLs on the served file hash.**

## Performance

- **Duration:** ~25 min active (Tasks 1-2 by the first executor, Task 3 by this continuation; the wait for the human reply is excluded)
- **Started:** 2026-11-03 (first task commit 15:52 UTC)
- **Completed:** 2026-11-04
- **Tasks:** 3 (1 tracer, 1 TDD auto, 1 blocking-human checkpoint)
- **Files modified:** 14 created, 0 modified
- **HA boot time in the sandbox:** about 6.4 s to the first HTTPS answer; the full live suite takes 15-21 s

## Accomplishments

- The tracer proves the whole HA path against a real HA 2026.10.4: certificate script, config template, HTTPS from the local CA, onboarding, HTTP promote (active_config_type "stable", revert_at null) and core settings.
- Three guards are proven to refuse: non-loopback URL (exit 2, under 5 s, no socket), foreign CA (exit 1, TLS), wrong identity (exit 3, location_name unchanged).
- `resources-sync` reproduces the integration's `_file_content_hash` exactly and is idempotent; the second run reports "resources: 0 updated".
- The environment table is guarded by an invariant test (`test_envs.py`).
- The package-legitimacy checkpoint is answered and recorded; nothing was installed.

## Task Commits

1. **Task 1 (tracer): seed tool brings a real HA up over HTTPS from the local CA, onboarded and named "Family Hub DEV"** - `96acbf6` (feat)
2. **Task 2: resources-sync and environment invariants (TDD)**
   - RED: `1fe2896` (test)
   - GREEN: `c030abb` (feat)
3. **Task 3: Package legitimacy approval** - checkpoint, no code commit (human reply recorded below)

Wave merge by the orchestrator: `7733d8b`. Orchestrator post-merge checks: 22 unit tests pass, `live_dev.py` 7 tests OK (19 s).

**Plan metadata:** recorded in the `docs(02-01)` commit that adds this file.

_TDD note: `test_envs.py` passes immediately because it guards the Task 1 table; the RED evidence is carried by `test_resources.py` (10 assertion failures against a stub)._

## Package approvals

Task 3 checkpoint (`checkpoint:human-verify`, `gate="blocking-human"`).

Human reply, verbatim: "Approved"

Exactly these pins are approved, and nothing else:

| Venv | Package pins |
|------|--------------|
| Harness venv `$HOME/.cache/fh-hassfest/venv` | `ical==14.3.0`, `gcal-sync==9.2.0`, `oauth2client==4.1.3` |
| Screenshot venv `$HOME/.cache/fh-shots/venv` | `playwright==1.64.1` plus its Chromium download, `aiohttp==3.14.5`, `PyYAML==6.0.3` |

The laptop needs no pip installs (the seed tool runs inside the pinned HA image).

No installs were run at this checkpoint; each later plan installs at its own step (02-05 and 02-06 for ical, 02-08 for gcal-sync and oauth2client, 02-10 for the screenshot venv).

Pre-install state check, run after the reply:

```
$ ls "$HOME/.cache/fh-hassfest/venv/lib/python3.14/site-packages" | grep -c '^ical'
0
```

The count is 0, so no install happened early.

## Files Created/Modified

- `dev/config-template/configuration.yaml` - minimal HA config: frontend, lovelace, config, my, mobile_app, http with ssl; no default_config, no homeassistant block, no server_port
- `scripts/make-certs` - name-constrained local root CA (once) and a leaf for the reserved IP, 127.0.0.1 and localhost; exits 2 for public or malformed IPs; leaf carries SKID/AKID
- `tools/seed/envs.py` - `Env`, `ENVIRONMENTS`, `get_env`, `base_url`, `GuardRefused`
- `tools/seed/client.py` - `SeedError`, CA-pinned `HAClient` (`rest`, `login`, `ws`, `drive_config_flow`)
- `tools/seed/creds.py` - `CredentialStore` over `credentials-<env>.json` (0600 file, 0700 dir)
- `tools/seed/bootstrap.py` - `wait_http`, `onboard_if_needed`, `wait_running`, `promote_http`, `apply_core_config`, identity guard
- `tools/seed/resources.py` - `served_js_files`, `served_urls`, `content_hash`, `plan_updates`, `sync`
- `tools/seed/__main__.py` - CLI with `COMMANDS` (`wait`, `bootstrap`, `resources-sync`)
- `tools/seed/tests/live_ha.py` - `LiveHA` harness
- `tools/seed/tests/live_dev.py`, `test_envs.py`, `test_resources.py` - live and unit tests

## Decisions Made

- Name-constrained openssl CA rather than mkcert (D-06 allows either); leaf signed directly by the root.
- No `homeassistant:` block in the template, so the seed owns `location_name` and D-31 keys via `config/core/update`.
- Package installs approved by the human at exact pins; installs deferred to the plans that need them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] LiveHA starts hass with `--skip-pip`**
- **Found during:** Task 1
- **Issue:** The plan forbids any install before the Task 3 checkpoint, but HA tries to pip-install integration requirements on first use, which would install packages before approval.
- **Fix:** `LiveHA` starts hass with `--skip-pip`. `hass_frontend`, `nacl`, `PIL`, `cronsim` and `securetar` were already in the venv, so Tasks 1-2 run without installs.
- **Files modified:** `tools/seed/tests/live_ha.py`
- **Verification:** Live suite OK with no package installed (the `ical` count is still 0).
- **Committed in:** `96acbf6`
- **Note for later plans:** plans that need `ical`, `gcal-sync` or `oauth2client` must drop `--skip-pip` (or pass it only when nothing is missing) after installing the approved pins.

**2. [Rule 1 - Bug] `config/auth/list` includes the system user "Home Assistant Content"**
- **Found during:** Task 1 (idempotence test)
- **Issue:** The test as planned asserted exactly one user, but HA lists a system-generated user too.
- **Fix:** The test asserts exactly one non-system user, named `fhtools`.
- **Files modified:** `tools/seed/tests/live_dev.py`
- **Verification:** Live suite OK.
- **Committed in:** `96acbf6`

### Additions beyond the written steps (within scope)

- `served_urls()` reads the `*_JS_URL` constants so resource paths follow what the integration serves; `plan_updates` takes an optional `urls` argument.
- `panel/theme-builder-panel.js` gets no resource (registered as a panel); `panel/theme-selector-card.js` does.
- `resources-sync` runs the identity guard through `open_admin` (a preview target against a dev instance exits 3).
- After writing, `resources-sync` re-lists and fails on duplicate rows.
- `leaf.cnf` carries SKID/AKID; `make-certs` exits 2 for public or malformed IPs.

### Checkpoint-continuation bookkeeping

The plan's per-plan commit ledger lived in the first executor's worktree git dir and is not available here. `commits: 3` was measured from the plan base `e9f9463a` to `c030abb` (`git rev-list --count`), which excludes the orchestrator's merge commits and other plans' commits. `plan_head_after` is the last plan commit, `c030abb`.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both were needed to keep the no-install-before-approval rule and to make the idempotence test correct. No scope creep.

## Interface Notes for Later Plans

- `HAWebSocket.call()` returns the whole result message; read `reply["result"]`.
- `drive_config_flow` handles menu steps.
- `CredentialStore.exists()` exists alongside `admin()`, `member()` and `save()`.
- `COMMANDS` entries are `Command(help, run, configure)` dataclasses.
- `LiveHA.seed(*args, target=, base_url=, ca=, env=, timeout=)`; `LiveHA.admin_session()` yields `(client, token, ws)`; `admin_ws()` yields `ws`.

## Issues Encountered

None beyond the deviations above. No authentication gates occurred.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required. The package approvals above allow installs that later plans run themselves.

## Next Phase Readiness

- Plan 02-02 (same wave, already merged) wraps this tool in `scripts/dev-up` and `scripts/dev-cards`.
- Plans 02-05, 02-06, 02-08 and 02-10 may install their approved pins at their own step; the `--skip-pip` flag in `LiveHA` needs to be dropped when `ical`, `gcal-sync` or `oauth2client` are first needed.
- No blockers.

## Self-Check: PASSED

- All 14 created files exist on disk (checked with `ls` against the plan's file list).
- Commits `96acbf6`, `1fe2896`, `c030abb` are ancestors of HEAD.
- `ls "$HOME/.cache/fh-hassfest/venv/lib/python3.14/site-packages" | grep -c '^ical'` prints 0.

---
*Phase: 02-dev-family-preview*
*Completed: 2026-11-04*
