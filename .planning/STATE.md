---
gsd_state_version: "1.0"
milestone: v1.0
milestone_name: Family Preview Loop
current_phase: 1
current_phase_name: Clean Foundation
status: planning
stopped_at: Phase 1 context gathered
last_updated: "2026-10-26T07:34:23.359Z"
last_activity: 2026-10-26
last_activity_desc: Roadmap created (4 phases, 43/43 v1 requirements mapped)
state_head: 5fff4444879cc4c074436135877fd77f08d2f89b
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-26)

**Core value:** The family product owner can use a working Family Hub every day and see each change she asks for appear in a safe Preview before it reaches the family's real Home setup, without anything breaking the real calendars and lists.
**Current focus:** Phase 1: Clean Foundation

## Current Position

Phase: 1 of 4 (Clean Foundation)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-10-26 - Roadmap created (4 phases, 43/43 v1 requirements mapped)

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

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Four phases from the brief: Clean Foundation, Dev + Family Preview, Safety Net, Family-Led Customisation Loop. Phase 3 depends only on Phase 1 and may overlap the tail of Phase 2.
- [Roadmap]: All phases are in MVP mode with user-story goals. From Phase 2 on, success criteria are things she does and sees in Preview.
- [Phase 1 due]: Fork version scheme (recommend continuing above 1.168.85, next 1.169.0), the real minimum HA version for `hacs.json`, and one pinned HA tag for Dev, Preview and tests (research recommends 2026.10.4).
- [Phase 2 due]: Where Preview runs (always-on Docker host, not the laptop). Preview is a separate instance from Home. Access is LAN-only (Tailscale deferred to v2).

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

Last session: 2026-10-26T07:34:23.334Z
Stopped at: Phase 1 context gathered
Resume file: .planning/phases/01-clean-foundation/01-CONTEXT.md
