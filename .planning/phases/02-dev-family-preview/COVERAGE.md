# API Coverage — Google Calendar (through Home Assistant's `google` integration and Google's secret iCal feed)

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Scope: Phase 2 connects Dev and Preview read/write to a chosen list of the family's real Google calendars (D-07). The tooling never calls Google directly except to fetch each calendar's secret iCal address for backups (D-30); everything else goes through HA's Google Calendar integration. Home Assistant's own REST/WebSocket API is local, not an external service, and is not listed here.

| capability | decision | reason |
|---|---|---|
| oauth-signin | INTEGRATE | |
| token-refresh | INTEGRATE | |
| list-calendars | INTEGRATE | |
| calendar-selection | INTEGRATE | |
| list-events | INTEGRATE | |
| create-event | INTEGRATE | |
| delete-event | INTEGRATE | |
| secret-ical-export | INTEGRATE | |
| update-event | OPT-OUT | not needed: the seed never edits events; a changed seeded event is deleted and re-created by its key, and the card's own edit flow stays as upstream |
| recurring-events | OPT-OUT | explicitly out of scope: seeded events are single, and the D-11 matcher refuses recurring events for safety |
| event-reminders | OPT-OUT | not available: HA's create_event takes only summary, description, location and times; subscribers' default reminders apply, accepted in D-25 |
| attendees-invitations | OPT-OUT | not needed: family calendars, no invitations; HA does not expose attendees on create |
| search-events-service | OPT-OUT | not needed: GET /api/calendars/<entity> covers every read the tooling does |
| create-delete-calendars | OPT-OUT | explicitly out of scope: D-25 chose no dedicated seed calendar |
| read-only-access-mode | OPT-OUT | not needed now: D-15 makes Dev and Preview read/write; the calendar_access option is noted in research for later |
| push-sync-channels | OPT-OUT | handled inside HA's gcal-sync library; the tooling does not drive it |
| ics-import-restore | OPT-OUT | not needed as automation: restoring an event is a rare, documented manual Google Calendar Import (dev/GOOGLE.md) |
| token-revocation | OPT-OUT | not needed as automation: manual at myaccount.google.com/permissions, documented in dev/GOOGLE.md |
