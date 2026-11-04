---
phase: 02-dev-family-preview
plan: 06
subsystem: infra
tags: [home-assistant, seed-tool, calendar, local-calendar, google-calendar-safety, diff-sync, unittest]

requires:
  - phase: 02-dev-family-preview
    provides: "02-01 seed tool: HAClient, CredentialStore, open_admin identity guard, ENVIRONMENTS (tag, marker_prefix), LiveHA harness, ical==14.3.0 approval"
provides:
  - "tools/seed/calendar_tags.py: marker(), parse_marker(), matches() - the single five-condition gate before any seeded event is deleted"
  - "tools/seed/events.py: CalendarSlot, DesiredEvent, window(), delete_window(), plan_week_events(), diff(), sync(), clean(), and the CLI python -m tools.seed.events {plan,sync,clean}"
  - "Event marker contract: summary prefix '[DEV] ' / '[PREVIEW] ', description line family-hub-seed:<env>:<key>, key <iso-year>w<iso-week>-<weekday>-<slot>-<person-slug>"
  - "Live D-11 proof on a Local Calendar in HA 2026.10.4 and 105 pure tests"
affects: [02-07, 02-08, 02-09, 02-10]

# Actuals (#2632): chars/4 over the 5 files this plan created (66743 bytes)
actuals:
  tokens: 16700
  tasks: 2
  commits: 2
plan_head_before: 0a69161b96545c3020c61d8f27347ebb2fa41a07
plan_head_after: 1c90dcec76fafe769b980fdd49547cf5b3d46302

tech-stack:
  added: []
  patterns:
    - "One gate before any delete: every existing event passes calendar_tags.matches() first; no other code path builds a delete list"
    - "Week-anchored keys plus diff sync: create only missing, delete only stale, keep unchanged (no daily churn)"
    - "Dry run is the default for sync and clean; --apply is required to write"
    - "Next-week template is built by filtering the this-week template, so rollovers only add events"

key-files:
  created:
    - tools/seed/calendar_tags.py
    - tools/seed/events.py
    - tools/seed/tests/live_events.py
    - tools/seed/tests/test_calendar_tags.py
    - tools/seed/tests/test_events_plan.py
  modified: []

key-decisions:
  - "diff() takes existing events as a mapping entity_id -> list of HA API event dicts, so duplicate detection and keep/delete are per (calendar, key)"
  - "DesiredEvent.start/end are always naive local datetimes (all-day events start at midnight, end a day later, flag all_day), so the plan sorts on one type"
  - "The shared event gets the person slug 'shared', so it has the same key on both calendars"
  - "An existing event counts as unchanged when summary and start (or all-day date) are equal; end is not compared, to avoid churn from provider round-trip differences"
  - "A calendar is read, written or deleted from only when it is writable; events from read-only or unnamed calendars never enter any list"

patterns-established:
  - "Pattern: matcher conditions are each pinned by a one-thing-different test and by a mutation check"
  - "Pattern: times from HA are wall-clock in the instance's own zone (tz offset dropped, never converted)"

requirements-completed: [PREV-04, PREV-03]

coverage:
  - id: D1
    description: "The exact matcher: only an event with the target environment's exact tag, a whole-line marker with a [a-z0-9-]+ key, no recurrence, a start inside the half-open window and a calendar on the allow-list is a delete candidate"
    requirement: PREV-03
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_calendar_tags.py (36 tests: look-alikes, recurrence, one-second boundaries, all-day edges, allow-list)"
        status: pass
      - kind: other
        ref: "mutation check: 8 weakened matcher conditions (no tag, no marker, no recurrence check, no window start, no window end, inclusive end, no allow-list, prefix-only marker) each make the suite fail"
        status: pass
    human_judgment: false
  - id: D2
    description: "Live proof on a Local Calendar: sync dry run writes nothing; sync --apply deletes exactly the stale in-window [DEV] event and creates the plan; a second apply reports create 0, delete 0; clean --apply removes only the created events; untagged, other-environment, half-marked look-alike and out-of-window events keep their uids throughout"
    requirement: PREV-03
    verification:
      - kind: integration
        ref: "tools/seed/tests/live_events.py (python -B -m unittest discover -s tools/seed/tests -t . -p live_events.py): 6 tests OK on HA 2026.10.4, run three times"
        status: pass
    human_judgment: false
  - id: D3
    description: "Week-anchored plan: every this-week day has a morning or all-day and a 16:00-or-later event, Saturday 4 events, Friday an all-day event, one event shared by two members, a free member every day, next-week Sunday empty and Tuesday with one event; sorted and deterministic; empty and one-calendar edges"
    requirement: PREV-04
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_events_plan.py (69 tests over 21 consecutive dates with Monday rollovers)"
        status: pass
    human_judgment: false
  - id: D4
    description: "No daily churn: unchanged events are kept, a Monday rollover only adds events for days present in both windows, a second sync reports create 0, delete 0"
    requirement: PREV-04
    verification:
      - kind: unit
        ref: "tools/seed/tests/test_events_plan.py#PlanStabilityTests and DiffTests"
        status: pass
      - kind: integration
        ref: "tools/seed/tests/live_events.py#test_d_second_apply_changes_nothing"
        status: pass
    human_judgment: false
  - id: D5
    description: "Seeded events on the family's real Google calendars are acceptable to the family and look right on phones"
    verification: []
    human_judgment: true
    rationale: "Plan 02-08 points this at the real Google calendars; how the events read on family phones is a human judgment no test can assert"

