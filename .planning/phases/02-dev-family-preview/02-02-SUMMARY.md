---
phase: 02-dev-family-preview
plan: 02
subsystem: infra
tags: [docker-compose, bash, home-assistant, gitattributes, dev-environment]

requires:
  - phase: 02-dev-family-preview
    provides: "Plan 02-01 (same wave): tools.seed subcommands wait/bootstrap/resources-sync, scripts/make-certs, dev/config-template/configuration.yaml. Referenced by path and command line only; not present in this tree."
provides:
  - "scripts/dev-up: one command that starts Dev (compose project familyhub-dev) and hands over to the seed bootstrap"
  - "scripts/dev-cards, dev-restart, dev-down: the Dev edit loop"
  - "scripts/lib.sh: shared helpers (fh_load_env, fh_compose, fh_seed, fh_ensure_certs, fh_ensure_config) for every later script"
  - "dev/compose.yaml + dev/compose.dev.yaml: pinned HA image on 127.0.0.1:8130 with the working copy mounted read-only"
  - "dev/host.env.example and the gitignored dev/host.env contract"
  - ".gitattributes LF rules"
affects: [02-05, 02-07, 02-09, deploy-preview, reset-preview, refresh-preview, doctor]

actuals:
  tokens: 1950
  tasks: 2
  commits: 2
plan_head_before: e9f9463a6b7dd78c3b4d1ba67bf04548870ce471
plan_head_after: a325d717cd4ea20c86a4ecc87b3aab445ba427e8

tech-stack:
  added: []
  patterns:
    - "Compose base + per-environment overlay, run from the repo root with --env-file versions.env --env-file dev/host.env"
    - "Thin bash wrappers sourcing scripts/lib.sh; seed tool runs in a throwaway container of the pinned HA image (FH_SEED_CMD overrides it for tests)"

key-files:
  created:
    - dev/compose.yaml
    - dev/compose.dev.yaml
    - dev/host.env.example
    - scripts/lib.sh
    - scripts/dev-up
    - scripts/dev-cards
    - scripts/dev-restart
    - scripts/dev-down
    - .gitattributes
  modified:
    - .gitignore

key-decisions:
  - "fh_seed runs the seed tool inside the pinned HA image with the repo mounted read-only and only dev/.ha-secrets (mode 700) writable, as the caller's uid:gid"
  - "git add --renormalize was NOT run (see Deviations)"

patterns-established:
  - "No laptop-specific path in any script or compose file; every host value comes from dev/host.env"
  - "Dev is published on 127.0.0.1 only; no privileged, no network_mode"

requirements-completed: [DEV-01, DEV-02]

coverage:
  - id: D1
    description: "scripts/dev-up renders as a pinned-image Dev on 127.0.0.1:8130 with the integration mounted read-only and hands over to fh_seed dev bootstrap"
    requirement: DEV-01
    verification:
      - kind: automated_ui
        ref: "docker compose -p familyhub-dev ... config --format json asserted by the Task 1 gate (dev_compose_ok True)"
        status: pass
    human_judgment: true
    rationale: "Live start of Dev, second-run idempotency and the real bootstrap need Docker and plan 02-01; checked at the plan 02-09 laptop checkpoint"
  - id: D2
    description: "Edit loop scripts (dev-cards, dev-restart, dev-down) parse, are executable and call their seed or compose subcommand"
    requirement: DEV-02
    verification:
      - kind: other
        ref: "Task 2 gate: bash -n, executable bit, grep for fh_seed dev resources-sync / fh_seed dev wait; dev-cards run against an FH_SEED_CMD stub"
        status: pass
    human_judgment: true
    rationale: "A card edit appearing after a normal refresh needs a running Dev and the 02-01 resources-sync; checked at the plan 02-09 laptop checkpoint"
  - id: D3
    description: "Scripts, YAML, Python, env examples and PowerShell resolve to eol lf"
    verification:
      - kind: other
        ref: "git check-attr eol on scripts/dev-up, tools/seed/envs.py, dev/compose.yaml, dev/host.env.example, scripts/windows/setup-host.ps1 (all lf)"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-11-03
status: complete
---

# Phase 2 Plan 02: Dev host layer Summary

**One-command Dev (scripts/dev-up) on the pinned HA 2026.10.4 image, loopback port 8130, working copy mounted read-only, with a dev-cards/dev-restart/dev-down edit loop and LF-forcing .gitattributes**

## Performance

- **Duration:** about 12 min
- **Tasks:** 2
- **Files modified:** 10 (9 created, 1 modified)

