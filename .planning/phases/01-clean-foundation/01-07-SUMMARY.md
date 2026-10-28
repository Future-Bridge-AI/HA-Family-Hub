---
phase: 01-clean-foundation
plan: 07
subsystem: infra
tags: [translations, hassfest, git-hygiene, home-assistant, strings-json]

requires:
  - phase: 01-clean-foundation
    provides: "01-01 triage record and hassfest harness; 01-06 move of it/nl/pl/pt/pt-BR into translations/"
provides:
  - "Each translation exists only in translations/ (root de/en/es/fr.json and strings.json deleted)"
  - "No tracked .bak file (calendar card .bak_divfix deleted); none of the 9 orphan keys remains in any tracked file under custom_components/"
  - "hassfest 'after translations' record: strings.json errors gone, fh_ui and grocy_url objections remain for Phase 3"
affects: [01-05, phase-03-validation]

actuals:
  tokens: 0
  tasks: 2
  commits: 2

plan_head_before: 476a3c488d7c3b8b684cb679e04148aa992cada7
plan_head_after: 0ca31a89c688fff48b52b201249877b0a6b1795b
commits: 2

tech-stack:
  added: []
  patterns:
    - "Deletion-only commits with fixed subjects so each removal is auditable and independently revertible"
    - "Validate an index export with HA's own hassfest after structural deletions"

key-files:
  created: []
  modified: []

key-decisions:
  - "Orphan keys not ported (D-06): re-ran git grep -w for all nine; only root de.json, es.json and the .bak_divfix backup held them, no served file"
  - "translations/ left untouched, fh_ui preserved (D-09); hassfest still reports the fh_ui objection, proving it"

requirements-completed: [FOUND-01, FOUND-03]

coverage:
  - id: D1
    description: "Root de/en/es/fr.json and strings.json are deleted in one deletion-only commit of exactly 5 paths; manifest.json is the only top-level .json under custom_components/family_hub/"
    requirement: FOUND-03
    verification:
      - kind: other
        ref: "Task 1 automated gate (one top-level json, orphan keys only in .bak_divfix, hassfest checks) printed GATE_OK; git show --diff-filter=D lists 5 paths, --diff-filter=AMRC lists none"
        status: pass
    human_judgment: false
  - id: D2
    description: "All nine languages in translations/ still have exactly the same 2,139 leaf keys as translations/en.json, and no translations/ file differs from the phase base bc7e90c"
    requirement: FOUND-03
    verification:
      - kind: other
        ref: "nine-language parity script prints 'langs 9 en_keys 2139 bad []'; git diff --quiet bc7e90c HEAD on translations/{de,en,es,fr}.json, *.py and services.yaml exits 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "HA 2026.10.4 hassfest on the index export reports no strings.json error and still reports the fh_ui objection for translations/en.json"
    requirement: FOUND-03
    verification:
      - kind: other
        ref: "hassfest-01-07.txt: 'Integrations: 1', no 'Invalid strings.json', contains \"Invalid translations/en.json: not a valid option at 'fh_ui'\""
        status: pass
    human_judgment: false
  - id: D4
    description: "The .bak_divfix backup is removed in its own deletion-only commit; no tracked file name contains .bak, no orphan key remains, and all 15 registered served paths are still tracked"
    requirement: FOUND-01
    verification:
      - kind: other
        ref: "Task 2 automated gate printed 'orphan_key_files [] rc 1', 'registered 15 missing []', GATE2_OK; git show --diff-filter=D lists exactly the .bak_divfix path"
        status: pass
    human_judgment: false
  - id: D5
    description: "Every language is still reachable at every point of history: the 01-06 move commit is an ancestor of the 01-07 deletion commit"
    requirement: FOUND-03
    verification:
      - kind: other
        ref: "git merge-base --is-ancestor <01-06 move> <01-07 deletion> exits 0"
        status: pass
    human_judgment: false

duration: 1 min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 07: Delete Root Translations, strings.json and the .bak_divfix Backup Summary

**Truncated root de/en/es/fr.json and the unused strings.json deleted, then the 1.2 MB calendar card .bak_divfix removed, in two deletion-only commits, with HA 2026.10.4 hassfest confirming the strings.json errors are gone while the fh_ui translation category is preserved.**

## Performance

- **Duration:** about 1 min of executor time (23:48:28Z to 23:49:11Z)
- **Started:** 2026-10-26T23:48:28Z
- **Completed:** 2026-10-26T23:49:11Z
- **Tasks:** 2
- **Files modified:** 6 deleted, 0 created, 0 changed

## Accomplishments

