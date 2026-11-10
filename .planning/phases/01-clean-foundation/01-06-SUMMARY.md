---
phase: 01-clean-foundation
plan: 06
subsystem: i18n
tags: [translations, home-assistant, hacs, git-mv, fh_ui]

requires:
  - phase: 01-clean-foundation
    provides: "plan 01-01 root-translation triage (01-TRIAGE.md): root it, nl, pl, pt, pt-BR each have 2139 leaf keys, symmetric difference 0 vs translations/en.json"
provides:
  - "All nine languages (de, en, es, fr, it, nl, pl, pt, pt-BR) sit in custom_components/family_hub/translations/ with the same 2,139 leaf keys and the fh_ui category"
  - "Italian, Dutch, Polish, Portuguese and Brazilian Portuguese are now in the folder Home Assistant loads"
  - "No root copy of it, nl, pl, pt or pt-BR remains tracked"
affects: [01-07, phase-03-ci-guard]

actuals:
  tokens: 198323
  tasks: 1
  commits: 1

plan_head_before: ea59698c88a2e4c3d66527177458d159d803ec63
plan_head_after: 3c9a7031dcf4c521840595f513c1477f944e15bb
commits: 1

tech-stack:
  added: []
  patterns:
    - "Moves are git mv with zero content change so renames stay R100 and history follows the file"

key-files:
  created:
    - custom_components/family_hub/translations/it.json
    - custom_components/family_hub/translations/nl.json
    - custom_components/family_hub/translations/pl.json
    - custom_components/family_hub/translations/pt.json
    - custom_components/family_hub/translations/pt-BR.json
  modified: []

key-decisions:
  - "pt.json and pt-BR.json moved as two separate byte-identical files (md5 2c33d85a4f5e8c6c7fc1701232a652ce), not merged or deduplicated (D-05)"
  - "fh_ui top-level category left exactly as is (D-09)"

patterns-established:
  - "Tracer verify gate: nine-language flatten-and-compare script against translations/en.json (expects en_keys 2139 bad [])"

requirements-completed: [FOUND-02]

coverage:
  - id: D1
    description: "it, nl, pl, pt and pt-BR are in translations/ with the same 2,139 keys as translations/en.json and fh_ui preserved"
    requirement: "FOUND-02"
    verification:
      - kind: other
        ref: "nine-language parity script from 01-06-PLAN.md Task 1 <verify> (printed: en_keys 2139 bad [])"
        status: pass
    human_judgment: false
  - id: D2
    description: "The move is exactly five exact renames in one commit, and de/en/es/fr translations and Portuguese md5s are unchanged"
    requirement: "FOUND-02"
    verification:
      - kind: other
        ref: "git show -M100% --name-status 3c9a703 (5 R100 lines); git diff --quiet bc7e90c on translations/{de,en,es,fr}.json; md5sum of pt.json and pt-BR.json"
        status: pass
    human_judgment: false
  - id: D3
    description: "A user with Italian, Dutch, Polish, Portuguese or Brazilian Portuguese selected sees Family Hub in that language"
    requirement: "FOUND-02"
    verification: []
    human_judgment: true
    rationale: "Rendering in the selected language depends on Home Assistant loading translations on a real instance; no automated test in this repo exercises it. Verified at the file level only."

duration: 1 min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 06: Move Remaining Translations Summary

**Italian, Dutch, Polish, Portuguese and Brazilian Portuguese translations moved from the integration root into translations/ as five byte-exact git renames, giving all nine languages full 2,139-key parity with fh_ui intact**

## Performance

- **Duration:** 1 min
- **Started:** 2026-10-26T23:07:54Z
- **Completed:** 2026-10-26T23:08:10Z (task commit; SUMMARY follows)
- **Tasks:** 1
- **Files modified:** 10 file entries (5 renames, each at source and destination)

## Accomplishments
- Moved `it.json`, `nl.json`, `pl.json`, `pt.json` and `pt-BR.json` into `custom_components/family_hub/translations/` with `git mv`; content and key order untouched.
- Nine-language parity gate passes: every language file in `translations/` has the same 2,139 leaf keys as `en.json` and keeps `fh_ui`. Gate output: `en_keys 2139 bad []`.
- `translations/pt.json` and `translations/pt-BR.json` both have md5 `2c33d85a4f5e8c6c7fc1701232a652ce` and remain two separate files.
- Existing `translations/de.json`, `en.json`, `es.json` and `fr.json` are unchanged against `bc7e90c`; the plan-level invariant (no `.py`, `services.yaml` or those four files changed since `bc7e90c`) holds.
- `translations/` now tracks exactly 9 files.

Tracer gate: the task's `<verify>` carries only `<automated>`, so it was re-run end to end after the commit and passed (tracer verified end-to-end). There were no expansion tasks.

## Task Commits

1. **Task 1 (tracer): Move it, nl, pl, pt and pt-BR into translations/ unchanged** - `3c9a703` (chore)

**Plan metadata:** committed separately as `docs(01-06): complete translations move plan`

## Files Created/Modified
- `custom_components/family_hub/translations/it.json` - Italian translations (renamed from root, R100)
- `custom_components/family_hub/translations/nl.json` - Dutch translations (renamed from root, R100)
- `custom_components/family_hub/translations/pl.json` - Polish translations (renamed from root, R100)
- `custom_components/family_hub/translations/pt.json` - Portuguese translations (renamed from root, R100)
- `custom_components/family_hub/translations/pt-BR.json` - Brazilian Portuguese translations (renamed from root, R100)

## Decisions Made
None - followed plan as specified (D-05 `git mv` unchanged, D-09 `fh_ui` preserved, D-24 one commit).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

Acceptance criteria results:
- Gate prints `en_keys 2139 bad []` and exits 0: PASS
- Move commit has exactly five lines, all `R100`: PASS
- Move commit has no A/D/M/C entries (pure renames): PASS
- `translations/` has 9 tracked files: PASS

Note on `actuals.tokens`: renames carry no diff content, so the figure is chars/4 over the five moved files (793,291 chars), the same scale as the estimate.

## Known Stubs

None. The plan moves existing files and adds no code, data wiring or placeholder text.

## Threat Flags

None. No new network endpoint, auth path or trust-boundary schema change; T-01-07 (tampering during the move) is mitigated by the R100, md5 and parity checks above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Ready for 01-07: the root `de.json`, `en.json`, `es.json`, `fr.json` and `strings.json` are still in place for that plan to delete.
- No blockers.

## Self-Check: PASSED

- FOUND: `custom_components/family_hub/translations/{it,nl,pl,pt,pt-BR}.json` (all five tracked, `translations/` has 9 files)
- FOUND: commit `3c9a703` is an ancestor of HEAD
- `git rev-list --count ea59698..HEAD` before this metadata commit: 1, matching `commits: 1`

---
*Phase: 01-clean-foundation*
*Completed: 2026-10-26*
