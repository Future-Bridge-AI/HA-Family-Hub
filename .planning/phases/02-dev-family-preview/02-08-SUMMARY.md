---
phase: 02-dev-family-preview
plan: 08
subsystem: infra
tags: [google-calendar, oauth, home-assistant, application-credentials, ics-backup, entity-registry, seed-tool, bash, unittest]

requires:
  - phase: 02-dev-family-preview
    provides: "02-01 seed tool and LiveHA, 02-05 family file and seed/verify, 02-06 events.sync and CalendarSlot, 02-07 deploy/reset/refresh scripts with the D-08 hook points and entries.calendar_slots"
provides:
  - "tools/seed/google.py: save_entry, restore_entry, ensure_credential, link, select_entities, apply_selection, google_slots, member_calendars"
  - "tools/seed/backup.py: BackupError (exit 5), backup_calendars, default_fetch, read_snapshots"
  - "seed commands google-save, google-restore, google-link, backup-calendars; seed and refresh run the Google setup"
  - "scripts/lib.sh: fh_google_save, fh_google_restore, fh_backup_calendars (first step of fh_reset_env, deploy-preview, refresh-preview)"
  - "family file google block (client_id, client_secret, calendars[]) fully validated; member calendar google:<key>"
  - "dev/GOOGLE.md: one-time Google setup, first sign-in, expiry and revoke, restore an event from a backup"
affects: [02-09, 02-10]

# Actuals (#2632): chars/4 over the 16 files changed (200643 bytes, whole-file size)
actuals:
  tokens: 50160
  tasks: 3
  commits: 5
plan_head_before: 038e5186af24597d3d5e12004cb3445090284402
plan_head_after: acc76dca6c25badb643cf8746ff2585d5b744698

tech-stack:
  added: []
  patterns:
    - "Save the Google config entry from the STOPPED instance into a 0600 file outside the HA volume, write it back as the only entry of core.config_entries before HA starts, then create the application credential and reload until loaded"
    - "A backup folder with a date on it is always complete: files go into a .partial folder that is renamed only after every calendar succeeded"
    - "Calendar selection by exact unique_id '<entry unique_id>-<calendar_id>', never by suffix; every other google-platform entity is disabled on every run"
    - "Secret iCal addresses are used only to fetch; error messages carry the calendar key and the exception type, never the address or the exception text"
    - "Stub docker in test_scripts.py plays three containers (read-only cat, restore writer, wipe), so save/wipe/restore ordering is asserted without a Docker daemon"

key-files:
  created:
    - tools/seed/google.py
    - tools/seed/backup.py
    - dev/GOOGLE.md
    - tools/seed/tests/live_google.py
    - tools/seed/tests/test_google.py
    - tools/seed/tests/test_backup.py
  modified:
    - tools/seed/family_file.py
    - tools/seed/entries.py
    - tools/seed/__main__.py
    - tools/seed/data/family.example.yaml
    - tools/seed/tests/live_ha.py
    - tools/seed/tests/test_family_file.py
    - tools/seed/tests/test_scripts.py
    - scripts/lib.sh
    - scripts/deploy-preview
    - scripts/refresh-preview

key-decisions:
  - "The synthetic Google entry points at the credential id Home Assistant derives (slugify of 'google.<client_id>'), not the literal 'google' the plan named, because only that id resolves once the seed has created the credential"
  - "The Google save and restore skip silently inside the seed commands (they read the family file), not in shell, so the shell only needs to pipe and the stub tests stay simple"
  - "In seed, accounts and to-do lists come before the Google link, so the very first run (no sign-in yet) already has the developer's own account to sign in with; Google is still ahead of the Family Hub entry"
  - "refresh calls link with reload=False (check only) and then re-applies the selection, so a daily refresh does not reload the Google entry"
  - "deploy-preview gets its own step 2 'backing up the chosen Google calendars', so a backup failure reads 'failed at step 2', not 'taking the lock'"

patterns-established:
  - "Pattern: any destructive script calls fh_backup_calendars plainly (not in an if or after ||) right after its lock, and a stub test with FH_STUB_FAIL=backup-calendars asserts no docker, refresh or seed call follows"
  - "Pattern: a saved secret travels through a pipe or a shell variable, never a temporary file"

requirements-completed: [PREV-03, PREV-04]

