---
phase: 01-clean-foundation
plan: 02
subsystem: infra
tags: [cleanup, served-paths, cards, panels, home-assistant, hacs]

requires:
  - phase: 01-clean-foundation
    provides: "plan 01-01 per-file D-01 triage record (01-TRIAGE.md), all 14 root .js rows discarded"
provides:
  - "Every card and panel exists only at its served path: 12 files in card/, 2 in panel/"
  - "No tracked .js file remains directly under custom_components/family_hub/"
  - "Served-path contract verified: all 15 f-string integration_dir paths registered in async_setup_entry are tracked files"
affects: [01-04, 01-06, 01-07, phase-03-ci-guard]

actuals:
  tokens: 734359
  tasks: 2
  commits: 1

plan_head_before: 0657e780fe9b323ce76eb8367444588e39688686
plan_head_after: b7353c658a190ea9ff1c3b38da573ededcee2b2e
commits: 1

tech-stack:
  added: []
  patterns:
    - "Deletion-only commit with a fixed subject, gated by a script that parses the StaticPathConfig list and the triage table"

key-files:
  created: []
  modified: []
  deleted:
    - custom_components/family_hub/family-hub-active-timers-card.js
    - custom_components/family_hub/family-hub-chores-card.js
    - custom_components/family_hub/family-hub-goals-card.js
    - custom_components/family_hub/family-hub-my-chores-card.js
    - custom_components/family_hub/family-hub-pantry-card.js
    - custom_components/family_hub/family-hub-recipe-box-card.js
    - custom_components/family_hub/family-hub-rewards-card.js
    - custom_components/family_hub/family-hub-todo-card.js
    - custom_components/family_hub/family-right-now-card.js
    - custom_components/family_hub/family-screensaver-card.js
    - custom_components/family_hub/family-today-card.js
    - custom_components/family_hub/family-week-calendar-card.js
    - custom_components/family_hub/theme-builder-panel.js
    - custom_components/family_hub/theme-selector-card.js

key-decisions:
  - "Acted on the recorded triage outcome without re-deciding it: all 14 rows were discarded, so no port commit was made"

patterns-established:
  - "Triage-first deletion: a file is removed only after a committed per-file review row names its outcome (D-01, D-04)"

requirements-completed: [FOUND-01]

coverage:
  - id: D1
    description: "No stale root-level card or panel .js duplicate remains tracked; each card and panel exists only in card/ or panel/"
    requirement: FOUND-01
    verification:
      - kind: other
        ref: "python3 -B -I served-path contract script (prints: registered 15 missing [] unregistered_js [])"
        status: pass
      - kind: other
        ref: "git ls-files custom_components/family_hub | grep -cE '^custom_components/family_hub/[^/]+\\.js$' (prints 0)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Served card/*.js and panel/*.js are byte-identical to the phase base bc7e90c and no Python module or services.yaml changed, so nothing the family uses on Home changed"
    requirement: FOUND-01
    verification:
      - kind: other
        ref: "Task 1 triage-outcome gate (prints: rows 14 ported [] changed [] foreign [] unported [] syntax [])"
        status: pass
      - kind: other
        ref: "git diff --quiet bc7e90c HEAD -- ':(glob)custom_components/family_hub/*.py' custom_components/family_hub/services.yaml (exit 0)"
        status: pass
    human_judgment: false

duration: 1min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 02: Delete stale root card and panel duplicates Summary

**All 14 stale root-level card and panel `.js` copies removed in one deletion-only commit, leaving card/ and panel/ as the only served copy; no hunk needed porting.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-10-26T23:05:14Z
- **Completed:** 2026-10-26T23:05:52Z
- **Tasks:** 2
- **Files modified:** 14 (all deletions)

## Accomplishments

- Task 1 (tracer) read the Outcome cell of each of the 14 rows in `01-TRIAGE.md`. Every row says `discarded`, so no port was needed and no port commit exists. Ported hunks: none (14 rows discarded).
- Task 2 deleted the 14 root duplicates in a single commit that adds, modifies and renames nothing.
- The served-path contract holds: `registered 15 missing [] unregistered_js []`. All 15 `{integration_dir}/...` paths that `async_setup_entry` registers are tracked, and no stray `.js` is left outside them.
- 14 served files stay tracked (12 under `card/`, 2 under `panel/`), unchanged from `bc7e90c`.

## Task Commits

1. **Task 1 (tracer): Act on every recorded triage outcome before deletion** - no commit. All 14 rows are `discarded`, so the port step has nothing to apply. The gate exits 0 and prints `rows 14 ported [] changed [] foreign [] unported [] syntax []`.
2. **Task 2: Delete the 14 stale root card and panel copies** - `b7353c6` (chore)

**Plan metadata:** recorded in the `docs(01-02): complete stale root duplicate removal plan` commit that follows this file.

## Port commits

Ported hunks: none (14 rows discarded). No served file was touched, so there is no port commit hash to record.

## Files Created/Modified

- Deleted (14): `custom_components/family_hub/family-hub-active-timers-card.js`, `family-hub-chores-card.js`, `family-hub-goals-card.js`, `family-hub-my-chores-card.js`, `family-hub-pantry-card.js`, `family-hub-recipe-box-card.js`, `family-hub-rewards-card.js`, `family-hub-todo-card.js`, `family-right-now-card.js`, `family-screensaver-card.js`, `family-today-card.js`, `family-week-calendar-card.js`, `theme-builder-panel.js`, `theme-selector-card.js` (all under `custom_components/family_hub/`). Together 54,697 lines. `family-right-now-card.js` and `theme-selector-card.js` were byte-identical to their served copies.

## Decisions Made

- Followed the recorded triage outcome exactly. The 01-TRIAGE.md review found the root-only hunks were older implementations (the timer-alarm singleton, hardcoded English labels, inline CSS, retired my-chores body), none a fix missing from the served copy.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The `actuals.tokens` figure (734,359) is chars/4 over the bytes deleted, because the realized diff is deletions only. It is not comparable with the plan's 25,000 estimate, which assumed little text volume.

## Known Stubs

None. This plan only deleted files.

## Threat Flags

None. No new network endpoint, auth path, file access or schema surface was introduced.

## Verification Results

- Served-path contract script: `registered 15 missing [] unregistered_js []` (pass).
- Task 1 triage-outcome gate: exit 0, `changed []` (pass).
- `git ls-files custom_components/family_hub | grep -cE '^custom_components/family_hub/[^/]+\.js$'` prints 0 (pass).
- `git diff --quiet bc7e90c HEAD -- ':(glob)custom_components/family_hub/*.py' custom_components/family_hub/services.yaml` exits 0 (pass).
- The deletion commit lists exactly 14 deleted paths and no added, modified, renamed or copied paths (pass).
- 14 served card and panel `.js` files stay tracked (pass).
- No commit since `bc7e90c` touched served `card/*.js` or `panel/*.js` (pass; there is no `fix(01-02): port root-only hunk from` commit).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 01-06 and 01-07 still own the translation moves, the `.bak_divfix` backup deletion and the truncated root translations and `strings.json`.
- Phase 3 CI-04 will add the invariant guard against stray root `.js` files. It is deferred and not built here.

## Self-Check: PASSED

- Deletion commit `b7353c6` is an ancestor of HEAD.
- All 14 deleted paths are absent from the tree, and the 14 served files exist.

---
*Phase: 01-clean-foundation*
*Completed: 2026-10-26*
