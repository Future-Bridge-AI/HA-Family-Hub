---
phase: 02-dev-family-preview
plan: 04
subsystem: planning-docs
tags: [roadmap, requirements, project, google-calendar, preview, scope-change]

requires:
  - phase: 02-dev-family-preview
    provides: "02-CONTEXT.md decisions D-01..D-31 (scope changes D-03 and D-07)"
provides:
  - "ROADMAP, REQUIREMENTS and PROJECT.md consistently describe Preview as laptop-hosted at agreed times"
  - "One calendar story: read/write to a chosen list of real Google calendars with tags, backups and a loud delete confirm"
  - "Phase 2 decisions recorded as made (placement, separate instance, access)"
affects: [02-05, 02-06, 02-07, 02-08, 02-09, 02-10, phase-2-verification]

actuals:
  tokens: 4500
  tasks: 2
  commits: 2
plan_head_before: e9f9463a6b7dd78c3b4d1ba67bf04548870ce471
plan_head_after: d74c1925cf671426e29caf685030f9cc3cb0f119

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/PROJECT.md

key-decisions:
  - "Docs now treat the Google Calendar API as the one accepted cloud exception for Dev and Preview (D-02, D-07)"
  - "Always-on is relaxed to agreed times while Preview lives on the developer's laptop; it returns with a dedicated box (D-03)"
  - "D-07 recorded as a one-way decision: a deleted real event is gone unless restored from the D-08 backup"

requirements-completed: [PREV-01, PREV-03]

duration: 8min
completed: 2026-11-03
status: complete
---

# Phase 2 Plan 04: Reword Preview promises Summary

**ROADMAP, REQUIREMENTS and PROJECT.md now say Preview runs on the developer's laptop at agreed times and connects read/write to a chosen list of real Google calendars, guarded by [PREVIEW] tags, dated .ics backups and a loud delete confirm.**

## Performance

- **Duration:** about 8 min
- **Completed:** 2026-11-03T15:47:36Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Task 1 (tracer): ROADMAP Phase 2 criterion 2, PREV-03, both Out of Scope tables, the Locality and Safety constraints, the Environments Family Preview row, the Active bullet and Key Decisions all tell the same D-07 calendar story. A new Key Decisions row records it as one-way.
- Task 2: ROADMAP overview, phase-list line and criteria 1 and 2 say "agreed times" (D-03, D-28); PREV-01 and the REQUIREMENTS footer match; the "Decisions due" block became "Decisions (made in 02-CONTEXT.md)"; the research line is marked done; the three PROJECT.md Preview-placement rows read "Decided in Phase 2"; the Dev row names `scripts/dev-restart` and `scripts/dev-cards`.
- Both plan gates pass together on the final files (`d07_ok True`, `d03_ok True`, no old phrase left).

## Task Commits

1. **Task 1 (tracer): One calendar story (D-07)** - `1b9dad2` (docs)
2. **Task 2: Preview on the laptop at agreed times, decisions recorded** - `d74c192` (docs)

**Plan metadata:** committed separately after this summary (docs: complete plan)

## Files Created/Modified
- `.planning/ROADMAP.md` - Phase 2 overview, phase-list line, success criteria 1 and 2, decisions block, research line
- `.planning/REQUIREMENTS.md` - PREV-01, PREV-03, two Out of Scope rows, footer
- `.planning/PROJECT.md` - Active bullet, two Out of Scope bullets, Environments rows, Locality and Safety constraints, Key Decisions rows (three decided, one new)

## Decisions Made
None beyond recording the CONTEXT.md decisions (D-01, D-03, D-05, D-06, D-06a, D-07 to D-11, D-16, D-23, D-28) in the project documents.

## Deviations from Plan

None - plan executed exactly as written. Line numbers in the plan's read_first lists were slightly off from the live files; each edit was matched by its exact current text instead, and the verify gates confirm the intended result.

## Issues Encountered
None. Per the worktree rules, only content edits were made to ROADMAP.md; the plan-progress checkboxes and progress table were left for the orchestrator, and STATE.md was not touched. `.claude/CLAUDE.md` (generated mirror of PROJECT.md) was deliberately not edited, so its Locality and Safety text will lag until it is regenerated.

## Known Stubs
None.

## Threat Flags
None. T-02-06 (requirements promising "never the real calendars") is mitigated: all six old phrases are gone and the D-07 and D-03 wording is required by the gates.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The verifier and plans 02-05 to 02-10 now check the agreed behaviour.
- `.claude/CLAUDE.md` still carries the old Locality and Safety constraints until it is regenerated from PROJECT.md.

## Self-Check: PASSED

- FOUND: `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/PROJECT.md`
- FOUND commits: `1b9dad2`, `d74c192`
- Task 1 gate re-run after Task 2: `old_phrases_left [] d07_ok True`; Task 2 gate: `old_phrases_left [] d03_ok True`
- PREV checkbox count still 8; `### Phase` heading count still 4

---
*Phase: 02-dev-family-preview*
*Completed: 2026-11-03*
