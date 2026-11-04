---
phase: 01-clean-foundation
plan: 03
subsystem: infra
tags: [identity, manifest, hacs, hassfest, github-actions, docusaurus, gplv3]

requires:
  - phase: 01-clean-foundation
    provides: "plan 01-01 hygiene baseline (bc7e90c is the phase base for the unchanged checks)"
provides:
  - "manifest.json codeowners, documentation and issue_tracker point at Future-Bridge-AI/HA-Family-Hub"
  - "README badges, 14 images, HACS one-click link and docs link point at the fork, with the upstream credit line kept"
  - "Dangling CHANGELOG_ARCHIVE.md links in README.md and CHANGELOG.md now resolve to website/docs/changelog-archive.md"
  - "Docs site config and installation/intro/license pages point at the fork; footer keeps Bordello Labs and credits upstream"
  - ".github/workflows/validate.yml: non-blocking HACS and hassfest jobs ready for the plan 01-05 baseline run"
affects: [01-04, 01-05, phase-03-validation]

actuals:
  tokens: 5256
  tasks: 3
  commits: 3

plan_head_before: 803ff1aad61916a3b1e2e16464ac36cabb3ba4c4
plan_head_after: 26b898bbd9e1175c3595bde356e1fd87a9d2dd4e
commits: 3

tech-stack:
  added: []
  patterns:
    - "Exact-string gates on every rewritten URL with case-sensitive owner Future-Bridge-AI; lowercase only for the GitHub Pages host"
    - "Validation workflow as two independent jobs so one failure cannot hide the other, with least-privilege permissions"

key-files:
  created:
    - .github/workflows/validate.yml
  modified:
    - custom_components/family_hub/manifest.json
    - README.md
    - CHANGELOG.md
    - website/docusaurus.config.js
    - website/docs/installation.md
    - website/docs/intro.md
    - website/docs/license.md

key-decisions:
  - "manifest.json key order left unchanged on purpose so hassfest's ordering error stays in the honest Phase 1 baseline; Phase 3 fixes it"
  - "validate.yml uses the docs-prescribed floating refs hacs/action@main and hassfest@master (D-22); Phase 3 pins commit SHAs"
  - "Historical release links in website/docs/changelog.md and changelog-archive.md, and the upstream CMS config, left untouched"

patterns-established:
  - "Upstream credit is kept visible in two places: README License section and the docs footer copyright"

requirements-completed: [FOUND-06, FOUND-09]

coverage:
  - id: D1
    description: "manifest.json codeowners, documentation and issue_tracker point at the fork; domain, name and key order unchanged"
    requirement: FOUND-06
    verification:
      - kind: other
        ref: "python3 -B -I manifest check (list(m)==expected key order, codeowners==['@Future-Bridge-AI'], documentation, issue_tracker, iot_class, config_flow); prints manifest_ok True"
        status: pass
    human_judgment: false
  - id: D2
    description: "README badges, images, HACS link and docs link point at the fork; the single remaining upstream mention is the credit line; Bordello Labs copyright kept; archive links fixed"
    requirement: FOUND-06
    verification:
      - kind: other
        ref: "Task 1 grep gate in 01-03-PLAN.md (exit 0), plus git ls-files --error-unmatch on all 14 referenced images"
        status: pass
    human_judgment: false
  - id: D3
    description: "Docs site config and pages point at the fork with an upstream credit in the footer; history pages, CMS config and deploy-docs.yml unchanged"
    requirement: FOUND-06
    verification:
      - kind: other
        ref: "Task 2 grep gate in 01-03-PLAN.md (exit 0) including node --input-type=module --check on docusaurus.config.js"
        status: pass
    human_judgment: false
  - id: D4
    description: "validate.yml defines the hacs and hassfest jobs with the required triggers and permissions and no suppression, secrets, PR-target trigger or concurrency group"
    requirement: FOUND-09
    verification:
      - kind: other
        ref: "Task 3 YAML-parsing gate in 01-03-PLAN.md (prints workflow_ok True, exit 0)"
        status: pass
    human_judgment: false
  - id: D5
    description: "The workflow actually runs on GitHub and records the FOUND-09 baseline failure list"
    requirement: FOUND-09
    verification: []
    human_judgment: true
    rationale: "The baseline run and VALIDATION-BASELINE.md are produced by plan 01-05; this plan only places the workflow file."

