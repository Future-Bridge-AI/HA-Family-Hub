---
phase: 02-dev-family-preview
plan: 05
subsystem: infra
tags: [home-assistant, seed-tool, family-hub, config-flow, lovelace, notification-isolation, verify, unittest]

requires:
  - phase: 02-dev-family-preview
    provides: "Seed tool client, credential store, bootstrap and the LiveHA harness (plan 02-01); dev-up and lib.sh (plan 02-02); approved ical==14.3.0 install"
provides:
  - "python -m tools.seed --target {dev,preview} seed: accounts, lists, calendars, Family Hub config flow, dashboard, her sidebar, her pretend week, safe notifications, then verify"
  - "python -m tools.seed --target ... verify: FAIL <check>: <detail> lines, exit 1 on any problem"
  - "tools/seed/family_file.py and the invented example family (Sam, Jordan, Riley, Casey)"
  - "tools/seed/content.py: pure date-relative content builder following UI-SPEC S5"
  - "scripts/dev-up now runs seed"
affects: [02-06, 02-07, 02-08, 02-09, 02-10]

# Actuals (#2632): chars/4 over the 16 files changed (129248 bytes, whole-file size)
actuals:
  tokens: 32300
  tasks: 3
  commits: 7
plan_head_before: 0a69161b96545c3020c61d8f27347ebb2fa41a07
plan_head_after: 5513149c12b92b79ddc9c272c537f524e2a51315

tech-stack:
  added: []
  patterns:
    - "Pure check_* functions return lists of problems; unreadable input is always a problem"
    - "Every seed step is an idempotent top-up; a second seed changes nothing (proven by a snapshot comparison)"
    - "Content is built by a pure date-relative function and applied by a separate I/O module"
    - "Config flows that fail half way are aborted on the server so a retry is not blocked"

key-files:
  created:
    - tools/seed/family_file.py
    - tools/seed/data/family.example.yaml
    - tools/seed/users.py
    - tools/seed/entries.py
    - tools/seed/dashboard.py
    - tools/seed/content.py
    - tools/seed/family_hub.py
    - tools/seed/verify.py
    - tools/seed/tests/test_family_file.py
    - tools/seed/tests/test_content.py
    - tools/seed/tests/test_verify.py
    - tools/seed/tests/live_family.py
  modified:
    - tools/seed/__main__.py
    - tools/seed/client.py
    - tools/seed/creds.py
    - scripts/dev-up

key-decisions:
  - "The Recipes card reads the recipes store (family_hub/get_recipes and set_recipes), not todo.recipe_box, so recipes are written through set_recipes into an empty store; ingredients ride in the description text because the record has no ingredients field"
  - "Meal Suggestions are seeded as one item in todo.meal_suggestions; the card migrates it into its own suggestions store the first time it opens"
  - "Grocy blank is checked through family_hub/get_grocy_recipes (configured false), because config entry options are not exposed over the API"
  - "verify minimums are the seeded counts for areas that do not decay (rewards 5, recipes 3, pantry 3, groceries 6, errands 3, per-child chores 4) and plain non-empty for dinners, so a later standalone verify raises no false alarm"
  - "Pantry tab kept per D-18; dropping it is a one-entry change in DASHBOARD_VIEWS"

patterns-established:
  - "Pattern: Family Hub config flow answers keyed by step id, with a callable for the member_profile loop that reads the member name from description_placeholders"
  - "Pattern: names of the invented family live only in family.example.yaml and the tests; code and comments say parent, child, admin parent, non-admin parent"

requirements-completed: [DEV-03, PREV-02, PREV-03, PREV-04, PREV-08, ACCESS-01]

