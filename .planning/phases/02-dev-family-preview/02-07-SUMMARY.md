---
phase: 02-dev-family-preview
plan: 07
subsystem: infra
tags: [docker-compose, bash, flock, git-archive, home-assistant, seed-tool, build-stamp, reset, refresh, unittest]

requires:
  - phase: 02-dev-family-preview
    provides: "02-01 seed tool (client, creds, bootstrap, LiveHA), 02-02 scripts/lib.sh and the compose base, 02-03 card build-stamp tokens, 02-05 seed/verify, 02-06 events.sync"
provides:
  - "scripts/deploy-preview <ref> [--what] [--view] [--tap]: git archive export, stamp, swap, start, seed, verify-served, hand-off note"
  - "scripts/reset-preview and scripts/dev-reset [--yes]: typed-confirm reset with a hard no-resurrection check"
  - "scripts/refresh-preview [--yes]: non-interactive daily top-up, event sync, safe notifications, verify"
  - "scripts/preview-down, dev/compose.preview.yaml (familyhub-preview, 0.0.0.0:8124, restart unless-stopped, no source mount)"
  - "scripts/lib.sh: FH_STATE_DIR, FH_HOST_ENV, fh_lock, fh_export_build, fh_swap_integration, fh_confirm, fh_wipe_dir, fh_wipe, fh_reset_env"
  - "tools/seed/deploy.py (verify_served, handoff_note) and seed commands verify-served, note, refresh; seed and refresh both run events.sync(apply=True)"
affects: [02-08, 02-09, 02-10]

# Actuals (#2632): chars/4 over the 17 files changed (134926 bytes, whole-file size)
actuals:
  tokens: 33700
  tasks: 3
  commits: 5
plan_head_before: 2a38de571f8cc3481f2127956274c35cc1fcfc72
plan_head_after: 1310c93d1840b94eb3e2aedffe659c1c4d1c76e4

tech-stack:
  added: []
  patterns:
    - "One flock per environment (dev/.ha-locks/ENV.lock, fd 9) shared by deploy, reset and refresh; a second run exits 1 before touching anything"
    - "Export from a resolved commit with git archive, stamp only the exported card, swap in only after export and stamping succeeded, delete the previous copy only after the served check"
    - "Wipe through a throwaway container of the pinned image, then fail hard if .storage or family_hub_backups survive, so a half-finished wipe never reaches the restart"
    - "Stub docker + stub seed command log every call to one file, so script call order is asserted without a Docker daemon"
    - "FH_STATE_DIR and FH_HOST_ENV redirect every .ha-* path and the host settings, so tests never touch the real dev/ state"

key-files:
  created:
    - dev/compose.preview.yaml
    - scripts/deploy-preview
    - scripts/reset-preview
    - scripts/dev-reset
    - scripts/refresh-preview
    - scripts/preview-down
    - tools/seed/deploy.py
    - tools/seed/tests/test_deploy.py
    - tools/seed/tests/test_scripts.py
    - tools/seed/tests/test_refresh.py
    - tools/seed/tests/test_onboard_after_reset.py
    - tools/seed/tests/live_preview.py
  modified:
    - scripts/lib.sh
    - tools/seed/__main__.py
    - tools/seed/entries.py
    - tools/seed/bootstrap.py
    - tools/seed/tests/live_ha.py

key-decisions:
  - "fh_export_build extracts to OUT/custom_components/family_hub and writes OUT/fh-build.env; fh_swap_integration moves that directory into .ha-ENV/custom_components/family_hub and parks the live copy in $FH_DEPLOY_WORK/previous"
  - "deploy-preview reports failures from an EXIT trap rather than an ERR trap, because fh_die exits explicitly and an ERR trap would miss it"
  - "A failure after stop but before the swap restarts the previous copy; a failure after the swap keeps the previous copy in the work dir and says which copy is live"
  - "The wipe is fh_wipe_dir DIR (so the live harness can call it on its own config dir) and fh_wipe ENV is a one-line wrapper"
  - "refresh uses ensure_users and ensure_local_calendars (create-if-missing only) to get the ids it needs, and otherwise only the plan's steps; it has no code path to a stop, wipe or delete"
  - "verify-served trusts substring checks on the served build line plus the resource hashes against the files on disk, as the plan says; it does not hash the served body"