duration: 5min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 03: Fork identity and validation workflow Summary

**Manifest, README, docs site and HACS links now point at Future-Bridge-AI/HA-Family-Hub with upstream and Bordello Labs credit kept, plus a two-job non-blocking hassfest and HACS validation workflow**

## Performance

- **Duration:** 5 min
- **Started:** 2026-10-26T22:58:00Z (approximate)
- **Completed:** 2026-10-26T23:04:00Z
- **Tasks:** 3
- **Files modified:** 8 (7 modified, 1 created)

## Accomplishments
- manifest.json has codeowner `@Future-Bridge-AI` and the fork's documentation and issue-tracker URLs. The diff against bc7e90c is exactly 3 insertions and 3 deletions, and domain, name and key order are unchanged.
- README.md badges, 14 images, the HACS one-click link and the docs link use the fork. The only upstream mention left is the credit line in the License section, next to the kept Bordello Labs copyright.
- Both dangling `CHANGELOG_ARCHIVE.md` links (README.md, CHANGELOG.md) now point at `website/docs/changelog-archive.md`.
- The docs site config and the installation, intro and license pages use the fork. The footer copyright keeps Bordello Labs and adds the upstream credit. `docusaurus.config.js` parses as an ES module.
- `.github/workflows/validate.yml` has independent `hacs` and `hassfest` jobs, top-level `permissions: {}`, `contents: read` only on hassfest, and no suppression, secrets, concurrency group or PR-target trigger.

## Task Commits

Each task was committed atomically:

1. **Task 1 (tracer): Point manifest and README at the fork** - `1799d94` (chore)
2. **Task 2: Point the docs site at the fork** - `5b5be05` (chore)
3. **Task 3: Add the validation workflow** - `26b898b` (ci)

**Plan metadata:** committed separately after this file (docs: complete plan)

## Files Created/Modified
- `custom_components/family_hub/manifest.json` - codeowners, documentation, issue_tracker now name the fork
- `README.md` - fork badges, images, HACS and docs links; upstream credit line; archive link fix
- `CHANGELOG.md` - archive link fix
- `website/docusaurus.config.js` - url, organizationName, editUrl, navbar and footer links, footer credit
- `website/docs/installation.md` - HACS one-click link owner
- `website/docs/intro.md` - GitHub link
- `website/docs/license.md` - LICENSE link
- `.github/workflows/validate.yml` - new HACS and hassfest validation workflow

## Decisions Made
- Left manifest key order as is so the hassfest ordering error is part of the honest baseline (Phase 3 fixes it).
- Kept the floating action refs `hacs/action@main` and `hassfest@master` per D-22 (threat T-01-10 accepted); Phase 3 pins SHAs.
- Did not touch historical upstream release links, the CMS config, DOCUMENTATION.md, LICENSE or any Python/JS source (D-16, D-17).

## Deviations from Plan

None - plan executed exactly as written.

The tracer feedback gate ran in auto mode: Task 1's verify was re-run before expansion and passed.

## Issues Encountered

None. The plan's baseline invariant (D-17) was re-checked at the end: `git diff --quiet bc7e90c HEAD` over the Python modules, services.yaml, served card/panel JS and LICENSE exits 0.

## Known Stubs

None.

## Threat Flags

None - no new network endpoints, auth paths or trust-boundary schema. The new workflow is the planned T-01-09 / T-01-11 surface and its gate asserts the mitigations.

## User Setup Required

None - no external service configuration required. Note for later: the workflows and the docs site only take effect once this branch is on `main` of Future-Bridge-AI/HA-Family-Hub; the README images render at that point too.

## Next Phase Readiness
- Plan 01-04 can set the version in manifest.json (left at 1.168.85 here).
- Plan 01-05 can run the single baseline validation using `validate.yml` and record it. FOUND-09 stays open until that baseline is recorded.

## Self-Check: PASSED

- `.github/workflows/validate.yml` exists; commits 1799d94, 5b5be05 and 26b898b are ancestors of HEAD.
- All three task gates exit 0 and the D-17 invariant against bc7e90c holds.

---
*Phase: 01-clean-foundation*
*Completed: 2026-10-26*