coverage:
  - id: D1
    description: "One seed command turns a freshly onboarded instance into accounts for every family-file member (admin parent in system-admin, others system-users), seven Local To-do lists, a Local Calendar per member, the Family Hub entry through its own config flow and the storage-mode dashboard family-hub"
    requirement: DEV-03
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_family.py test_a..test_f (python -B -m unittest discover -s tools/seed/tests -t . -p live_family.py): 16 tests OK, about 31 s"
        status: pass
    human_judgment: false
  - id: D2
    description: "Her non-admin login lands on a dashboard with seven icon tabs in order Calendar, Today, Chores, Rewards, To-dos, Recipes, Pantry and a sidebar showing only Family Hub; her hiddenPanels is the sorted list of every other panel and default_panel is family-hub"
    requirement: ACCESS-01
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_family.py test_c_her_login_is_not_admin_and_sees_only_family_hub, test_f_dashboard_has_one_card_per_tab"
        status: pass
      - kind: unit
        ref: "tools/seed/tests/test_verify.py SidebarTests (lookalike panel hidden, missing family-hub fails, only panel leaves nothing hidden)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Sign-in details survive a reset: passwords and kid PINs are generated once into the credentials file; each child can elevate with the stored PIN and is listed for kiosk sign-in"
    requirement: PREV-02
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_family.py test_x (login as her with stored password after re-seed), test_y (kiosk elevate with stored PINs), test_k"
        status: pass
    human_judgment: false
  - id: D4
    description: "Seeded content follows UI-SPEC S5 relative to today: 4 to 6 recurring chores per child with at least 2 due today and none overdue, 5 rewards with balances that afford the cheapest but not the dearest, one goal, a morning routine, 3 recipes, dinners on 6 of the next 7 nights, Groceries 6, Errands 3, Meal Suggestions 1, 3 pantry notes; a re-run adds nothing"
    requirement: PREV-04
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_content.py (14 dates including a Sunday and a month end)"
        status: pass
      - kind: integration
        ref: "tools/seed/tests/live_family.py test_g..test_k and test_z_second_seed_changes_nothing"
        status: pass
    human_judgment: false
  - id: D5
    description: "Environment identity: location name, dashboard title and global theme all name the environment (Dev blossom, Preview midnight, never slate); verify fails on an empty or wrong name and on a missing theme"
    requirement: PREV-02
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_verify.py IdentityTests"
        status: pass
      - kind: integration
        ref: "tools/seed/tests/live_family.py test_k (globalThemeId blossom) and test_f (title Family Hub DEV)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Nothing can reach a real phone or speaker: every profile has empty notify targets and all alerts off, alarmDevices empty, no media_player or assist_satellite entity, config entry domains only from the allow list, no discovery components loaded, Grocy blank; verify fails on any offender and the live tamper test proves exit 1 then pass after re-seed"
    requirement: PREV-03
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_verify.py IsolationTests, GrocyTests"
        status: pass
      - kind: integration
        ref: "tools/seed/tests/live_family.py test_l, test_m, test_x_verify_fails_on_a_real_phone_target_and_passes_again_after_seed"
        status: pass
    human_judgment: false
  - id: D7
    description: "The committed repo holds only the invented example family; the real family file tools/seed/family.local.yaml is ignored and never tracked, and no real names appear in non-test code"
    requirement: PREV-04
    verification:
      - kind: other
        ref: "git check-ignore -q --no-index tools/seed/family.local.yaml (exit 0); git grep -l -w -e Sam -e Jordan -e Riley -e Casey -- tools/seed ':!tools/seed/data/family.example.yaml' ':!tools/seed/tests' prints nothing"
        status: pass
    human_judgment: false
  - id: D8
    description: "The Pantry tab is useful with Grocy off (the Also Tracking list with three seeded notes)"
    verification: []
    human_judgment: true
    rationale: "Whether the Pantry tab earns its place with Grocy off is a product judgment (UI-SPEC A3); the developer looks at it in Dev after scripts/dev-up and decides"

# Metrics
duration: 14 min
completed: 2026-11-04
status: complete
---

# Phase 02 Plan 05: Her Pretend Week, Her Dashboard and a Verify That Fails Loudly Summary

