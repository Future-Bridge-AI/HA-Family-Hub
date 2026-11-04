---
phase: 01-clean-foundation
plan: 05
subsystem: infra
tags: [hassfest, hacs, github-actions, validation, home-assistant, baseline]

requires:
  - phase: 01-clean-foundation
    provides: "01-01 hassfest harness and triage; 01-02 port commits (none needed); 01-03 validate.yml and versions.env; 01-04 credit lines; 01-06/01-07 translation layout and backup removal"
provides:
  - "01-VALIDATION-BASELINE.md: local hassfest prediction (HA 2026.10.4), HACS prediction from live metadata, the authoritative hosted Validate run 40422777272, and a per-ID Differences table"
  - "Stable Phase 3 fix list: HF-01..HF-04, HF-W01, HACS-01..HACS-03, HACS-W01"
  - "Manual repo-settings steps (D-23) and out-of-scope notes for Phase 3"
  - "Phase 1 success-criteria sweep: every Phase 1 check passes together on the finished tree"
  - "PROJECT.md records that no Home installation exists yet; a future Home install must meet the 2024.12.0 minimum"
affects: [phase-02-preview, phase-03-safety-net, CI-03, CI-04]

actuals:
  tokens: 3800
  tasks: 3
  commits: 2

plan_head_before: c2571b071b0b51a19f7f653ac822c3c9d55cabfe
plan_head_after: 6c2f019240ba08b2a07b9b356636f71c25d76437
commits: 2

tech-stack:
  added: []
  patterns:
    - "Predicted (local) and authoritative (hosted) validation results kept in separate sections, paired per stable ID in a Differences table"
    - "Hosted run evidence gathered read-only from the unauthenticated public GitHub API (run, jobs, steps, check-run annotations, job logs)"

key-files:
  created:
    - .planning/phases/01-clean-foundation/01-VALIDATION-BASELINE.md
  modified:
    - .planning/PROJECT.md

key-decisions:
  - "FOUND-09 is satisfied by hosted Validate run 40422777272 (head bd8de7a, push on ccr-ab9176f1-jbs2rg): both validator steps executed, both jobs concluded failure, as expected for a baseline"
  - "No Home Assistant installation exists yet (developer, 2026-10-27): PROJECT.md records 'none yet' instead of a version; the first fork release v2.0.0 will be a fresh install, and any Home install must be HA >= 2024.12.0"
  - "Hosted failures match the prediction one for one (9 IDs, 0 hosted-only); the HACS images rule is predicted-only because hacs/action did not run it for this integration"
  - "Nothing fixed: HF-02 fh_ui (D-09) and HACS-03 LICENSE detection (D-16) recorded only; Issues, topics and LICENSE left unchanged"

patterns-established:
  - "Failure IDs: HF-NN for hassfest, HACS-NN for HACS, W in the number for warnings, listed in validator order"

requirements-completed: [FOUND-09]

coverage:
  - id: D1
    description: "Local hassfest (HA 2026.10.4) and HACS predictions recorded with stable IDs in validator order, plus manual repo-settings steps and out-of-scope notes"
    requirement: FOUND-09
    verification:
      - kind: other
        ref: "Task 1 gate 1 (hassfest on index export + baseline heading/token check) exited 0 at commit bd8de7a"
        status: pass
    human_judgment: false
  - id: D2
    description: "Phase 1 success-criteria sweep: served-path contract, nine-language parity, no bytecode/Screenshots/.bak/extra root files, credit-only upstream mentions, no runtime file changed against bc7e90c, versions.env and validate.yml present"
    requirement: FOUND-09
    verification:
      - kind: other
        ref: "Task 1 gate 2 (Phase 1 sweep) exited 0 at HEAD c2571b0; results tabled in 01-VALIDATION-BASELINE.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "Authoritative hosted run 40422777272 recorded: run URL, head commit, one conclusion line per job, verbatim failure lines, failure table and per-ID Differences table; no HOSTED-RUN-PENDING placeholder left"
    requirement: FOUND-09
    verification:
      - kind: other
        ref: "Task 3 gate 2 (public API): run_ok True, executed_ok True"
        status: pass
      - kind: other
        ref: "Task 3 gate 1 baseline clauses (order, no placeholder, run URL, both job lines, HF/HACS IDs, Differences) all True; the PROJECT.md 'Home runs Home Assistant YYYY.M' clause is False by design (no Home install exists, see Deviations)"
        status: pass
    human_judgment: false
  - id: D4
    description: "PROJECT.md records Home's Home Assistant situation against the 2024.12.0 minimum (no installation yet; future install must meet it)"
    requirement: FOUND-09
    verification: []
    human_judgment: true
    rationale: "The plan's regex expects a running Home version, which does not exist; the developer should confirm the 'none yet' wording is the record they want"

