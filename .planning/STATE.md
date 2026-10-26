---
gsd_state_version: "1.0"
milestone: v1.0
milestone_name: Family Preview Loop
current_phase: 01
current_phase_name: Clean Foundation
status: executing
stopped_at: Completed 01-01-PLAN.md
last_updated: "2026-10-26T23:00:47.308Z"
last_activity: 2026-10-26
last_activity_desc: Phase 01 execution started
state_head: 9acc8329444ab5167b7a72971f4eeecec7f27b49
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 7
  completed_plans: 1
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-26)

**Core value:** The family product owner can use a working Family Hub every day and see each change she asks for appear in a safe Preview before it reaches the family's real Home setup, without anything breaking the real calendars and lists.
**Current focus:** Phase 01 — Clean Foundation

## Current Position

Phase: 01 (Clean Foundation) — EXECUTING
Plan: 2 of 7
Status: Ready to execute
Last activity: 2026-10-26 — Phase 01 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | n/a | 3 tasks | 72 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Four phases from the brief: Clean Foundation, Dev + Family Preview, Safety Net, Family-Led Customisation Loop. Phase 3 depends only on Phase 1 and may overlap the tail of Phase 2.
- [Roadmap]: All phases are in MVP mode with user-story goals. From Phase 2 on, success criteria are things she does and sees in Preview.
- [Phase 1 due]: Fork version scheme (recommend continuing above 1.168.85, next 1.169.0), the real minimum HA version for `hacs.json`, and one pinned HA tag for Dev, Preview and tests (research recommends 2026.10.4).
- [Phase 2 due]: Where Preview runs (always-on Docker host, not the laptop). Preview is a separate instance from Home. Access is LAN-only (Tailscale deferred to v2).
- [Phase 01]: All 14 root .js duplicates triaged as discarded (no hunk to port); recorded in 01-TRIAGE.md
- [Phase 01]: Hassfest run only via the owner-approved pinned harness at $HOME/.cache/fh-hassfest against an index export; state (a) baseline errors left unfixed for Phase 3

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 2]: Needs `/gsd-plan-phase --research-phase 2` before planning. Open questions:
  - dashboard/resource creation path
  - which `family_hub/*` commands can seed data, and their kiosk gates
  - config-flow automation
  - reproducible non-admin dashboard and sidebar
  - HTTPS parity
  - Preview host and Companion setup
- [Phase 2]: `reset-preview` must wipe the whole config volume including `family_hub_backups/`. `store.py` restores from backups when storage loads empty.
- [Phase 1 -> 3]: Expect the first hassfest/HACS run to be red. Likely causes: manifest ordering, the `fh_ui` category, translation string rules, codeowners, Issues disabled on the fork. The Phase 1 spike sizes Phase 3.
- [Phase 3]: `pytest-homeassistant-custom-component` needs Python 3.14. Confirm `uv` provides it on the dev machine.
- [Phase 4]: `git.create_tag: true` makes milestone completion create a `v1.0`-style tag. `release.yml` (REL-01) must ignore tags that are not `vX.Y.Z`, or that config setting should change.

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-26T23:00:47.263Z
Stopped at: Completed 01-01-PLAN.md
Resume file: None