**One `seed` command turns a freshly onboarded Home Assistant 2026.10.4 into her Family-Hub-only login (non-admin, seven icon tabs, a date-relative week of chores, rewards, meals, lists, recipes and pantry notes in the environment's own theme) and ends with a verify that exits 1 if any notify target, speaker, outbound entry or missing piece could break the safe-Preview promise.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-11-04T00:11:03Z
- **Completed:** 2026-11-04T00:25:11Z
- **Tasks:** 3 (1 tracer, 2 TDD auto)
- **Files modified:** 16 (12 created, 4 modified)
- **Test runs at the end:** 87 unit tests OK; `live_family.py` 16 tests OK (31 s); `live_dev.py` 7 tests OK (16 s)

## Accomplishments

- Tracer: the whole path works on a real HA 2026.10.4: users, seven to-do lists, four Local Calendars, Family Hub through its own config flow, the `family-hub` dashboard and her sidebar. Tracer verified end-to-end before expansion (the live gate, `bash -n scripts/dev-up` and the `fh_seed dev seed` grep all passed).
- Her pretend week: chores, rewards, balances, goal, routine, pantry notes, recipes, dinners and list items are idempotent top-ups; a second seed leaves a snapshot of everything byte-equal.
- Safety: `apply_safe_notifications` forces every profile to no notify targets and all alerts off, clears `alarmDevices` and `remove_outbound_entries` deletes `radio_browser`, `google_translate` and `met`; `verify` enforces all of it and the live tamper test proves exit 1 (naming `notifyTargets` and her user id) and a pass after re-seeding.
- Forbidden component found loaded: **none**. The live run shows no `zeroconf`, `ssdp`, `dhcp`, `bluetooth`, `usb`, `cloud`, `homeassistant_alerts` or `default_config`, because the config template carries no `default_config`. The list was not widened.
- Which recipe store the Recipes card reads: the recipes store behind `family_hub/get_recipes` and `family_hub/set_recipes` (`entry_data["recipes_store"]`), not `todo.recipe_box` (that list is only read once to migrate an unmigrated store).

## Task Commits

1. **Task 1 (tracer): her non-admin login lands on the Family Hub dashboard with only Family Hub in the sidebar** - `d29e39b` (feat)
2. **Task 2: her pretend week (TDD)**
   - RED: `aacbba4` (test) - 84 assertion failures in `test_content.py` against a stub; `test_family_file.py` passes at once because it guards Task 1 code
   - GREEN: `7008894` (feat, content builder) and `38b49d6` (feat, Family Hub top-up, settings, PINs, live tests)
3. **Task 3: nothing reaches a real phone (TDD)**
   - RED: `c752921` (test) - 26 assertion failures in `test_verify.py` against a stub, the positive cases already pass
   - GREEN: `5d09fa6` (feat, pure checks and `run_verify`) and `5513149` (feat, safe notifications, outbound removal, CLI wiring, live tamper test)

**Plan metadata:** the `docs(02-05)` commit that adds this file.

## TDD Gate Compliance

RED (`test(02-05)`) precedes GREEN (`feat(02-05)`) for Tasks 2 and 3. RED evidence: unittest output run against a stub module with the real signatures (so the target tests loaded and failed on their planned assertions, not on import errors). The `gsd_run check tdd-red-evidence` classifier was not run (no `gsd_run` in this sandbox); the semantic assessment was made by inspecting the failures: every failing test names its planned assertion (volumes, sorting, whole-string match). No REFACTOR commits.

## Files Created/Modified

- `tools/seed/family_file.py` - strict loader: unknown keys, one admin parent, a non-admin parent, ages, colours, usernames, calendars; errors name the key path (exit 2)
- `tools/seed/data/family.example.yaml` - invented family Sam (admin parent), Jordan (non-admin parent), Riley (9), Casey (6)
- `tools/seed/users.py` - `ensure_users`: accounts by login name, groups checked, half-made accounts removed
- `tools/seed/entries.py` - `ensure_todo_lists`, `ensure_local_calendars`, `ensure_family_hub_entry`, `entity_for_entry` (entity ids from the registry)
- `tools/seed/dashboard.py` - `DASHBOARD_VIEWS`, `build_config`, `ensure_dashboard`, `hidden_panels`, `set_member_sidebar`
- `tools/seed/content.py` - dataclasses and `build_content(family, env, today)`
- `tools/seed/family_hub.py` - `apply_content`, `apply_settings`, `apply_safe_notifications`, `remove_outbound_entries`, `instance_today`
- `tools/seed/verify.py` - `check_identity`, `check_isolation`, `check_grocy`, `check_dashboard`, `check_sidebar`, `check_content`, `check_resources`, `run_verify`
- `tools/seed/__main__.py` - `seed` and `verify` subcommands (`--family`, `--integration-dir`)
- `tools/seed/client.py`, `tools/seed/creds.py` - flow abort on failure; `CredentialStore.pin`
- `scripts/dev-up` - runs `seed` instead of `bootstrap`
- `tools/seed/tests/test_family_file.py`, `test_content.py`, `test_verify.py`, `live_family.py` - tests (87 unit, 16 live)

## Decisions Made

- Recipes go through `set_recipes` into an empty store; ingredients are carried in the description text.
- Dev and Preview show the same week; `env` is accepted by `build_content` so wording can diverge later.
- Chore due dates are stored as the end of the local day (23:59 in the instance's time zone) so nothing is overdue when seeded; "today" is read from the instance's own time zone.
- Pantry kept per the locked D-18 (see the human check below).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Failed config flows left the flow open and blocked the next run**
- **Found during:** Task 1 (first live run)
- **Issue:** `drive_config_flow` left a half-finished Family Hub flow on the server after an error, so the next seed aborted with `already_in_progress`.
- **Fix:** `drive_config_flow` now aborts the flow (`DELETE .../flow/<id>`) on any SeedError before re-raising.
- **Files modified:** `tools/seed/client.py`
- **Verification:** `live_family.py` and `live_dev.py` OK
- **Committed in:** `d29e39b`

**2. [Rule 3 - Blocking] Family Hub's member_profile only accepts its six palette colours**
- **Found during:** Task 1
- **Issue:** The example colours for the children were not in the setup form's palette (`#7ec9d9`, `#9ed97e`, `#b07ed9`, `#d97e9e`, `#d9a67e`, `#d9bf7e`), so the flow returned HTTP 400.
- **Fix:** The example family uses palette colours. A family-file colour outside the palette is answered with a palette colour in the flow and then written to the member's profile by `apply_settings`.
- **Files modified:** `tools/seed/data/family.example.yaml`, `tools/seed/entries.py`, `tools/seed/family_hub.py`
- **Committed in:** `d29e39b`, `38b49d6`

**3. [Rule 3 - Blocking] `CredentialStore` had no PIN accessor**
- **Found during:** Task 1
- **Issue:** The plan has each child's 4-digit PIN generated once and saved in the credentials file, but `creds.py` only stored passwords.
- **Fix:** Added `CredentialStore.pin(first_name)` (generated once with `secrets.randbelow`, saved 0600 like the rest).
- **Files modified:** `tools/seed/creds.py` (not in the plan's file list)
- **Committed in:** `d29e39b`

**4. [Rule 1 - Bug] A star-reward goal needs a positive star value**
- **Found during:** Task 2 (second seed in the live test)
- **Issue:** `family_hub/goals/create` rejected the goal with `invalid_star_value`.
- **Fix:** `Goal.star_value` (5) is sent with the goal.
- **Files modified:** `tools/seed/content.py`, `tools/seed/family_hub.py`
- **Committed in:** `38b49d6`

### Interpretations and small additions

- `run_verify` takes the admin `token` as well (the REST entries list needs it): `run_verify(client, token, ws, env, family, creds, integration_dir, say)`.
- Grocy blank is checked through `family_hub/get_grocy_recipes` (`configured: false`), since config entry options are not readable over the API. If Grocy were configured, that call would make one request to the configured Grocy; in a seeded instance it never is.
- `verify` minimums use the seeded counts for areas that do not decay and "not empty" for upcoming dinners (see key-decisions); the plan said "the Task 2 minimums".
- `seed` also takes `--integration-dir` (needed by its closing verify), and `family_file.load` rejects a non-null `google` block with "needs plan 02-08".
- Notification flags are enforced off by verify as well as the notify targets (the plan's truth lists them together).

### Environment note

The per-plan commit ledger and the cwd-drift sentinel could not be written into the worktree's git directory (the sandbox refused writes outside the worktree), so `plan_head_before` is the known base commit `0a69161` (the worktree HEAD at spawn, checked at start) and the ledger copy lives in the session scratchpad. `commits: 7` is `git rev-list --count 0a69161..HEAD` before this summary's own commit.

---

**Total deviations:** 4 auto-fixed (2 bug, 2 blocking), plus the interpretations above
**Impact on plan:** All needed for correctness or to make the live flow complete; no scope creep.

## Issues Encountered

None beyond the deviations above. No authentication gates.

## Known Stubs

None. (The `google` block in the family file is rejected until plan 02-08 defines it, by design.)

## Threat Flags

None. The seed adds no endpoint or auth path to the integration; the new surface is the seed tool's own client calls, all on the loopback guard from plan 02-01. T-02-07 (notifications), T-02-08 (real data in git: `family.local.yaml` ignored, only the invented family committed) and T-02-09 (non-admin accounts, proven `is_admin` false) are mitigated and covered by tests. T-02-SC held: only the pre-approved `ical==14.3.0` was used.

## User Setup Required

None - no external service configuration required.

**Human check (from Task 3):** in Dev after `scripts/dev-up` on the laptop (plan 02-09), sign in as the example's non-admin parent and open the Pantry tab. If the "Also Tracking" list is useful with Grocy off, keep it; if not, say so and the Pantry entry is removed from `DASHBOARD_VIEWS` (UI-SPEC A3).

## Next Phase Readiness

- Plan 02-06 (calendar events) can add `tools/seed/calendar_tags.py` and `events.py`; plan 02-07 wires them after `apply_content` in `seed`, before the closing verify.
- Plan 02-07's reset test can reuse `live_family.py`'s stored-credentials login (test_x signs in as her with the stored password after a re-seed).
- `LiveHA` still starts with `--skip-pip`; `ical` is pre-installed so Local To-do and Local Calendar load.
- No blockers.

## Self-Check: PASSED

- All 12 created files exist on disk (checked with `ls`): family_file.py, data/family.example.yaml, users.py, entries.py, dashboard.py, content.py, family_hub.py, verify.py, tests/test_family_file.py, test_content.py, test_verify.py, live_family.py.
- Commits `d29e39b`, `aacbba4`, `7008894`, `38b49d6`, `c752921`, `5d09fa6`, `5513149` are ancestors of HEAD.
- Acceptance re-run: 87 unit tests OK; `live_family.py` 16 tests OK; `live_dev.py` 7 tests OK; `bash -n scripts/dev-up` and `fh_seed dev seed` grep pass; `git check-ignore --no-index tools/seed/family.local.yaml` exits 0; four `first_name:` lines in the example; the name grep over `tools/seed` outside the example and tests prints nothing; `grep -c alarmDevices` is 2 in verify.py and 1 in family_hub.py; `grep -c '^import aiohttp\|^from aiohttp' tools/seed/content.py` is 0; the only `reminder_minutes` occurrences are an empty-tuple default and an empty list.

---
*Phase: 02-dev-family-preview*
*Completed: 2026-11-04*
