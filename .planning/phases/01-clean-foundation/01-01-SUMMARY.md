---
phase: 01-clean-foundation
plan: 01
subsystem: infra
tags: [git-hygiene, gitignore, hassfest, triage, bytecode, home-assistant]

requires:
  - phase: none
    provides: first plan of the first phase
provides:
  - "Tracked tree without compiled bytecode (49 .pyc index entries removed)"
  - "01-TRIAGE.md: per-file D-01/D-02 record for all 14 root .js duplicates, root translations, strings.json diff, screenshots, icons and the upstream-sync rule"
  - "Redundant screenshots, unserved icon/logo duplicates and empty readme removed in one commit"
  - ".gitignore protecting HA state, backups and backup files"
  - "Local hassfest harness (HA core 2026.10.4) at $HOME/.cache/fh-hassfest, outside the repo"
affects: [01-02, 01-05, 01-06, 01-07, phase-03-validation]

actuals:
  tokens: 4017
  tasks: 3
  commits: 4

plan_head_before: 57243fc1aba78df4cca307ba0d13cdd2c8c046bc
plan_head_after: ddc34428405518a7c789c886cfcec6e8e4271523
commits: 4

tech-stack:
  added: ["homeassistant==2026.10.4, infrared-protocols==10.1.0, tqdm==4.70.1 (scratch venv at $HOME/.cache/fh-hassfest only, not committed)"]
  patterns:
    - "Validate an index export (git ls-files | checkout-index --work-tree) with HA's own hassfest, never the working copy"
    - "One logical change per commit: untrack bytecode, triage record and hygiene deletions are three separate commits"

key-files:
  created:
    - .planning/phases/01-clean-foundation/01-TRIAGE.md
  modified:
    - .gitignore

key-decisions:
  - "All 14 root .js duplicates are discarded; no hunk is ported (Ported hunks: none). The highest version tag in any root-only line is 1.119.0 (1.132.61 for my-chores), always older than the served copy"
  - "strings.json key diff was recomputed from the tree (566 leaf keys, 2 only-in-strings keys), equal to the research expectation"
  - "Hassfest state (a) baseline is recorded as-is; none of its errors are fixed in Phase 1 (Phase 3 work)"

patterns-established:
  - "Triage-before-delete: 01-TRIAGE.md is committed before any card, panel or translation file is removed"

requirements-completed: [FOUND-04, FOUND-05]

coverage:
  - id: D1
    description: "Compiled bytecode is no longer tracked: git ls-files lists no .pyc or __pycache__ path, and the untracking is its own commit that deletes exactly 49 index entries and changes nothing else"
    requirement: FOUND-04
    verification:
      - kind: other
        ref: "git ls-files | grep -cE '\\.pyc$|__pycache__' prints 0; git show --diff-filter=D on d61341f lists 49 .pyc; --diff-filter=AMRC lists nothing"
        status: pass
    human_judgment: false
  - id: D2
    description: "HA 2026.10.4 hassfest loads a clean index export of the integration and reports Integrations: 1 with the expected pre-cleanup errors"
    requirement: FOUND-04
    verification:
      - kind: other
        ref: "Task 1 automated verify (export, no .pyc in export, hassfest output contains 'Integrations: 1' and 'Integration family_hub')"
        status: pass
    human_judgment: false
  - id: D3
    description: "01-TRIAGE.md exists, was committed before any deletion of cards/panels/translations, and passes both recomputation gates (14 rows, 9 orphan keys, strings.json diff)"
    requirement: FOUND-05
    verification:
      - kind: other
        ref: "Task 2 automated verify: 'rows 14 missing [] no_outcome []' and 'unrecorded []'"
        status: pass
    human_judgment: false
  - id: D4
    description: "Screenshots folder, four unserved icon/logo duplicates and the empty readme are removed in one commit that deletes exactly 20 paths and modifies only .gitignore; served icon.png and brand/ are unchanged"
    requirement: FOUND-05
    verification:
      - kind: other
        ref: "Task 3 automated verify (GATE_OK); 20 deletions, AMRC lists only .gitignore; git diff --quiet bc7e90c HEAD -- icon.png brand exits 0"
        status: pass
    human_judgment: false
  - id: D5
    description: ".gitignore equals the 6 original lines plus 5 new patterns and covers backup files, family_hub_backups/, .storage/ and dev/.ha-* while leaving versions.env tracked"
    requirement: FOUND-04
    verification:
      - kind: other
        ref: "sha256sum .gitignore = a2ca450d4549f1bd3062e00cf48ecedc09a5e85c2fc91afdadf39e56b0218166; git check-ignore probes"
        status: pass
    human_judgment: false