duration: 7h 43m wall clock (includes the Task 2 checkpoint wait; active work about 20 min)
completed: 2026-10-27
status: complete
---

# Phase 1 Plan 05: Validation Baseline Summary

**First hosted Validate run (40422777272, head bd8de7a) recorded as the authoritative hassfest and HACS baseline: both jobs executed and failed, with HF-01 to HF-04, HF-W01, HACS-01 to HACS-03 and HACS-W01 matching the local HA 2026.10.4 prediction one for one, and no Home installation yet**

## Performance

- **Duration:** 7h 43m wall clock, most of it waiting at the Task 2 checkpoint; active work about 20 min
- **Started:** 2026-10-26T23:50:00Z
- **Completed:** 2026-10-27T07:33:00Z
- **Tasks:** 3 (Task 1 tracer, Task 2 developer checkpoint, Task 3)
- **Files modified:** 2

## Accomplishments

- **Hosted run:** https://github.com/Future-Bridge-AI/HA-Family-Hub/actions/runs/40422777272 (Validate, run 8, `push` on `ccr-ab9176f1-jbs2rg`, head `bd8de7a6cfed4b39c7e781e5d23a832103a7d2bf`, 2026-10-26)
  - Job hacs (HACS validation): failure. Step `Run hacs/action@main` executed; result `3/10 checks failed`.
  - Job hassfest (hassfest): failure. Step `Run home-assistant/actions/hassfest@master` executed; result `Invalid integrations: 1`.
- **Failure IDs for Phase 3 (CI-03):**
  - hassfest: HF-01 manifest key order, HF-02 `fh_ui` not a valid option in `translations/en.json`, HF-03 and HF-04 `grocy_url` strings contain a URL, HF-W01 CONFIG_SCHEMA warning.
  - HACS: HACS-01 issues disabled, HACS-02 no topics, HACS-03 license not identified (SPDX NOASSERTION), HACS-W01 no integration categories.
- **Differences:** every predicted ID was reproduced by the hosted run, and there are 0 hosted-only failures. The HACS `images` rule shows up only in the prediction, because the hosted integration run did not execute it.
- **Phase 1 sweep:** every Phase 1 success check passes together on the finished tree.
- **Home HA version:** there is no Home installation yet (hardware not chosen). PROJECT.md records this. Any future Home install must be at least 2024.12.0, and v2.0.0 will be a fresh install.

## Task Commits

1. **Task 1 (tracer): Reproduce validation locally and record the predicted baseline** - `bd8de7a` (docs)
2. **Task 2: Developer enables Actions and lets Validate run once** - no commit (checkpoint: human-action). The developer enabled Actions and the push of `bd8de7a` triggered run 40422777272.
3. **Task 3: Record the hosted run as the authoritative baseline and note Home's HA version** - `6c2f019` (docs)

**Plan metadata:** recorded in the SUMMARY and state commits that follow.

## Files Created/Modified

- `.planning/phases/01-clean-foundation/01-VALIDATION-BASELINE.md` - created in Task 1 (local prediction, HACS prediction, manual steps, out-of-scope notes, sweep). Task 3 filled the Hosted run and Differences sections.
- `.planning/PROJECT.md` - Context bullet "Home HA version: none yet". The Platform constraint and the HA-versions decision rationale are reworded because no Home install exists yet.

