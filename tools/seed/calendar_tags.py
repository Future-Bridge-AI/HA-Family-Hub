"""The only gate before a seeded calendar event may be deleted (D-11, D-15, PREV-03).

With plan 02-08 the seeded events live on the family's real Google calendars next to real
events, so deleting by "looks like ours" is not good enough. ``matches`` is the single function
every delete candidate must pass; events.py builds its delete list from nothing else. Every
condition is there for a reason, and all of them must hold:

* The summary starts with the exact environment tag (``[DEV] ``, ``[PREVIEW] ``), case
  sensitive and including the trailing space. A tag in the middle of a title, ``[DEV]x`` or
  ``[dev] `` is somebody else's text, and the other environment's tag is the other
  environment's event (D-15: Dev and Preview never touch each other's events).
* The description has a whole line ``family-hub-seed:<env>:<key>`` with a key of ``[a-z0-9-]+``.
  The tag alone is not enough: a real event titled "[DEV] something" typed by a person has no
  marker, and a marker pasted into a real event's notes has no tag.
* The event is a single event: no rrule and no recurrence_id. Deleting one instance of a series
  can silently remove the whole series, and the seed never creates recurring events.
* The event starts inside [window_start, window_end), half open. Old tagged events outside the
  bounded window are never touched, however well they match.
* The calendar is on the allow-list passed in, so a calendar the family file did not mark
  writable (or one nobody named) is never modified.

Times are wall-clock values in the Home Assistant instance's own time zone: HA's calendar API
already converts to local time, so a time zone offset on an event start is dropped, never
converted. The module is pure: no I/O, no Home Assistant, stdlib only.
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Collection, Mapping, Optional, Union

from .envs import Env

KEY_PATTERN = re.compile(r"[a-z0-9-]+")

EventTime = Union[datetime.datetime, datetime.date]


def marker(env: Env, key: str) -> str:
    """Return the description line that marks an event as seeded by ``env``."""
    if not isinstance(key, str) or KEY_PATTERN.fullmatch(key) is None:
        raise ValueError("event key %r must match [a-z0-9-]+" % (key,))
    return env.marker_prefix + key


def parse_marker(description: Optional[str], env: Env) -> Optional[str]:
    """Return the key from the first description line that is exactly a marker for ``env``.

    The whole line has to match: no leading or trailing text, no upper-case or underscore in
    the key, and the other environment's prefix never matches.
    """
    if not isinstance(description, str) or not env.marker_prefix:
        return None
    pattern = re.escape(env.marker_prefix) + "(" + KEY_PATTERN.pattern + ")"
    for line in description.splitlines():
        found = re.fullmatch(pattern, line)
        if found is not None:
            return found.group(1)
    return None


def event_start(event: Mapping[str, Any]) -> Optional[EventTime]:
    """Return an event's start as a naive wall-clock datetime or a date (all-day), else None.

    Accepts HA's API shape (``{"dateTime": ...}`` / ``{"date": ...}``), ISO strings and plain
    date or datetime objects. Anything unreadable is None, which makes the event not match.
    """
    raw = event.get("start")
    if isinstance(raw, Mapping):
        raw = raw.get("dateTime") or raw.get("date")
    try:
        if isinstance(raw, datetime.datetime):
            return raw.replace(tzinfo=None)
        if isinstance(raw, datetime.date):
            return raw
        if isinstance(raw, str):
            if len(raw) == 10:
                return datetime.date.fromisoformat(raw)
            return datetime.datetime.fromisoformat(raw).replace(tzinfo=None)
    except ValueError:
        return None
    return None


def as_naive_datetime(value: EventTime) -> datetime.datetime:
    """A date counts as local midnight; a datetime loses any tzinfo (wall-clock comparison)."""
    if isinstance(value, datetime.datetime):
        return value.replace(tzinfo=None)
    return datetime.datetime.combine(value, datetime.time.min)


def matches(
    event: Mapping[str, Any],
    env: Env,
    calendar: str,
    allowed_calendars: Collection[str],
    window_start: EventTime,
    window_end: EventTime,
) -> bool:
    """True only when ``event`` is a single seeded event of ``env`` that may be deleted."""
    if isinstance(allowed_calendars, (str, bytes)):
        raise TypeError("allowed_calendars must be a collection of entity ids, not one string")
    if not env.tag or not env.marker_prefix:
        return False
    summary = event.get("summary")
    if not isinstance(summary, str) or not summary.startswith(env.tag):
        return False
    if parse_marker(event.get("description"), env) is None:
        return False
    if event.get("rrule") or event.get("recurrence_id"):
        return False
    start = event_start(event)
    if start is None:
        return False
    if not as_naive_datetime(window_start) <= as_naive_datetime(start) < as_naive_datetime(window_end):
        return False
    return isinstance(calendar, str) and calendar in allowed_calendars