duration: not measured (work split across two executor sessions)
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 01: Clean Foundation, Hygiene and Triage Summary

**Bytecode untracked, a per-file triage record written before any deletion (all 14 root duplicates discarded, nothing to port), redundant screenshots/icons/readme removed, .gitignore hardened for HA state, and a local HA 2026.10.4 hassfest harness proven on a clean index export.**

## Performance

- **Duration:** not measured (the plan ran across two executor sessions, with a checkpoint on the validator run between them)
- **Completed:** 2026-10-26
- **Tasks:** 3
- **Files modified:** 1 created (`01-TRIAGE.md`), 1 modified (`.gitignore`), 69 deleted (49 bytecode index entries, 15 screenshots, 4 duplicate icons, 1 empty readme)

## Accomplishments

- A fresh clone or HACS download no longer receives 49 compiled `.pyc` files. The local `__pycache__` folders stay on disk and are ignored.
- `01-TRIAGE.md` records, from git evidence, that every root-level card and panel copy is superseded by its served copy (12 differ by older code and hardcoded English, 2 are byte-identical). Plans 01-02 and 01-07 can delete them with a written reason.
- The root translations hold nothing served that `translations/` lacks; the only unique content is 9 orphan keys used solely by the debris `.bak_divfix` file.
- Local Home Assistant state, family backups and `*.bak*` files can no longer be committed by accident.
- HA core 2026.10.4's own validator runs against an index export outside the repo, which plans 01-07 and 01-05 reuse.

## Task Commits

1. **Task 1 (tracer): Untrack bytecode and prove HA's validator loads a clean export** - `d61341f` (chore). Hassfest run itself writes no commit.
2. **Task 2: Write 01-TRIAGE.md from read-only git evidence** - `9f428de` (docs)
3. **Task 3: Remove screenshots, duplicate icons and empty readme; extend .gitignore** - `ddc3442` (chore)

**Plan metadata:** recorded in the follow-up `docs(01-01): complete ...` commit. The measured count `commits: 4` in the frontmatter covers the three task commits plus the orchestrator's `8b3e986 docs(state): begin phase 1 execution`, which landed between Task 1 and Task 2.

## Hassfest harness

- **Harness path:** `$HOME/.cache/fh-hassfest` (`/root/.cache/fh-hassfest`), outside the repo, never committed: `venv` (CPython 3.14.9, homeassistant 2026.10.4, infrared-protocols 10.1.0, tqdm 4.70.1), `core` (shallow clone of tag 2026.10.4, `const.py` shows 2026 / 10 / "4"), `tree` (the index export) and `hassfest-01-01.txt` (full output).
- **Run:** `PYTHONDONTWRITEBYTECODE=1 "$W/venv/bin/python" -B -m script.hassfest --action validate --integration-path "$W/tree/custom_components/family_hub"` from `$W/core`, against an export made with `git ls-files -z custom_components/family_hub | xargs -0 git --work-tree="$W/tree" checkout-index --`. The export held 0 `.pyc` files. Exit status 1, as expected.
- **Approval:** the repo owner explicitly approved running this validator from the pinned clone and venv for plans 01-01, 01-07 and 01-05 after the first attempt was blocked as external code. It reads the export and writes only `hassfest-01-01.txt`.