## Decisions Made

- The run counts as FOUND-09 evidence. Both validator steps executed (concluded failure, not skipped or cancelled), and `head_sha` is an ancestor of HEAD.
- Every hosted line was taken from the public API without authentication: run, jobs, steps, check-run annotations and job logs. The developer pasted no lines. Only validator lines and check names were copied, never full logs (T-01-16).
- The two GitHub runner annotations (Node.js 20 deprecation on `actions/checkout@v4`, the ubuntu-latest migration notice) are listed under "Runner notices" without a failure ID, for the Phase 3 action-pinning work.

## Deviations from Plan

### Gate clause not satisfiable as written

**1. [Rule 1 - Plan assumption] PROJECT.md records "no Home installation yet" instead of "Home runs Home Assistant <version>"**
- **Found during:** Task 3 (developer reply to the Task 2 checkpoint)
- **Issue:** Task 3 step 6 and gate 1 expect `Home runs Home Assistant YYYY.M`. The developer reported that no Home Assistant installation exists yet: hardware is not chosen, and the build happens in Dev first with Home installed later. Writing a version would record something false.
- **Fix:** The PROJECT.md bullet now reads `**Home HA version:** none yet — no Home installation exists ...`, and it states that any Home install must meet the 2024.12.0 minimum. The Platform constraint and the HA-versions decision rationale no longer claim an existing Home install. Baseline manual step 7 is reworded to match.
- **Verification:** All baseline clauses of gate 1 print True: order, no placeholder, run URL, both job lines, HF/HACS IDs, Differences. Only the PROJECT.md regex prints False. A substitute check (`grep 'Home HA version:\*\* none yet'` plus the `2024.12.0` mention) passes. Gate 2 prints `run_ok True` and `executed_ok True`.
- **Committed in:** `6c2f019`

### Minor notes

- The plan's Task 2 instructions suggested an empty trigger commit. None was needed: once Actions was enabled, the normal branch push of `bd8de7a` started the run. `git rev-list --left-right --count HEAD...origin/ccr-ab9176f1-jbs2rg` printed `0 0`, so there was nothing to fast-forward.
- A previous continuation executor wrote the Task 3 edits but hit a usage limit before committing. This executor reviewed them against the live API (jobs, steps and annotations re-read on 2026-10-27), found them correct and committed them unchanged.

---

**Total deviations:** 1 (Rule 1, plan assumption about an existing Home install)
**Impact on plan:** The record stays truthful. FOUND-09 is satisfied by the executed hosted run, and the gate's Home-version clause cannot apply until Home exists.

## Issues Encountered

None. Both jobs failed, as expected for a baseline. Nothing was fixed (Phase 3).

## User Setup Required

These manual repo-settings steps (D-23) are listed in `01-VALIDATION-BASELINE.md`. They are allowed now that the baseline run is recorded:
- Enable Issues and add topics (these fix HACS-01 and HACS-02).
- Confirm the repository description.
- Set Pages source to GitHub Actions.
- Phase 3 decision: canonical GPLv3 LICENSE text (fixes HACS-03).
- When Home is installed, use Home Assistant 2024.12.0 or later.

## Next Phase Readiness

- Phase 1 plans are all summarised. The phase is ready for verification.
- Phase 3 (Safety Net) has a stable fix list (HF-NN / HACS-NN). The hosted hassfest image is unpinned and may add checks later.
- Home does not exist yet. Phase 2 (Preview) and later phases should plan a fresh install rather than an upgrade.

## Self-Check: PASSED

- FOUND: `.planning/phases/01-clean-foundation/01-VALIDATION-BASELINE.md`
- FOUND: commit `bd8de7a` (ancestor of HEAD)
- FOUND: commit `6c2f019` (ancestor of HEAD)
- No `HOSTED-RUN-PENDING` placeholder remains (count 0). `git status --porcelain` was clean after the Task 3 commit.

---
*Phase: 01-clean-foundation*
*Completed: 2026-10-27*
