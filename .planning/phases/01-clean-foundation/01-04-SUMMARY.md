---
phase: 01-clean-foundation
plan: 04
subsystem: infra
tags: [versioning, hacs, home-assistant, versions-env, semver]

requires:
  - phase: 01-clean-foundation
    provides: "plan 01-03 set the fork identity values (codeowners, documentation, issue_tracker) in manifest.json"
provides:
  - "versions.env: single source of pinned HA 2026.10.4, Python 3.14, pytest-homeassistant-custom-component 0.13.375 and minimum HA 2024.12.0"
  - "hacs.json homeassistant minimum 2024.12.0 (first release with every API the code imports)"
  - "Fork version scheme decided and recorded: starts at 2.0.0, tags vX.Y.Z equal manifest.json, strictly increasing"
  - "manifest.json version 2.0.0"
affects: [phase-02-dev-preview, phase-03-tests-ci, phase-04-release-REL-01]

actuals:
  tokens: 2200
  tasks: 3
  commits: 2
plan_head_before: f17ed6d36ead55a58e5b96cb2d80065cb215d4b5
plan_head_after: 64f512fe1fa5c2846126eeac9f2e8a74e51b2e1f

tech-stack:
  added: []
  patterns:
    - "versions.env plain KEY=value file (no export, no quotes) read by later tooling; HA_MIN_VERSION mirrors hacs.json"
    - "Release tag vX.Y.Z must equal manifest.json version; versions strictly increase"

key-files:
  created:
    - versions.env
  modified:
    - hacs.json
    - custom_components/family_hub/manifest.json
    - .planning/PROJECT.md
    - .claude/CLAUDE.md
    - .planning/codebase/STACK.md

key-decisions:
  - "D-19 (developer-confirmed at checkpoint): fork starts at 2.0.0, not 1.169.0"
  - "D-20: versions.env is the single pin source for Dev, Preview and tests"
  - "D-21: hacs.json minimum is 2024.12.0, the verified API floor, never the 2026.10.4 pin"

patterns-established:
  - "One-way version decisions are gated by a blocking decision checkpoint and committed separately so they are revertible on their own"

requirements-completed: [FOUND-07, FOUND-08]

coverage:
  - id: D1
    description: "versions.env records HA_VERSION=2026.10.4, PYTHON_VERSION=3.14, PYTEST_HACC_VERSION=0.13.375, HA_MIN_VERSION=2024.12.0; bash can source it and git does not ignore it"
    requirement: FOUND-08
    verification:
      - kind: other
        ref: "Task 1 automated gate (python3 -B -I json/versions.env check + bash source + git check-ignore) exit 0, versions_ok True"
        status: pass
    human_judgment: false
  - id: D2
    description: "hacs.json minimum is exactly 2024.12.0 and project docs (PROJECT.md, CLAUDE.md, STACK.md) agree with the minimum and the pin"
    requirement: FOUND-08
    verification:
      - kind: other
        ref: "Task 1 automated gate grep counts (no 2024.1 minimum wording left; 2026.10.4 mentions present) exit 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "manifest.json version is 2.0.0 (strictly above 1.168.85) and the PROJECT.md Fork versioning row records v2.0.0 tags, strictly increasing numbers and the HACS GitHub Release need"
    requirement: FOUND-07
    verification:
      - kind: other
        ref: "Task 3 automated gate (python3 -B -I manifest/PROJECT.md check) printed 'version 2.0.0 changed [codeowners, documentation, issue_tracker, version] ok True'"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every future release is strictly greater than the previous one and no published number is reused (enforcement)"
    requirement: FOUND-07
    verification: []
    human_judgment: true
    rationale: "Backstop edge: only enforceable once the Phase 4 REL-01 tag check exists; Phase 1 delivers the recorded scheme only"

duration: 36min
completed: 2026-10-26
status: complete
---

# Phase 01 Plan 04: Version Pins and Fork Version Summary

**Pinned HA 2026.10.4 in versions.env, set the real HACS minimum to 2024.12.0, and started the fork at version 2.0.0 with a recorded strictly-increasing vX.Y.Z tag scheme.**

## Performance

- **Duration:** about 36 min wall clock (includes the wait at the D-19 decision checkpoint)
- **Started:** 2026-10-26T23:10Z (first task commit; plan began slightly earlier)
- **Completed:** 2026-10-26T23:47Z
- **Tasks:** 3 (1 tracer, 1 decision checkpoint, 1 auto)
- **Files modified:** 6 (1 created, 5 modified)