- Each translation now exists in exactly one place, `custom_components/family_hub/translations/`. `manifest.json` is the only top-level `.json` file left under `custom_components/family_hub/` (it was 11 at the phase start, 6 after plan 01-06).
- `strings.json` is gone (custom integrations never read it). The convention of keeping it in sync with `translations/en.json` is retired.
- The 9 orphan de/es keys were re-checked with `git grep -w` and appear in no served file, so they were not ported (D-06). With the `.bak_divfix` deletion no tracked file under `custom_components/` holds any of them.
- `card/family-week-calendar-card.js.bak_divfix` is removed. All 15 served paths registered in `__init__.py` are still tracked.
- Nine languages still carry exactly 2,139 leaf keys each, and `translations/` is byte-for-byte unchanged since the phase base `bc7e90c` for de/en/es/fr (the other five were moved, not edited, in 01-06).

## Task Commits

1. **Task 1 (tracer): Delete the truncated root translations and strings.json** - `5dd2cae` (chore). Exactly 5 deletions, no additions or modifications.
2. **Task 2: Delete the unserved calendar card .bak_divfix backup** - `0ca31a8` (chore). Exactly 1 deletion.

**Plan metadata:** recorded in the follow-up `docs(01-07): complete ...` commit.

## Hassfest, after translations

Run: HA core 2026.10.4 (`const.py` PATCH_VERSION "4") from the pinned harness at `$HOME/.cache/fh-hassfest`, against a fresh index export of `custom_components/family_hub` taken right after commit `5dd2cae`. Full output: `$HOME/.cache/fh-hassfest/hassfest-01-07.txt` (outside the repo, not committed). The run was explicitly approved by the repo owner for plans 01-01, 01-07 and 01-05.

Header: `Integrations: 1`, `Invalid integrations: 1`. Remaining lines (long messages truncated by hassfest or by this record):

```
* [ERROR] [MANIFEST] Manifest keys are not sorted correctly: domain, name, then alphabetical order
* [ERROR] [TRANSLATIONS] Invalid translations/en.json: not a valid option at 'fh_ui'. Got {'nav': {'legend_events': 'Events', ...
  the string should not contain URLs, please use description placeholders instead at 'config.step.grocy.data.grocy_url'. Got 'Grocy URL (e.g. http://homeassistant.local:9192)'
  the string should not contain URLs, please use description placeholders instead at 'options.step.grocy.data.grocy_url'. Got 'Grocy URL (e.g. http://homeassistant.local:9192)'
* [WARNING] [CONFIG_SCHEMA] Integrations which implement 'async_setup' or 'setup' must define either 'CONFIG_SCHEMA', 'PLATFORM_SCHEMA' or 'PLATFORM_SCHEMA_BASE'. ...
```

Compared with the 01-01 baseline (state a):

- The `Invalid strings.json: not a valid option at 'fh_ui'` error is gone.
- The `Invalid translations/en.json ... 'fh_ui'` error and the two `grocy_url` objections remain. They are Phase 3 work and were deliberately not fixed here (D-09).
- The manifest key-order error and the CONFIG_SCHEMA warning are unchanged and also belong to later work.

## Files Created/Modified

- Deleted: `custom_components/family_hub/de.json`, `en.json`, `es.json`, `fr.json`, `strings.json` (commit `5dd2cae`)
- Deleted: `custom_components/family_hub/card/family-week-calendar-card.js.bak_divfix` (commit `0ca31a8`)

## Decisions Made

- Followed the plan as specified. The orphan keys stay unported (D-06), `translations/` and its `fh_ui` category stay untouched (D-09), and the two removals stay in separate deletion-only commits (D-04, D-24).

## Deviations from Plan

None - plan executed exactly as written. Note that the plan's "baseline at HEAD: 11" top-level `.json` files and "root it/nl/pl/pt/pt-BR" are historical figures from before plan 01-06. At the start of this plan six top-level `.json` files remained (`de`, `en`, `es`, `fr`, `strings`, `manifest`), and five were deleted as the plan states.

## Issues Encountered

None.

## Known Stubs

None - no stub patterns in the files touched; this plan only deletes files.

## Threat Flags

None - deletions only; no new network endpoint, auth path, file-access pattern or schema surface.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for plan 01-05 (the remaining plan of the phase), which can reuse the hassfest harness. The index export in `$HOME/.cache/fh-hassfest/tree` is stale after any new commit and must be re-exported.
- Phase 3 inputs recorded: the `fh_ui` category rejected by hassfest in `translations/en.json` and the `grocy_url` strings that contain a URL example.

## Self-Check: PASSED

- FOUND commits: `5dd2cae`, `0ca31a8` (both ancestors of HEAD)
- No tracked path contains `.bak`; `strings.json` and root `de/en/es/fr.json` no longer tracked; `git ls-files` shows `manifest.json` as the only top-level `.json`
- Task 1 and Task 2 verify gates and acceptance criteria re-run and passing; plan-level verification passing (parity `en_keys 2139 bad []`, no runtime change versus `bc7e90c`)

---
*Phase: 01-clean-foundation*
*Completed: 2026-10-26*