coverage:
  - id: D1
    description: "A reset keeps the Google sign-in: the stopped instance's entry is saved (0600, outside the volume), written back as the only entry before HA starts, and after the credential is created and the entry reloaded it is 'loaded' again"
    requirement: PREV-03
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_google.py LiveGoogleSigninTests (real HA 2026.10.4: setup_error without the credential, loaded with it, before and after a wipe; saved file 0600 with the same entry_id, unique_id and refresh_token; restore refused into a non-wiped dir)"
        status: pass
      - kind: unit
        ref: "tools/seed/tests/test_scripts.py GoogleResetTests (save before the wipe, write-back before the start, a failed save or restore stops the reset)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Without the application credential the entry is in setup_error and the seed stops with the one-time sign-in instruction from dev/GOOGLE.md; with no entry at all it says the same and still creates the credential"
    requirement: PREV-03
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_google.py LiveGoogleNoEntryTests and test_b/test_e (state 'setup_error', reason 're-authentication required')"
        status: pass
      - kind: unit
        ref: "tools/seed/tests/test_google.py CredentialAndLinkTests (setup_error, setup_retry with reauth pending, no entry)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Only the chosen calendars stay enabled: exact unique_id match, every other google entity (Birthdays and Work location included, look-alike suffixes included) disabled, a user-disabled chosen one enabled again, other platforms untouched"
    requirement: PREV-03
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_google.py SelectEntitiesTests and ApplySelectionTests (fake entity registry and websocket)"
        status: pass
    human_judgment: true
    rationale: "With a fake token Google returns no calendars, so no real google calendar entity exists here. The unique_id format was read from HA 2026.10.4's google/calendar.py; the selection against a real account is checked at the plan 02-09 laptop checkpoint"
  - id: D4
    description: "Pretend events go only to chosen Google calendars marked writable and expect_events; read-only calendars get none and the sync's delete allow-list holds only those plus the local ones"
    requirement: PREV-03
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_google.py GoogleSlotsTests (slots, the allow-list through entries.calendar_slots)"
        status: pass
      - kind: integration
        ref: "tools/seed/tests/live_events.py test_f_a_read_only_calendar_is_never_written (writable=False slot never written, on a real Local Calendar)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Family file google block: valid example passes; errors name the key path for missing client_id, upper-case key, unknown person, unknown member calendar key, ical backup without address, wrong host or extension, duplicate calendar_id, expect_events without writable; the secret address never appears in a message"
    requirement: PREV-03
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_family_file.py GoogleBlockTests (23 cases)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Before every deploy-preview, reset-preview, dev-reset and refresh-preview each chosen calendar is exported to a dated 0600 .ics that must be HTTP 200, non-empty, start with BEGIN:VCALENDAR and contain END:VCALENDAR; any failure stops the command before anything is stopped, wiped, exported or deleted"
    requirement: PREV-03
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_backup.py (404, empty, HTML, cut-off, raising fetch, partial leaves nothing, snapshot cases, URL never printed, exit code 5) and test_scripts.py BackupHardStopTests (the stub docker log has no stop, down, wipe or up and no refresh or seed call after the failure)"
        status: pass
    human_judgment: true
    rationale: "The real fetch (urllib to Google's secret iCal address) was never run here: no Google account and no network path to one. Whether Google's feed is fresh enough (A11) and its single-event import works (A12) is checked at the plan 02-09 checkpoint with a throwaway calendar"
  - id: D7
    description: "dev/GOOGLE.md gives the developer the Google Cloud project, the published OAuth consent screen, the Web application client and redirect URI, the first sign-in per environment, calendar choice, token expiry and revoke steps, and how to restore one event from a backup"
    requirement: PREV-04
    verification:
      - kind: other
        ref: "gate: google_md_missing [] (every required phrase present); no client id committed outside tests"
        status: pass
    human_judgment: true
    rationale: "Whether the guide is followable end to end is only known when the developer does it for real at the plan 02-09 laptop checkpoint (real project, real first sign-in)"
  - id: D8
    description: "The real chosen Google calendars and the pretend events appear together in the week she sees"
    requirement: PREV-04
    verification: []
    human_judgment: true
    rationale: "Needs a real Google account, the Windows browser sign-in and Docker on the laptop: the plan 02-09 checkpoint"

# Metrics
duration: 20 min
completed: 2026-11-04
status: complete
---

# Phase 02 Plan 08: Google Calendar Connection with Guardrails Summary

**Dev and Preview can connect read and write to the chosen real Google calendars: the sign-in is saved before a reset and written back before Home Assistant starts, only the chosen calendars stay enabled, pretend events go only to writable ones, and every deploy, reset and refresh first backs each chosen calendar up to a dated .ics and stops hard if any backup is not a real calendar file.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-11-04T00:59:44Z
- **Completed:** 2026-11-04T01:19:41Z
- **Tasks:** 3 (1 tracer, 2 TDD auto)
- **Files modified:** 16 (6 created, 10 modified)
- **Final runs:** 319 unit and stub tests OK in 5 s; all live modules (`live_*.py`, 54 tests, none skipped) OK in 188 s on HA 2026.10.4; `bash -n` clean on lib.sh, deploy-preview, refresh-preview, reset-preview, dev-reset

