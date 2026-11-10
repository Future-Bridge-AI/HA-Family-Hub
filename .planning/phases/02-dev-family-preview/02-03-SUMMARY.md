---
phase: 02-dev-family-preview
plan: 03
subsystem: ui
tags: [lovelace-card, vanilla-js, build-stamp, delete-guard, node-check]

requires:
  - phase: 01-foundation
    provides: served calendar card at card/family-week-calendar-card.js and the family_hub/calendar/delete_support websocket command
provides:
  - "Build stamp footer in the calendar card: 'Preview · <version>+<hash7> · <D Mon HH:mm>' after deploy substitution, 'Dev · live' in Dev, nothing on Home"
  - "Loud second native confirm before deleting a real Google event in Dev or Preview (D-09)"
  - "DOM-free testable helper block (marker comments) plus tools/card-checks/phase2-card-helpers.test.mjs"
affects: [02-07 deploy-preview, 02-08 seed, 02-10 guide]

actuals:
  tokens: 6000
  tasks: 2
  commits: 3
plan_head_before: e9f9463a6b7dd78c3b4d1ba67bf04548870ce471
plan_head_after: 02908949447d5e5f571607a109294cc95ac07ada

tech-stack:
  added: []
  patterns:
    - "Testable helpers: pure functions between __FH_TESTABLE_HELPERS_BEGIN/END marker comments, evaluated by a node script with new Function (no bundler, no package.json)"
    - "Build tokens appear once in source; the unsubstituted test is a regex that contains no full token, so deploy substitution cannot rewrite it"

key-files:
  created:
    - tools/card-checks/phase2-card-helpers.test.mjs
  modified:
    - custom_components/family_hub/card/family-week-calendar-card.js

key-decisions:
  - "Stamp row is a hidden template element that _updateBuildStamp removes from the DOM when the text is empty and re-inserts after .fh-main-layout when the location name later matches, so Home gets no element and no spacing"
  - "Seed-tag exemption is an exact startsWith on '[PREVIEW] ' / '[DEV] ' (case-sensitive, trailing space), so lookalikes still get the warning"

patterns-established:
  - "Additive helpers plus small hooks in the calendar card monolith; no restructuring"

requirements-completed: [PREV-07]

coverage:
  - id: D1
    description: "Build stamp text logic: Dev shows 'Dev · live', Home and near-miss names show nothing, substituted build shows the full Preview stamp, partly substituted build never leaks token text"
    requirement: PREV-07
    verification:
      - kind: unit
        ref: "node tools/card-checks/phase2-card-helpers.test.mjs (stamp checks, including simulated deploy substitution)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Loud delete confirm text and gating (exact S4 copy, google-only, DEV/PREVIEW whole-word, seed-tag exemption, 80 code point truncation) and its position between the existing confirm and the Deleting state"
    verification:
      - kind: unit
        ref: "node tools/card-checks/phase2-card-helpers.test.mjs (warning and structural checks)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Stamp row renders visibly without scrolling on a 360x800 phone and a 1280x800 desktop, wraps rather than truncates, and clears the + button"
    verification: []
    human_judgment: true
    rationale: "Layout in the real HA shadow DOM was not exercised in a browser here (no HA instance or browser available in this run); needs a visual look in Dev"
  - id: D4
    description: "In a real Dev/Preview instance, the second native confirm appears on a Google event delete, cancel at either prompt aborts silently, and Home is unchanged"
    verification: []
    human_judgment: true
    rationale: "Native window.confirm flow against a live Google calendar cannot be asserted by the node check"

duration: 22min
completed: 2026-11-03
status: complete
---

# Phase 2 Plan 03: Build stamp and loud delete confirm Summary

**Calendar card shows a "Preview · version+hash · time" / "Dev · live" stamp row (nothing on Home) and asks a second, loud native confirm before deleting a real Google event in Dev or Preview, proven by a 39-check node script including a simulated deploy substitution.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-11-03T15:27:00Z
- **Completed:** 2026-11-03T15:49:10Z
- **Tasks:** 2 (tracer + TDD auto)
- **Files modified:** 2

## Accomplishments