### State (a): before cleanup

Output header: `Integrations: 1` then `Integration family_hub - .../tree/custom_components/family_hub:`. The error and warning lines (hassfest itself truncates the two long translation messages; the full text of `fh_ui` / `grocy_url` is in `hassfest-01-01.txt`):

```
* [ERROR] [MANIFEST] Manifest keys are not sorted correctly: domain, name, then alphabetical order
* [ERROR] [TRANSLATIONS] Invalid strings.json: not a valid option at 'fh_ui'. Got {'nav': {'settings': 'Settings', 'week': 'Week', 'week_view_title': 'Week view', ...
* [ERROR] [TRANSLATIONS] Invalid translations/en.json: not a valid option at 'fh_ui'. Got {'nav': {'legend_events': 'Events', 'legend_reminders': 'Reminders', ...
* [WARNING] [CONFIG_SCHEMA] Integrations which implement 'async_setup' or 'setup' must define either 'CONFIG_SCHEMA', 'PLATFORM_SCHEMA' or 'PLATFORM_SCHEMA_BASE'. ...
```

`grocy_url` appears in the full text of the translation errors, as the plan expected. Nothing was fixed (Phase 3 work).

## Files Created/Modified

- `.planning/phases/01-clean-foundation/01-TRIAGE.md` - five-section audit record for every Phase 1 deletion
- `.gitignore` - 5 new patterns (`.env`, `*.bak*`, `family_hub_backups/`, `.storage/`, `dev/.ha-*`), 11 lines total
- Deleted: 49 bytecode index entries, the 15 files under the backslash-named Screenshots folder, `icon (1).png`, `icon@2x.png`, `logo.png`, `logo@2x.png` and `readme.md` under `custom_components/family_hub/`

## Decisions Made

- Every root `.js` duplicate is `discarded`, none `ported hunk`: the highest version tag inside any root-only line is 1.119.0 (my-chores 1.132.61), older than every served copy, and the root-only hunks are the older timer-alarm singleton, untranslated labels, older inline CSS or the retired my-chores body.
- The strings.json diff in the triage is the script output (566 / 2 keys), not copied research.
- The hassfest baseline is recorded unchanged so Phase 3 can show a before/after.

## Deviations from Plan

None - plan executed exactly as written. The run was split across two executors because the first one's validator call was denied by the permission classifier; the repo owner then approved it explicitly and this executor ran it exactly as the plan states.

## Issues Encountered

- The first executor's hassfest run was blocked by the permission classifier as external code. Resolved by explicit owner approval; no workaround was attempted.
- The measured `commits:` value (4) includes the orchestrator's `8b3e986` state commit, so the plan's own commits are 3.

## Known Stubs

None - no stub patterns in the files created or modified.

## Threat Flags

None - no new network endpoint, auth path, file-access pattern or schema surface was introduced; changes are deletions, one ignore-file edit and one planning document.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 01-TRIAGE.md is committed, so plan 01-02 (delete the root cards and panels) and 01-07 (translations, strings.json, `.bak_divfix`) may proceed. 01-02 has no hunk to port.
- The hassfest harness is ready for 01-07 and 01-05; re-run only the version check on `$W/core/homeassistant/const.py`.
- Residual assumption (FOUND-04): `git rm --cached` left local `__pycache__` on disk; no other compiled or cache artifact is tracked (`git ls-files` shows no `.pyc` or `__pycache__`).

## Self-Check: PASSED

- FOUND: `.planning/phases/01-clean-foundation/01-TRIAGE.md`, `.gitignore`
- FOUND commits: `d61341f`, `9f428de`, `ddc3442`
- Task 1, 2 and 3 verify gates and acceptance criteria re-run and passing; plan-level verification passing (0 tracked bytecode, 0 Screenshots paths, `.gitignore` sha256 `a2ca450d...8166`, no runtime change versus `bc7e90c`)

---
*Phase: 01-clean-foundation*
*Completed: 2026-10-26*