patterns-established:
  - "Pattern: every destructive script carries the D-08 hook comment at the point plan 02-08 will add the Google calendar backup, and a test asserts the exact text in lib.sh, deploy-preview and refresh-preview"
  - "Pattern: a typed confirm is tested through a real pty, and anything but the exact word stops with no docker call"

requirements-completed: [PREV-01, PREV-05, PREV-06, PREV-07, DEV-03, ACCESS-05]

coverage:
  - id: D1
    description: "deploy-preview exports the resolved ref with git archive, fills the three build tokens in the exported card only, swaps it in after export and stamping, starts Preview, seeds, proves the served card carries the full stamp and every resource ends in ?v=<hash of the file>, and prints the hand-off note"
    requirement: PREV-05
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_preview.py LiveDeployTests (verify-served on a real HA running the exported copy; wrong stamp exits 1)"
        status: pass
      - kind: unit
        ref: "tools/seed/tests/test_deploy.py ExportBuildTests and test_scripts.py DeployTests (call order, swap, previous copy removed only at the end)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Idempotency and failure behaviour of deploy: the same ref twice gives the same version and hash with a newer time and one resource per card path; an unknown ref changes nothing; a failed served check never prints the ready line and keeps the previous copy; a failure before the swap restarts the previous copy"
    requirement: PREV-07
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_preview.py LiveDeployTests.test_g_deploying_the_same_commit_again_keeps_one_resource_per_card_path"
        status: pass
      - kind: unit
        ref: "tools/seed/tests/test_scripts.py DeployTests (unknown ref, failed served check, failure before swap, same ref twice with stubbed time)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Hand-off note: UI-SPEC S6 shape, every line at most 72 Unicode code points, one sentence for what changed, exact fallbacks when no note or no screen is given, U+00B7 separator"
    requirement: ACCESS-05
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_deploy.py HandoffNoteTests (13 tests, including a 200-character note, a 300-character word and code points versus bytes)"
        status: pass
    human_judgment: true
    rationale: "Whether the note reads naturally to her when the developer passes it on is a judgment; the shape and limits are tested"
  - id: D4
    description: "One flock shared by deploy, reset and refresh: a second run while one holds it exits 1 with 'Preview is busy' before logging any docker call"
    requirement: PREV-07
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_scripts.py (ResetTests, DeployTests, RefreshTests lock cases, using a real fcntl.flock on dev/.ha-locks/preview.lock)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Preview and Dev side by side: compose projects familyhub-preview and familyhub-dev, config dirs dev/.ha-preview and dev/.ha-dev, host ports 0.0.0.0:8124 and 127.0.0.1:8130, Preview restarts unless-stopped and mounts no source tree"
    requirement: PREV-01
    verification:
      - kind: other
        ref: "docker compose config rendering of both overlays asserted by the Task 1 gate (preview_compose_ok True)"
        status: pass
    human_judgment: true
    rationale: "Starting both containers and reaching Preview from her phone needs Docker and the laptop; checked at the plan 02-09 laptop checkpoint"
  - id: D6
    description: "reset-preview and dev-reset ask 'This will erase all Preview data and re-seed it. Type PREVIEW to continue:' (DEV for Dev), accept --yes, refuse without a terminal and without --yes, run down, wipe, up, seed in that order, and stop before the restart when .storage or family_hub_backups survive"
    requirement: PREV-06
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_scripts.py ResetTests (16 cases including a real pty and a half-finished wipe)"
        status: pass
    human_judgment: false
  - id: D7
    description: "After a reset none of her earlier data comes back: a canary reward and a ticked chore are gone, family_hub_backups and .storage are absent before the restart, and the catalog, balances and chores equal a fresh seed; her stored login still works"
    requirement: PREV-06
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_preview.py LiveResetTests (real HA: seed, mutate, stop, lib.sh wipe, re-render, start, seed)"
        status: pass
    human_judgment: false
  - id: D8
    description: "refresh-preview tops up content and syncs events without wiping, re-applies safe notification settings after a Companion device registered, ends with verify, exits non-zero with 'Preview is not running' when Preview does not answer, and its second run keeps the very same calendar events"
    requirement: PREV-07
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_preview.py LiveRefreshTests (tagged events after seed, same event uids after refresh, canary survives, fake mobile_app device removed from notify targets)"
        status: pass
      - kind: unit
        ref: "tools/seed/tests/test_scripts.py RefreshTests and test_refresh.py (never stops or wipes, order, lock, not-running message)"
        status: pass
    human_judgment: false
  - id: D9
    description: "The real Docker path of every script (compose up/down, the wipe in the pinned image as root-owned files, the seed in a throwaway container with --network host) and a real phone reaching Preview"
    verification: []
    human_judgment: true
    rationale: "No Docker daemon in this sandbox: the docker paths are proven only by stub orchestration and compose config. The live run is the plan 02-09 laptop checkpoint"