- Build stamp (D-20, UI-SPEC S3): `__FH_BUILD` object with the three tokens (once each), `__fhBuildStampText`, `.fh-build-stamp` non-scrolling flex row, one `console.info` per page load.
- Loud delete confirm (D-09, UI-SPEC S4): `__fhRealCalendarDeleteWarning` with exact S4 copy, `platform` passed through `_getCalendarDeleteSupport`, second `window.confirm` hooked after the existing one and before `btn.disabled = true`.
- `tools/card-checks/phase2-card-helpers.test.mjs`: 39 checks, no dependencies, reads the card and evaluates only the marker-delimited helper block.

## Code locations (card/family-week-calendar-card.js)

| Piece | Line |
|---|---|
| Helper block (`__FH_TESTABLE_HELPERS_BEGIN`..`END`) | 107-142 (`__FH_BUILD` 108, `__fhBuildStampText` 109, `__fhRealCalendarDeleteWarning` 126) |
| `.fh-build-stamp` CSS | 5687 (plus `b` and `[hidden]` rules just after) |
| `.fh-build-stamp` element (template, after `.fh-main-layout`, before the first modal overlay) | 14539 |
| `_updateBuildStamp` method | 11115 (called from `set hass` at 5926 and at the end of `_build` at 16177) |
| `platform` passthrough in `_getCalendarDeleteSupport` | 13357 (`platform: null` default at 13343) |
| Loud confirm hook in `_wireEventInfoDeleteButton` | 23791-23797 |

## Task Commits

1. **Task 1 (tracer): Build stamp from token to footer** - `138847e` (feat)
2. **Task 2 (TDD): Loud second confirm** - RED `502f80a` (test), GREEN `0290894` (feat); no refactor commit needed

**Plan metadata:** committed separately (docs: complete plan)

## TDD Gate Compliance

- RED: `test(02-03)` `502f80a` added warning, truncation, structural-order and platform-passthrough checks. Run result: exit 1, first target check "warning helper is defined" failed on `typeof` equal to `'undefined'` (expected `'function'`), i.e. the planned helper was missing, not a syntax or load error (semantic assessment: valid RED). The project has no TAP reporter for this script, so `gsd_run check tdd-red-evidence` was not applied; evidence is the real failing run.
- GREEN: `feat(02-03)` `0290894`; script reports 39 checks passed.
- REFACTOR: none.

## Files Created/Modified

- `custom_components/family_hub/card/family-week-calendar-card.js` - helpers, stamp row, platform passthrough, second confirm
- `tools/card-checks/phase2-card-helpers.test.mjs` - node check including simulated deploy substitution

## Decisions Made

- Stamp element ships in the template as `hidden` (no flash of padding before hass), is removed from the DOM when the text is empty, and re-inserted after the main layout if the location name later matches.
- The seed-tag exemption is exact and case-sensitive, so "[PREVIEW]Dentist" and "[preview] Dentist" still warn.

## Deviations from Plan

None - plan executed exactly as written. One small refinement within plan latitude: `isPlaceholder` also treats non-string/empty build values as unsubstituted so a missing field can never print "undefined".

## Issues Encountered

None. The visual check on 360x800 and 1280x800 viewports (UI-SPEC S3) could not be run here (no HA instance or browser in this worktree); recorded as coverage D3 for end-of-phase human verification.

## Verification Results

- `node --check` card: pass. `node tools/card-checks/phase2-card-helpers.test.mjs`: 39 checks passed.
- Counts: each build token 1, `console.info` 1, `console.log` 3 (baseline), `window.confirm(` 18 (baseline 17 + 1), `platform: res.platform` 1, S4 headline 1, `__fhRealCalendarDeleteWarning(` 2, `fh-build-stamp` 5.
- `git diff --quiet ed72072 -- __init__.py translations`: unchanged. No other card or backend file touched.

## Known Stubs

None.

## Threat Flags

None. T-02-04 mitigated by Task 2 (add/edit remain unguarded per UI-SPEC A6, accepted); T-02-05 mitigated (stamp built with `textContent` and a `<b>` element).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-07 (deploy-preview) can substitute the three tokens in the exported copy; the node check proves detection survives substitution.
- Plan 02-08 seeds must name the HA location "Family Hub DEV" / "Family Hub PREVIEW" and tag pretend events `[DEV] ` / `[PREVIEW] `.

## Self-Check: PASSED

- Files exist: card, test script (verified by running both).
- Commits `138847e`, `502f80a`, `0290894` are ancestors of HEAD.

---
*Phase: 02-dev-family-preview*
*Completed: 2026-11-03*
