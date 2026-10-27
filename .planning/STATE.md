---
gsd_state_version: "1.0"
milestone: v1.0
milestone_name: Family Preview Loop
current_phase: 2
current_phase_name: Dev + Family Preview
status: planning
stopped_at: Phase 01 complete, ready to plan Phase 2
last_updated: "2026-10-27T08:19:31.360Z"
last_activity: 2026-10-27
last_activity_desc: Phase 01 complete, transitioned to Phase 2
state_head: 84efe440ae4bd0efefbe6be6a9da75aad17c1175
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 7
  completed_plans: 7
  percent: 25
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-27)

**Core value:** The family product owner can use a working Family Hub every day and see each change she asks for appear in a safe Preview before it reaches the family's real Home setup, without anything breaking the real calendars and lists.
**Current focus:** Phase 2 — Dev + Family Preview

## Current Position

Phase: 2 — Dev + Family Preview
Plan: Not started
Status: Ready to plan
Last activity: 2026-10-27 — Phase 01 complete, transitioned to Phase 2

Progress: [███░░░░░░░] 25%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 7 | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | n/a | 3 tasks | 72 files |
| Phase 01 P03 | 5 min | 3 tasks | 8 files |
| Phase 01 P02 | 1 min | 2 tasks | 14 files |
| Phase 01 P06 | 1 min | 1 tasks | 10 files |
| Phase 01 P04 | 36 min | 3 tasks | 6 files |
| Phase 01 P07 | 1 min | 2 tasks | 6 files |
| Phase 01 P05 | 7h 43m | 3 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Four phases from the brief: Clean Foundation, Dev + Family Preview, Safety Net, Family-Led Customisation Loop. Phase 3 depends only on Phase 1 and may overlap the tail of Phase 2.
- [Roadmap]: All phases are in MVP mode with user-story goals. From Phase 2 on, success criteria are things she does and sees in Preview.
- [Phase 2 due]: Where Preview runs (always-on Docker host, not the laptop). Preview is a separate instance from Home. Access is LAN-only (Tailscale deferred to v2).
- [Phase 01]: All 14 root .js duplicates triaged as discarded (no hunk to port); recorded in 01-TRIAGE.md
- [Phase 01]: Hassfest run only via the owner-approved pinned harness at $HOME/.cache/fh-hassfest against an index export; state (a) baseline errors left unfixed for Phase 3
- [Phase 01]: manifest.json key order left unchanged in 01-03 so hassfest's ordering error stays in the honest baseline; Phase 3 fixes it
- [Phase 01]: validate.yml uses floating refs hacs/action@main and hassfest@master per D-22; Phase 3 pins commit SHAs
- [Phase 01]: Plan 01-02 deleted all 14 root card and panel .js duplicates in one deletion-only commit (b7353c6); no port commit needed since every triage row was discarded
- [Phase 01]: Plan 01-06 moved it, nl, pl, pt and pt-BR into translations/ as five R100 renames; pt and pt-BR stay separate identical files
- [Phase 01]: Fork version starts at 2.0.0 (D-19, developer chose fork-2-0-0); tags vX.Y.Z equal manifest.json, strictly increasing
- [Phase 01]: versions.env is the single HA pin source (2026.10.4); hacs.json minimum is 2024.12.0 (D-20, D-21)
- [Phase 01]: 01-07: root de/en/es/fr.json and strings.json deleted; translations/ is the only translation location; 9 orphan keys not ported (D-06); fh_ui preserved (D-09)
- [Phase 01]: FOUND-09 satisfied by hosted Validate run 40422777272 (head bd8de7a): hacs failure, hassfest failure; failures HF-01..04, HF-W01, HACS-01..03, HACS-W01 match the prediction, 0 hosted-only
- [Phase 01]: No Home Assistant installation exists yet; first fork release v2.0.0 is a fresh install and any Home install must be HA >= 2024.12.0

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
- [Phase 2]: No Home Assistant install exists yet and the hardware is undecided. Phase 2 discussion must cover the Dev/Preview host and, later, the Home hardware.
- [Phase 2]: `reset-preview` must wipe the whole config volume including `family_hub_backups/`. `store.py` restores from backups when storage loads empty.
- [Phase 1 -> 3]: Validate is red by design until Phase 3. The recorded baseline is hassfest HF-01..04 + HF-W01 and HACS HACS-01..03 (Issues disabled, no topics, license NOASSERTION) + HACS-W01; see `01-VALIDATION-BASELINE.md`.
- [Phase 3]: `pytest-homeassistant-custom-component` needs Python 3.14. Confirm `uv` provides it on the dev machine.
- [Phase 4]: `git.create_tag: true` makes milestone completion create a `v1.0`-style tag. `release.yml` (REL-01) must ignore tags that are not `vX.Y.Z`, or that config setting should change.

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-27T07:34:06.609Z
Stopped at: Phase 01 complete, ready to plan Phase 2
Resume file: None