# Metrics
duration: 22 min
completed: 2026-11-04
status: complete
---

# Phase 02 Plan 07: Deploy, Reset and Refresh Preview Summary

**`deploy-preview <ref>` puts a committed ref on Preview with a stamped card and proves HA serves it, `reset-preview` and `dev-reset` bring back the starting week with a hard check that no old data survives the wipe, and `refresh-preview` keeps the week current under one shared flock without ever wiping, with the 02-06 event sync wired into seed and refresh.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-11-04T00:30:00Z
- **Completed:** 2026-11-04T00:52:00Z
- **Tasks:** 3 (1 tracer, 2 TDD auto)
- **Files modified:** 17 (12 created, 5 modified)
- **Final runs:** 236 unit and stub tests OK in 4 s; all live modules (`live_*.py`, 46 tests, none skipped) OK in 160 s on HA 2026.10.4; `docker compose config` renders both overlays

## Accomplishments

- **deploy-preview**: resolves the ref first (an unknown ref fails before Preview is touched), exports with `git archive`, checks each build token occurs exactly once, substitutes them in the exported card only, stops Preview, swaps the new copy in, starts, seeds, runs `verify-served` and prints the hand-off note. Failures print `deploy-preview failed at step N (<name>)`, never the ready line, and say which copy is live. The previous copy is deleted only after the served check.
- **verify-served**: the served card's `const __FH_BUILD` line must carry the stamp's three parts, `__FH_BUILD_VERSION__` must be gone, and every card resource must be `?v=<sha256(file)[:10]>` with one row per path.
- **Reset**: typed `PREVIEW` or `DEV` (tested through a real pty), `--yes` for the scheduler, refusal without a terminal; `down`, wipe in the pinned image (keeping only `custom_components`), template config back, `up -d`, seed. A wipe that leaves `.storage` or `family_hub_backups` stops the reset before the restart. Live canary test: a reward and a ticked chore are gone afterwards and her stored login works.
- **Refresh**: wait with a plain "Preview is not running - refresh skipped (is WSL/Docker up?)", then identity, outbound entries, content top-up, event sync, safe notifications and verify. A second refresh keeps the very same calendar events (same uids). A fake Companion device registered on Preview and set as Jordan's notify target makes verify fail, and the next refresh clears it.
- **One lock**: deploy, reset and refresh share an flock on `dev/.ha-locks/preview.lock`; the stub tests hold it with `fcntl.flock` and see exit 1, "Preview is busy" and no docker call.

## Example hand-off note (printed by `python -m tools.seed --target preview note`)

With a note, a screen and a tap:

```
Preview is updated and ready for you to try.

What changed:  Chores now show how many stars each one is worth.
Where to look: Open Family Hub PREVIEW, tap Chores, then the first chore
                 on Riley's list.
Check it is new: the small line at the bottom of the Calendar should say
                 "Preview · 2.0.0+2a38de5 · 4 Nov 14:05".
```

With nothing given (the deploy still succeeds):

```
Preview is updated and ready for you to try.

What changed:  (no note was given - tell her what changed yourself)
Where to look: Open Family Hub PREVIEW.
                 (no screen was given - tell her where to tap yourself)
Check it is new: the small line at the bottom of the Calendar should say
                 "Preview · 2.0.0+2a38de5 · 4 Nov 14:05".
```

## Task Commits