## Synthetic entry and observed state transitions

The synthetic Google entry (no Google contacted for credentials; the calendar platform's call with the fake token fails and is only logged):

- File `core.config_entries`: `version` 1, `minor_version` 5 (`homeassistant.config_entries.STORAGE_VERSION` and `STORAGE_VERSION_MINOR`).
- Entry: `version` 1, `minor_version` 1 (`google.config_flow.OAuth2FlowHandler.VERSION` and `MINOR_VERSION`), `domain` google, `unique_id` `test-primary@example.com`, options `calendar_access: read_write`, a token valid for 30 days with scope `https://www.googleapis.com/auth/calendar`, and `auth_implementation` set to the credential id for the fake client (`google_test_client_apps_googleusercontent_com`).

Observed (live, twice, same result):

| Moment | Entry state |
|---|---|
| restored before the first start, after bootstrap, no credential | `setup_error` ("The configured authentication method is no longer available, re-authentication required") |
| after `google-link` (credential created, entry reloaded) | `loaded` |
| after stop, wipe, restore, start, bootstrap, still no credential | `setup_error` (and the application credentials list is empty again) |
| after `google-link` again | `loaded`, same `entry_id` |

`google-save` of the stopped instance wrote `google-dev.json` with mode 0600 in a 0700 directory, with the same `entry_id`, `unique_id` and `refresh_token`; `git status --porcelain` showed no secrets file in the repository.

## Accomplishments

- **Sign-in survives a reset (D-10):** `fh_google_save` (after compose down, read-only container `cat` piped into `google-save --stdin`) and `fh_google_restore` (after the wipe check, before compose up, through a variable and a pipe, never a temp file). A failed save stops the reset before anything is wiped, a failed restore before the start. `google-link` creates the credential only when none matches the client id and waits up to 120 s for `loaded`; `setup_error`, or `setup_retry` with a reauth flow pending, becomes the one-time instruction naming `dev/GOOGLE.md, First sign-in`.
- **Only the chosen calendars (D-07):** `select_entities` matches `<entry unique_id>-<calendar_id>` exactly and disables every other google-platform entity; `apply_selection` waits for the kept entities to report a state and errors by calendar id if a chosen one has no entity.
- **Events only where allowed (D-11, D-25):** `google_slots` gives `CalendarSlot(writable=True)` only for `writable` plus `expect_events`; `entries.calendar_slots` merges them with the local slots; the event sync's delete allow-list is built from writable slots only. `member_calendars` maps a member on `google:<key>` to that entity for the Family Hub member calendar and the dashboard.
- **Backup with a hard stop (D-08, D-30):** `backup_calendars` writes `<key>.ics` (0600) into `dev/.ha-backups/<env>/<stamp>/`, atomically via a `.partial` folder; `ha-snapshot` calendars are written as `<key>.json` from the running instance; `backup-calendars` exits 5 with `backup failed for <key>: <reason> - nothing was changed`. `fh_backup_calendars` is the first action of `fh_reset_env`, of `deploy-preview` (own step 2) and of `refresh-preview` (after the running check, because snapshots need the running instance).
- **Family file google block** with key-path errors, defaults (`backup: ical`, flags false) and no echo of the secret address.
- **dev/GOOGLE.md** covering the project, published consent screen, Web application client with redirect `https://my.home-assistant.io/redirect/oauth`, calendar choice, first sign-in per environment (ports 8130 and 8124), what resets keep, token expiry and revoke, the secrets table, the `google` block keys, and "Restore an event from a backup" with disk use and pruning.

## Task Commits

1. **Task 1 (tracer): Google sign-in survives a reset** - `c8cb15d` (feat). Tracer gate: auto mode, automated-only `<verify>`; re-run after the commit (8 live tests OK) so expansion went ahead ("Tracer verified end-to-end - expanding").
2. **Task 2: chosen calendars, writable-only events, Google guide (TDD)**
   - RED: `932856f` (test) - 16 assertion failures in `test_family_file.py` (google block validation not written) and 9 in `test_google.py` (selection and slots returned empty stubs); one ERROR (`KeyError: 'backup'`, the missing default)
   - GREEN: `187abed` (feat)
3. **Task 3: backup before anything destructive (TDD)**
   - RED: `5a81ff5` (test) - 34 assertion failures (placeholder `backup_calendars` wrote nothing, the command did nothing, no script called `fh_backup_calendars`) plus one ERROR (listing a backup folder the placeholder never wrote)
   - GREEN: `acc76dc` (feat)

**Plan metadata:** the `docs(02-08)` commit that adds this file.

## TDD Gate Compliance

RED (`test(02-08)`) precedes GREEN (`feat(02-08)`) for Tasks 2 and 3. RED evidence is the real unittest output against placeholders with the real signatures, so the target tests loaded and failed on their planned assertions (not on import or syntax errors). The two ERROR entries are target tests that failed on the planned behavior itself (a missing default, a folder never written). `gsd_run check tdd-red-evidence` was not run (no `gsd_run` in this sandbox); the semantic assessment was made by reading the failures. Task 1 is a tracer, so its tests were written with the code. No REFACTOR commits.

## Files Created/Modified

- `tools/seed/google.py` - sign-in save/restore, credential, link, selection, slots
- `tools/seed/backup.py` - `BackupError`, `backup_calendars`, `default_fetch`, `read_snapshots`
- `tools/seed/__main__.py` - commands `google-save`, `google-restore`, `google-link`, `backup-calendars`; `_google_setup` in seed and refresh; exit 5 for `BackupError`
- `tools/seed/family_file.py`, `tools/seed/entries.py`, `tools/seed/data/family.example.yaml` - google block, slots, example comment
- `scripts/lib.sh`, `scripts/deploy-preview`, `scripts/refresh-preview` - save, restore and backup hooks; `fh_seed` passes `-i` for a pipe and mounts `.ha-backups`
- `dev/GOOGLE.md` - developer guide
- `tools/seed/tests/live_google.py`, `test_google.py`, `test_backup.py`, `test_family_file.py`, `test_scripts.py`, `live_ha.py` - tests (`LiveHA.seed` gained `input_text`)

## Decisions Made

See `key-decisions` above. The ones to remember: the saved sign-in is only as good as the client id staying the same, and every guardrail (backup, save, restore) fails closed, stopping the caller before anything is destroyed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The synthetic entry's `auth_implementation` could never resolve**
- **Found during:** Task 1 (reading `application_credentials/__init__.py`)
- **Issue:** The plan said `auth_implementation: "google"`, but the credential the seed creates gets the id `slugify("google.<client_id>")`, so an entry pointing at `"google"` would stay `setup_error` after the credential exists.
- **Fix:** `live_google.py` builds the entry with `homeassistant.util.slugify("google.<client_id>")`, which is what a real sign-in stores.
- **Files modified:** `tools/seed/tests/live_google.py`
- **Verification:** `setup_error` before the credential, `loaded` after (live).
- **Committed in:** `c8cb15d`

**2. [Rule 2 - Missing Critical] `application_credentials/create` does not exist on an instance with no Google entry**
- **Found during:** Task 1
- **Issue:** The application_credentials component is only loaded once Google is set up or a Google flow starts, so on the very first run the seed could not create the credential and the developer would have had to paste the client secret into the UI.
- **Fix:** `ensure_credential` falls back to starting (and closing) a Google config flow, which loads the component, then creates the credential. `link` still ends with the sign-in instruction because no entry exists.
- **Files modified:** `tools/seed/google.py`
- **Verification:** `LiveGoogleNoEntryTests` (credential created, exit 1 with the instruction).
- **Committed in:** `c8cb15d`

**3. [Rule 3 - Blocking] Family file had to accept the google block in Task 1**
- **Found during:** Task 1
- **Issue:** The live test needs a family file with a google block, but full validation is Task 2's TDD work and the plan 02-05 refusal blocked everything.
- **Fix:** Task 1 lifted the refusal with a minimal check (client id, secret, calendars is a list) and replaced the "needs plan 02-08" test; Task 2 wrote the full validation test-first.
- **Files modified:** `tools/seed/family_file.py`, `tools/seed/tests/test_family_file.py`
- **Committed in:** `c8cb15d`, then `187abed`

**4. [Rule 1 - Bug] First-run order would have locked the developer out**
- **Found during:** Task 2 (writing GOOGLE.md section 4)
- **Issue:** With the Google link right after bootstrap, the first run (no sign-in yet) stopped before the accounts existed, so there was no developer account to sign in to Home Assistant with.
- **Fix:** In seed, `ensure_users` and `ensure_todo_lists` run before the Google setup; Google is still ahead of the Family Hub entry and the member calendars, which is what the plan needs.
- **Files modified:** `tools/seed/__main__.py`
- **Committed in:** `187abed`

### Interpretations and small additions

- **Save and restore skip inside the seed commands**, not in shell: `google-save --stdin` always consumes stdin, then does nothing without a google block; `google-restore --stdout` prints nothing in that case, and the shell skips the write when the output is empty.
- **`google-link`, `google-save`, `google-restore` take `--family`** (so tests can pass a family file); `backup-calendars` also takes `--backups-dir` (default `dev/.ha-backups`).
- **Step numbers of `deploy-preview` moved by one** after the new backup step; the existing stub tests were updated (`step 3`, `step 5`, `step 7`) and every reset, deploy and refresh test now counts the backup call.
- **The stub `docker` in `test_scripts.py`** now only wipes when the command contains `rm -rf`, and plays the read-only `cat` container and the restore writer.
- **`entries.calendar_slots` takes the Google slots as a third argument** instead of computing them, so it stays free of Home Assistant calls.
- **`_cmd_refresh` sits after the Google commands** in `__main__.py` because an older refresh test slices the source from `_cmd_refresh` to `COMMANDS`.
- **The acceptance grep** `git grep -nE 'apps\.googleusercontent\.com' -- ':!tools/seed/tests'` prints one line: the plan file itself, which quotes the fake test client id. No source, script or doc outside the tests carries a client id.
- **`grep -c fh_backup_calendars scripts/lib.sh`** prints 4 (header comment, definition, the call in `fh_reset_env`, and a comment); the test asserts exactly one definition and one call per script.

---

**Total deviations:** 4 auto-fixed (2 bugs, 1 missing critical, 1 blocking), plus the interpretations above
**Impact on plan:** All fixes support the plan's own truths (a sign-in that loads, a first run that works, an instruction instead of a half-seeded instance). No scope creep.

## Issues Encountered

- The worktree harness refuses compound shell commands (`&&`, `;`, subshell loops) and `sleep`, so gates and commits ran as separate plain commands and long live runs went to the background with a log file.
- Not exercised, and recorded honestly: any contact with real Google (the OAuth sign-in, the real secret iCal fetch, real calendar entities), and every Docker path (`docker run ... cat` and the restore writer exist only as stubs). The entity selection against real Google entities is proven only against a fake registry. These are the plan 02-09 laptop checkpoint (assumptions A9, A11, A12 included).

## Known Stubs

None. (`backup.py` and the Google selection functions began as RED placeholders and were replaced in their GREEN commits.)

## Threat Flags

None beyond the plan's threat model. T-02-15 is mitigated by the backup-first hook with a hard stop proven by the stub orchestration test; T-02-16 by 0600 files under git-ignored `dev/.ha-*`, no temporary file for the restored entry, and the address never printed (test asserts the output); T-02-17 by exact unique_id selection, writable plus expect_events slots, and HA's own read-only rule; T-02-18 by `link` turning `setup_error` or reauth into the instruction; T-02-SC held: nothing was installed (the orchestrator's pins were already in the harness venv).

## User Setup Required

None for this plan's code. The real Google Cloud project, OAuth client and first sign-in are the developer's own steps, written up in `dev/GOOGLE.md` and carried out at the plan 02-09 checkpoint.

## Next Phase Readiness

- Plan 02-09 runs the real thing on the laptop: create the project and client (`dev/GOOGLE.md` sections 1 to 3), the first sign-in per environment (section 4), check A9 (tokens do not die weekly), A11 and A12 (feed freshness, single-event import with a throwaway calendar), a reset that keeps the sign-in, and the secret iCal fetch.
- Plan 02-10 can rely on `family.google`, `google_slots` and `member_calendars` for the week she sees.
- No blockers.

## Self-Check: PASSED

- All created files exist on disk (`tools/seed/google.py`, `tools/seed/backup.py`, `dev/GOOGLE.md`, `live_google.py`, `test_google.py`, `test_backup.py`).
- Commits `c8cb15d`, `932856f`, `187abed`, `5a81ff5`, `acc76dc` are on this branch after `038e518` (`git log` shows exactly these five).
- Acceptance re-run: Task 1 gate (8 live tests, `bash -n scripts/lib.sh`), Task 2 gate (unit suite and `google_md_missing []`), Task 3 gates (unit suite, `bash -n` on five scripts, `grep -q 'Restore an event from a backup'`, all 54 live tests) all exit 0; `grep -c ical_secret_url tools/seed/backup.py` prints 1 and the test asserts the address never appears in output; `git status --porcelain` is clean.

---
*Phase: 02-dev-family-preview*
*Completed: 2026-11-04*