## Accomplishments

- `versions.env` created with the four pins; Phase 2 (Dev/Preview) and Phase 3 (tests/CI) read it instead of hard-coding versions.
- `hacs.json` minimum raised from 2024.1.0 to the verified API floor 2024.12.0 (not the 2026.10.4 pin, so an older Home HA is not blocked from updates).
- PROJECT.md, CLAUDE.md and STACK.md updated to the 2024.12.0 minimum / 2026.10.4 pin wording; new Key Decisions row for the HA versions.
- Fork version scheme confirmed by the developer and recorded: `manifest.json` version `2.0.0`, tags `vX.Y.Z` equal to the manifest, strictly increasing, no reuse. No git tag created.

## Task Commits

1. **Task 1 (tracer): Record pinned and minimum HA versions** - `65c5b8a` (chore)
2. **Task 2: Confirm one-way fork version scheme (D-19)** - checkpoint, no commit; choice recorded below
3. **Task 3: Set confirmed fork version and record scheme** - `64f512f` (chore)

**Plan metadata:** committed with this SUMMARY (docs: complete plan)

## Checkpoint choice

**Task 2 (checkpoint:decision, D-19, gate=blocking): developer selected `fork-2-0-0`.**

- Fork starts at 2.0.0 (rather than continuing upstream numbering at 1.169.0).
- Rationale from the options: strictly above Home's upstream 1.168.85 so HACS sees an upgrade; marks the fork boundary clearly; can never collide with an upstream 1.x number.
- Accepted trade-off: semantic versioning reads 2.0.0 as a breaking change, which this is not; departs from CONTEXT D-19's default of 1.169.0.
- Recorded here before Task 3 ran, as the acceptance criterion requires.

## Files Created/Modified

- `versions.env` - single pin source: HA_VERSION, PYTHON_VERSION, PYTEST_HACC_VERSION, HA_MIN_VERSION
- `hacs.json` - `homeassistant` 2024.1.0 to 2024.12.0
- `custom_components/family_hub/manifest.json` - `version` 1.168.85 to 2.0.0
- `.planning/PROJECT.md` - minimum/pin wording, new HA versions Key Decision, Fork versioning row decided
- `.claude/CLAUDE.md` - mirrored minimum/pin wording
- `.planning/codebase/STACK.md` - same two replacements so a regenerated CLAUDE.md keeps them

## Decisions Made

- **Fork version starts at 2.0.0 (D-19, developer choice `fork-2-0-0`)** - one-way: once Home installs it via HACS, lower or reset numbers read as a downgrade. Tags are `v2.0.0`-style, equal to manifest.json, strictly increasing, and no published number is reused. HACS update detection needs a published GitHub Release (Phase 4 REL-01).
- **versions.env is the single pin source (D-20)** - HA_MIN_VERSION mirrors hacs.json; Phase 3 CI-04 can assert they agree.
- **hacs.json minimum is 2024.12.0 (D-21)** - first release with StaticPathConfig (2024.7), calendar DATA_COMPONENT (2024.10) and the no-arg OptionsFlow `config_entry` (2024.12); supersedes the CONTEXT estimate of about 2024.7.

## Deviations from Plan

None - plan executed exactly as written. The only variation from the plan default is the developer's checkpoint choice (2.0.0 instead of the default 1.169.0), which the plan explicitly offers as an option.

## Issues Encountered

None.

## Known Stubs

None.

## Threat Flags

None. T-01-13 (hacs.json floor) and T-01-14 (one-way version scheme) mitigations applied and gated; T-01-15 accepted (versions.env holds only public pins).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 01-05 and 01-07 can proceed. Note for Phase 4 REL-01: the first release tag must be `v2.0.0`, equal to manifest.json, and published as a GitHub Release so HACS offers the update.
- The semver trade-off (2.0.0 reads as breaking) is accepted by the developer; mention it in the first release notes.

## Self-Check: PASSED

- versions.env, hacs.json, manifest.json, PROJECT.md, CLAUDE.md, STACK.md present on disk.
- Commits 65c5b8a and 64f512f are ancestors of HEAD.
- Task 1 and Task 3 automated gates exit 0; `git tag --list` is empty (no tag created).

---
*Phase: 01-clean-foundation*
*Completed: 2026-10-26*