1. **Task 1 (tracer): deploy-preview from branch to a stamped, verified Preview with the hand-off note** - `f07b09a` (feat)
2. **Task 2: reset-preview and dev-reset (TDD)**
   - RED: `a8cacc5` (test) - 16 assertion failures in `test_scripts.py` against exit-0 stubs and 4 assertion failures in the live canary test against a missing `fh_wipe_dir`
   - GREEN: `1876a0e` (feat)
3. **Task 3: refresh-preview and events wired into seed and refresh (TDD)**
   - RED: `53f3b92` (test) - 12 assertion failures against stubs, plus 3 live assertion failures (no events line, no refresh output, notify target not cleared)
   - GREEN: `1310c93` (feat)

**Plan metadata:** the `docs(02-07)` commit that adds this file.

Tracer feedback gate: auto mode with an automated-only `<verify>`; all three Task 1 gates (compose render and assertions, unit suite, `live_preview.py`) were run after the Task 1 commit and passed, so expansion went ahead ("Tracer verified end-to-end - expanding").

## TDD Gate Compliance

RED (`test(02-07)`) precedes GREEN (`feat(02-07)`) for Tasks 2 and 3. RED evidence is the real unittest output run against stubs with the real signatures (an exit-0 script, `calendar_slots` returning `[]`, a placeholder `refresh` command), so the target tests loaded and failed on their planned assertions, not on missing files. The `gsd_run check tdd-red-evidence` classifier was not run (no `gsd_run` in this sandbox); the semantic assessment was made by reading each failure. Task 1 is a tracer, not TDD; its tests were written with the code. No REFACTOR commits.

## Files Created/Modified

- `dev/compose.preview.yaml` - Preview overlay: `restart: unless-stopped`, `${PREVIEW_BIND:-0.0.0.0}:8124:8123`, `./.ha-preview:/config`, no source mount
- `scripts/lib.sh` - new helpers (lock, export and stamp, swap, typed confirm, wipe, reset); `FH_STATE_DIR` and `FH_HOST_ENV` now drive every path
- `scripts/deploy-preview`, `scripts/preview-down`, `scripts/reset-preview`, `scripts/dev-reset`, `scripts/refresh-preview` - thin wrappers over lib.sh
- `tools/seed/deploy.py` - `verify_served`, `check_served_card`, `handoff_note`, `parse_stamp`
- `tools/seed/__main__.py` - commands `verify-served`, `note`, `refresh`; `seed` now syncs events
- `tools/seed/entries.py` - `calendar_slots`
- `tools/seed/bootstrap.py` - post-reset onboarding race fix (see Deviations)
- `tools/seed/tests/test_deploy.py`, `test_scripts.py`, `test_refresh.py`, `test_onboard_after_reset.py`, `live_preview.py`, `live_ha.py` - tests (`live_ha.py` gains `wipe_config`, `rerender_config`)

## Decisions Made

See `key-decisions` above. The two worth repeating: a failure between the stop and the swap restarts the previous copy, so a deploy that fails early does not leave her without a Preview; and the reset treats a surviving `family_hub_backups/` as fatal, because the integration restores from it when its stores load empty.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] A restarted, wiped instance could be misread as already onboarded**
- **Found during:** Task 2 (reasoning about the real `up -d` then `seed` sequence after a wipe)
- **Issue:** With credentials already stored (they survive a reset on purpose, D-27), `onboard_if_needed` asked `/api/onboarding` with no settle time, so the 404 HA gives before its onboarding views exist read as "already onboarded" and the seed failed at login on a fresh instance.
- **Fix:** When the answer is 404 and credentials exist, try the stored login; if it fails with an auth error, keep asking for the onboarding steps for up to 30 s.
- **Files modified:** `tools/seed/bootstrap.py`, new `tools/seed/tests/test_onboard_after_reset.py` (3 tests with a fake client)
- **Verification:** unit tests; the live reset test and all other live modules still pass. The race itself could not be reproduced on demand here.
- **Committed in:** `1876a0e`