## Accomplishments
- `scripts/dev-up` loads versions.env and dev/host.env, creates certificates and `dev/.ha-dev/configuration.yaml` only when absent, runs `docker compose up -d` for project `familyhub-dev`, then `fh_seed dev bootstrap`, and prints "Dev is ready: https://127.0.0.1:8130 (Family Hub DEV)". Every step is idempotent, so a second run changes nothing.
- Compose renders (verified with `docker compose config`) the pinned image, `127.0.0.1:8130:8123` as the only port, `PYTHONDONTWRITEBYTECODE=1`, `/ssl` read-only, `custom_components/family_hub` read-only, and no `privileged` or `network_mode` (threat T-02-24).
- `scripts/lib.sh` gives later scripts one shared set of helpers; a missing dev/host.env stops with "copy dev/host.env.example to dev/host.env" (checked live).
- `scripts/dev-cards`, `dev-restart`, `dev-down` implement the edit loop; `.gitattributes` keeps them LF on a Windows-side clone.
- `dev/host.env` and `tools/seed/*.local.*` are gitignored; the committed example holds invented values only (T-02-26).

## Task Commits

1. **Task 1 (tracer): One command starts Dev in Docker on the pinned image** - `ec078df` (feat)
2. **Task 2: Edit loop scripts and LF line endings** - `a325d71` (feat)

**Plan metadata:** committed separately as the docs(02-02) SUMMARY commit.

Tracer feedback gate: auto mode is active; the Task 1 `<verify>` was run end to end (compose render and assertions, syntax, ignore rules) and passed before expansion, so Task 2 proceeded.

## Files Created/Modified
- `dev/compose.yaml` - base service `ha`: pinned image, TZ, PYTHONDONTWRITEBYTECODE, 60s grace, `/ssl:ro`
- `dev/compose.dev.yaml` - Dev overlay: `127.0.0.1:8130:8123`, `./.ha-dev:/config`, integration mounted `:ro`
- `dev/host.env.example` - the eleven documented host keys with invented values
- `scripts/lib.sh` - FH_ROOT, fh_die, fh_info, fh_load_env, fh_compose, fh_seed, fh_ensure_certs, fh_ensure_config
- `scripts/dev-up`, `dev-cards`, `dev-restart`, `dev-down` - mode 100755 wrappers
- `.gitattributes` - `* text=auto` plus eol=lf rules
- `.gitignore` - adds `dev/host.env` and `tools/seed/*.local.*`

## Decisions Made
- `fh_ensure_certs` passes `--out dev/.ha-certs` and, when `PREVIEW_HOST_IP` is set, `--ip` to `scripts/make-certs` (the plan 02-01 CLI contract); 02-09 confirms the pairing for real.
- `fh_seed` creates `dev/.ha-secrets` with mode 700 before mounting it, as the plan specifies.

## Deviations from Plan

### Not run, as the plan allows

**1. `git add --renormalize .` was not run**
- **Reason:** the plan says to run it only if it changes nothing outside this plan's files. A dry run (`git add --renormalize --dry-run .`) listed about 1,050 existing paths, so it would touch files outside this plan. Existing files were left alone; the new `.gitattributes` applies to new and later-modified files.
- **Impact:** none for this plan's files, which were all created LF. Existing files keep their current line endings until someone renormalises deliberately.

**Total deviations:** 0 auto-fixed. **Impact on plan:** none.

## Issues Encountered
None. No Docker daemon is available, so containers were not started; per the plan the gates use `docker compose config` only. Live start, second-run idempotency, `--network host` reaching the published port from the seed container, and real bootstrap/resources-sync are covered by the plan 02-09 laptop checkpoint together with plan 02-01.

## Known Stubs
None.

## Threat Flags
None beyond the plan's threat model (T-02-24, T-02-25, T-02-26 mitigated as described above).

## User Setup Required
None - no external service configuration required. The developer copies `dev/host.env.example` to `dev/host.env` and edits it before the first `scripts/dev-up`.

## Next Phase Readiness
- lib.sh and the compose base are ready for the Preview overlay and the deploy/reset/refresh/doctor scripts (plan 02-07).
- Depends on plan 02-01 for `tools/seed`, `scripts/make-certs` and `dev/config-template/configuration.yaml` at run time; none of these existed in this worktree and none were created here.

## Self-Check: PASSED

- All 10 listed files exist; scripts are mode 100755.
- Commits `ec078df` and `a325d71` are in the branch history.
- Task 1 and Task 2 gates and acceptance criteria re-run and passing.

---
*Phase: 02-dev-family-preview*
*Completed: 2026-11-03*