# Metrics
duration: ~40 min (start time not recorded; estimated from task timestamps)
completed: 2026-11-04
status: complete
---

# Phase 02 Plan 06: Tagged Pretend Calendar Events Summary

**Exact-match tagged calendar events (`[DEV] ` / `[PREVIEW] ` plus a `family-hub-seed:<env>:<key>` marker line) planned week-anchored for this week and next, synced by diff so only missing events are created and only stale, fully matching events are deleted, and proven live on a Local Calendar next to untagged, other-environment and look-alike events.**

## Performance

- **Duration:** ~40 min (start time was not recorded, so this is an estimate)
- **Completed:** 2026-11-04T00:17Z (last live gate run)
- **Tasks:** 2 (1 tracer, 1 TDD auto)
- **Files modified:** 5 created, 0 modified
- **Live suite:** 6 tests, 24-52 s per run (one HA boot); pure suites 105 tests in under 0.1 s

## Accomplishments

- `calendar_tags.matches()` is the only delete gate: exact tag (case sensitive, trailing space), whole-line marker with a `[a-z0-9-]+` key, no rrule or recurrence_id, start in a half-open window, calendar on the allow-list. `events.diff()` filters every existing event through it and builds the delete list from nothing else (`grep -c 'calendar_tags.matches(' tools/seed/events.py` prints 1).
- `python -m tools.seed.events {plan,sync,clean}` with `--calendar ENTITY=PERSON[:ro]`, `--today`, `--apply`. `sync` and `clean` are dry runs unless `--apply` is given; the loopback guard exits 2, a SeedError exits 1, an identity mismatch exits 3 (reused from 02-01's `open_admin`).
- Live proof (HA 2026.10.4, Local Calendars "Sam" and "Jordan"): dry run unchanged; `sync --apply` deleted exactly the stale `[DEV] Old event` and created the 31 planned events (2-calendar mapping); second apply `create 0, delete 0`; `clean --apply` left exactly the six non-matching pre-existing events with their original uids; a `:ro` calendar received nothing.
- 105 pure tests, with a mutation check: each of 8 deliberately weakened matcher conditions makes the suite fail.

## Task Commits

1. **Task 1 (tracer): tagged events created, kept and cleaned on a live Local Calendar** - `2079e60` (feat)
2. **Task 2 (TDD): pin the matcher and the week plan with exhaustive pure tests** - `1c90dce` (test)

**Plan metadata:** the `docs(02-06)` commit that adds this file.

Tracer feedback gate: auto/end-of-phase mode with an automated-only `<verify>`; the live suite was re-run after the Task 1 commit (6 tests OK) before expansion. Logged "Tracer verified end-to-end - expanding".

## Event templates

The template members are indexes 0 to 3 and map onto the writable calendars in the order given (modulo how many there are). With the invented family in the order Sam, Jordan, Riley, Casey they are Sam (0), Jordan (1), Riley (2), Casey (3). Times are local wall-clock in the instance's time zone.

### This week (Monday to Sunday)

| Weekday | Slot | Time | Title | Member(s) |
|---------|------|------|-------|-----------|
| Mon | 1 | 08:30-09:00 | School drop-off | Riley (2) |
| Mon | 2 | 16:30-17:15 | Piano lesson | Riley (2) |
| Tue | 1 | 08:30-09:00 | School drop-off | Casey (3) |
| Tue | 2 | 17:00-18:00 | Football practice | Riley (2) |
| Wed | 1 | 10:00-11:00 | Dentist | Riley (2) |
| Wed | 2 | 18:30-21:00 | Family movie night | Sam (0) and Jordan (1), shared, key person slug `shared` |
| Thu | 1 | 08:30-09:00 | School drop-off | Casey (3) |
| Thu | 2 | 16:30-17:15 | Piano lesson | Casey (3) |
| Fri | 1 | all day | Grandma visits | Jordan (1) |
| Fri | 2 | 17:00-18:00 | Football practice | Riley (2) |
| Sat | 1 | 09:00-10:30 | Football practice | Riley (2) |
| Sat | 2 | 11:00-11:45 | Piano lesson | Casey (3) |
| Sat | 3 | 14:00-16:00 | Grandma visits | Jordan (1) |
| Sat | 4 | 16:30-17:30 | Football practice | Riley (2) |
| Sun | 1 | 10:00-10:45 | Piano lesson | Casey (3) |
| Sun | 2 | 18:00-20:00 | Family movie night | Sam (0) |

### Next week

Identical to this week (same slots, times, titles and members) except Sunday has no events (both slots dropped) and Tuesday keeps only slot 1 (School drop-off, Casey). It is built by filtering the this-week template, so a Monday rollover only adds events to the days present in both windows (Sunday and Tuesday slot 2 fill in, plus a new next week appears) and last week's events, now outside the plan window but inside the 28-day delete window, are deleted as stale.

Counts per day this week: Mon 2, Tue 2, Wed 2 (one shared on two calendars), Thu 2, Fri 2 (one all-day), Sat 4, Sun 2. Next week: Sun 0, Tue 1, others as this week.

## Files Created/Modified

- `tools/seed/calendar_tags.py` - pure matcher: `marker`, `parse_marker`, `event_start`, `matches`, `as_naive_datetime`
- `tools/seed/events.py` - plan, diff, sync, clean and the CLI
- `tools/seed/tests/live_events.py` - live D-11 proof (port 18132, target dev)
- `tools/seed/tests/test_calendar_tags.py` - 36 matcher/marker tests
- `tools/seed/tests/test_events_plan.py` - 69 plan, diff and CLI tests over 21 dates

## Decisions Made

- See `key-decisions` above. In short: per-(calendar, key) diff, naive local datetimes everywhere, `shared` person slug for the shared event, unchanged means equal summary and start, read-only calendars invisible to every list.
- Key format uses a zero-padded two-digit ISO week (`2026w45`), which satisfies `[a-z0-9-]+`.
- The partial-calendar rule (a member with no event every day) is guaranteed when there are four or more writable calendars, because the template has four members; with fewer calendars members double up (two calendars keep the shared event on both, so Wednesday has no free member). One writable calendar gets every event, the shared event once.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Live test gained an out-of-window genuine [DEV] event (u7) and a read-only-calendar case**
- **Found during:** Task 1
- **Issue:** The plan's six pre-existing events do not exercise the bounded-window condition on a live calendar (u3 is stale but inside the window), nor the "read-only calendar receives nothing" truth.
- **Fix:** Added u7 "[DEV] Ancient event" with a valid dev marker 60 days before Monday (must survive every run) and `test_f_a_read_only_calendar_is_never_written`. The final survivor set is therefore u1, u2, u4, u5, u6, u7 rather than the plan's u1, u2, u4, u5, u6.
- **Files modified:** `tools/seed/tests/live_events.py`
- **Verification:** live suite OK (6 tests)
- **Committed in:** `2079e60`

### TDD note (Task 2)

`test_calendar_tags.py` and `test_events_plan.py` passed on their first meaningful run, because Task 1 (the tracer) already shipped the implementation as the plan orders it. The only failures were two bugs in my own new tests (a `date` has no `.date()`, and a rollover expectation that wrongly ignored the events that fill in the new this-week days). RED evidence is replaced by a mutation check: 8 weakened matcher conditions are each caught by the suite. No GREEN `feat` commit exists for Task 2 because no production code changed.

---

**Total deviations:** 1 auto-fixed (1 missing-critical test coverage), plus the TDD note
**Impact on plan:** Stronger live proof of the window bound; no scope creep.

## TDD Gate Compliance

Task 2 carries `tdd="true"` but the plan is `type: execute`, so the plan-level gate sequence is not enforced. The test commit `1c90dce` (`test(02-06)`) exists; there is no `feat(02-06)` commit after it because the implementation preceded the tests (Task 1 `2079e60` is a `feat(02-06)` commit). The suites were validated by mutation instead of an intentional RED.

## Issues Encountered

- The worktree harness refuses compound git/shell commands, so the live gate and commits ran as separate plain commands. No effect on results.
- `scripts/dev-up` and the other plan 02-05 files were not touched.

## Authentication Gates

None. The precondition (02-01 package approval covering `ical==14.3.0`) was met and the orchestrator had installed exactly that pin; nothing else was installed. `LiveHA` still starts HA with `--skip-pip`, and Local Calendar loaded because `ical` was already present.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. T-02-10 (deleting a real event) is mitigated by the five-condition matcher, dry-run default and the live look-alike test; T-02-11 (churn) by week-anchored keys and the create 0, delete 0 re-run; T-02-SC by the 02-01 approval. Plan 02-08 still has to add the dated backups and the hard stop before the first destructive run on real Google calendars.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-07 can call `events.sync(client, token, slots, env, today, apply)` after the family file maps each member to a writable calendar entity; the module has its own entry point and does not touch `tools/seed/__main__.py`.
- Plan 02-08 points the same code at the chosen Google calendars; it still owes the `.ics` backup and the hard stop (T-02-10).
- Shared requirement IDs PREV-03 and PREV-04 are also declared by other plans; REQUIREMENTS.md was not edited here (the orchestrator owns shared-ID marking).

## Self-Check: PASSED

- All 5 created files exist on disk.
- Commits `2079e60` and `1c90dce` are ancestors of HEAD.
- Pure suites: 105 tests OK. Live suite: 6 tests OK, no skips.
- Acceptance greps: `calendar_tags.matches(` count 1; `startswith(...[DEV|PREVIEW]...)` count 0 in events.py; `def test_` count in test_calendar_tags.py is 36 (at least 18); test_events_plan.py iterates 21 dates.

---
*Phase: 02-dev-family-preview*
*Completed: 2026-11-04*