**2. [Rule 3 - Blocking] Tests needed a way to avoid dev/host.env**
- **Found during:** Task 1
- **Issue:** `fh_load_env` required the real `dev/host.env`, so the script tests could not run without writing there.
- **Fix:** `FH_HOST_ENV` (default `$FH_ROOT/dev/host.env`) next to the plan's `FH_STATE_DIR`; `fh_compose` and `fh_seed` use it too. Behaviour with neither variable set is unchanged.
- **Files modified:** `scripts/lib.sh`
- **Committed in:** `f07b09a`

### Interpretations and small additions

- **Failure reporting uses an EXIT trap, not an ERR trap**, because `fh_die` exits explicitly and an ERR trap would not see it. Same output (step number and name on stderr, no ready line).
- **`fh_wipe_dir DIR` plus `fh_wipe ENV`** instead of only `fh_wipe ENV`, so `LiveHA.wipe_config()` runs the very same helper on the harness config directory.
- **`refresh-preview` calls `fh_seed preview --timeout 300 wait`** (global option before the subcommand), because the `wait` subcommand has no `--timeout` of its own.
- **Event line wording:** the real line is `events: create 0, delete 0, keep N (applied)`; the plan's behaviour text omitted `keep N`. The live test asserts the real line.
- **refresh** also runs `ensure_users` and `ensure_local_calendars` (both create only what is missing) to obtain the user and calendar ids that content and events need, and retries login or connection errors for up to two minutes while HA is still starting (a refresh may run right after Docker restarted Preview).
- **A failure after stop but before the swap restarts the previous copy** (not in the plan); covered by a stub test that makes the swap fail.
- **Extra tests:** a live same-commit redeploy (one resource per path), the live fake-Companion case, `test_refresh.py`, and the stub `docker` simulating the throwaway container so the wipe really deletes in the order test.
- **RED stubs** (`reset-preview`, `dev-reset`, `refresh-preview`, `calendar_slots`, a placeholder `refresh` command) were committed with the RED tests so the targets failed on assertions; each was replaced in the GREEN commit.

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking), plus the interpretations above
**Impact on plan:** Both fixes support the plan's own truths (same logins after reset, tests that never touch the real dev/ state). No scope creep.

## Issues Encountered

- The worktree harness refuses compound git and `bash -c` commands, so the live gates and commits ran as separate plain commands and the script-level checks ran through Python test files.
- Docker cannot run here. Not exercised, and recorded honestly: `docker compose up/down` against a real daemon, the wipe in the pinned HA image on root-owned files (research assumption A2), `fh_seed`'s `docker run --network host`, WSL keep-alive, and a phone reaching port 8124. These are the plan 02-09 laptop checkpoint.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. T-02-12 is mitigated by `git archive` of a resolved commit and `verify-served`; T-02-13 by the loopback-only Dev port, the documented `preview-down` and the generated passwords (the Windows firewall rule is plan 02-09); T-02-14 by the pinned-image wipe, the survivor check, the single flock and the swap-after-stamp order, all covered by tests; T-02-SC held: nothing was installed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-08 adds the Google calendar backup and sign-in preservation at the three marked hook points (`fh_reset_env`, `deploy-preview` after its lock, `refresh-preview` after its lock), and Google calendars into `entries.calendar_slots` with their writable flag. Until then `family_file.py` refuses a `google` block, so no Google-connected instance can reach those lines.
- Plan 02-09 runs the real Docker paths on the laptop: `scripts/dev-up`, `deploy-preview`, `reset-preview`, `refresh-preview` as scheduled tasks, and checks whether her phone needs to sign in again after a reset (D-27).
- No blockers.

## Self-Check: PASSED

- All 12 created files and 5 modified files exist on disk; the five scripts are mode 100755.
- Commits `f07b09a`, `a8cacc5`, `1876a0e`, `53f3b92`, `1310c93` are ancestors of HEAD.
- Acceptance re-run: all three Task gates exit 0; `grep -c '__FH_BUILD_ENV__'` on the repo card prints 1; `grep -c 'Type PREVIEW to continue:' scripts/lib.sh` prints 1; `grep -c 'events.sync(' tools/seed/__main__.py` prints 2; `grep -cE 'compose (preview |\$ENV )?down|fh_wipe' scripts/refresh-preview` prints 0; `git status --porcelain` lists no dev/.ha-* or temp paths.

---
*Phase: 02-dev-family-preview*
*Completed: 2026-11-04*
